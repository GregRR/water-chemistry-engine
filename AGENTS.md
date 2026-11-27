# Water Chemistry Engine

## Scientific changes

- For changes to calculations or data semantics, consult the relevant section of the [scientific design](docs/WATER_CHEM_DESIGN.md). For changes to public interfaces, check the [consumer contract](docs/CONSUMER_API.md). Resolve conflicts among active design decisions, code, and tests before changing behavior.
- Trace new quantitative rules to primary or authoritative sources. Record the evidence, assumptions, and limits in the [source register](docs/WATER_CHEM_REFERENCES.md). Where evidence is insufficient, preserve the unknown or defer the calculation.
- Test scientific changes against an independent reference calculation, published example, or checkable invariant. Cover affected boundaries and unsupported inputs. Update the affected documentation in the same change.

## Validation and review

- Before committing, run `git diff --check`. For code changes, run the applicable [CI checks](.github/workflows/ci.yml) in a locked environment. Mirror the full runtime matrix for compatibility-sensitive changes and release candidates.
- Review the accumulated code and science after each coherent implementation slice. Resolve confirmed issues before starting dependent work.
- Pause for independent scientific and code review when completing a substantial model, changing the public API or core data semantics, finishing a milestone or significant remediation, or preparing a release candidate. Keep review reports and finding dispositions private in the ignored `notes-and-references/reviews/` directory. Never stage or force-add those files. Add regression tests for confirmed bugs.

## Commits

Follow Conventional Commits format.

```text
<type>[optional scope]: <description>

[optional body]
```

## Releases and shared history

- Before tagging, confirm green CI on the exact pushed candidate. Check the publish configuration and inspect wheel and sdist contents and metadata for obsolete packages or local files. Install the wheel outside the checkout on the minimum supported Python version and run the README quickstart and a representative calculation. When practical, build from the sdist and compare package metadata.
- Obtain explicit user approval before rewriting shared history, force-pushing, tagging, publishing, or creating a release. After publication, verify the public package from a fresh environment.
