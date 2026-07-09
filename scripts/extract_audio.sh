#!/usr/bin/env bash
# Extract audio from docs/video/*.mp4 into docs/audio/sessio_N/
# Produces: audio.mp3 (full, mono 64k) + chunk_%04d.mp3 (20-min splits)
# for uploading to AssemblyAI.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VIDEO_DIR="$ROOT/docs/video"
AUDIO_DIR="$ROOT/docs/audio"
CHUNK_SECS=1200  # 20 min

mkdir -p "$AUDIO_DIR"

declare -A MAPPING=(
  ["DIVAS Y TRAGONAS A LA PRIMERA AVENTURA __ CAMPANYA III __.mp4"]="sessio_3"
  ["DIVAS Y TRAGONAS A LA PRIMERA AVENTURA __ CAMPANYA IV __.mp4"]="sessio_4"
  ["D&D SESSIÓ 5 - FUMAROLA.mp4"]="sessio_5"
  ["D&D SESSIÓ 6 - La Mina Perduda del Phentanilo.mp4"]="sessio_6"
  ["D&D SESSIÓ 8 - VARA DE VIDRE.mp4"]="sessio_8"
)

for src in "${!MAPPING[@]}"; do
  dst="${MAPPING[$src]}"
  in="$VIDEO_DIR/$src"
  out_dir="$AUDIO_DIR/$dst"
  full="$out_dir/audio.mp3"

  mkdir -p "$out_dir"

  if [[ ! -f "$in" ]]; then
    echo "⚠  Falta: $in — saltant"
    continue
  fi

  if [[ -f "$full" ]]; then
    echo "✓  $dst/audio.mp3 ja existeix — saltant extracció"
  else
    echo "▶  Extraient àudio: $src → $dst/audio.mp3"
    ffmpeg -nostdin -hide_banner -loglevel warning -y \
      -i "$in" -vn -ac 1 -ar 16000 -b:a 64k "$full"
  fi

  if compgen -G "$out_dir/chunk_*.mp3" > /dev/null; then
    echo "✓  $dst/ ja té chunks — saltant divisió"
  else
    echo "✂  Dividint en chunks de $((CHUNK_SECS/60)) min: $dst/"
    ffmpeg -nostdin -hide_banner -loglevel warning -y \
      -i "$full" -f segment -segment_time "$CHUNK_SECS" \
      -c copy -reset_timestamps 1 \
      "$out_dir/chunk_%04d.mp3"
  fi

  echo
done

echo "✅  Fet. Estructura:"
find "$AUDIO_DIR" -maxdepth 2 -type f -printf "  %p (%s bytes)\n" | sort
