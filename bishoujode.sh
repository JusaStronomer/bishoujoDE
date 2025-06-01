#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

PROJECT_DIR="/home/jusa/Projects/bhunivelze/bishoujoDE"
VENV_PATH="${PROJECT_DIR}/.venv_dev/bin/activate"

# Log script execution start for debugging
echo "bishoujode.sh: Starting up at $(date)" >> "${PROJECT_DIR}/bishoujode_service.log"

if [ ! -d "${PROJECT_DIR}" ]; then
    echo "bishoujode.sh: Error - Project directory ${PROJECT_DIR} not found." >> "${PROJECT_DIR}/bishoujode_service.log"
    exit 1
fi
cd "${PROJECT_DIR}"
echo "bishoujode.sh: Changed to directory ${PROJECT_DIR}." >> "${PROJECT_DIR}/bishoujode_service.log"

if [ ! -f "${VENV_PATH}" ]; then
    echo "bishoujode.sh: Error - Virtual environment activate script not found at ${VENV_PATH}." >> "${PROJECT_DIR}/bishoujode_service.log"
    exit 1
fi
source "${VENV_PATH}"
echo "bishoujode.sh: Virtual environment activated." >> "${PROJECT_DIR}/bishoujode_service.log"

echo "bishoujode.sh: Launching main.py..." >> "${PROJECT_DIR}/bishoujode_service.log"
# It's often good to use the full path to the python interpreter in the venv,
# though `python3` should work after `source activate`.
# For explicit clarity: "${PROJECT_DIR}/.venv_dev/bin/python3" main.py
python3 main.py >> "${PROJECT_DIR}/bishoujode_app.log" 2>&1
echo "bishoujode.sh: main.py exited at $(date)." >> "${PROJECT_DIR}/bishoujode_service.log"

exit 0
