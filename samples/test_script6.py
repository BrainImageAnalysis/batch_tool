from concurrent import futures
import os
from time import sleep
from batchtool import batchjob, batchjob_helper  # type: ignore


def all_pids(value):
    sleep(1)
    return os.getpid()


# use multiple threads per batch
@batchjob.suppress_output
def process_file(in_file, out_file, param, lock):
    answer = []
    with futures.ThreadPoolExecutor() as executor:
        # get pids from pool -> should be all the same as only using threads
        for res in executor.map(all_pids, range(0, 5)):
            answer.append(res)

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
