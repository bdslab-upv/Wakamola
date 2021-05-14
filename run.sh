#!/usr/bin/env bash
python wakamola.py  &
apache2ctl -D FOREGROUND
