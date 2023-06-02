import codecs
import json
import os
from pathlib import Path
import tarfile
import tempfile
from os import path

import numpy as np
import pytest
import jsonschema

from sigmf import error, sigmffile
from sigmf.archive import (SIGMF_COLLECTION_EXT,
                           SIGMF_DATASET_EXT,
                           SIGMF_METADATA_EXT,
                           SigMFArchive)

from .testdata import TEST_FLOAT32_DATA_1, TEST_METADATA_1


def create_test_archive(test_sigmffile, tmpfile):
    sigmf_archive = test_sigmffile.archive(fileobj=tmpfile)
    sigmf_tarfile = tarfile.open(sigmf_archive, mode="r", format=tarfile.PAX_FORMAT)
    return sigmf_tarfile


def test_without_data_file_throws_fileerror(test_sigmffile):
    test_sigmffile.data_file = None
    with tempfile.NamedTemporaryFile() as temp:
        with pytest.raises(error.SigMFFileError):
            test_sigmffile.archive(file_path=temp.name)


def test_invalid_md_throws_validationerror(test_sigmffile):
    del test_sigmffile._metadata["global"]["core:datatype"]  # required field
    with tempfile.NamedTemporaryFile() as temp:
        with pytest.raises(jsonschema.exceptions.ValidationError):
            test_sigmffile.archive(file_path=temp.name)


def test_name_wrong_extension_throws_fileerror(test_sigmffile):
    with tempfile.NamedTemporaryFile() as temp:
        with pytest.raises(error.SigMFFileError):
            test_sigmffile.archive(file_path=temp.name + ".zip")


def test_fileobj_extension_ignored(test_sigmffile):
    with tempfile.NamedTemporaryFile(suffix=".tar") as temp:
        test_sigmffile.archive(fileobj=temp)


def test_name_used_in_fileobj(test_sigmffile):
    with tempfile.NamedTemporaryFile() as temp:
        sigmf_archive = test_sigmffile.archive(file_path="testarchive",
                                               fileobj=temp)
        sigmf_tarfile = tarfile.open(sigmf_archive, mode="r")
        basedir, file1, file2 = sigmf_tarfile.getmembers()
        assert basedir.name == test_sigmffile.name
        assert sigmf_tarfile.name == temp.name

        def filename(tarinfo):
            path_root, _ = path.splitext(tarinfo.name)
            return path.split(path_root)[-1]

        assert filename(file1) == test_sigmffile.name
        assert filename(file2) == test_sigmffile.name


def test_fileobj_not_closed(test_sigmffile):
    with tempfile.NamedTemporaryFile() as temp:
        test_sigmffile.archive(fileobj=temp)
        assert not temp.file.closed


def test_unwritable_fileobj_throws_fileerror(test_sigmffile):
    with tempfile.NamedTemporaryFile(mode="rb") as temp:
        with pytest.raises(error.SigMFFileError):
            test_sigmffile.archive(fileobj=temp)


def test_unwritable_name_throws_fileerror(test_sigmffile):
    # Cannot assume /root/ is unwritable (e.g. Docker environment)
    # so use invalid filename
    unwritable_file = '/bad_name/'
    with pytest.raises(error.SigMFFileError):
        test_sigmffile.archive(file_path=unwritable_file)


def test_tarfile_layout(test_sigmffile):
    with tempfile.NamedTemporaryFile() as temp:
        sigmf_tarfile = create_test_archive(test_sigmffile, temp)
        basedir, file1, file2 = sigmf_tarfile.getmembers()
        assert tarfile.TarInfo.isdir(basedir)
        assert tarfile.TarInfo.isfile(file1)
        assert tarfile.TarInfo.isfile(file2)


def test_tarfile_names_and_extensions(test_sigmffile):
    with tempfile.NamedTemporaryFile() as temp:
        sigmf_tarfile = create_test_archive(test_sigmffile, temp)
        basedir, file1, file2 = sigmf_tarfile.getmembers()
        sigmffile_name = basedir.name
        assert sigmffile_name == test_sigmffile.name
        archive_name = sigmf_tarfile.name
        assert archive_name == temp.name
        path.split(temp.name)[-1]
        file_extensions = {SIGMF_DATASET_EXT, SIGMF_METADATA_EXT}

        file1_name, file1_ext = path.splitext(file1.name)
        assert file1_ext in file_extensions
        assert path.split(file1_name)[-1] == test_sigmffile.name

        file_extensions.remove(file1_ext)

        file2_name, file2_ext = path.splitext(file2.name)
        assert path.split(file2_name)[-1] == test_sigmffile.name
        assert file2_ext in file_extensions


def test_multirec_archive_into_fileobj(test_sigmffile,
                                       test_alternate_sigmffile):
    with tempfile.NamedTemporaryFile() as t:
        # add first sigmffile to the fileobj t
        create_test_archive(test_sigmffile, t)
        # add a second one to the same fileobj
        multirec_tar = create_test_archive(test_alternate_sigmffile, t)
        members = multirec_tar.getmembers()
        assert len(members) == 6  # 2 directories and 2 files per directory


def test_tarfile_persmissions(test_sigmffile):
    with tempfile.NamedTemporaryFile() as temp:
        sigmf_tarfile = create_test_archive(test_sigmffile, temp)
        basedir, file1, file2 = sigmf_tarfile.getmembers()
        assert basedir.mode == 0o755
        assert file1.mode == 0o644
        assert file2.mode == 0o644


def test_contents(test_sigmffile):
    with tempfile.NamedTemporaryFile() as temp:
        sigmf_tarfile = create_test_archive(test_sigmffile, temp)
        basedir, file1, file2 = sigmf_tarfile.getmembers()
        if file1.name.endswith(SIGMF_METADATA_EXT):
            mdfile = file1
            datfile = file2
        else:
            mdfile = file2
            datfile = file1

        bytestream_reader = codecs.getreader("utf-8")  # bytes -> str
        mdfile_reader = bytestream_reader(sigmf_tarfile.extractfile(mdfile))
        assert json.load(mdfile_reader) == TEST_METADATA_1

        datfile_reader = sigmf_tarfile.extractfile(datfile)
        # calling `fileno` on `tarfile.ExFileObject` throws error (?), but
        # np.fromfile requires it, so we need this extra step
        data = np.frombuffer(datfile_reader.read(), dtype=np.float32)

        assert np.array_equal(data, TEST_FLOAT32_DATA_1)


def test_tarfile_type(test_sigmffile):
    with tempfile.NamedTemporaryFile() as temp:
        sigmf_tarfile = create_test_archive(test_sigmffile, temp)
        assert sigmf_tarfile.format == tarfile.PAX_FORMAT


def test_create_archive_pathlike(test_sigmffile, test_alternate_sigmffile):
    with tempfile.NamedTemporaryFile() as t:
        input_sigmffiles = [test_sigmffile, test_alternate_sigmffile]
        arch = SigMFArchive(input_sigmffiles, path=Path(t.name))
        output_sigmf_files = sigmffile.fromarchive(archive_path=arch.path)
        assert len(output_sigmf_files) == 2
        assert input_sigmffiles == output_sigmf_files


def test_archive_names(test_sigmffile):
    with tempfile.NamedTemporaryFile(suffix=".sigmf") as t:
        a = SigMFArchive(sigmffiles=test_sigmffile, path=t.name)
        assert a.path == t.name
        observed_sigmffile = sigmffile.fromarchive(t.name)
        assert observed_sigmffile.name == test_sigmffile.name

    with tempfile.NamedTemporaryFile(suffix=".sigmf") as t:
        archive_path = test_sigmffile.archive(t.name)
        assert archive_path == t.name
        observed_sigmffile = sigmffile.fromarchive(t.name)
        assert observed_sigmffile.name == test_sigmffile.name

    with tempfile.NamedTemporaryFile(suffix=".sigmf") as t:
        test_sigmffile.tofile(t.name, toarchive=True)
        observed_sigmffile = sigmffile.fromarchive(t.name)
        assert observed_sigmffile.name == test_sigmffile.name


def test_single_recording_with_collection(test_sigmffile):
    sigmf_meta_file = test_sigmffile.name + SIGMF_METADATA_EXT
    try:
        with open(sigmf_meta_file, mode="w") as sigmf_meta_fd:
            test_sigmffile.dump(sigmf_meta_fd)
        test_collection = sigmffile.SigMFCollection([sigmf_meta_file])
        input_collection_json = test_collection.dumps(pretty=True)
        with tempfile.NamedTemporaryFile(suffix=".sigmf") as tmpfile:
            archive = SigMFArchive(test_sigmffile,
                                   test_collection,
                                   fileobj=tmpfile)
            with tarfile.open(archive.path) as tar:
                # 1 collection_file + 1 dir + 1 meta file + 1 data file
                assert len(tar.getmembers()) == 4
                for member in tar.getmembers():
                    if member.isfile():
                        if member.name.endswith(SIGMF_COLLECTION_EXT):
                            collection_file = tar.extractfile(member)
                            output_collection_json = json.load(collection_file)
                            assert (json.loads(input_collection_json) ==
                                    output_collection_json)
    finally:
        if os.path.exists(sigmf_meta_file):
            os.remove(sigmf_meta_file)


def test_multiple_recordings_with_collection(test_sigmffile,
                                             test_alternate_sigmffile,
                                             test_alternate_sigmffile_2):
    sigmf_meta_files = [
        test_sigmffile.name + SIGMF_METADATA_EXT,
        test_alternate_sigmffile.name + SIGMF_METADATA_EXT,
        test_alternate_sigmffile_2.name + SIGMF_METADATA_EXT
    ]
    input_sigmf_files = [test_sigmffile,
                         test_alternate_sigmffile,
                         test_alternate_sigmffile_2]
    try:
        for sigmf_meta_file, sigmf_file in zip(sigmf_meta_files,
                                               input_sigmf_files):
            with open(sigmf_meta_file, mode="w") as sigmf_meta_fd:
                sigmf_file.dump(sigmf_meta_fd)
        test_collection = sigmffile.SigMFCollection(sigmf_meta_files)
        input_collection_json = test_collection.dumps(pretty=True)
        with tempfile.NamedTemporaryFile(suffix=".sigmf") as tmpfile:
            archive = SigMFArchive(input_sigmf_files,
                                   test_collection,
                                   fileobj=tmpfile)
            with tarfile.open(archive.path) as tar:
                # 1 collection_file + 3 dir + 3 meta file + 3 data file
                assert len(tar.getmembers()) == 10
                for member in tar.getmembers():
                    if member.isfile():
                        if member.name.endswith(SIGMF_COLLECTION_EXT):
                            collection_file = tar.extractfile(member)
                            output_collection_json = json.load(collection_file)
                            assert (json.loads(input_collection_json) ==
                                    output_collection_json)
    finally:
        for sigmf_meta_file in sigmf_meta_files:
            if os.path.exists(sigmf_meta_file):
                os.remove(sigmf_meta_file)


def test_extra_sigmf_file_not_in_collection(test_sigmffile,
                                            test_alternate_sigmffile,
                                            test_alternate_sigmffile_2):
    sigmf_meta_files = [
        test_sigmffile.name + SIGMF_METADATA_EXT,
        test_alternate_sigmffile.name + SIGMF_METADATA_EXT,
        test_alternate_sigmffile_2.name + SIGMF_METADATA_EXT
    ]
    input_sigmf_files = [test_sigmffile,
                         test_alternate_sigmffile,
                         test_alternate_sigmffile_2]
    try:
        for sigmf_meta_file, sigmf_file in zip(sigmf_meta_files,
                                               input_sigmf_files):
            with open(sigmf_meta_file, mode="w") as sigmf_meta_fd:
                sigmf_file.dump(sigmf_meta_fd)
        test_collection = sigmffile.SigMFCollection(sigmf_meta_files[:2])
        with tempfile.NamedTemporaryFile(suffix=".sigmf") as tmpfile:
            with pytest.raises(error.SigMFValidationError):
                SigMFArchive(input_sigmf_files,
                             test_collection,
                             fileobj=tmpfile)
    finally:
        for sigmf_meta_file in sigmf_meta_files:
            if os.path.exists(sigmf_meta_file):
                os.remove(sigmf_meta_file)


def test_extra_recording_not_in_sigmffiles(test_sigmffile,
                                           test_alternate_sigmffile,
                                           test_alternate_sigmffile_2):
    sigmf_meta_files = [
        test_sigmffile.name + SIGMF_METADATA_EXT,
        test_alternate_sigmffile.name + SIGMF_METADATA_EXT,
        test_alternate_sigmffile_2.name + SIGMF_METADATA_EXT
    ]
    input_sigmf_files = [test_sigmffile,
                         test_alternate_sigmffile,
                         test_alternate_sigmffile_2]
    try:
        for sigmf_meta_file, sigmf_file in zip(sigmf_meta_files,
                                               input_sigmf_files):
            with open(sigmf_meta_file, mode="w") as sigmf_meta_fd:
                sigmf_file.dump(sigmf_meta_fd)
        test_collection = sigmffile.SigMFCollection(sigmf_meta_files)

        with tempfile.NamedTemporaryFile(suffix=".sigmf") as tmpfile:
            with pytest.raises(error.SigMFValidationError):
                SigMFArchive(input_sigmf_files[:2],
                             test_collection,
                             fileobj=tmpfile)
    finally:
        for sigmf_meta_file in sigmf_meta_files:
            if os.path.exists(sigmf_meta_file):
                os.remove(sigmf_meta_file)


def test_mismatched_sigmffiles_collection(test_sigmffile,
                                          test_alternate_sigmffile,
                                          test_alternate_sigmffile_2):
    sigmf_meta_files = [
        test_sigmffile.name + SIGMF_METADATA_EXT,
        test_alternate_sigmffile.name + SIGMF_METADATA_EXT,
        test_alternate_sigmffile_2.name + SIGMF_METADATA_EXT
    ]
    input_sigmf_files = [test_sigmffile,
                         test_alternate_sigmffile,
                         test_alternate_sigmffile_2]
    try:
        for sigmf_meta_file, sigmf_file in zip(sigmf_meta_files,
                                               input_sigmf_files):
            with open(sigmf_meta_file, mode="w") as sigmf_meta_fd:
                sigmf_file.dump(sigmf_meta_fd)
        test_collection = sigmffile.SigMFCollection(sigmf_meta_files[:2])

        with tempfile.NamedTemporaryFile(suffix=".sigmf") as tmpfile:
            with pytest.raises(error.SigMFValidationError):
                SigMFArchive(input_sigmf_files[1:3],
                             test_collection,
                             fileobj=tmpfile)
    finally:
        for sigmf_meta_file in sigmf_meta_files:
            if os.path.exists(sigmf_meta_file):
                os.remove(sigmf_meta_file)


def test_archive_no_path_or_fileobj(test_sigmffile):
    """Error should be raised when no path or fileobj given."""
    with pytest.raises(error.SigMFFileError):
        SigMFArchive(test_sigmffile)
