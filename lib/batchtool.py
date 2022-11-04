import copy
import glob
import multiprocessing
import os
import resource
import time
from collections import defaultdict
from concurrent import futures
from contextlib import redirect_stdout
from functools import wraps
from io import StringIO


class batchjob:
    def __init__(self) -> None:
        #self.parser = argparse.ArgumentParser()
        self.results = None
        pass

    # def _init_pool(self, the_data):
    #     global d_shared
    #     d_shared = the_data

    def _process_file_batch(self, fn, batches: list, param: dict, max_workers: int = 1):
        # TODO check ThreadPoolExecutor
        with futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        #with futures.ProcessPoolExecutor(max_workers=max_workers, initializer=self._init_pool, initargs=(param,)) as executor:
            # creating a lock object
            m = multiprocessing.Manager()
            d_shared = m.dict()
            self.param = param
            self.param['d_shared'] = d_shared
            lock = m.Lock()
            res = []
            self.results = [None for i in range(len(batches))]
            for bid, batch in enumerate(batches):
                infile, outfile = batch
                p = copy.deepcopy(param)
                p['batch_id'] = bid
                p['d_shared'] = d_shared
                f = executor.submit(fn, infile, outfile, p, lock)
                #f.add_done_callback()
                res.append(f)


            for i, f in enumerate(futures.as_completed(res)):
                if f.exception() == None:
                    print('success processing batch: {0}/{1}: {2}'.format(
                        i, len(res), batches[i] if param.get('verbose') == True else '(set verbose to log files)'))
                    r = f.result()
                    self.results[i] = r
                    # print('buf', buf[i])
                    #print('res', f.result())
                else:
                    print('failed to process batch: {0}/{1}: {2}'.format(
                        i, len(res), f.exception()))


    def process_files(self, fn, in_files: list, out_files: list, param: dict, max_workers: int = 1, group_batches=None):
        if group_batches == None:
            # from single files
            batches = list(zip(in_files, out_files))
        else:
            batches = group_batches(in_files, out_files)

        self._process_file_batch(fn=fn, batches=batches,
                            param=param, max_workers=max_workers)


    def print_result(self):
        for r in self.results:
            print(r)


    def get_result(self):
        return self.results


    def process_result(self, fn):
        return fn(self.results, self.param)

    def print_rusage(self):
        # peak memory usage (kilobytes on Linux)
        inMb = 1.0e-3
        print('RUSAGE_SELF:     {0:.2f} Mb'.format(resource.getrusage(
            resource.RUSAGE_SELF).ru_maxrss * inMb))
        print('RUSAGE_CHILDREN: {0:.2f} Mb'.format(resource.getrusage(
            resource.RUSAGE_CHILDREN).ru_maxrss * inMb))


    ''' decorators'''
    @staticmethod
    def suppress_output(func):
        @wraps(func)
        #def wrapper(*args, **kwargs):
        def wrapper(infile, outfile, p, lock):
            # print out in the end if failed
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
    def debug_process_file_batch(in_files, out_files, param, lock):
        with lock:
            print(param['batch_id'])

    @staticmethod
    def group_by_folder(in_files, out_files):
        tgi = [os.path.split(p) for p in in_files]
        tgo = [os.path.split(p) for p in out_files]

        gi = defaultdict(list)
        for k, v in tgi:
            gi[k].append(v)

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
