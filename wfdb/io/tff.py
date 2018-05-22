"""
Module for reading ME6000 .tff format files.

http://www.biomation.com/kin/me6000.htm

"""

import struct

import numpy as np

import pdb




def rdtff(file_name, sampfrom=0, sampto=None, channels='all'):
    """
    Read values from a tff file

    """

    file_size = os.path.getsize(file_name)

    with open(file_name, 'rb') as fp:

        fields, header_size = _rdheader(fp)


        signal = _rdsignal(fp, file_size=file_size, header_size=header_size,
                           n_sig=fields['n_sig'], bit_width=fields['bit_width'],
                           is_signed=fields['is_signed'])

    signal = _dac(signal, fields)

    return signal, fields


def _rdheader(fp):
    """
    Read header info of the windaq file
    """

    tag = None

    # The '2' tag indicates the end of tags.
    while tag != 2:
        # For each header element, there is a tag indicating data type,
        # followed by the data size, followed by the data itself. 0's
        # pad the content to the nearest 4 bytes. If data_len=0, no pad.
        tag = struct.unpack('>H', fp.read(2))[0]
        data_size = struct.unpack('>H', fp.read(2))[0]
        pad_len = (4 - (data_size % 4)) % 4
        pos = fp.tell()

        # Currently, most tags will be ignored...

        # fs, unit16
        if tag == 1003:
            fs = struct.unpack('>H', fp.read(2))[0]
        # sensor type
        elif tag == 1007:
            # Each byte contains information for one channel
            n_sig = data_size
            channel_data = struct.unpack('>%dB' % data_size, fp.read(data_size))

            channel_map = ((0, 0, 'empty'), (1, 1, 'emg'),
                           (15, 30, 'goniometer'), (31, 46, 'accelerometer'),
                           (47, 62, 'inclinometer'),
                           (63, 78, 'polar_interface'), (79, 94, 'ecg'),
                           (95, 110, 'torque'), (111, 126, 'gyrometer'),
                           (127, 142, 'sensor'))
            sig_name = []

            # The number range that the data lies between gives the
            # channel
            for data in channel_data:
                for item in channel_map:
                    if item[0] <= data <= item[1]:
                        existing_count = [item[2] in name for name in sig_name].count(True)
                        sig_name.append('%s_%d' % (item[2], existing_count))
                        break

        # sample format, uint8
        elif tag == 3:
            sample_fmt = struct.unpack('B', fp.read(1))[0]
            is_signed = bool(sample_fmt >> 7)
            # ie. 8 or 16 bits
            bit_width = sample_fmt & 127

        # Go to the next tag
        fp.seek(pos + data_size + pad_len)

    header_size = fp.tell()

    fields = {'fs':fs, 'n_sig':n_sig, 'sig_name':sig_name,
              'bit_width':bit_width, 'is_signed':is_signed}

    return fields, header_size


def _rdsignal(fp, file_size, header_size, n_sig, bit_width, is_signed):
    """
    Read the signal


    """
    # Cannot initially figure out signal length because there
    # are escape sequences.
    fp.seek(header_size)

    signal_size = file_size - header_size

    # numpy dtype
    dtype = str(int(bit_width / 8))
    if is_signed:
        dtype = 'i' + dtype
    else:
        dtype = 'u' + dtype
    # big endian
    dtype = '>' + dtype

    # Allocate memory for the maximum number of samples.
    signal = np.empty((int(signal_size / (bit_width / 8))), dtype=dtype)
    # Number of samples read
    sample_num = 0

    # Read one sample for all channels at a time
    while True:
        chunk = fp.read(2)
        if not chunk:
            break

        # Check for escape sequence
        tag = struct.unpack('>H', chunk)[0]

        if tag == -32768:
            # Escape sequence structure: int16 marker, uint8 type,
            # uint8 length, uint8 * length data, padding % 2
            fp.seek(1)
            escape_len = struct.unpack('B', fp.read(1))[0]
            fp.seek(escape_len + escape_len % 2)
        else:
            fp.seek(-2, 1)
            signal[sample_num:sample_num + n_sig] = np.fromfile(fp,
                                                                dtype=dtype,
                                                                count=n_sig)
            sample_num += n_sig

    signal = signal[:sample_num]
    signal = signal.reshape((-1, n_sig))

    return signal


def _dac(signal, fields):
    """
    Perform dac

    """

    return signal
