#!/usr/bin/env python3
"""Mux audio onto video with explicit stream maps + verification gates.

Usage:
    python scripts/verify_mux.py VIDEO AUDIO OUT [--no-loudness]

Gates (all must pass, exit 0):
  1. ffmpeg mux with explicit -map 0:v:0 -map 1:a:0 (video from 0, audio from 1)
  2. decode-clean: `ffmpeg -v error -i OUT -f null -` produces no stderr
  3. frame count: ffprobe nb_read_frames > 0 (printed for eyeballing vs expected)
  4. loudness: ebur128 integrated ~-12.7 LUFS, true peak < -0.7 dBTP (unless --no-loudness)
"""
import argparse
import re
import subprocess
import sys


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("audio")
    ap.add_argument("out")
    ap.add_argument("--no-loudness", action="store_true")
    ap.add_argument("--bitrate", default="192k")
    args = ap.parse_args()

    # 1. mux — explicit maps, video stream-copied, audio to AAC 48k
    mux = run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", args.video, "-i", args.audio,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", args.bitrate, "-ar", "48000",
        "-movflags", "+faststart", args.out,
    ])
    if mux.returncode != 0:
        print("MUX FAILED:\n" + mux.stderr, file=sys.stderr)
        return 1
    print(f"muxed: {args.out}")

    # 2. decode-clean
    dec = run(["ffmpeg", "-v", "error", "-i", args.out, "-f", "null", "-"])
    if dec.returncode != 0 or dec.stderr.strip():
        print("DECODE NOT CLEAN:\n" + dec.stderr, file=sys.stderr)
        return 1
    print("decode: clean")

    # 3. frame count
    fr = run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-count_frames", "-show_entries", "stream=nb_read_frames,duration",
        "-of", "default=nw=1", args.out,
    ])
    m = re.search(r"nb_read_frames=(\d+)", fr.stdout or "")
    if not m or int(m.group(1)) <= 0:
        print("FRAME COUNT FAILED:\n" + fr.stdout + fr.stderr, file=sys.stderr)
        return 1
    print(f"frames: {m.group(1)}")
    for line in (fr.stdout or "").splitlines():
        if line.startswith("duration="):
            print(line)

    # 4. loudness gates
    if not args.no_loudness:
        loud = run([
            "ffmpeg", "-hide_banner", "-nostats", "-i", args.out,
            "-af", "ebur128=peak=true", "-f", "null", "-",
        ])
        out = loud.stderr
        mi = re.search(r"I:\s*(-?\d+\.?\d*)\s*LUFS", out.rsplit("Summary:", 1)[-1])
        mt = re.search(r"Peak:\s*(-?\d+\.?\d*)\s*dBFS", out.rsplit("Summary:", 1)[-1])
        if mi:
            integrated = float(mi.group(1))
            print(f"integrated: {integrated} LUFS")
            if not (-16.0 <= integrated <= -10.0):
                print("LOUDNESS OUT OF BAND (-16..-10 LUFS)", file=sys.stderr)
                return 1
        else:
            print("LOUDNESS PARSE FAILED (summary missing)", file=sys.stderr)
            return 1
        if mt:
            tp = float(mt.group(1))
            print(f"true peak: {tp} dBFS")
            if tp > -0.7:
                print("TRUE PEAK TOO HOT (> -0.7)", file=sys.stderr)
                return 1

    print("ALL GATES PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
