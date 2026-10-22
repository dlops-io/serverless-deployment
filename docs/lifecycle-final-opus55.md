I found no new blocking bugs, so the delta passes. I'm Claude Opus 5.5 (`claude-opus-5-5`). I made no edits and ran no cloud commands. The only gcloud call was the local `gcloud run deploy --help`.

**Account inspection** (`tutorial/lifecycle/lifecycle.py:70-87`)

- **Pagination:** this is handled. `iam service-accounts list` has no `--limit` or `--page-size`, so gcloud fetches every page and then applies `--filter`.
- **Exact match:** the `--filter=email=` result is filtered again in Python by exact email equality (`:87`). A partial filter match therefore can't be treated as present, and an unrelated account is never adopted. The test at `test_lifecycle.py:198` covers the empty, matching and unrelated cases.
- **Fails closed:** a failed list raises `RuntimeError`, and a 403 or `PERMISSION_DENIED` is never read as absence. Only a successful but empty list returns `None`. Teardown runs every ownership check before the first delete, as before.
- **Ownership:** the list output includes `description`, so `owned()` still checks the exact marker. Disabled accounts still appear in the list and stay subject to that check. Soft-deleted accounts don't appear, so they are treated as absent, which is the intended behaviour.

**Public access** (`:175`, `:180`)

`--no-invoker-iam-check` is a real flag in the installed SDK. `gcloud run deploy --help` on Google Cloud SDK 570.0.0 lists `--[no-]invoker-iam-check` with "Use … --no-invoker-iam-check to disable". The tests assert that `--allow-unauthenticated` is absent (`test_lifecycle.py:95`). With no `allUsers` binding, teardown has no public-invoker binding to clean up, because deleting the service removes the setting. `docs/lifecycle.md:78` and `:186-190` describe this behaviour accurately.

**Credentials and privileges**

These are unchanged. Projects get the same two roles and buckets the same two grants, `--developer-member` stays optional with Token Creator on the web account only, and no keys are created anywhere.

**Offline tests:** `python -m unittest discover -s tutorial/tests -q` ran 25 tests, `OK`.

**Non-blocking notes**

1. When an account list fails, `describe` still uses the shared NOT_FOUND/404 regex, so a list failing with NOT_FOUND (for example, an unknown project) would count as absence. The fix is to treat every non-zero exit as an error for `kind == 'account'`, since a successful empty list is the only real absence signal for that kind. The project regex check and the 403s gcloud gives for unknown projects make this unlikely.
2. `lifecycle-live-check.md:86-90` says the script was switched to the list path after the live teardown. The script's own list-based teardown therefore hasn't run live; only the manual exact-email listings were checked. Run one more spin-up and tear-down to close that gap.
3. The docs call it an "active-account list", but the list also returns disabled accounts, so "non-deleted" would be more precise. `README.md:200` and `:311` still use `--allow-unauthenticated` for the manual path, which is outside the lifecycle scope but inconsistent with it.