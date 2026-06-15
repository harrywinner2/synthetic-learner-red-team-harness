#!/usr/bin/env python3
"""
tts.py — turn demo narration beats into audio clips via OpenAI TTS.

Reads the deployed-app key from OPENAI_API_KEY (or APP_AI_KEY). The key is read
from the environment only; never pass it on the command line and never log it.

Input (one of):
  --beats demo/beats.json      JSON list: [{"id":1,"text":"..."}, ...]
  --script demo/script.md      Markdown/plain text; split into beats on blank
                               lines, ignoring '#' headings and HTML comments.

Output:
  <outdir>/clip_001.mp3 ...    one file per beat
  <outdir>/manifest.json       [{"id","file","seconds","text"}], durations used
                               downstream to time the matching screen capture.

Usage:
  python scripts/tts.py --script demo/script.md --out demo/audio
  python scripts/tts.py --beats demo/beats.json --out demo/audio --voice alloy
"""
import argparse, json, os, re, subprocess, sys, urllib.request, urllib.error
from pathlib import Path

API_URL = "https://api.openai.com/v1/audio/speech"

def load_beats(args):
    if args.beats:
        data = json.loads(Path(args.beats).read_text())
        return [{"id": b.get("id", i + 1), "text": b["text"].strip()}
                for i, b in enumerate(data) if b.get("text", "").strip()]
    raw = Path(args.script).read_text()
    raw = re.sub(r"<!--.*?-->", "", raw, flags=re.DOTALL)      # drop HTML comments
    blocks, beats = re.split(r"\n\s*\n", raw), []
    for blk in blocks:
        lines = [ln for ln in blk.splitlines() if not ln.lstrip().startswith("#")]
        text = " ".join(l.strip() for l in lines).strip()
        text = re.sub(r"\s+", " ", text)
        if text:
            beats.append({"id": len(beats) + 1, "text": text})
    return beats

def synth(text, voice, model, key):
    body = json.dumps({"model": model, "voice": voice, "input": text,
                       "response_format": "mp3"}).encode()
    req = urllib.request.Request(
        API_URL, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()

def duration_seconds(path):
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-of", "json", "-show_format", str(path)],
            capture_output=True, text=True, check=True)
        return round(float(json.loads(out.stdout)["format"]["duration"]), 2)
    except Exception:
        # ffprobe absent → rough estimate at ~150 wpm so timing still works.
        words = len(Path(path).with_suffix(".txt").read_text().split()) \
            if Path(path).with_suffix(".txt").exists() else 0
        return round(words / 2.5, 2) if words else 0.0

def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--beats"); src.add_argument("--script")
    ap.add_argument("--out", default="demo/audio")
    ap.add_argument("--voice", default="alloy")
    ap.add_argument("--model", default="gpt-4o-mini-tts")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("APP_AI_KEY")
    if not key:
        sys.exit("No app AI key in env (OPENAI_API_KEY / APP_AI_KEY). Aborting.")

    beats = load_beats(args)
    if not beats:
        sys.exit("No narration beats found in input.")
    outdir = Path(args.out); outdir.mkdir(parents=True, exist_ok=True)

    manifest = []
    for b in beats:
        clip = outdir / f"clip_{b['id']:03d}.mp3"
        try:
            clip.write_bytes(synth(b["text"], args.voice, args.model, key))
        except urllib.error.HTTPError as e:
            sys.exit(f"TTS failed on beat {b['id']} (HTTP {e.code}). "
                     f"Ship the script + silent capture and flag narration pending.")
        (clip.with_suffix(".txt")).write_text(b["text"])  # for fallback duration
        secs = duration_seconds(clip)
        manifest.append({"id": b["id"], "file": clip.name,
                         "seconds": secs, "text": b["text"]})
        print(f"  clip_{b['id']:03d}.mp3  {secs:>6}s")

    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Wrote {len(manifest)} clips + manifest.json to {outdir}")

if __name__ == "__main__":
    main()
