import scons517.wheel
import scons517.extension

from SCons.Environment import Environment


def tool(env: Environment):
    scons517.wheel.generate(env)
    scons517.extension.generate(env)
