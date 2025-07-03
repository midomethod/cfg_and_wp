#!/usr/bin/env bash

file_path="$1"

viu "$file_path"
./color_palette_util.py -if "$file_path"
