# Logic Pro Channel Strip Reverse Engineering

Version **0.2.0**  
Status: **Experimental, empirically validated for UADx dbx 160**

This repository documents a practical method for modifying Logic Pro `.cst`
Channel Strip Setting files programmatically.

## Key finding

A Logic Pro CST can contain the full plugin state, not just the plugin identity.
For the tested **UADx dbx 160**, the plugin state is stored in a Base64 encoded
`jucePluginState`.

After decoding, relevant parameters can be edited as little-endian 32-bit
floating-point values.

A generated CST with several dbx parameters changed simultaneously was
successfully loaded by Logic Pro and displayed correctly in the UADx dbx 160 UI.

## Important architectural point

At the current stage this project supports:

**compatible CST template + known parameter mapping -> modified CST**

It does **not** yet claim to create an arbitrary Logic Pro CST completely from
scratch.

A valid reference/template CST is therefore part of the documented knowledge.
The repository includes one canonical minimal dbx-only reference file:

`reference/UADx_dbx160_reference.cst`

Known values in that reference:

- Threshold normalized: `0.50`
- Compression normalized: `0.50`
- Compression visible value: `4`
- Output Gain: `0 dB`
- Mix: `100 %`

This template can be copied and modified by the supplied script.

## UADx dbx 160 state layout

Inside the decoded `jucePluginState`:

- value type: `float32`, little-endian
- parameter block repetitions: **32**
- block stride: **68 bytes**

Offsets used in the tested reference state:

| Parameter | Offset |
|---|---:|
| Threshold | 209 |
| Compression | 213 |
| Output Gain | 217 |
| Mix | 229 |

These offsets are empirical and may depend on plugin version/state format.
They should be validated again after relevant Logic Pro or UADx updates.

## Parameter mappings

### Threshold

Normalized parameter range: `0.0 .. 1.0`

Observed:

- minimum -> `0.0`
- middle -> `0.5`
- maximum -> `1.0`

This corresponds to knob position. The visible threshold markings themselves
are not a linear physical scale.

### Compression

Normalized internal range: `0.0 .. 1.0`

Observed:

- visible `1` -> `0.0`
- visible `4` -> `0.5`
- maximum -> `1.0`
- approx. visible `3` -> `0.359985`
- approx. visible `6` -> `0.669983`

The visible Compression scale is therefore non-linear relative to the internal
normalized parameter.

### Output Gain

Normalized range: `0.0 .. 1.0`  
Visible range: `-20 dB .. +20 dB`

Formula:

```text
dB = 40*x - 20
x  = (dB + 20) / 40
```

Examples:

- `0.00` -> `-20 dB`
- `0.50` -> `0 dB`
- `0.75` -> `+10 dB`
- `1.00` -> `+20 dB`

### Mix

Normalized range: `0.0 .. 1.0`  
Visible range: `0 .. 100 %`

Formula:

```text
percent = 100*x
x = percent / 100
```

Observed:

- minimum -> `0.0`
- visually near middle in one manual test -> `0.47998046875`
- maximum -> `1.0`

## Validation test

A CST was generated with these four values changed simultaneously:

```text
Threshold   = 0.50
Compression = 0.50
Output Gain = 0.75  (+10 dB)
Mix         = 0.25  (25 %)
```

Logic Pro loaded the generated file successfully and the UADx dbx 160 showed
the expected settings.

This validates the basic editing workflow:

1. Start with a compatible CST template.
2. Locate the Base64 encoded `jucePluginState`.
3. Decode it.
4. Change each mapped `float32` value in all 32 repeated blocks.
5. Encode the state again.
6. Write it back to the CST without altering unrelated structure.
7. Load the CST in Logic Pro and verify the result.

## Included files

- `README.md`  
  Human-readable documentation.

- `logic-plugin-mappings.json`  
  Machine-readable mapping database.

- `dbx160_cst_editor.py`  
  Example Python editor for the tested dbx 160 state layout.

- `reference/UADx_dbx160_reference.cst`  
  Canonical minimal CST template containing only the UADx dbx 160.

## Example

```bash
python dbx160_cst_editor.py   reference/UADx_dbx160_reference.cst   My_dbx_Setting.cst   --threshold 0.5   --compression 0.5   --output-db 10   --mix-percent 25
```

## Recommended future repository structure

As more plugins are reverse-engineered, each plugin should ideally have:

1. a machine-readable parameter mapping,
2. at least one minimal validated reference CST,
3. documented known parameter values for that reference,
4. a successful Logic Pro validation test,
5. version/compatibility notes.

Planned mapping targets include UADx LA-3A, Manley Tube Preamp, UADx Neve 1073,
UADx Pultec and Aguilar Amp/Cab.

## Scope and caution

This is reverse-engineered experimental work. Logic Pro or plugin updates may
change serialization details. Always keep an original CST and verify generated
files in Logic Pro before relying on them in production projects.
