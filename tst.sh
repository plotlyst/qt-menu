#!/bin/bash

# exit when any command fails
set -e

python -X faulthandler -m pytest test  --cov=qtmenu --junitxml=report.xml --cov-report html:coverage --cov-report term -v --color=yes
