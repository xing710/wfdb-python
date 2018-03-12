import struct

import numpy as np

import pdb

# https://www.dataq.com/resources/pdfs/misc/ff.pdf

"""
- the data file header
- the acquired ADC data
- the data file trailer.

The header contains 35 elements of various byte sizes describing virtually every data acquisition parameter,
as well as various relative references to the ADC data and trailer elements. The headers currently have
space for up to 256 channels, depending on MAX Channels

2 versions: standard and multiplexer

Is endianness little?

"""


def rdwindaq(file_name, sampfrom=0, sampto=None, channels='all'):
    """
    Read values from a windaq file

    """

    fp = open(file_name, 'rb')

    fields = _rdheader(fp)

    signal = _rdsignal(fp, fields['sig_len'], fields['n_sig'])

    signal = _dac(signal, fields)

    return signal, fields



def _rdheader(fp):
    """
    Read header info of the windaq file
    """
    # element 1, bytes 0-1
    n_sig = struct.unpack('<B', fp.read(1))[0]
    max_channel_flag = struct.unpack('<B', fp.read(1))[0]
    # flag specifies whether max_channels >= 144. Look at 7 lsb.
    if max_channel_flag:
        n_sig = n_sig & 254
    # max channels = 29. Look at 5 lsb (with max=29, not 31)
    else:
        n_sig = min(29, n_sig & 31)

    # element 2, bytes 2-3
    oversamp_factor = struct.unpack('<H', fp.read(2))[0]
    # element 3, byte 4
    header_channel_offset = struct.unpack('b', fp.read(1))[0]
    # element 4, byte 5
    bytes_per_channel_info = struct.unpack('b', fp.read(1))[0]
    # element 5, bytes 6-7
    header_size = struct.unpack('<h', fp.read(2))[0]
    # element 6, bytes 8-11. Number of ADC data bytes (if it were unpacked)
    # Use element 27 to determine if it were packed
    data_size = struct.unpack('<L', fp.read(4))[0]

    # element 7, bytes 12-15
    trailer_size = struct.unpack('<L', fp.read(4))[0]
    # element 8, bytes 16-17
    user_ann_size = struct.unpack('<H', fp.read(2))[0]
    # Skip to element 13
    fp.seek(28)
    # element 13, bytes 28-35 - "time between channel samples"
    channel_dt = struct.unpack('<d', fp.read(8))[0]
    # For sampling rate, assume it is not AT-CODAS legacy version
    # Use element 1 and 13 to calculate fs
    fs = n_sig / channel_dt
    # element 14, bytes 36-39
    start_time_offset = struct.unpack('<l', fp.read(4))[0]
    # Skip to element 27


    fp.seek(100)
    # element 27, bytes 100-101
    packing_info = struct.unpack('<H', fp.read(2))[0]
    # bit 14 of this element contains 'packed' label
    # (packed files are WinDaq/Pro+ files with at least one channel
    # that has a sample rate divisor other than 1)
    packed = bool(packing_info & 8192)
    # Skip to element 34
    fp.seek(110)

    # element 34, bytes 110 to header_size - 3
    # element 4 (currently 36) bytes of info per channel
    slope = []
    intercept = []
    units = []
    sample_rate_divisor = []

    for ch in range(n_sig):
        # Skip to item 3
        fp.seek(8, 1)
        # item 3, bytes 8-15, 8 bytes
        slope.append(struct.unpack('<d', fp.read(8))[0])
        # item 4, bytes 16-23, 8 bytes
        intercept.append(struct.unpack('<d', fp.read(8))[0])
        # item 5, bytes 24-29, 6 bytes
        units.append(struct.unpack('6s', fp.read(6))[0].decode('ascii')[:4].strip())
        # skip to item 7
        fp.seek(1, 1)
        # item 7, byte 31, 1 byte. Used for packed files only.
        sample_rate_divisor.append(struct.unpack('b', fp.read(1))[0])
        # skip to next channel
        fp.seek(4, 1)

    # Adjust number of data bytes if file is not packed
    if packed:
        pass
    else:
        pass

    sig_len = int(data_size / 2 / n_sig)

    fields = {'n_sig':n_sig, 'sig_len':sig_len,
              'slope': slope, 'intercept':intercept, 'units':units,
              'sample_rate_divisor':sample_rate_divisor}

    return fields


def _rdsignal(f, sig_len, n_sig):
    """
    Read the signal
    """
    signal = np.fromfile(f, dtype='<i2', count=sig_len * n_sig)

    # Keep 14 lsb
    np.right_shift(signal, 2, out=signal)
    # Assume no differential treatment for packed and unpacked files?
    signal = signal.reshape((sig_len, n_sig))

    return signal


def _dac(signal, fields):
    """
    Perform dac
    """

    return signal
