# Serverless deployment: four teaching steps

**Development branch.** This is the proposed AC215 lecture 14 tutorial. New
examples are under development. The [original tutorial](docs/original-tutorial.md)
and existing top-level code remain available.

The story: deploy a function, share a locally tested web app, authorize it to call
a cloud model, then run the same processing as an unattended job. Each step
introduces one main idea. A UI does not require a custom container; we use a
container because we already have a packaged application to deploy.

| Part | New idea | Result | Runtime access |
| --- | --- | --- | --- |
| 1. Function | Supply handler and dependencies | Translation at an HTTP URL | Existing translation provider |
| 2. Container service | Deploy a locally tested image | Translation UI with language selectors | Same translation provider |
| 3. Service account | Authorize a cloud model call | Play translated speech in the browser | Vertex AI inference |
| 4. Job | Finish finite work and retain output | Translated text and audio in a bucket | Vertex AI inference + writes to one bucket |

## Running App as Cloud Function

Part 1 uses [`tutorial/function/`](tutorial/function/). In the intended,
billing-enabled project, open **Cloud Run → Write a function**. Select a supported
Python runtime (rehearse with Python 3.12), set the entry point to `hello_http`, and
provide `main.py` and `requirements.txt`. The original Python 3.10 instruction is
stale. Allow public invocation for this demo if project policy permits it.

Deploy, copy **your service URL** from service details, and open it first without
parameters. Then supply `text`, `src`, and `dest` query parameters:

```text
?text=Good%20afternoon%20everyone&src=en&dest=fr
```

Google builds an image from the source, stores it in Artifact Registry, and deploys
a service. Dependency installation happens during the build, not per request.
Show the build log, then verify a real translation and its request log. Build
success does not by itself establish application success.

The Python library calls an external translation web service. We are not training
or hosting that model. Rehearse a response-only fallback if the provider fails.

## Running App in Cloud Run

Part 2 uses [`tutorial/app/`](tutorial/app/). First run the UI locally: two text
boxes, source and destination language selectors, and a Translate button. Build
and publish its image, then deploy the same image to a Cloud Run **service**.
Repeat the same translation at the hosted URL.

Motivation: "It works on my laptop; how do I share it?" HTML does not inherently
require a custom image. A browser page stays visible without its application
instance continuously running. Inspect the image reference, revision, and logs.

## Part 3: authorize speech generation

Keep the same web app and translation provider. Add a **Play audio** button. The
service calls Gemini TTS through Vertex AI and returns audio directly to the
browser. No output bucket is needed for this interactive example.

Attach a dedicated runtime service account with the required Vertex AI inference
permission. Use Application Default Credentials from that attached identity, not
a key file baked into the image. Validate model and region availability, API
enablement, billing, quotas, audio format, and playback during rehearsal.

Separate who may invoke the service from what the running service may access.
Service accounts are runtime identities, not features exclusive to jobs.

### How was this developed before deployment?

Pause here to explain the development workflow, before the prebuilt app feels
like magic. The developer runs the same Python application on a laptop and calls
Vertex AI using **Application Default Credentials (ADC)**. Start with developer
credentials, or impersonate the intended runtime service account to test its
permissions. Edit, run, and debug locally; do not rebuild and publish on every edit.

Then test the packaged container locally, publish the tested image, and attach
the runtime service account when deploying it. The client library discovers ADC
in both environments: local credentials during development, attached identity
in Cloud Run. A CLI login, application ADC, and the deployed runtime identity are
different things; choosing a project does not give the application credentials.

This is an explanation plus an optional short local demonstration, not a required
detour through every Dockerfile or authentication detail. Show a small local API
call if time allows. The [local development guide](tutorial/app/README.md#local-development-against-gcp)
has commands for ADC login, impersonation, permissions, quota-project setup, and
credential mounts for local containers. No credentials belong in the image.
Local success still needs a final check of deployed identity and networking.

**Implementation status:** the Vertex AI speech adapter and browser WAV playback
are implemented and covered by offline checks. Enable speech explicitly after
configuring ADC or a runtime identity. A real Vertex call using impersonated ADC
has returned valid WAV audio both from local Python and through the local
container HTTP route. Browser playback and Cloud Run deployment
still need rehearsal; do not present those as verified yet. The
[application guide](tutorial/app/README.md#create-the-runtime-identity-console-or-cli)
shows both console setup and equivalent service-account/IAM CLI commands.

## Part 4: make a translated audio edition as a job

Use a short supplied passage, such as the [original sample](tutorial/app/examples/passage.txt).
Translate the complete passage, synthesize speech with the same provider as part
3, save text and audio to Cloud Storage, and exit. Outputs persist after the
container stops; no browser waits for completion.

Use the **same application image**, changing its startup command from web server
to batch CLI. Cloud Run jobs execute container processes to completion; they do
not use the HTTP function's "Write a function" path.

Give the job a separate runtime service account with Vertex AI inference access
and permission to read the input bucket and create objects **in the particular
output bucket**. Candidates are `roles/storage.objectViewer` on the input bucket
and `roles/storage.objectCreator` on the output bucket. The latter cannot overwrite
existing objects. Use a
fresh output prefix and settle retry behavior before enabling uploads. The person
retrieving outputs needs separate read access. Files need not be public.

### Set up once, then run from the console or terminal

Students use their own GCP project and storage, not the instructor's buckets.
They share our published image; project IDs, bucket paths, and service accounts
are supplied as configuration. No student rebuild is needed.

1. **One-time setup:** create the input/output buckets, configure the job identity
   with the three access requirements above, and create a Cloud Run job using the
   published image and batch command. Also establish the student's permission to
   upload input, launch job executions (including argument overrides), and retrieve
   results. Keep caller permissions distinct from the job's runtime permissions.
2. **Console demonstration:** upload a text file, supply its Cloud Storage URI and
   a fresh output prefix as job arguments, execute, inspect logs, and retrieve
   the saved text/audio. A local filename is not visible to the remote container.
3. **CLI demonstration:** use `gcloud storage cp` to upload a local text file, then
   `gcloud run jobs execute` with input/output argument overrides. This executes
   the already-created job; it does not require returning to the console.
4. **Optional helper:** combine those two commands after showing both explicitly.
   The helper should upload, launch, report execution status/output location, and
   optionally download results. It must not imply the job-launch command itself
   automatically uploads local files.

The [job walkthrough design](docs/job-workflow.md) records the proposed console
arguments and CLI sequence. The storage-input option and helper remain work to
implement, not supported commands in the current application scaffold.

A short classroom task illustrates the same pattern as unattended overnight
work. Rehearse resource limits, task timeout, and retries explicitly. Start with
one passage sequentially. Processing independent passages in parallel is a
stretch goal; splitting a poem into isolated lines can lose translation context.

**Scaffold boundary:** the batch CLI has a `--plan` mode. Actual batch execution and uploads
are unimplemented; the web speech adapter is implemented. The old tutorial's Gemini job describes **one translation**,
not batch processing. Its separate published image has not been inspected here.

## Implementation and publication checklist

- [x] Document the four-part story and preserve original instructions.
- [x] Add a translation UI and shared code with service and batch entry points.
- [x] Supply one Dockerfile for service and job; separate images are unnecessary.
- [x] Verify the local container serves the UI and returns a real translation.
- [x] Implement Vertex AI speech and browser audio playback with offline contract checks.
- [ ] Verify a real Vertex speech call and browser playback with the intended service account.
- [ ] Implement bucket uploads and retry-safe artifact naming.
- [ ] Add Cloud Storage input, console execution instructions, and CLI upload/execute/download examples.
- [ ] Add the optional upload-and-launch helper after the explicit CLI steps work.
- [ ] Verify runtime identities and public invocation in the teaching project.
- [x] Build and smoke-test a Linux AMD64 image locally.
- [ ] Push a versioned image to Docker Hub or Artifact Registry.
- [ ] Record its tested digest and replace documentation placeholders.
- [ ] Rehearse all parts, output retrieval, and resource cleanup.

**A local development image has been built and smoke-tested; it has not been
published or deployed to Cloud Run.** Students must not be told to pull a proposed
image before publication and verification.
See the [application scaffold guide](tutorial/app/README.md) for local commands.

An [independent Opus 5.5 teaching-flow review](docs/flow-review-opus55.md) identifies
further sequencing improvements. Its recommendations are recorded, not yet applied.
