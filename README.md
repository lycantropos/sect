sect
====

[![](https://travis-ci.com/lycantropos/sect.svg?branch=master)](https://travis-ci.com/lycantropos/sect "Travis CI")
[![](https://dev.azure.com/lycantropos/sect/_apis/build/status/lycantropos.sect?branchName=master)](https://dev.azure.com/lycantropos/sect/_build/latest?definitionId=23&branchName=master "Azure Pipelines")
[![](https://codecov.io/gh/lycantropos/sect/branch/master/graph/badge.svg)](https://codecov.io/gh/lycantropos/sect "Codecov")
[![](https://img.shields.io/github/license/lycantropos/sect.svg)](https://github.com/lycantropos/sect/blob/master/LICENSE "License")
[![](https://badge.fury.io/py/sect.svg)](https://badge.fury.io/py/sect "PyPI")

In what follows
- `python` is an alias for `python3.5` or any later
version (`python3.6` and so on),
- `pypy` is an alias for `pypy3.5` or any later
version (`pypy3.6` and so on).

Installation
------------

Install the latest `pip` & `setuptools` packages versions:
- with `CPython`
  ```bash
  python -m pip install --upgrade pip setuptools
  ```
- with `PyPy`
  ```bash
  pypy -m pip install --upgrade pip setuptools
  ```

### User

Download and install the latest stable version from `PyPI` repository:
- with `CPython`
  ```bash
  python -m pip install --upgrade sect
  ```
- with `PyPy`
  ```bash
  pypy -m pip install --upgrade sect
  ```

### Developer

Download the latest version from `GitHub` repository
```bash
git clone https://github.com/lycantropos/sect.git
cd sect
```

Install dependencies:
- with `CPython`
  ```bash
  python -m pip install --force-reinstall -r requirements.txt
  ```
- with `PyPy`
  ```bash
  pypy -m pip install --force-reinstall -r requirements.txt
  ```

Install:
- with `CPython`
  ```bash
  python setup.py install
  ```
- with `PyPy`
  ```bash
  pypy setup.py install
  ```

Usage
-----
```python
>>> from sect.triangulation import delaunay_triangles
>>> delaunay_triangles([(0, 0), (1, 0), (0, 1)])
[((0, 0), (1, 0), (0, 1))]
>>> delaunay_triangles([(0, 0), (3, 0), (1, 1), (0, 3)])
[((0, 0), (3, 0), (1, 1)), ((0, 0), (1, 1), (0, 3)), ((0, 3), (1, 1), (3, 0))]
>>> delaunay_triangles([(0, 0), (1, 0), (1, 1), (0, 1)])
[((0, 1), (1, 0), (1, 1)), ((0, 0), (1, 0), (0, 1))]
>>> from sect.triangulation import constrained_delaunay_triangles
>>> constrained_delaunay_triangles([(0, 0), (1, 0), (0, 1)])
[((0, 0), (1, 0), (0, 1))]
>>> constrained_delaunay_triangles([(0, 0), (3, 0), (1, 1), (0, 3)])
[((0, 0), (3, 0), (1, 1)), ((0, 0), (1, 1), (0, 3))]
>>> constrained_delaunay_triangles([(0, 0), (4, 0), (0, 4)],
...                                [[(0, 0), (2, 1), (1, 2)]])
[((0, 0), (4, 0), (2, 1)), ((0, 4), (2, 1), (4, 0)), ((0, 0), (1, 2), (0, 4)), ((0, 4), (1, 2), (2, 1))]

```

Development
-----------

### Bumping version

#### Preparation

Install
[bump2version](https://github.com/c4urself/bump2version#installation).

#### Pre-release

Choose which version number category to bump following [semver
specification](http://semver.org/).

Test bumping version
```bash
bump2version --dry-run --verbose $CATEGORY
```

where `$CATEGORY` is the target version number category name, possible
values are `patch`/`minor`/`major`.

Bump version
```bash
bump2version --verbose $CATEGORY
```

This will set version to `major.minor.patch-alpha`. 

#### Release

Test bumping version
```bash
bump2version --dry-run --verbose release
```

Bump version
```bash
bump2version --verbose release
```

This will set version to `major.minor.patch`.

### Running tests

Install dependencies:
- with `CPython`
  ```bash
  python -m pip install --force-reinstall -r requirements-tests.txt
  ```
- with `PyPy`
  ```bash
  pypy -m pip install --force-reinstall -r requirements-tests.txt
  ```

Plain
```bash
pytest
```

Inside `Docker` container:
- with `CPython`
  ```bash
  docker-compose --file docker-compose.cpython.yml up
  ```
- with `PyPy`
  ```bash
  docker-compose --file docker-compose.pypy.yml up
  ```

`Bash` script (e.g. can be used in `Git` hooks):
- with `CPython`
  ```bash
  ./run-tests.sh
  ```
  or
  ```bash
  ./run-tests.sh cpython
  ```

- with `PyPy`
  ```bash
  ./run-tests.sh pypy
  ```

`PowerShell` script (e.g. can be used in `Git` hooks):
- with `CPython`
  ```powershell
  .\run-tests.ps1
  ```
  or
  ```powershell
  .\run-tests.ps1 cpython
  ```
- with `PyPy`
  ```powershell
  .\run-tests.ps1 pypy
  ```
