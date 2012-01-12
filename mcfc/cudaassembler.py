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
from formutils import extractCoordinates
from utilities import uniqify
# FEniCS UFL libs
import ufl.finiteelement
from ufl.differentiation import SpatialDerivative

# Variables used throughout the code generation
state            = Variable('state',              Pointer(Class('StateHolder')))

localVector      = Variable('localVector',        Pointer(Real()))
localMatrix      = Variable('localMatrix',        Pointer(Real()))
globalVector     = Variable('globalVector',       Pointer(Real()))
globalMatrix     = Variable('globalMatrix',       Pointer(Real()))
solutionVector   = Variable('solutionVector',     Pointer(Real()))

# Variables used in the run_model and initialiser functions

numEle           = Variable('numEle',            Integer())
numNodes         = Variable('numNodes',          Integer())
eleNodes         = Variable('eleNodes',          Pointer(Integer()))
nodesPerEle      = Variable('nodesPerEle',       Integer())
numValsPerNode   = Variable('numValsPerNode',    Integer())
numVectorEntries = Variable('numVectorEntries',  Integer())

# State methods that provide each of these variables, and the name of the field
# that they're taken from, if they require a field. We get things from the
# coordinate field for now, assuming that they're the same for all fields. This
# will change once we have the basic functionality working.

getters = { numEle:           ('getNumEle',                  None,        ), \
            numNodes:         ('getNumNodes',                None,        ), \
            eleNodes:         ('getEleNodes',                None,        ), \
            nodesPerEle:      ('getNodesPerEle',             'Coordinate' ), \
            numValsPerNode:   ('getValsPerNode',             None         ), \
            numVectorEntries: ('getNodesPerEle',             None         )  }

def _getTmpField(field):
    "Get the name of the temporary field on the GPU"
    return 'd'+field

class CudaAssemblerBackend(AssemblerBackend):

    def compile(self, equation):

        self._eq = equation

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

        # Build definitions
        # This comes last since it requires information from earlier steps
        definitions = self._buildHeadersAndGlobals()

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
        func.append(ArrowOp(state, call))

        # Extract accessed fields
        for rank, field in self._eq.state.accessedFields().values():
            params = [ Literal(field), Literal(rank) ]
            call = FunctionCall('extractField',params)
            func.append(ArrowOp(state, call))

        # Allocate memory and transfer to GPU
        call = FunctionCall('allocateAllGPUMemory')
        func.append(ArrowOp(state, call))

        call = FunctionCall('transferAllFields')
        func.append(ArrowOp(state, call))

        # Get num_ele, num_nodes etc
        simpleAppend(func, numEle)
        simpleAppend(func, numNodes)

        # If the coefficient is not written back to state, insert a
        # temporary field for it
        for field in self._eq.getTmpCoeffNames():
            params = [ Literal(field), Literal(self._eq.getFieldFromCoeff(field)) ]
            call = FunctionCall('insertTemporaryField',params)
            func.append(ArrowOp(state, call))

        self._sparsities = {}
        # FIXME: This will stupidly extract a sparsity for each coefficient
        # solved for (which is not necessary in the general case)
        for field in self._eq.getResultCoeffNames():

            # Get sparsity of the field we're solving for
            sparsity = Variable(field+'_sparsity', Pointer(Class('CsrSparsity')))
            call = FunctionCall('getSparsity', [ Literal(field) ])
            assignment = AssignmentOp(Declaration(sparsity), ArrowOp(state, call))
            func.append(assignment)

            matrixColmSize   = Variable(field+'_colm_size',   Integer())
            matrixFindrmSize = Variable(field+'_findrm_size', Integer())
            matrixColm       = Variable(field+'_colm',        Pointer(Integer()))
            matrixFindrm     = Variable(field+'_findrm',      Pointer(Integer()))

            # Initialise matrix_colm, findrm, etc.
            # FIXME: When you tidy this up, put these in a dict???
            matrixVars = [ matrixColm,    matrixFindrm,    matrixColmSize, matrixFindrmSize ]
            sourceFns  = ['getCudaColm', 'getCudaFindrm', 'getSizeColm',  'getSizeFindrm'   ]

            for var, source in zip(matrixVars, sourceFns):
                call = FunctionCall(source)
                rhs = ArrowOp(sparsity, call)
                assignment = AssignmentOp(var, rhs)
                func.append(assignment)

            # Remember the sparsity variable information
            self._sparsities[field] = dict(zip(['colm','findrm','colm_size','findrm_size'], matrixVars))

        # Only allocate device memory if we actually do a solve
        # FIXME: In the following we stupidly take the last coefficient solved for
        # Actually, we need to determine the maximum space required and allocate
        # that
        if len(self._eq.solves) > 0:
            # Get the number of values per node and use it to calculate the
            # size of all the local vector entries. FIXME: For now we'll use the same
            # logic as before, that we're only solving on one field, so we can
            # get these things from the last similar field that we found.
            simpleAppend(func, numValsPerNode, param=field)
            simpleAppend(func, numVectorEntries, param=field)
            
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
            buildAppendCudaMalloc(func, localVector, MultiplyOp(numEle, numVectorEntries))
            buildAppendCudaMalloc(func, localMatrix, MultiplyOp(numEle, numMatrixEntries))
            buildAppendCudaMalloc(func, globalVector, MultiplyOp(numNodes, numValsPerNode))
            buildAppendCudaMalloc(func, globalMatrix, matrixColmSize)
            buildAppendCudaMalloc(func, solutionVector,MultiplyOp(numNodes, numValsPerNode))

        return func

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
        declVars = [localVector, localMatrix, globalVector, globalMatrix, solutionVector ]
        for sparsity in self._sparsities.values():
            declVars += sparsity.values()

        for var in declVars:
            scope.append(Declaration(var))

        return scope

    def _buildRunModel(self):
     
        # List of field values that we've already extracted when building the function 
        self._alreadyExtracted = []

        dtp = Variable('dt_pointer', Pointer(Real()))
        func = FunctionDefinition(Void(), 'run_model_', [dtp])
        func.setExternC(True)
        
        # Fortran always passes by reference, so we need to dereference to get the
        # timestep.
        dt = Variable('dt', Real())
        setDt = AssignmentOp(Declaration(dt), Dereference(dtp))
        func.append(setDt)

        # Initialise some variables we need
        toBeInitialised = [ numEle, numNodes, eleNodes, nodesPerEle ]
        for var in toBeInitialised:
            simpleAppend(func, var)

        # Build the block dimension declaration. Eventually this needs to be configurable
        # (e.g. for autotuning, performance experiments.)
        blockXDim = Variable('blockXDim', Integer())
        assignment = AssignmentOp(Declaration(blockXDim), Literal(64))
        func.append(assignment)
        gridXDim = Variable('gridXDim', Integer())
        assignment = AssignmentOp(Declaration(gridXDim), Literal(128))
        func.append(assignment)

        # These parameters will be needed by every matrix/vector assembly
        # see also the KernelParameterComputer in cudaform.py.
        matrixParameters = [numEle, localMatrix, dt]
        vectorParameters = [numEle, localVector, dt]

        for count, forms in self._eq.solves.items():
            # Unpack the bits of information we want
            result = self._eq.getResultCoeffName(count)
            matrix = forms[0]
            vector = forms[1]
            sparsity = self._sparsities[result]

            # Call the matrix assembly
            # FIXME what if we have multiple integrals?
            tree = matrix.integrals()[0].integrand()
            params = self._makeParameterListAndGetters(func, tree, matrix, matrixParameters)
            matrixAssembly = CudaKernelCall(self._eq.getFormName(matrix), params, gridXDim, blockXDim)
            func.append(matrixAssembly)

            # Then call the rhs assembly
            # FIXME what if we have multiple integrals?
            tree = vector.integrals()[0].integrand()
            params = self._makeParameterListAndGetters(func, tree, vector, vectorParameters)
            vectorAssembly = CudaKernelCall(self._eq.getFormName(vector), params, gridXDim, blockXDim)
            func.append(vectorAssembly)

            # Zero the global matrix and vector
            # First we need to get numvalspernode, for the length of the global vector
            buildAppendCudaMemsetZero(func, globalMatrix, sparsity['colm_size'])
            size = MultiplyOp(stateGetter(numValsPerNode, param=result), numNodes)
            buildAppendCudaMemsetZero(func, globalVector, size)

            # Build calls to addto kernels. 
            # For the matrix
            params = [ sparsity['findrm'], sparsity['colm'], globalMatrix, eleNodes, \
                         localMatrix, numEle, nodesPerEle ]
            matrixAddto = CudaKernelCall('matrix_addto', params, gridXDim, blockXDim)
            func.append(matrixAddto)

            # And the vector
            params = [ globalVector, eleNodes, localVector, numEle, nodesPerEle ]
            vectorAddto = CudaKernelCall('vector_addto', params, gridXDim, blockXDim)
            func.append(vectorAddto)
            
            # call the solve
            params = [ sparsity['findrm'], sparsity['findrm_size'], sparsity['colm'], sparsity['colm_size'], \
                          globalMatrix, globalVector, numNodes, solutionVector ]
            cgSolve = FunctionCall('cg_solve', params)
            func.append(cgSolve)

            # expand the result
            var = self.extractCoefficient(func, result)
            params = [ var, solutionVector, eleNodes, numEle, stateGetter(numValsPerNode, param=result), nodesPerEle ]
            expand = CudaKernelCall('expand_data', params, gridXDim, blockXDim)
            func.append(expand)

        # Transfer all fields solved for on the GPU and written back to state
        for field in self._eq.getReturnedFieldNames():
            # Sanity check: only copy back fields that were solved for
            if field in self._eq.getResultCoeffNames():
                params = [ Literal(field) ]
                returnCall = FunctionCall('returnFieldToHost', params)
                func.append(ArrowOp(state, returnCall))

        return func

    def extractCoefficient(self, func, coefficientName):
        varName = coefficientName + 'Coeff'
        var = Variable(varName, Pointer(Real()))
        
        # Don't declare and extract coefficients twice
        if varName not in self._alreadyExtracted:
            # Get expanded field on device
            simpleAppend(func, var, 'getElementValue', coefficientName)
            self._alreadyExtracted.append(varName)
        
        return var

    def _makeParameterListAndGetters(self, func, tree, form, staticParameters):
        # Figure out which parameters to pass
        params = list(staticParameters)

        for coeff in form.form_data().original_coefficients:
            # Find which field this coefficient came from, then extract from
            # that field.
            # Skip the Jacobian and pass the coordinate field instead
            name = self._eq.getInputCoeffName(extractCoordinates(coeff).count())
            var = self.extractCoefficient(func, name)
            params.append(var)
         
        return params

def buildAppendCudaMemsetZero(func, base, length):
    t = base.type().getBaseType()
    size = MultiplyOp(SizeOf(t), length)
    params = [ base, Literal(0), size ]
    memset = FunctionCall('cudaMemset', params)
    func.append(memset)

def buildAppendCudaMalloc(scope, var, size):
    cast = Cast(Pointer(Pointer(Void())), AddressOfOp(var))
    sizeof = SizeOf(var.type().getBaseType())
    sizeArg = MultiplyOp(sizeof, size)
    params = [ cast, sizeArg ]
    malloc = FunctionCall('cudaMalloc', params)
    scope.append(malloc)

def stateGetter(var, provider=None, param=None):
    params = []

    if provider is None:
        provider, defaultParam = getters[var]
        if param is None:
            param = defaultParam

    if param is not None:
        params.append(Literal(param))

    call = FunctionCall(provider, params)
    return ArrowOp(state, call)

def simpleAppend(func, var, provider=None, param=None):
    """Append a variable declaration to func, without building a new
    Variable instance. The declaration is initialised by the provider
    with the parameter param, unless these are not specified. If they
    are not specified, then the getters dict is used to look one up."""

    assignment = AssignmentOp(Declaration(var), stateGetter(var, provider, param))
    func.append(assignment)

# vim:sw=4:ts=4:sts=4:et
