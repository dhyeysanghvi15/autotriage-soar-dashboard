# Block IP (Mock)

## Goal
Reduce exposure by blocking a known-bad or suspicious IP address.

## Steps
1. Validate the IP is not a critical dependency.
2. Add a block rule to your firewall / proxy / EDR policy.
3. Search for other events involving the IP (lateral movement, C2).
4. Document the change and monitor for regression.

