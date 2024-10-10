import copy
import glob
import multiprocessing
import os
import resource
import time
from collections import defaultdict
from multiprocessing import Semaphore
from concurrent import futures
from contextlib import redirect_stdout
from functools import wraps
from io import StringIO
try:
    from tqdm import tqdm
except:
    def tqdm(**kwargs):
        print("tqdm not installed;  progress bar disabled")
        return no_tqdm()

# use for missing tqdm or verbose run
class no_tqdm():
    def __init__(self, *args, **kwargs):
        pass
    def update(self, *args, **kwargs):
        pass
    def close(self, *args, **kwargs):
        pass

# proxy for submitting tasks
def submit_proxy(cancel_semaphore, semaphore, function, *args, **kwargs):
    # use blocking and timeout to avoid race for checking for cancel
    if cancel_semaphore.acquire(blocking=True, timeout=1):
        # immediately release
        cancel_semaphore.release()
    else:
        # signal to cancel, do not start this job
        raise futures.CancelledError()
    # acquire the semaphore, blocks if occupied
    semaphore.acquire()
    # run the task
    return function(*args, **kwargs)


class batchjob_config:
    __instance = None
    __d = {}

    def __init__(self, *args, **kwargs) -> None:
        pass

    @classmethod
    def getInstance(cls):
        if batchjob_config.__instance is None:
            batchjob_config.__instance = batchjob_config()
        return batchjob_config.__instance

    def get(self, key, default=None):
        try:
            v = self.__d.get(key, default)
        except:
            print(f'key not found k={key}')
            v = None
        return v

    def set(self, d: dict):
        for k in d.keys():
            self.__d[k] = d[k]


class batchjob:
    def __init__(self, *args, **kwargs) -> None:
        self._results = None
        self._cancel_callback = None
        self._over_commit = kwargs.get('over_commit', False)
        self._batchjob_config = batchjob_config.getInstance()
        # copy kwargs to batchjob_config instance
        self._batchjob_config.set(kwargs)

    def _init_jobs(self, batches: list, param: dict) -> tuple[list, dict]:
        # copy parameters to batchjob_config instance
        self._batchjob_config.set(param)
        # TODO add init function
        return batches, param


    def _process_file_batch(self, fn, batches: list, param: dict, max_workers: int = 1):
        sconfig = self.get_slurm_config()
        if sconfig.get('SLURM_CPUS_PER_TASK') != None:
            cpus_per_task = int(sconfig.get('SLURM_CPUS_PER_TASK'))
            if cpus_per_task < max_workers:
                print('WARNING: max_workers={} > SLURM_CPUS_PER_TASK={}'.format(
                    max_workers,
                    cpus_per_task))
                if self._over_commit:
                    print('WARNING: over commiting')
                else:
                    print('lowering max_workers to SLURM_CPUS_PER_TASK')
                    max_workers = cpus_per_task
        else:
            cpus_per_task = multiprocessing.cpu_count()
            if cpus_per_task < max_workers:
                print('WARNING: max_workers={} > CPU_COUNT={}'.format(
                    max_workers,
                    cpus_per_task))
                if self._over_commit:
                    print('WARNING: over commiting')
                else:
                    print('lowering max_workers to CPU_COUNT')
                    max_workers = cpus_per_task


        if param.get('verbose') == True:
            # actually + futures.process.EXTRA_QUEUED_CALLS
            print("process batches using max_workers:", max_workers)

        # from concurrent.futures.process import EXTRA_QUEUED_CALLS
        # max_workers = max(1, max_workers - EXTRA_QUEUED_CALLS)

        # default context, method='fork'
        mp = multiprocessing.get_context()

        # available is method='spawn' method='forkserver'
        #mp = multiprocessing.get_context(method='spawn')
        # creating shared dict and lock object
        m = mp.Manager()
        semaphore = m.Semaphore(max_workers)
        cancel_semaphore = m.Semaphore(1)

        # futures.ThreadPoolExecutor also possible here
        with futures.ProcessPoolExecutor(max_workers=max_workers, mp_context=mp) as executor:
            d_shared = m.dict()
            self.param = param
            self.param['d_shared'] = d_shared
            lock = m.Lock()

            # call init
            batches, param = self._init_jobs(batches, param)

            # define hard cancel before starting jobs, otherwise might deadlock
            def cancel_callback_hard(gracefully=False):
                print("cancel all jobs immediately")
                for p in mp.active_children():
                    p.kill()

            self._cancel_callback = cancel_callback_hard

            # callback for completed tasks
            def task_complete_callback(f):
                # release the semaphore only if we did not receive a cancel
                if not f.cancelled() and self._cancel_callback is not None:
                    semaphore.release()


            jobs = []
            self._results = [None for i in range(len(batches))]
            for bid, batch in enumerate(batches):
                if isinstance(batch, tuple):
                    infile, outfile = batch
                else:
                    infile = batch
                    outfile = None
                p = copy.deepcopy(param)
                p['batch_id'] = bid
                p['d_shared'] = d_shared
                #f = executor.submit(fn, infile, outfile, p, lock)
                #f.add_done_callback()

                # use semaphore to better control workers
                f =  executor.submit(submit_proxy, cancel_semaphore, semaphore, fn, infile, outfile, p, lock)
                f.add_done_callback(task_complete_callback)

                jobs.append(f)

            # register cancel callback with graceful shutdown
            def cancel_callback(gracefully=False):
                if gracefully:
                    print("cancel jobs; wait for running batches")
                    jobs_to_cancel = [f.cancel() for f in jobs]
                    print("- job cancelled:", jobs_to_cancel.count(True))
                    jobs_running = [f.running() for f in jobs].count(True)
                    print("- job running/queued:  ", jobs_running)
                    jobs_completed = jobs_to_cancel.count(False) - jobs_running
                    print("- job completed:  ", jobs_completed)
                    # aquire and never release
                    cancel_semaphore.acquire()
                else:
                    cancel_callback_hard()

            self._cancel_callback = cancel_callback
            if param.get('verbose') == False:
                # use a progress bar
                pbar_success = tqdm(total=len(jobs))
            else:
                pbar_success = no_tqdm()

            for i, f in enumerate(futures.as_completed(jobs)):
                if f.cancelled():
                    print('cancelled processing batch: {0}/{1}'.format(
                        i, len(jobs)))
                elif isinstance(f.exception(), futures.CancelledError):
                    print('cancelled processing batch: {0}/{1}'.format(
                        i, len(jobs)))
                elif f.exception() == None:
                    if isinstance(batches[i], tuple):
                        infile, outfile = batches[i]
                    else:
                        infile = batches[i]
                        outfile = None
                    if param.get('verbose') == True:
                        print('success processing batch: {0}/{1}: {2}'.format(
                            i, len(jobs),
                            '\n'+batchjob_helper.format_batch(infile, outfile)))
                    else:
                        pbar_success.update(1)

                    r = f.result()
                    self._results[i] = r
                else:
                    print('failed to process batch: {0}/{1}: {2}'.format(
                        i, len(jobs), f.exception()))

            pbar_success.close()
            # remove cancel_callback
            self._cancel_callback = None


    def cancel(self, gracefully=False):
        if self._cancel_callback is not None:
            self._cancel_callback(gracefully)
        # only call cancel once
        self._cancel_callback = None


    def process_files(self, fn, in_files: list, out_files: list, param: dict, max_workers: int = 1, group_batches=None):
        if group_batches == None:
            # from single files
            if out_files is None:
                batches = in_files
            else:
                batches = list(zip(in_files, out_files))
        else:
            batches = group_batches(in_files, out_files, param)

        self._process_file_batch(fn=fn, batches=batches,
                            param=param, max_workers=max_workers)


    def print_result(self):
        for r in self._results:
            print(r)


    def get_result(self):
        return self._results


    def process_result(self, fn):
        return fn(self._results, self.param)

    def print_rusage(self):
        # peak memory usage (kilobytes on Linux)
        inMb = 1.0e-3
        print('RUSAGE_SELF:     {0:.2f} Mb'.format(resource.getrusage(
            resource.RUSAGE_SELF).ru_maxrss * inMb))
        print('RUSAGE_CHILDREN: {0:.2f} Mb'.format(resource.getrusage(
            resource.RUSAGE_CHILDREN).ru_maxrss * inMb))

    def get_slurm_config(self):
        # slurm environment variables
        sconfig = {}
        for k in os.environ:
            if k.find('SLURM') > -1:
                sconfig[k] = os.environ[k]
        return sconfig


    ''' decorators'''
    @staticmethod
    def suppress_output(func):
        @wraps(func)
        #def wrapper(*args, **kwargs):
        def wrapper(infile, outfile, p, lock):
            # print out in the end if failed
            try:
                config = batchjob_config.getInstance()
                __verbose = config.get("verbose")
            except Exception as e:
                print(f'failed to read config: e={e}')
                raise e

            if __verbose is not None and __verbose:
                print("VERBOSE: suppress_output disabled")
                return func(infile, outfile, p, lock)

            #print('start wrapper')
            try:
                with redirect_stdout(StringIO()) as buf:
                    #result = func(*args, **kwargs)
                    result = func(infile, outfile, p, lock)
            except Exception as e:
                print('failed processing BID={0}:'.format(p['batch_id']))
                print(buf.getvalue())
                raise e

            #print('end wrapper')
            return result
        return wrapper

    @staticmethod
    def suppress_all(func):
        @wraps(func)
        #def wrapper(*args, **kwargs):
        def wrapper(infile, outfile, p, lock):
            # no output
            with redirect_stdout(StringIO()) as buf:
                #result = func(*args, **kwargs)
                result = func(infile, outfile, p, lock)

            return result
        return wrapper

    @staticmethod
    def buffer_output(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # print out in the end
            print('start wrapper2')
            out_buf = ''
            result = None
            try:
                with redirect_stdout(StringIO()) as buf:
                    result = func(*args, **kwargs)
            except Exception as e:
                print(buf.getvalue())
                raise e
            finally:
                out_buf += buf.getvalue()

            print('end wrapper2')
            return result, out_buf
        return wrapper

    @staticmethod
    def timethis(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            print(func.__name__, end-start)
            return result
        return wrapper


class PrintWrapper(StringIO):
    def __call__(self, *args, **kwargs):
        import builtins

        # Pass the object instance (self) as the file
        return builtins.print(*args, file=self, **kwargs)

    def print(self):
        import builtins

        # Pass the object instance (self) as the file
        return builtins.print(self.getvalue())


class batchjob_helper:
    @staticmethod
    def get_filenames(data_folder: str, pattern: str, out_folder: str, extension: str, fstub: str, subpath: str, out_extension: str = None):
        in_files = sorted(
            glob.glob(os.path.join(data_folder, pattern), recursive=True))
        # postprocessed
        if out_extension == None:
            out_extension = extension

        if data_folder.endswith('/'):
            data_folder = data_folder[:-1]
        if out_folder.endswith('/'):
            out_folder = out_folder[:-1]

        out_files = [os.path.join(out_folder, s.replace(
            data_folder, out_folder).replace(extension, fstub + out_extension)) for s in in_files]
        out_files = [os.path.join(os.path.split(s)[0], subpath,
                                os.path.split(s)[1]) for s in out_files]
        return in_files, out_files

    @staticmethod
    def print_first(in_files, out_files):
        print(next(zip(in_files, out_files)))

    @staticmethod
    def print_batch(batch_in, batch_out):
        print(batchjob_helper.format_batch(batch_in, batch_out))

    @staticmethod
    def format_batch(batch_in, batch_out):
        if not (isinstance(batch_in, tuple) or isinstance(batch_in, list)):
            # single item
            batch_in = [batch_in]
        if not (isinstance(batch_out, tuple) or isinstance(batch_out, list)):
            # single item
            batch_out = [batch_out]

        return 'batch_in:\n{}\nbatch_out:\n{}'.format(
            '\n'.join([ ' - '+ str(s) for s in batch_in])
            if batch_in is not None else "None",
            '\n'.join([ ' - '+ str(s) for s in batch_out])
            if batch_out is not None else "None"
            )

    @staticmethod
    def debug_process_file_batch(in_files, out_files, param, lock):
        with lock:
            print(param['batch_id'])

    @staticmethod
    def group_by_folder(in_files, out_files):
        tgi = [os.path.split(p) for p in in_files]
        gi = defaultdict(list)
        for k, v in tgi:
            gi[k].append(v)

        tgo = [os.path.split(p) for p in out_files]
        go = defaultdict(list)
        for k, v in tgo:
            go[k].append(v)

        return gi, go

    @staticmethod
    def get_batch_per_folder(in_files, out_files):
        gi, go = batchjob_helper.group_by_folder(in_files, out_files)
        assert(len(gi) == len(go))
        for i, batch in enumerate(zip(gi, go)):
            infolder, outfolder = batch
            infiles_batch = [os.path.join(infolder, f) for f in gi.get(infolder)]
            outfiles_batch = [os.path.join(outfolder, f)
                            for f in go.get(outfolder)]

            yield i, infiles_batch, outfiles_batch

    @staticmethod
    def str2bool(val: str) -> bool:
        assert(type(val) == str)
        return val.lower() in ("yes", "true", "t", "1")

    @staticmethod
    def as_bool(val) -> bool:
        if type(val) == bool:
            return val
        elif type(val) == str:
            return batchjob_helper.str2bool(val)
        else:
            raise NotImplementedError(f'no conversion from type: {type(val)}')
