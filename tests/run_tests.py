import contextlib
import subprocess
import sys
import tempfile
import unittest
import pathlib
import build.env
import os.path

current_dir = pathlib.Path(__file__).parent
examples_dir = current_dir / "examples"
scons517_dir = current_dir.parent

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

    def _copy_file(self, example_file, destname):
        with open(examples_dir / example_file) as infile:
            self.root_dir.joinpath(destname).write_text(infile.read())

    def test(self):
        self._copy_file("module.py", "module.py")
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
        self.root_dir.joinpath("sconstruct.py").write_text(f"""
import scons517
env = Environment(tools=["default", scons517.tool])
tag = "py38-none-any"
wheel = env.Wheel(tag=tag)
wheel.add_sources(["module.py"])
sdist=env.SDist(["pyproject.toml", "sconstruct.py", "module.py"])
env.Alias("wheel", wheel.target)
env.Alias("sdist", sdist)
        """)

        builder = build.ProjectBuilder(self.root_dir)
        whl_path = builder.build("wheel", self.root_dir / "dist")

        self.install_env.install([f"testproject@file://{whl_path}"])
        self._execute_install_env("module", "example")

    def _execute_install_env(self, module, function):
        cmd = [
            os.path.join(self.install_env.path, "bin/python"),
            "-c",
            f"import {module}; {module}.{function}()"
        ]
        try:
            subp = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print(e.output.decode(), end='', file=sys.stderr)
            raise e
        self.assertEqual(subp.stdout.decode().strip(), "Hello, world!")