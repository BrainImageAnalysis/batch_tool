from functools import reduce
import os
from random import randint
from batchtool import batchjob, batchjob_helper  # type: ignore
import numpy as np


@batchjob.suppress_output
def process_file(in_files, out_files, param, lock):
    with lock:
        print('process file (PID={0}/BID={1}): {2}'.format(
            os.getpid(), param['batch_id'], in_files))

    return np.array([1, len(in_files)])


# example: caluclates overall sum of files
def process_result(results: list, param: dict):
    return reduce(lambda x, y: x+y, results, np.array([0, 0]))


def group_batches_by_folder(in_files, out_files):
    group_in_folders = [[infiles, outfiles]
                        for i, infiles, outfiles in batchjob_helper.get_batch_per_folder(in_files, out_files)]
    return group_in_folders


# example: group batches by folder
def group_batches(infiles, outfiles):
    return group_batches_by_folder(infiles, outfiles)
