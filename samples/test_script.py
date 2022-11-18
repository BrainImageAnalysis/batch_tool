from functools import reduce
import os
from random import randint
from batchtool import batchjob, batchjob_helper  # type: ignore


@batchjob.suppress_output
def process_file(in_file, out_file, param, lock):
    with lock:
        print('process file (PID={0}/BID={1}): {2}'.format(
            os.getpid(), param['batch_id'], 'lock aquired'))
    print('process file (PID={0}/BID={1}): {2}'.format(
        os.getpid(), param['batch_id'], in_file))

    # img, affine, header = read_in_file(in_file)
    # out_img_post = postprocess(img)
    # write_out_file(out_file, out_img_post, affine)

    # test exceptions
    if randint(0, 1) % 2 == 0:
        raise Exception('test exception raised to test for batch failed')

    return 'process file (PID={0}/BID={1}): {2}'.format(os.getpid(), param['batch_id'], randint(0, 3))


# example: caluclates overall length of string output
def process_result(results: list, param: dict):
    return reduce(lambda x, y: x+len(y) if y != None else x, results, 0)


def group_batches_by_folder(in_files, out_files):
    group_in_folders = [[infiles, outfiles]
                        for i, infiles, outfiles in batchjob_helper.get_batch_per_folder(in_files, out_files)]
    return group_in_folders


# example: group batches by folder
def group_batches(infiles, outfiles, parameters):
    return group_batches_by_folder(infiles, outfiles)
