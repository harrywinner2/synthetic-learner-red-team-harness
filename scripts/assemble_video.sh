#!/usr/bin/env bash
# assemble_video.sh — stitch per-beat screen clips + TTS narration into one mp4.
#
# Pairs each narration clip (from tts.py manifest) with the matching screen
# capture by zero-padded id, makes each segment exactly as long as its
# narration, then concatenates. Handles either a video clip or a single still
# image per beat; missing captures become a neutral slate so assembly still
# completes.
#
# Usage:
#   scripts/assemble_video.sh <clips_dir> <audio_dir> <out.mp4>
#   (audio_dir must contain manifest.json from tts.py)
set -euo pipefail

command -v ffmpeg  >/dev/null || { echo "ffmpeg not found — defer assembly to user."; exit 3; }
command -v python3 >/dev/null || { echo "python3 needed to read manifest."; exit 3; }

CLIPS="${1:?clips dir}"; AUDIO="${2:?audio dir}"; OUT="${3:?output mp4}"
MAN="$AUDIO/manifest.json"
[ -f "$MAN" ] || { echo "missing $MAN (run tts.py first)"; exit 3; }

WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
W=1920; H=1080; FPS=30

# Emit "id<TAB>seconds" per beat, in order.
mapfile -t ROWS < <(python3 - "$MAN" <<'PY'
import json,sys
for b in json.load(open(sys.argv[1])):
    print(f"{int(b['id']):03d}\t{float(b['seconds']) or 4.0}")
PY
)

find_clip(){ # $1=id -> path of first matching capture, or empty
  for ext in mp4 webm mov mkv png jpg jpeg; do
    local m; m=$(ls "$CLIPS/clip_$1."$ext 2>/dev/null | head -n1 || true)
    [ -n "$m" ] && { echo "$m"; return; }
  done
}
is_still(){ case "$1" in *.png|*.jpg|*.jpeg) return 0;; *) return 1;; esac; }

LIST="$WORK/concat.txt"; : > "$LIST"; i=0
for row in "${ROWS[@]}"; do
  id="${row%%$'\t'*}"; dur="${row##*$'\t'}"
  aud="$AUDIO/clip_$id.mp3"; clip="$(find_clip "$id")"; seg="$WORK/seg_$id.mp4"
  vf="scale=$W:$H:force_original_aspect_ratio=decrease,pad=$W:$H:(ow-iw)/2:(oh-ih)/2,fps=$FPS,format=yuv420p"

  if [ -z "$clip" ]; then
    ffmpeg -y -v error -f lavfi -i "color=c=0x101418:s=${W}x${H}:r=$FPS" \
      -t "$dur" -vf "$vf" -an "$seg.v.mp4"
  elif is_still "$clip"; then
    ffmpeg -y -v error -loop 1 -i "$clip" -t "$dur" -vf "$vf" -an "$seg.v.mp4"
  else
    # loop/trim the screen clip to exactly the narration length
    ffmpeg -y -v error -stream_loop -1 -i "$clip" -t "$dur" -vf "$vf" -an "$seg.v.mp4"
  fi

  if [ -f "$aud" ]; then
    ffmpeg -y -v error -i "$seg.v.mp4" -i "$aud" -t "$dur" \
      -c:v libx264 -preset veryfast -crf 20 -c:a aac -b:a 192k \
      -af "apad" -shortest "$seg"
  else
    ffmpeg -y -v error -i "$seg.v.mp4" -t "$dur" \
      -c:v libx264 -preset veryfast -crf 20 -an "$seg"
  fi
  echo "file '$seg'" >> "$LIST"; i=$((i+1))
done

[ "$i" -gt 0 ] || { echo "no segments built"; exit 3; }
mkdir -p "$(dirname "$OUT")"
ffmpeg -y -v error -f concat -safe 0 -i "$LIST" -c:v libx264 -preset veryfast \
  -crf 20 -c:a aac -b:a 192k -pix_fmt yuv420p "$OUT"
echo "Wrote $OUT ($i beats)."
