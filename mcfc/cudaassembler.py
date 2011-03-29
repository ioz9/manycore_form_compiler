"""This module generates the code that extracts the relevant fields from
Fluidity state, transfers it to the GPU, and the run_model_ function that
executes the model for one timestep, by calling the kernels generated by
cudaform.py, and the necessary solves."""

# MCFC libs
from assembler import *
from codegeneration import *
from utilities import uniqify
# FIXME: This is referred to as mcfcstate because of the clash with the
# variable called state.
import state as mcfcstate
# FEniCS UFL libs
import ufl.finiteelement
from ufl.differentiation import SpatialDerivative
from ufl.algorithms.transformations import Transformer

# Variables used throughout the code generation
state = Variable('state', Pointer(Class('StateHolder')))

localVector = Variable('localVector', Pointer(Real()))
localMatrix = Variable('localMatrix', Pointer(Real()))
globalVector = Variable('globalVector', Pointer(Real()))
globalMatrix = Variable('globalMatrix', Pointer(Real()))
solutionVector = Variable('solutionVector', Pointer(Real()))

matrixColmSize = Variable('matrix_colm_size', Integer())
matrixFindrmSize = Variable('matrix_findrm_size', Integer())
matrixColm = Variable('matrix_colm', Pointer(Integer()))
matrixFindrm = Variable('matrix_findrm', Pointer(Integer()))

class CudaAssemblerBackend(AssemblerBackend):

    def compile(self, ast, uflObjects):
        # Build definitions
        definitions = self.buildHeadersAndGlobals(ast, uflObjects)

        # Build declarations
        declarations = GlobalScope()
        state = self.buildState()
        declarations.append(state)
        initialiser = self.buildInitialiser(ast, uflObjects)
        declarations.append(initialiser)
        finaliser = self.buildFinaliser(ast, uflObjects)
        declarations.append(finaliser)
        runModel = self.buildRunModel(ast, uflObjects)
        declarations.append(runModel)

        return definitions, declarations

 #   def buildStateType(self):
#	return Pointer(Class('StateHolder'))

    def buildState(self):
#	t = self.buildStateType()
#	state = Variable('state', t)
	decl = Declaration(state)
	return decl

    def buildInitialiser(self, ast, uflObjects):

        self._uflObjects = uflObjects

	func = FunctionDefinition(Void(), 'initialise_gpu_')
	func.setExternC(True)

	# Call the state constructor
	#state = Variable('state')
	newState = New(Class('StateHolder'))
	construct = AssignmentOp(state, newState)
	func.append(construct)
	
	# Call the state initialiser
	call = FunctionCall('initialise')
	arrow = ArrowOp(state, call)
	func.append(arrow)

	# Extract accessed fields
	accessedFields = findAccessedFields(ast)
	for field in accessedFields:
	    fieldString = '"' + field + '"'
	    params = ExpressionList([Literal(fieldString)])
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
	solveResultFields = findSolveResults(ast)
	for field in solveResultFields:
	    similarField = self.findSimilarField(field)
	    similarFieldString = '"' + similarField + '"'
	    fieldString = '"' + field + '"'
	    params = ExpressionList([Literal(fieldString), Literal(similarFieldString)])
	    call = FunctionCall('insertTemporaryField',params)
	    arrow = ArrowOp(state, call)
	    func.append(arrow)

	# Get num_ele, num_nodes etc
        numEle = self.buildAndAppendNumEle(func)
	numNodes = self.buildAndAppendNumNodes(func)

        # Get sparsity of the field we're solving for
	sparsity = Variable('sparsity', Pointer(Class('CsrSparsity')))
	# We can use the similarFieldString from earlier, since its
	# the only field we're solving on for now. When we start working
	# with solving multiple fields, this logic will need re-working.
	# (For each solve field, we should use the similar field and
	# generate a new sparsity from that)
	params = ExpressionList([Literal(similarFieldString)])
	call = FunctionCall('getSparsity', params)
	arrow = ArrowOp(state, call)
	assignment = AssignmentOp(Declaration(sparsity), arrow)
	func.append(assignment)

        # Initialise matrix_colm, findrm, etc.
	# When you tidy this up, put these in a dict???
	matrixVars = [Variable('matrix_colm'), Variable('matrix_findrm'), \
	              Variable('matrix_colm_size'), Variable('matrix_findrm_size')]
	sourceFns  = ['getCudaColm', 'getCudaFindrm', 'getSizeColm', 'getSizeFindrm']

	for var, source in zip(matrixVars, sourceFns):
	    call = FunctionCall(source)
	    rhs = ArrowOp(sparsity, call)
	    assignment = AssignmentOp(var, rhs)
	    func.append(assignment)

        # Get the number of values per node and use it to calculate the
	# size of all the local vector entries. For now we'll use the same
	# logic as before, that we're only solving on one field, so we can
	# get these things from the last similar field that we found.
        numValsPerNode = Variable('numValsPerNode', Integer())
	params = ExpressionList([Literal(similarFieldString)])
	call = FunctionCall('getValsPerNode', params)
	lhs = Declaration(numValsPerNode)
        rhs = ArrowOp(state, call)
	assignment = AssignmentOp(lhs, rhs)
	func.append(assignment)
	
        numVectorEntries = Variable('numVectorEntries', Integer())
	params = ExpressionList([Literal(similarFieldString)])
	call = FunctionCall('getNodesPerEle', params)
	lhs = Declaration(numVectorEntries)
        rhs = ArrowOp(state, call)
	assignment = AssignmentOp(lhs, rhs)
	func.append(assignment)
	
        # Now multiply numVectorEntries by numValsPerNode to get the correct
	# size of the storage required
	mult = MultiplyOp(numVectorEntries, numValsPerNode)
	assignment = AssignmentOp(numVectorEntries, mult)
	func.append(assignment)

	# The space for the local matrix storage is simply the local vector
	# storage size squared. (I'm tired, some of these comments are a bit
	# nonsensey. note to self, tidy them up.)
	numMatrixEntries = Variable('numMatrixEntries', Integer())
	rhs = MultiplyOp(numVectorEntries, numVectorEntries)
	assignment = AssignmentOp(Declaration(numMatrixEntries), rhs)
	func.append(assignment)

	# Generate Mallocs for the local matrix and vector, and the solution
	# vector.
	malloc = self.buildCudaMalloc(localVector, MultiplyOp(numEle, numVectorEntries))
	func.append(malloc)
	malloc = self.buildCudaMalloc(localMatrix, MultiplyOp(numEle, numMatrixEntries))
	func.append(malloc)
	malloc = self.buildCudaMalloc(globalVector, matrixVars[2]) # matrix_colm_size
	func.append(malloc)
	malloc = self.buildCudaMalloc(globalMatrix, MultiplyOp(numNodes, numValsPerNode))
	func.append(malloc)
	malloc = self.buildCudaMalloc(solutionVector,MultiplyOp(numNodes, numValsPerNode))
	func.append(malloc)

	return func

    def buildCudaMalloc(self, var, size):
        cast = Cast(Pointer(Pointer(Void())), AddressOfOp(var))
	sizeof = SizeOf(var.getType().getBaseType())
	sizeArg = MultiplyOp(sizeof, size)
        params = ExpressionList([cast, sizeArg])
        malloc = FunctionCall('cudaMalloc', params)
	return malloc

    def findSimilarField(self, field):
        obj = self._uflObjects[field]
	element = obj.element()
	degree = element.degree()
	
	if isinstance(element, ufl.finiteelement.FiniteElement):
	    sourceFields = mcfcstate._finiteElements
	elif isinstance(element, ufl.finiteelement.FiniteElement):
	    sourceFields = mcfcstate._vectorElements
	elif isinstance(element, ufl.finiteelement.FiniteElement):
	    sourceFields = mcfcstate._tensorElements
	else:
	    print "Oops."

	for k in sourceFields:
	    if sourceFields[k] == degree:
	        return k
	
	print "Big oops."

    def buildFinaliser(self, ast, uflObjects):
        func = FunctionDefinition(Void(), 'finalise_gpu_')
	func.setExternC(True)

        #state = Variable('state')
	delete = Delete(state)
	func.append(delete)

	return func

    def buildHeadersAndGlobals(self, ast, uflObjects):
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

    def simpleBuildAndAppend(self, func, var, t, provider, param=None):
        """Build and append a variable declaration to func. It initialises
        itself by the return value from the provided state method. A string
	parameter can also be passed to the state method (e.g. to choose a 
	different field"""
        params = ExpressionList()
        if param is not None:
	     paramString = Literal('"'+param+'"')
	     params.append(paramString)

        #state = Variable('state')
	varAst = Variable(var, t)
	call = FunctionCall(provider, params)
	arrow = ArrowOp(state, call)
	assignment = AssignmentOp(Declaration(varAst), arrow)
	func.append(assignment)
	return varAst

    def buildAndAppendNumEle(self, func):
	return self.simpleBuildAndAppend(func, 'numEle', Integer(), 'getNumEle')

    def buildAndAppendNumNodes(self, func):
	return self.simpleBuildAndAppend(func, 'numNodes', Integer(), 'getNumNodes')

    def buildAndAppendDetwei(self, func):
	return self.simpleBuildAndAppend(func, 'detwei', Pointer(Real()), 'getDetwei')

    def buildAndAppendEleNodes(self, func):
	return self.simpleBuildAndAppend(func, 'eleNodes', Pointer(Integer()), 'getEleNodes')

    def buildAndAppendCoordinates(self, func):
	return self.simpleBuildAndAppend(func, 'coordinates', Pointer(Real()), 'getCoordinates')

    def buildAndAppendDn(self, func):
	return self.simpleBuildAndAppend(func, 'dn', Pointer(Real()), 'getReferenceDn')
        
    def buildAndAppendQuadWeights(self, func):
	return self.simpleBuildAndAppend(func, 'quadWeights', Pointer(Real()), 'getQuadWeights')

    def buildAndAppendNDim(self, func):
        return self.simpleBuildAndAppend(func, 'nDim', Integer(), 'getDimension', 'Coordinate')

    def buildAndAppendNQuad(self, func):
        return self.simpleBuildAndAppend(func, 'nQuad', Integer(), 'getNumQuadPoints', 'Coordinate')

    def buildAndAppendNodesPerEle(self, func):
        return self.simpleBuildAndAppend(func, 'nodesPerEle', Integer(), 'getNodesPerEle', 'Coordinate')

    def buildAndAppendShape(self, func):
        return self.simpleBuildAndAppend(func, 'shape', Pointer(Real()), 'getBasisFunction', 'Coordinate')

    def buildAndAppendDShape(self, func):
        return self.simpleBuildAndAppend(func, 'dShape', Pointer(Real()), 'getBasisFunctionDerivative', 'Coordinate')

    def buildRunModel(self, ast, uflObjects):
     
        # List of field values that we've already extracted when building the function 
        self._alreadyExtracted = []

	dt = Variable('dt', Real())
	params = ParameterList([dt])
	func = FunctionDefinition(Void(), 'run_model_', params)
	func.setExternC(True)

        numEle = self.buildAndAppendNumEle(func)
	numNodes = self.buildAndAppendNumNodes(func)
        detwei = self.buildAndAppendDetwei(func)
        eleNodes = self.buildAndAppendEleNodes(func)
	coordinates = self.buildAndAppendCoordinates(func)
	dn = self.buildAndAppendDn(func)
	quadWeights = self.buildAndAppendQuadWeights(func)

        # We get these from the coordinate field for now,
	# assuming that everything's the same for all fields.
	nDim = self.buildAndAppendNDim(func)
	nQuad = self.buildAndAppendNQuad(func)
        nodesPerEle = self.buildAndAppendNodesPerEle(func)
	shape = self.buildAndAppendShape(func)
        dShape = self.buildAndAppendDShape(func)

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
	params = ExpressionList([blockXDim, nDim, nodesPerEle])
	t2pShMemSizeCall = FunctionCall('t2p_shmemsize', params)
	assignment = AssignmentOp(Declaration(shMemSize), t2pShMemSizeCall)
	func.append(assignment)

        # Create a call to transform_to_physical.
        paramList = [coordinates, dn, quadWeights, dShape, detwei, numEle, nDim, nQuad, nodesPerEle]
	params = ExpressionList(paramList)
	t2pCall = CudaKernelCall('transform_to_physical', params, gridXDim, blockXDim, shMemSize)
	func.append(t2pCall)

        # These parameters will be needed by every matrix/vector assembly
	# see also the KernelParameterComputer in cudaform.py.
	matrixParameters = [localMatrix, numEle, dt, detwei]
	vectorParameters = [localVector, numEle, dt, detwei]

        # Traverse the AST looking for solves
        solves = findSolves(ast)
	
	for solve in solves:
	    # Unpack the bits of information we want
	    result = str(solve.getChild(0))
	    solveNode = solve.getChild(1)
	    matrix = solveNode.getChild(0)
	    vector = solveNode.getChild(1)
	    
	    # Call the matrix assembly
            form = uflObjects[str(matrix)]
	    tree = form.integrals()[0].integrand()
	    params = self.makeParameterListAndGetters(func, ast, tree, form, matrixParameters, shape, dShape)
	    matrixAssembly = CudaKernelCall(str(matrix), params, gridXDim, blockXDim)
	    func.append(matrixAssembly)

	    # Then call the rhs assembly
	    form = uflObjects[str(vector)]
	    tree = form.integrals()[0].integrand()
	    params = self.makeParameterListAndGetters(func, ast, tree, form, vectorParameters, shape, dShape)
            vectorAssembly = CudaKernelCall(str(vector), params, gridXDim, blockXDim)
	    func.append(vectorAssembly)

	    # call the addtos

            # First we need to zero the global matrix
	    sizeOfGlobalMatrix = MultiplyOp(SizeOf(Real()), matrixColmSize)
	    params = ExpressionList([globalMatrix, Literal(0), sizeOfGlobalMatrix])
	    zeroMatrix = FunctionCall('cudaMemset', params)
	    func.append(zeroMatrix)

	    # and zero the global vector
	    # need to get numvalspernode
	    #sizeOfGlobalVector = MultiplyOp(SizeOf(Real()), matrixColmSize)
	    #params = ExpressionList([globalMatrix, Literal(0), sizeOfGlobalMatrix])
	    #zeroMatrix = FunctionCall('cudaMemset', params)
	    #func.append(zeroMatrix)

	    # call the solve

	    # expand the result

	# Traverse the AST looking for fields that need to return to the host
	
	    # Found one? ok, call the method to return it.

	return func

    def makeParameterListAndGetters(self, func, ast, tree, form, staticParameters, shape, dShape):
	paramUFL = generateKernelParameters(tree, form)
	# Figure out which parameters to pass
	params = ExpressionList(list(staticParameters))
	needShape = False
	needDShape = False
	for obj in paramUFL:
	    if isinstance(obj, ufl.coefficient.Coefficient):
		# find which field this coefficient came from
		field = findFieldFromCoefficient(ast, obj)
		varName = field+'Coeff'
		# Don't declare and get things twice
		if varName not in self._alreadyExtracted:
		    var = self.simpleBuildAndAppend(func, varName, Pointer(Real()), 'getElementValue', field)
		    self._alreadyExtracted.append(varName)
		# Add to parameters
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


