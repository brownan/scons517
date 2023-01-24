import contextlib
import subprocess
import sys
import tempfile
import unittest
import pathlib
import build.env
import os.path

import scons517

current_dir = pathlib.Path(__file__).parent
examples_dir = current_dir / "examples"
scons517_dir = current_dir.parent


def _subp_exec(cmd, cwd=None):
    try:
        subp = subprocess.run(cmd, cwd=cwd,
                              check=True, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              )
    except subprocess.CalledProcessError as e:
        print(e.output.decode(), end='', file=sys.stderr)
        raise e
    return subp.stdout.decode()


class TestScons517(unittest.TestCase):
    def setUp(self):
        with contextlib.ExitStack() as stack:
            # Root of our fake "test" package
            self.root_dir = pathlib.Path(stack.enter_context(tempfile.TemporaryDirectory()))

            # Isolated virtual environment which we'll be installing our build test
            # packages into
            self.install_env: build.env._IsolatedEnvVenvPip
            self.install_env = stack.enter_context(build.env.IsolatedEnvBuilder())
            self.install_env.install(["pip>=22.3.1"])

            self.context = stack.pop_all()


    def tearDown(self) -> None:
        self.context.__exit__(None, None, None)

    def _copy_file(self, example_file):
        """Copy a file into the fake source directory"""
        with open(examples_dir / example_file) as infile:
            self.root_dir.joinpath(example_file).write_text(infile.read())

    def _assert_installed_module(self, module, function):
        """Runs a python function in the install environment and
        asserts that it prints Hello, world!
        """
        cmd = [
            os.path.join(self.install_env.path, "bin/python"),
            "-c",
            f"import {module}; {module}.{function}()"
        ]
        output = _subp_exec(cmd)
        self.assertEqual(output.strip(), "Hello, world!")

    def _write_pyproject(self):
        self.root_dir.joinpath("pyproject.toml").write_text(f"""
[build-system]
build-backend = "scons517.api"
requires = [
    "scons517 @ file://{scons517_dir.resolve()}"
]
[project]
name = "testproject"
version = "1.0.0"
        """)

    def _write_sconstruct(self, contents: str):
        self.root_dir.joinpath("sconstruct.py").write_text(contents)

    def test_pure_python(self):
        """Builds a wheel containing a single python module"""
        self._copy_file("module.py")
        self._write_pyproject()
        self._write_sconstruct(f"""
import scons517
env = Environment(tools=["default", scons517.tool])
tag = {scons517.get_pure_tag()!r}
wheel = env.Wheel(tag=tag)
wheel.add_sources(["module.py"])
sdist=env.SDist(["pyproject.toml", "sconstruct.py", "module.py"])
env.Alias("wheel", wheel.target)
env.Alias("sdist", sdist)
        """)

        self._build_and_install()
        self._assert_installed_module("module", "example")

    def _build_and_install(self):
        builder = build.ProjectBuilder(self.root_dir)
        whl_path = builder.build("wheel", self.root_dir / "dist")
        self.install_env.install([f"testproject@file://{whl_path}"])

    def test_extension_module(self):
        self._copy_file("extension.c")
        self._write_pyproject()
        self._write_sconstruct(f"""
import scons517
env = Environment(tools=["default", scons517.tool])
tag = {scons517.get_binary_tag()!r}
wheel = env.Wheel(tag=tag)
wheel.add_sources(env.ExtModule("extension.c"))
sdist =env.SDist(["pyproject.toml", "sconstruct.py", "extension.c"])
env.Alias("wheel", wheel.target)
env.Alias("sdist", sdist)
        """)

        self._build_and_install()
        self._assert_installed_module("extension", "example")

    def test_install_inplace(self):
        self._copy_file("extension.c")
        self._write_pyproject()
        self._write_sconstruct(f"""
import scons517
env = Environment(tools=["default", scons517.tool])
tag = {scons517.get_binary_tag()!r}
wheel = env.Wheel(tag=tag)
inplace = env.InstallInplace(env.ExtModule("extension.c"))
env.Alias("inplace", inplace)
        """)
        _subp_exec([
            "scons", "inplace"
        ], cwd=self.root_dir)
        output = _subp_exec([
            sys.executable,
            "-c",
            "import extension; extension.example()",
        ], cwd=self.root_dir)
        self.assertEqual(output.strip(), "Hello, world!")

    def test_cython(self):
        self._copy_file("cythonmod.pyx")
        self._write_pyproject()
        self._write_sconstruct(f"""
import scons517
env = Environment(tools=["default", scons517.tool])
tag = {scons517.get_binary_tag()!r}
wheel = env.Wheel(tag=tag)
wheel.add_sources(env.CythonModule("cythonmod.pyx"))
sdist =env.SDist(["pyproject.toml", "sconstruct.py", "cythonmod.pyx"])
env.Alias("wheel", wheel.target)
env.Alias("sdist", sdist)
        """)

        self._build_and_install()
        self._assert_installed_module("cythonmod", "example")
