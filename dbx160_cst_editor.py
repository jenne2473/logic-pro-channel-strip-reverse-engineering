#!/usr/bin/env python3
"""
Experimental UADx dbx 160 CST editor.

Usage:
    python dbx160_cst_editor.py input.cst output.cst \
        --threshold 0.5 \
        --compression 0.5 \
        --output-db 10 \
        --mix-percent 25

Important:
- This uses offsets derived from the tested dbx 160 CST template.
- Plugin/version changes may invalidate the offsets.
"""

from pathlib import Path
import argparse
import base64
import re
import struct

OFFSETS = {
    "threshold": 209,
    "compression": 213,
    "output_gain": 217,
    "mix": 229,
}
STRIDE = 68
REPETITIONS = 32


def clamp01(v):
    if not 0.0 <= v <= 1.0:
        raise ValueError(f"Normalized value must be 0..1, got {v}")
    return float(v)


def output_db_to_normalized(db):
    if not -20.0 <= db <= 20.0:
        raise ValueError("Output gain must be between -20 and +20 dB")
    return (db + 20.0) / 40.0


def mix_percent_to_normalized(percent):
    if not 0.0 <= percent <= 100.0:
        raise ValueError("Mix must be between 0 and 100 percent")
    return percent / 100.0


def modify_cst(src, dst, threshold, compression, output_gain, mix):
    data = Path(src).read_bytes()

    match = re.search(
        br'(<key>jucePluginState</key>\s*<data>\s*)(.*?)(\s*</data>)',
        data,
        re.S,
    )
    if not match:
        raise RuntimeError("jucePluginState not found")

    original_b64 = match.group(2)
    compact = re.sub(br"\s+", b"", original_b64)
    state = bytearray(base64.b64decode(compact))

    targets = {
        "threshold": clamp01(threshold),
        "compression": clamp01(compression),
        "output_gain": clamp01(output_gain),
        "mix": clamp01(mix),
    }

    for name, offset in OFFSETS.items():
        packed = struct.pack("<f", targets[name])
        for i in range(REPETITIONS):
            pos = offset + i * STRIDE
            state[pos:pos+4] = packed

    encoded = base64.b64encode(bytes(state))

    # Preserve original Base64 whitespace/wrapping.
    parts = re.split(br"(\s+)", original_b64)
    cursor = 0
    rebuilt = []
    for part in parts:
        if not part:
            continue
        if re.fullmatch(br"\s+", part):
            rebuilt.append(part)
        else:
            n = len(part)
            rebuilt.append(encoded[cursor:cursor+n])
            cursor += n

    if cursor != len(encoded):
        raise RuntimeError("Base64 length/wrapping mismatch")

    new_data = data[:match.start(2)] + b"".join(rebuilt) + data[match.end(2):]
    Path(dst).write_bytes(new_data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--threshold", type=float, required=True,
                    help="normalized 0..1")
    ap.add_argument("--compression", type=float, required=True,
                    help="normalized 0..1")
    ap.add_argument("--output-db", type=float, required=True,
                    help="-20..+20 dB")
    ap.add_argument("--mix-percent", type=float, required=True,
                    help="0..100 percent")
    args = ap.parse_args()

    modify_cst(
        args.input,
        args.output,
        threshold=args.threshold,
        compression=args.compression,
        output_gain=output_db_to_normalized(args.output_db),
        mix=mix_percent_to_normalized(args.mix_percent),
    )


if __name__ == "__main__":
    main()
