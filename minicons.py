"""Proof of concept of a dead simple dependency tracker and build framework"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Union


class File:
    """Represents a file, perhaps abstract

    An abstract file is a file that does not yet have a location (path) on the filesystem

    A concrete file is one which has a path, but the file may or may not yet exist.

    """
    def __init__(self, outname: str, rel_path: str, build_dir_name: str):
        self.path: Optional[Path] = None
        self.outname = outname
        self.rel_path = rel_path
        self.build_dir_name = build_dir_name


class AbstractDirectory:
    def __init__(self):
        self.path: Optional[Path ]= None

BuilderSource = Union[str, "Builder", Path]
BuilderSources = Union[BuilderSource, Iterable[BuilderSource]]

class Builder(ABC):
    def __init__(self, env, sources: BuilderSources):
        self.env = env
        self.dependencies: List["Builder"]
        self.sources: List[Path]
        self.dependencies, self.sources = self._process_sources(sources)

    def _process_sources(
        self, items: BuilderSources,
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
