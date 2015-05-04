# Big data in little laptop: a streaming story (featuring toolz)

> In my brief experience people rarely take this [streaming] route. They use
> single-threaded in-memory Python until it breaks, and then seek out Big Data
> Infrastructure like Hadoop/Spark at relatively high productivity overhead.
> — Matt Rocklin

Single point to take home today: consider whether you can solve your problem
with iterators. If so, DO IT.

It's marginally harder but makes later scaling way easier.

And the toolz library reduces the difficulty even further.

(toolz because it's an amalgam of functoolz, itertoolz, and dicttoolz — two of
which are in the standard library but are quite lacking in functionality.)

# The "traditional" programming model

- Load your dataset into a suitable format, e.g. `pandas.DataFrame`
- Do various processing on it, often including some copies of the data
- Output the result, usually a highly reduced process of the data

- almost all major libraries do this (e.g. sklearn, pandas)

# "streaming"

- *not* necessarily web-based or "infinite" data stream
- *iterate* through data on-disk, never storing full data

# Toy example

Let's take the sum of all even numbers up to 10.

1. input = list(range(6))
   doubled = [x * 2 for x in input]
   summed = sum(doubled)

2. input = range(6)
   doubled = (x * 2 for x in input)
   summed = sum(doubled)

# toolz piping

3. def double(a): return a * 2
   double_all = tz.curried.map(double)
   import toolz as tz
   summed = tz.pipe(range(6), double_all, sum)

# tips

- (list -> return list) becomes (iterator/generator -> yield elem)
- convert f(a -> return b) to streaming with curried.map(f)

# Bigger example: take PCA from a large dataset

sklearn has `IncrementalPCA` class. But you need to chunk your data yourself.

```python
import toolz as tz
from toolz import curried
from sklearn import decomposition
from sklearn import datasets
import numpy as np

def streaming_pca(samples, n_components=2, batch_size=100):
    ipca = decomposition.IncrementalPCA(n_components=n_components,
                                        batch_size=batch_size)
    _ = list(tz.pipe(samples, curried.partition(batch_size),
                     curried.map(list), curried.map(np.array),
                     ipca.partial_fit))
    return ipca
```

If your data is in a csv file, it's simple to take the PCA of it, while using
negligible memory!

```python
def array_from_txt(line, sep=',', dtype=np.float):
    return np.array(line.rstrip().split(sep), dtype=dtype)

with open('data.csv') as fin:
    pca_obj = tz.pipe(fin, array_from_txt, streaming_pca)
```

In a second pass, we can compute the PCA of the data:

```python
with open('data.csv') as fin:
    components = np.array(tz.pipe(fin, array_from_txt, pca_obj.transform))

from matplotlib import pyplot as plt

plt.scatter(*components.T)
```

# k-mer counting

In genomics, it's important to count the appearance of "k-mers", or bits of
genetic sequence of length k. This is used heavily, for example, in error
correction.

```python
def fa_transform(seq):
    seq = seq.rstrip()
    if seq.startswith('>'):
        return '$'
    return seq

import glob
k = 10
counts = tz.pipe(glob.glob('*.fa'), curried.map(open), tz.concat,  # lines
                 curried.map(fa_transform),  # discard names, add separator
                 tz.concat,  # characters
                 curried.sliding_window(k), curried.map(''.join),  # k-mers
                 tz.frequencies)
```


# assembly

```python
seq = 'ATGGSGTGSA'
g = nx.DiGraph()

path = tz.pipe(seq, curried.sliding_window(3),
                    curried.map(''.join),
                    curried.map(eu.edge_from_kmer),
                    eu.add_edges(g),
                    eu.eulerian_path)
path

p = list(path)
```

# tips

- (list of list -> list) with tz.concat

- don't get caught out:
    - iterators get consumed
    - iterators are *lazy*; need to force evaluation sometimes.

# in conclusion

- streaming in Python is easy when you use a few abstractions
- streaming can make you more productive:
    - big data takes linearly longer than small data (no nasty memory swapping)
    - don't need a bigger machine
    - if your tests pass on small data, they'll pass on big data
- streaming code is concise and readable using toolz (cytoolz for speed)

Read more on Matt Rocklin's blog!
