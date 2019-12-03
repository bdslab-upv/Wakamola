#!/usr/bin/env bash
rm -r __pycache__
python wakamola.py -l es --godmode wakafill --statistics statistics --network create_graph --network_link "158.42.166.224/wakamolaupv" &
apache2ctl -D FOREGROUND
