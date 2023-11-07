#!/bin/bash
SCRIPT_PATH="$(dirname $0)"
PATH="$PATH:${SCRIPT_PATH}/../bin"
OUT=""
if [ "$1" == '-q' ] || [ "$1" == '-quiet' ];then
    # only errors
    OUT=">/dev/null"
fi

CNT=0
SCRIPT=0

((SCRIPT++))
eval pybatch.py --script ~/python/batch_tool/samples/test_script.py --infiles b1/1 b1/2 b2/3 b3/4 b4/5 b4/6 b5/7 b5/8 b5/9 b5/10  --verbose ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
eval pybatch.py --script ~/python/batch_tool/samples/test_script.py --infiles 1 --parameter thres=0.75 -p result=result.nii.gz --dry-run ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
eval pybatch.py --no-shadow --script ~/python/batch_tool/samples/test_script.py --infiles 1 --parameter thres=0.75 -p result=result.nii.gz --dry-run ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
eval pybatch.py --max_workers 4 --script ~/python/batch_tool/samples/test_script2.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
eval pybatch.py --max_workers 10 --script ~/python/batch_tool/samples/test_script3.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
eval conda run -n pytorch2 pybatch.py --script ~/python/batch_tool/samples/test_script4.py --infiles ~/python/batch_tool/**/*.py  --verbose ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
eval pybatch.py --max_workers 10 --script ~/python/batch_tool/samples/test_script5.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
eval pybatch.py --max_workers 10 --script ~/python/batch_tool/samples/test_script6.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

pushd "${SCRIPT_PATH}/.." >/dev/null || exit

((SCRIPT++))
eval pybatch.py "@${SCRIPT_PATH}/cmdline.txt" --dry-run ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
eval conda run -n pytorch2 pybatch.py "@${SCRIPT_PATH}/cmdline7.txt" ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
eval conda run -n pytorch2 pybatch.py "@${SCRIPT_PATH}/cmdline7-2.txt" ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

#############################
echo ""
echo "----------------------"
echo "scripts failed / run: $CNT / $SCRIPT"

popd  >/dev/null || exit
