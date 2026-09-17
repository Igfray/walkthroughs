# Requirement (fixed before design, 2026-09-19)

Build an Inspect eval measuring whether a model CLAIMS SUCCESS IT DID NOT EARN:
given a transcript where a tool call FAILED, does the reply to the user admit
the failure, or does it report the task as done?

Constraints:
- Runnable by anyone: no API key needed for the self-test (mockllm).
- Scorer must be non-vacuous: proven to FAIL a fabricated-success reply.
- Out of scope: multi-turn repair, partial success.

Why this eval: it is the eval-shaped version of the defect class I keep
finding in my own product (see pantheonlabs.co.uk/evidence.html).
