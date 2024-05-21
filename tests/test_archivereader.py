# Copyright: Multiple Authors
#
# This file is part of sigmf-python. https://github.com/sigmf/sigmf-python
#
# SPDX-License-Identifier: LGPL-3.0-or-later

"""Tests for SigMFArchiveReader"""

import os
import shutil
import tempfile
import unittest

import numpy as np

from sigmf import SigMFArchiveReader, SigMFFile, __specification__
from sigmf.archive import SIGMF_METADATA_EXT, SigMFArchive
from sigmf.sigmffile_collection import SigMFFileCollection


class TestArchiveReader(unittest.TestCase):
    def setUp(self):
        # in order to check shapes we need some positive number of samples to work with
        # number of samples should be lowest common factor of num_channels
        self.raw_count = 16
        self.lut = {
            "i8": np.int8,
            "u8": np.uint8,
            "i16": np.int16,
            "u16": np.uint16,
            "u32": np.uint32,
            "i32": np.int32,
            "f32": np.float32,
            "f64": np.float64,
        }

    def test_access_data_without_untar(self):
        """iterate through datatypes and verify IO is correct"""
        _, temp_path = tempfile.mkstemp()
        _, temp_archive = tempfile.mkstemp(suffix=".sigmf")

        for key, dtype in self.lut.items():
            # for each type of storage
            temp_samples = np.arange(self.raw_count, dtype=dtype)
            temp_samples.tofile(temp_path)
            for num_channels in [1, 4, 8]:
                # for single or 8 channel
                for complex_prefix in ["r", "c"]:
                    # for real or complex
                    target_count = self.raw_count
                    temp_meta = SigMFFile(
                        name="test",
                        data_file=temp_path,
                        global_info={
                            SigMFFile.DATATYPE_KEY: f"{complex_prefix}{key}_le",
                            SigMFFile.NUM_CHANNELS_KEY: num_channels,
                            SigMFFile.VERSION_KEY: __specification__,
                        },
                    )
                    temp_meta.tofile(temp_archive, toarchive=True)

                    reader = SigMFArchiveReader(temp_archive)
                    assert len(reader) == 1
                    readback = reader[0]
                    readback_samples = readback[:]

                    if complex_prefix == "c":
                        # complex data will be half as long
                        target_count //= 2
                        self.assertTrue(np.all(np.iscomplex(readback_samples)))
                    if num_channels != 1:
                        # check expected # of channels
                        self.assertEqual(
                            readback_samples.ndim,
                            2,
                            "Mismatch in shape of readback samples.",
                        )
                    target_count //= num_channels

                    self.assertEqual(
                        target_count,
                        temp_meta._count_samples(),
                        "Mismatch in expected metadata length.",
                    )
                    self.assertEqual(
                        target_count,
                        len(readback),
                        "Mismatch in expected readback length",
                    )


def test_extract_single_recording(test_sigmffile):
    """Test reading an archive with 1 recording"""
    with tempfile.NamedTemporaryFile() as tf:
        expected_sigmffile = test_sigmffile
        arch = SigMFArchive(expected_sigmffile, path=tf.name)
        reader = SigMFArchiveReader(arch.path)
        assert len(reader) == 1
        actual_sigmffile = reader[0]
        assert expected_sigmffile == actual_sigmffile


def test_extract_multi_recording(test_sigmffile, test_alternate_sigmffile):
    """Test reading an archive with 2 recordings"""
    with tempfile.NamedTemporaryFile() as tf:
        # Create a multi-recording archive
        expected_sigmffiles = SigMFFileCollection([test_sigmffile, test_alternate_sigmffile])
        arch = SigMFArchive(expected_sigmffiles, path=tf.name)
        reader = SigMFArchiveReader(arch.path)
        assert len(reader) == 2
        for expected in expected_sigmffiles.get_sigmffiles():
            assert expected in reader.sigmffiles


def test_archivereader_subfolders_1(test_sigmffile,
                                        test_alternate_sigmffile):
    """Test reading a SigMF archive containing 2 subfolders each containing a subfolder"""
    try:
        os.makedirs("folder1", exist_ok=True)
        test_sigmffile.name = os.path.join("folder1", "test1")
        os.makedirs("folder2", exist_ok=True)
        test_alternate_sigmffile.name = os.path.join("folder2", "test2")

        os.makedirs("archive_folder", exist_ok=True)
        archive_path = os.path.join("archive_folder", "test_archive.sigmf")
        input_sigmffiles = SigMFFileCollection([test_sigmffile, test_alternate_sigmffile])
        arch = SigMFArchive(input_sigmffiles, path=archive_path)
        reader = SigMFArchiveReader(arch.path)
        assert len(reader) == 2  # number of SigMFFiles
        for actual_sigmffile in reader:
            assert actual_sigmffile in input_sigmffiles.get_sigmffiles()
    finally:
        if os.path.exists(archive_path):
            os.remove(archive_path)
        if os.path.exists("folder1"):
            shutil.rmtree("folder1")
        if os.path.exists("folder2"):
            shutil.rmtree("folder2")
        if os.path.exists("archive_folder"):
            shutil.rmtree("archive_folder")


def test_archivereader_subfolders_2(test_sigmffile,
                                   test_alternate_sigmffile):
    """Test reading a SigMF archive containing 1 subfolder containing 2 additional subfolders"""
    try:
        os.makedirs("folder1", exist_ok=True)
        test_sigmffile.name = os.path.join("folder1", "test1")
        test_alternate_sigmffile.name = os.path.join("folder1", "test2")

        os.makedirs("archive_folder", exist_ok=True)
        archive_path = os.path.join("archive_folder", "test_archive.sigmf")
        input_sigmffiles = SigMFFileCollection([test_sigmffile, test_alternate_sigmffile])
        arch = SigMFArchive(input_sigmffiles, path=archive_path)
        reader = SigMFArchiveReader(arch.path)
        assert len(reader) == 2  # number of SigMFFiles
        for actual_sigmffile in reader:
            assert actual_sigmffile in input_sigmffiles.get_sigmffiles()
    finally:
        if os.path.exists(archive_path):
            os.remove(archive_path)
        if os.path.exists("folder1"):
            shutil.rmtree("folder1")
