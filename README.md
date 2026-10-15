# Hermit build and validation

This is the private build repository, not a game submission. It contains all
checking code. Submission source repositories and final images retain only their
production files. Nothing in this workflow commits changes back to the source.

## First run

1. Keep this repository private.
2. Create a fine-grained personal access token in GitHub Settings > Developer
   settings > Personal access tokens > Fine-grained tokens. Choose the owner of
   the submission repositories, select only those repositories, and grant
   **Contents: Read-only** (Metadata read is automatic). No source write access
   or package permissions are required for this token. Use a short expiry.
3. In this build repository's Settings > Secrets and variables > Actions, create
   a repository secret named **SUBMISSION_READ_TOKEN** containing that token.
   Never paste it into code, logs, README, chat, or a committed file.
4. Review targets.json. It currently points to the local source repository and
   exact committed SHA discovered during preparation. Each directory is relative
   to that repository root. If using three independent repositories, set each
   repository and full revision separately and set its directory to `.`.
5. Commit and push this repository's workflow/scripts/checkers/config.
6. Open Actions > Build and validate Hermit submissions > Run workflow. Leave
   **publish_ghcr unchecked**. This builds and checks only; no image is published.
7. Inspect all three jobs. Download their small report artifacts and review
   validation.json and protocol.log. Red jobs are failures even if another game
   passed. Build output is in build.log. Artifacts expire after three days.

The private source checkout requires a separate read token because GITHUB_TOKEN
is normally limited to the build repository. No Docker/WSL installation is needed
on the participant's computer. Workflow files use the current documented
actions/checkout v6 and upload-artifact v7 interfaces.

## Current source configuration

The detected source is Apoorv-Bhardwaj/triad_tactics at
7ce9f7fc171c00af38a55fae747bddda3ff97daa, with chess/, uno/, bluff/ subdirectories.
The supplied rules.txt requests three separate private SDK repositories. The
builder can validate this combined source layout, but it does not waive that
submission requirement. Update targets.json when the final repos/commits change.

## What the workflow does

- Runs only on manual dispatch, not every commit/PR.
- Uses standard Ubuntu 24.04 hosted runners, capped at 20 minutes per game.
- Pulls CPU Python parents, then builds each exact checked-out source offline
  with --network=none --pull=false for Linux/amd64.
- Validates image platform, user, card runtime labels, and card image size.
- Mounts external checkers read-only; containers have no network, a read-only
  root, restricted CPU/RAM/PIDs and bounded /tmp.
- Runs the actual production entry point in subprocess lifecycle checks.
- Chess uses a fake inference gateway for both colors with the real manifest
  configuration. This does not prove live organizer-model compatibility or strength.
- Records source SHA and image ID, and rejects source changes after checking.
- Uploads small logs, not model/image tarballs, with three-day retention.

The checker copies come from the supplied SDK files. Only the driver that injects
the submitted harness configuration is participant tooling. The production SDK
runner and final decision/evidence contract are unchanged.

## Optional publication, only after registry acceptance

Once the organizers confirm GHCR is accepted, rerun with publish_ghcr checked.
Only UNO and Bluff images are pushed, after their checks pass, to:

- ghcr.io/apoorv-bhardwaj/hermit-uno:SOURCE_COMMIT
- ghcr.io/apoorv-bhardwaj/hermit-bluff:SOURCE_COMMIT

Publication uses the build job's GITHUB_TOKEN with packages:write, not the source
read token. Never make the source repositories public to bypass authentication.
Give organizers pull access to private packages according to the announced intake
process; GitHub repository collaborator access alone may not grant registry access.
An existing package may need this build repository granted Actions write access.
The published immutable repository@sha256 reference appears in the Actions job
summary and published.json. Publication does not itself register a submission.

If a different registry is required, do not enable this option; configure that
registry separately. No registry publishing or workflow execution has been done
by preparing these files.

## Cost controls

Use remaining included standard Linux runner minutes, inspect your account's
Actions usage/budgets, and do not enable paid overages. There are no scheduled
workflows, large runner jobs, container tar artifacts or dependency caches here.
