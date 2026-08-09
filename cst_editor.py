#!/usr/bin/env python3
"""Experimental Logic Pro CST editor for mapped UADx plugins."""
from pathlib import Path
import argparse, base64, re, struct

STRIDE = 68
REPETITIONS = 32

MAPS = {
    "dbx160": {
        "offsets": {"threshold":209,"compression":213,"output_gain":217,"mix":229}
    },
    "la3a": {
        "offsets": {"peak_reduction":209,"gain":213,"comp_lim":217,"meter":221,"hf":225,"mix":229}
    }
}

def modify(source, destination, offsets, values):
    data = Path(source).read_bytes()
    m = re.search(br'(<key>jucePluginState</key>\s*<data>\s*)(.*?)(\s*</data>)', data, re.S)
    if not m: raise RuntimeError("jucePluginState not found")
    original = m.group(2)
    state = bytearray(base64.b64decode(re.sub(br"\s+", b"", original)))
    for name, value in values.items():
        if name not in offsets: continue
        if not 0 <= value <= 1: raise ValueError(f"{name}: normalized value must be 0..1")
        packed = struct.pack("<f", value)
        for i in range(REPETITIONS):
            pos = offsets[name] + i*STRIDE
            state[pos:pos+4] = packed
    encoded = base64.b64encode(state)
    chunks = re.split(br"(\s+)", original)
    cursor, rebuilt = 0, []
    for chunk in chunks:
        if not chunk: continue
        if re.fullmatch(br"\s+", chunk): rebuilt.append(chunk)
        else:
            n=len(chunk); rebuilt.append(encoded[cursor:cursor+n]); cursor += n
    if cursor != len(encoded): raise RuntimeError("Encoded state length mismatch")
    Path(destination).write_bytes(data[:m.start(2)] + b"".join(rebuilt) + data[m.end(2):])

def main():
    p=argparse.ArgumentParser()
    p.add_argument("plugin", choices=MAPS)
    p.add_argument("input_cst")
    p.add_argument("output_cst")
    p.add_argument("--set", action="append", default=[], metavar="PARAM=VALUE",
                   help="Set normalized parameter value (0..1); repeat as needed")
    a=p.parse_args()
    values={}
    for item in a.set:
        k,v=item.split("=",1); values[k]=float(v)
    modify(a.input_cst,a.output_cst,MAPS[a.plugin]["offsets"],values)

if __name__=="__main__": main()
