import scons517

env = Environment(tools=["default", scons517.tool])

tag = scons517.get_pure_tag()

wheel = env.Wheel(tag=tag)
wheel.add_sources(["module.py"])

sdist=env.SDist(["pyproject.toml", "sconstruct.py", "module.py"])

env.Alias("wheel", wheel.target)
env.Alias("sdist", sdist)
