# Notes

## Day 1: what the README says
| Battery | Discharge current | Cutoff voltage | Ambient temp |
|---|---|---|---|
| B0005 | 2 A | 2.7 V | 24 °C (checked in data) |
| B0006 | 2 A | 2.5 V | 24 °C (checked in data) |
| B0007 | 2 A | 2.2 V | 24 °C (checked in data) |
| B0018 | 2 A | 2.5 V | 24 °C (checked in data) |

Rated capacity: 2 Ah
End of life (EOL): 30% fade, 2 Ah to 1.4 Ah

Things I still need to check in the data:
- README says Capacity is "till 2.7 V", but 3 batteries have a different cutoff. Which is true?
- does B0007 ever reach 1.4 Ah?
- B0005 has 170 charge vs 168 discharge entries.
  Found: the log ends with a charge (no discharge after it),
  and charges repeat back-to-back at entries 23 and 84.
  Not fully explained yet. Count is off by about 1.
  - B0005 first discharge capacity = 1.856 Ah (confirmed in data, not 2.0)
- B0005 EOL (first capacity <= 1.4 Ah) = discharge index 124, never goes back above 1.4 after that
- B0005 test continued past EOL: 168 discharges in total, so about 43 after it. Reason not known yet.
- capacity went back up late in the test (last 1.325 vs lowest 1.287). That looks like capacity regeneration.
- B0007 lowest capacity = 1.4005 Ah at index 165, last = 1.4325 Ah. Never reaches 1.4, so no EOL observed.
- Decision (provisional, to confirm): B0007 never reaches 1.4 Ah, so it is excluded from RUL testing and kept for capacity/SoH.
## Day 2: capacity fade plot

(a) Fastest fade: B0018 reaches 1.4 Ah first (discharge 96), then B0006 (108),
    then B0005 (124). B0007 never reaches it. B0006 drops the most overall
    (2.035 Ah down to 1.154 Ah).
(b) The small upward jumps are capacity regeneration: after a rest, the battery
    reads a slightly higher capacity, so the fade line is not smooth.
    Still to check: the jumps look to be at similar cycle numbers in different
    batteries, which may come from the test schedule.

## Decisions so far
- B0007 never reaches EOL, so it is left out of RUL testing (kept for capacity/SoH).
  Provisional, to confirm.
- SoH base: rated 2.0 Ah (provisional, to confirm). Reason: one EOL rule for all
  batteries (1.4 Ah = 70% SoH). Downside: B0006 starts above 100%.

## Why answers
- Read the exact temperature from the data: the README only said "room temperature",
  and the data showed 24 C for every entry of every battery.
- Different cutoff voltages (2.7, 2.5, 2.2, 2.5 V): batteries drained further release
  more charge, so they are not measured on exactly the same scale.
- Same 2 A and 24 C: good because fewer things change, bad because the model only
  knows this one condition.
- 1.4 Ah = 2 Ah minus 30% of 2 Ah (0.6 Ah).
## EOL definition
- Capacity bounces back above 1.4 Ah after the first dip: B0018 (8 cycles, up to 1.46 Ah), B0006 (once, 1.405).
- Primary rule: EOL = first cycle <= 1.4 Ah. Check rule: "permanent" crossing (B0006 121, B0018 122).
- NASA README says tests stopped at EOL, but our data continues past the first dip. Unexplained.
- SoH = capacity / 2.0 Ah (decided). RUL = EOL cycle - current cycle. B0007 has no RUL (no EOL).
## Features
- Features = clues from the discharge curve: time to reach voltage levels, charge in voltage windows, voltage/temperature stats.
- Total discharge time is left out on purpose: capacity is current x time, so it would leak the answer.
## Feature check
- t_to_3.0 correlates 1.00 with capacity, so it nearly restates the target. Run models on all features and on a partial curve (above 3.4 V) to be honest about this.
- Total discharge time correlates only 0.95. Guess (to confirm): Capacity counts only discharge down to 2.7 V, so extra tail below 2.7 V in B0006/B0007/B0018 is not counted.