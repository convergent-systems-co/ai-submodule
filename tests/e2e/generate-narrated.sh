#!/usr/bin/env bash
# generate-narrated.sh — Generate narrated MP4 videos from VHS recordings + transcripts.
#
# Uses macOS `say` for TTS and ffmpeg to overlay audio onto video.
#
# Usage:
#   bash tests/e2e/generate-narrated.sh              # Generate all narrated videos
#   bash tests/e2e/generate-narrated.sh init-test     # Generate a specific one
#
# Prerequisites:
#   - macOS (for `say` command)
#   - ffmpeg
#   - MP4 files already generated in tests/e2e/output/
#   - Transcript .md files in tests/e2e/transcripts/
#
# Output:
#   tests/e2e/output/<name>-narrated.mp4

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/output"
TRANSCRIPT_DIR="$SCRIPT_DIR/transcripts"
VOICE="${VOICE:-Samantha}"
RATE="${RATE:-175}"
SPECIFIC=""

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
  case "$1" in
    --voice)
      VOICE="$2"
      shift 2
      ;;
    --rate)
      RATE="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: $0 [--voice NAME] [--rate WPM] [tape-name]"
      echo ""
      echo "Options:"
      echo "  --voice NAME   macOS voice (default: Samantha)"
      echo "  --rate WPM     Speech rate in words per minute (default: 175)"
      echo ""
      echo "Arguments:"
      echo "  tape-name      Generate narration for a specific tape (without extension)"
      exit 0
      ;;
    -*)
      echo "Error: unknown option: $1" >&2
      exit 1
      ;;
    *)
      SPECIFIC="$1"
      shift
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Check prerequisites
# ---------------------------------------------------------------------------

if [[ "$(uname)" != "Darwin" ]]; then
  echo "ERROR: This script requires macOS (for the 'say' command)." >&2
  exit 1
fi

if ! command -v ffmpeg &>/dev/null; then
  echo "ERROR: ffmpeg is not installed." >&2
  echo "Install: brew install ffmpeg" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# Narrate function
# ---------------------------------------------------------------------------

generate_narrated() {
  local name="$1"
  local video="$OUTPUT_DIR/${name}.mp4"
  local transcript="$TRANSCRIPT_DIR/${name}.md"
  local audio_tmp="$OUTPUT_DIR/${name}-narration.m4a"
  local output="$OUTPUT_DIR/${name}-narrated.mp4"

  if [[ ! -f "$video" ]]; then
    echo "SKIP: $name — no video file ($video)"
    return 0
  fi

  if [[ ! -f "$transcript" ]]; then
    echo "SKIP: $name — no transcript file ($transcript)"
    return 0
  fi

  echo "--- Generating narration: $name ---"

  # Extract plain text from markdown (strip headers, blank lines, emphasis)
  local plain_text
  plain_text=$(sed -E '
    /^#/d
    /^$/d
    s/\*\*([^*]+)\*\*/\1/g
    s/\*([^*]+)\*/\1/g
    s/`([^`]+)`/\1/g
  ' "$transcript")

  # Generate TTS audio
  echo "  Generating audio (voice: $VOICE, rate: $RATE wpm)..."
  say -v "$VOICE" -r "$RATE" -o "$audio_tmp" --data-format=aac "$plain_text"

  # Get durations
  local video_duration audio_duration
  video_duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$video" 2>/dev/null)
  audio_duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$audio_tmp" 2>/dev/null)

  echo "  Video duration: ${video_duration}s"
  echo "  Audio duration: ${audio_duration}s"

  # Overlay audio onto video
  # If audio is longer than video, extend the video with the last frame
  # If video is longer than audio, the remaining video plays silent
  echo "  Combining video + audio..."
  ffmpeg -y -i "$video" -i "$audio_tmp" \
    -c:v copy \
    -c:a aac -b:a 128k \
    -map 0:v:0 -map 1:a:0 \
    -shortest \
    "$output" 2>/dev/null

  # Clean up temp audio
  rm -f "$audio_tmp"

  local output_size
  output_size=$(ls -lh "$output" | awk '{print $5}')
  echo "  DONE: $output ($output_size)"
  echo ""
}

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

passed=0
total=0

if [[ -n "$SPECIFIC" ]]; then
  generate_narrated "$SPECIFIC"
  total=1
  passed=1
else
  for transcript in "$TRANSCRIPT_DIR"/*.md; do
    [[ -f "$transcript" ]] || continue
    name="$(basename "$transcript" .md)"
    total=$((total + 1))
    if generate_narrated "$name"; then
      passed=$((passed + 1))
    fi
  done
fi

echo "================================"
echo "Narration Summary"
echo "  Total:   $total"
echo "  Generated: $passed"
echo "================================"
