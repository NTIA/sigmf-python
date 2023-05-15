# Copyright: Multiple Authors
#
# This file is part of SigMF. https://github.com/sigmf/sigmf-python
#
# SPDX-License-Identifier: LGPL-3.0-or-later

"""Create and extract SigMF archives."""

import collections
import os
import shutil
import tarfile
import tempfile
from typing import BinaryIO, Iterable, Union

import sigmf


from .error import SigMFFileError, SigMFValidationError


SIGMF_ARCHIVE_EXT = ".sigmf"
SIGMF_METADATA_EXT = ".sigmf-meta"
SIGMF_DATASET_EXT = ".sigmf-data"
SIGMF_COLLECTION_EXT = ".sigmf-collection"


class SigMFArchive():
    """Archive one or more `SigMFFile`s. A collection file can
    optionally be included.

    A `.sigmf` file must include both valid metadata and data.
    If `self.data_file` is not set or the requested output file
    is not writable, raise `SigMFFileError`.

    Parameters:

      sigmffiles -- A single SigMFFIle or an iterable of SigMFFile objects with
                    valid metadata and data_files

      collection -- An optional SigMFCollection.

      path       -- Path to archive file to create. If file exists, overwrite.
                    If `path` doesn't end in .sigmf, it will be appended. The
                    `self.path` instance variable will be updated upon
                    successful writing of the archive to point to the final
                    archive path.


      fileobj    -- If `fileobj` is specified, it is used as an alternative to
                    a file object opened in binary mode for `path`. If
                    `fileobj` is an open tarfile, it will be appended to. It is
                    supposed to be at position 0. `fileobj` won't be closed. If
                    `fileobj` is given, `path` has no effect.
    """
    def __init__(self,
                 sigmffiles: Union["sigmf.sigmffile.SigMFFile",
                                   Iterable["sigmf.sigmffile.SigMFFile"]],
                 collection: "sigmf.sigmffile.SigMFCollection" = None,
                 path: Union[str, os.PathLike] = None,
                 fileobj: BinaryIO = None):

        if (not path) and (not fileobj):
            raise SigMFFileError("'path' or 'fileobj' required for creating "
                                 "SigMF archive!")

        if isinstance(sigmffiles, sigmf.sigmffile.SigMFFile):
            self.sigmffiles = [sigmffiles]
        elif (hasattr(collections, "Iterable") and
              isinstance(sigmffiles, collections.Iterable)):
            self.sigmffiles = sigmffiles
        elif isinstance(sigmffiles, collections.abc.Iterable):  # python 3.10
            self.sigmffiles = sigmffiles
        else:
            raise SigMFFileError("Unknown type for sigmffiles argument!")

        if path:
            self.path = str(path)
        else:
            self.path = None
        self.fileobj = fileobj
        self.collection = collection

        self._check_input()

        archive_name = self._get_archive_name()
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

        if collection:
            with tempfile.NamedTemporaryFile(mode="w") as tmpfile:
                collection.dump(tmpfile, pretty=True)
                tmpfile.flush()
                collection_filename = archive_name + SIGMF_COLLECTION_EXT
                sigmf_archive.add(tmpfile.name,
                                  arcname=collection_filename,
                                  filter=chmod)

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
        self._ensure_path_has_correct_extension()
        for sigmffile in self.sigmffiles:
            self._ensure_sigmffile_name_set(sigmffile)
            self._ensure_data_file_set(sigmffile)
            self._validate_sigmffile_metadata(sigmffile)
        if self.collection:
            self._validate_sigmffile_collection(self.collection,
                                                self.sigmffiles)

    def _ensure_path_has_correct_extension(self):
        path = self.path
        if path is None:
            return

        has_extension = "." in path
        has_correct_extension = path.endswith(SIGMF_ARCHIVE_EXT)
        if has_extension and not has_correct_extension:
            apparent_ext = os.path.splitext(path)[-1]
            err = "extension {} != {}".format(apparent_ext, SIGMF_ARCHIVE_EXT)
            raise SigMFFileError(err)

        self.path = path if has_correct_extension else path + SIGMF_ARCHIVE_EXT

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

    @staticmethod
    def _validate_sigmffile_collection(collectionfile, sigmffiles):
        if len(collectionfile) != len(sigmffiles):
            raise SigMFValidationError("Mismatched number of recordings "
                                       "between sigmffiles and collection "
                                       "file!")
        streams_key = collectionfile.STREAMS_KEY
        streams = collectionfile.get_collection_field(streams_key)
        sigmf_meta_hashes = [s["hash"] for s in streams]
        if not streams:
            raise SigMFValidationError("No recordings in collection file!")
        for sigmffile in sigmffiles:
            with tempfile.NamedTemporaryFile(mode="w") as tmpfile:
                sigmffile.dump(tmpfile, pretty=True)
                tmpfile.flush()
                meta_path = tmpfile.name
                sigmf_meta_hash = sigmf.sigmf_hash.calculate_sha512(meta_path)
                if sigmf_meta_hash not in sigmf_meta_hashes:
                    raise SigMFValidationError("SigMFFile given that "
                                               "is not in collection file!")

    def _get_archive_name(self):
        if self.fileobj and not self.path:
            pathname = self.fileobj.name
        else:
            pathname = self.path

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
                err = "can't open {!r} for writing".format(self.path)

            raise SigMFFileError(err)

        return fileobj

    def _get_open_fileobj(self):
        if self.fileobj:
            fileobj = self.fileobj
            fileobj.write(bytes())  # force exception if not byte-writable
        else:
            fileobj = open(self.path, "wb")

        return fileobj
