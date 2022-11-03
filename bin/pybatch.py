#!/usr/bin/env python3
from collections import defaultdict
import glob
import importlib
import sys as sys
import argparse
import textwrap
import os
import multiprocessing


def parser_args():
    #parser = argparse.ArgumentParser(prog='PROG', usage='%(prog)s [options]')
    parser = argparse.ArgumentParser(exit_on_error=False,
                                     fromfile_prefix_chars='@',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent('''\
        Please do not mess up this text!
        --------------------------------
            I have indented it
            exactly the way
            I want it
        '''))
    parser.add_argument('-p', '--parameter', action='append',
                        nargs='?', help='parameters')
    parser.add_argument('-v', '--verbose', required=False, action='store_true',
                        help='verbose', default=False)
    parser.add_argument('-i', '--infiles', required=True,
                        nargs='+', help='file names', type=str)
    parser.add_argument('-s', '--script', required=True,
                        nargs=1, help='script file', type=str)
    parser.add_argument('-m', '--max_workers', required=False, nargs='?',
                        default=multiprocessing.cpu_count(), type=int)
    parser.add_argument('-n', '--dry_run', required=False, action='store_true',
                        help='verbose', default=False)
    parser.add_argument('-x', '--sys_path', action='append',
                        nargs='?', help='extra path')
    #parser.print_help()
    #args = parser.parse_args()
    #return args
    return parser


# def test():
#     t = '''
#     --script samples/test_script.py
#     --parameter p1=5
#     --parameter p2=3
#     --verbose
#     #--infiles /disk/matthias/hokto/hokto_data/DATA/**/brain_img.nii.gz
#     # quotes
#     --infiles '/disk/matthias/hokto/hokto_data/DATA/**/brain_img.nii.gz'
#     --infiles "/disk/matthias/hokto/hokto_data/DATA/**/brain_img.nii.gz"
#     # will fail
#     #--infiles /disk/matthias/hokto/hokto_data/DATA/*/brain_img.nii.gz
#     # no glob
#     #--infiles '/disk/matthias/hokto/hokto_data/DATA/brain_img.nii.gz'
#     # fake
#     #--infiles 1 2 3 4 5
#     #--max_workers 1
#     #--dry_run
#     --sys_path /home/matthias/jupyter
#     --sys_path '/home/matthias/python'
#     --sys_path /home/matthias/jupyter/bia
#     '''
#     for line in t.splitlines():
#         print(line)
#         if line.replace(' ', '').startswith('#'):
#             t = t.replace(line,'')
#     return t


def add_to_syspath(path: str):
    for p in sys.path:
        if p == path:
            return
    sys.path.append(path)
    #print(sys.path)


def parameters(flags):
    param = {}
    for p in flags:
        k,v = p.split('=')
        param[k] = v
    return param


def print_parameters(param):
    r = [': '.join([k,str(v)])+'\n' for (k,v) in param.items()]
    print(*r)

def load_script(filename):
    if not os.path.exists(filename):
        raise FileNotFoundError('file not found: "{}"'.format(filename))

    path, mod = os.path.split(os.path.abspath(filename))
    print(path,mod)
    add_to_syspath(path)
    mod = mod.replace('.py', '')

    script = importlib.import_module(mod)
    return script


def load_batchtool(this_file, extra_path):
    #script = importlib.import_module(mod)
    # slurm tools
    add_to_syspath('/disk/soft/bia_software/slurm_tools')
    #
    #add_to_syspath('/home/matthias/jupyter')
    #add_to_syspath('/home/matthias/jupyter/bia')
    #add_to_syspath('/home/matthias/python')
    #print(os.path.join(os.path.dirname(this_file), '../tools'))
    add_to_syspath(os.path.join(os.path.dirname(this_file), '../lib'))
    for p in extra_path:
        add_to_syspath(p.strip('\'').strip('\"'))


def main(flags):
    param = parameters(flags.parameter)
    param['verbose'] = flags.verbose

    script = load_script(*flags.script)
    if not hasattr(script, 'process_file'):
        raise Exception(
            '"process_file(in_file, out_file, param, lock)" not defined in script "{}"'.format(*flags.script))

    in_files = str(flags.infiles[0])
    # in_files, out_files = batchjob_helper.get_filenames(
    #     data_folder, pattern, out_folder, extension, fstub, subpath, out_extension)

    if in_files.find('*') > -1:
        in_files = sorted(
            glob.glob(os.path.join(in_files.strip('\'').strip('\"')), recursive=True))
    out_files = in_files

    if in_files == None or len(in_files) == 0:
        raise Exception("filenames are empty")

    if flags.dry_run:
        print('script dry run:')
        print(' args:', vars(flags))
        print(' parameters:\n  ', '\n   '.join([': '.join([k,str(v)]) for (k,v) in param.items()]))
        print(' first batch item:')
        print(' ', next(zip(in_files, out_files)))
        return 0
    else:
        bj = batchjob()
        group_batches = None
        if hasattr(script, 'group_batches'):
            group_batches = script.group_batches

        bj.process_files(script.process_file, in_files=in_files,
                            out_files=out_files, param=param, max_workers=32, group_batches=group_batches)

        bj.print_result()
        if hasattr(script, 'process_result'):
            r = bj.process_result(fn=script.process_result)
            print('result:', r)
        # r2 = process_result(bj.get_result())
        # print(r1, r2)
        bj.print_rusage()

        return 0


if __name__ == "__main__":

    try:
        parser = parser_args()
        #print(parser.prog)
        try:
            #flags = parser.parse_args(test().split())
            flags = parser.parse_args()
        except Exception as e:
            print(e)
            parser.print_help()
            sys.exit(-1)

        load_batchtool(sys.argv[0], flags.sys_path)
        #from bia.tools.batchtool import batchjob, batchjob_helper
        from batchtool import batchjob, batchjob_helper

        sys.exit(main(flags=flags))
    except Exception as e:
        print('script failed:\n{}'.format('Unknown error' if e is None else e))

    sys.exit(-1)
