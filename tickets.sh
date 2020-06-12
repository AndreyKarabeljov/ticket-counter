#!/usr/bin/env bash
DIR="$(dirname "$(readlink -f "$0")")"
echo $DIR
python $DIR/ticket-counter.py