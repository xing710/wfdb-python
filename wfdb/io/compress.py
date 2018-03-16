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


_extensions = {'bz2':'bz2', 'gzip':'gz', 'lz4':'lz4', 'zstd':'zst'}

def compress_file(file, fmt, level,
                  write_dir='/home/cx1111/Downloads/compressed/'):
    """
    Compress a file with a particular fmt, delete it, and return the
    compressed file size.

    """

    with open(file, 'rb') as f_in:
        compressed_file = (os.path.join(write_dir, os.path.basename(file))
                           + _extensions[fmt])

        # slightly different api for zstd
        if fmt == 'zstd':
            cctx = zstd.ZstdCompressor(level=level)
            f_out =  open(compressed_file, 'wb')
            cctx.copy_stream(f_in, f_out)
        else:
            if fmt == 'bz2':
                f_out = bz2.BZ2File(compressed_file, 'wb',
                                    compresslevel=level)
            elif fmt == 'gzip':
                f_out = gzip.GzipFile(compressed_file, 'wb',
                                      compresslevel=level)
            elif fmt == 'lz4':
                f_out = lz4.frame.open(compressed_file, 'wb',
                                       compression_level=level)

            copyfileobj(f_in, f_out)

        f_out.close()

        compressed_size = os.path.getsize(compressed_file)

        # cleanup
        os.remove(compressed_file)

    return compressed_size


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
    compressed_sizes = []

    t_start = time.time()


    with Pool(os.cpu_count() - 1) as pool:
        compressed_sizes = pool.starmap(compress_file,
                                        zip(test_dat_files,
                                            n_files * [fmt],
                                            n_files * [compress_level]))

    t_end = time.time()
    t_elapsed = t_end - t_start

    uncompressed_sizes = np.array(uncompressed_sizes)
    compressed_sizes = np.array(compressed_sizes)
    compression_ratios = uncompressed_sizes / compressed_sizes

    # Return the compression ratios and time taken
    return (uncompressed_sizes, compressed_sizes, compression_ratios,
            t_elapsed)


def summarize_compression(uncompressed_sizes, compressed_sizes,
                          compression_ratios, t_elapsed, mode='print'):
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
        print('Total time elapsed: %d' % t_elapsed)
    else:
        return (n_files, uncompressed_total, compressed_total,
                overall_compression_ratio)


def compare_compressions(fmts, compress_levels):
    """
    Run the compression tests and summarize the results of multiple
    formats/compress pairs.

    """
    df = pd.DataFrame(columns=['fmt', 'compress_level', 'n_files',
                               'uncompressed_total', 'compressed_total',
                               'compression_ratio', 'time_elapsed'])
    # Iterate through formats and compress levels
    for i in range(len(fmts)):
        fmt = fmts[i]
        compress_level = compress_levels[i]
        print('Testing fmt: %s, compress level: %d' % (fmt, compress_level))

        (uncompressed_sizes, compressed_sizes, compression_ratios,
            t_elapsed) = test_compression(fmt=fmt,
                                          compress_level=compress_level)

        (n_files, uncompressed_total,
         compressed_total,
         overall_compression_ratio) = summarize_compression(uncompressed_sizes,
                                                            compressed_sizes,
                                                            compression_ratios,
                                                            t_elapsed,
                                                            mode='return')

        df.loc[i] = [fmt, compress_level, n_files,
                     cx.readable_size(uncompressed_total, 'string'),
                     cx.readable_size(compressed_total, 'string'),
                     '%.2f' % overall_compression_ratio, '%.2f' % t_elapsed]

    return df
