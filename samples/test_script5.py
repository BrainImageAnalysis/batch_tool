import os
from time import sleep
from batchtool import batchjob, batchjob_helper  # type: ignore
import multiprocessing


def all_pids(value):
    sleep(1)
    return os.getpid()


# use multiple processes per batch
@batchjob.suppress_output
def process_file(in_file, out_file, param, lock):

    pool_obj = multiprocessing.Pool()
    # get pids from pool
    answer = pool_obj.map(all_pids, range(0, 5))

    # use shared memory
    d_shared: dict = param['d_shared']
    # use lock to access shared memory
    with lock:
        if d_shared.get('cnt') == None:
            d_shared['cnt'] = 1
        else:
            d_shared['cnt'] += 1

    return [os.getpid(), d_shared['cnt'], answer]


def process_result(results: list, param: dict):
    return param['d_shared']['cnt']
