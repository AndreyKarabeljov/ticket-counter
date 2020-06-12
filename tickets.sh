#!/usr/bin/env bash
DIR="$(dirname "$(readlink -f "$0")")"
python $DIR/ticket-counter.py > ~/tmp.log