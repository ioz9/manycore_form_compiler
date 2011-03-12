"""
MCFC Canonicaliser. Uses the FEniCS UFL implementation to canonicalise
the input and write it out.
"""

# The UFL packages are required so that the sources execute correctly
# when they are read in
import ufl
# For indices, measures, spaces and cells pretty syntax (dx, i, j, etc...)
from ufl.objects import *
# Regular python modules
import getopt, sys, ast
# Python unparser
from unparse import Unparser
# For getting unparsed stuff to execute it
import StringIO
# If we need debugging
import pdb
# The remaining modules are part of the form compiler
import state
from symbolicvalue import SymbolicValue


def init():

    # Symbolic values that we need during the interpretation of UFL
    global c, n, dt
    n = state.TemporalIndex()
    c = state.ConstantTemporalIndex()
    dt = SymbolicValue("dt")

# Intended as the front-end interface to the parser. e.g. to use,
# call canonicalise(filename).

def canonicalise(filename):
    
    init()

    # Read in the AST
    fd = open(filename, 'r')
    chars = fd.read()
    lines = charstolines(chars)
    fd.close

    # Interpret the UFL file line by line
    for line in lines:
	UFLInterpreter(line)

# Solve needs to return an appropriate function in order for the interpretation
# to continue

def solve(M,b):
    vector = ufl.algorithms.preprocess(b)
    form_data = vector.form_data()
    element = form_data.arguments[0].element()
    return Coefficient(element)

# Action needs to do the same trick

def action(M,v):
    return ufl.formoperators.action(M,v)

def main():
    
    # Get options
    try:
	opts, args = getopt.getopt(sys.argv[1:], "ho:", ["help"])
    except getopt.error, msg:
	print msg
	print "for help use --help"
	sys.exit(2)
    
    # process options
    if len(args)>0:
        inputfile = args[0]
    outputfile = None

    for o, a in opts:
	if o in ("-h", "--help"):
	    print __doc__
	    sys.exit(0)
    
    # Run canonicaliser
    print "Canonicalising " + inputfile
    canonicalise(inputfile);

    return 0


def Coefficient(arg):
    return ufl.coefficient.Coefficient(arg)

def TestFunction(arg):
    return ufl.argument.TestFunction(arg)

def TrialFunction(arg):
    return ufl.argument.TrialFunction(arg)

def dot(arg1, arg2):
    return ufl.operators.dot(arg1,arg2)

def grad(arg):
    return ufl.operators.grad(arg)

def div(arg):
    return ufl.operators.div(arg)

def charstolines(chars):

    lines = []
    line = ''

    for char in chars:
        if not char == '\n':
	    line = line + char
	else:
	    lines.append(line)
	    line = ''
    
    return lines

class UFLInterpreter:

    def __init__(self, line):
        st = ast.parse(line)
	print '# ' + line
	self.dispatch(st)

    def dispatch(self, tree):
        if isinstance(tree, list):
	    for s in tree:
	        self.dispatch(s)
        name = "_"+tree.__class__.__name__
	
	try:
	    meth = getattr(self, name)
	except AttributeError:
            return
	meth(tree)

    def _Module(self, tree):
        for stmt in tree.body:
	    self.dispatch(stmt)
	    
    def _Assign(self, tree):

        # Since we execute code from the source file in this function,
	# all locals are prefixed with _ to prevent name collision.
 
        # Get the left-hand side of the assignment
        _lhs = tree.targets[0]
	_target = unparse(_lhs)

	# Get the AST of the right-hand side of the expression
	_rhs = tree.value
        # Evaluate the RHS of the expression
	_statement =  _target + ' = ' + unparse(_rhs)
	exec(_statement,globals())
	
	if isToBeExecuted(_lhs,_rhs):
	    # Create an assignment statement that assigns the result of 
	    # executing the statement to the LHS.
	    
	    # Execute the RHS
	    _result = eval(_target)
	    # If the result of executing the RHS is a form, we need to
	    # preprocess it
	    if isinstance(_result, ufl.form.Form):
		_result = ufl.algorithms.preprocess(_result)
	    
	    # Construct the representation that we are going to print
	    _newstatement = _target + ' = ' + repr(_result)
            
	    # If the RHS uses values from a field, we need to remember
	    # which field it is from.
	    if usesValuesFromField(_rhs):
	        _source = getSourceField(_rhs)
		_newstatement = _newstatement + ' & source(' + _source + ')'

	    print _newstatement
	# This is the case where we print the original statement, not the
	# result of executing it
	else:
	    print _statement

def isToBeExecuted(lhs,rhs):
    # We don't want to put the result of executing certain functions
    # in our output source code. Instead, we want to print them out
    # verbatim. These include solve, and action.
    
    # If the LHS is a subscript, then it is returning something into
    # state. Either the RHS is a variable, or it is a solve or
    # action, or a sum of functions. In any of these cases, we don't
    # want to print the result of executing it.
    if isinstance(lhs, ast.Subscript):
        return False

    # Anything that isn't a function is to be executed, except subscripts
    # (Because subscripts provide access to the syntax for state)
    if not isinstance(rhs, ast.Call):
        if isinstance(rhs, ast.Subscript):
	    return False
	else:
	    return True
    
    # Check if the function is one to avoid executing
    name = rhs.func.id
    if name in ['solve', 'action']:
	return False
    else:
	return True

def usesValuesFromField(st):
    # TestFunctions, TrialFunctions and Coefficients use values that
    # we need to pull from fields.
    
    # Things that aren't functions don't use values from a field
    # (well, not directly anyway, so we don't care)
    if not isinstance(st, ast.Call):
        return False
    
    name = st.func.id
    if name in ['TestFunction', 'TrialFunction', 'Coefficient']:
        return True
    else:
        return False

def getSourceField(st):
    # Get us the name of the field from which the argument's value
    # is derived.
    return st.args[0].id

def unparse(st):
    value = StringIO.StringIO()
    Unparser(st,value)
    return value.getvalue().rstrip('\n')


if __name__ == "__main__":
    sys.exit(main())
