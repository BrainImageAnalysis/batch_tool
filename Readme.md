# batch tool
```
usage: pybatch.py [-h] [-p [PARAMETER]] [-v] [-r] -s SCRIPT [-m [MAX_WORKERS]]
                  [-n] [-x [SYS_PATH]] [--no-shadow] -i INFILES [INFILES ...]

batch tool
--------------------------------
example:
    pybatch.py --script script_file.py --parameter thres=0.75 --infiles **/img*.nii.gz

options:
  -h, --help            show this help message and exit
  -p [PARAMETER], --parameter [PARAMETER]
                        parameters
  -j [PARAMETER_JSON], --parameter-json [PARAMETER_JSON]
                        parameters in json file
  -v, --verbose         verbose
  -r, --print_results   print results for each batch
  -s SCRIPT, --script SCRIPT
                        script file
  -m [MAX_WORKERS], --max_workers [MAX_WORKERS]
  -n, --dry-run         print first batch item and parameters then exit
  -x [SYS_PATH], --sys-path [SYS_PATH]
                        extra path
  --no-shadow           do not create a shadow copy
  -g, --generate-filenames
                        generate filenames using function given as INFILES
  -i INFILES [INFILES ...], --infiles INFILES [INFILES ...]
                        file names

```

## run script

at least ```process_file``` needs to be defined
```python
from batchtool import batchjob, batchjob_helper  # type: ignore

# use annotation to suppress output of successful batches
@batchjob.suppress_output
def process_file(in_file, out_file, param, lock):
    pass
```

optional ```process_result``` and ```group_batches```

```python
def process_file(in_files, out_files, param, lock):
    res = do_something()
    return res


# do something with results returned by batches -> runs after loop
def process_result(results: list, param: dict):
    return do_something(results)

# group batches and return new batches -> runs before loop
def group_batches(infiles, outfiles, parameters):
    return do_something(infiles, outfiles, parameters)

```
optional ```--generate_filenames``` can be used to generate filenames
using the function given as parameter ```--infiles fn_name```

here cmd line is: ```--generate_filenames --infiles generate_filenames_fn```

```python
# example 1: generate_filename with parameters
def generate_filenames_fn(parameters):
    in_files, out_files = do_something(parameters)
    return in_files, out_files

# example 2: generate_filename with internal helper function
def generate_filenames_fn(parameters):
    in_files, out_files = batchjob_helper.get_filenames(
        data_folder=os.path.expandvars(parameters['data_folder']),
        pattern=parameters['pattern'],
        out_folder=os.path.expandvars(parameters['out_folder']),
        extension=parameters['extension'],
        fstub=parameters['fstub'],
        subpath=parameters['subpath'],
        out_extension=parameters['out_extension'], #if None = parameters['extension']
        )
    return in_files, out_files

```

### parameters

use ```--parameter``` to pass parameters from command line

```bash
-p int_value=5 -p list_value="[1,2,3]" ...
```
use ```--parameters-json``` to pass parameters from json file(s)
```json
{
    "int_value": 5,
    "list_value": [1,2,3]
}
```

Can be combined and multiple files and command line arguments can be used.
json files are parsed before command line parameters.
If the same parameter is defined multiple times, the last one is used.
command line parameters are passed as strings.

### cmd line
you can define cmd line arguments in a text file (see samples)
```bash
pybatch.py @samples/cmdline.txt
```
### extra libs
use ```--sys-path``` to define paths for your imports

### add to path
```bash
export PATH=${PATH}:/FULL_PATH/batch_tool/bin
```

## examples

example scripts are in the samples folder
```bash
pybatch.py --script samples/test_script.py --infiles b1/1 b1/2 b2/3 b3/4 b4/5 b4/6 b5/7 b5/8 b5/9 b5/10  --verbose
```

use dry-run to print paramters and first batch item
```bash
pybatch.py --script samples/test_script.py --infiles b1/1 b1/2 b2/3 b3/4 b4/5 b4/6 b5/7 b5/8 b5/9 b5/10 --parameter thres=0.75 -p result=result.nii.gz --dry-run
```
Output:
```
md5 2cdcb621189369bf6e0fc1a5229c8ac2
file already exists, and is sane:  /tmp/2cdcb621189369bf6e0fc1a5229c8ac2.py
loading 2cdcb621189369bf6e0fc1a5229c8ac2.py from /tmp
script dry run:
 args: {'parameter': ['thres=0.75', 'result=result.nii.gz'], 'parameter_json': None, 'verbose': False, 'print_results': False, 'script': ['samples/test_script.py'], 'max_workers': 32, 'dry_run': True, 'sys_path': None, 'no_shadow': False, 'generate_filenames': False, 'infiles': ['b1/1', 'b1/2', 'b2/3', 'b3/4', 'b4/5', 'b4/6', 'b5/7', 'b5/8', 'b5/9', 'b5/10']}
 parameters:
   thres: 0.75
   result: result.nii.gz
   verbose: False
 first batch item:
   batch_in:
    - b1/1
    - b1/2
   batch_out:
    - b1/1
    - b1/2

number of batches: 5
files per batch: [2, 1, 1, 2, 4]
```

pybatch generates a shadow copy of the script before running it.
Use ```--no-shadow``` to disable
```bash
pybatch.py --no-shadow --script samples/test_script.py --infiles b1/1 b1/2 b2/3 b3/4 b4/5 b4/6 b5/7 b5/8 b5/9 b5/10 --parameter thres=0.75 -p result=result.nii.gz --dry-run
```
Output:
```
loading test_script.py from /home/matthias/python/batch_tool/samples
script dry run:
 args: {'parameter': ['thres=0.75', 'result=result.nii.gz'], 'parameter_json': None, 'verbose': False, 'print_results': False, 'script': ['samples/test_script.py'], 'max_workers': 32, 'dry_run': True, 'sys_path': None, 'no_shadow': True, 'generate_filenames': False, 'infiles': ['b1/1', 'b1/2', 'b2/3', 'b3/4', 'b4/5', 'b4/6', 'b5/7', 'b5/8', 'b5/9', 'b5/10']}
 parameters:
   thres: 0.75
   result: result.nii.gz
   verbose: False
 first batch item:
   batch_in:
    - b1/1
    - b1/2
   batch_out:
    - b1/1
    - b1/2

number of batches: 5
files per batch: [2, 1, 1, 2, 4]
```

simple example
```bash
pybatch.py --max_workers 4 --script ~/python/batch_tool/samples/test_script2.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose
```

uses a shared dict which can be accessed by each batch
```bash
pybatch.py --max_workers 10 --script ~/python/batch_tool/samples/test_script3.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose
```

count python files and folders which have files (example needs numpy)
```bash
conda run -n pytorch pybatch.py --script ~/python/batch_tool/samples/test_script4.py --infiles ~/python/batch_tool/**/*.py  --verbose
```

it is possible to use multiple processes in a batch process
```bash
pybatch.py --max_workers 10 --script ~/python/batch_tool/samples/test_script5.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose
```

it is possible to use multiple threads in a batch process
```bash
pybatch.py --max_workers 10 --script ~/python/batch_tool/samples/test_script6.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose
```

read from file
```bash
pybatch.py @samples/cmdline.txt --dry-run
```

Generate INFILES count python files and folders which have files (example needs numpy)
```bash
conda run -n pytorch pybatch.py --script ~/python/batch_tool/samples/test_script7.py --infiles ~/python/batch_tool/**/*.py  --verbose
```
## conda

run in a conda env
```bash
conda run -n pytorch pybatch.py --script ~/python/batch_tool/samples/test_script.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose
```

## slurm
use slurm to run scripts

```--max_workers``` and  ```-c, --cpus-per-task``` should make sense
```bash
srun --pty --mem 16G -c 10 -t 240 conda run -n pytorch pybatch.py --max_workers 10 --script ~/python/batch_tool/samples/test_script2.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose
```
```bash
srun --nodelist=rtxa5000-01 --gres=gpu:1 --pty --mem 16G -c 2 -t 240 conda run -n pytorch  pybatch.py --script ~/python/batch_tool/samples/test_script2.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose
```

## jupyter notebooks
batch tool class can also be used in notebooks
see the sample file for usage
```
samples/template_process_files.ipynb
```