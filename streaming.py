from cytoolz import pipe

def logging_range(m):
    print("range start")
    for i in range(m):
        print("yielding %i" % i)
        yield i
    print("range done")

def logging_times2(it):
    print("times2 start")
    for i in it:
        print("multiplying %i by 2" % i)
        yield i * 2
    print("times2 done")

def logging_sum(it):
    print("sum start")
    acc = 0
    for i in it:
        print("adding %i to current total %i" % (i, acc))
        acc += i
    print("sum done")
    return acc

if __name__ == '__main__':
    s = pipe(5, logging_range, logging_times2, logging_sum)
    print("the result is %i" % s)
