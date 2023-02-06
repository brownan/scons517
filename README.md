# Scons517

Pep 517 compliant Python Distribution Wheel Builder

This project's primary goal is to provide a simple and extensible set of tools for building
Python wheels *without* using setuptools. Setuptools has served the Python community well,
but I've often been frustrated when trying to extend it in uncommon ways.

For example, extending setuptools to also run build steps such as building a webpack bundle or
running Django's collectstatic routine are non-trivial to add.

This led me to the [enscons](https://github.com/dholth/enscons) project which provides a
set of wheel building tools on top of the [Scons](https://scons.org/) build framework.
Enscons works well (and you should use it if you want a more stable and mature project) but
for compiling C extension modules, it still calls into setuptools under the hood.

So this project started out as an experiment to see if I could eliminate setuptools *entirely*
and still provide C-extension support and the full power of Scons. I also started to re-imagine
the interface to make things (in my opinion) a bit more straightforward.

## Using Scons517
Enough history. How do you use it?

There are two files you need in the root of your project directory:

``pyproject.toml``

This should contain at a minimum a ``[build-system]`` section declaring Scons517 as the build
backend, and a ``[project]`` section with at a minimum a ``name`` and a ``version`` key.

For example:
```toml
[build-system]
build-backend = "scons517.api"
requires = [
    "scons517",
]

[project]
name = "example-project"
version = "0.0.1"
dependencies = [
    "dep1",
    "dep2",
]
readme = "README.md"
```
The formal list of keys allowed in the ``[project]`` table are defined by the PyPA specification
page on [Declaring project metadata](https://packaging.python.org/en/latest/specifications/declaring-project-metadata/)

``sconstruct.py``

This file defines your build targets and how to build them. Here's the minimal boilerplate for a 
pure-python distribution with no platform-specific dependencies:

```python
import scons517

env = Environment(tools=["default", scons517.tool])
tag = scons517.get_pure_tag()
sources = ["add_your_source_files_here.py"]

wheel = env.Wheel(tag=tag)
wheel.add_sources(sources)

sdist = env.SDist(["pyproject.toml", "sconstruct.py"] + sources)

editable = env.Editable(tag, ".")

env.Alias("wheel", wheel.target)
env.Alias("sdist", sdist)
env.Alias("editable", editable)

```
The sconstruct file *must* define the two target aliases ``wheel``, ``sdist``.
An ``editable`` target enables editable installs (``pip install -e``)

For examples compiling extension modules and cython modules, see the `tests/examples/` directory.

## Building a project

Once you have those two files in place, build your wheel using a compatible build frontend
such as [build](https://pypa-build.readthedocs.io/en/stable/index.html)

Install it with
```bash
pip install build
```

Then build your wheel with
```bash
python -m build
```

Your wheel files will be placed in the `dist/` directory by default.
