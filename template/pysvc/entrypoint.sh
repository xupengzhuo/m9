#!/bin/bash
set -e

if [ -e ./start.bin]; then
    exec start.bin
elif [ -e ./start.py]; then
    exec python start.py
fi

exec "$@"