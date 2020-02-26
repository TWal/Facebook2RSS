#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

cd output
python -m http.server 8080
