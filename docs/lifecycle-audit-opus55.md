I'm Claude Opus 5.5 (`claude-opus-5-5`). This audit was read-only: I ran no cloud commands and edited no files. Everything I ran was local: the offline test suites (14/14 and 19/19 pass), a plan-mode `spin_up.py`, a Python harness that fed real gcloud error text into `describe()`, and reads of the gcloud 570.0.0 source in the Nix store.

**Top finding: `spin_up.py --apply` cannot succeed on a fresh stack, and teardown cannot recover from the failed function build that the docs describe.**

## Bugs, in priority order

**1. Cloud Run "not found" is treated as an inspection failure** (`tutorial/lifecycle/lifecycle.py:51`). gcloud 570 reports a missing service as `Cannot find service [{}]` (`surface/run/services/describe.py:114`) and a missing job as `Cannot find job [{}].` (`surface/run/jobs/describe.py:87`). Neither message matches `NOT_FOUND|\bnot found\b|does not exist|status=404|HTTPError 404`. I fed both strings to `Cloud.describe()` and both raised `RuntimeError: Cannot inspect resource`. Two failures follow from that:
- **Setup:** the collision loop (`:90-92`) describes `{prefix}-function`. On a fresh stack it doesn't exist yet, so `--apply` always stops there. By then the APIs are already enabled, and no manifest has been written.
- **Teardown:** a service left in the `creating` state by a failed source build was never created. Describing it raises, which blocks every deletion. That is exactly the recovery path in `docs/lifecycle.md:25-26` and `:178-182`.

**Fix:** add `Cannot find (service|job) \[` to the regex. Also add a test that patches `subprocess.run` with that exact stderr. `FakeCloud.describe` bypasses the regex, which is why all 14 tests pass with this bug in place.

**2. The web service settings differ from the tutorial** (`lifecycle.py:145-149`). The README (`:311-312`) deploys with `--max-instances=2 --concurrency=4 --timeout=120`. The script uses `--max-instances=3` and leaves concurrency and timeout at Cloud Run's defaults (80 and 300 s). The image runs gunicorn with 1 worker, 4 threads and `--timeout 90` (`__main__.py`). With concurrency 80, one instance accepts up to 80 requests it can only serve 4 at a time, so this rehearsal stack behaves differently from what students deploy. **Fix:** copy the README flags exactly and update `docs/lifecycle.md:78`, which says "maximum of three instances".

**3. Project IAM bindings on a just-created service account can fail from propagation lag** (`lifecycle.py:119-122`). The bindings run immediately after the account is created. I haven't reproduced this here, but IAM commonly rejects bindings for a newly created account with "Service account … does not exist" for a few seconds. When that happens, setup stops and the only recovery is teardown followed by a new manifest. Running teardown at that point is blocked by bug 1. The bucket bindings at `:131` and the Token Creator grant at `:134` have the same exposure. **Fix:** retry these specific binding mutations with backoff when stderr matches that message, or poll `describe('account', …)` after each create. A `--apply` run in a fresh project would show whether the error occurs.

**4. The unlabeled-bucket window needs manual recovery** (`lifecycle.py:105-106`). I confirmed the docs' claim that `gcloud storage buckets create` has no label flag in 570. If `buckets update --update-labels` fails, the bucket stays in `creating` without the owner label, and teardown refuses it (by design, `docs/lifecycle.md:184-189`). A cheap improvement keeps the safety boundary: in teardown, for a `creating` bucket with no labels, retry the label step only if the bucket's `metageneration == 1` and its `timeCreated` is later than a `created_at` timestamp written to the manifest. Without that, the documented manual step stands, which is acceptable.

**5. Orphaned project bindings when an account disappears out of band** (`lifecycle.py:204-205, 213-215`). If a runtime account is gone before teardown, it's marked `deleted` and its `roles/aiplatform.user` and `serviceUsageConsumer` bindings are never read. They stay in the policy as `deleted:serviceAccount:…`. This leaks permissions entries but deletes nothing wrongly. **Fix:** when an account is absent, still scan the policy for `deleted:serviceAccount:<email>?uid=` members with these two roles and print them for manual removal. Don't remove them automatically.

**6. The default image is a mutable tag** (`lifecycle.py:13`). The repo already pins `sha256:c17b6db0…` for `lecture14-agent-platform-20261022` (`README.md:1013`, `tutorial/app/README.md:236`). Using `cgumb/ac215-translation-demo@sha256:c17b…` as the default makes repeated rehearsals deploy the same bytes, and the image regex at `:272` already accepts `@`. The working-tree app changes are only "Vertex AI" → "Agent Platform" strings. The current default tag now matches every README reference. Earlier in this audit it was `lecture14-batch-50d8201`, which would have shown the old UI strings, but the file changed while I was reading it.

**7. `--model-location=global` is rejected** (`lifecycle.py:269`). The location regex requires a hyphen, but `speech.py` supports `global`. **Fix:** allow `global` explicitly.

**8. The `lifecycle` package can be shadowed** (`spin_up.py:3`, `tear_down.py:3`). `tutorial/lifecycle/` has no `__init__.py`, so it imports as a namespace package. Any regular package or module named `lifecycle` elsewhere on `sys.path` takes precedence. **Fix:** add an empty `__init__.py`.

## Checked and correct

**Destructive boundaries hold.**
- Teardown checks that the manifest project matches `--project` and rebuilds the full expected name set from project and prefix (`:166-186`), so a tampered manifest can't name an unrelated resource.
- It checks ownership of every remaining resource before the first delete (`:201-208`), and items still `planned` are never touched.
- It requires the separate `--delete-objects` acknowledgement.
- Project role removal only touches the owned account's unconditional bindings, and only for roles it actually reads from the live policy.
- Deletion runs job → service → bucket → bindings → account, and the manifest is saved after each step.
- 403 messages ("or it may not exist") don't match the absence regex, so permission failures stop the run rather than being read as absence.

**The commands match the tutorial except for bug 2.**
- The bucket flags (`--public-access-prevention`, `--uniform-bucket-level-access`, `--default-storage-class`, `--soft-delete-duration`) all exist in 570.
- `storage rm --recursive` on `gs://bucket` deletes the bucket too (`surface/storage/rm.py:103-104`).
- The function deploy matches `README.md:197-200` and adds its own role-less identity. `tutorial/function` contains only `main.py` and `requirements.txt`.
- The job command, args, env, retries, timeout and resources match `README.md:771-773`.
- The IAM scopes match the console steps.
- Object Creator is enough for the output bucket because `storage.py:46,54` writes with `if_generation_match=0`.

Plan mode makes no subprocess calls and writes no manifest, and the test suite covers that.

Fix bug 1 first, then do one `--apply` setup and teardown in a scratch project. That run is the evidence that would confirm or rule out bug 3.