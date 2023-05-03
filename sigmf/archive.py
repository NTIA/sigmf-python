# Copyright: Multiple Authors
#
# This file is part of SigMF. https://github.com/sigmf/sigmf-python
#
# SPDX-License-Identifier: LGPL-3.0-or-later

"""Create and extract SigMF archives."""

import os
import shutil
import tarfile
import tempfile
from typing import BinaryIO, Iterable, Union

import sigmf


from .error import SigMFFileError


SIGMF_ARCHIVE_EXT = ".sigmf"
SIGMF_METADATA_EXT = ".sigmf-meta"
SIGMF_DATASET_EXT = ".sigmf-data"
SIGMF_COLLECTION_EXT = ".sigmf-collection"


class SigMFArchive():
    """Archive one or more `SigMFFile`s.

    A `.sigmf` file must include both valid metadata and data.
    If `self.data_file` is not set or the requested output file
    is not writable, raise `SigMFFileError`.

    Parameters:

      sigmffile -- An iterable of SigMFFile objects with valid metadata and data_files

      name      -- path to archive file to create. If file exists, overwrite.
                    If `name` doesn't end in .sigmf, it will be appended. The
                    `self.path` instance variable will be updated upon
                    successful writing of the archive to point to the final
                    archive path.


      fileobj   -- If `fileobj` is specified, it is used as an alternative to
                    a file object opened in binary mode for `name`. If
                    `fileobj` is an open tarfile, it will be appended to. It is
                    supposed to be at position 0. `fileobj` won't be closed. If
                    `fileobj` is given, `name` has no effect.
    """
    def __init__(self, sigmffiles : Union["SigMFFile", Iterable["SigMFFile"]], name : str = None, fileobj : BinaryIO =None):

        if isinstance(sigmffiles[0], sigmf.sigmffile.SigMFFile):
            self.sigmffiles = sigmffiles
        else:
            self.sigmffiles = [sigmffiles]
            
        self.name = name
        self.fileobj = fileobj

        self._check_input()

        mode = "a" if fileobj is not None else "w"
        sigmf_fileobj = self._get_output_fileobj()
        try:
            sigmf_archive = tarfile.TarFile(mode=mode,
                                            fileobj=sigmf_fileobj,
                                            format=tarfile.PAX_FORMAT)
        except tarfile.ReadError:
             # fileobj doesn't contain any archives yet, so reopen in 'w' mode
            sigmf_archive = tarfile.TarFile(mode='w',
                                            fileobj=sigmf_fileobj,
                                            format=tarfile.PAX_FORMAT)
            
        def chmod(tarinfo):
            if tarinfo.isdir():
                tarinfo.mode = 0o755  # dwrxw-rw-r
            else:
                tarinfo.mode = 0o644  # -wr-r--r--
            return tarinfo

        for sigmffile in self.sigmffiles:
            with tempfile.TemporaryDirectory() as tmpdir:
                sigmf_md_filename = sigmffile.name + SIGMF_METADATA_EXT
                sigmf_md_path = os.path.join(tmpdir, sigmf_md_filename)
                sigmf_data_filename = sigmffile.name + SIGMF_DATASET_EXT
                sigmf_data_path = os.path.join(tmpdir, sigmf_data_filename)

                with open(sigmf_md_path, "w") as mdfile:
                    sigmffile.dump(mdfile, pretty=True)

                shutil.copy(sigmffile.data_file, sigmf_data_path)
                sigmf_archive.add(tmpdir, arcname=sigmffile.name, filter=chmod)

        sigmf_archive.close()
        if not fileobj:
            sigmf_fileobj.close()
        else:
            sigmf_fileobj.seek(0)  # ensure next open can read this as a tar

        self.path = sigmf_archive.name

    def _check_input(self):
        self._ensure_name_has_correct_extension()
        for sigmffile in self.sigmffiles:
            self._ensure_sigmffile_name_set(sigmffile)
            self._ensure_data_file_set(sigmffile)
            self._validate_sigmffile_metadata(sigmffile)

    def _ensure_name_has_correct_extension(self):
        name = self.name
        if name is None:
            return

        has_extension = "." in name
        has_correct_extension = name.endswith(SIGMF_ARCHIVE_EXT)
        if has_extension and not has_correct_extension:
            apparent_ext = os.path.splitext(name)[-1]
            err = "extension {} != {}".format(apparent_ext, SIGMF_ARCHIVE_EXT)
            raise SigMFFileError(err)

        self.name = name if has_correct_extension else name + SIGMF_ARCHIVE_EXT

    @staticmethod
    def _ensure_sigmffile_name_set(sigmffile):
        if not sigmffile.name:
            err = "the `name` attribute must be set to pass to `SigMFArchive`"
            raise SigMFFileError(err)
    
    @staticmethod
    def _ensure_data_file_set(sigmffile):
        if not sigmffile.data_file:
            err = "no data file - use `set_data_file`"
            raise SigMFFileError(err)

    @staticmethod
    def _validate_sigmffile_metadata(sigmffile):
        sigmffile.validate()

    def _get_archive_name(self):
        if self.fileobj and not self.name:
            pathname = self.fileobj.name
        else:
            pathname = self.name

        filename = os.path.split(pathname)[-1]
        archive_name, archive_ext = os.path.splitext(filename)
        return archive_name

    def _get_output_fileobj(self):
        try:
            fileobj = self._get_open_fileobj()
        except:
            if self.fileobj:
                err = "fileobj {!r} is not byte-writable".format(self.fileobj)
            else:
                err = "can't open {!r} for writing".format(self.name)

            raise SigMFFileError(err)

        return fileobj

    def _get_open_fileobj(self):
        if self.fileobj:
            fileobj = self.fileobj
            fileobj.write(bytes())  # force exception if not byte-writable
        else:
            fileobj = open(self.name, "wb")

        return fileobj
