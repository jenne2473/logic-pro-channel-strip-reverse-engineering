# Logic Pro Channel Strip Reverse Engineering

Version **0.3.0**  
Status: **Experimental; empirically validated for UADx dbx 160 and UADx LA-3A**

This repository documents a practical method for programmatically modifying
Logic Pro `.cst` Channel Strip Settings.

## Current architecture

The validated workflow is:

**compatible reference CST + known plugin-state mapping → modified CST**

The project does not yet claim arbitrary CST generation completely from scratch.
Minimal reference CST files are therefore part of the reverse-engineering data.

## Common UADx state pattern observed

Both mapped UADx plugins use a Base64-encoded `jucePluginState`. In the tested
states, mapped values are little-endian `float32`, repeated **32 times** with a
**68-byte stride**.

This is an empirical observation, not a guaranteed Universal Audio file-format
contract.

## Mapped plugins

### UADx dbx 160

Offsets:

| Parameter | Offset |
|---|---:|
| Threshold | 209 |
| Compression | 213 |
| Output Gain | 217 |
| Mix | 229 |

Output Gain mapping:

`dB = 40*x - 20`

Mix mapping:

`percent = 100*x`

Compression uses a non-linear visible scale. Confirmed examples include visible
1 → 0.0 and visible 4 → 0.5.

A multi-parameter generated CST was successfully loaded and verified in Logic Pro.

### UADx LA-3A

Observed decoded plugin-state size: **2614 bytes**.

| Parameter | Offset | Mapping / values |
|---|---:|---|
| Peak Reduction | 209 | visible 0/5/10 → 0/0.5/1 |
| Gain | 213 | visible 0 ≈ 0.00997925; 5 ≈ 0.49499512; 10 = 1 |
| COMP/LIM | 217 | COMP=0; LIM=1 |
| Meter | 221 | OFF=0; GR=0.5; OUTPUT=1 |
| HF | 225 | normalized 0..1 |
| Mix | 229 | normalized 0..1 |

The slight deviations around manually selected midpoint values appear to be
control/mouse quantization and are preserved as empirical observations rather
than forced into an assumed exact formula.

#### LA-3A validation

A generated CST simultaneously set:

- Peak Reduction normalized `0.70`
- Gain normalized `0.30`
- Mode `LIM`
- Meter `OUTPUT`
- HF normalized `0.25`
- Mix normalized `0.75`

The file loaded successfully in Logic Pro and the user confirmed that all six
controls appeared correctly. This establishes the LA-3A as the second validated
automatable plugin in the project.

## Reference CSTs

`reference/UADx_dbx160_reference.cst`

Canonical dbx-only template with documented normalized values.

`reference/UADx_LA-3A_reference.cst`

Canonical LA-3A-only template. Defined state:

- Peak Reduction = 0.5 (visible 5)
- Gain = 0.494995117 (empirically visible 5)
- Mode = COMP
- Meter = GR
- HF = 0.5
- Mix = 1.0

## Machine-readable data

`logic-plugin-mappings.json` is the authoritative machine-readable mapping
database. Future plugins should be added there together with a minimal reference
CST and a successful Logic validation test.

## Editor

`cst_editor.py` is a small generic proof-of-concept editor for the mapped
normalized parameters.

Example:

```bash
python cst_editor.py la3a   reference/UADx_LA-3A_reference.cst   LA3A_Test.cst   --set peak_reduction=0.7   --set gain=0.3   --set comp_lim=1   --set meter=1   --set hf=0.25   --set mix=0.75
```

## Compatibility warning

All offsets and layouts are reverse-engineered and empirical. Logic Pro or
plugin updates may change serialization. Keep original CSTs and revalidate
generated files after relevant software updates.

## Next targets

Planned mapping work includes Manley Tube Preamp, UADx Neve 1073, UADx Pultec
and Aguilar Amp/Cab.
