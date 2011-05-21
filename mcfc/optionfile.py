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

import libspud

class _OptionIterator:

    def __init__(self, path, test, return_object):
        self.p = path
        self.t = test
        self.i = 0
        self.n = libspud.number_of_children(path)
        self.o = return_object

    def __iter__(self):
        return self

    def next(self):
        if self.i >= self.n:
            raise StopIteration
        child = libspud.get_child_name(self.p,self.i)
        self.i += 1
        return self.o(self.p+'/'+child) if self.t(child) else self.next()

class Mesh:

    def __init__(self, path):
        self.path = path
        self.name = libspud.get_option(path+'/name')

        # Meshes read from file are alway P1 CG
        if libspud.have_option(path+'/from_file'):
            self.shape = 'CG'
            self.degree = 1

        # For derived meshes, check if shape or degree are overridden
        elif libspud.have_option(path+'/from_mesh'):
            # Take the inherited options as default
            basemesh = Mesh('/geometry/'+libspud.get_child_name(path+'/from_mesh',0))
            self.shape = basemesh.shape
            self.degree = basemesh.degree
            # Override continuity if set
            if libspud.have_option(path+'/from_mesh/mesh_continuity'):
                if libspud.get_option(path+'/from_mesh/mesh_continuity') == 'discontinuous':
                    self.shape = 'DG'
            # Override polynomial degree if set
            if libspud.have_option(path+'/from_mesh/mesh_shape/polynomial_degree'):
                self.degree = libspud.get_option(path+'/from_mesh/mesh_shape/polynomial_degree')

class _MeshIterator(_OptionIterator):

    def __init__(self):
        _OptionIterator.__init__(self, '/geometry', lambda s: s.startswith('mesh'), Mesh)

class MaterialPhase:

    def __init__(self, path):
        self.path = path
        self.name = libspud.get_option(path+'/name')

class _MaterialPhaseIterator(_OptionIterator):

    def __init__(self):
        _OptionIterator.__init__(self, '/', lambda s: s.startswith('material_phase'), MaterialPhase)

class Field:

    def __init__(self, path, parent = None):
        prefix = parent.name if parent else ''
        self.name = prefix + libspud.get_option(path+'/name')
        self.rank = int(libspud.get_option(path+'/rank')) if libspud.have_option(path+'/rank') else parent.rank
        for field_type in [ 'diagnostic', 'prescribed', 'prognostic', 'aliased' ]:
            if libspud.have_option(path + '/' + field_type):
                self.field_type = field_type
                break
        fieldtypepath = path + '/' + self.field_type
        # For an aliased field, store material phase and field it is
        # aliased to, come back later to assign element of the target
        # field
        if self.field_type == 'aliased':
            self.to_phase = libspud.get_option(fieldtypepath + '/material_phase_name')
            self.to_field = libspud.get_option(fieldtypepath + '/field_name')
        else:
            self.mesh = libspud.get_option(fieldtypepath+'/mesh/name') if libspud.have_option(fieldtypepath+'/mesh/name') else parent.mesh
            if self.field_type == 'prognostic':
                if libspud.have_option(fieldtypepath + '/equation/name') and libspud.get_option(fieldtypepath + '/equation/name') == 'UFL':
                    self.ufl_equation = libspud.get_option(fieldtypepath + '/equation::UFL')

class _FieldIterator(_OptionIterator):

    def __init__(self, material_phase, parent):
        _OptionIterator.__init__(self, material_phase, lambda s: s[:12] in ('scalar_field', 'vector_field', 'tensor_field'), lambda p: Field(p, parent))

def _field_gen(material_phase):
    for i in range(libspud.number_of_children(material_phase)):
        child = libspud.get_child_name(material_phase,i)
        if child[:12] in ('scalar_field', 'vector_field', 'tensor_field'):
            field = Field(material_phase+'/'+child)
            yield field
            if field.field_type != 'aliased':
                # Recursively treat subfields (if any)
                for f in _FieldIterator(material_phase+'/'+child+'/'+field.field_type, field):
                    yield f

class OptionFile:

    def __init__(self, filename):
        libspud.load_options(filename)
        self.mesh_iterator = _MeshIterator
        self.material_phase_iterator = _MaterialPhaseIterator
        self.field_iterator = _field_gen
        
# vim:sw=4:ts=4:sts=4:et