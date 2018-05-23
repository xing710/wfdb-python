import bz2
from datetime import timedelta
import gzip
from multiprocessing import Pool
import os
from shutil import copyfileobj
import subprocess
import time

import cxutils as cx
import lz4.frame
import numpy as np
import pandas as pd
import wfdb
from wfdb.io._signal import wfdbfmtres
import zstd


def compress_file(file, fmt, level):
    """
    Compress and decompress a single file.

    Parameters
    ----------
    file : str
        Full file path
    fmt : str
        The compression format
    level : int
        The compression level

    Returns
    -------
    compressed_size : int
       Compressed file size in bytes
    compression_time : float
        Time taken to compress, in seconds.
    decompression_time : float
        Time taken to decompress, in seconds.

    """
    with open(file, 'rb') as f_in:
        u_data = f_in.read()

        t0 = time.time()

        if fmt == 'zstd':
            cctx = zstd.ZstdCompressor(level=level, write_content_size=True)
            c_data = cctx.compress(u_data)
            t1 = time.time()
            dctx = zstd.ZstdDecompressor()
            u_data = dctx.decompress(c_data)
        elif fmt == 'bz2':
            c_data = bz2.compress(u_data, compresslevel=level)
            t1 = time.time()
            u_data = bz2.decompress(c_data)
        elif fmt == 'gzip':
            c_data = gzip.compress(u_data, compresslevel=level)
            t1 = time.time()
            u_data = gzip.decompress(c_data)
        elif fmt == 'lz4':
            c_data = lz4.frame.compress(u_data, compression_level=level)
            t1 = time.time()
            u_data = lz4.frame.decompress(c_data)
        elif fmt == 'flac':
            # command line processing
            record = wfdb.rdheader(file[:-4])
            out_file = os.path.join('/home/cx1111/Downloads/writedir/', os.path.basename(file).strip('.dat') + '.flac')
            # Write the file since we need to decompress it
            compress_command = "flac %s --endian=little --channels=%d --sample-rate=%d --bps=%d --sign=signed -%d -o %s" % (
                file, record.n_sig, record.fs, wfdbfmtres(record.fmt[0]), level, out_file)
            subprocess.run(compress_command, shell=True)
            t1 = time.time()
            decompress_command = "flac -d %s -c" % out_file
            subprocess.run(decompress_command, shell=True)

        t2 = time.time()

        if fmt == 'flac':
            compressed_size = os.path.getsize(out_file)
            os.remove(out_file)
        else:
            compressed_size = len(c_data)

        compression_time = t1 - t0
        decompression_time = t2 - t1

    return compressed_size, compression_time, decompression_time


def test_compression(fmt, compress_level, test_dat_files):
    """
    Test a type of compression of a specified level, on all target dat
    files.

    """
    n_files = len(test_dat_files)
    uncompressed_sizes = [os.path.getsize(file) for file in test_dat_files]

    with Pool(os.cpu_count() - 1) as pool:
        output = pool.starmap(compress_file,
                                        zip(test_dat_files,
                                            n_files * [fmt],
                                            n_files * [compress_level]))
    compressed_sizes, compression_times, decompression_times = zip(*output)

    # Calculate performance summary
    compression_ratio = np.sum(uncompressed_sizes) / np.sum(compressed_sizes)
    compression_time = np.sum(compression_times)
    decompression_time = np.sum(decompression_times)

    return compression_ratio, compression_time, decompression_time


def compare_compressions(fmts, compress_levels):
    """
    For each compression format/level pair, run the full compression
    test. Return the aggregate results. Rounds to nearest second.

    The data is the waveforms of the first 100 patients
    mimic3wdb/matched/ Total size is about 22 Gb.

    Returns
    -------
    compression_results : pandas dataframe
      Dataframe of results for each compression format/level combination.
      Results include compression ratio, compression time, and decompression
      time.
    dataset_info : dict
      Dictionary of

    """
    # Files to be compressed
    data_dirs = cx.list_dirs('/home/cx1111/Downloads/data/mimic3wdb/matched')
    test_dat_files = cx.list_files(data_dirs, extensions=['dat'])

    # kloogy inaccurate fix for flac files
    if 'flac' in fmts:
        test_dat_files = [file for file in test_dat_files if not file.endswith('n.dat')]

    n_files = len(test_dat_files)
    uncompressed_sizes = [os.path.getsize(file) for file in test_dat_files]
    uncompressed_total = cx.readable_size(np.sum(uncompressed_sizes))
    dataset_info = {'n_files':n_files, 'uncompressed_total':uncompressed_total}

    # Compression results
    compression_results = pd.DataFrame(columns=['fmt', 'compress_level',
                                       'compression_ratio', 'time_compress',
                                       'time_decompress'])

    # Iterate through formats and compress levels
    for i in range(len(fmts)):
        fmt = fmts[i]
        compress_level = compress_levels[i]
        print('Testing %s with compress level=%d ...' % (fmt, compress_level))

        (compression_ratio, compression_time,
         decompression_time) = test_compression(fmt=fmt,
                                                compress_level=compress_level,
                                                test_dat_files=test_dat_files)

        compression_results.loc[i] = [fmt, compress_level,
                                      '%.2f' % compression_ratio,
                                      str(timedelta(seconds=int(compression_time))),
                                      str(timedelta(seconds=int(decompression_time)))]

    print('Full benchmark complete')
    return compression_results, dataset_info
