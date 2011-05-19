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

import ufl.finiteelement
import libspud

def get_all_children(optionpath, test = lambda s: True):
    allchildren = [libspud.get_child_name(optionpath,i) for i in range(libspud.number_of_children(optionpath))]
    allchildren = [optionpath+'/'+s for s in allchildren if test(s)]
    return allchildren

class UflState:

    def __init__(self):
        self.scalarfields = {}
        self.vectorfields = {}
        self.tensorfields = {}

    def __getitem__(self,key):

        if isinstance(key,int):
            if key == 0:
                return self.scalarfields
            elif key == 1:
                return self.vectorfields
            elif key == 2:
                return self.tensorfields
            else:
                raise IndexErrror

        else:
            raise TypeErrror

    def __repr__(self):
        return str(self.scalarfields)+', '+str(self.vectorfields)+', '+str(self.tensorfields)

    def insert_field(self, field, rank, options):
        self[rank][field] = ufl.finiteelement.FiniteElement(options[0], "triangle", options[1])

class OptionFileParser:

    def __init__(self):
        self.element_types = {}
        self.states = {}

    def parse(self, filename):
        libspud.load_options(filename)
        self._build_states()

    def _build_states(self):
        # Build dictionary of element types for meshes
        meshpaths = get_all_children('/geometry', lambda s: s.startswith('mesh'))
        self.element_types = {}
        # Get shape and degree for each mesh
        for mesh in meshpaths:
            name = libspud.get_option(mesh+'/name')

            # Meshes read from file are alway P1 CG
            if libspud.have_option(mesh+'/from_file'):
                self.element_types[name] = ('CG',1)

            # For derived meshes, check if shape or degree are overridden
            elif libspud.have_option(mesh+'/from_mesh'):
                # Take the inherited options as default
                mesh_options = self.element_types[libspud.get_option(mesh+'/from_mesh/mesh/name')]
                shape = mesh_options[0]
                degree = mesh_options[1]
                # Override continuity if set
                if libspud.have_option(mesh+'/from_mesh/mesh_continuity'):
                    if libspud.get_option(mesh+'/from_mesh/mesh_continuity') == 'discontinuous':
                        shape = 'DG'
                # Override polynomial degree if set
                if libspud.have_option(mesh+'/from_mesh/mesh_shape/polynomial_degree'):
                    degree = libspud.get_option(mesh+'/from_mesh/mesh_shape/polynomial_degree')
                self.element_types[name] = (shape,degree)

        # Build dictionary of material phases
        materialphasepaths = get_all_children('/', lambda s: s.startswith('material_phase'))
        aliased_fields = []
        for phase in materialphasepaths:
            phasename = libspud.get_option(phase+'/name')
            # Build state (dictionary of fields)
            state = UflState()
            fieldpaths = get_all_children(phase, lambda s: s[7:].startswith('field'))
            for field in fieldpaths:
                name = libspud.get_option(field+'/name')
                rank = int(libspud.get_option(field+'/rank'))
                fieldtype = libspud.get_child_name(field,2)
                fieldtypepath = field + '/' + fieldtype
                # For an aliased field, store material phase and field it is
                # aliased to, come back later to assign element of the target
                # field
                if fieldtype == 'aliased':
                    aliased_fields.append(
                            {
                                'rank': rank,
                                'from': {'phase': phasename, 'field': name},
                                'to': {
                                    'phase': libspud.get_option(fieldtypepath + '/material_phase_name'),
                                    'field': libspud.get_option(fieldtypepath + '/field_name') }
                            }
                        )
                else:
                    mesh = libspud.get_option(fieldtypepath+'/mesh/name')
                    state.insert_field(name, rank, self.element_types[mesh])
                    # Recurse to subfields if any
                    subfieldpaths = get_all_children(fieldtypepath, lambda s: s[7:].startswith('field'))
                    for subfield in subfieldpaths:
                        childname = name + libspud.get_option(subfield+'/name')
                        childrank = libspud.get_option(subfield+'/rank')
                        state.insert_field(childname, rank, self.element_types[mesh])
            self.states[phasename] = state

        # Resolve aliased fields
        for alias in aliased_fields:
            self.states[alias['from']['phase']][alias['rank']][alias['from']['field']] = self.states[alias['to']['phase']][alias['rank']][alias['to']['field']]

if __name__ == "__main__":
    import sys
    filename = sys.argv[1]
    p = OptionFileParser()
    p.parse(filename)
    print 'element types: ', p.element_types
    print 'states: ', p.states
        
# vim:sw=4:ts=4:sts=4:et