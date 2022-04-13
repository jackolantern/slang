import "prelude.slang";

let it = function(desc, actual, expected) namespace {
    description = desc;
    actual = actual;
    expected = expected;
};

let describe = function(desc, tests) namespace {
    description = desc;
    tests = tests;
};

[
    describe("prelude", [
        it("max returns maximum value.", 7, math::max(1, 7)),
        it("max returns maximal value.", 7, math::max(7, 7)),
        it("max handles negative numbers.", -1, math::max(-1, -7)),
        it("ceil handles negative numbers.", 0, math::ceil(-0.9)),
        it("floor handles negative numbers.", -1, math::floor(-0.9)),

        it("zip handles equal length arrays.",
            [[1, 4], [2, 5], [3, 6]],
            zip([1, 2, 3], [4, 5, 6]))

        it("zip handles arrays with longer lhs.",
            [[1, 4], [2, 5], [3, 6]],
            zip([1, 2, 3, 0], [4, 5, 6]))

        it("zip handles arrays with longer rhs.",
            [[1, 4], [2, 5], [3, 6]],
            zip([1, 2, 3], [4, 5, 6, 0]))

        it("zip handles empty arrays.", [], zip([], [])),

        it("map array maps function.", [1, 2, 3].map(function(x) x + 1), [2, 3, 4]),
        it("map array handles empty array.", [].map(function(x) x + 1), []),

        it("map2 array maps function.", [[1, 2], [2, 3], [3, 4]].map(function(x) [x[0] + 1, x[1] + 2]), [[2, 4], [3, 5], [4, 6]]),
        it("enumerate enumerates non empty lists.", [100, 200, 300].enumerate(), [[0, 100], [1, 200], [2, 300]])
        it("enumerate enumerates empty lists.", [].enumerate(), [])
    ])
]
