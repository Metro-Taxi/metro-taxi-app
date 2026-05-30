#!/bin/bash
# Génère 3 vidéos MP4 verticales 1080x1920 à partir des 12 images Nano Banana
# Durée par image: 3 sec | Transition fade 0.5s | Format mobile vertical (TikTok/Reels)

set -e
MARKETING_DIR="/app/frontend/public/marketing"
cd "$MARKETING_DIR"

build_scenario() {
    local name="$1"
    local prefix="$2"
    local output="${name}.mp4"

    echo "=== Building $output ==="

    # Concatène les 4 images avec transition fade
    # Chaque image dure 3 sec, transition crossfade 0.5s entre chaque
    ffmpeg -y \
        -loop 1 -t 3 -i "${prefix}_01.png" \
        -loop 1 -t 3 -i "${prefix}_02.png" \
        -loop 1 -t 3 -i "${prefix}_03.png" \
        -loop 1 -t 3 -i "${prefix}_04.png" \
        -filter_complex "
            [0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[v0];
            [1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[v1];
            [2:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[v2];
            [3:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[v3];
            [v0][v1]xfade=transition=fade:duration=0.5:offset=2.5[vt1];
            [vt1][v2]xfade=transition=fade:duration=0.5:offset=5[vt2];
            [vt2][v3]xfade=transition=fade:duration=0.5:offset=7.5[vout]
        " \
        -map "[vout]" \
        -c:v libx264 -pix_fmt yuv420p -crf 23 -preset fast \
        -r 30 -movflags +faststart \
        "$output" 2>&1 | tail -3

    if [ -f "$output" ]; then
        size=$(du -h "$output" | cut -f1)
        echo "  ✅ $output ($size)"
    else
        echo "  ❌ ÉCHEC $output"
    fi
}

# Génération parallèle des 3 scénarios
build_scenario "metrotaxi_scenario1_bus_bonde" "scenario1_bus_bonde" &
PID1=$!
build_scenario "metrotaxi_scenario2_metro_vs" "scenario2_metro_vs" &
PID2=$!
build_scenario "metrotaxi_scenario3_transbordement" "scenario3_transbordement" &
PID3=$!

wait $PID1 $PID2 $PID3

echo ""
echo "=== RÉSULTAT FINAL ==="
ls -lh "$MARKETING_DIR"/*.mp4 2>/dev/null
