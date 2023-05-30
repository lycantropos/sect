sect
====

[![](https://github.com/lycantropos/sect/workflows/CI/badge.svg)](https://github.com/lycantropos/sect/actions/workflows/ci.yml "Github Actions")
[![](https://readthedocs.org/projects/sect/badge/?version=latest)](https://sect.readthedocs.io/en/latest "Documentation")
[![](https://codecov.io/gh/lycantropos/sect/branch/master/graph/badge.svg)](https://codecov.io/gh/lycantropos/sect "Codecov")
[![](https://img.shields.io/github/license/lycantropos/sect.svg)](https://github.com/lycantropos/sect/blob/master/LICENSE "License")
[![](https://badge.fury.io/py/sect.svg)](https://badge.fury.io/py/sect "PyPI")

In what follows `python` is an alias for `python3.7` or `pypy3.7`
or any later version (`python3.8`, `pypy3.8` and so on).

Installation
------------

Install the latest `pip` & `setuptools` packages versions
```bash
python -m pip install --upgrade pip setuptools
```

### User

Download and install the latest stable version from `PyPI` repository
```bash
python -m pip install --upgrade sect
```

### Developer

Download the latest version from `GitHub` repository
```bash
git clone https://github.com/lycantropos/sect.git
cd sect
```

Install dependencies
```bash
python -m pip install -r requirements.txt
```

Install
```bash
python setup.py install
```

Usage
-----
```python
>>> from ground.base import get_context
>>> from sect.triangulation import Triangulation
>>> context = get_context()
>>> Contour, Point = context.contour_cls, context.point_cls
>>> (Triangulation.delaunay([Point(0, 0), Point(1, 0), Point(0, 1)],
...                         context=context).triangles()
...  == [Contour([Point(0, 0), Point(1, 0), Point(0, 1)])])
True
>>> (Triangulation.delaunay([Point(0, 0), Point(3, 0), Point(1, 1),
...                          Point(0, 3)],
...                         context=context).triangles()
...  == [Contour([Point(0, 0), Point(3, 0), Point(1, 1)]),
...      Contour([Point(0, 0), Point(1, 1), Point(0, 3)]),
...      Contour([Point(0, 3), Point(1, 1), Point(3, 0)])])
True
>>> (Triangulation.delaunay([Point(0, 0), Point(1, 0), Point(1, 1),
...                          Point(0, 1)],
...                         context=context).triangles()
...  == [Contour([Point(0, 1), Point(1, 0), Point(1, 1)]),
...      Contour([Point(0, 0), Point(1, 0), Point(0, 1)])])
True
>>> Polygon = context.polygon_cls
>>> (
...      Triangulation.constrained_delaunay(
...          Polygon(Contour([Point(0, 0), Point(1, 0), Point(0, 1)]), []),
...          context=context
...      ).triangles()
...      == [Contour([Point(0, 0), Point(1, 0), Point(0, 1)])]
... )
True
>>> (
...      Triangulation.constrained_delaunay(
...          Polygon(Contour([Point(0, 0), Point(3, 0), Point(1, 1),
...                           Point(0, 3)]),
...                  []),
...          context=context
...      ).triangles()
...      == [Contour([Point(0, 0), Point(3, 0), Point(1, 1)]),
...          Contour([Point(0, 0), Point(1, 1), Point(0, 3)])]
... )
True
>>> (
...      Triangulation.constrained_delaunay(
...          Polygon(Contour([Point(0, 0), Point(4, 0), Point(0, 4)]),
...                  [Contour([Point(0, 0), Point(1, 2), Point(2, 1)])]),
...          context=context
...      ).triangles()
...      == [Contour([Point(0, 0), Point(4, 0), Point(2, 1)]),
...          Contour([Point(1, 2), Point(2, 1), Point(4, 0)]),
...          Contour([Point(0, 4), Point(1, 2), Point(4, 0)]),
...          Contour([Point(0, 0), Point(1, 2), Point(0, 4)])]
... )
True
>>> from sect.decomposition import Graph
>>> graph = Graph.from_polygon(Polygon(Contour([Point(0, 0), Point(6, 0),
...                                             Point(6, 6), Point(0, 6)]),
...                                    [Contour([Point(2, 2), Point(2, 4),
...                                              Point(4, 4), Point(4, 2)])]),
...                            context=context)
>>> Point(0, 0) in graph
True
>>> Point(1, 1) in graph
True
>>> Point(2, 2) in graph
True
>>> Point(3, 3) in graph
False
>>> from ground.base import Location
>>> graph.locate(Point(0, 0)) is Location.BOUNDARY
True
>>> graph.locate(Point(1, 1)) is Location.INTERIOR
True
>>> graph.locate(Point(2, 2)) is Location.BOUNDARY
True
>>> graph.locate(Point(3, 3)) is Location.EXTERIOR
True

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

Install dependencies
```bash
python -m pip install -r requirements-tests.txt
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

`Bash` script:
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

`PowerShell` script:
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
