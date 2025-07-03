#!/bin/bash
# This script receives the image path and does something with it
image_path="$1"
current_wp_path="~/Pictures/current_wallpaper"
rm -rf $current_wp_path
mkdir $current_wp_path
cp $image_path "${current_wp_path}/"

# # Do stuff to infer color palette and update css
# run ~/.config/hypr/color_palette_util/color_palette_util.py > get palette
# update ~/.config/waybar/style.css
# update ~/.config/hypr/config/colors.conf > cachyos colors
# # Lower priority
# update ~/.config/starship.toml
# update ~/.config/ghostty/config
# update ~/.config/rofi/config.rasi

# Kill ongoing
killall -q swaybg

# Set new WP, reset Waybar & Hyprland
nohup swaybg -o '*' -i "$image_path" -m fill > /dev/null 2>&1 &
bash ~/.config/waybar/waybar.sh
hyprctl reload

notify-send "Done!"
