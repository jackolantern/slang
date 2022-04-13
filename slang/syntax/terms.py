# pyre-strict
import types as pytypes
import logging
from typing import Any, Dict, List, Optional

from . import Position

DEFAULT = object()


class EnvironmentError(Exception):
    pass


class Environment:
    parent: Optional["Environment"]
    symbols: Dict[str, "Expression"]

    def __init__(
        self,
        parent: Optional["Environment"] = None,
        symbols: Optional[Dict[str, "Expression"]] = None,
    ):
        self.parent = parent
        self.symbols = symbols if symbols else {}

    def push(self) -> "Environment":
        return Environment(self)

    def keys(self) -> List[str]:
        return list(self.symbols.keys()) + (self.parent.keys() if self.parent else [])

    def add_symbol(self, name: str, value: "Expression") -> None:
        existing = self.symbols.get(name)
        if existing:
            raise EnvironmentError(f"This env already defines a value named '{name}'.")
        else:
            self.symbols[name] = value

    def find_symbol(self, name: str, default: Any = DEFAULT) -> "Expression":
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.find_symbol(name, default)
        else:
            if default == DEFAULT:
                raise EnvironmentError(f"No symbol named '{name}'.")
            return default

    def get_root(self) -> "Environment":
        env = self
        while env.parent:
            env = env.parent
        return env


class Node:
    def __init__(self, position: Optional[Position]):
        self.position = position

    def __repr__(self):
        return str(self)


class Statement(Node):
    def is_value(self):
        return False


class Expression(Node):
    def is_value(self):
        return False


class Bang(Statement):
    def __init__(self, expression: Expression, position: Optional[Position] = None):
        assert expression is not None
        super().__init__(position)
        self.expression = expression


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


class Block(Expression):
    def __init__(
        self,
        statements: List[Statement],
        expression: Expression,
        position: Optional[Position] = None,
    ):
        super().__init__(position)
        self.expression = expression
        self.statements = statements


class This(Expression):
    pass


class UnaryOperation(Expression):
    def __init__(self, op, expression, position=None):
        assert op is not None
        assert expression is not None
        super().__init__(position)
        self.op = op
        self.expression = expression


class BinaryOperation(Expression):
    def __init__(self, op, lhs, rhs, position=None):
        assert op is not None
        assert lhs is not None
        assert rhs is not None
        super().__init__(position)
        self.op = op
        self.lhs = lhs
        self.rhs = rhs


class Bound(Expression):
    def __init__(self, name, index, position=None):
        assert name is not None
        assert index is not None
        super().__init__(position)
        self.name = name
        self.index = index


class Variable(Expression):
    def __init__(self, name, position=None):
        assert name is not None
        super().__init__(position)
        self.name = name


class IfThenElse(Expression):
    def __init__(self, test, true, false, position: Optional[Position] = None):
        assert test is not None
        assert true is not None
        assert false is not None
        super().__init__(position)
        self.test = test
        self.true = true
        self.false = false


class Parameter:
    def __init__(self, name, typ, position=None):
        assert name is not None
        self.typ = typ
        self.name = name
        self.position = position

    def __str__(self):
        return self.name


class FunctionDefinition(Expression):
    def __init__(
        self,
        parameters: List[Parameter],
        body: Expression,
        builtin: bool,
        position: Optional[Position] = None,
    ):
        super().__init__(position)
        self.body = body
        self.is_builtin = builtin
        self.parameters = parameters

    def __eq__(self, other):
        return (
            type(self) == type(other)
            and self.parameters == other.parameters
            and self.body == other.body
        )

    def __hash__(self):
        return hash(tuple(p.name for p in self.parameters))

    def is_value(self):
        return False


class Function(Expression):
    def __init__(self, definition: FunctionDefinition, environment: Environment):
        super().__init__(definition.position)
        self.definition = definition
        self.environment = environment

    def __eq__(self, other):
        return (
            type(self) == type(other)
            and self.definition == other.definition
            and self.body == other.body
        )

    def __hash__(self):
        return hash(tuple(p.name for p in self.parameters))

    def is_value(self):
        return True


class Call(Expression):
    def __init__(
        self, expression: Expression, arguments: List[Expression], position=None
    ):
        super().__init__(position)
        self.arguments = arguments
        self.expression = expression


# class Chain(Expression):
#     def __init__(self, function: Function, argument: Expression, position=None):
#         super().__init__(position)
#         self.argument = argument
#         self.function = function


class Lookup(Expression):
    def __init__(self, expression: Expression, var: Variable, position=None):
        super().__init__(position)
        self.var = var
        self.expression = expression


class NamespaceDefinition(Expression):
    def __init__(self, name: str, value, position: Optional[Position] = None):
        assert name is not None
        assert value is not None
        super().__init__(position)
        self.name = name
        self.value = value


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
        for d in reversed(self.definitions):
            if d.name == name:
                return d.value
        raise Exception(f"The namespace does not define a symbol named '{name}'.")

    def for_json(self):
        return {d.name: d.value.for_json() for d in self.definitions}


class Index(Expression):
    def __init__(self, lhs, rhs, position=None):
        assert lhs is not None
        assert rhs is not None
        super().__init__(position)
        self.lhs = lhs
        self.rhs = rhs


class Value(Expression):
    def __init__(self, value, position: Optional[Position] = None):
        assert value is not None
        if isinstance(value, Node):
            raise Exception(f"!{value.value}")
        super().__init__(position)
        self.value = value

    def is_value(self):
        return True

    def __neg__(self):
        return Value(-self.value)

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        return Value(self.value == other.value)

    def __ne__(self, other):
        return Value(self.value != other.value)

    def __lt__(self, other):
        return Value(self.value < other.value)

    def __le__(self, other):
        return Value(self.value <= other.value)

    def __gt__(self, other):
        return Value(self.value > other.value)

    def __ge__(self, other):
        return Value(self.value >= other.value)

    def __add__(self, other):
        return Value(self.value + other.value)

    def __sub__(self, other):
        return Value(self.value - other.value)

    def __mul__(self, other):
        return Value(self.value * other.value)

    def __pow__(self, other):
        return Value(self.value ** other.value)

    def __mod__(self, other):
        return Value(self.value % other.value)

    def __truediv__(self, other):
        return Value(self.value / other.value)

    def for_json(self):
        return self.value


class Array(Value):
    def __init__(self, value, position=None):
        assert value is not None
        super().__init__(value, position=position)
        assert isinstance(value, list)

    def __add__(self, other):
        if not isinstance(other, Array):
            raise Exception(
                f"Concatenation not defined between array and '{type(other)}'."
            )
        return Array(self.value + other.value)

    def for_json(self):
        return [v.for_json() for v in self.value]

    def __eq__(self, other):
        return from_value(self) == from_value(other)

    def __str__(self):
        return str(from_value(self))


def from_value(value: Expression):
    if isinstance(value, Array):
        return [from_value(item) for item in value.value]
    elif isinstance(value, Namespace):
        return {item.name: from_value(item.value) for item in value.definitions}
    elif isinstance(value, Value):
        return value.value
    raise ValueError(f"Not supported: {type(value)}")
