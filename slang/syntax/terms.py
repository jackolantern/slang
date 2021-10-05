import types as pytypes
import logging
from typing import Optional, List

from . import Position
from ..pretty import pretty


class Node:
    def __init__(self, position: Optional[Position]):
        self.position = position


class Statement(Node):
    pass


class Expression(Node):
    def is_value(self):
        return False

    def simplify(self):
        return self


class Bang(Statement):
    def __init__(self, expression, position=None):
        assert expression is not None
        super().__init__(position)
        self.expression = expression

    def _repr_pretty_(self, p, cycle):
        assert not cycle
        p.text("!")
        p.pretty(self.expression)


class Import(Statement):
    def __init__(self, path, program, position=None):
        assert path is not None
        assert program is not None
        super().__init__(position)
        self.path = path
        self.program = program


class Assignment(Statement):
    def __init__(self, name, expression, position=None):
        assert name is not None, f"Name: {name}"
        assert expression is not None, f"Name - Expression: {name} - {expression}"
        super().__init__(position)
        self.name = name
        self.expression = expression

    def _repr_pretty_(self, p, cycle):
        p.text("let ")
        p.text(self.name)
        p.text(" = ")
        p.pretty(self.expression)
        p.text(";")


class Block(Expression):
    def __init__(self, statements, expression, position=None):
        assert statements is not None
        assert expression is not None
        super().__init__(position)
        self.expression = expression
        self.statements = statements

    def _repr_pretty_(self, p, cycle):
        assert not cycle
        p.text("{")
        with p.group(4):
            p.breakable()
            for s in self.statements:
                p.pretty(s)
                p.breakable()
            p.pretty(self.expression)
        p.breakable()
        p.text("}")


class Reference(Expression):
    def __init__(self, name, value, position=None):
        assert name is not None
        assert value is not None
        super().__init__(position)
        self.name = name
        self.value = value

    def copy(self):
        return Reference(self.name, self.value)

    def substitute(self, pairs, threshold):
        return Reference(self.name, self.value.substitute(pairs, threshold))

    def _repr_pretty_(self, p, cycle):
        assert not cycle
        if p.verbose:
            p.pretty(self.value)
        else:
            p.text(self.name)


class This(Reference):
    def __init__(self, value, position=None):
        super().__init__("this", value, position)

    def simplify(self):
        return self

    def substitute(self, pairs, threshold):
        return self

    def __repr__(self):
        return "this"


class UnaryOperation(Expression):
    def __init__(self, op, expression, position=None):
        assert op is not None
        assert expression is not None
        super().__init__(position)
        self.op = op
        self.expression = expression

    def substitute(self, pairs, threshold):
        return UnaryOperation(self.op, self.expression.substitute(pairs, threshold))

    def simplify(self):
        expression = self.expression.simplify()
        if not expression.is_value():
            return UnaryOperation(self.op, expression, self.position)
        if self.op == "+":
            return expression
        elif self.op == "-":
            return -expression
        elif self.op == "~":
            return ~expression
        elif self.op == "!":
            return not expression
        raise Exception(f"Unknown unary operator `{self.op}`.")

    def _repr_pretty_(self, p, cycle):
        assert not cycle
        p.text(self.op)
        p.pretty(self.expression)


class BinaryOperation(Expression):
    def __init__(self, op, lhs, rhs, position=None):
        assert op is not None
        assert lhs is not None
        assert rhs is not None
        super().__init__(position)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

    def simplify(self):
        lhs = self.lhs.simplify()
        rhs = self.rhs.simplify()
        if not (lhs.is_value() and rhs.is_value()):
            return BinaryOperation(self.op, lhs, rhs, self.position)
        if self.op == "+":
            return lhs + rhs
        elif self.op == "-":
            return lhs - rhs
        elif self.op == "*":
            return lhs * rhs
        elif self.op == "/":
            return lhs / rhs
        elif self.op == "^":
            return lhs ** rhs
        elif self.op == "%":
            return lhs % rhs
        elif self.op == "==":
            return lhs == rhs
        elif self.op == "<":
            return lhs < rhs
        elif self.op == ">":
            return lhs > rhs
        elif self.op == "<=":
            return lhs <= rhs
        elif self.op == ">=":
            return lhs >= rhs
        raise Exception(f"Unknown binary operator `{self.op}`.")

    def substitute(self, pairs, threshold):
        return BinaryOperation(
            self.op,
            self.lhs.substitute(pairs, threshold),
            self.rhs.substitute(pairs, threshold),
        )

    def _repr_pretty_(self, p, cycle):
        assert not cycle
        with p.group(2, "(", ")"):
            p.pretty(self.lhs)
            p.text(" ")
            p.text(self.op)
            p.text(" ")
            p.pretty(self.rhs)


class Bound(Expression):
    def __init__(self, name, index, position=None):
        assert name is not None
        assert index is not None
        super().__init__(position)
        self.name = name
        self.index = index

    def substitute(self, pairs, threshold):
        if self.index < threshold:
            return self
        index = self.index - threshold
        (_, value) = pairs[index]
        return value

    def _repr_pretty_(self, p, cycle):
        assert not cycle
        if p.verbose:
            p.text(f"<{self.name} : {self.index}>")
        else:
            p.text(self.name)


class Variable(Expression):
    def __init__(self, name, position=None):
        assert name is not None
        super().__init__(position)
        self.name = name

    def substitute(self, pairs, threshold):
        return self

    def _repr_pretty_(self, p, cycle):
        assert not cycle
        if p.verbose:
            p.text("var:")
            p.text(self.name)
        else:
            p.text(self.name)


class IfThenElse(Expression):
    def __init__(self, test, true, false, position: Optional[Position] = None):
        assert test is not None
        assert true is not None
        assert false is not None
        super().__init__(position)
        self.test = test
        self.true = true
        self.false = false

    def substitute(self, pairs, threshold):
        test = self.test.substitute(pairs, threshold)
        true = self.true.substitute(pairs, threshold)
        false = self.false.substitute(pairs, threshold)
        return IfThenElse(test, true, false)

    def _repr_pretty_(self, p, cycle):
        assert not cycle
        p.text("if ")
        p.pretty(self.test)
        p.breakable()
        p.text("then ")
        p.pretty(self.true)
        p.breakable()
        p.text("else ")
        p.pretty(self.false)


class FunctionDef(Expression):
    def __init__(self, parameters, body, position: Optional[Position] = None):
        assert body is not None
        assert parameters is not None
        super().__init__(position)
        self.body = body
        self.parameters = parameters

    def is_value(self):
        return True

    def is_builtin(self):
        t = type(self.body)
        return (
            t in (pytypes.FunctionType, pytypes.MethodType)
            or t.__name__ == "builtin_function_or_method"
        )

    def _repr_pretty_(self, p, cycle):
        p.text("function(")
        for idx, param in enumerate(self.parameters):
            if idx != 0:
                p.text(", ")
            p.text(param.name)
            if param.typ:
                p.text(" : ")
                p.pretty(param.typ)
        p.text(") ")
        p.pretty(self.body)


class FunctionRef(FunctionDef):
    def __eq__(self, other):
        return (
            type(self) == type(other)
            and self.parameters == other.parameters
            and self.body == other.body
        )

    def __hash__(self):
        return hash(tuple(p.name for p in self.parameters))

    def call(self, runner, arguments):
        an = len(arguments)
        pn = len(self.parameters)
        if an != pn:
            logging.error(
                f"Function: arguments '{pretty(arguments)}' -- parameters '{pretty(self.parameters)}'"
            )
            raise Exception(
                f"The function defined at {self.position} takes {pn} arguments, not {an}."
            )
        pairs = list(zip([p.name for p in self.parameters], arguments))
        if self.is_builtin():
            body = self.body(runner, arguments)
        else:
            body = self.body.substitute(pairs, 0)
        return body

    def substitute(self, pairs, threshold):
        if self.is_builtin():
            return self
        return FunctionRef(
            self.parameters,
            self.body.substitute(pairs, threshold + len(self.parameters)),
        )

    def for_json(self):
        return "function"


class Parameter:
    def __init__(self, name, typ, position=None):
        assert name is not None
        self.typ = typ
        self.name = name
        self.position = position

    def _repr_pretty_(self, p, cycle):
        assert not cycle
        p.text(self.name)
        p.text(" : ")
        if self.typ:
            p.pretty(self.typ)
        else:
            p.text("Any")


class Call(Expression):
    def __init__(self, expression, arguments, position=None):
        assert arguments is not None
        assert expression is not None
        super().__init__(position)
        self.arguments = arguments
        self.expression = expression

    def substitute(self, pairs, threshold):
        arguments = [arg.substitute(pairs, threshold) for arg in self.arguments]
        expression = self.expression.substitute(pairs, threshold)
        return Call(expression, arguments)

    def _repr_pretty_(self, p, cycle):
        assert not cycle
        # prints `(function(x) x)(y)` instead of `function(x) x()`.
        if isinstance(self.expression, FunctionRef):
            p.text("(")
            p.pretty(self.expression)
            p.text(")")
        else:
            p.pretty(self.expression)
        p.text("(")
        for idx, arg in enumerate(self.arguments):
            if idx:
                p.text(", ")
            p.pretty(arg)
        p.text(")")


class Chain(Expression):
    def __init__(self, function, argument, position=None):
        assert function is not None
        assert argument is not None
        super().__init__(position)
        self.argument = argument
        self.function = function

    def substitute(self, pairs, threshold):
        argument = self.argument.substitute(pairs, threshold)
        function = self.function.substitute(pairs, threshold)
        return Chain(function, argument)

    def _repr_pretty_(self, p, cycle):
        assert not cycle
        p.text("(")
        p.pretty(self.function)
        p.text(".")
        p.pretty(self.argument)
        p.text(")")


class Lookup(Expression):
    def __init__(self, expression, var, position=None):
        assert var is not None
        assert expression is not None
        super().__init__(position)
        self.var = var
        self.expression = expression

    def substitute(self, pairs, threshold):
        return Lookup(self.expression.substitute(pairs, threshold), self.var)

    def _repr_pretty_(self, p, cycle):
        assert not cycle
        if isinstance(self.expression, (Bound, Variable, Reference)):
            p.text(self.expression.name)
        else:
            p.pretty(self.expression)
        p.text("::")
        p.text(self.var.name)


class NamespaceDefinition(Expression):
    def __init__(self, name: str, value, position: Optional[Position] = None):
        assert name is not None
        assert value is not None
        super().__init__(position)
        self.name = name
        self.value = value

    def substitute(self, pairs, threshold):
        return NamespaceDefinition(self.name, self.value.substitute(pairs, threshold))

    def _repr_pretty_(self, p, cycle):
        assert not cycle
        p.text(self.name)
        p.text(" = ")
        p.pretty(self.value)
        p.text(";")


class Namespace(Expression):
    def __init__(
        self,
        definitions: List[NamespaceDefinition],
        position: Optional[Position] = None,
    ):
        super().__init__(position)
        self.definitions = definitions

    def is_value(self):
        return True

    def has(self, name):
        for d in self.definitions:
            if d.name == name:
                return True
        return False

    def remove(self, name):
        definitions = [d for d in self.definitions if d.name != name]
        return Namespace(definitions)

    def combine(self, other):
        other_names = [d.name for d in other.definitions]
        definitions = other.definitions + [
            d for d in self.definitions if d.name not in other_names
        ]
        return Namespace(definitions)

    def lookup(self, name):
        for d in self.definitions:
            if d.name == name:
                return d
        raise Exception(f"The namespace does not define a symbol named '{name}'.")

    def substitute(self, pairs, threshold):
        return Namespace([d.substitute(pairs, threshold) for d in self.definitions])

    def for_json(self):
        return {d.name: d.value for d in self.definitions}

    def _repr_pretty_(self, p, cycle):
        assert not cycle
        p.text("namespace {")
        with p.group(4):
            p.breakable()
            for d in self.definitions:
                p.pretty(d)
                p.breakable()
        p.breakable()
        p.text("}")


class Index(Expression):
    def __init__(self, lhs, rhs, position=None):
        assert lhs is not None
        assert rhs is not None
        super().__init__(position)
        self.lhs = lhs
        self.rhs = rhs

    def substitute(self, pairs, threshold):
        lhs = self.lhs.substitute(pairs, threshold)
        rhs = self.rhs.substitute(pairs, threshold)
        return Index(lhs, rhs)

    def _repr_pretty_(self, p, cycle):
        assert not cycle
        p.pretty(self.lhs)
        p.text("[")
        p.pretty(self.rhs)
        p.text("]")
