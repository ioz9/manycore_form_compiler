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

from expression import *
from cudaparameters import numElements

import ufl.differentiation

# Variables

threadCount = Variable("THREAD_COUNT")
threadId = Variable("THREAD_ID")

# The ElementIndex is here and not form.py because not all backends need
# an element index (e.g. OP2).

class ElementIndex:

    def extent(self):
        return numElements

    def name(self):
        return "i_ele"

def buildElementLoop():
    indVarName = ElementIndex().name()
    var = Variable(indVarName, Integer())
    init = InitialisationOp(var, threadId)
    test = LessThanOp(var, numElements)
    inc = PlusAssignmentOp(var, threadCount)
    ast = ForLoop(init, test, inc)
    return ast

def buildSubscript(variable, indices):
    """Given a list of indices, return an AST that computes
    the offset into the given array using those indices. The order is
    important."""

    # Start our expression with the first index
    name = indices[0].name()
    offset = Variable(name)
    
    # Compute the expression for all indices
    for v in range(1,len(indices)):
        subindices = indices[:v]
        name = indices[v].name()
        expr = Variable(name)
        
        # Find the correct offset for this index
        for u in range(len(subindices)):
            multiplier = subindices[u].extent()
            expr = MultiplyOp(multiplier, expr)
        offset = AddOp(offset, expr)
    
    return Subscript(variable, offset)

def buildMultiArraySubscript(variable, indices):
    """Given a list of indices, return an AST of the variable
    subscripted by the indices as if it were a multidimensional
    array."""

    indexList = []
    for i in indices:
        variable = Subscript(variable, Variable(i.name()))

    return variable

# Expression builders

class CudaExpressionBuilder(ExpressionBuilder):

    def buildSubscript(self, variable, indices):
        return buildSubscript(variable, indices)

    def buildMultiArraySubscript(self, variable, indices):
        return buildMultiArraySubscript(variable, indices)

    def subscript(self, tree, depth=None):
        meth = getattr(self, "subscript_"+tree.__class__.__name__)
        if depth is None:
            return meth(tree)
        else:
            return meth(tree, depth)

    def subscript_Argument(self, tree):
        # Build the subscript based on the argument count
        count = tree.count()
        indices = []
        for dimIndices in self._indexStack:
            indices.extend(dimIndices)
        indices = indices + [self._formBackend.buildBasisIndex(count), self._formBackend.buildGaussIndex()]
        return indices

    def subscript_SpatialDerivative(self,tree,dimIndices):
        # Build the subscript based on the argument count and the
        # indices
        operand, _ = tree.operands()
        count = operand.count()

        if isinstance(operand, ufl.argument.Argument):
            indices = [ ElementIndex()]
            indices.extend(dimIndices)
            indices = indices + [ self._formBackend.buildGaussIndex(),
                                  self._formBackend.buildBasisIndex(count) ]
        elif isinstance(operand, ufl.coefficient.Coefficient):
            indices = [ self._formBackend.buildGaussIndex() ]
            indices.extend(dimIndices)

        return indices

    def subscript_LocalTensor(self, form):
        form_data = form.form_data()
        rank = form_data.rank
        
        # First index is the element index
        indices = [ElementIndex()]

        # One rank index for each rank
        for r in range(rank):
            indices.append(self._formBackend.buildBasisIndex(r))

        return indices

    def subscript_CoeffQuadrature(self, coeff):
        # Build the subscript based on the rank
        indices = [self._formBackend.buildGaussIndex()]
        rank = coeff.rank()

        if isinstance(coeff, SpatialDerivative):
            rank = rank + 1 

        if rank > 0:
            dimIndices = self._indexStack.peek()
            if len(dimIndices) != rank:
                raise RuntimeError("Number of indices does not match rank of coefficient. %d vs %d." % (len(dimIndices), rank))
            indices.extend(dimIndices)
        
        return indices

class CudaQuadratureExpressionBuilder(QuadratureExpressionBuilder):

    def buildSubscript(self, variable, indices):
        return buildSubscript(variable, indices)

    def subscript(self, tree):
        rank = tree.rank()
        indices = [ ElementIndex() ]
        for r in range(rank):
            index = self._formBackend.buildDimIndex(r)
            indices.append(index)
        indices.append(self._formBackend.buildBasisIndex(0))
        return indices

    def subscript_argument(self, tree):
        # The count of the basis function induction variable is always
        # 0 in the quadrature loops (i.e. i_r_0)
        indices = [self._formBackend.buildBasisIndex(0), 
                   self._formBackend.buildGaussIndex()]
        return indices

    def subscript_spatial_derivative(self, tree):
        # The count of the basis function induction variable is always
        # 0 in the quadrature loops (i.e. i_r_0), and only the first dim
        # index should be used to subscript the derivative (I think).
        indices = [ ElementIndex(),
                    self._formBackend.buildDimIndex(0),
                    self._formBackend.buildGaussIndex(),
                    self._formBackend.buildBasisIndex(0) ]
        return indices

# vim:sw=4:ts=4:sts=4:et
