import os.path
import tempfile
from typing import Optional

import SCons.Node.Alias
import SCons.Script.Main
import SCons.Script.SConsOptions


def _launch_scons(args):
    with tempfile.TemporaryDirectory() as build_dir:
        args.append(f"WHEEL_BUILD_DIR={build_dir}")
        args.append("--silent")

        # Make an scons option parser and pass our own args into it, instead of sys.argv
        parser = SCons.Script.SConsOptions.Parser("")
        parser.parse_args(args)

        # Call into the main scons entry point
        SCons.Script.Main._main(parser)

    # Now look at the output of the target node
    target: str = str(SCons.Script.BUILD_TARGETS[0])
    alias: SCons.Node.Alias.Alias = SCons.Script.Alias(target)[0]
    node: SCons.Node.Node = alias.sources[0]
    filename = os.path.basename(str(node))
    return filename


def build_wheel(
    wheel_directory: str,
    config_settings: Optional[dict] = None,
    metadata_directory: Optional[str] = None,
):
    return _launch_scons([f"WHEEL_DIR={wheel_directory}", "wheel"])


def build_sdist(sdist_directory: str, config_settings: Optional[dict] = None):
    return _launch_scons([f"SDIST_DIR={sdist_directory}", "sdist"])


def build_editable(
    wheel_directory: str,
    config_settings: Optional[dict] = None,
    metadata_directory: Optional[str] = None,
):
    return _launch_scons([f"EDITABLE_DIR={wheel_directory}", "editable"])
