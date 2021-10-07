let factorial = function(x) {
    if x <= 0
    then 1
    else x * this(x - 1)
};

factorial(7)
