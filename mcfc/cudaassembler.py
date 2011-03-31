# This file is part of the Manycore Form Compiler.
#
# The Manycore Form Compiler is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
# 
# The Manycore Form Compiler is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
# 
# You should have received a copy of the GNU General Public License along with
# the Manycore Form Compiler.  If not, see <http://www.gnu.org/licenses>
#
# Copyright (c) 2011, Graham Markall <grm08@doc.ic.ac.uk> and others. Please see
# the AUTHORS file in the main source directory for a full list of copyright
# holders.


"""This module generates the code that extracts the relevant fields from
Fluidity state, transfers it to the GPU, and the run_model_ function that
executes the model for one timestep, by calling the kernels generated by
cudaform.py, and the necessary solves."""

# MCFC libs
from assembler import *
from codegeneration import *
from utilities import uniqify
# This is referred to as mcfcstate because of the clash with the
# variable called state.
import state as mcfcstate
# FEniCS UFL libs
import ufl.finiteelement
from ufl.differentiation import SpatialDerivative
from ufl.algorithms.transformations import Transformer

# Variables used throughout the code generation
state            = Variable('state',              Pointer(Class('StateHolder')))

localVector      = Variable('localVector',        Pointer(Real()))
localMatrix      = Variable('localMatrix',        Pointer(Real()))
globalVector     = Variable('globalVector',       Pointer(Real()))
globalMatrix     = Variable('globalMatrix',       Pointer(Real()))
solutionVector   = Variable('solutionVector',     Pointer(Real()))

matrixColmSize   = Variable('matrix_colm_size',   Integer())
matrixFindrmSize = Variable('matrix_findrm_size', Integer())
matrixColm       = Variable('matrix_colm',        Pointer(Integer()))
matrixFindrm     = Variable('matrix_findrm',      Pointer(Integer()))

# Variables used in the run_model and initialiser functions

numEle           = Variable('numEle',            Integer())
numNodes         = Variable('numNodes',          Integer())
detwei           = Variable('detwei',            Pointer(Real()))
eleNodes         = Variable('eleNodes',          Pointer(Integer()))
coordinates      = Variable('coordinates',       Pointer(Real()))
dn               = Variable('dn',                Pointer(Real()))
quadWeights      = Variable('quadWeights',       Pointer(Real()))
nDim             = Variable('nDim',              Integer())
nQuad            = Variable('nQuad',             Integer())
nodesPerEle      = Variable('nodesPerEle',       Integer())
shape            = Variable('shape',             Pointer(Real()))
dShape           = Variable('dShape',            Pointer(Real()))
numValsPerNode   = Variable('numValsPerNode',    Integer())
numVectorEntries = Variable('numVectorEntries',  Integer())

# State methods that provide each of these variables, and the name of the field
# that they're taken from, if they require a field. We get things from the
# coordinate field for now, assuming that they're the same for all fields. This
# will change once we have the basic functionality working.

getters = { numEle:           ('getNumEle',                  None,        ), \
            numNodes:         ('getNumNodes',                None,        ), \
            detwei:           ('getDetwei',                  None,        ), \
            eleNodes:         ('getEleNodes',                None,        ), \
            coordinates:      ('getCoordinates',             None,        ), \
            dn:               ('getReferenceDn',             None,        ), \
            quadWeights:      ('getQuadWeights',             None,        ), \
            nDim:             ('getDimension',               'Coordinate' ), \
            nQuad:            ('getNumQuadPoints',           'Coordinate' ), \
            nodesPerEle:      ('getNodesPerEle',             'Coordinate' ), \
            shape:            ('getBasisFunction',           'Coordinate' ), \
            dShape:           ('getBasisFunctionDerivative', 'Coordinate' ), \
            numValsPerNode:   ('getValsPerNode',             None         ), \
            numVectorEntries: ('getNodesPerEle',             None         )  }

class CudaAssemblerBackend(AssemblerBackend):

    def compile(self, ast, uflObjects):

        self._ast = ast
        self._uflObjects = uflObjects

        # Build definitions
        definitions = self._buildHeadersAndGlobals()

        # Build declarations
        declarations = GlobalScope()
        state = self._buildState()
        declarations.append(state)
        initialiser = self._buildInitialiser()
        declarations.append(initialiser)
        finaliser = self._buildFinaliser()
        declarations.append(finaliser)
        runModel = self._buildRunModel()
        declarations.append(runModel)

        return definitions, declarations

    def _buildState(self):
        decl = Declaration(state)
        return decl

    def _buildInitialiser(self):

        func = FunctionDefinition(Void(), 'initialise_gpu_')
        func.setExternC(True)

        # Call the state constructor
        newState = New(Class('StateHolder'))
        construct = AssignmentOp(state, newState)
        func.append(construct)
        
        # Call the state initialiser
        call = FunctionCall('initialise')
        arrow = ArrowOp(state, call)
        func.append(arrow)

        # Extract accessed fields
        accessedFields = findAccessedFields(self._ast)
        for field in accessedFields:
            rank = mcfcstate.getRank(field)
            params = [ Literal(field), Literal(rank) ]
            call = FunctionCall('extractField',params)
            arrow = ArrowOp(state, call)
            func.append(arrow)

        # Allocate memory and transfer to GPU
        call = FunctionCall('allocateAllGPUMemory')
        arrow = ArrowOp(state, call)
        func.append(arrow)

        call = FunctionCall('transferAllFields')
        arrow = ArrowOp(state, call)
        func.append(arrow)
        
        # Insert temporary fields into state
        solveResultFields = findSolveResults(self._ast)
        for field in solveResultFields:
            similarField = self.findSimilarField(field)
            params = [ Literal(field), Literal(similarField) ]
            call = FunctionCall('insertTemporaryField',params)
            arrow = ArrowOp(state, call)
            func.append(arrow)

        # Get num_ele, num_nodes etc
        self.simpleAppend(func, numEle)
        self.simpleAppend(func, numNodes)

        # Get sparsity of the field we're solving for
        sparsity = Variable('sparsity', Pointer(Class('CsrSparsity')))
        # We can use the similarField from earlier, since its
        # the only field we're solving on for now. When we start working
        # with solving multiple fields, this logic will need re-working.
        # (For each solve field, we should use the similar field and
        # generate a new sparsity from that)
        params = [ Literal(similarField) ]
        call = FunctionCall('getSparsity', params)
        arrow = ArrowOp(state, call)
        assignment = AssignmentOp(Declaration(sparsity), arrow)
        func.append(assignment)

        # Initialise matrix_colm, findrm, etc.
        # When you tidy this up, put these in a dict???
        matrixVars = [ matrixColm,    matrixFindrm,    matrixColmSize, matrixFindrmSize ]
        sourceFns  = ['getCudaColm', 'getCudaFindrm', 'getSizeColm',  'getSizeFindrm'   ]

        for var, source in zip(matrixVars, sourceFns):
            call = FunctionCall(source)
            rhs = ArrowOp(sparsity, call)
            assignment = AssignmentOp(var, rhs)
            func.append(assignment)

        # Get the number of values per node and use it to calculate the
        # size of all the local vector entries. For now we'll use the same
        # logic as before, that we're only solving on one field, so we can
        # get these things from the last similar field that we found.
        self.simpleAppend(func, numValsPerNode, param=similarField)
        self.simpleAppend(func, numVectorEntries, param=similarField)
        
        # Now multiply numVectorEntries by numValsPerNode to get the correct
        # size of the storage required
        mult = MultiplyOp(numVectorEntries, numValsPerNode)
        assignment = AssignmentOp(numVectorEntries, mult)
        func.append(assignment)

        # The space for the local matrix storage is equal to the local vector
        # storage size squared.
        numMatrixEntries = Variable('numMatrixEntries', Integer())
        rhs = MultiplyOp(numVectorEntries, numVectorEntries)
        assignment = AssignmentOp(Declaration(numMatrixEntries), rhs)
        func.append(assignment)

        # Generate Mallocs for the local matrix and vector, and the solution
        # vector.
        self.buildAppendCudaMalloc(func, localVector, MultiplyOp(numEle, numVectorEntries))
        self.buildAppendCudaMalloc(func, localMatrix, MultiplyOp(numEle, numMatrixEntries))
        self.buildAppendCudaMalloc(func, globalVector, MultiplyOp(numNodes, numValsPerNode))
        self.buildAppendCudaMalloc(func, globalMatrix, matrixColmSize)
        self.buildAppendCudaMalloc(func, solutionVector,MultiplyOp(numNodes, numValsPerNode))

        return func

    def buildAppendCudaMalloc(self, scope, var, size):
        cast = Cast(Pointer(Pointer(Void())), AddressOfOp(var))
        sizeof = SizeOf(var.getType().getBaseType())
        sizeArg = MultiplyOp(sizeof, size)
        params = [ cast, sizeArg ]
        malloc = FunctionCall('cudaMalloc', params)
        scope.append(malloc)

    def buildAppendCudaMemsetZero(self, func, base, length):
        t = base.getType().getBaseType()
        size = MultiplyOp(SizeOf(t), length)
        params = [ base, Literal(0), size ]
        memset = FunctionCall('cudaMemset', params)
        func.append(memset)

    def findSimilarField(self, field):
        """Find a field with the same basis as the named field. You should
        always be able to find a similar field."""

        obj = self._uflObjects[field]
        element = obj.element()
        degree = element.degree()
        
        if isinstance(element, ufl.finiteelement.FiniteElement):
            sourceFields = mcfcstate._finiteElements
        elif isinstance(element, ufl.finiteelement.FiniteElement):
            sourceFields = mcfcstate._vectorElements
        elif isinstance(element, ufl.finiteelement.FiniteElement):
            sourceFields = mcfcstate._tensorElements

        for k in sourceFields:
            if sourceFields[k] == degree:
                return k

    def _buildFinaliser(self):
        func = FunctionDefinition(Void(), 'finalise_gpu_')
        func.setExternC(True)

        delete = Delete(state)
        func.append(delete)

        return func

    def _buildHeadersAndGlobals(self):
        scope = GlobalScope()
        include = Include('cudastatic.hpp')
        scope.append(include)
        include = Include('cudastate.hpp')
        scope.append(include)

        # Declare vars in global scope
        declVars = [localVector, localMatrix, globalVector, globalMatrix, solutionVector, \
                    matrixColmSize, matrixFindrmSize, matrixColm, matrixFindrm ]

        for var in declVars:
            scope.append(Declaration(var))

        return scope

    def simpleAppend(self, func, var, provider=None, param=None):
        """Append a variable declaration to func, without building a new
        Variable instance. The declaration is initialised by the provider
        with the parameter param, unless these are not specified. If they
        are not specified, then the getters dict is used to look one up."""
        params = []
        
        if provider is None:
            provider, defaultParam = getters[var]
            if param is None:
                param = defaultParam
        
        if param is not None:
            paramString = Literal(param)
            params.append(paramString)

        call = FunctionCall(provider, params)
        arrow = ArrowOp(state, call)
        assignment = AssignmentOp(Declaration(var), arrow)
        func.append(assignment)

    def _buildRunModel(self):
     
        # List of field values that we've already extracted when building the function 
        self._alreadyExtracted = []

        dt = Variable('dt', Real())
        func = FunctionDefinition(Void(), 'run_model_', [dt])
        func.setExternC(True)

        # Initialise some variables we need
        toBeInitialised = [ numEle, numNodes, detwei, eleNodes, coordinates, dn, \
          quadWeights, nDim, nQuad, nodesPerEle, shape, dShape ]
        for var in toBeInitialised:
            self.simpleAppend(func, var)

        # Build the block dimension declaration. Eventually this needs to be configurable
        # (e.g. for autotuning, performance experiments.)
        blockXDim = Variable('blockXDim', Integer())
        assignment = AssignmentOp(Declaration(blockXDim), Literal(1))
        func.append(assignment)
        gridXDim = Variable('gridXDim', Integer())
        assignment = AssignmentOp(Declaration(gridXDim), Literal(1))
        func.append(assignment)

        # Call the function that computes the amount of shared memory we need for
        # transform_to_physical. 
        shMemSize = Variable('shMemSize', Integer())
        params = [ blockXDim, nDim, nodesPerEle ]
        t2pShMemSizeCall = FunctionCall('t2p_shmemsize', params)
        assignment = AssignmentOp(Declaration(shMemSize), t2pShMemSizeCall)
        func.append(assignment)

        # Create a call to transform_to_physical.
        params = [ coordinates, dn, quadWeights, dShape, detwei, numEle, nDim, nQuad, nodesPerEle ]
        t2pCall = CudaKernelCall('transform_to_physical', params, gridXDim, blockXDim, shMemSize)
        func.append(t2pCall)

        # These parameters will be needed by every matrix/vector assembly
        # see also the KernelParameterComputer in cudaform.py.
        matrixParameters = [localMatrix, numEle, dt, detwei]
        vectorParameters = [localVector, numEle, dt, detwei]

        # Traverse the AST looking for solves
        solves = findSolves(self._ast)
        
        for solve in solves:
            # Unpack the bits of information we want
            result = str(solve.getChild(0))
            solveNode = solve.getChild(1)
            matrix = solveNode.getChild(0)
            vector = solveNode.getChild(1)
            
            # Call the matrix assembly
            form = self._uflObjects[str(matrix)]
            tree = form.integrals()[0].integrand()
            params = self._makeParameterListAndGetters(func, tree, form, matrixParameters)
            matrixAssembly = CudaKernelCall(str(matrix), params, gridXDim, blockXDim)
            func.append(matrixAssembly)

            # Then call the rhs assembly
            form = self._uflObjects[str(vector)]
            tree = form.integrals()[0].integrand()
            params = self._makeParameterListAndGetters(func, tree, form, vectorParameters)
            vectorAssembly = CudaKernelCall(str(vector), params, gridXDim, blockXDim)
            func.append(vectorAssembly)

            # Zero the global matrix and vector
            # First we need to get numvalspernode, for the length of the global vector
            similarField = self.findSimilarField(result)
            self.simpleAppend(func, numValsPerNode, param=similarField)
            self.buildAppendCudaMemsetZero(func, globalMatrix, matrixColmSize)
            size = MultiplyOp(numValsPerNode, numNodes)
            self.buildAppendCudaMemsetZero(func, globalVector, size)

            # Build calls to addto kernels. 
            # For the matrix
            params = [ matrixFindrm, matrixColm, globalMatrix, eleNodes, \
                         localMatrix, numEle, nodesPerEle ]
            matrixAddto = CudaKernelCall('matrix_addto', params, gridXDim, blockXDim)
            func.append(matrixAddto)

            # And the vector
            params = [ globalVector, eleNodes, localVector, numEle, nodesPerEle ]
            vectorAddto = CudaKernelCall('vector_addto', params, gridXDim, blockXDim)
            func.append(vectorAddto)
            
            # call the solve
            params = [ matrixFindrm, matrixFindrmSize, matrixColm, matrixColmSize, \
                          globalMatrix, globalVector, numNodes, solutionVector ]
            cgSolve = FunctionCall('cg_solve', params)
            func.append(cgSolve)

            # expand the result
            var = self.extractCoefficient(func, result)
            params = [ var, solutionVector, eleNodes, numEle, numValsPerNode, nodesPerEle ]
            expand = CudaKernelCall('expand_data', params, gridXDim, blockXDim)
            func.append(expand)

        # Traverse the AST looking for fields that need to return to the host
        returnedFields = findReturnedFields(self._ast)
        
        for hostField, GPUField in returnedFields:
            # Found one? ok, call the method to return it.
            params = [ Literal(hostField), Literal(GPUField) ]
            returnCall = FunctionCall('returnFieldToHost', params)
            arrow = ArrowOp(state, returnCall)
            func.append(arrow)

        return func

    def extractCoefficient(self, func, coefficientName):
        varName = coefficientName + 'Coeff'
        var = Variable(varName, Pointer(Real()))
        
        # Don't declare and extract coefficients twice
        if varName not in self._alreadyExtracted:
            self.simpleAppend(func, var, 'getElementValue', coefficientName)
            self._alreadyExtracted.append(varName)
        
        return var

    def _makeParameterListAndGetters(self, func, tree, form, staticParameters):
        paramUFL = generateKernelParameters(tree, form)
        # Figure out which parameters to pass
        params = list(staticParameters)
        needShape = False
        needDShape = False
        
        for obj in paramUFL:
            
            if isinstance(obj, ufl.coefficient.Coefficient):
                # find which field this coefficient came from, then
                # extract from that field.
                field = findFieldFromCoefficient(self._ast, obj)
                var = self.extractCoefficient(func, field)
                params.append(var)
            
            if isinstance(obj, ufl.argument.Argument):
                needShape = True
            
            if isinstance(obj, ufl.differentiation.SpatialDerivative):
                needDShape = True

        if needShape:
            params.append(shape)
        if needDShape:
            params.append(dShape)
         
        return params

class KernelParameterGenerator(Transformer):
    """Mirrors the functionality of the kernelparametercomputer
    in cudaform.py - maybe merge at some point?"""

    def generate(self, tree, form):
        self._coefficients = []
        self._arguments = []
        self._spatialDerivatives = []

        self.visit(tree)

        form_data = form.form_data()
        formCoefficients = form_data.coefficients
        originalCoefficients = form_data.original_coefficients
        formArguments = form_data.arguments
        originalArguments = form_data.original_arguments

        parameters = []
 
        for coeff in self._coefficients:
            i = formCoefficients.index(coeff)
            originalCoefficient = originalCoefficients[i]
            parameters.append(originalCoefficient)

        for arg in self._arguments:
            i = formArguments.index(arg)
            originalArgument = originalArguments[i]
            parameters.append(originalArgument)
        
        for derivative in self._spatialDerivatives:
            subject = derivative.operands()[0]
            indices = derivative.operands()[1]
            
            if isinstance(subject, ufl.argument.Argument):
                i = formArguments.index(subject)
                originalArgument = originalArguments[i]
                parameters.append(ufl.differentiation.SpatialDerivative(originalArgument,indices))
            elif isinstance(subject, ufl.coefficient.Coefficient):
                i = formCoefficients.index(subject)
                originalCoefficient = originalCoefficients[i]
                parameters.append(originalCoefficient)

        parameters = uniqify(parameters)

        return parameters

    def expr(self, tree, *ops):
        pass

    def spatial_derivative(self, tree):
        self._spatialDerivatives.append(tree)

    def argument(self, tree):
        self._arguments.append(tree)

    def coefficient(self, tree):
        self._coefficients.append(tree)

def generateKernelParameters(tree, form):
    KPG = KernelParameterGenerator()
    return KPG.generate(tree, form)

# vim:sw=4:ts=4:sts=4:et
