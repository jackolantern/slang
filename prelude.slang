let length = builtins::length;

let map_array = function(index, array, f) {
    if index < length(array)
        then [f(array[index])] + this(index + 1, array, f)
        else []
};

let map_array2 = function(index, array, f) {
    if index < length(array)
        then [f(array[index][0], array[index][1])] + this(index + 1, array, f)
        else []
};

let where_array = function(index, array, f) {
    if index < length(array)
    then if f(array[index])
         then [array[index]] + this(index + 1, array, f)
         else this(index + 1, array, f)
    else []
};

namespace {
    math = namespace {
        pi = 14159265359;
        ceil = builtins::ceil;
        floor = builtins::floor;
        sin = builtins::sin;
        cos = builtins::cos;
        tan = builtins::tan;
        sinh = builtins::sinh;
        cosh = builtins::cosh;
        tanh = builtins::tanh;
        ln = builtins::ln;
        max = function(lhs, rhs) {
            if lhs < rhs then rhs else lhs
        };

        min = function(lhs, rhs) {
            if lhs > rhs then rhs else lhs
        };
    };

    range = function(start, stop, step) namespace {
        step = step;
        stop = stop;
        start = start;
    };

    map = function(array, f) map_array(0, array, f);
    map2 = function(array, f) map_array2(0, array, f);

    each = function(r, f) {
        if r::start < r::stop
            then [f(r::start)] + this(range(r::start + r::step, r::stop, r::step), f)
            else []
    };

    zip = function(lhs, rhs) {
        let n = math::min(length(lhs), length(rhs));
        range(0, n, 1).each(function(i) [lhs[i], rhs[i]])
    };

    echo = builtins::echo;
    length = length;

    enumerate = function(array) range(0, array.length(), 1).each(function(i) [i, array[i]]);

    where = function(array, predicate) where_array(0, array, predicate);
}
