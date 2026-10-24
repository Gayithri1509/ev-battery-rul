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