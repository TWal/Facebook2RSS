#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

mkdir -p output
for pagename in $(cat subscriptions); do
    echo "Proccesing $pagename"
    python main.py $pagename > output/$pagename.xml
done
