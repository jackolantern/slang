import io
import contextlib
from unittest import TestCase

from slang.syntax import types, terms
from slang.runtime import (
    run_file,
    run_string,
    parse_string,
    make_default_environment,
    Environment,
)

env = make_default_environment()


def _convert_array(array):
    return [e.value for e in array.value]


class TestSlang(TestCase):
    def test_basic_arithmetic(self):
        self.assertEqual(run_string("1", env).value, 1)
        self.assertEqual(run_string("1 + 1", env).value, 2)
        self.assertEqual(run_string("-1 + 1", env).value, 0)
        self.assertEqual(run_string("1 - 1", env).value, 0)
        self.assertEqual(run_string("1 + -1", env).value, 0)
        self.assertEqual(run_string("1 / 2", env).value, 0.5)
        self.assertEqual(run_string("0 / 2", env).value, 0)
        self.assertEqual(run_string("2 * 3", env).value, 6)

    def test_conditional(self):
        assert run_string("true", env).value is True
        assert run_string("false", env).value is False
        self.assertEqual(run_string("if true then 7 else 3", env).value, 7)
        self.assertEqual(run_string("if false then 7 else 3", env).value, 3)

    def test_function_abstraction_and_application(self):
        self.assertEqual(run_string("(function(x) { x })(0)", env).value, 0)
        self.assertEqual(run_string("(function(x, y) { x })(0, 1)", env).value, 0)
        self.assertEqual(
            run_string(
                """
        let y = 0;
        let f = function(x) { x };
        let g = function(x) {
            function(y) { x(y) }
        };
        g(f)(y)
        """,
                env,
            ).value,
            0,
        )

    def test_self_application(self):
        self.assertEqual(
            run_string(
                """
            let g = function(x, y) {
                let f = this;
                function(x) namespace { x = x; y = y; }
            };
            g(1, 2)(3)
        """,
                env,
            ).for_json(),
            run_string("namespace { x = 3; y = 2; }", env).for_json(),
        )
        self.assertEqual(
            _convert_array(
                run_string(
                    """
           let g = function(x) {
               let f = this;
               if x <= 0 then x else f(x-1)
           };
           [g(-1), g(0), g(1)]
        """,
                    env,
                )
            ),
            [-1, 0, 0],
        )
        self.assertEqual(
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
                    env,
                )
            ),
            [-1, 0, 0],
        )
        self.assertEqual(
            run_string(
                """
        let f = function(x) {
           if x == 0
               then 1
               else x * this(x - 1)
        };
        f(7)
        """,
                env,
            ).value,
            5040,
        )

    def test_array_length(self):
        assert run_string("builtins::length([])", env).value == 0
        assert run_string("builtins::length([1, 2, 3])", env).value == 3

    def test_nslib_has(self):
        assert (
            run_string(
                'builtins::nslib::has(namespace{ qux = 0; foo = 1; bar = 2; }, "qux")',
                env,
            ).value
            is True
        )
        assert (
            run_string(
                'builtins::nslib::has(namespace{ qux = 0; foo = 1; bar = 2; }, "foo")',
                env,
            ).value
            is True
        )
        assert (
            run_string(
                'builtins::nslib::has(namespace{ qux = 0; foo = 1; bar = 2; }, "bar")',
                env,
            ).value
            is True
        )
        assert (
            run_string(
                'builtins::nslib::has(namespace{ qux = 0; foo = 1; bar = 2; }, "bin")',
                env,
            ).value
            is False
        )

    def test_nslib_remove(self):
        assert (
            run_string(
                'builtins::nslib::has(builtins::nslib::remove(namespace{ qux = 0; foo = 1; bar = 2; }, "qux"), "qux")',
                env,
            ).value
            is False
        )
        assert (
            run_string(
                'builtins::nslib::has(builtins::nslib::remove(namespace{ qux = 0; foo = 1; bar = 2; }, "qux"), "foo")',
                env,
            ).value
            is True
        )

    def test_nslib_combine(self):
        assert (
            run_string(
                "builtins::nslib::combine(namespace{ foo = 1; }, namespace{ bar = 2; })::bar",
                env,
            ).value
            == 2
        )
        assert (
            run_string(
                "builtins::nslib::combine(namespace{ foo = 1; }, namespace{ foo = 2; })::foo",
                env,
            ).value
            == 2
        )
        assert (
            run_string(
                "builtins::nslib::combine(namespace{ foo = 1; }, namespace{ bar = 2; })::foo",
                env,
            ).value
            == 1
        )

    def test_echo(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.assertEqual(run_string("builtins::echo(1)", env).value, 1)
        self.assertEqual(f.getvalue(), "1\n")

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            assert run_string("builtins::echo(true)", env).value is True
        assert f.getvalue() == "True\n"

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            # We assume that the return value is correct.
            run_string("builtins::echo((function(x) x)(2))", env)
        assert f.getvalue() == "2\n"

    def test_prelude(self):
        for suit in run_file("test.slang", env).value:
            for test in suit.lookup("tests").value:
                actual = terms.from_value(test.lookup("actual"))
                expected = terms.from_value(test.lookup("expected"))
                if actual != expected:
                    print(terms.from_value(test.lookup("description")))
                    print("actual:", actual)
                    print("expected:", expected)
                    assert False
