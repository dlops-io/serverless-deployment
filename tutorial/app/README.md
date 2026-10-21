# Application scaffold

Part 2 has a translation UI and HTTP route. Live translation requires outbound
network access and a functioning googletrans provider. Parts 3 and 4 are explicit
integration boundaries: no speech or Cloud Storage uploads are implemented yet.

## Local development

With uv and Python 3.12:

```bash
uv sync --frozen
uv run python -m translation_demo serve
```

Open `http://localhost:8080`. Test the same input that worked in part 1. The browser
sends a JSON POST here; part 1 used URL query parameters. Explain that input-format
change if showing the requests. The disabled audio button is a future feature.

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
setup applies when implementing Vertex AI speech and Cloud Storage uploads.
Those integrations are still unimplemented in this scaffold; authentication setup
alone will not enable the speech button or make the batch command execute.

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
  translation-demo:dev
```

Adjust the host path if your gcloud credential location differs. Matching the
container UID to your host user permits reading a user-private credential file.
Do not make the file world-readable to work around permissions. Supply any
additional model/region settings expected by the eventual speech adapter.
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

## Image publication: not done yet

Maintainers must choose a registry namespace and verify write access before
publishing. Tag a tested image with an explicit version, push it, record its
digest, and test deployment from that digest. Do not overwrite the original
tutorial's `latest` image while developing this branch. No student-ready image
address is claimed by these instructions.

Students can follow the final tutorial using prebuilt images. These source files,
the Dockerfile, and CLI are available for optional inspection; reading them is
not a prerequisite to deploying an image through the console.
