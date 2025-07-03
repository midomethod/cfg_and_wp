#!/usr/bin/env bash

find ~/Pictures/wallpapers -type f -print0 | while IFS= read -r -d '' file; do
  viu "$file"
  ./color_palette_util.py -if "$file"
done
