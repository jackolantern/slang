import io
import contextlib

from slang.pretty import pretty
from slang.syntax import types
from slang.compiler import (
    run_file,
    run_string,
    parse_string,
    Scope,
    Compiler,
    make_default_scope,
)

from nose import tools


scope = make_default_scope()
compiler = Compiler(types.Universe())


def _judge(text):
    program = parse_string(text, scope)
    compiled = compiler.walk(program, scope)
    return compiler.checker.judge(compiled, scope)


def _convert_array(array):
    return [e.value for e in array.value]


def test_atomic_type_judgments():
    tools.eq_(_judge("1"), types.Int)


def test_arithmetic_type_judgments():
    tools.eq_(_judge("1 + 2"), types.Int)
    tools.eq_(_judge("1 + 2.0"), types.Float)
    tools.eq_(_judge("1 / 2"), types.Float)
    tools.eq_(_judge("1 * 2"), types.Int)
    tools.eq_(_judge("1.0 * 2"), types.Float)


def test_function_type_judgments():
    tools.eq_(_judge("function(x) x"), types.Function([types.Any], types.Any))
    # tools.eq_((_judge("function(x, y) x + y"))  #, types.Function([types.Any], types.Any))


def test_basic_arithmetic():
    tools.eq_(run_string("1", scope).value, 1)
    tools.eq_(run_string("1 + 1", scope).value, 2)
    tools.eq_(run_string("-1 + 1", scope).value, 0)
    tools.eq_(run_string("1 - 1", scope).value, 0)
    tools.eq_(run_string("1 + -1", scope).value, 0)
    tools.eq_(run_string("1 / 2", scope).value, 0.5)
    tools.eq_(run_string("0 / 2", scope).value, 0)
    tools.eq_(run_string("2 * 3", scope).value, 6)


def test_conditional():
    assert run_string("true", scope).value is True
    assert run_string("false", scope).value is False
    tools.eq_(run_string("if true then 7 else 3", scope).value, 7)
    tools.eq_(run_string("if false then 7 else 3", scope).value, 3)


def test_function_abstraction_and_application():
    tools.eq_(run_string("(function(x) { x })(0)", scope).value, 0)
    tools.eq_(run_string("(function(x, y) { x })(0, 1)", scope).value, 0)
    tools.eq_(
        run_string(
            """
    let y = 0;
    let f = function(x) { x };
    let g = function(x) {
        function(y) { x(y) }
    };
    g(f)(y)
    """,
            scope,
        ).value,
        0,
    )


def test_self_application():
    tools.eq_(
        run_string(
            """
        let g = function(x, y) {
            let f = this;
            function(x) namespace { x = x; y = y; }
        };
        g(1, 2)(3)
    """,
            scope,
        ).for_json(),
        run_string("namespace { x = 3; y = 2; }", scope).for_json(),
    )
    tools.eq_(
        _convert_array(
            run_string(
                """
        let g = function(x) {
            let f = this;
            if x <= 0 then x else f(x-1)
        };
        [g(-1), g(0), g(1)]
    """,
                scope,
            )
        ),
        [-1, 0, 0],
    )
    tools.eq_(
        _convert_array(
            run_string(
                """
        let g = function(x) {
            let f = this;
            function() if x <= 0 then x else f(x-1)()
        };
        let h = g(-1);
        let i = g(0);
        let j = g(1);
        [h(), i(), j()]
    """,
                scope,
            )
        ),
        [-1, 0, 0],
    )
    tools.eq_(
        run_string(
            """
    let f = function(x) {
        if x == 0
            then 1
            else x * this(x - 1)
    };
    f(7)
    """,
            scope,
        ).value,
        5040,
    )


def test_array_length():
    assert run_string("builtins::length([])", scope).value == 0
    assert run_string("builtins::length([1, 2, 3])", scope).value == 3


def test_nslib_has():
    assert (
        run_string(
            'builtins::nslib::has(namespace{ qux = 0; foo = 1; bar = 2; }, "qux")',
            scope,
        ).value
        is True
    )
    assert (
        run_string(
            'builtins::nslib::has(namespace{ qux = 0; foo = 1; bar = 2; }, "foo")',
            scope,
        ).value
        is True
    )
    assert (
        run_string(
            'builtins::nslib::has(namespace{ qux = 0; foo = 1; bar = 2; }, "bar")',
            scope,
        ).value
        is True
    )
    assert (
        run_string(
            'builtins::nslib::has(namespace{ qux = 0; foo = 1; bar = 2; }, "bin")',
            scope,
        ).value
        is False
    )


def test_nslib_remove():
    assert (
        run_string(
            'builtins::nslib::has(builtins::nslib::remove(namespace{ qux = 0; foo = 1; bar = 2; }, "qux"), "qux")',
            scope,
        ).value
        is False
    )
    assert (
        run_string(
            'builtins::nslib::has(builtins::nslib::remove(namespace{ qux = 0; foo = 1; bar = 2; }, "qux"), "foo")',
            scope,
        ).value
        is True
    )


def test_nslib_combine():
    assert (
        run_string(
            "builtins::nslib::combine(namespace{ foo = 1; }, namespace{ bar = 2; })::bar",
            scope,
        ).value
        == 2
    )
    assert (
        run_string(
            "builtins::nslib::combine(namespace{ foo = 1; }, namespace{ foo = 2; })::foo",
            scope,
        ).value
        == 2
    )
    assert (
        run_string(
            "builtins::nslib::combine(namespace{ foo = 1; }, namespace{ bar = 2; })::foo",
            scope,
        ).value
        == 1
    )


def test_echo():
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        tools.eq_(run_string("builtins::echo(1)", scope).value, 1)
    tools.eq_(f.getvalue(), "1\n")

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        assert run_string("builtins::echo(true)", scope).value is True
    assert f.getvalue() == "True\n"

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        # We assume that it returns the input.
        run_string("builtins::echo((function(x) x)(2))", scope)
    assert f.getvalue() == "(function(x) x)(2)\n"


def test_prelude():
    for suit in run_file("test.slang", scope).value:
        for test in suit.lookup("tests").value.value:
            actual = test.lookup("actual").value
            expected = test.lookup("expected").value
            assert (actual == expected).value, test.lookup("description").value.value
