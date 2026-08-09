#!/usr/bin/env python3
"""
Experimental UADx dbx 160 CST editor.

Validated workflow:
    compatible dbx-only reference CST -> modify mapped plugin values -> new CST

Example:
    python dbx160_cst_editor.py \
        reference/UADx_dbx160_reference.cst \
        output.cst \
        --threshold 0.5 \
        --compression 0.5 \
        --output-db 10 \
        --mix-percent 25
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


def check_normalized(value, name):
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0.0 and 1.0")
    return value


def output_db_to_normalized(db):
    db = float(db)
    if not -20.0 <= db <= 20.0:
        raise ValueError("Output Gain must be between -20 and +20 dB")
    return (db + 20.0) / 40.0


def mix_percent_to_normalized(percent):
    percent = float(percent)
    if not 0.0 <= percent <= 100.0:
        raise ValueError("Mix must be between 0 and 100 percent")
    return percent / 100.0


def replace_state_values(state, values):
    state = bytearray(state)
    for name, offset in OFFSETS.items():
        packed = struct.pack("<f", values[name])
        for i in range(REPETITIONS):
            pos = offset + i * STRIDE
            if pos + 4 > len(state):
                raise RuntimeError(
                    "Reference state is smaller than expected. "
                    "Plugin/state format may have changed."
                )
            state[pos:pos+4] = packed
    return bytes(state)


def modify_cst(source, destination, threshold, compression, output_gain, mix):
    data = Path(source).read_bytes()

    match = re.search(
        br'(<key>jucePluginState</key>\s*<data>\s*)(.*?)(\s*</data>)',
        data,
        re.S,
    )
    if not match:
        raise RuntimeError("jucePluginState not found")

    original_b64 = match.group(2)
    compact_b64 = re.sub(br"\s+", b"", original_b64)
    state = base64.b64decode(compact_b64)

    values = {
        "threshold": check_normalized(threshold, "Threshold"),
        "compression": check_normalized(compression, "Compression"),
        "output_gain": check_normalized(output_gain, "Output Gain"),
        "mix": check_normalized(mix, "Mix"),
    }

    modified_state = replace_state_values(state, values)
    encoded = base64.b64encode(modified_state)

    # Preserve the original Base64 whitespace/line wrapping.
    chunks = re.split(br"(\s+)", original_b64)
    cursor = 0
    rebuilt = []
    for chunk in chunks:
        if not chunk:
            continue
        if re.fullmatch(br"\s+", chunk):
            rebuilt.append(chunk)
        else:
            length = len(chunk)
            rebuilt.append(encoded[cursor:cursor+length])
            cursor += length

    if cursor != len(encoded):
        raise RuntimeError("Encoded state length no longer matches template")

    new_data = (
        data[:match.start(2)]
        + b"".join(rebuilt)
        + data[match.end(2):]
    )
    Path(destination).write_bytes(new_data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_cst")
    parser.add_argument("output_cst")
    parser.add_argument("--threshold", type=float, required=True,
                        help="Normalized Threshold position, 0.0..1.0")
    parser.add_argument("--compression", type=float, required=True,
                        help="Normalized Compression value, 0.0..1.0")
    parser.add_argument("--output-db", type=float, required=True,
                        help="Output Gain in dB, -20..+20")
    parser.add_argument("--mix-percent", type=float, required=True,
                        help="Mix in percent, 0..100")
    args = parser.parse_args()

    modify_cst(
        args.input_cst,
        args.output_cst,
        threshold=args.threshold,
        compression=args.compression,
        output_gain=output_db_to_normalized(args.output_db),
        mix=mix_percent_to_normalized(args.mix_percent),
    )


if __name__ == "__main__":
    main()
