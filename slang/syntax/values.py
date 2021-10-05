from typing import Optional

from . import Position
from .terms import Expression


class Value(Expression):
    def __init__(self, value, position: Optional[Position] = None):
        assert value is not None
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

    def _repr_pretty_(self, p, cycle):
        assert not cycle
        if isinstance(self.value, str):
            p.text('"')
            p.text(self.value)
            p.text('"')
        else:
            p.pretty(self.value)

    def substitute(self, pairs, threshold):
        return self

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

    def substitute(self, pairs, threshold):
        return Array([e.substitute(pairs, threshold) for e in self.value])

    def _repr_pretty_(self, p, cycle):
        with p.group(4, "[", "]"):
            for idx, item in enumerate(self.value):
                if idx:
                    p.text(", ")
                p.pretty(item)
