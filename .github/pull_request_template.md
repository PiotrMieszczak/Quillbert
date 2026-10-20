## Description

<!-- What changed and why. Link the ADR if this makes or reverses a decision. -->

## How to test

<!-- The commands you actually ran, and what to look at. -->

## Notes

<!-- Deferred work, known gaps, anything you want a second opinion on. Delete if none. -->

## Definition of done

- [ ] Docs updated in the same commit, or no doc change needed
- [ ] Tokens only — no hardcoded colours, radii, or shadows ([ADR-0004](../docs/adr/adr-0004-css-modules-over-tailwind.md))
- [ ] Architectural boundaries intact — ingestion calls no generative model, model access goes through the Gateway, queries scoped by `campaign_id`
- [ ] Build and lint pass locally
