import pathlib

from SCons.Builder import Builder
from SCons.Node import Node
from SCons.Node.FS import Dir
from SCons.Scanner import Scanner


def sphinx_source_scanner(node: Node, env, path):
    path = pathlib.Path(node.get_abspath())
    all_files = [env.File(str(p)) for p in path.glob("**/*") if p.is_file() and "__pycache__" not
                                                               in p.parts]
    return all_files

def sphinx_target_emitter(target, source, env):
    # Sphinx does its own dependency checking
    target[0].always_build = True
    return target, source

Sphinx = Builder(
    action="sphinx-build $SOURCE $TARGET",
    source_factory=Dir,
    target_factory=Dir,
    source_scanner=Scanner(sphinx_source_scanner),
    emitter=sphinx_target_emitter,
)