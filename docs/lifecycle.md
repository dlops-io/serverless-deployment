# Optional CLI setup and cleanup

These optional helpers create a separate practice stack and remove only
resources recorded in its ownership manifest. They automate the same function,
web service, runtime identities, buckets and job that students create through the
console. **Follow the console walkthrough first to learn the components.** Neither helper executes the audio job automatically.

Run from the repository root with Python 3 and a current, signed-in `gcloud` CLI.
Applied builds and deployments stream gcloud progress to the terminal.
Both helpers **print a plan by default**. Add `--apply` to make cloud changes.
The planning mode does not contact Google Cloud or create local files.

## Prerequisites

Choose a billing-enabled project where you are allowed to enable APIs, create
service accounts and buckets, deploy Cloud Run services/jobs, attach runtime
identities, and manage the relevant IAM bindings. These scripts do not grant
administrator permissions to the person running them. Organization policies
may prohibit public endpoints; the script stops on that error.

Source-based function deployment also needs an authorized Cloud Build identity.
If your project has never built a function, follow the Cloud Run source-deploy
permissions guidance before applying this script. The script enables the API
services but does not alter the build account's IAM permissions, create a key,
or change organization policies. A failed source build is journaled and can be
cleaned up using the same manifest.

See [source deployment permissions](https://docs.cloud.google.com/run/docs/deploying-source-code#permissions_required_to_deploy)
and [Cloud Run functions deployment](https://docs.cloud.google.com/run/docs/deploy-functions).

## 1. Preview and create

Use a short, unique prefix. These examples use `lecture14-demo`. The resulting
names differ from the short names in the student walkthrough to avoid colliding
with an existing tutorial deployment:

| Resource | Example name |
|---|---|
| HTTP function | `lecture14-demo-function` |
| Public web service, with speech enabled | `lecture14-demo-web` |
| Finite audio job | `lecture14-demo-audio` |
| Input bucket | `YOUR_PROJECT_ID-lecture14-demo-input` |
| Output bucket | `YOUR_PROJECT_ID-lecture14-demo-output` |
| Runtime service accounts | `lecture14-demo-function`, `lecture14-demo-web`, `lecture14-demo-job` |

```bash
python tutorial/spin_up.py \
  --project=YOUR_PROJECT_ID \
  --prefix=lecture14-demo \
  --manifest=./local-state/lecture14-demo.json
```

Read the printed commands, then repeat with `--apply`:

```bash
python tutorial/spin_up.py \
  --project=YOUR_PROJECT_ID \
  --prefix=lecture14-demo \
  --manifest=./local-state/lecture14-demo.json \
  --apply
```

Defaults match the tutorial: Toronto (`northamerica-northeast2`) for Cloud Run
and Storage, `us-central1` for the speech model, and the tutorial's published
`cgumb/ac215-translation-demo@sha256:c17b6db09f7402febb582bf327920ec9ca4eee113f5ddefa38e9da5619dbe72e` image. Override with
`--region`, `--model-location`, and `--image`. The default digest fixes the
practice stack to the image bytes tested for this tutorial; a tag can change later.
This does **not** build or publish the app image; the source-based function is built by Google Cloud.

The script enables the Cloud Run, Cloud Build, Artifact Registry, Agent Platform,
Cloud Storage, IAM and IAM Service Account Credentials APIs before inspecting
resource names, because a new project cannot inspect resources until those APIs
are available. If a name collision is found, no resources are created, but the
enabled APIs remain enabled. It uploads the
repository's example passage to `run-001/passage.txt`, creates the function from
`tutorial/function`, deploys the existing app image as a public web service,
and creates the job with the `python -m translation_demo batch` command. The
function and web service are public through `--no-invoker-iam-check`, matching
the console's **Allow public access** setting. Public invocation is separate
from the runtime identity the service uses to call other APIs. The function has
a maximum of three instances. The web service matches Part 2: maximum two instances, concurrency
four, and a 120-second request timeout.
The job has one task, no automatic retries and a five-minute task timeout.

Runtime permissions are separated:

- The function has its own identity and no added model or Storage role.
- The web account receives **Agent Platform User** (`roles/aiplatform.user`) and
  **Service Usage Consumer**. It receives no Storage permission.
- The job account receives those two API roles, **Storage Object Viewer** on
  only its input bucket, and **Storage Object Creator** on only its output bucket.

Both buckets enforce public access prevention, uniform access, Standard storage
and a seven-day soft-delete policy. They remain private. The output bucket
writer cannot read or overwrite results; your signed-in developer identity
needs its own permissions to upload inputs, execute with overrides and read
outputs.

To allow your own account to impersonate the web runtime for local development,
add `--developer-member=user:YOUR_EMAIL` to the **initial setup** invocation.
This grants **Service Account Token Creator** only on that newly created web
account. It does not sign you in or write ADC credentials. Perform the browser
login separately as described in Part 3.

## 2. Inspect and exercise

Obtain the actual public service URLs:

```bash
gcloud run services describe lecture14-demo-function \
  --project=YOUR_PROJECT_ID --region=northamerica-northeast2 \
  --format='value(status.url)'
gcloud run services describe lecture14-demo-web \
  --project=YOUR_PROJECT_ID --region=northamerica-northeast2 \
  --format='value(status.url)'
```

Open the function URL; open the web service URL, translate a short sentence,
and play the speech. Execute the job explicitly when ready:

```bash
gcloud run jobs execute lecture14-demo-audio \
  --project=YOUR_PROJECT_ID --region=northamerica-northeast2 --wait
```

Inspect the execution and its logs, then open the output bucket's `run-001/`
prefix. The unique attempt folder contains translated text, audio and a
completion manifest. To run a new local passage and download the results:

```bash
python tutorial/run_job.py tutorial/app/examples/passage.txt \
  --project=YOUR_PROJECT_ID --region=northamerica-northeast2 \
  --job=lecture14-demo-audio \
  --input-bucket=YOUR_PROJECT_ID-lecture14-demo-input \
  --output-bucket=YOUR_PROJECT_ID-lecture14-demo-output \
  --download-dir=./results
```

## 3. Preview and remove

Keep the manifest until cleanup. It contains resource names and a random
ownership token, **not credentials**. Do not publish local state in Git. The
script refuses to adopt existing resources or overwrite an existing manifest.
To create another practice stack, choose a new prefix and manifest, or remove the
old stack first and archive its completed manifest before starting again.

Preview the cleanup:

```bash
python tutorial/tear_down.py \
  --project=YOUR_PROJECT_ID \
  --manifest=./local-state/lecture14-demo.json \
  --delete-objects
```

`--delete-objects` is a separate, required acknowledgement that tutorial input
and output objects, including older object versions, will be removed with the
buckets. Without it, the helper stops before deleting any resource. Add
`--apply` after reviewing the plan:

```bash
python tutorial/tear_down.py \
  --project=YOUR_PROJECT_ID \
  --manifest=./local-state/lecture14-demo.json \
  --delete-objects --apply
```

Before any deletion, the helper checks **every remaining resource's ownership**
against its label or service-account description and the manifest. It removes
the job, services, buckets, the two added project roles for each applicable
runtime identity, and finally the service accounts. It never deletes a project,
disables APIs or searches for resources by a broad name prefix. The impersonation
binding disappears with its managed service account. Unrelated IAM bindings,
services, buckets and accounts are left alone.

Cloud Storage's soft-delete retention still applies. Deleted data can remain
recoverable and billable during that period; removal is not an immediate purge.
The script does not override a bucket retention policy or legal hold.

## Failure and recovery

The manifest is an incremental journal. Each successful resource creation or
deletion is saved. If a command fails, later commands do not run. Fix the cause
and rerun **tear_down** with that manifest to clean up partial setup; setup does
not silently resume into a mixture of existing resources. A missing resource
is skipped, while a permission or network failure stops inspection. Service
accounts are inspected through an authorized non-deleted-account list filtered to
the exact email, because IAM can return 403 when describing a soft-deleted
account. The list operation must itself succeed; a failed list operation is never treated as
absence. Deleted accounts remain subject to Google Cloud recovery retention.

A narrow interruption window exists between bucket creation and applying its
ownership label (the CLI cannot set labels on creation). If that happens,
teardown refuses to guess ownership. Inspect that exact bucket and the saved
journal before manually labeling or removing it. Never add ownership labels to
unrelated resources just to make cleanup proceed. The same refusal applies if
someone removes an ownership label or edits an account's managed description.

IAM grants retry only the specific newly-created-service-account propagation
error, for up to 31 seconds. Permission errors and other failures stop immediately.
If a runtime account was deleted outside the helper, teardown reports any
matching deleted-principal project-role entries for manual cleanup; it does
not remove unknown policy members automatically.

Source builds can create build logs, source archives and images in Google's
shared, automatically managed build repositories/buckets. Those artifacts are
**retained** because deleting an entire shared repository could remove other
work. The script also retains enabled APIs and local downloaded results. Review
Artifact Registry and build storage separately if you need to remove the
function's build artifacts; do not delete a shared repository as a shortcut.

Offline lifecycle and helper checks:

```bash
python -m unittest discover -s tutorial/tests -v
```
