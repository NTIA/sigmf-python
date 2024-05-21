from abc import ABC, abstractmethod
from typing import Iterable

import sigmf

from .archive import SigMFArchive


class AbstractSigMFFileCollection(ABC):
    """Abstract collection of SigMF files that can be
    represented by a single SigMF or multiple SigMF files"""

    @abstractmethod
    def sigmffile_count(self):
        pass

    @abstractmethod
    def get_sigmffiles(self):
        pass

    # should tofile() be added?

    @abstractmethod
    def archive(self, name=None, fileobj=None, pretty=True):
        pass


class SigMFFileCollection(AbstractSigMFFileCollection):
    """Implementation of AbstractSigMFFileCollection representing
    collection of multiple SigMF files"""

    def __init__(self, sigmffiles: Iterable["sigmf.sigmffile.SigMFFile"]) -> None:
        self.sigmffiles = sigmffiles

    def sigmffile_count(self):
        return len(self.sigmffiles)

    def get_sigmffiles(self):
        return self.sigmffiles

    # should tofile() be added?
    def archive(self, name=None, fileobj=None, pretty=True):
        archive = SigMFArchive(self,
                               path=name,
                               fileobj=fileobj,
                               pretty=pretty)
        return archive.path
