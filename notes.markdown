# Big data in little laptop: a streaming story (featuring toolz)

> In my brief experience people rarely take this [streaming] route. They use
> single-threaded in-memory Python until it breaks, and then seek out Big Data
> Infrastructure like Hadoop/Spark at relatively high productivity overhead.
> — Matt Rocklin

Single point to take home today: consider whether you can solve your problem
with iterators. If so, DO IT.

It's marginally harder initially but makes later scaling way easier.

And the toolz library reduces the difficulty even further.

(toolz because it's an amalgam of functoolz, itertoolz, and dicttoolz — two of
which are in the standard library but are quite lacking in functionality.)

# The "traditional" programming model

- Load your dataset into a suitable format, e.g. `pandas.DataFrame`
- Do various processing on it, often including some copies of the data
- Output the result, usually a highly reduced process of the data

- almost all major libraries work on this model (e.g. sklearn, pandas)

# "streaming"

- *not* necessarily web-based or "infinite" data stream
- *iterate* through data on-disk, never loading full data in RAM

# Toy example

Let's take the sum of all even numbers up to 10.

List approach:

```python
input = list(range(6))
doubled = [x * 2 for x in input]
summed = sum(doubled)
```

Streaming approach:

```python
input = range(6)
doubled = (x * 2 for x in input)
summed = sum(doubled)
```

# verbose example

```python
from toolz import pipe

def verbose_range(m):
    print("range start")
    for i in range(m):
        print("yielding %i" % i)
        yield i
    print("range done")

def verbose_times2(it):
    print("times2 start")
    for i in it:
        print("multiplying %i by 2" % i)
        yield i * 2
    print("times2 done")

def verbose_sum(it):
    print("sum start")
    acc = 0
    for i in it:
        print("adding %i to current total %i" % (i, acc))
        acc += i
    print("sum done")
    return acc

if __name__ == '__main__':
    s = pipe(5, verbose_range, verbose_times2, verbose_sum)
    print("the result is %i" % s)
```

# toolz piping

`tz.pipe` is syntacting sugar for streaming.

```python
import toolz as tz
from toolz import curried
def double(a):
    return a * 2
double_all = curried.map(double)
summed = tz.pipe(range(6), double_all, sum)
```

# tips

- (list -> return list) becomes (iterator/generator -> yield elem)
- convert f(a -> return b) (single element function) to function operating on
  stream using `curried.map(f)`

# Bigger example: take PCA from a large dataset

sklearn has `IncrementalPCA` class. But you need to chunk your data yourself.
Let's make a function that can take a stream of data samples and perform PCA.
Be sure to look at the [documentation](http://scikit-learn.org/stable/modules/generated/sklearn.decomposition.IncrementalPCA.html)
for the class to understand some of the code below.

```python
import toolz as tz
from toolz import curried
from sklearn import decomposition
from sklearn import datasets
import numpy as np

def streaming_pca(samples, n_components=2, batch_size=100):
    ipca = decomposition.IncrementalPCA(n_components=n_components,
                                        batch_size=batch_size)
    # we use `tz.last` to force evaluation of the full iterator
    _ = tz.last(tz.pipe(samples,  # iterator of 1D arrays
                        curried.partition(batch_size),  # iterator of tuples
                        curried.map(np.array),  # iterator of 2D arrays
                        curried.map(ipca.partial_fit)))  # partial_fit on each
    return ipca
```

If your data is in a csv file, it's simple to take the PCA of it, while using
negligible memory!

```python
def array_from_txt(line, sep=',', dtype=np.float):
    return np.array(line.rstrip().split(sep), dtype=dtype)

with open('iris.csv') as fin:
    pca_obj = tz.pipe(fin, curried.map(array_from_txt), streaming_pca)
```

In a second pass, we can compute the PCA of the data:

```python
with open('iris.csv') as fin:
    components = np.squeeze(tz.pipe(fin,
                                    curried.map(array_from_txt),
                                    curried.map(pca_obj.transform)))

from matplotlib import pyplot as plt
plt.scatter(*components.T)
```

# k-mer counting

In genomics, it's important to count the appearance of "k-mers", or bits of
genetic sequence of length k. This is used heavily, for example, in error
correction.

```python
def fa_filter(sequence_iter):
    for seq in sequence_iter:
        if not seq.startswith('>'):
            yield seq.rstrip()

import glob
k = 6
counts = tz.pipe(glob.glob('*.fasta'), curried.map(open), tz.concat,  # lines
                 curried.map(fa_filter),  # discard names
                 curried.map(curried.sliding_window(k)), apply sliding to each
                 tz.concat,  # k-mers as char tuples
                 curried.map(''.join),  # k-mers
                 tz.frequencies)

plt.hist(list(counts.values()), bins=25)
```


# assembly

Genome assembly: we use a toy genetic sequence to demonstrate a De Bruijn graph
assembler.
See [this link](http://www.cs.jhu.edu/~langmea/resources/lecture_notes/assembly_dbg.pdf)
for more on this topic. The sequence is derived from Fig 3 of
[this paper](http://www.nature.com/nbt/journal/v29/n11/full/nbt.2023.html), but
in our case it is not circular.

First, we are going to write a function to generate random reads from the
sequence:

```python
@tz.curry
def generate_reads(seq, nreads=60, readlen=5):  # 30x coverage
    for i in range(nreads):
        start = np.random.randint(0, len(seq) - readlen + 1)
        yield seq[start : start+readlen]
```

Next, we generate some reads and feed them into a De Bruijn graph implemented
in networkx.

```python
seq = 'ATGGSGTGSA'
g = nx.DiGraph()
```

We can draw the graph:

```python
import nxeuler as eu  # local module

draw_circular = tz.partial(nx.draw_circular, with_labels=True,
                                             node_color='w',
                                             node_size=600)
reads = generate_reads(seq)
draw = tz.pipe(reads, curried.map(curried.sliding_window(3)),  # k-mers
                      tz.concat,  # join k-mer streams from all reads
                      curried.map(''.join),  # make strings from tup of char
                      curried.map(eu.edge_from_kmer),  # get k-1-mer tuples
                      eu.add_edges(g),  # add them as edges to the graph
                      draw_circular)  # draw the graph
```

(Note that the graph is *much smaller* than the original dataset of the reads!)

Or, we can feed the graph directly into an Eulerian path algorithm, and
reconstruct the original genome from that:

```python
def assemble(euler_path):
    start = tz.first(euler_path)[0]
    rest = tz.pipe(euler_path, curried.pluck(0),  # 1st k-1-mer
                               curried.pluck(1),  # 2nd letter
                               ''.join)
    return start + rest

reads = generate_reads(seq)
g = nx.DiGraph()
inferred = tz.pipe(reads, curried.map(curried.sliding_window(3)),  # k-mers
                          tz.concat,  # join k-mer streams from all reads
                          curried.map(''.join),  # make string from tup of char
                          curried.map(eu.edge_from_kmer),  # get k-1-mer tups
                          eu.add_edges(g),  # add edges to g
                          eu.eulerian_path,  # iterate over euler path edges
                          assemble)  # get assembled string from path
print(seq)
print(inferred)
```

Note that real assembly requires lots of sophisticated error correction. But I
hope this gives you an idea of the potential to stream over reads to generate a
more compact view for assembly.

# tips

- (list of list -> list) with tz.concat

- don't get caught out:
    - iterators get *consumed*. So if you make a generator, do some processing,
      and then a later step fails, you need to re-create the generator. The
      original is already gone.
    - iterators are *lazy*; need to force evaluation sometimes.

- when you have lots of functions in a pipe, it's sometimes hard to figure out
  where things go wrong. Take a small stream and add functions to your pipe one
  by one from the first/leftmost until you find the broken one.

# other examples

As I mentioned, I've been using streaming patterns more and more in my own
work. Here's some streaming image analysis examples:

- [streaming image montage](https://github.com/microscopium/microscopium/blob/master/microscopium/preprocess.py#L848)
- streaming illumination
  [finding](https://github.com/microscopium/microscopium/blob/master/microscopium/preprocess.py#L567)
  and [correction](https://github.com/microscopium/microscopium/blob/master/microscopium/preprocess.py#L587)
- [estimate](https://github.com/microscopium/microscopium/blob/master/microscopium/preprocess.py#L639)
  range of pixel intensity over many images

If you take 1s/image, for 1M images you take about 12h. Totally doable. No need
for cloud/compute clusters.


# in conclusion

- streaming in Python is easy when you use a few abstractions
- streaming can make you more productive:
    - big data takes linearly longer than small data (no nasty memory swapping)
    - don't need a bigger machine
    - if your tests pass on small data, they'll pass on big data
- streaming code is concise and readable using toolz (cytoolz for speed)

Read more on Matt Rocklin's blog!


# notes for follow-up email based on in-person questions

- CyToolz is a version of Toolz written in Cython. It's much faster than Toolz,
  but it is much worse for debugging. My advice is to use Toolz for
  development, then switch to CyToolz for production.
- `tz.pipe(a, f1, f2, f3)` is shorthand for `f3(f2(f1(a)))`. imho `pipe` makes
  these calls much more readable.
- to force evaluation of an iterator when you don't care about the result,
  only the side effects, use `tz.last`. For example, in my streaming PCA
  example, I used `list()` to force the evaluation of the call to `pipe`, but
  then you end up with a (potentially big) list. `tz.last` gives you the last
  element of an iterator, so it necessarily evaluates every element of the
  iterator. I've changed the example in these notes to reflect this.
- I also mentioned that you can iterate over more things than you think in
  Python. For example, you can use the `requests` library to iterate over a
  remote file, never storing the full dataset on your computer. Similarly, you
  can stream over a gzip-encoded text file.
- Time to reiterate my take-home: think about whether you can stream over a
  dataset, and if you can, do it. Your future self will thank you. Doing it
  later is [harder](https://pbs.twimg.com/media/CDxc6HTVIAAsiFO.jpg). ;)

# more reading

- As mentioned, [Matt Rocklin's blog](http://matthewrocklin.com/blog/). Start
  around early 2013 and work your way to the present day.
- [This post](http://matthewrocklin.com/blog/work/2013/11/15/Functional-Wordcount)
  is the one that really started me on this road.
- I've tried to make the point that streaming saves you *coding time* by
  letting you process data on your laptop, without spinning up a compute
  cluster. Often, you'd get there a bit faster with a cluster. But don't
  overestimate the *computational* overhead of a cluster. Frank McSherry has a
  couple of [posts](http://www.frankmcsherry.org/graph/scalability/cost/2015/02/04/COST2.html)
  doing the rounds, in which he shows graph analysis is *faster* streaming on
  his laptop than on common specialised compute cluster frameworks.
