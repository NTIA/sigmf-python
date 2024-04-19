# Copyright: Multiple Authors
#
# This file is part of sigmf-python. https://github.com/sigmf/sigmf-python
#
# SPDX-License-Identifier: LGPL-3.0-or-later

"""Provides pytest fixtures for other tests."""

import tempfile

import pytest

from sigmf import __specification__
from sigmf.sigmffile import SigMFFile

from .testdata import (TEST_FLOAT32_DATA_1,
                       TEST_METADATA_1,
                       TEST_FLOAT32_DATA_2,
                       TEST_METADATA_2,
                       TEST_FLOAT32_DATA_3,
                       TEST_METADATA_3)


@pytest.fixture
def test_data_file_1():
    """when called, yields temporary file"""
    with tempfile.NamedTemporaryFile() as temp:
        TEST_FLOAT32_DATA_1.tofile(temp.name)
        yield temp


@pytest.fixture
def test_data_file_2():
    """when called, yields temporary file"""
    with tempfile.NamedTemporaryFile() as t:
        TEST_FLOAT32_DATA_2.tofile(t.name)
        yield t


@pytest.fixture
def test_data_file_3():
    """when called, yields temporary file"""
    with tempfile.NamedTemporaryFile() as t:
        TEST_FLOAT32_DATA_3.tofile(t.name)
        yield t


@pytest.fixture
def test_sigmffile(test_data_file_1):
    """If pytest uses this signature, will return valid SigMF file."""
    f = SigMFFile(name='test1')
    f.set_global_field("core:datatype", "rf32_le")
    f.add_annotation(start_index=0, length=len(TEST_FLOAT32_DATA_1))
    f.add_capture(start_index=0)
    f.set_data_file(test_data_file_1.name)
    assert f._metadata == TEST_METADATA_1
    return f


@pytest.fixture
def test_alternate_sigmffile(test_data_file_2):
    """If pytest uses this signature, will return valid SigMF file."""
    f = SigMFFile(name='test2')
    f.set_global_field("core:datatype", "rf32_le")
    f.add_annotation(start_index=0, length=len(TEST_FLOAT32_DATA_2))
    f.add_capture(start_index=0)
    f.set_data_file(test_data_file_2.name)
    assert f._metadata == TEST_METADATA_2
    return f


@pytest.fixture
def test_alternate_sigmffile_2(test_data_file_3):
    """If pytest uses this signature, will return valid SigMF file."""
    meta = SigMFFile("test")
    meta.set_global_field("core:datatype", "rf32_le")
    meta.set_global_field("core:version", __specification__)
    meta.add_annotation(start_index=0, length=len(TEST_FLOAT32_DATA_3))
    meta.add_capture(start_index=0)
    meta.set_data_file(test_data_file_3.name)
    assert meta._metadata == TEST_METADATA_3
    return meta
