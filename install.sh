#!/bin/bash

for ver in 3.12 3.11 3.13 3.10 python3; do
    if command -v python$ver &>/dev/null; then
        PYTHON_EXE="python$ver"
        break
    fi
done


$PYTHON_EXE -m venv .venv

./.venv/bin/pip install --upgrade pip setuptools wheel packaging && \
./.venv/bin/pip install ocp_vscode && \
./.venv/bin/pip install --upgrade build123d