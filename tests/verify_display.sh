#!/bin/bash
# shellcheck source-path=SCRIPTDIR
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
# shellcheck source=../package/gunslugs2/display.inc
source package/gunslugs2/display.inc
GAMEDIR="$(mktemp -d)"
trap 'rmdir "$GAMEDIR"' EXIT
for size in 640x480 720x480 720x720 1024x768 1280x720 960x544 320x240; do
    DISPLAY_WIDTH="${size%x*}" DISPLAY_HEIGHT="${size#*x}"
    GUNSLUGS2_RESOLUTION=auto
    gunslugs2_display_setup
    [[ "${display_env[0]}" == "WESTON_HEADLESS_WIDTH=$DISPLAY_WIDTH" ]]
    [[ "${display_env[1]}" == "WESTON_HEADLESS_HEIGHT=$DISPLAY_HEIGHT" ]]
    [[ "${display_java[0]}" == "-Dgunslugs2.width=$DISPLAY_WIDTH" ]]
    [[ "${display_java[1]}" == "-Dgunslugs2.height=$DISPLAY_HEIGHT" ]]
done
DISPLAY_WIDTH=0 DISPLAY_HEIGHT=0
gunslugs2_display_setup
[[ "${#display_env[@]}" == 0 && "${#display_java[@]}" == 0 ]]
for bad in 0x480 640x0 100x100 9999x720 640x480oops '640x480;exit' 640X480; do
    GUNSLUGS2_RESOLUTION="$bad"
    if gunslugs2_display_setup; then echo "Accepted invalid size: $bad"; exit 1; fi
done
GUNSLUGS2_RESOLUTION=0720x0480
gunslugs2_display_setup
[[ "${display_java[0]}" == '-Dgunslugs2.width=720' ]]
[[ "${display_java[1]}" == '-Dgunslugs2.height=480' ]]
printf '720x720\r\n' > "$GAMEDIR/resolution.txt"
GUNSLUGS2_RESOLUTION=""
gunslugs2_display_setup
[[ "${display_java[1]}" == '-Dgunslugs2.height=720' ]]
GUNSLUGS2_RESOLUTION=1280x720
gunslugs2_display_setup
[[ "${display_java[0]}" == '-Dgunslugs2.width=1280' ]]
rm -- "$GAMEDIR/resolution.txt"
echo 'DISPLAY_CHECKS_OK: sizes, override precedence, CRLF, invalid inputs, automatic fallback'
