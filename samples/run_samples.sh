#!/bin/bash
SCRIPT_PATH="$(dirname $0)"
PATH="$PATH:${SCRIPT_PATH}/../bin"
SAMPLE_PATH=${SCRIPT_PATH}
BATCHTOOL_PATH=${SCRIPT_PATH}
OUT=""
if [ "$1" == '-q' ] || [ "$1" == '-quiet' ];then
    # only errors
    OUT=">/dev/null"
fi

CNT=0
SCRIPT=0

((SCRIPT++))
echo pybatch.py --script "${SAMPLE_PATH}"/test_script.py --infiles b1/1 b1/2 b2/3 b3/4 b4/5 b4/6 b5/7 b5/8 b5/9 b5/10  --verbose
eval pybatch.py --script "${SAMPLE_PATH}"/test_script.py --infiles b1/1 b1/2 b2/3 b3/4 b4/5 b4/6 b5/7 b5/8 b5/9 b5/10  --verbose ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
echo pybatch.py --script "${SAMPLE_PATH}"/test_script.py --infiles b1/1 b1/2 b2/3 b3/4 b4/5 b4/6 b5/7 b5/8 b5/9 b5/10  --verbose --dry-run
eval pybatch.py --script "${SAMPLE_PATH}"/test_script.py --infiles b1/1 b1/2 b2/3 b3/4 b4/5 b4/6 b5/7 b5/8 b5/9 b5/10  --verbose --dry-run ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
echo pybatch.py --script "${SAMPLE_PATH}"/test_script.py --infiles 1 --parameter thres=0.75 -p result=result.nii.gz --dry-run
eval pybatch.py --script "${SAMPLE_PATH}"/test_script.py --infiles 1 --parameter thres=0.75 -p result=result.nii.gz --dry-run ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
echo pybatch.py --no-shadow --script "${SAMPLE_PATH}"/test_script.py --infiles 1 --parameter thres=0.75 -p result=result.nii.gz
eval pybatch.py --no-shadow --script "${SAMPLE_PATH}"/test_script.py --infiles 1 --parameter thres=0.75 -p result=result.nii.gz ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
echo pybatch.py --max_workers 4 --script "${SAMPLE_PATH}"/test_script2.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose
eval pybatch.py --max_workers 4 --script "${SAMPLE_PATH}"/test_script2.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
echo pybatch.py --max_workers 10 --script "${SAMPLE_PATH}"/test_script3.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose
eval pybatch.py --max_workers 10 --script "${SAMPLE_PATH}"/test_script3.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
echo conda run -n pytorch2 pybatch.py --script "${SAMPLE_PATH}"/test_script4.py --infiles "${BATCHTOOL_PATH}"/**/*.py  --verbose
eval conda run -n pytorch2 pybatch.py --script "${SAMPLE_PATH}"/test_script4.py --infiles "${BATCHTOOL_PATH}"/**/*.py  --verbose ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
echo pybatch.py --max_workers 10 --script "${SAMPLE_PATH}"/test_script5.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose
eval pybatch.py --max_workers 10 --script "${SAMPLE_PATH}"/test_script5.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
echo pybatch.py --max_workers 10 --script "${SAMPLE_PATH}"/test_script6.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose
eval pybatch.py --max_workers 10 --script "${SAMPLE_PATH}"/test_script6.py --infiles 1 2 3 4 5 6 7 8 9 10  --verbose ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
echo pybatch.py --max_workers 10 --script "${SAMPLE_PATH}"/test_script6.py --infiles 1 2 3 4 5 6 7 8 9 10
eval pybatch.py --max_workers 10 --script "${SAMPLE_PATH}"/test_script6.py --infiles 1 2 3 4 5 6 7 8 9 10 ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

pushd "${SCRIPT_PATH}/.." >/dev/null || exit

((SCRIPT++))
echo pybatch.py "@${SCRIPT_PATH}/cmdline.txt" --dry-run
eval pybatch.py "@${SCRIPT_PATH}/cmdline.txt" --dry-run ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
echo conda run -n pytorch2 pybatch.py "@${SCRIPT_PATH}/cmdline7.txt"
eval conda run -n pytorch2 pybatch.py "@${SCRIPT_PATH}/cmdline7.txt" ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

((SCRIPT++))
echo pybatch.py "@${SCRIPT_PATH}/cmdline7-2.txt" --conda-env pytorch2
eval pybatch.py "@${SCRIPT_PATH}/cmdline7-2.txt" --conda-env pytorch2 ${OUT} || echo "script ${SCRIPT} failed: $((CNT++))"

#############################
echo ""
echo "----------------------"
echo "scripts failed / run: $CNT / $SCRIPT"

popd  >/dev/null || exit
