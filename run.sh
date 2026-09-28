#!/bin/bash

cd "$(dirname "$(readlink -f "$0")")"

python run_script.py "$@"
