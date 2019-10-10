#!/bin/bash

# this code is meant to be executed by Wakamola to generate
# a html page with the network
# the files are already in the correct folder by code
# reconstruct the html page
cd networkVisualizer
python _generador.py
# move it to the apache server
mv networkVisualizer/ejemplo.html /var/www/index.html
