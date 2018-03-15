import bz2
import gzip
from multiprocessing import Pool
import os
from shutil import copyfileobj
import time

import cxutils as cx
import lz4.frame
import numpy as np
import zstandard


def compress_bz2(file, write_dir='/home/cx1111/Downloads/compressed/'):
    """
    Compress a file (bzip2), delete it, and return the compressed file
    size.

    """
    with open(file, 'rb') as f_in:
        compressed_file = os.path.join(write_dir, os.path.basename(file)) + '.bz2'

        with bz2.BZ2File(compressed_file, 'wb', compresslevel=9) as f_out:
            copyfileobj(f_in, f_out)

        compressed_size = os.path.getsize(compressed_file)

        # cleanup
        os.remove(compressed_file)

    return compressed_size


def compress_gzip(file, write_dir='/home/cx1111/Downloads/compressed/'):
    """
    Compress a file (gzip), delete it, and return the compressed file size.

    """
    with open(file, 'rb') as f_in:
        compressed_file = os.path.join(write_dir, os.path.basename(file)) + '.gz'

        with gzip.GzipFile(compressed_file, 'wb', compresslevel=9) as f_out:
            copyfileobj(f_in, f_out)

        compressed_size = os.path.getsize(compressed_file)

        # cleanup
        os.remove(compressed_file)

    return compressed_size


def compress_lz4(file, write_dir='/home/cx1111/Downloads/compressed/'):
    """
    Compress a file (lz4), delete it, and return the compressed file size.

    Specify compression level!
    """
    with open(file, 'rb') as f_in:
        compressed_file = os.path.join(write_dir, os.path.basename(file)) + '.lz4'
        with lz4.frame.open(compressed_file, 'wb') as f_out:
            copyfileobj(f_in, f_out)

        compressed_size = os.path.getsize(compressed_file)

        # cleanup
        os.remove(compressed_file)

    return compressed_size

def compress_zstd(file, write_dir='/home/cx1111/Downloads/compressed/'):
    """
    Compress a file (zstd), delete it, and return the compressed file size.

    """
    with open(file, 'rb') as f_in:
        compressed_file = os.path.join(write_dir, os.path.basename(file)) + '.lz4'

        cctx = zstd.ZstdCompressor()
        with open(compressed_file, 'wb') as f_out:
            cctx.copy_stream(f_in, f_out)


        compressed_size = os.path.getsize(compressed_file)

        # cleanup
        os.remove(compressed_file)

    return compressed_size



def test_compression(algorithm):
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

    compress_func = {'bz2':compress_bz2, 'gzip':compress_gzip}[algorithm]

    with Pool(os.cpu_count() - 1) as pool:
        compressed_sizes = pool.map(compress_func, test_dat_files)

    t_end = time.time()
    t_elapsed = t_end - t_start

    uncompressed_sizes = np.array(uncompressed_sizes)
    compressed_sizes = np.array(compressed_sizes)
    compression_ratio = uncompressed_sizes / compressed_sizes

    # Return the compression ratios and time taken
    return (uncompressed_sizes, compressed_sizes, compression_ratios, t_elapsed)


def summarize_compression(uncompressed_sizes, compressed_sizes,
                          compression_ratios, t_elapsed):
    """
    Print a summary of the compression

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

