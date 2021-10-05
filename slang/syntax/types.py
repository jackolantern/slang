from typing import List, Callable


class Type:
    pass


class BasicType(Type):
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, BasicType) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name


class Array(Type):
    def __init__(self, element_type):
        assert element_type is not None
        self.element_type = element_type

    def __eq__(self, other):
        return isinstance(other, Array) and self.element_type == other.element_type

    def __hash__(self):
        return 2 * hash(self.element_type)

    def __str__(self):
        return f"Array<{self.element_type}>"

    def __repr__(self):
        return str(self)


class Function(Type):
    def __init__(self, parameters: List[Type], ret: Type):
        self.ret = ret
        self.parameters = parameters

    def __eq__(self, other):
        return (
            isinstance(other, Function)
            and self.parameters == other.parameters
            and self.ret == other.ret
        )

    def __hash__(self):
        return hash(self.parameters) + hash(self.ret)

    def __str__(self):
        parameters = ", ".join([str(p) for p in self.parameters])
        return f"Function<{parameters}, {self.ret}>"


class UnionType(Type):
    def __init__(self, lhs: Type, rhs: Type):
        self.lhs = lhs
        self.rhs = rhs

    def __eq__(self, other):
        return isinstance(other, UnionType) and (
            (self.lhs == other.lhs and self.rhs == other.rhs)
            or (self.lhs == other.rhs and self.rhs == other.lhs)
        )

    def __hash__(self):
        return hash(self.lhs) + hash(self.rhs)

    def __str__(self):
        return f"({self.lhs} | {self.rhs})"

    def __repr__(self):
        return str(self)


class Universe:
    """
    I assume that the number of basic types is small (less than 50?).
    If this assumption is wrong, than doing a search in for the coercion and building it up piecewise
    instead of explicit transitivity might prove more practical.
    """

    def __init__(self):
        self.basic_types = set()
        for t in (Int, Float, Bool, String):
            self.add_basic_type(t)
        self.basic_coercions = {}
        self.add_coercion(Int, Float, float)
        self.add_coercion(Bool, Int, int)

    def add_basic_type(self, t: Type):
        assert t != Any
        assert t != Void
        assert t not in self.basic_types
        self.basic_types.add(t)

    def add_coercion(self, small, big, f):
        assert (small, big) not in self.basic_coercions
        self.basic_coercions[(small, big)] = f
        for t in self.basic_types:
            g = self.basic_coercions.get((big, t))
            if g:
                self.basic_coercions[(small, t)] = compose(g, f)

    def make_union(self, lhs, rhs):
        if lhs == Void:
            return rhs
        if rhs == Void:
            return lhs
        if lhs == Any or rhs == Any:
            return Any
        if self.is_subtype(lhs, rhs):
            return rhs
        if self.is_subtype(rhs, lhs):
            return lhs
        return UnionType(lhs, rhs)

    # def try_coerce(self, value, dst):
    #     coercion = self.try_coercion(value.typ, dst)
    #     if coercion:
    #         return values.Value(coercion(value.value))
    #     return None

    # def try_coercion(self, src, dst):
    #     if dst == Any or src == Void:
    #         return identity
    #     if src in self.basic_types and dst in self.basic_types:
    #         return self.basic_coercions.get((src, dst))
    #     elif isinstance(src, Array) and isinstance(dst, Array):
    #         f = self.try_coercion(src.element_type, dst.element_type)
    #         if f:
    #             return lambda arr: Array(
    #                 [values.Value(f(x.value)) for x in arr.value]
    #             )
    #     return None

    def is_subtype(self, lhs, rhs):
        if lhs == rhs:
            return True
        if isinstance(lhs, UnionType):
            return self.is_subtype(lhs.lhs, rhs) and self.is_subtype(lhs.rhs, rhs)
        if isinstance(rhs, UnionType):
            return self.is_subtype(lhs, rhs.lhs) or self.is_subtype(lhs, rhs.rhs)
        return False


Any = BasicType("Any")
Void = BasicType("Void")
Int = BasicType("Int")
Float = BasicType("Float")
Bool = BasicType("Bool")
String = BasicType("String")

EmptyArray = Array(Void)


def identity(x: Type) -> Type:
    return x


def compose(
    f: Callable[[Type], Type], g: Callable[[Type], Type]
) -> Callable[[Type], Type]:
    return lambda x: f(g(x))
