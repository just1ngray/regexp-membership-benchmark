# Regular Expression Membership Benchmarking

This is a __simplified__ version of my [undergraduate honour's project](https://github.com/just1ngray/SMUHon-Practical-RE-Membership-Algs) at Saint Mary's University from May 2021 to April 2022. Instead of using practical regular expressions with wildcard matches, character classes, and anchors, this repository uses theoretical regular expressions limited to their basic mathematical definition.

This repository is currently configured and set-up to test various partial derivative related algorithms on the one-word membership problem. Partial derivative algorithms gain their efficiency by using the theorem that $|pd(r)| \leq |r|_\Sigma$. This says that given a regular expression $r$ we cannot derive (through 0 or more steps) more than the alphabet length of $r$ partial derivatives from it. However, checking equality of regular expression (trees) has proven expensive in practice, and the theoretical benefits have been somewhat out of reach. Notably, in my honour's project we found that constructing the PDDAG NFA and then deciding membership on it was usually faster than using partial derivatives directly. This does not make sense since we needlessly compute useless states in the PDDAG NFA with respect to deciding membership of an arbitrary word $w$ (there may be some states in the NFA that are never visited while deciding membership of $w$). We also test the follow NFA construction + NFA membership since it was shown to be efficient in both construction time and size.

## Methodology
1. Populate the `data/regexps.txt` file with one regular expression per line
1. Find an untested regular expression $r$ from `data/regexps.txt`
1. Use pairwise language generation to find a set of words $\subseteq L(r)$
1. Using the accepted words, apply single-symbol deletion on each word to find a set of rejecting words $\subseteq \Sigma ^* \backslash L(r)$
1. For each specified method in `methods.py::METHODS`, decide membership for each accepting and rejecting word and measure the time taken
1. Mark the regular expression as done
1. Perform the analysis


## Installation

### Requirements
- git
- Python 3.10 and a corresponding pip installation. [pyenv](https://github.com/pyenv/pyenv) is highly recommended
- [Microsoft PICT](https://github.com/Microsoft/pict/): simply git clone, build, and move the `build/cli/pict` into your bin

### Install
```bash
$ git clone https://github.com/just1ngray/regexp-membership-benchmark
$ cd regexp-membership-benchmark
$ pip install -r requirements.txt
```


## Usage

### config.yaml
Edit the configuration file to change the parameters of the experiment. There are comments inside this file to explain what each option does.

### The regular expression file
Using `$ python generate_regexps.py` and the options in `config.yaml`, you can generate a list of regular expressions to test.

Alternatively you can manually create the regexps file (i.e., `data/regexps.txt`) with one regular expression per line. Note that the regular expressions __must__ be parsable using FAdo's [str2regexp](https://www.dcc.fc.up.pt/~rvr/FAdoDoc/index.html) parser. You could also write your own parser and hook it into the `converters.py` module if you choose.

### Testing/benchmarking regular expressions
Using `$ python run_benchmarks.py` you can test the regular expressions. Note you can interrupt this process (Ctrl+C) without issue as it may take some time. Start where you left off by re-executing the command. To restart the benchmark, delete the todo (and optionally output) data files.

### Analysis
`$ python analysis.py` TODO