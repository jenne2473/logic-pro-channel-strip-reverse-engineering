# Logic CST Plugin Mapping

Version: **0.1.0**  
Status: **Experimental / empirically validated**

This project documents reverse-engineered parameter mappings for Logic Pro
`.cst` Channel Strip Setting files.

## Current plugin

### UADx dbx 160

The dbx 160 stores its plugin state inside an XML/plist-style
`jucePluginState` field encoded as Base64.

After Base64 decoding, the tested state contains the relevant parameter values
as little-endian 32-bit floating-point values.

In the tested template, the parameter block is repeated **32 times**, with a
stride of **68 bytes**.

Template-relative offsets inside the decoded `jucePluginState`:

| Parameter | Offset |
|---|---:|
| Threshold | 209 |
| Compression | 213 |
| Output Gain | 217 |
| Mix | 229 |

These offsets are **template/version dependent** and should not be assumed to
be universal across all future plugin versions or state formats.

## Parameter mappings

### Threshold

Normalized range: `0.0 .. 1.0`

Observed:
- minimum = `0.0`
- middle = `0.5`
- maximum = `1.0`

The normalized value corresponds to knob position. The visible mV/V markings
are not a linear physical scale.

### Compression

Normalized range: `0.0 .. 1.0`

Observed:
- visible value 1 = `0.0`
- visible value 4 = `0.5`
- maximum = `1.0`
- approx. visible value 3 = `0.359985`
- approx. visible value 6 = `0.669983`

The visible scale is non-linear relative to the normalized internal value.

### Output Gain

Normalized range: `0.0 .. 1.0`

Visible range: `-20 dB .. +20 dB`

Formula:

```text
dB = 40*x - 20
x  = (dB + 20) / 40
```

Examples:
- `0.0` = `-20 dB`
- `0.5` = `0 dB`
- `0.75` = `+10 dB`
- `1.0` = `+20 dB`

### Mix

Normalized range: `0.0 .. 1.0`

Formula:

```text
percent = 100*x
x = percent / 100
```

Observed mouse-position reference:
- minimum = `0.0`
- visually near middle = `0.47998046875`
- maximum = `1.0`

## Validation

A CST was generated automatically with:

```text
Threshold   = 0.50
Compression = 0.50
Output Gain = 0.75  (+10 dB)
Mix         = 0.25  (25 %)
```

The generated CST loaded successfully in Logic Pro and all four controls
appeared at the expected positions.

This validates the overall approach:

1. Extract `jucePluginState`
2. Base64-decode it
3. Modify the relevant float32 values in every repeated state block
4. Base64-encode the state again
5. Write it back into the CST
6. Load the modified CST in Logic Pro

## Files

- `logic-plugin-mappings.json` – machine-readable mapping database
- `dbx160_cst_editor.py` – example editor for the tested dbx 160 template
- `README.md` – this documentation

## Next plugins

Planned mapping sequence:

1. UADx LA-3A
2. Manley Tube Preamp
3. UADx Neve 1073
4. UADx Pultec
5. Aguilar Amp/Cab

The JSON file is intended to grow into a reusable mapping database for complete
Logic Pro channel-strip generation.
