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

**Scaffold boundary:** the UI and adapter contract exist, but live Vertex AI speech
is unimplemented and returns an explicit not-implemented response. The audio
button is disabled by default. Do not present it as a working feature yet.

## Part 4: make a translated audio edition as a job

Use a short supplied passage, such as the [original sample](tutorial/app/examples/passage.txt).
Translate the complete passage, synthesize speech with the same provider as part
3, save text and audio to Cloud Storage, and exit. Outputs persist after the
container stops; no browser waits for completion.

Use the **same application image**, changing its startup command from web server
to batch CLI. Cloud Run jobs execute container processes to completion; they do
not use the HTTP function's "Write a function" path.

Give the job a separate runtime service account with Vertex AI inference access
and permission to create objects **in the particular output bucket**. A candidate
is `roles/storage.objectCreator`, which cannot overwrite existing objects. Use a
fresh output prefix and settle retry behavior before enabling uploads. The person
retrieving outputs needs separate read access. Files need not be public. Reading
input from a private bucket would need additional read permission; that is an
optional extension.

A short classroom task illustrates the same pattern as unattended overnight
work. Rehearse resource limits, task timeout, and retries explicitly. Start with
one passage sequentially. Processing independent passages in parallel is a
stretch goal; splitting a poem into isolated lines can lose translation context.

**Scaffold boundary:** the batch CLI has a `--plan` mode. Actual speech and uploads
are unimplemented. The old tutorial's Gemini job describes **one translation**,
not batch processing. Its separate published image has not been inspected here.

## Implementation and publication checklist

- [x] Document the four-part story and preserve original instructions.
- [x] Add a translation UI and shared code with service and batch entry points.
- [x] Supply one Dockerfile for service and job; separate images are unnecessary.
- [ ] Rehearse the UI against the actual translation provider.
- [ ] Implement Vertex AI speech and test browser audio playback.
- [ ] Implement bucket uploads and retry-safe artifact naming.
- [ ] Verify runtime identities and public invocation in the teaching project.
- [ ] Build and smoke-test a Linux AMD64 image.
- [ ] Push a versioned image to Docker Hub or Artifact Registry.
- [ ] Record its tested digest and replace documentation placeholders.
- [ ] Rehearse all parts, output retrieval, and resource cleanup.

**No new image has been built, published, or deployed for this branch.** Students
must not be told to pull a proposed image before publication and verification.
See the [application scaffold guide](tutorial/app/README.md) for local commands.
