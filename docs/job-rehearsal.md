# Batch job rehearsal

The public image `cgumb/ac215-translation-demo:lecture14-batch-50d8201` supports
both the web service and the batch command. Its digest is
`sha256:a1d4858aca190421b8aabeb0d5fcc6fda0d0902486ca5f34319adcf42453c6e6`.
An anonymous Docker pull succeeded. The existing service was updated to this
same image; startup command is what distinguishes service and job behavior.

## Teaching resources

- Project: `ac215-project`
- Job: `translation-audio`
- Job region: `northamerica-northeast2`
- Model location: `us-central1`
- Runtime identity: `translation-audio-job@ac215-project.iam.gserviceaccount.com`
- Private input bucket: `ac215-project-lecture14-input`
- Private output bucket: `ac215-project-lecture14-output`
- Execution settings: one task, zero retries, five-minute timeout, 512 MiB, one CPU.

The job identity has Vertex AI User and Service Usage Consumer on the project,
Object Viewer on the input bucket, and Object Creator on the output bucket.
The web-service account has no added Storage access. The buckets use uniform
access and public access prevention. Students create their own buckets and job
identity; they only share the public image.

The first execution read the sample passage from
`gs://ac215-project-lecture14-input/rehearsal-001/passage.txt`, translated it to
French, generated speech, wrote its artifacts under
`gs://ac215-project-lecture14-output/rehearsal-001/`, and exited successfully.
The downloaded artifacts were verified: the manifest reports completion, the
translated text contains the full passage, and the WAV is mono 24 kHz audio
lasting about eleven seconds. The passage was processed as a whole, not line by
line or in parallel. The web UI, translation, and speech routes also passed
live HTTP checks after deploying this same image to the service.

[Open the cloud job](https://console.cloud.google.com/run/jobs/details/northamerica-northeast2/translation-audio?project=ac215-project)

[Browse the saved outputs](https://console.cloud.google.com/storage/browser/ac215-project-lecture14-output/rehearsal-001?project=ac215-project)

The [student walkthrough](job-workflow.md) gives the full setup, console argument
fields, and CLI upload/execute/download sequence. A console button-click run has
not been claimed as verified; the underlying job was executed through gcloud.

A second terminal submission uploaded a different local text file under
`rehearsal-002`, executed the existing job with complete argument overrides
(including Spanish as the destination), and also completed successfully.
This verifies the upload-then-execute workflow without creating a new job.

The local helper was then tested end to end with a new short text file. One
invocation uploaded it, executed the cloud job with its input/output paths,
waited for successful completion, downloaded the resulting attempt folder, and
verified that a completion manifest, translated text, and WAV audio were present.
The downloaded WAV was separately inspected as 24 kHz audio. Five offline helper
checks cover dry-run, upload failure, execution failure, successful download,
and skipping download. The seventeen application checks remain separate.

## Cleanup after teaching

Keep the resources available for rehearsal until the instructor is finished.
Afterward, delete the named job and service through Cloud Run if no longer needed,
then delete the tutorial input/output objects and buckets through Storage.
Delete the two dedicated runtime accounts when they are no longer attached to
anything. Remove obsolete image tags and the private rehearsal copy separately.
The public Docker Hub tag is a course dependency; retain it while students use it.
No cleanup or deletion has been performed by this rehearsal.
