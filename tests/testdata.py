# Copyright: Multiple Authors
#
# This file is part of sigmf-python. https://github.com/sigmf/sigmf-python
#
# SPDX-License-Identifier: LGPL-3.0-or-later

"""Shared test data for tests."""

import numpy as np

from sigmf import SigMFFile, __specification__, __version__

TEST_FLOAT32_DATA_1 = np.arange(16, dtype=np.float32)

TEST_METADATA_1 = {
    SigMFFile.ANNOTATION_KEY: [{SigMFFile.LENGTH_INDEX_KEY: 16, SigMFFile.START_INDEX_KEY: 0}],
    SigMFFile.CAPTURE_KEY: [{SigMFFile.START_INDEX_KEY: 0}],
    SigMFFile.GLOBAL_KEY: {
        SigMFFile.DATATYPE_KEY: "rf32_le",
        SigMFFile.HASH_KEY: "f4984219b318894fa7144519185d1ae81ea721c6113243a52b51e444512a39d74cf41a4cec3c5d000bd7277cc71232c04d7a946717497e18619bdbe94bfeadd6",
        SigMFFile.NUM_CHANNELS_KEY: 1,
        SigMFFile.VERSION_KEY: __specification__,
    },
}

TEST_FLOAT32_DATA_2 = np.arange(16, 32, dtype=np.float32)

TEST_METADATA_2 = {
    SigMFFile.ANNOTATION_KEY: [{SigMFFile.LENGTH_INDEX_KEY: 16, SigMFFile.START_INDEX_KEY: 0}],
    SigMFFile.CAPTURE_KEY: [{SigMFFile.START_INDEX_KEY: 0}],
    SigMFFile.GLOBAL_KEY:  {
        SigMFFile.DATATYPE_KEY: 'rf32_le',
        SigMFFile.HASH_KEY: 'a85018cf117a4704596c0f360dbc3fce2d0d561966d865b9b8a356634161bde6a528c5181837890a9f4d54243e2e8eaf7e19bd535e54e3e34aabf76793723d03',
        SigMFFile.NUM_CHANNELS_KEY: 1,
        SigMFFile.VERSION_KEY: __specification__,
    }
}

TEST_FLOAT32_DATA_3 = np.arange(32, 48, dtype=np.float32)

TEST_METADATA_3 = {
    SigMFFile.ANNOTATION_KEY: [{SigMFFile.LENGTH_INDEX_KEY: 16, SigMFFile.START_INDEX_KEY: 0}],
    SigMFFile.CAPTURE_KEY: [{SigMFFile.START_INDEX_KEY: 0}],
    SigMFFile.GLOBAL_KEY:  {
        SigMFFile.DATATYPE_KEY: 'rf32_le',
        SigMFFile.HASH_KEY: '089753bd48a1724c485e822eaf4d510491e4e54faa83cc3e7b3f18a9f651813190862aa97c922278454c66f20a741050762e008cbe4f96f3bd0dcdb7d720179d',
        SigMFFile.NUM_CHANNELS_KEY: 1,
        SigMFFile.VERSION_KEY: __specification__,
    }
}

# Data0 is a test of a compliant two capture recording
TEST_U8_DATA0 = list(range(256))
TEST_U8_META0 = {
    SigMFFile.ANNOTATION_KEY: [],
    SigMFFile.CAPTURE_KEY: [
        {SigMFFile.START_INDEX_KEY: 0, SigMFFile.HEADER_BYTES_KEY: 0},
        {SigMFFile.START_INDEX_KEY: 0, SigMFFile.HEADER_BYTES_KEY: 0},
    ],  # very strange..but technically legal?
    SigMFFile.GLOBAL_KEY: {SigMFFile.DATATYPE_KEY: "ru8", SigMFFile.TRAILING_BYTES_KEY: 0},
}
# Data1 is a test of a two capture recording with header_bytes and trailing_bytes set
TEST_U8_DATA1 = [0xFE] * 32 + list(range(192)) + [0xFF] * 32
TEST_U8_META1 = {
    SigMFFile.ANNOTATION_KEY: [],
    SigMFFile.CAPTURE_KEY: [
        {SigMFFile.START_INDEX_KEY: 0, SigMFFile.HEADER_BYTES_KEY: 32},
        {SigMFFile.START_INDEX_KEY: 128},
    ],
    SigMFFile.GLOBAL_KEY: {SigMFFile.DATATYPE_KEY: "ru8", SigMFFile.TRAILING_BYTES_KEY: 32},
}
# Data2 is a test of a two capture recording with multiple header_bytes set
TEST_U8_DATA2 = [0xFE] * 32 + list(range(128)) + [0xFE] * 16 + list(range(128, 192)) + [0xFF] * 16
TEST_U8_META2 = {
    SigMFFile.ANNOTATION_KEY: [],
    SigMFFile.CAPTURE_KEY: [
        {SigMFFile.START_INDEX_KEY: 0, SigMFFile.HEADER_BYTES_KEY: 32},
        {SigMFFile.START_INDEX_KEY: 128, SigMFFile.HEADER_BYTES_KEY: 16},
    ],
    SigMFFile.GLOBAL_KEY: {SigMFFile.DATATYPE_KEY: "ru8", SigMFFile.TRAILING_BYTES_KEY: 16},
}
# Data3 is a test of a three capture recording with multiple header_bytes set
TEST_U8_DATA3 = [0xFE] * 32 + list(range(128)) + [0xFE] * 32 + list(range(128, 192))
TEST_U8_META3 = {
    SigMFFile.ANNOTATION_KEY: [],
    SigMFFile.CAPTURE_KEY: [
        {SigMFFile.START_INDEX_KEY: 0, SigMFFile.HEADER_BYTES_KEY: 32},
        {SigMFFile.START_INDEX_KEY: 32},
        {SigMFFile.START_INDEX_KEY: 128, SigMFFile.HEADER_BYTES_KEY: 32},
    ],
    SigMFFile.GLOBAL_KEY: {SigMFFile.DATATYPE_KEY: "ru8"},
}
# Data4 is a two channel version of Data0
TEST_U8_DATA4 = [0xFE] * 32 + [y for y in list(range(96)) for i in [0, 1]] + [0xFF] * 32
TEST_U8_META4 = {
    SigMFFile.ANNOTATION_KEY: [],
    SigMFFile.CAPTURE_KEY: [
        {SigMFFile.START_INDEX_KEY: 0, SigMFFile.HEADER_BYTES_KEY: 32},
        {SigMFFile.START_INDEX_KEY: 64},
    ],
    SigMFFile.GLOBAL_KEY: {
        SigMFFile.DATATYPE_KEY: "ru8",
        SigMFFile.TRAILING_BYTES_KEY: 32,
        SigMFFile.NUM_CHANNELS_KEY: 2,
    },
}
