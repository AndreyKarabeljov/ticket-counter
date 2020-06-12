#!/data/data/com.termux/files/usr/bin/sh
DIR="$(dirname "$(readlink -f "$0")")"
python $DIR/ticket-counter.py > ~/tmp.log