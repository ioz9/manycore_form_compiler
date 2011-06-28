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


# MCFC libs
from form import *
from cudaparameters import CudaKernelParameterGenerator, numElements, statutoryParameters
from cudaexpression import CudaExpressionBuilder, CudaQuadratureExpressionBuilder, ElementIndex

# Variables

threadCount = Variable("THREAD_COUNT")
threadId = Variable("THREAD_ID")

class CudaFormBackend(FormBackend):

    def __init__(self):
        FormBackend.__init__(self)
        self._expressionBuilder = CudaExpressionBuilder(self)
        self._quadratureExpressionBuilder = CudaQuadratureExpressionBuilder(self)
        self._indexSumCounter = IndexSumCounter()

    def compile(self, name, form):

        # FIXME what if we have multiple integrals?
        integrand = form.integrals()[0].integrand()
        form_data = form.form_data()
        assert form_data, "Form has no form data attached!"
        rank = form_data.rank
        
        # Get parameter list for kernel declaration.
        formalParameters, actualParameters = self._buildKernelParameters(integrand, form)
        # Attach list of formal and actual kernel parameters to form data
        form.form_data().formalParameters = formalParameters
        form.form_data().actualParameters = actualParameters

        # Build the loop nest
        loopNest = self.buildLoopNest(form)

        # Initialise the local tensor values to 0
        initialiser = self.buildLocalTensorInitialiser(form)
        depth = rank + 1 # Rank + element loop
        loopBody = getScopeFromNest(loopNest, depth)
        loopBody.prepend(initialiser)

        # Insert the expressions into the loop nest
        partitions = findPartitions(integrand)
        for (tree, depth) in partitions:
            expression = self.buildExpression(form, tree)
            exprDepth = depth + rank + 2 # 2 = Ele loop + gauss loop
            loopBody = getScopeFromNest(loopNest, exprDepth)
            loopBody.prepend(expression)

        # Build the function with the loop nest inside
        statements = [loopNest]
        body = Scope(statements)
        kernel = FunctionDefinition(Void(), name, formalParameters, body)
        
        # If there's any coefficients, we need to build a loop nest
        # that calculates their values at the quadrature points
        if form_data.num_coefficients > 0:
            declarations = self.buildCoeffQuadDeclarations(form)
            quadLoopNest = self.buildQuadratureLoopNest(form)
            loopNest.prepend(quadLoopNest)
            for decl in declarations:
                loopNest.prepend(decl)
        
        # Make this a Cuda kernel.
        kernel.setCudaKernel(True)
        return kernel

    def _buildKernelParameters(self, tree, form):
        KPG = CudaKernelParameterGenerator()
        return KPG.generate(tree, form, statutoryParameters)

    def buildCoeffQuadDeclarations(self, form):
        # The FormBackend's list of variables to declare is
        # fine, but we want them to be __shared__
        declarations = FormBackend.buildCoeffQuadDeclarations(self, form)
        for decl in declarations:
            decl.setCudaShared(True)
        return declarations

    def buildQuadratureLoopNest(self, form):
        
        # FIXME what if we have multiple integrals?
        integrand = form.integrals()[0].integrand()
        coefficients, spatialDerivatives = self._coefficientUseFinder.find(integrand)

        # Outer loop over gauss points
        indVar = self.buildGaussIndex().name()
        gaussLoop = buildSimpleForLoop(indVar, self.numGaussPoints)

        # Build a loop nest for each coefficient containing expressions
        # to compute its value
        for coeff in coefficients:
            rank = coeff.rank()
            self.buildCoefficientLoopNest(coeff, rank, gaussLoop)

        for spatialDerivative in spatialDerivatives:
            operand = spatialDerivative.operands()[0]
            rank = operand.rank() + 1
            self.buildCoefficientLoopNest(spatialDerivative, rank, gaussLoop)

        return gaussLoop

    def buildCoefficientLoopNest(self, coeff, rank, scope):

        loop = scope

        # Build loop over the correct number of dimensions
        for r in range(rank):
            indVar = self.buildDimIndex(r).name()
            dimLoop = buildSimpleForLoop(indVar, self.numDimensions)
            loop.append(dimLoop)
            loop = dimLoop

        # Add initialiser here
        initialiser = self.buildCoeffQuadratureInitialiser(coeff)
        loop.append(initialiser)

        # One loop over the basis functions
        indVar = self.buildBasisIndex(0).name()
        basisLoop = buildSimpleForLoop(indVar, self.numNodesPerEle)
        loop.append(basisLoop)
    
        # Add the expression to compute the value inside the basis loop
        computation = self.buildQuadratureExpression(coeff)
        basisLoop.append(computation)


    def buildLoopNest(self, form):
        form_data = form.form_data()
        rank = form_data.rank
        # FIXME what if we have multiple integrals?
        integrand = form.integrals()[0].integrand()

        # The element loop is the outermost loop
        loop = self.buildElementLoop()
        outerLoop = loop

        # Build the loop over the first rank, which always exists
        indVarName = self.buildBasisIndex(0).name()
        basisLoop = buildSimpleForLoop(indVarName, self.numNodesPerEle)
        loop.append(basisLoop)
        loop = basisLoop

        # Add another loop for each rank of the form (probably no
        # more than one more... )
        for r in range(1,rank):
            indVarName = self.buildBasisIndex(r).name()
            basisLoop = buildSimpleForLoop(indVarName, self.numNodesPerEle)
            loop.append(basisLoop)
            loop = basisLoop
        
        # Add a loop for the quadrature
        indVarName = self.buildGaussIndex().name()
        gaussLoop = buildSimpleForLoop(indVarName, self.numGaussPoints)
        loop.append(gaussLoop)
        loop = gaussLoop

        # Determine how many dimension loops we need by inspection.
        # We count the nesting depth of IndexSums to determine
        # how many dimension loops we need.
        numDimLoops = self._indexSumCounter.count(integrand)

        # Add loops for each dimension as necessary. 
        for d in range(numDimLoops):
            indVarName = self.buildDimIndex(d).name()
            dimLoop = buildSimpleForLoop(indVarName, self.numDimensions)
            loop.append(dimLoop)
            loop = dimLoop

        # Hand back the outer loop, so it can be inserted into some
        # scope.
        return outerLoop

    def buildElementLoop(self):
        indVarName = ElementIndex().name()
        var = Variable(indVarName, Integer())
        init = InitialisationOp(var, threadId)
        test = LessThanOp(var, numElements)
        inc = PlusAssignmentOp(var, threadCount)
        ast = ForLoop(init, test, inc)
        return ast

# vim:sw=4:ts=4:sts=4:et
