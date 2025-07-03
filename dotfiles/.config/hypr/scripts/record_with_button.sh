#!/bin/bash

# List of known outputs (edit as needed)
OUTPUTS=("eDP-1" "HDMI-A-2")

# Build newline-separated string for the combo box
OUTPUT_CHOICES=$(printf "%s!" "${OUTPUTS[@]}")
OUTPUT_CHOICES=${OUTPUT_CHOICES::-1}  # remove trailing '!'

# Show YAD form dialog
FORM_RESULT=$(yad --form \
    --title="Screen Recorder" \
    --center \
    --on-top \
    --width=400 \
    --height=200 \
    --field="Monitor:CB" "$OUTPUT_CHOICES" \
    --field="Capture Microphone:CHK" "FALSE" \
    --button="Start Recording:0" --button="Cancel:1")

# If user cancels
[ $? -ne 0 ] && notify-send "Recording canceled." && exit 1

# Parse the result
SELECTED_MONITOR=$(echo "$FORM_RESULT" | cut -d'|' -f1)
MIC_ENABLED=$(echo "$FORM_RESULT" | cut -d'|' -f2)

# Sanity check
[ -z "$SELECTED_MONITOR" ] && notify-send "No monitor selected." && exit 1

# Construct output filename
OUTFILE=~/Videos/recording_$(date +%s).mp4

# Add -a if mic checkbox is checked
AUDIO_FLAG=""
if [ "$MIC_ENABLED" = "TRUE" ]; then
    AUDIO_FLAG="-a"
fi

notify-send "Recording on $SELECTED_MONITOR ($MIC_ENABLED)..."

# Start wf-recorder with optional -a
wf-recorder -y -o "$SELECTED_MONITOR" $AUDIO_FLAG -f "$OUTFILE" &
RECORD_PID=$!

# Show stop button
yad --title="Recording..." \
    --button="Stop Recording:1" \
    --center \
    --on-top \
    --undecorated \
    --skip-taskbar \
    --width=200 --height=100

# Kill recording
kill $RECORD_PID
notify-send "Recording saved to $OUTFILE"
