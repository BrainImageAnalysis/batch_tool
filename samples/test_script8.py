from functools import reduce
import os
import time
from batchtool import batchjob, batchjob_helper  # type: ignore


@batchjob.suppress_output
def process_file(in_file, out_file, param, lock):
    with lock:
        print('process file (PID={0}/BID={1}): {2}'.format(
            os.getpid(), param['batch_id'], 'lock aquired'))
    time.sleep(10)
    return param['batch_id']


# example: caluclates overall sum of batch IDs
def process_result(results: list, param: dict):
    return reduce(lambda x, y: x+(y) if y != None else x, results, 0)
