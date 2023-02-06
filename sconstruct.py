from typing import TYPE_CHECKING

import scons517

if TYPE_CHECKING:
    from SCons.Environment import Environment

env: Environment = Environment(
    tools=["default", scons517.tool],
)

tag = "py38-none-any"
sources = env.Glob("scons517/*.py")

wheel = scons517.wheel.Wheel(
    env,
    tag=tag,
    root_is_purelib=True,
)
wheel.add_sources(sources)

sdist = scons517.wheel.SDist(env, sources + ["pyproject.toml", "sconstruct.py", "README.md"])
editable = scons517.wheel.Editable(env, tag)

env.Alias("wheel", wheel.target)
env.Alias("sdist", sdist)
env.Alias("editable", editable)
env.Default("wheel", "sdist")
