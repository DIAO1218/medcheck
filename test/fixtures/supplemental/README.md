# Supplemental M4 dose cases

`m4_dose_cases.json` contains 9 synthetic case proposals for M3/M4 integration.
It is a collection with a `cases` array, not a single CLI case file. To run a
case through the CLI, save one entry as a separate JSON object and pass its path
using `--case`. The additional expected-value fields are test metadata.

The frozen 25-case set is unchanged. These cases are not yet wired into pytest
or the semantic evaluation gate. Split-dose integration expectations need M3/M4
agreement. Tablet conversion and a new ambiguous-prescription policy are outside
this set. The unsupported-frequency case follows the existing FIELD_UNPARSED
behavior already exercised by the frozen case c16.

## Initial local observations

These observations predate the M4 accumulation fix. As of November 20, M4's
tests independently verify summed doses and HOLD for an unusable schedule when
both records reach the rules layer. The default extractor still drops the second
same-name record, so the original text cases are not claimed fixed. M4 emits
`UNIT_UNSUPPORTED`; the `FIELD_UNPARSED` expectation for the ninth case requires
M3 to populate the existing extraction warning. Do not weaken that expectation
just to match the current extractor.

| Cases | Observation |
|---|---|
| `m4_split_below`, `m4_split_at_limit` | Verdict matches, but only one medication entry is extracted. These are not evidence of correct dose aggregation. |
| `m4_split_above` | Expected BLOCK; actual APPROVE. |
| `m4_twice_daily_equivalent`, `m4_grams_twice_daily` | Expected BLOCK; actual BLOCK. |
| `m4_micrograms_at_limit`, `m4_morning_only`, `m4_evening_only` | Expected APPROVE; actual APPROVE. |
| `m4_split_unparsed_frequency` | Expected HOLD; actual APPROVE. |

Future automated assertions must check the extracted entries and normalized
daily total as well as verdict and finding codes. Matching a verdict alone can
hide lost records. Repeated mentions must not automatically be interpreted as
additional administrations.
