# Lifecycle integration check — 2026-10-22

This is evidence for the CLI lifecycle helpers, not a claim about GIF coverage.
The check used a separate `l14-overnight` stack in `ac215-project`. Existing
`translation-demo`, `translation-audio`, tutorial buckets and their runtime
identities were left alone. No credentials or service-account keys were copied
into the image, repository, report or submitted input.

## Setup and functional checks

Applied the actual helper:

```bash
python tutorial/spin_up.py --project=ac215-project --prefix=l14-overnight \
  --manifest=local-state/l14-overnight.json --apply
```

The immutable image was
`cgumb/ac215-translation-demo@sha256:c17b6db09f7402febb582bf327920ec9ca4eee113f5ddefa38e9da5619dbe72e`.
The script created three runtime identities, two private buckets, the source-built
function, a public web service and a finite job. Every resource was journaled
as created. No pre-existing resource was adopted.

Verified against the live deployment:

| Check | Actual result |
|---|---|
| Function GET with `text=Good afternoon everyone`, `src=en`, `dest=fr` | HTTP 200, `Bonjour à tous` |
| Public web page | HTTP 200; Agent Platform labels present; obsolete Vertex AI UI label absent |
| Web translation POST | `Bonjour à tous` |
| Web speech POST using the attached runtime identity | HTTP 200, `audio/wav`; valid RIFF/WAVE; 1.451 seconds |
| Web runtime configuration | Concurrency 4, request timeout 120 seconds |
| Project IAM roles for each web/job identity | Exactly Agent Platform User and Service Usage Consumer |
| Job input grant | Storage Object Viewer on only the input bucket |
| Job output grant | Storage Object Creator on only the output bucket |
| Web identity Storage grants | None on either bucket |
| Bucket access | Uniform bucket-level access; public access prevention enforced |

Two French job executions reused `run-001/` and wrote separate attempt folders.
The matching manifest/output sets were checked locally after download:

| Execution | Output attempt under `gs://ac215-project-l14-overnight-output/` | WAV duration |
|---|---|---|
| `l14-overnight-audio-tb6n9` | `run-001/6684661877ca46768b170cd1d0a9ef1e/` | 11.091 s |
| `l14-overnight-audio-kdx6s` | `run-001/e3cced31146a4da097c6ffb2da4d6866/` | 11.291 s |

Each attempt contained nonempty `translated.txt`, valid `speech.wav`, and a
`manifest.json` with `status: complete` and the matching execution name. This
also verified that rerunning the job did not overwrite the earlier attempt.

Then ran the real helper, without `--dry-run`:

```bash
python tutorial/run_job.py tutorial/app/examples/passage.txt \
  --project=ac215-project --region=northamerica-northeast2 \
  --job=l14-overnight-audio \
  --input-bucket=ac215-project-l14-overnight-input \
  --output-bucket=ac215-project-l14-overnight-output \
  --dest=es --download-dir=local-state/l14-overnight-helper-results
```

It uploaded the passage, executed with overrides, waited, downloaded results,
and validated the complete set. The matching execution was
`l14-overnight-audio-k6wc9`; the output was
`run-20261022-053100-607973a8d939/53e7686e3d124171b24da0d4009d34d5/`.
The Spanish speech WAV was 12.811 seconds.

The completed integration probe finished at 05:31:34 UTC on 2026-10-22.

## Cleanup and independent verification

Previewed the command plan, then applied:

```bash
python tutorial/tear_down.py --project=ac215-project \
  --manifest=local-state/l14-overnight.json --delete-objects --apply
```

Teardown completed successfully. Independently checked every one of its eight
managed resources: the job, both services, both buckets and all three active
service accounts were absent. The project IAM policy had no members containing
these runtime-account names. All eight manifest entries were `deleted` and
`torn_down` was true. APIs and shared source-build artifacts remain as documented;
Storage and IAM recovery retention still applies to deleted resources.

Verification used successful active-account listings filtered to exact emails.
A direct IAM `describe` after deletion returned a 403, which cannot distinguish
a missing account from insufficient access; the script now uses the authorized
list operation for account inspection. A failed list operation still stops the
script. It never treats permission failure as absence.

## Corrections exercised by this check

- Missing Cloud Run resources produce `Cannot find service [...]` / `Cannot find
  job [...]`; those exact messages are covered by offline tests and live setup.
- The web service's maximum instances, concurrency and timeout match Part 2.
- IAM grant retry is limited to the specific new-principal propagation error;
  generic 403 errors are never retried. This live setup required no IAM retry.
- The default image is immutable and displays current product naming.
- `gcloud storage cp --recursive` requires an existing local destination.
  The main README already included `mkdir -p results`; the supporting
  `docs/job-workflow.md` example was corrected to include it too. The job helper
  already creates its destination.
- `global` is accepted as a model location; the lifecycle package has an
  `__init__.py` to avoid import shadowing.

Offline validation: `python -m unittest discover -s tutorial/tests -q` passed
25 tests (20 lifecycle checks and five job-helper checks). No commit or push was
attempted; the user is asleep and signing requires their unlock.

## Same-prefix recreation and interrupted-setup recovery

A second setup used the same project and prefix after archiving the first
completed journal. Exact-email active-account preflight succeeded after the
first accounts were deleted. All three accounts and both buckets were recreated
with the same names and a new ownership token; the source function became
`Ready=True` with that token. This confirms that recovery-retained objects do
not prevent the active-name inspection used by the helper.

The local second setup process exited with SIGTERM (143) during the function
step; the cause was not established. The cloud deployment had completed, but
the journal correctly retained the function as `creating`, with web service and
job still `planned`. This second attempt is **not** counted as a complete second
setup. It exercised real interrupted-setup cleanup instead.

Before cleanup, tested the current public-access representation on that function:

```bash
gcloud run services update l14-overnight-function \
  --project=ac215-project --region=northamerica-northeast2 \
  --no-invoker-iam-check
```

Removed the owned function's earlier `allUsers` invoker binding, then verified
`run.googleapis.com/invoker-iam-disabled=true`, no `allUsers` IAM binding,
unchanged dedicated runtime identity, and an anonymous HTTP 200 returning
`Bonjour à tous`. The lifecycle helpers now deploy both function and web service
with `--no-invoker-iam-check`, matching **Allow public access** in the current
console. The first full cycle used the earlier equivalent public IAM binding;
the new flag was tested directly on the recreated function, not through a third
complete stack build.

Applied teardown to the partial journal. It successfully removed the owned
function despite its `creating` journal state, both buckets, all runtime project
roles and all three accounts. It skipped the never-created web service and job.
Independent final verification again found **all eight names absent as active
resources**, no matching project IAM members, and the manifest marked
`torn_down`. The completed first-cycle journal is preserved locally as
`local-state/l14-overnight-cycle1.json`; partial-cycle cleanup is recorded in
`local-state/l14-overnight.json`. Neither is committed.

Applied non-IAM commands now stream gcloud's build/deploy progress, so a long
operation is visible rather than hidden behind captured output. IAM add-binding
commands retain captured output only to recognize the bounded propagation retry.
