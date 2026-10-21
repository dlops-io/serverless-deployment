# Part 4: console and CLI workflow design

The batch CLI supports both `--text-file` (inside the container) and `--input-uri`
(Cloud Storage). It reuses the web app's translation and Vertex speech adapters.
`--plan` describes work without network calls. A real run writes translated text,
WAV audio, and a completion manifest to a unique attempt folder, then exits.

## One-time setup in each student's project

- Enable the required Cloud Run, Vertex AI, and Cloud Storage APIs and billing.
- Create private input/output buckets with globally unique names. If using one
  bucket instead, explain that its granted read/write permissions apply there.
- Create a job runtime service account. Grant input-object read access on the
  input bucket, object creation on the output bucket, and the required Vertex AI
  inference permission. Use bucket-level grants rather than project-wide storage
  administration. Keep the public web service's identity separate.
- Ensure the student's CLI identity can upload source text, execute the job with
  overrides, and read results. These are not the runtime identity's permissions.
- Create a Cloud Run job from the tested published image. Set its command to
  `python` and arguments as below. Attach the job service account. Use one task;
  select timeout and retry settings deliberately. Verify retry-safe outputs
  before enabling retries. Set model/project/region configuration separately.

The image is shared; students supply their own job/project/storage configuration.
The instructor can prepare their own resources before lecture, but students
following along still need explicit setup instructions for theirs.

### Equivalent setup commands

Choose globally unique bucket names; the names below are placeholders. This is
one-time setup, not work repeated for every passage. The instructor can show the
same actions through **Storage → Buckets → Create** and each bucket's
**Permissions → Grant access**. Use uniform bucket access and keep both buckets
private. The public UI's runtime identity does not receive these Storage roles.

```bash
PROJECT_ID=YOUR_PROJECT_ID
REGION=northamerica-northeast2
INPUT_BUCKET=YOUR_GLOBALLY_UNIQUE_INPUT_BUCKET
OUTPUT_BUCKET=YOUR_GLOBALLY_UNIQUE_OUTPUT_BUCKET
JOB_ACCOUNT=translation-audio-job
JOB_EMAIL="${JOB_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"
IMAGE=PUBLIC_IMAGE_ADDRESS

gcloud services enable run.googleapis.com aiplatform.googleapis.com storage.googleapis.com \
  --project="$PROJECT_ID"
gcloud storage buckets create "gs://$INPUT_BUCKET" --project="$PROJECT_ID" \
  --location="$REGION" --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets create "gs://$OUTPUT_BUCKET" --project="$PROJECT_ID" \
  --location="$REGION" --uniform-bucket-level-access --public-access-prevention
gcloud iam service-accounts create "$JOB_ACCOUNT" --project="$PROJECT_ID"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$JOB_EMAIL" --role=roles/aiplatform.user --condition=None
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$JOB_EMAIL" --role=roles/serviceusage.serviceUsageConsumer --condition=None
gcloud storage buckets add-iam-policy-binding "gs://$INPUT_BUCKET" \
  --member="serviceAccount:$JOB_EMAIL" --role=roles/storage.objectViewer
gcloud storage buckets add-iam-policy-binding "gs://$OUTPUT_BUCKET" \
  --member="serviceAccount:$JOB_EMAIL" --role=roles/storage.objectCreator
```

The deployer must also be able to attach the job account (Service Account User),
and the caller needs Cloud Run execution permission. Executing with argument
overrides requires `run.jobs.runWithOverrides`; Cloud Run Jobs Executor With
Overrides supplies that role. These caller permissions are separate from what
the container itself can do. A project administrator can grant these permissions
when a student is not already authorized.

Create the job after uploading its initial passage. In the console, use **Cloud
Run → Jobs → Create job**, choose the image and runtime account, and enter command
`python`. Set `ENABLE_SPEECH=true`, your `GOOGLE_CLOUD_PROJECT`, and model location
`GOOGLE_CLOUD_LOCATION=us-central1`. Use one task, zero retries, and a five-minute
task timeout for the initial rehearsal. The equivalent CLI is:

```bash
gcloud storage cp ./passage.txt "gs://$INPUT_BUCKET/run-001/passage.txt" --project="$PROJECT_ID"
gcloud run jobs create translation-audio --project="$PROJECT_ID" --region="$REGION" \
  --image="$IMAGE" --service-account="$JOB_EMAIL" --command=python \
  --args="-m,translation_demo,batch,--input-uri,gs://$INPUT_BUCKET/run-001/passage.txt,--src,en,--dest,fr,--output-uri,gs://$OUTPUT_BUCKET/run-001/" \
  --set-env-vars="ENABLE_SPEECH=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1" \
  --tasks=1 --max-retries=0 --task-timeout=300 --memory=512Mi --cpu=1
```

## First, show a console execution

Upload a text file to the input bucket using the Storage console. For the job,
use the following individual container arguments, replacing the placeholders:

```text
-m
translation_demo
batch
--input-uri
gs://INPUT_BUCKET/run-001/passage.txt
--src
en
--dest
fr
--output-uri
gs://OUTPUT_BUCKET/run-001/
```

Run it. Inspect execution status and logs, then retrieve `translated.txt`,
`speech.wav`, and `manifest.json` from the unique attempt folder under the output
prefix. A manifest with `status: complete` is written last; missing manifests
mean that an attempt did not finish, even if some files exist. Do not expect the job to expose a web-app URL.
Use a new prefix for every independently submitted run. Every attempt also adds
a unique child folder and creates objects with generation preconditions, so
retries cannot overwrite earlier files. Retries can still duplicate paid API
work and leave incomplete attempt folders; they do not provide exactly-once
processing. Keep retries off for the first demo.

Use a short UTF-8 passage. The demo accepts at most 5,000 source characters and
4,000 UTF-8 bytes of translated speech input. It processes the passage as a whole,
sequentially; arbitrary long documents and parallel chunking are future work.

## Then, run from the laptop terminal

Once the job exists, ordinary GCP CLI commands can submit new work:

```bash
gcloud storage cp ./passage.txt gs://INPUT_BUCKET/run-002/passage.txt \
  --project=YOUR_PROJECT_ID

gcloud run jobs execute translation-audio \
  --project=YOUR_PROJECT_ID \
  --region=YOUR_REGION \
  --args=-m,translation_demo,batch,--input-uri,gs://INPUT_BUCKET/run-002/passage.txt,--src,en,--dest,fr,--output-uri,gs://OUTPUT_BUCKET/run-002/ \
  --wait

gcloud storage cp --recursive gs://OUTPUT_BUCKET/run-002 ./results \
  --project=YOUR_PROJECT_ID
```

The execute example assumes the job's command is already `python`; argument
overrides replace its complete argument list for that execution. Arguments are
comma-separated here, so avoid commas in these example object paths. `--wait`
waits for completion; it does not stream the application logs. The download
command is a separate step. Skip it if execution fails and inspect the job logs.

CLI authentication uses the gcloud caller's login, not necessarily the ADC used
by locally running Python. In the cloud, the job obtains ADC from its attached
runtime identity. No developer credential files are uploaded with the text.

## Optional convenience helper

After demonstrating the two explicit submission commands, a local helper could:

1. Accept a local text-file path, target language, project, region, job, and buckets.
2. Allocate a fresh run prefix and upload the file.
3. Execute the existing job with that input URI and output prefix.
4. Report execution status and the output location; optionally download results.

It should stop on upload or execution failure and never silently overwrite output.
This helper is a convenience layer around GCP CLI calls, not another deployed
web service. Implement and test it only after the underlying workflow works.

References: [storage cp](https://docs.cloud.google.com/sdk/gcloud/reference/storage/cp),
[jobs execute](https://docs.cloud.google.com/sdk/gcloud/reference/run/jobs/execute).
