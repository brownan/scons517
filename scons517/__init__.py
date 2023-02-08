import pathlib
from typing import Iterable, List, Union

import packaging.tags
from SCons.Environment import Environment
from SCons.Util import flatten


def tool(env: Environment):
    import scons517.extension
    import scons517.wheel
    scons517.wheel.generate(env)
    scons517.extension.generate(env)


def get_binary_tag():
    """Gets the most specific binary tag for the current machine"""
    # This looks through sys_tags() for the first tag that doesn't use the manylinux platform.
    # Why do we skip the manylinux platform?
    #
    # sys_tags() lists tags compatible with the current system in order. since
    # the generic linux_x86_64 platform is not a precise enough tag to guarantee compatibility,
    # the packaging library considers "manylinux" to be a higher priority for installation
    # candidates.
    #
    # However, we are not choosing an installation candidate, we want to find a tag for the
    # distribution being built, so our priorities are a bit different. Instead, it makes sense
    # for linux builds to use the imprecise linux_x86_64 (or similar) platform, since
    # we cannot programmatically guarantee platform compatibility with the manylinux spec.
    # In the future, maybe there is some way to incorporate functionality from the "auditwheel"
    # tool to automatically determine a more precise linux platform.
    return str(
        next(tag for tag in packaging.tags.sys_tags() if "manylinux" not in tag.platform)
    )


def get_pure_tag():
    """Gets the tag for a pure-python wheel with no platform specific aspects compatible
    with the current python version and up

    """
    interp_tag = (
        f"py{packaging.tags.interpreter_version()}"
    )
    return f"{interp_tag}-none-any"


PathLike = Union[str, pathlib.Path, "Base"]

def arg2nodes(objs: Union[PathLike , List[PathLike]], node_factory):
    """Turns strings or path objects into nodes. Similar to the
    build-in Environment.arg2nodes, but supports Path objects.

    """
    if not objs:
        return []
    objs_flattened: List[PathLike] = flatten(objs, SequenceTypes=Iterable)

    nodes = []
    for obj in objs_flattened:
        if isinstance(obj, str):
            nodes.append(node_factory(obj))
        elif isinstance(obj, pathlib.Path):
            nodes.append(node_factory(str(obj)))
        else:
            nodes.append(obj)
    return nodes
