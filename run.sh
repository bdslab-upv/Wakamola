#!/usr/bin/env bash
rm -r __pycache__
python wakamola.py  & apache2ctl -D FOREGROUND
