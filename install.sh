#!/bin/bash
PY_VERSION=`python -c 'import sys; print(sys.version_info[0] == 3 and sys.version_info[1] == 6)'`
if [[ $PY_VERSION == True ]]; then
    python -m pip install dataclasses
fi
python -m pip install simple-parsing
