# batch tool
```
usage: pybatch.py [-h] [-p [PARAMETER]] [-v] -i INFILES [INFILES ...] -s SCRIPT [-m [MAX_WORKERS]] [-n] [-x [SYS_PATH]]

batch tool
--------------------------------
example:
    pybatch.py --script script_file.py --parameter thres=0.75 --infiles **/img*.nii.gz

options:
  -h, --help            show this help message and exit
  -p [PARAMETER], --parameter [PARAMETER]
                        parameters
  -v, --verbose         verbose
  -i INFILES [INFILES ...], --infiles INFILES [INFILES ...]
                        file names
  -s SCRIPT, --script SCRIPT
                        script file
  -m [MAX_WORKERS], --max_workers [MAX_WORKERS]
  -n, --dry-run         print first batch item and parameters then exit
  -x [SYS_PATH], --sys-path [SYS_PATH]
                        extra path

```

## run script

at least ```process_file``` needs to be defined
```python
from batchtool import batchjob, batchjob_helper  # type: ignore

# use annotation to suppress output of succesful batches
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
def group_batches(infiles, outfiles):
    return do_something(infiles, outfiles)

```
### extra libs
use ```--sys-path``` to define paths for your imports

### add to path
```bash
export PATH=${PATH}:/FULL_PATH/batch_tool/bin
```

## examples
complete example
```bash
pybatch.py --script ~/python/batch_tool/samples/test_script.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose
```
use dry-run to print paramters and first batch item
```bash
pybatch.py --script ~/python/batch_tool/samples/test_script.py --infiles 1 --parameter thres=0.75 -p result=result.nii.gz --dry-run
```
```
/home/matthias/python/batch_tool/samples test_script.py
script dry run:
 args: {'parameter': ['thres=0.75', 'result=result.nii.gz'], 'verbose': False, 'infiles': ['1'], 'script': ['/home/matthias/python/batch_tool/samples/test_script.py'], 'max_workers': 32, 'dry_run': True, 'sys_path': None}
 parameters:
   thres: 0.75
   result: result.nii.gz
   verbose: False
 first batch item:
  ('1', '1')
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