"""Proof of concept of a dead simple dependency tracker and build framework"""
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, Iterator, List, NewType, Optional, Tuple, TypeVar, Union, Dict

DependsTypes = Union["File", "Dir", "Builder", str, Iterable["File"], Iterable[str]]


class Environment:
    def __init__(self, build_dir: Optional[Path]):
        self.root = Path.cwd()
        self.build_root = build_dir or self.root.joinpath("build")
        self.known_paths: Dict[Path, Union["File", "Dir"]] = {}

    def file(self, *args, **kw):
        return File(self, *args, **kw)

    def get_rel_path(self, src: Union[str, Path]) -> Path:
        src = self.root.relative_to(src)
        return src.relative_to(self.root)

    def get_build_path(
        self,
        src: Union[str, Path],
        build_dir: Union[str, Path],
        new_ext: Optional[str] = None,
    ) -> Path:
        rel_path = self.get_rel_path(src)
        build_dir = self.build_root.joinpath(build_dir)

        full_path = build_dir.joinpath(rel_path).relative_to(self.root)
        if new_ext is not None:
            full_path = full_path.with_suffix(new_ext)
        return full_path

    def DependsFiles(
        self,
        builder: "Builder",
        sources: DependsTypes,
    ) -> Union[Iterable["File"], "Dir"]:
        """Record "builder" as depending on the given sources.

        Returns an opaque iterable of objects which will, during the build phase, have a
        get_path() method usable to get a location on the filesystem to read the source.

        Sources may be any of:

        * Abstract file, in which case a list of length one is returned with a File object
          which will be concrete during the build phase.
        * Concrete file, in which case a list of length one is returned containing that file
          object
        * Abstract or concrete Dir, in which case a Dir object will be returned which,
          when iterated over during the build phase, will iterate over all File objects in
          that directory
        * str or list of strs: each str will be treated as a file relative to the root,
          and a list of File objects will be returned
        * Builder: the builder's targets will be gathered and returned here. Whether the
          returned item is a list of Files or a Dir depends on the builder.
        """
        pass  # TODO

    def DependsFile(
        self, builder: "Builder", sources: Union[DependsTypes, Iterable[DependsTypes]]
    ) -> "File":
        """Same as DependsFiles except only a single file is returned

        Builders must return a single file or an error is raised.
        """
        pass  # TODO


E = TypeVar("E", bound="Entry")


class Entry(ABC):
    """Represents a file or a directory, perhaps abstract

    An abstract file/dir is one that does not yet have a location (path) on the filesystem

    A concrete file/dir is one which has a path, but the file/dir may or may not yet exist.

    """

    def __init__(
        self,
        env: "Environment",
        path: Union[str, Path, None] = None,
        *,
        rel_path: Optional[Path] = None,
        build_dir_name: Optional[str] = None,
    ):
        self.env = env
        self.path: Optional[Path] = Path(path) if path else None
        self.rel_path = rel_path
        self.build_dir_name = build_dir_name

        if path is None:
            assert self.rel_path and self.build_dir_name, (
                "Abstract paths must have a rel_path " "and build_dir_name"
            )

    def get_path(self) -> Path:
        if self.path is None:
            raise RuntimeError("This object is abstract and does not have a path")
        return self.path

    def derive(self: E, new_ext: str, build_dir_name: str) -> E:
        """Create a derivative abstract file/dir from this file"""
        if self.path is not None:
            # Concrete path
            new_rel_path = self.env.get_rel_path(self.path)
        else:
            assert self.rel_path is not None
            new_rel_path = self.rel_path.with_suffix(new_ext)

        return type(self)(
            self.env,
            rel_path=new_rel_path,
            build_dir_name=build_dir_name,
        )


class File(Entry):
    pass


class Dir(Entry):
    def __iter__(self) -> Iterator["File"]:


BuilderSource = Union[str, "Builder", Path]
BuilderSources = Union[BuilderSource, Iterable[BuilderSource]]


class Builder(ABC):
    def __init__(self, env, sources: BuilderSources):
        self.env = env
        self.dependencies: List["Builder"]
        self.sources: List[Path]
        self.dependencies, self.sources = self._process_sources(sources)

    def _process_sources(
        self,
        items: BuilderSources,
    ) -> Tuple[List["Builder"], List[Path]]:
        deps: List["Builder"] = []
        sources: List[Path] = []

        for item in [items]:
            if isinstance(item, str):
                sources.append(Path(item))
            elif isinstance(item, Builder):
                deps.append(item)
            elif isinstance(item, Path):
                sources.append(item)
            elif isinstance(item, Iterable):
                newdeps, newsources = self._process_sources(item)
                deps.extend(newdeps)
                sources.extend(newsources)
            else:
                raise TypeError(f"Unknown source type {item}")

        return deps, sources

    @abstractmethod
    def get_targets(self):
        """Returns a File, list of Files, or a Directory declaring what this builder outputs

        Abstract files / directories are resolved to concrete files by the dependent
        builders before passing back to this builder's build().

        The returned items from this method declare what this builder outputs. Generally,
        builders should output abstract files if the exact set of files is known at resolution
        time.

        Some builders don't know the set of files being output until build time, in which case
        they should return an abstract directory which the builder should use at build time
        to write its output files to.

        If the builder wants to output its files to a particular place in the filesystem,
        it can return a concrete file list or directory. The intent of abstract files
        is so builders don't have to worry about the location of their output, letting
        the build framework determine where files should go.

        """

    @abstractmethod
    def build(self, targets):
        """Called to actually build the targets

        Output should go to the given targets.
        The targets argument is a concrete or set of concrete objects corresponding to
        what was previously returned by get_output().

        So if get_output() returned an AbstractFile, this method is passed a ConcreteFile
        and is expected to write its output to that file.

        Similarly, if AbstractDirectory was given, a ConcreteDirectory is passed in here
        and this builder is expected to write all its files underneath the given directory.
        """
