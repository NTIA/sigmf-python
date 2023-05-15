# Copyright: Multiple Authors
#
# This file is part of SigMF. https://github.com/gnuradio/SigMF
#
# SPDX-License-Identifier: LGPL-3.0-or-later

"""Access SigMF archives without extracting them."""

import os
import tarfile

from .sigmffile import SigMFCollection, SigMFFile
from .archive import (SIGMF_COLLECTION_EXT,
                      SIGMF_DATASET_EXT,
                      SIGMF_METADATA_EXT,
                      SIGMF_ARCHIVE_EXT)
from .error import SigMFFileError


class SigMFArchiveReader():
    """Access data within SigMF archive `tar` in-place without extracting. This
    class can be used to iterate through multiple SigMFFiles in the archive.

    Parameters:

      path    -- path to archive file to access. If file does not exist,
                 or if `path` doesn't end in .sigmf, SigMFFileError is raised.
    """
    def __init__(self, path=None, skip_checksum=False, map_readonly=True, archive_buffer=None):
        self.path = path
        tar_obj = None
        try:
            if self.path is not None:
                if not self.path.endswith(SIGMF_ARCHIVE_EXT):
                    err = "archive extension != {}".format(SIGMF_ARCHIVE_EXT)
                    raise SigMFFileError(err)

                tar_obj = tarfile.open(self.path)

            elif archive_buffer is not None:
                tar_obj = tarfile.open(fileobj=archive_buffer, mode='r:')

            else:
                raise ValueError('In sigmf.archivereader.__init__(), either `name` or `archive_buffer` must be not None')

            json_contents = None
            data_offset_size = None
            sigmffile_name = None
            self.sigmffiles = []
            data_found = False
            collection_metadata = {}

            for memb in tar_obj.getmembers():
                if memb.isdir():  # memb.type == tarfile.DIRTYPE:
                    # the directory structure will be reflected in the member name
                    continue

                elif memb.isfile():  # memb.type == tarfile.REGTYPE:
                    if memb.name.endswith(SIGMF_METADATA_EXT):
                        json_contents = memb.name
                        if data_offset_size is None:
                            # consider a warnings.warn() here; the datafile should be earlier in the
                            # archive than the metadata, so that updating it (like, adding an annotation)
                            # is fast.
                            pass
                        with tar_obj.extractfile(memb) as memb_fid:
                            json_contents = memb_fid.read()

                        _, sigmffile_name = os.path.split(memb.name)
                        sigmffile_name, _ = os.path.splitext(sigmffile_name)
                    elif memb.name.endswith(SIGMF_DATASET_EXT):
                        data_offset_size = memb.offset_data, memb.size
                        data_found = True
                    elif memb.name.endswith(SIGMF_COLLECTION_EXT):
                        with tar_obj.extractfile(memb) as collection_f:
                            collection_metadata = collection_f.read()
                    else:
                        print('A regular file', memb.name, 'was found but ignored in the archive')
                else:
                    print('A member of type', memb.type, 'and name', memb.name, 'was found but not handled, just FYI.')

                if data_offset_size is not None and json_contents is not None:
                    sigmffile = SigMFFile(sigmffile_name,
                                          metadata=json_contents)
                    sigmffile.validate()

                    sigmffile.set_data_file(self.path,
                                            data_buffer=archive_buffer,
                                            skip_checksum=skip_checksum,
                                            offset=data_offset_size[0],
                                            size_bytes=data_offset_size[1],
                                            map_readonly=map_readonly)

                    self.sigmffiles.append(sigmffile)
                    data_offset_size = None
                    json_contents = None
                    sigmffile_name = None
            if collection_metadata:
                # Currently the SigMFCollection class does not support getting
                # SigMFFiles (SigMFCollection.get_SigMFFile()) when created
                # here in SigMFArchiveReader. This is because the SigMF
                # metadata files are not extracted from the tarfile to the
                # file system.
                self.collection = SigMFCollection(metadata=collection_metadata,
                                                  skip_checksums=True)
            else:
                self.collection = None

            if not data_found:
                raise SigMFFileError('No .sigmf-data file found in archive!')
        finally:
            if tar_obj:
                tar_obj.close()

    def __len__(self):
        return len(self.sigmffiles)

    def __iter__(self):
        return self.sigmffiles.__iter__()

    def __getitem__(self, sli):
        return self.sigmffiles.__getitem__(sli)
