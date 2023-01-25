import contextlib
import os.path
import pathlib
import subprocess
import sys
import tarfile
import tempfile
import unittest

import build.env

current_dir = pathlib.Path(__file__).parent
examples_dir = current_dir / "examples"
scons517_dir = current_dir.parent


def _subp_exec(cmd, cwd=None):
    try:
        subp = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        print(e.output.decode(), end="", file=sys.stderr)
        raise e
    return subp.stdout.decode()


class TestScons517(unittest.TestCase):
    def setUp(self):
        with contextlib.ExitStack() as stack:
            # Temp dir for built wheels
            self.dist_dir = stack.enter_context(tempfile.TemporaryDirectory())

            # Isolated virtual environment with which we'll build packages in
            self.build_env = stack.enter_context(build.env.IsolatedEnvBuilder())
            self.build_env.install(["pip>=22.3.1"])
            self.build_env.install(
                ["scons517 @ file://{}".format(os.path.abspath(scons517_dir))]
            )

            # Isolated virtual environment which we'll be installing our built test
            # packages into
            self.install_env: build.env._IsolatedEnvVenvPip
            self.install_env = stack.enter_context(build.env.IsolatedEnvBuilder())
            self.install_env.install(["pip>=22.3.1"])

            self.context = stack.pop_all()

    def tearDown(self) -> None:
        self.context.__exit__(None, None, None)

    def _assert_installed_module(self, module, function):
        """Runs a python function in the install environment and
        asserts that it prints Hello, world!
        """
        cmd = [
            os.path.join(self.install_env.path, "bin/python"),
            "-c",
            f"import {module}; {module}.{function}()",
        ]
        output = _subp_exec(cmd)
        self.assertEqual(output.strip(), "Hello, world!")

    def _make_isolated_builder(self, src_dir):
        builder = build.ProjectBuilder(src_dir)
        builder.python_executable = self.build_env.executable
        builder.scripts_dir = self.build_env.scripts_dir
        self.build_env.install(builder.build_system_requires)
        return builder

    def _build_sdist(self, proj_dir):
        """Build an sdist from the given example project in an isolated environment."""
        builder = self._make_isolated_builder(proj_dir)
        return builder.build("sdist", self.dist_dir)

    def _build_wheel_from_sdist(self, sdist_path):
        """Builds a wheel from an sdist"""
        sdist_name = os.path.basename(sdist_path)[: -len(".tar.gz")]
        sdist_extract_dir = self.context.enter_context(tempfile.TemporaryDirectory())
        with tarfile.open(sdist_path) as t:
            t.extractall(sdist_extract_dir)
        builder = self._make_isolated_builder(
            os.path.join(sdist_extract_dir, sdist_name)
        )
        return builder.build("wheel", self.dist_dir)

    def _build_and_install(self, proj_dir):
        sdist = self._build_sdist(proj_dir)
        wheel = os.path.abspath(self._build_wheel_from_sdist(sdist))
        self.install_env.install([f"testproject@file://{wheel}"])

    def test_pure_python_ex(self):
        """Tests the pure python example project"""
        proj_dir = examples_dir / "pure-python"
        self._build_and_install(proj_dir)
        self._assert_installed_module("module", "example")

    def test_extension_module(self):
        """Tests the example project with a compiled C extension"""
        proj_dir = examples_dir / "c-extension"
        self._build_and_install(proj_dir)
        self._assert_installed_module("extension", "example")

    def test_cython(self):
        proj_dir = examples_dir / "cython"
        self._build_and_install(proj_dir)
        self._assert_installed_module("cythonmod", "example")

    def test_install_inplace(self):
        # Install environment needs the build requirements
        self.install_env.install(
            ["scons517 @ file://{}".format(os.path.abspath(scons517_dir))]
        )
        _subp_exec(
            [
                self.install_env.executable,
                "-m",
                "pip",
                "install",
                "--no-build-isolation",
                "-e",
                str(examples_dir / "pure-python"),
            ]
        )
        self._assert_installed_module("module", "example")
