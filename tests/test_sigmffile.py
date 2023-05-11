# Copyright 2017 GNU Radio Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import shutil
import tempfile
import json
import numpy as np
import unittest

from sigmf import sigmffile, utils
from sigmf.archivereader import SigMFArchiveReader
from sigmf.sigmffile import SigMFFile, fromarchive
from sigmf.archive import SIGMF_DATASET_EXT, SIGMF_METADATA_EXT, SigMFArchive

from .testdata import *


class TestClassMethods(unittest.TestCase):
    def setUp(self):
        '''assure tests have a valid SigMF object to work with'''
        _, temp_path = tempfile.mkstemp()
        TEST_FLOAT32_DATA_1.tofile(temp_path)
        self.sigmf_object = SigMFFile("test",
                                      TEST_METADATA_1,
                                      data_file=temp_path)

    def test_iterator_basic(self):
        '''make sure default batch_size works'''
        count = 0
        for _ in self.sigmf_object:
            count += 1
        self.assertEqual(count, len(self.sigmf_object))


def simulate_capture(sigmf_md, n, capture_len):
    start_index = capture_len * n

    capture_md = {"core:datetime": utils.get_sigmf_iso8601_datetime_now()}

    sigmf_md.add_capture(start_index=start_index, metadata=capture_md)

    annotation_md = {
        "core:latitude": 40.0 + 0.0001 * n,
        "core:longitude": -105.0 + 0.0001 * n,
    }

    sigmf_md.add_annotation(start_index=start_index,
                            length=capture_len,
                            metadata=annotation_md)


def test_default_constructor():
    SigMFFile(name="test")


def test_set_non_required_global_field():
    sigf = SigMFFile(name="test")
    sigf.set_global_field('this_is:not_in_the_schema', None)


def test_add_capture():
    sigf = SigMFFile(name="test")
    sigf.add_capture(start_index=0, metadata={})


def test_add_annotation():
    sigf = SigMFFile(name="test")
    sigf.add_capture(start_index=0)
    meta = {"latitude": 40.0, "longitude": -105.0}
    sigf.add_annotation(start_index=0, length=128, metadata=meta)


def test_add_annotation_with_duplicate_key():
    f = SigMFFile(name="test")
    f.add_capture(start_index=0)
    m1 = {"latitude": 40.0, "longitude": -105.0}
    f.add_annotation(start_index=0, length=128, metadata=m1)
    m2 = {"latitude": 50.0, "longitude": -115.0}
    f.add_annotation(start_index=0, length=128, metadata=m2)
    assert len(f.get_annotations(64)) == 2


def test_fromarchive(test_sigmffile):
    print("test_sigmffile is:\n", test_sigmffile)
    tf = tempfile.mkstemp()[1]
    td = tempfile.mkdtemp()
    archive_path = test_sigmffile.archive(file_path=tf)
    result = sigmffile.fromarchive(archive_path=archive_path, dir=td)
    assert result == test_sigmffile
    os.remove(tf)
    shutil.rmtree(td)


def test_fromarchive_multi_recording(test_sigmffile,
                                     test_alternate_sigmffile,
                                     test_alternate_sigmffile_2):
    # single recording
    with tempfile.NamedTemporaryFile(suffix=".sigmf") as t_file:
        path = t_file.name
        test_sigmffile.archive(fileobj=t_file)
        single_sigmffile = fromarchive(path)
        assert isinstance(single_sigmffile, SigMFFile)
        assert single_sigmffile == test_sigmffile

    # 2 recordings
    with tempfile.NamedTemporaryFile(suffix=".sigmf") as t_file:
        path = t_file.name
        input_sigmffiles = [test_sigmffile, test_alternate_sigmffile]
        SigMFArchive(input_sigmffiles, fileobj=t_file)
        sigmffile_one, sigmffile_two = fromarchive(path)
        assert isinstance(sigmffile_one, SigMFFile)
        assert sigmffile_one == test_sigmffile
        assert isinstance(sigmffile_two, SigMFFile)
        assert sigmffile_two == test_alternate_sigmffile

    # 3 recordings
    with tempfile.NamedTemporaryFile(suffix=".sigmf") as t_file:
        path = t_file.name
        input_sigmffiles = [test_sigmffile,
                            test_alternate_sigmffile,
                            test_alternate_sigmffile_2]
        SigMFArchive(input_sigmffiles, fileobj=t_file)
        list_of_sigmffiles = fromarchive(path)
        assert len(list_of_sigmffiles) == 3
        assert isinstance(list_of_sigmffiles[0], SigMFFile)
        assert list_of_sigmffiles[0] == test_sigmffile
        assert isinstance(list_of_sigmffiles[1], SigMFFile)
        assert list_of_sigmffiles[1] == test_alternate_sigmffile
        assert isinstance(list_of_sigmffiles[2], SigMFFile)
        assert list_of_sigmffiles[2] == test_alternate_sigmffile_2


def test_add_multiple_captures_and_annotations():
    sigf = SigMFFile(name="test")
    for idx in range(3):
        simulate_capture(sigf, idx, 1024)


def test_multichannel_types():
    '''check that real & complex for all types is reading multiple channels correctly'''
    lut = {
        'i8': np.int8,
        'u8': np.uint8,
        'i16': np.int16,
        'u16': np.uint16,
        'u32': np.uint32,
        'i32': np.int32,
        'f32': np.float32,
        'f64': np.float64,
    }
    raw_count = 16
    _, temp_path = tempfile.mkstemp()
    for key, dtype in lut.items():
        # for each type of storage
        np.arange(raw_count, dtype=dtype).tofile(temp_path)
        for num_channels in [1, 8]:
            # for single or 8 channel
            for complex_prefix in ['r', 'c']:
                # for real or complex
                check_count = raw_count * 1 # deepcopy
                temp_signal = SigMFFile(
                    name="test",
                    data_file=temp_path,
                    global_info={
                        SigMFFile.DATATYPE_KEY: f'{complex_prefix}{key}_le',
                        SigMFFile.NUM_CHANNELS_KEY: num_channels,
                    },
                )
                temp_samples = temp_signal.read_samples()

                if complex_prefix == 'c':
                    # complex data will be half as long
                    check_count //= 2
                    assert np.all(np.iscomplex(temp_samples))
                if num_channels != 1:
                    assert temp_samples.ndim == 2
                check_count //= num_channels

                assert check_count == temp_signal._count_samples()


def test_multichannel_seek():
    '''assure that seeking is working correctly with multichannel files'''
    _, temp_path = tempfile.mkstemp()
    # write some dummy data and read back
    np.arange(18, dtype=np.uint16).tofile(temp_path)
    temp_signal = SigMFFile(
        name="test",
        data_file=temp_path,
        global_info={
            SigMFFile.DATATYPE_KEY: 'cu16_le',
            SigMFFile.NUM_CHANNELS_KEY: 3,
        },
    )
    # read after the first sample
    temp_samples = temp_signal.read_samples(start_index=1, autoscale=False)
    # assure samples are in the order we expect
    assert np.all(temp_samples[:, 0] == np.array([6+7j, 12+13j]))


def test_key_validity():
    '''assure the keys in test metadata are valid'''
    for top_key, top_val in TEST_METADATA_1.items():
        if type(top_val) is dict:
            for core_key in top_val.keys():
                assert core_key in vars(SigMFFile)[f'VALID_{top_key.upper()}_KEYS']
        elif type(top_val) is list:
            # annotations are in a list
            for annot in top_val:
                for core_key in annot.keys():
                    assert core_key in SigMFFile.VALID_ANNOTATION_KEYS
        else:
            raise ValueError('expected list or dict')


def test_ordered_metadata():
    '''check to make sure the metadata is sorted as expected'''
    sigf = SigMFFile(name="test")
    top_sort_order = ['global', 'captures', 'annotations']
    for kdx, key in enumerate(sigf.ordered_metadata()):
        assert kdx == top_sort_order.index(key)


def test_captures_checking():
    '''
    these tests make sure the various captures access tools work properly
    '''
    np.array(TEST_U8_DATA0, dtype=np.uint8).tofile('/tmp/d0.sigmf-data')
    with open('/tmp/d0.sigmf-meta','w') as f0: json.dump(TEST_U8_META0, f0)
    np.array(TEST_U8_DATA1, dtype=np.uint8).tofile('/tmp/d1.sigmf-data')
    with open('/tmp/d1.sigmf-meta','w') as f1: json.dump(TEST_U8_META1, f1)
    np.array(TEST_U8_DATA2, dtype=np.uint8).tofile('/tmp/d2.sigmf-data')
    with open('/tmp/d2.sigmf-meta','w') as f2: json.dump(TEST_U8_META2, f2)
    np.array(TEST_U8_DATA3, dtype=np.uint8).tofile('/tmp/d3.sigmf-data')
    with open('/tmp/d3.sigmf-meta','w') as f3: json.dump(TEST_U8_META3, f3)
    np.array(TEST_U8_DATA4, dtype=np.uint8).tofile('/tmp/d4.sigmf-data')
    with open('/tmp/d4.sigmf-meta','w') as f4: json.dump(TEST_U8_META4, f4)

    sigmf0 = sigmffile.fromfile('/tmp/d0.sigmf-meta', skip_checksum=True)
    sigmf1 = sigmffile.fromfile('/tmp/d1.sigmf-meta', skip_checksum=True)
    sigmf2 = sigmffile.fromfile('/tmp/d2.sigmf-meta', skip_checksum=True)
    sigmf3 = sigmffile.fromfile('/tmp/d3.sigmf-meta', skip_checksum=True)
    sigmf4 = sigmffile.fromfile('/tmp/d4.sigmf-meta', skip_checksum=True)

    assert sigmf0._count_samples() == 256
    assert sigmf0._is_conforming_dataset()
    assert (0,0) == sigmf0.get_capture_byte_boundarys(0)
    assert (0,256) == sigmf0.get_capture_byte_boundarys(1)
    assert np.array_equal(TEST_U8_DATA0, sigmf0.read_samples(autoscale=False))
    assert np.array_equal(np.array([]), sigmf0.read_samples_in_capture(0))
    assert np.array_equal(TEST_U8_DATA0, sigmf0.read_samples_in_capture(1,autoscale=False))

    assert sigmf1._count_samples() == 192
    assert not sigmf1._is_conforming_dataset()
    assert (32,160) == sigmf1.get_capture_byte_boundarys(0)
    assert (160,224) == sigmf1.get_capture_byte_boundarys(1)
    assert np.array_equal(np.array(range(128)), sigmf1.read_samples_in_capture(0,autoscale=False))
    assert np.array_equal(np.array(range(128,192)), sigmf1.read_samples_in_capture(1,autoscale=False))

    assert sigmf2._count_samples() == 192
    assert not sigmf2._is_conforming_dataset()
    assert (32,160) == sigmf2.get_capture_byte_boundarys(0)
    assert (176,240) == sigmf2.get_capture_byte_boundarys(1)
    assert np.array_equal(np.array(range(128)), sigmf2.read_samples_in_capture(0,autoscale=False))
    assert np.array_equal(np.array(range(128,192)), sigmf2.read_samples_in_capture(1,autoscale=False))

    assert sigmf3._count_samples() == 192
    assert not sigmf3._is_conforming_dataset()
    assert (32,64) == sigmf3.get_capture_byte_boundarys(0)
    assert (64,160) == sigmf3.get_capture_byte_boundarys(1)
    assert (192,256) == sigmf3.get_capture_byte_boundarys(2)
    assert np.array_equal(np.array(range(32)), sigmf3.read_samples_in_capture(0,autoscale=False))
    assert np.array_equal(np.array(range(32,128)), sigmf3.read_samples_in_capture(1,autoscale=False))
    assert np.array_equal(np.array(range(128,192)), sigmf3.read_samples_in_capture(2,autoscale=False))

    assert sigmf4._count_samples() == 96
    assert not sigmf4._is_conforming_dataset()
    assert (32,160) == sigmf4.get_capture_byte_boundarys(0)
    assert (160,224) == sigmf4.get_capture_byte_boundarys(1)
    assert np.array_equal(np.array(range(64)), sigmf4.read_samples_in_capture(0,autoscale=False)[:,0])
    assert np.array_equal(np.array(range(64,96)), sigmf4.read_samples_in_capture(1,autoscale=False)[:,1])


def test_archive_collection(test_sigmffile,
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
    data = [TEST_FLOAT32_DATA_1, TEST_FLOAT32_DATA_2, TEST_FLOAT32_DATA_3]
    try:
        for sigmf_meta_file, sigmf_file, _data in zip(sigmf_meta_files,
                                                      input_sigmf_files,
                                                      data):
            with open(sigmf_meta_file, mode="w") as sigmf_meta_fd:
                sigmf_file.dump(sigmf_meta_fd)
            sample_data = sigmf_file.read_samples(autoscale=False,
                                                  raw_components=True)
            assert np.array_equal(sample_data, _data)
            sample_data.tofile(sigmf_file.name + SIGMF_DATASET_EXT)
        test_collection = sigmffile.SigMFCollection(sigmf_meta_files)
        with tempfile.NamedTemporaryFile(suffix=".sigmf") as tmpfile:
            archive_path = test_collection.archive(fileobj=tmpfile)
            archive_reader = SigMFArchiveReader(path=archive_path)
            for input_sigmf_file in input_sigmf_files:
                assert input_sigmf_file in archive_reader.sigmffiles
            assert test_collection == archive_reader.collection
    finally:
        for sigmf_meta_file in sigmf_meta_files:
            if os.path.exists(sigmf_meta_file):
                os.remove(sigmf_meta_file)
        for sigmf_file in input_sigmf_files:
            filename = sigmf_file.name + SIGMF_DATASET_EXT
            if os.path.exists(filename):
                os.remove(filename)


def test_tofile_collection(test_sigmffile,
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
    data = [TEST_FLOAT32_DATA_1, TEST_FLOAT32_DATA_2, TEST_FLOAT32_DATA_3]
    try:
        for sigmf_meta_file, sigmf_file, _data in zip(sigmf_meta_files,
                                                      input_sigmf_files,
                                                      data):
            with open(sigmf_meta_file, mode="w") as sigmf_meta_fd:
                sigmf_file.dump(sigmf_meta_fd)
            sample_data = sigmf_file.read_samples(autoscale=False,
                                                  raw_components=True)
            assert np.array_equal(sample_data, _data)
            sample_data.tofile(sigmf_file.name + SIGMF_DATASET_EXT)
        test_collection = sigmffile.SigMFCollection(sigmf_meta_files)
        with tempfile.NamedTemporaryFile(suffix=".sigmf") as tmpfile:
            test_collection.tofile(tmpfile.name, toarchive=True)
            archive_reader = SigMFArchiveReader(path=tmpfile.name)
            for input_sigmf_file in input_sigmf_files:
                assert input_sigmf_file in archive_reader.sigmffiles
            assert test_collection == archive_reader.collection
    finally:
        for sigmf_meta_file in sigmf_meta_files:
            if os.path.exists(sigmf_meta_file):
                os.remove(sigmf_meta_file)
        for sigmf_file in input_sigmf_files:
            filename = sigmf_file.name + SIGMF_DATASET_EXT
            if os.path.exists(filename):
                os.remove(filename)
