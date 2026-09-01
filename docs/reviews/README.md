# External Review Records

This directory preserves point-in-time external technical reviews used as
release checkpoints.

Review reports are historical audit artifacts, not normative project
specifications. A finding in an earlier report may be superseded by a later
remediation/follow-up report. Current behavior is defined by the code, tests,
and active design/roadmap documentation.

For the 0.2 engine checkpoint, read these together:

1. `0.2-external-review.md`
2. `0.2-remediation-follow-up.md`
3. `0.2.0-release-candidate-review.md`
4. `0.2.0-remediation-follow-up.md`

The release-candidate review required focused remediation. The subsequent
follow-up independently verified the release-blocking findings as resolved and
cleared the project to proceed with the final 0.2.0 release audit.

For the first 0.3 consumer-API checkpoint, read these together:

1. `0.3-consumer-api-pass-1.md`
2. `0.3-consumer-api-pass-2.md`
3. `0.3-consumer-api-remediation-follow-up.md`

The first two records preserve the independent discovery and focused reviews
of the original slice plus the maintainer's finding-by-finding adjudication.
The remediation follow-up independently verified all four findings as closed,
found no new defect, and cleared that bounded consumer-facade checkpoint.

For the 0.3 source-reporting/provenance API checkpoint, read these together:

1. `0.3-source-reporting-pass-1.md`
2. `0.3-source-reporting-pass-2.md`

The discovery and focused reviews found no scientific or runtime defect. They
identified an unexported public typing alias and incomplete migration guidance
for the published pH contracts. Both findings are remediated in the current
development tree but require a focused external follow-up before the checkpoint
is closed.
