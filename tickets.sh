#!/usr/bin/env bash
BASEDIR="$(cd "$(dirname "$0")" && pwd)"
echo $BASEDIR
python $BASEDIR/ticket-counter.py