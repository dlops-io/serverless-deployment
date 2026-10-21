# Application scaffold

Part 2 has a translation UI and HTTP route. Live translation requires outbound
network access and a functioning googletrans provider. Part 3 implements Vertex AI speech and browser WAV playback, enabled explicitly
after configuring identity. Part 4 still has no Cloud Storage uploads or batch execution.
Offline speech checks pass. A real Vertex call using impersonated service-account
ADC has returned valid WAV audio both from local Python and through the container
HTTP route. Local browser playback was confirmed by the instructor. The deployed Cloud Run
UI, translation route, and speech route also pass live checks; manual cloud
browser playback remains to be checked.

## Local development

With uv and Python 3.12:

```bash
uv sync --frozen
uv run python -m translation_demo serve
```

Open `http://localhost:8080`. Test the same input that worked in part 1. The browser
sends a JSON POST here; part 1 used URL query parameters. Explain that input-format
change if showing the requests. Audio stays disabled in part 2. Enable it after completing the part 3 setup below.

Run offline checks:

```bash
uv run python -m unittest discover -s tests -v
uv run python -m translation_demo batch --plan \
  --text-file examples/passage.txt --src en --dest fr \
  --output-uri gs://YOUR_OUTPUT_BUCKET/fresh-run-prefix
```

The plan command makes no API calls, creates no files, and uploads nothing.
Without `--plan`, the scaffold exits unsuccessfully rather than pretending to run.

## Local development against GCP

The classroom deployment instructions start from a prebuilt application. Your own
development should have a faster loop: **edit → run locally → call the real API →
inspect the response**. Rebuilding and publishing an image belongs later.

The translation provider in part 2 does not use GCP credentials. The following
setup applies to Vertex AI speech and, later, Cloud Storage uploads.
Speech is implemented; batch uploads remain unimplemented.

### Create the runtime identity: console or CLI

In the console, open **IAM & Admin → Service Accounts → Create service account**.
Create a dedicated translation demo account and grant **Vertex AI User** on your
project. Also grant **Service Usage Consumer** so it can use this project as the
API quota project. On that service account's **Permissions** tab, grant your developer user
**Service Account Token Creator**. These are two different grants: the runtime
account can call Vertex AI; the developer can request temporary credentials as it.
The person deploying Cloud Run also needs permission to attach this account
(`iam.serviceAccounts.actAs`, commonly via Service Account User).

Equivalent CLI setup, run by an identity authorized to create accounts and edit IAM:

```bash
PROJECT_ID=YOUR_PROJECT_ID
DEVELOPER_EMAIL=YOUR_GOOGLE_ACCOUNT_EMAIL
SERVICE_ACCOUNT_NAME=translation-demo
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud services enable aiplatform.googleapis.com iamcredentials.googleapis.com \
  --project="$PROJECT_ID"
gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
  --display-name="Translation demo runtime" --project="$PROJECT_ID"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role=roles/aiplatform.user --condition=None
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role=roles/serviceusage.serviceUsageConsumer --condition=None
gcloud iam service-accounts add-iam-policy-binding "$SERVICE_ACCOUNT_EMAIL" \
  --member="user:$DEVELOPER_EMAIL" \
  --role=roles/iam.serviceAccountTokenCreator --project="$PROJECT_ID" --condition=None
```

Console and CLI change the same cloud resources. These commands are also useful
for reproducible setup scripts and coding agents acting with your authorization.
They do not give an agent permissions beyond the identity running the commands.
Do not grant Storage access to the interactive web service; part 4 will introduce
that separately for its job identity.

### Choose a local identity

Install the Google Cloud CLI, choose your development project, and enable the
APIs the application will actually call. The identity also needs the relevant
API permissions; credentials do not grant permissions by themselves.

For local Python development using your own Google identity:

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

The second command assigns the ADC quota project. It requires the Service Usage
Consumer role or equivalent permission on that project. Configure the application's target project
and model region separately; a quota project is not a model-location setting.
Ordinary `gcloud auth login` configures the CLI identity and is not a substitute
for setting up your application's ADC.

To test with the intended runtime service account instead:

```bash
gcloud auth application-default login \
  --impersonate-service-account=SERVICE_ACCOUNT_EMAIL
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

Your developer identity needs `roles/iam.serviceAccountTokenCreator` on that
service account, and the IAM Service Account Credentials API must be enabled in
the appropriate project. The service account itself needs the API permissions
being tested. Google's Python authentication libraries support impersonated ADC.
This tests the service identity's permissions more accurately than using a
developer account with broad project access. It still does not reproduce all
of Cloud Run's networking and execution environment.

Impersonation uses temporary access tokens; you do not download a service-account
private key. The local ADC file still contains sensitive credentials. Keep it out
of Git, build contexts, and container images. On Cloud Run, attach the runtime
service account and let ADC obtain its credentials there. Do not upload your
local ADC file to configure the deployed service.

### Enable and test short speech

After configuring ADC (prefer impersonation above), run:

```bash
export ENABLE_SPEECH=true
export GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
export GOOGLE_CLOUD_LOCATION=us-central1
uv run python -m translation_demo serve
```

Translate a short sentence, then select **Play audio**. The server calls
`gemini-2.5-flash-tts` through Vertex AI using ADC, wraps the returned mono 24 kHz
16-bit PCM in a WAV header, and returns it directly to the browser. No bucket is
used. The browser retains the audio for replay until the next translation.
`VERTEX_TTS_MODEL` and `VERTEX_TTS_VOICE` can override the defaults (voice: `Kore`).
Model location is independent of the Cloud Run region. Verify model availability
and language support for your selected location. The demo limits speech input to
4,000 UTF-8 bytes and reports credential, permission, and provider failures.

For Cloud Run, supply these environment settings and attach the runtime service
account. Do not run an interactive ADC login inside the deployed container.
The default remains `ENABLE_SPEECH=false` for part 2.

[Gemini TTS format, models, and locations](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts).

### Iterate before publishing

1. Run the application directly with `uv run python -m translation_demo serve`.
   Edit the Python code, restart, and debug using local logs or a debugger.
2. Test a small real API call with the local ADC identity. Use offline tests and
   mocked providers for most checks; real API calls can incur charges.
3. When application behavior works, build and test the container locally.
4. Publish the tested image, deploy it with its runtime identity, and verify the
   final cloud configuration. Avoid a full deployment loop for each code edit.

Client libraries should discover ADC rather than hard-code a credential filename
or load a private key in application code. Keep project, region, model choice,
and output bucket configurable. The integration should work unchanged with local
ADC and with an attached Cloud Run identity.

### Give a local container access to ADC

Your host's credentials are **not automatically inside a container**. After a
local image build, this Linux/macOS example mounts only the ADC file read-only:

```bash
docker run --rm -p 8080:8080 \
  --user "$(id -u):$(id -g)" \
  --mount "type=bind,source=${HOME}/.config/gcloud/application_default_credentials.json,target=/tmp/dev-adc.json,readonly" \
  -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/dev-adc.json \
  -e GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID \
  -e ENABLE_SPEECH=true \
  -e GOOGLE_CLOUD_LOCATION=us-central1 \
  translation-demo:dev
```

Adjust the host path if your gcloud credential location differs. Matching the
container UID to your host user permits reading a user-private credential file.
With rootless Docker, the host user may map to container UID 0 instead; inspect
the mounted file ownership inside the container and use `--user 0:0` for this
local rootless development run if needed. Do not change the production image user.
Do not make the file world-readable to work around permissions. Supply any
additional model/voice settings if overriding the speech adapter defaults.
These are development-only mounts; use an attached service account in Cloud Run.

Troubleshooting: unauthenticated means credentials were not found or accepted;
permission denied means the caller lacks access or a policy blocks it. Also check
the API's enabled status, model region, quota project, and billing. Always identify
which identity the client is actually using before changing permissions.

References: [local ADC setup](https://docs.cloud.google.com/docs/authentication/set-up-adc-local-dev-environment),
[ADC for a containerized development environment](https://docs.cloud.google.com/docs/authentication/set-up-adc-containerized-environment),
and [service account impersonation](https://docs.cloud.google.com/iam/docs/service-account-impersonation).

## One image, two startup commands

Build from this directory (a Linux AMD64 development build has been smoke-tested):

```bash
docker build --platform linux/amd64 -t translation-demo:dev .
docker run --rm -p 8080:8080 translation-demo:dev
```

The image defaults to the web server. For a job, override its command:

```bash
docker run --rm translation-demo:dev \
  python -m translation_demo batch --plan \
  --text-file examples/passage.txt --src en --dest fr \
  --output-uri gs://YOUR_OUTPUT_BUCKET/fresh-run-prefix
```

In Cloud Run job settings the **command** would be `python` and the individual
**arguments** would start with `-m`, `translation_demo`, `batch`. Do not paste the
whole command into one argument field. Remove `--plan` only after real execution
is implemented and rehearsed.

## Image publication: teaching-project rehearsal

The image has been published privately to the teaching project’s Artifact
Registry and deployed successfully to Cloud Run; see the
[rehearsal record](../../docs/cloud-run-rehearsal.md). A student-accessible registry
address is still needed. Maintainers must choose that namespace and verify write
access before publishing for students. Tag a tested image with an explicit version, push it, record its
digest, and test deployment from that digest. Do not overwrite the original
tutorial's `latest` image while developing this branch. No student-ready image
address is claimed by these instructions.

Students can follow the final tutorial using prebuilt images. These source files,
the Dockerfile, and CLI are available for optional inspection; reading them is
not a prerequisite to deploying an image through the console.
