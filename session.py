# coding: utf-8
input = list(range(6))
input
doubled = [x * 2 for x in input]
doubled
summed = sum(doubled)
summed
input = range(6)
input
doubled = (x * 2 for x in input)
doubled
summed = sum(doubled)
summed
def verbose_range(n):
    print('range started')
    for elem in range(n):
        print('yielding %i' % n)
        yield i
    print('range done')
    
list(range(3))
list(verbose_range(3))
def verbose_range(n):
    print('range started')
    for elem in range(n):
        print('yielding %i' % elem)
        yield elem
    print('range done')
    
list(verbose_range(3))
def verbose_double(iterator):
    print('double start')
    for elem in iterator:
        print('multiplying %i by 2 to get %i' % (elem, elem * 2))
        yield elem * 2
    print('doubled done')
    
list(doubled(range(3))

)
list(verbose_doubled(verbose_range(3)))
list(verbose_double(verbose_range(3)))
def verbose_sum(iterator):
    print('sum started')
    acc = 0
    for elem in iterator:
        print('adding %i to %i to get %i' % (elem, acc, acc + elem))
        acc += elem
    print('sum done')
    return acc
verbose_sum(verbose_double(verbose_range(5)))
import toolz as tz
tz.pipe(5, verbose_range, verbose_double, verbose_sum)
def double(x): return x * 2
from toolz import curried
list(map(double, [0, 1, 2]))
double_all = curried.map(double)
list(double_all([0, 1, 2]))
from sklearn import decomposition
import numpy as np
def streaming_pca(samples, n_components=2, batch_size=50):
    ipca = decomposition.IncrementalPCA(n_components=n_components,
                                        batch_size=batch_size)
    _ = list(tz.pipe(samples, curried.partition(batch_size),
                     curried.map(np.array),
                     curried.map(ipca.partial_fit)))
    return ipca
def array_from_txt(line):
    return np.array(line.rstrip().split(','), dtype=np.float)
with open('iris.csv') as fin:
    pca_obj = tz.pipe(fin, curried.map(array_from_txt), streaming_pca)
    
with open('iris.csv') as fin:
    components = np.squeeze(list(tz.pipe(fin,
                                         curried.map(array_from_txt),
                                  curried.map(pca_obj.transform))))
    
from matplotlib import pyplot as plt
plt.scatter(*components.T)
type(open('iris.csv').readlines())
import glob
counts = tz.pipe(glob.glob('sample.fasta'), curried.map(open),
                 tz.concat, curried.filter(lambda x: not x.startswith('>')),
                 curried.interpose('$'), tz.concat,
                 curried.sliding_window(6), curried.map(''.join),
                 curried.filter(lambda x: '$' not in x),
                 tz.frequencies)
for k in counts:
    print(k, counts[k])
    break
counts_list = list(counts.values())
plt.hist(counts_list, bins=25)
