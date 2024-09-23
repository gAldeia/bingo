#!/usr/bin/env bash

set -e
echo "importing os"
python -c "import mpi4py;"
echo "importing mpi4py"
python -c "import os;"
echo "getting filename"
python -c "import mpi4py;import os;filename = list(mpi4py.get_config().values())[0];"
echo "Finding MPI install"
MPI_EXEC=$(python -c "import mpi4py;import os;filename = list(mpi4py.get_config().values())[0];print(os.path.dirname(filename)+'/mpiexec');")
echo $MPI_EXEC
RUN_MODE=${1-"coverage"}
echo $RUN_MODE

echo "Running tests in $RUN_MODE mode"

# run mpi tests
for i in tests/integration/mpitests/*.py
do
  if [ $i != "tests/integration/mpitests/mpitest_util.py" ]
  then
    echo "Running mpitest: $i in $RUN_MODE mode"
    if [ $RUN_MODE == "coverage" ]
    then
      $MPI_EXEC -np 3 coverage run --parallel-mode --source=bingo $i
    elif [ $RUN_MODE == "normal" ]
    then
      $MPI_EXEC -np 3 python $i
    fi
  fi
done

# run pytest tests
if [ $RUN_MODE == "coverage" ]
then
  coverage combine
  pytest tests --cov=bingo --cov-report=term-missing --cov-append
elif [ $RUN_MODE == "normal" ]
then
  pytest tests
fi
