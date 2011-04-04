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
from parameters import KernelParameterGenerator
import form
from codegeneration import Variable, Pointer, Real

statutoryParameters = [ form.localTensor, form.timestep, form.detwei ]

class Op2KernelParameterGenerator(KernelParameterGenerator):

    def _buildCoefficientParameter(self,coeff):
        name = form.buildCoefficientName(coeff)
        return Variable(name, Pointer(Real()))

    def _buildArgumentParameter(self,arg):
        name = form.buildArgumentName(arg)
        return Variable(name, Pointer(Real()))
        
    def _buildSpatialDerivativeParameter(self,argDeriv):
        name = form.buildSpatialDerivativeName(argDeriv)
        return Variable(name, Pointer(Real()))

def generateKernelParameters(tree, form):
    KPG = Op2KernelParameterGenerator()
    return KPG.generate(tree, form, statutoryParameters)

# vim:sw=4:ts=4:sts=4:et
