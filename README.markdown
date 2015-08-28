# Notes from a talk about streaming programming patterns

### IPython notebook from EuroSciPy 2015

`'Big data in little laptop.ipynb'` contains the IPython notebook used.

Download the Drosophila genome file from
[here](http://hgdownload.soe.ucsc.edu/goldenPath/dm6/bigZips/dm6.fa.gz),
unzip it, and place it in the `data` directory.

If you use Anaconda and Python 3.4, it should just work!

### (Given at Melbourne Python Users Group meeting 2015-05-04)

`notes.markdown` is the (enhanced post-talk) script I was following. You should
be able to run it using [notedown](https://github.com/aaren/notedown).

Use [conda](http://conda.pydata.org/docs/index.html) to recreate the
environment I used for the demo. You can use the
[`conda env`](http://conda.pydata.org/docs/commands/env/conda-env-create.html)
command with the environment descriptor `environment.yml` file.

`session.py` is the log of the IPython session I did during the talk, warts and
all.

`nxeuler.py` contains some helper functions for the genome assembly example,
which I didn't get to in the talk but is in the notes.

`iris.csv` and `sample.fasta` are the sample datasets used in various parts of
the notebook.

