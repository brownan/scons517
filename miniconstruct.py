import tarfile
import zipfile
from abc import ABC

import minicons

env = minicons.Environment()

class SharedLibraryBuilder(minicons.Builder):
    def __init__(self, env: minicons.Environment, targets: minicons.NodeArg, sources:
    minicons.NodeArg):


# Takes as input: File sources
so_file = SharedLibraryBuilder(env, "path/source.c")
# Returns: Abstract file
# outname: source.so
# rel_path: path/source.so
# build_dir_name = lib-linux-x86_64
# full path: #BUILDDIR / $build_dir_name / $rel_path
# dependencies: path/source.c

# Takes as input: directory target, File input
# Essentially either realizes an abstract file into a concrete file, or copies a concrete
# file to another directory
installed_file = Install(env, "location/", so_file)
# Returns concrete file
# path: location/source.so
# dependencies: so_file (abstract)

# Takes as input: file list input
wheel = Wheel(env, ["pkg/mod.py", so_file])
# Returns abstract file
# name: my_dist-1.0.0-py3-none-any.whl
# build_dir_name: None
# full path: $BUILDDIR / my_dist-1.0.0-py3-none-any.whl
# dependencies: pkg_mod.py, so_file

# Takes as input: sphinx doc directory
docs = SphinxDocs(env, "docs/source/")
# Returns: abstract directory
# name: None (unspecified)
# dependencies: all files under docs/source/

# Wheel builder can add more sources. This custom method takes:
# category dir, files
wheel.add_data("data/html-docs", docs)


"""
Possible builder outputs:
(Abstract or concrete) (file or dir or file list or dir list or file+dir list)
A builder's source must be compatible

Abstract files and directories are not backed by the filesystem. They represent a file
or directory that /can/ exist in the future if another builder needs it.
Abstract directories essentially represent a set of files that are unknown at resolution time
Abstract entries are given a build prefix and a relative path and name
Abstract directories don't generally have a name
Abstract files & directories are written out under the temp directory, with the possible
exception being a single dependent builder which is the Install builder, then it can just
be written directly to the final location.

Concrete files and directories are files and directories in an actual location
somewhere on the filesystem.

Most builders will be abstract builders, which only means their output /location/ is
defined by the builder with which it's used. Builders generally declare what they output,
and how to generate the output from the inputs, but where that output actually goes is up
to the downstream dependent builders.

Concrete builders are how things actually get to the filesystem, and generally go at the
end of a dependency DAG to write out the final build artifacts. The goal is for developers
not to care about where (or even if) intermediate files are written.

In practice, most abstract files and directories /will/ be written to the filesystem, but
in a location determined by the build framework, not by the developer. Intermediate
build artifacts aren't generally important where they are saved to.

Some builders may not know the exact set of output files at resolution time. To deal with
this, they should output a directory. Directories are treated for resolution purposes
as if all files underneath the directory are given as a list of files.


Builder interface:
- Builders are classes which implement a simple interface: .get_targets() and .build()
- Builder classes can take arbitrary other arguments and organize their internals any way they 
want.

Builders will be passed, at some point, "source" objects. A source object may take several forms:
- string (referencing a relative file path)
- A builder object
- A File object
- A Dir object

During construction, the builder should use env.DependsFile() or env.DependsFiles(), passing
in the source objects, to get back either a File, list of Files, or Dir.

The builder should hang on to these objects. File and Dir objects may not have a path associated
with them when immediately returned from env.DependsFiles(), but they will by the time the
framework calls .build()

Builder.get_targets()
This is called by the framework when a builder is passed in to env.DependsFiles(). get_targets()
must return a File, list of Files, or a Dir object. The returned objects may be abstract or
concrete. Abstract objects are automatically resolved by the framework.
Targets returned by get_targets() are then returned from env.DependsFiles().
If env.DependsFile() is used, the builder must return a single file or a list of one file,
or an error is raised.

Builder.build(targets)
Called by the framework to actually perform the work of building the targets. The passed
in targets is a File, list of Files, or Dir object (corresponding to whatever was returned
by get_targets()), but the objects are guaranteed to be concrete (have an actual filesystem path)

The implementation is expected to use its sources (saved in instance variables as the class
implementation sees fit) to create the given target files. The exact path of target files
which were originally abstract is determined by the framework by looking at the downstream 
builders.

The builder's saved sources (previously returned from env.DependsFiles()) are now concrete,
meaning they have paths.

TODO: if a builder wants to output multiple files: a primary file and several "side effect" files,
using the builder as a source should resolve to the main file, but the side effect files
should still be accessible somehow (and dependency tracked)

Build Process:

Declare all builders
- Builder class interface is arbitrary. Classes can take sources at construction time, or
  via instance methods.
- All sources should be passed through one of the env.Depends*() to declare it as a
  dependency and resolve it to an abstract file or directory object(s)
  - env.DependsFile(builder, source-like obj) -> File
  - env.DependsFiles(builder, source-like obj) -> List[File]
  If an obj is passed into one of the above methods but does not return the expected type,
  an error is raised. Builders are expected to know what kind of dependency they expect.
  
  Passed-in objects may be:
  * str (interpreted as a relative path)
  * Concrete File object
  * List of concrete file objects
  * Dir object
  * Builder instance, whose get_targets() is called to get a File or Dir object
  
  Returned objects are usually "abstract", meaning they do not (yet) have a filesystem path
- Builders track the returned dependency objects as opaque objects at this point.
 
Gather targets
- The targets to be built are the root(s) of the dependency graph, named explicitly on the 
command line or by the caller somehow

Gather dependencies
- Each builder, starting with the targets, has get_dependencies() called. This should return
all sources for that builder. Each source may be: a string (representing a concrete path),
a concrete File or Directory object, or another builder instance (representing the output
file(s) of that builder)
- A dependency graph is formed between builders from these declared sources

Resolve Paths
- Each builder's get_targets() is called to get what it outputs.
- If it outputs abstract files, those files are resolved to concrete files
- After this step, all abstract paths are concrete
- ?? How do the existing objects referenced by builders get updated?

Out of Date resolution
- Determines which targets need building
- starts at the top of the tree
- If a file is newer than the last time that file was read, its builders are marked out of date
- If a directory's contents have changed, its builders are marked out of date
- If a builder is out of date, any dependent builders are also out of date

Execution
- From the top of the tree down: run all builders marked out of date
- Framework deletes the builder's targets. Files are unlinked. Directories are recursively deleted.
- Each builder is given the resolved concrete paths matching its declared abstract paths
- The builder is called to execute its routine and generate the declared files.
- If a builder declares a directory, it is created for the builder and the builder populates it

"""

# Example:

class Wheel(minicons.Builder):
    def __init__(self, env):
        super().__init__(env)
        self.wheel_sources = []
        self.data_sources = []

    def add_sources(self, sources, root="."):
        self.wheel_sources.append((root, self.env.DependsFiles(sources)))

    def add_data(self, category, sources, root="."):
        self.data_sources.append((category, root, self.env.DependsFiles(sources)))

    def get_targets(self):
        return AbstractFile("my-dist-1.0.0-py3-none-any.whl")

    def build(self, target):
        zip = zipfile.ZipFile(target.path, "w")
        for root, sources in self.wheel_sources:
            for source in sources:
                rel_path = sourcefile.rel_path
                if rel_path.startswith(root):
                    rel_path = rel_path[len(root):]
                    zip.write(source.get_abspath(), rel_path)

class ExtensionModule(minicons.Builder):
    def __init__(self, env, source, extra_sources):
        super().__init__(env)
        self.source = env.DependFile(self, source)
        self.extra_sources = env.DependFiles(extra_sources)

    def get_targets():
        # Perhaps there could be a helper method to convert a file into a new
        # abstract file. It would eliminate boilerplate related to passing the
        # relative path through.
        return AbstractFile(
                name=os.path.splitext(self.source.name)[0] + ".so",
                rel_path=self.source.rel_path,
        )

    def build(self, target):
        subprocess.check_call(
                ["cc", "-o", target.get_abspath(), self.source.get_abspath()] + [s.get_abspath() for s in self.extra_sources]
        )



env = Environment()
sources = list(env.root.glob("pkgname/**/*.py"))
sources.extend(
    ExtensionModule(s)
    for s in env.root.glob("pkgname/**/*.c")
)
wheel = Wheel()
wheel.add_sources(sources, root=".")
wheel.add_data("data/lens-docs", "doc/html/", "doc/html/")
installed = Install("dist/", wheel)
env.Alias("wheel", installed)
