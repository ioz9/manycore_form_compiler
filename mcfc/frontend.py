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


"""    Frontend. Usage:
 
    frontend.py [options] input

    Options can be: 
    
      --visualise, -v to output a visualisation of the AST
      --objvisualise  to output a deep visualisation of every ufl object
                      (warning: creates very big PDFs)
      -o:<filename>   to specify the output filename
      -b:<backend>    to specify the backend (defaults to CUDA)"""

# Python libs
import sys, getopt, pprint, ast
# MCFC libs
from visualiser import ASTVisualiser, ObjectVisualiser, ReprVisualiser
import canonicaliser
from driverfactory import drivers

def main():

    opts,args = get_options()
    keys = opts.keys()

    if len(args) > 0: 
        inputFile = args[0]
    else:
        print "No input."
        print __doc__
        sys.exit(-1)

    ast, uflObjects = canonicaliser.canonicalise(inputFile)

    if 'visualise' in keys or 'v' in keys:
        return visualise(ast, uflObjects, inputFile)

    if 'objvisualise' in keys:
        return visualise(ast, uflObjects, inputFile, True)

    if 'o' in keys:
        outputFile = opts['o']
    else:
        outputFile = inputFile[:-3] +'cu'

    if 'b' in keys:
        backend = opts['b']
    else:
        backend = "cuda"

    fd = open(outputFile, 'w')
    driver = drivers[backend]()
    driver.drive(ast, uflObjects, fd)
    fd.close()

    return 0

def testHook(inputFile, outputFile, backend = "cuda"):

    ast, uflObjects = canonicaliser.canonicalise(inputFile)
    fd = open(outputFile, 'w')
    driver = drivers[backend]()
    driver.drive(ast, uflObjects, fd)
    fd.close()
    return 0


def get_options():
    try: 
        opts, args = getopt.getopt(sys.argv[1:], "b:hvo:", ["visualise", "objvisualise"])
    except getopt.error, msg:
        print msg
        print __doc__
        sys.exit(-1)

    opts_dict = {}
    for opt in opts:
        key = opt[0].lstrip('-')
        value = opt[1]
        opts_dict[key] = value
    
    return opts_dict, args

def visualise(st, uflObjects, filename, obj=False):
    basename = filename[:-4]
    ASTVisualiser(st, basename + ".pdf")
    for i in uflObjects.keys():
        objectfile = "%s_%s.pdf" % (basename, i)
	if obj:
	    ObjectVisualiser(uflObjects[i], objectfile)
	else:
	    rep = ast.parse(repr(uflObjects[i]))
	    ReprVisualiser(rep, objectfile)
    return 0

if __name__ == "__main__":
    sys.exit(main())

# vim:sw=4:ts=4:sts=4:et
