# Slang

Slang is short for "simple language".
It is a simple functional language that is "easy" to extend.

## Example

```bash
$ slang examples/factorial.slang
```

## Language Overview

A slang program is executed in three stages:
- Parsing
- Simplification
- Normalization

Parsing transforms a slang program into an abstract syntax tree (AST).
Simplification --- as the name implies --- transforms an AST into a simpler AST
(well, in any case it transforms it into a tree that is no more complex than the tree you started with).

For example, the after parsing and simplifying `let x = 7; x * x` and `7 * 7` yields the same AST as parsing `49`.

### External Functions

You can add your own python functions (for examples, see how the default scope is constructed in `compiler.py`).
Such a function takes two arguments:

```python
def my_func(runner, arguments)
```

The `arguments` variable contains a list of arguments passed to this function.
Because of lazy evaluation, these arguments may not be in normal form.  To normalize the i-th argument,
do something like `runner.run(arguments[i])`.

Sometimes you only need to normalize up to a certain point.
For example, the function that gives the length of an array does not need to normalize the elements of the array.
For this, you can use `runner.walk(arguments[i])` instead.

### Types

slang was built with types in mind, but there is currently no type system implemented.
Stay tuned.

### Recursion

No need to implement your favorite fix point combinator, just use `this`.
For example, the factorial function can be defined as
```
let fact = function(n) {
    if n == 0
    then 1
    else n * this(n - 1)
};
```

### Chaining

"Chaining" is just syntactic sugar which transforms `x.f()` into `f(x)`.
This means that instead of writing
```
map2(enumerate(map(f, x)), g)
```
we can use chaining to write
```
x.map(f).enumerate().map2(g)
```
which is arguably easier to read.
