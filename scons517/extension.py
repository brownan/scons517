import os.path
import shlex
import subprocess
import sys
import sysconfig
from typing import TYPE_CHECKING, List, Optional, Sequence

import SCons.Action

from scons517.wheel import get_build_path, get_rel_path
from scons517 import arg2nodes

if TYPE_CHECKING:
    from SCons.Node.FS import Dir, File


def configure_compiler_env(env):
    # Get compiler and compiler options we need to build a python extension module
    (cc, cxx, cflags, ccshared, ldshared, ext_suffix,) = sysconfig.get_config_vars(
        "CC",
        "CXX",
        "CFLAGS",
        "CCSHARED",
        "LDSHARED",
        "EXT_SUFFIX",
    )

    paths = sysconfig.get_paths()

    include_dirs = {
        paths["include"],
        paths["platinclude"],
    }

    # Include Virtualenv
    if sys.exec_prefix != sys.base_exec_prefix:
        include_dirs.add(os.path.join(sys.exec_prefix, "include"))

    # Platform library directories
    library_dirs = {
        paths["stdlib"],
        paths["platstdlib"],
    }

    # Set compilers and flags
    env["CC"] = cc
    env["CXX"] = cxx
    env["SHLINK"] = ldshared
    env.Prepend(
        CFLAGS=shlex.split(cflags),
        CPPPATH=list(include_dirs),
        LIBPATH=list(library_dirs),
    )
    env.Replace(
        SHCFLAGS=shlex.split(ccshared) + env["CFLAGS"],
    )

    # Naming convention for extension module shared objects
    env["SHLIBSUFFIX"] = ext_suffix
    env["SHLIBPREFIX"] = ""


def ExtModule(
    env,
    modsource: "File",
    extra_sources: Optional[Sequence["File"]] = None,
):
    """Compiles and adds an extension module to a wheel"""
    env = env.Clone()
    configure_compiler_env(env)

    platform_specifier = f"{sysconfig.get_platform()}-{sys.implementation.cache_tag}"
    build_dir: "Dir" = env["WHEEL_BUILD_DIR"].Dir(f"temp.{platform_specifier}")
    lib_dir: "Dir" = env["WHEEL_BUILD_DIR"].Dir(f"lib.{platform_specifier}")

    modsource = arg2nodes(modsource, env.File)[0]

    source_files = [modsource]

    if extra_sources:
        source_files.extend(arg2nodes(extra_sources, env.File))

    objects = []
    for node in source_files:
        obj = get_build_path(env, node, build_dir, "")
        objects.append(env.SharedObject(target=str(obj), source=node))

    so = get_build_path(env, modsource, lib_dir, "")
    library = env.SharedLibrary(target=str(so), source=objects)

    return library


def _cython_action(target: List["File"], source: List["File"], env):
    subprocess.check_call(
        [
            "cython",
            "-3",
            "-o", target[0].get_abspath(),
            source[0].get_relpath(),
        ],
    )

CythonAction = SCons.Action.Action(
    _cython_action,
    "Cythonizing $SOURCE",
)


def CythonModule(env, source: "File"):
    source = arg2nodes(source, env.File)[0]
    target = get_build_path(env, source, "cython", ".c")
    c_source = env.Command(target, source, CythonAction)
    return ExtModule(env, c_source)


def InstallInplace(
    env,
    ext_module: "File",
):
    targets = []
    ext_modules = arg2nodes(ext_module, env.File)
    for module in ext_modules:
        relpath = get_rel_path(env, module)
        targets.extend(env.InstallAs(relpath, module))
    # When cleaning the inplace target, don't clear out the built shared objects from the build
    # directory, so running this target again is quick.
    # Usually scons clean mode will remove the target and all dependencies, but this is an
    # exception where we want to leave all dependencies. I'm not sure a better way to do this.
    # NoClean is conditionally applied so that cleaning other targets /does/ remove temp files
    if env.GetOption("clean"):
        deps = list(ext_modules)
        while deps:
            dep = deps.pop()
            env.NoClean(dep)
            deps.extend(dep.sources)
    return targets


def generate(env, **kwargs):
    env.AddMethod(ExtModule)
    env.AddMethod(InstallInplace)
    env.AddMethod(CythonModule)
