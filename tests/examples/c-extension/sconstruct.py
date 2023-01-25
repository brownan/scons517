import scons517

env = Environment(tools=["default", scons517.tool])

tag = scons517.get_binary_tag()

wheel = env.Wheel(tag=tag)
wheel.add_sources(env.ExtModule("extension.c"))

sdist =env.SDist(["pyproject.toml", "sconstruct.py", "extension.c"])

env.Alias("wheel", wheel.target)
env.Alias("sdist", sdist)