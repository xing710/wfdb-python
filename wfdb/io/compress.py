import bz2
import gzip
from multiprocessing import Pool
import os
from shutil import copyfileobj
import time

import cxutils as cx
import lz4.frame
import numpy as np
import pandas as pd
import zstd


def compress_file(file, fmt, level):
    """
    Compress and decompress a file with a particular fmt. Return
    compressed size and time for compression/decompression.

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

        compressed_size = len(c_data)

        t2 = time.time()
        t_compress = t1 - t0
        t_decompress = t2 - t1

    return compressed_size, t_compress, t_decompress


# can change header
# flac, wabpack
def test_compression(fmt, compress_level):
    """
    Test compression on target dat files.

    From mitdb and first 50 patient records of mimic3wdb/matched/

    Total size is about 10 Gb.

    """
    data_dirs = (['/home/cx1111/Downloads/data/mitdb']
                 + cx.list_dirs('/home/cx1111/Downloads/data/mimic3wdb/matched'))

    test_dat_files = cx.list_files(data_dirs)

    n_files = len(test_dat_files)

    uncompressed_sizes = [os.path.getsize(file) for file in test_dat_files]

    with Pool(os.cpu_count() - 1) as pool:
        output = pool.starmap(compress_file,
                                        zip(test_dat_files,
                                            n_files * [fmt],
                                            n_files * [compress_level]))
    compressed_sizes, compression_times, decompression_times = zip(*output)

    uncompressed_sizes = np.array(uncompressed_sizes)
    compressed_sizes = np.array(compressed_sizes)
    decompression_times = np.array(decompression_times)
    compression_ratios = uncompressed_sizes / compressed_sizes

    # Return the compression ratios and time taken
    return (uncompressed_sizes, compressed_sizes, compression_ratios,
            compression_times, decompression_times)


def summarize_compression(uncompressed_sizes, compressed_sizes,
                          compression_ratios, compression_times,
                          decompression_times, mode='print'):
    """
    Print or return a summary of the compression

    Input parameters are outputs of `test_compression`.

    """
    n_files = len(uncompressed_sizes)
    uncompressed_total = np.sum(uncompressed_sizes)
    compressed_total = np.sum(compressed_sizes)

    overall_compression_ratio = uncompressed_total / compressed_total

    # Sum of min(compressed, uncompressed) for all files
    smallest_total = np.sum([min(uncompressed_sizes[i], compressed_sizes[i])
                             for i in range(n_files)])
    smallest_overall_compression_ratio = uncompressed_total / smallest_total

    # Total times
    t_compress = np.sum(compression_times)
    t_decompress = np.sum(decompression_times)

    if mode == 'print':
        print('Number of files compressed: %d' % n_files)
        print('Total size of uncompressed files: %s'
              % cx.readable_size(uncompressed_total, 'string'))
        print('Total size of compressed files: %s'
              % cx.readable_size(compressed_total, 'string'))
        print('Overall compression ratio: %.2f'
              % overall_compression_ratio)
        print('Overall compression ratio without compressing inflated files: %.2f'
              % smallest_overall_compression_ratio)
        print('Total compression time: %.2f' % t_compress)
        print('Total compression time: %.2f' % t_decompress)
    else:
        return (n_files, uncompressed_total, compressed_total,
                overall_compression_ratio, t_compress, t_decompress)


def compare_compressions(fmts, compress_levels):
    """
    Run the compression tests and summarize the results of multiple
    formats/compress pairs.

    """
    df = pd.DataFrame(columns=['fmt', 'compress_level', 'n_files',
                               'uncompressed_total', 'compressed_total',
                               'compression_ratio', 'time_compress',
                               'time_decompress'])

    # Iterate through formats and compress levels
    for i in range(len(fmts)):
        fmt = fmts[i]
        compress_level = compress_levels[i]
        print('Testing fmt: %s, compress level: %d' % (fmt, compress_level))

        (uncompressed_sizes, compressed_sizes, compression_ratios,
         compression_times, decompression_times) = test_compression(fmt=fmt,
                                          compress_level=compress_level)

        (n_files, uncompressed_total,
         compressed_total,
         overall_compression_ratio,
         t_compress, t_decompress) = summarize_compression(uncompressed_sizes,
                                                           compressed_sizes,
                                                           compression_ratios,
                                                           compression_times,
                                                           decompression_times,
                                                           mode='return')

        df.loc[i] = [fmt, compress_level, n_files,
                     cx.readable_size(uncompressed_total, 'string'),
                     cx.readable_size(compressed_total, 'string'),
                     '%.2f' % overall_compression_ratio, '%.2f' % t_compress,
                     '%.2f' % t_decompress]

    return df
