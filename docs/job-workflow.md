# Part 4: console and CLI workflow design

**Proposed interface, not yet implemented end to end.** The scaffold currently
accepts `--text-file` for a file inside the image, and only plans work. The
`--input-uri` option below must be implemented along with Vertex AI speech and
artifact uploads before this becomes a runnable student tutorial. No helper or
new published image is available yet.

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

Run it. Inspect execution status and logs, then retrieve translated text and
audio from the output prefix. Do not expect the job to expose a web-app URL.
Use a new prefix for every independently submitted run.

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
