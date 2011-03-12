"""Backends.py - provides the C++/CUDA/OpenCL ASTs and unparsing"""

class BackendASTNode:
    pass

class Subscript(BackendASTNode):
    
    def __init__(self, base, offset):
        self._base = base
	self._offset = offset

    def unparse(self):
        base = self._base.unparse()
        offset = self._offset.unparse()
        code = '%s[%s]' % (base, offset)
	return code

class NullExpression(BackendASTNode):
    
    def unparse(self):
        return ''

class Variable(BackendASTNode):
    
    def __init__(self, name, t=None):
        self._name = name
	
	if t is None:
	    self._t = Type()
	else:
	    self._t = t

    def unparse(self):
        code = self._name
	return code

    def unparse_declaration(self):
        name = self._name
	t = self._t.unparse()
	code = '%s %s' % (t, name)
	return code

class Literal(BackendASTNode):

    def __init__(self, value):
        self._value = str(value)

    def unparse(self):
        code = self._value
	return code

class ForLoop(BackendASTNode):
    
    def __init__(self, init, test, inc, body=None):
        self._init = init
	self._test = test
	self._inc = inc
	if body is None:
	    self._body = Scope()
	else:
	    self._body = body

    def append(self, statement):
        self._body.append(statement)

    def prepend(self, statement):
        self._body.prepend(statement)

    def body(self):
        return self._body

    def unparse(self):
        init = self._init.unparse(False)
	test = self._test.unparse(False)
	inc = self._inc.unparse()
	body = self._body.unparse()
        code = 'for(%s; %s; %s)\n' % (init, test, inc)
	code = code + body
	return code

class ParameterList(BackendASTNode):

    def __init__(self, params):
        self._params = params

    def unparse(self):
        code = "("
	code = code + self._params[0].unparse_declaration()
	for p in self._params[1:]:
	    code = code + ", " + p.unparse_declaration()
	code = code + ")"
	return code

class FunctionDefinition(BackendASTNode):

    def __init__(self, t, name, params, body):
        self._t = t
	self._name = name
	self._params = params
	self._body = body

    def unparse(self):
        t = self._t.unparse()
        params = self._params.unparse()
	body = self._body.unparse()
        code = '%s %s%s\n%s' % (t, self._name, params, body)
	return code

class Scope(BackendASTNode):

    def __init__(self, statements=None):
        if statements is None:
	    self._statements = []
	else:
	    self._statements = statements

    def append(self, statement):
        self._statements.append(statement)

    def prepend(self, statement):
        self._statements.insert(0, statement)

    def find(self, matches):
        for s in self._statements:
	    if matches(s):
	        return s

    def unparse(self):
        indent = getIndent()
	code = '%s{' % (indent)
	indent = incIndent()
	for s in self._statements:
	    code = code + '\n' + indent + s.unparse() + ';'
	indent = decIndent()
	code = code + '\n' + indent + '}'
	return code

class BinaryOp(BackendASTNode):

    def __init__(self, lhs, rhs, op):
        self._lhs = lhs
	self._rhs = rhs
	self._op = op

    def unparse(self, bracketed=True):
        lhs = self._lhs.unparse()
	rhs = self._rhs.unparse()
        code = '%s %s %s' % (lhs, self._op, rhs)
	if bracketed:
	    code = '(' + code + ')'
	return code

class MultiplyOp(BinaryOp):

    def __init__(self, lhs, rhs):
        BinaryOp.__init__(self, lhs, rhs, '*')

class AddOp(BinaryOp):

    def __init__(self, lhs, rhs):
        BinaryOp.__init__(self, lhs, rhs, '+')

class AssignmentOp(BinaryOp):

    def __init__(self, lhs, rhs):
        BinaryOp.__init__(self, lhs, rhs, '=')

class PlusAssignmentOp(BinaryOp):

    def __init__(self, lhs, rhs):
        BinaryOp.__init__(self, lhs, rhs, '+=')

class LessThanOp(BinaryOp):

    def __init__(self, lhs, rhs):
        BinaryOp.__init__(self, lhs, rhs, '<')

class PlusPlusOp(BackendASTNode):

    def __init__(self, expr):
        self._expr = expr

    def unparse(self):
        expr = self._expr.unparse()
        code = '%s++' % (expr)
	return code

# Types

class Type:
    
    def unparse(self):
        return ""

class Void(Type):
    
    def unparse(self):
        return "void"

class Real(Type):

    def unparse(self):
        return "double"

class Integer(Type):

    def unparse(self):
        return "int"

class Pointer(Type):

    def __init__(self, base):
        self._base = base

    def unparse(self):
        base = self._base.unparse()
	code = '%s*' % (base)
	return code

# Utility functions

def buildSimpleForLoop(indVarName, upperBound):
    var = Variable(indVarName, Integer())
    init = AssignmentOp(var, Literal(0))
    test = LessThanOp(var, Literal(upperBound))
    inc = PlusPlusOp(var)
    ast = ForLoop(init, test, inc)
    return ast

# Unparser-specific functions

indentLevel = 0
indentSize = 2

def getIndent():
    return ' ' * indentLevel

def incIndent():
    global indentLevel
    indentLevel = indentLevel + indentSize
    return getIndent()

def decIndent():
    global indentLevel
    indentLevel = indentLevel - indentSize
    return getIndent()
    
