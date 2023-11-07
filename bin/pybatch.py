#!/usr/bin/env python3
import hashlib
import argparse
import glob
import importlib

try:
    # use json5 if available to support comments
    import json5 as json
except ModuleNotFoundError:
    import json

import multiprocessing
import os
import sys as sys
import tempfile
import textwrap
import traceback


def parser_args():
    #parser = argparse.ArgumentParser(prog='PROG', usage='%(prog)s [options]')
    parser = argparse.ArgumentParser(exit_on_error=False,
                                     fromfile_prefix_chars='@',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent('''\
        batch tool
        --------------------------------
        example:
            pybatch.py --script script_file.py --parameter thres=0.75 --infiles **/img*.nii.gz
        '''))
    parser.add_argument('-p', '--parameter', action='append',
                        nargs='?', help='parameters')
    parser.add_argument('-j', '--parameter-json', action='append',
                        nargs='?', help='parameters in json file')
    parser.add_argument('-v', '--verbose', required=False, action='store_true',
                        help='verbose', default=False)
    parser.add_argument('-r', '--print_results', required=False, action='store_true',
                        help='print results for each batch', default=False)
    parser.add_argument('-s', '--script', required=True,
                        nargs=1, help='script file', type=str)
    parser.add_argument('-m', '--max_workers', required=False, nargs='?',
                        default=multiprocessing.cpu_count(), type=int)
    parser.add_argument('-n', '--dry-run', required=False, action='store_true',
                        help='print first batch item and parameters then exit',
                        default=False)
    parser.add_argument('-x', '--sys-path', action='append',
                        nargs='?', help='extra path')
    parser.add_argument('--no-shadow',  required=False, action='store_true',
                        help='do not create a shadow copy', default=False)
    parser.add_argument('-g', '--generate-filenames',  required=False, action='store_true',
                        help='generate filenames using function given as INFILES', default=False)
    parser.add_argument('-i', '--infiles', required=True,
                        nargs='+', help='file names', type=str)

    def convert_arg_line_to_args(arg_line: str):
        # ignore commented lines
        if arg_line.strip().startswith('#'):
            return
        # same syntax as cmdline
        for arg in arg_line.split():
            if not arg.strip():
                continue
            yield arg
    parser.convert_arg_line_to_args = convert_arg_line_to_args

    return parser


def add_to_syspath(path: str):
    for p in sys.path:
        if p == path:
            return
    sys.path.append(path)


def parameters(flags,param={}):
    if flags == None:
        return param

    for p in flags:
        k, v = p.split('=')
        # strip quotes from parameters
        param[k] = v.strip('\'').strip('\"')
    return param


def json_read(filename):
    # do not catch exceptions
    if (os.path.isfile(filename)):
        with open(filename) as data_file:
            #data = json.loads(re.sub("^\s*//.*","",data_file.read(),flags=re.MULTILINE))
            data = json.load(data_file)
    else:
        data={}
    return data


def parameters_json(flags,param={}):
    if flags == None:
        return param

    for filename in flags:
        with open(filename) as data_file:
            data = json.load(data_file)
        for k, v in data.items():
            print(k,v)
            # copy parameters
            param[k] = v
    return param


def print_parameters(param):
    r = [': '.join([k, str(v)])+'\n' for (k, v) in param.items()]
    print(*r)


def load_script(filename):
    filename = os.path.expandvars(filename)
    if not os.path.exists(filename):
        raise FileNotFoundError('file not found: "{}"'.format(filename))

    path, mod = os.path.split(os.path.abspath(filename))
    print('loading {} from {}'.format(mod, path))
    add_to_syspath(path)
    mod = mod.replace('.py', '')

    script = importlib.import_module(mod)
    return script


def load_batchtool(this_file, extra_path):
    # slurm tools
    add_to_syspath('/disk/soft/bia_software/slurm_tools')
    # add self
    add_to_syspath(os.path.join(os.path.dirname(this_file), '../lib'))
    # add extra paths
    if extra_path != None:
        for p in extra_path:
            add_to_syspath(p.strip('\'').strip('\"'))


def expand_filenames(in_files):
    in_files_glob = []
    for file in in_files:
        if file.find('*') > -1:
            expand_in_files = sorted(
                glob.glob(os.path.join(file.strip('\'').strip('\"')), recursive=True))
            in_files_glob.extend(expand_in_files)
        else:
            in_files_glob.append(file)
    return in_files_glob


def unroll_filename(filename, no_shadow):
    filename = os.path.expandvars(filename)
    if not os.path.exists(filename):
        raise FileNotFoundError('file not found: "{}"'.format(filename))
    elif no_shadow:
        return filename

    with open(filename, 'r') as src:
        tmp = src.read()
        md5 = hashlib.md5(tmp.encode('utf-8')).hexdigest()
        print('md5', md5)
        unique_name = os.path.join(
            tempfile.gettempdir(),
            md5 + '.py'
            )

        if os.path.exists(unique_name):
            with open(unique_name, 'r') as existing_src:
                md5_check = hashlib.md5(
                    existing_src.read().encode('utf-8')).hexdigest()
                if md5 == md5_check:
                    print('file already exists, and is sane: ', unique_name)
                    return unique_name
                else:
                    print(
                        'file already exists but is corrupt;',
                        'will remove it: ', unique_name
                    )
                    # remove file to prevent loading wrong script
                    os.remove(unique_name)

        with open(unique_name, 'w') as f:
            f.write(tmp)
        print('shadow copy created: ', unique_name)

    return unique_name


def main(flags):
    param = parameters_json(flags.parameter_json)
    param = parameters(flags.parameter, param)
    param['verbose'] = flags.verbose

    script_filename = unroll_filename(*flags.script, flags.no_shadow)
    script = load_script(script_filename)

    if not hasattr(script, 'process_file'):
        raise Exception(
            '"process_file(in_file, out_file, param, lock)" not defined in script "{}"'.format(script_filename))
    if flags.generate_filenames:
        attr_name = flags.infiles[0]
        if not hasattr(script, attr_name):
            raise Exception(
                '"{}" not defined in script "{}"'.format(attr_name, script_filename))
        generate_filenames = getattr(script, attr_name)
        in_files, out_files = generate_filenames(param)
    else:
        in_files = expand_filenames(flags.infiles)
        out_files = in_files

    if in_files == None or len(in_files) == 0:
        raise Exception("filenames are empty")

    group_batches = None
    if hasattr(script, 'group_batches'):
        group_batches = script.group_batches

    if flags.dry_run:
        print('script dry run:')
        print(' args:', vars(flags))
        print(' parameters:\n  ', '\n   '.join(
            [': '.join([k, str(v)]) for (k, v) in param.items()]))
        print(' first batch item:')
        if group_batches == None:
            # from single files
            num_batches = len(in_files)
            batch_in, batch_out = next(zip(in_files, out_files))
            files_per_batch = [1 for _ in zip(in_files, out_files)]
        else:
            batches = group_batches(in_files, out_files, param)
            num_batches = len(batches)
            batch_in, batch_out = next(iter(batches))
            files_per_batch = [len(f) for f,_ in iter(batches)]

        print('  ', '   '.join([
            line+'\n' for line in
            batchjob_helper.format_batch(batch_in, batch_out).splitlines()
            ]))

        print('number of batches:', num_batches)
        print('files per batch:', files_per_batch)
        return 0
    else:
        bj = batchjob()

        max_workers = flags.max_workers
        bj.process_files(script.process_file, in_files=in_files,
                        out_files=out_files, param=param,
                        max_workers=max_workers, group_batches=group_batches)

        if flags.print_results:
            bj.print_result()

        if hasattr(script, 'process_result'):
            r = bj.process_result(fn=script.process_result)
            print('result:', r)

        bj.print_rusage()

        # close file and delete
        if flags.no_shadow:
            if flags.verbose:
                print('no shadow copy created, not removing file')
        else:
            try:
                os.remove(script_filename)
            except Exception as e:
                print('could not remove file:', e)

        return 0


if __name__ == "__main__":

    try:
        parser = parser_args()
        try:
            flags = parser.parse_args()
        except Exception as e:
            print(e)
            parser.print_help()
            sys.exit(-1)

        load_batchtool(sys.argv[0], flags.sys_path)
        # import the batchtool before call main
        from batchtool import batchjob, batchjob_helper  # type: ignore

        sys.exit(main(flags=flags))
    except Exception as e:
        print('script failed:\n{}\n{}'.format(
            flags.script[0],
            'Unknown error' if e is None else 'Exception: ' + str(e)))
        traceback.print_exc()

    sys.exit(-1)
