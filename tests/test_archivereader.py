# Copyright 2023 GNU Radio Foundation
import os
import shutil
import tempfile

import numpy as np
import unittest

from sigmf import SigMFFile, SigMFArchiveReader
from sigmf.archive import SIGMF_METADATA_EXT, SigMFArchive


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
    with tempfile.NamedTemporaryFile() as tf:
        expected_sigmffile = test_sigmffile
        arch = SigMFArchive(expected_sigmffile, path=tf.name)
        reader = SigMFArchiveReader(arch.path)
        assert len(reader) == 1
        actual_sigmffile = reader[0]
        assert expected_sigmffile == actual_sigmffile


def test_extract_multi_recording(test_sigmffile, test_alternate_sigmffile):
    with tempfile.NamedTemporaryFile() as tf:
        # Create a multi-recording archive
        expected_sigmffiles = [test_sigmffile, test_alternate_sigmffile]
        arch = SigMFArchive(expected_sigmffiles, path=tf.name)
        reader = SigMFArchiveReader(arch.path)
        assert len(reader) == 2
        for expected in expected_sigmffiles:
            assert expected in reader.sigmffiles


def test_archivereader_different_folder(test_sigmffile,
                                        test_alternate_sigmffile):
    try:
        os.makedirs("folder1", exist_ok=True)
        test_sigmffile.name = os.path.join("folder1", "test1")
        os.makedirs("folder2", exist_ok=True)
        test_alternate_sigmffile.name = os.path.join("folder2", "test2")
        meta1_filepath = test_sigmffile.name + SIGMF_METADATA_EXT
        with open(meta1_filepath, "w") as meta_fd:
            test_sigmffile.dump(meta_fd)
        meta2_filepath = test_alternate_sigmffile.name + SIGMF_METADATA_EXT
        with open(meta2_filepath, "w") as meta_fd:
            test_alternate_sigmffile.dump(meta_fd)

        os.makedirs("archive_folder", exist_ok=True)
        archive_path = os.path.join("archive_folder", "test_archive.sigmf")
        input_sigmffiles = [test_sigmffile, test_alternate_sigmffile]
        arch = SigMFArchive(input_sigmffiles, path=archive_path)
        reader = SigMFArchiveReader(arch.path)
        assert len(reader) == 2  # number of SigMFFiles
        for actual_sigmffile in reader:
            assert actual_sigmffile in input_sigmffiles
    finally:
        if os.path.exists(meta1_filepath):
            os.remove(meta1_filepath)
        if os.path.exists(meta2_filepath):
            os.remove(meta2_filepath)
        if os.path.exists(archive_path):
            os.remove(archive_path)
        if os.path.exists("folder1"):
            shutil.rmtree("folder1")
        if os.path.exists("folder2"):
            shutil.rmtree("folder2")
        if os.path.exists("archive_folder"):
            shutil.rmtree("archive_folder")


def test_archivereader_same_folder(test_sigmffile,
                                   test_alternate_sigmffile):
    try:
        os.makedirs("folder1", exist_ok=True)
        test_sigmffile.name = os.path.join("folder1", "test1")
        test_alternate_sigmffile.name = os.path.join("folder1", "test2")
        meta1_filepath = test_sigmffile.name + SIGMF_METADATA_EXT
        with open(meta1_filepath, "w") as meta_fd:
            test_sigmffile.dump(meta_fd)
        meta2_filepath = test_alternate_sigmffile.name + SIGMF_METADATA_EXT
        with open(meta2_filepath, "w") as meta_fd:
            test_alternate_sigmffile.dump(meta_fd)
        archive_path = os.path.join("folder1", "test_archive.sigmf")
        input_sigmffiles = [test_sigmffile, test_alternate_sigmffile]
        arch = SigMFArchive(input_sigmffiles, path=archive_path)
        reader = SigMFArchiveReader(arch.path)
        assert len(reader) == 2  # number of SigMFFiles
        for actual_sigmffile in reader:
            assert actual_sigmffile in input_sigmffiles
    finally:
        if os.path.exists(meta1_filepath):
            os.remove(meta1_filepath)
        if os.path.exists(meta2_filepath):
            os.remove(meta2_filepath)
        if os.path.exists(archive_path):
            os.remove(archive_path)
        if os.path.exists("folder1"):
            shutil.rmtree("folder1")
