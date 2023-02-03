import packaging.tags
from SCons.Environment import Environment

import scons517.extension
import scons517.wheel


def tool(env: Environment):
    scons517.wheel.generate(env)
    scons517.extension.generate(env)


def get_binary_tag():
    """Gets the most specific binary tag for the current machine"""
    return str(
        next(tag for tag in packaging.tags.sys_tags() if "manylinux" not in tag.platform)
    )


def get_pure_tag():
    """Gets the tag for a pure-python wheel with no platform specific aspects"""
    interp_tag = (
        f"{packaging.tags.interpreter_name()}{packaging.tags.interpreter_version()}"
    )
    return f"{interp_tag}-none-any"
