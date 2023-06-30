#!/bin/bash
SCRIPT_PATH="$(dirname $0)"
PATH="$PATH:${SCRIPT_PATH}/../bin"
OUT=""
if [ "$1" == '-q' ] || [ "$1" == '-quiet' ];then
    # only errors
    OUT=">/dev/null"
fi

CNT=0

eval pybatch.py --script ~/python/batch_tool/samples/test_script.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose ${OUT} || echo "script failed: $((CNT++))"

eval pybatch.py --script ~/python/batch_tool/samples/test_script.py --infiles 1 --parameter thres=0.75 -p result=result.nii.gz --dry-run ${OUT} || echo "script failed: $((CNT++))"

eval pybatch.py --max_workers 4 --script ~/python/batch_tool/samples/test_script2.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose ${OUT} || echo "script failed: $((CNT++))"

eval pybatch.py --max_workers 10 --script ~/python/batch_tool/samples/test_script3.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose ${OUT} || echo "script failed: $((CNT++))"

eval conda run -n pytorch pybatch.py --script ~/python/batch_tool/samples/test_script4.py --infiles ~/python/batch_tool/**/*.py  --verbose ${OUT} || echo "script failed: $((CNT++))"

eval pybatch.py --max_workers 10 --script ~/python/batch_tool/samples/test_script5.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose ${OUT} || echo "script failed: $((CNT++))"

eval pybatch.py --max_workers 10 --script ~/python/batch_tool/samples/test_script6.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose ${OUT} || echo "script failed: $((CNT++))"

pushd "${SCRIPT_PATH}/.." >/dev/null || exit
eval pybatch.py "@${SCRIPT_PATH}/cmdline.txt" --dry-run ${OUT} || echo "script failed: $((CNT++))"
popd  >/dev/null || exit
