# Serverless Deployment

In this tutorial, you will deploy a translation function, share a locally tested
web app, give that app access to a cloud speech model, and run the same processing
as a job that saves its results.

The translation model is provided by an external service. We are deploying the
**application code around the model**, not training or hosting the translation
model ourselves. This is the same application role we will need in the Cheese
App: accept input, call a model service, and return a result.

| Part | What you do | New idea |
| --- | --- | --- |
| [1. Deploy a function](#part-1-deploy-a-translation-function) | Call a URL with text and language parameters | Supply code; Google builds the runnable image |
| [2. Deploy a web app](#part-2-deploy-a-translation-web-app) | Move a working local UI to a public URL | Deploy an existing container image |
| [3. Add speech](#part-3-give-the-web-app-access-to-vertex-ai) | Play the translation as audio | Give a runtime identity permission to call Vertex AI |
| [4. Run a job](#part-4-generate-and-save-a-translated-audio-edition) | Translate a passage and save text and audio | Run finite work and keep its output in Storage |

**Follow the console steps first.** The expandable **Equivalent gcloud commands**
sections are alternative ways to perform the same actions, not additional steps
to run after creating the same resources in the console. Expand **More detail**
when you want to understand what is happening underneath.

## Before you begin

1. Open the [Google Cloud console](https://console.cloud.google.com/) and select
   **your course project** using the project selector at the top. Check the
   **project ID**, not only its display name. Use your own project and buckets
   when following along; instructor resources are examples.
2. Confirm billing is enabled and that you can create Cloud Run resources,
   service accounts, and buckets and grant their required permissions. If the
   course project restricts these actions, resolve that with course staff first.
3. Choose a Cloud Run region. These instructions use **Toronto
   (`northamerica-northeast2`)**. The speech model uses **`us-central1`**; that is
   a separate setting we introduce in part 3.
4. Clone or download the [tutorial branch](https://github.com/dlops-io/serverless-deployment/tree/codex/four-part-tutorial). Use the repository root as the working
   directory for terminal examples. Docker is needed for the local demonstration
   in part 2. Python and the Google Cloud CLI are needed for the local helper in
   part 4. Deploying a prebuilt image through the console does not require Docker.

Use these names as a worksheet. Resource names can be different if you carry
those choices through the later steps.

| Setting | Value used in this walkthrough |
| --- | --- |
| Function service | `translate-function` |
| Web service | `translation-demo` |
| Web runtime account | `translation-demo` |
| Job | `translation-audio` |
| Job runtime account | `translation-audio-job` |
| Input bucket | A globally unique name you choose in part 4 |
| Output bucket | A second globally unique name you choose in part 4 |

The public image used in parts 2–4 is:

```text
cgumb/ac215-translation-demo:lecture14-batch-50d8201
```

You do not need to build or publish an image to follow the tutorial. The source,
Dockerfile, and application CLI are available for optional inspection in
[`tutorial/app/`](tutorial/app/).

<details>
<summary>Terminal setup — run once before using any gcloud command boxes</summary>

Install the [Google Cloud CLI](https://docs.cloud.google.com/sdk/docs/install).
Run this in your local terminal, replacing the project ID. Cloud Shell already
has gcloud installed and normally uses your console identity.

```bash
gcloud auth login
export PROJECT_ID=YOUR_PROJECT_ID
export REGION=northamerica-northeast2
export IMAGE=cgumb/ac215-translation-demo:lecture14-batch-50d8201
export WEB_SERVICE=translation-demo
export JOB_NAME=translation-audio
export WEB_EMAIL="translation-demo@${PROJECT_ID}.iam.gserviceaccount.com"
export JOB_EMAIL="translation-audio-job@${PROJECT_ID}.iam.gserviceaccount.com"
```

Keep this terminal open for the command alternatives. Commands use an explicit
project flag so they do not depend on a different globally selected project.
This CLI login lets gcloud operate on your project. It does **not** set up the
application's local ADC; we introduce that in part 3.

</details>

## Part 1: Deploy a translation function

Start with the smallest possible app: receive text and language parameters,
call the translation provider, and return translated text. You supply a Python
handler and its dependencies. Google builds and runs the container for you.

### 1.1 Create the function

1. In the console, open **Cloud Run → Services** and select **Write a function**.
   On a narrow window, it can be under the toolbar’s **More actions** menu.
2. If prompted to enable required APIs, enable them and return to the form.
3. Set **Service name** to `translate-function` and choose your region.
4. Select **Python 3.12** as the runtime. Do not use the old tutorial's Python 3.10
   setting.
5. Under **Authentication**, select **Allow public access** for this classroom
   endpoint, then select **Create**.
6. Wait for the service to be created. Open its **Source** editor if the console
   does not take you there automatically. The initial service can contain sample
   code; we replace that next.

<details>
<summary>Console navigation — opening the function creation form</summary>

![Cloud Run Services: choose Write a function, then the inline function creation form](images/console/function-entry.gif)

The form is titled **Create service** even though you selected a function.
The animation stops before entering settings or creating a resource. Choose
your region and Python runtime as described above; do not keep the defaults
without checking them.

[Still image of the function creation form](images/console/function-create.png).

</details>

### 1.2 Supply the code and dependencies

1. Replace `main.py` with the contents of
   [`tutorial/function/main.py`](tutorial/function/main.py):

   ```python
   import functions_framework
   from googletrans import Translator

   @functions_framework.http
   def hello_http(request):
       text = request.args.get("text", "Welcome to AC215")
       source = request.args.get("src", "en")
       destination = request.args.get("dest", "es")
       return Translator().translate(text, src=source, dest=destination).text
   ```

2. Replace `requirements.txt` with
   [`tutorial/function/requirements.txt`](tutorial/function/requirements.txt):

   ```text
   functions-framework==3.10.2
   googletrans==4.0.0rc1
   ```

3. Set the **Function entry point** to `hello_http`. This is the Python function
   the serving framework should call, not the filename or service name.
4. Select **Save and redeploy** (some console versions label this **Save and
   deploy**). Wait for the revision to become ready.

### 1.3 Call the endpoint

1. Return to **service details** and copy the **URL** near the top. The build
   details page describes a build; the service page gives the application URL.
2. Open your URL in a browser. With no arguments, it translates the default text
   from English to Spanish.
3. Append the following query string to **your** URL:

   ```text
   ?text=Good%20afternoon%20everyone&src=en&dest=fr
   ```

4. Change `dest=fr` to `dest=el` or `dest=hi` and try again. For Chinese, use
   `dest=zh-cn` for Simplified Chinese.
5. Open **Observability → Logs** in service details and find the requests you
   just made. Confirm an HTTP **200** response for the translation request.

**Checkpoint:** the same endpoint accepts different inputs without a redeploy.
The question mark begins the query string; ampersands separate its parameters.
The `src` and `dest` parameters identify languages, not cloud regions.

<details>
<summary>Console capture — source files, completed deployment, and live response</summary>

![Edit the handler and dependencies, confirm build completion, then view the French translation](images/console/function-deploy-test.gif)

These screenshots from the console rehearsal show the handler, dependencies,
completed rollout, and live response. Build waiting time is omitted. The
translation request returned **Bonjour à tous**, and its request log showed
HTTP **200**.

</details>

<details>
<summary>Equivalent gcloud commands — deploy and call the function</summary>

Use the terminal setup above. Source deployment may prompt you to enable APIs or
create a build repository in a new project.

```bash
gcloud run deploy translate-function \
  --project="$PROJECT_ID" --region="$REGION" \
  --source=tutorial/function --function=hello_http --base-image=python312 \
  --allow-unauthenticated

FUNCTION_URL=$(gcloud run services describe translate-function \
  --project="$PROJECT_ID" --region="$REGION" --format='value(status.url)')
curl --get "$FUNCTION_URL" \
  --data-urlencode 'text=Good afternoon everyone' \
  --data-urlencode 'src=en' --data-urlencode 'dest=fr'
```

</details>

<details>
<summary>More detail — what is being built, and what is a cold start?</summary>

Open the deployment's build details. The build process receives your source,
uses Google's build tooling to assemble a Python environment, installs the
requirements, configures the Functions Framework, and publishes an application
image in Artifact Registry. It does not infer all dependencies from imports.
Dependency installation happens at **build time**, not on every request.

Cloud Run routes requests to application instances and can start additional
instances when needed. A cold start initializes an instance of the built
application; it does not necessarily boot a new VM dedicated to your request.
Scaling to zero applies to app instances, while Google's routing infrastructure
remains available. There is no fixed inactivity interval to rely on as a
prediction of the next cold start. Minimum-instance settings can keep capacity
warm when that matters.

The default text translation here uses `googletrans`, a wrapper around an
external translation service. It is independent of the Vertex AI speech call we
add later. Provider failures and quotas can affect a demo; inspect logs rather
than treating a completed build as proof that translation worked.

[Function deployment reference](https://docs.cloud.google.com/run/docs/quickstarts/functions/deploy-functions-console).

</details>

## Part 2: Deploy a translation web app

Now imagine you already have a working containerized web app on your laptop.
It has text boxes, language selectors, and a Translate button. Sharing
`localhost` does not make it available on another person's computer. We will
deploy that existing image and give the app a public URL.

### 2.1 Try the prebuilt app locally

1. With Docker running, open a local terminal and run:

   ```bash
   docker run --rm -p 8086:8080 \
     cgumb/ac215-translation-demo:lecture14-batch-50d8201
   ```

2. Open [http://localhost:8086](http://localhost:8086).
3. Enter a short sentence, choose source and destination languages, and select
   **Translate**. The translated text appears in the other box.
4. Notice that **Play audio** is disabled. We introduce the identity and speech
   permissions in part 3. Stop the local container with **Ctrl+C** when finished.

If you are following only the console demonstration, you can observe the
instructor's local run and continue to the next step.

### 2.2 Deploy the same image

1. Open **Cloud Run → Services → Deploy container**.
2. Choose deployment from an **existing container image** and paste:

   ```text
   cgumb/ac215-translation-demo:lecture14-batch-50d8201
   ```

3. Set **Service name** to `translation-demo` and choose your region.
4. Select **Allow public access**. Use request-based billing and zero minimum
   instances for this demo.
5. Leave the image's startup command unchanged. Do not add speech environment
   variables yet. Select **Create** and wait until the service is ready.
6. Copy its **URL**, open the page, and repeat your local translation.
7. Open **Revisions** and **Logs** in service details. A revision is a deployed
   version of the service's image and configuration.

**Checkpoint:** someone else can use the app through its cloud URL. We supplied
an already-built image, so this deployment did not need to build our source.

<details>
<summary>Equivalent gcloud commands — deploy the container service</summary>

```bash
gcloud run deploy "$WEB_SERVICE" \
  --project="$PROJECT_ID" --region="$REGION" --image="$IMAGE" \
  --allow-unauthenticated --min-instances=0 --max-instances=2 \
  --cpu=1 --memory=512Mi --concurrency=4 --timeout=120
```

This creates the part 2 service. If you are rerunning the tutorial with an
existing service that already has speech enabled, remove its `ENABLE_SPEECH`
setting to restore the part 2 behavior.

</details>

<details>
<summary>More detail — why use a container, and can a web UI scale to zero?</summary>

A function could also return HTML and implement this interface. The reason for
using a container is that we already packaged and tested an app and want to
carry that image into deployment. Custom images also give us control over system
libraries, startup commands, and application structure when needed.

The browser keeps displaying HTML and running client-side code after the server
responds. Selecting Translate sends another HTTP request; the app returns JSON
that updates the page. The container does not need to remain dedicated to that
browser between interactions. Successive requests can reach different instances.

The Cloud Run application is our **application backend**. That means server-side
application logic behind the interface, not the last service in a chain. It can
expose a public API and call other services. Here the flow is browser → our app →
external translation provider → our app → browser.

[Container deployment reference](https://docs.cloud.google.com/run/docs/deploying).

</details>

## Part 3: Give the web app access to Vertex AI

Keep the same app and translation provider. This time, enable **Play audio**.
The app will call Gemini text-to-speech through Vertex AI and return audio to
the waiting browser. This requires an authorized identity, not an output bucket.

Two permissions questions are separate: **who may call our public app**, and
**what the running app may access**. A service account answers the second one.

### 3.1 Enable the API and create the app's identity

1. In **APIs & Services → Library**, find **Vertex AI API** and enable it in your
   project if it is not already enabled.
2. Open **IAM & Admin → Service Accounts → Create service account**.
3. Use `translation-demo` as the account ID, with a descriptive display name.
   Its email will be `translation-demo@YOUR_PROJECT_ID.iam.gserviceaccount.com`.
4. In the step for granting this account access to the project, add **Vertex AI
   User** and **Service Usage Consumer**, then finish creation. The first grants
   model access; the second permits using the project for API quota/billing.
5. Record the account email. You do not need to create or download a key.

<details>
<summary>Equivalent gcloud commands — create the speech runtime identity</summary>

```bash
gcloud services enable aiplatform.googleapis.com --project="$PROJECT_ID"
gcloud iam service-accounts create translation-demo \
  --project="$PROJECT_ID" --display-name='Translation demo runtime'
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$WEB_EMAIL" --role=roles/aiplatform.user --condition=None
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$WEB_EMAIL" \
  --role=roles/serviceusage.serviceUsageConsumer --condition=None
```

Creating accounts, granting their permissions, and attaching them require your
caller identity to have the corresponding administrative rights. Attaching an
account requires `iam.serviceAccounts.actAs`, commonly provided by **Service
Account User** on that account. These are your deployment permissions, separate
from the account's runtime permissions.

</details>

### 3.2 Attach the identity and enable speech

1. Return to **Cloud Run → Services → translation-demo**.
2. Select **Edit & deploy new revision**.
3. Under **Security**, select the service account you just created.
4. Under the container's **Variables & Secrets** settings, add these environment
   variables:

   | Name | Value |
   | --- | --- |
   | `ENABLE_SPEECH` | `true` |
   | `GOOGLE_CLOUD_PROJECT` | Your project ID |
   | `GOOGLE_CLOUD_LOCATION` | `us-central1` |

5. Keep the same image and public invocation setting. Deploy the revision and
   wait for it to become ready.
6. Reload the app's URL. Translate a short English sentence into French, then
   select **Play audio**. Use the browser's audio controls to replay it.
7. If the request fails, read the message shown in the UI and inspect the
   service's **Logs** before changing permissions.

**Checkpoint:** the app can call an authenticated cloud API using its attached
service account. Audio is returned directly to the browser; no audio files have
to be saved to a bucket in this part.

<details>
<summary>Equivalent gcloud commands — attach the account and enable speech</summary>

```bash
gcloud run services update "$WEB_SERVICE" \
  --project="$PROJECT_ID" --region="$REGION" \
  --service-account="$WEB_EMAIL" \
  --update-env-vars="ENABLE_SPEECH=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1"
```

The service region and model location are different settings. We rehearsed this
with the service in Toronto and the speech model in `us-central1`. The defaults
are `gemini-2.5-flash-tts` and voice `Kore`. Model availability, language support,
and quota depend on the selected model/location.

[Gemini TTS reference](https://docs.cloud.google.com/text-to-speech/docs/gemini-tts).

</details>

### 3.3 How would you develop this locally?

You should not need to publish an image for every code edit. Run Python locally,
call the real API, debug, then test the container and deploy once the behavior
works. **Application Default Credentials (ADC)** lets the same code discover
credentials locally and on Cloud Run.

To test the runtime account's actual permissions, your local app can
**impersonate that service account**. You sign in as yourself, with permission
to obtain temporary credentials as the account. This avoids downloading its
private key. Cloud Run obtains credentials from the attached identity instead.

<details>
<summary>Try it locally — service account impersonation and ADC</summary>

First grant your developer user **Service Account Token Creator** on the web
runtime account: **IAM & Admin → Service Accounts → translation-demo →
Permissions → Grant access**. Add your user email as principal and that role.
Enable the **IAM Service Account Credentials API** under **APIs & Services**.
Equivalent commands, followed by the interactive application login:

```bash
export DEVELOPER_EMAIL=YOUR_GOOGLE_ACCOUNT_EMAIL
gcloud services enable iamcredentials.googleapis.com --project="$PROJECT_ID"
gcloud iam service-accounts add-iam-policy-binding "$WEB_EMAIL" \
  --project="$PROJECT_ID" --member="user:$DEVELOPER_EMAIL" \
  --role=roles/iam.serviceAccountTokenCreator --condition=None

gcloud auth application-default login --impersonate-service-account="$WEB_EMAIL"
gcloud auth application-default set-quota-project "$PROJECT_ID"
```

Complete the browser sign-in. The ADC file stays on your machine; it does not go
into Git or the image. Your developer user needs permission to use the selected
quota project as well. In a restricted project, course staff may need to grant
**Service Usage Consumer** to your developer identity.

With [uv](https://docs.astral.sh/uv/) installed, run the app directly:

```bash
cd tutorial/app
uv sync --frozen
ENABLE_SPEECH=true GOOGLE_CLOUD_PROJECT="$PROJECT_ID" \
  GOOGLE_CLOUD_LOCATION=us-central1 PORT=8086 \
  uv run python -m translation_demo serve
```

Open [http://localhost:8086](http://localhost:8086), translate, and play audio.
Edit code and restart locally; a new cloud deployment is not needed for each
edit. Run `cd ../..` when you return to repository-root commands below.

For container credential mounts, rootless Docker permissions, authentication
troubleshooting, and build/publish steps, use the
[development guide](tutorial/app/README.md#local-development-against-gcp).
Local identity tests do not reproduce every cloud networking or deployment
setting, so still verify the deployed app.

[Google's local ADC guide](https://docs.cloud.google.com/docs/authentication/set-up-adc-local-dev-environment).

</details>

## Part 4: Generate and save a translated audio edition

For an interactive web request, a person waits for the response. Now imagine
preparing a translated audio edition of a passage to collect later. The program
should read its input, translate it, generate speech, save the files, and exit.
That is a **job**, rather than an HTTP service waiting for requests.

We use the **same image** and the **same translation and speech code**. The new
pieces are its finite startup command and persistent files in Cloud Storage.
Work through the setup, then run it once from the console before using the CLI
or helper. The small passage finishes quickly, but the pattern also applies to
longer unattended work.

### 4.1 Create your input and output buckets

1. Open **Cloud Storage → Buckets → Create**.
2. Choose a **globally unique input bucket name**, such as your project ID plus
   `-translation-input`. Record the full name.
3. Use a **Region** location in your chosen region, **Standard** storage,
   **Uniform** access control, and keep **public access prevention** enabled.
   Create the bucket without adding a custom retention policy.
4. Repeat for a separate, globally unique **output bucket**.
5. Save the [sample passage](tutorial/app/examples/passage.txt) to your machine.
   Open the input bucket, create a folder named `run-001`, then use **Upload
   files** to upload it as `passage.txt`.
6. Open the uploaded object's details and copy its **gs:// URI**. It should look
   like `gs://YOUR_INPUT_BUCKET/run-001/passage.txt`.

The input bucket holds uploaded passages. The output bucket will hold generated
text, audio, and completion records. Neither bucket needs to be public. You use
your own buckets even though everyone shares the same public image.

<details>
<summary>Equivalent gcloud commands — create buckets and upload the first passage</summary>

Choose your own globally unique bucket names; keep these variables for the
remaining job command boxes.

```bash
export INPUT_BUCKET=YOUR_GLOBALLY_UNIQUE_INPUT_BUCKET
export OUTPUT_BUCKET=YOUR_GLOBALLY_UNIQUE_OUTPUT_BUCKET

gcloud services enable storage.googleapis.com --project="$PROJECT_ID"
gcloud storage buckets create "gs://$INPUT_BUCKET" \
  --project="$PROJECT_ID" --location="$REGION" \
  --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets create "gs://$OUTPUT_BUCKET" \
  --project="$PROJECT_ID" --location="$REGION" \
  --uniform-bucket-level-access --public-access-prevention
gcloud storage cp tutorial/app/examples/passage.txt \
  "gs://$INPUT_BUCKET/run-001/passage.txt" --project="$PROJECT_ID"
```

</details>

### 4.2 Create a separate identity for the job

1. Open **IAM & Admin → Service Accounts → Create service account**. Set the
   account ID to `translation-audio-job`.
2. Grant it **Vertex AI User** and **Service Usage Consumer** on your project,
   as you did for the web account. Record its email.
3. Open the **input bucket → Permissions → Grant access**. Add the job account
   email as principal and grant **Storage Object Viewer**.
4. Open the **output bucket → Permissions → Grant access**. Add the same job
   account and grant **Storage Object Creator**.
5. Leave the web app's runtime account unchanged. It does not need these bucket
   permissions, because its audio goes straight to the browser.

**Checkpoint:** the job account can read input, call the speech model, and create
output files. Your own console/CLI identity needs separate permission to upload
passages, launch executions, and read results.

<details>
<summary>Equivalent gcloud commands — grant the job's runtime permissions</summary>

```bash
gcloud iam service-accounts create translation-audio-job \
  --project="$PROJECT_ID" --display-name='Translation audio job'
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$JOB_EMAIL" --role=roles/aiplatform.user --condition=None
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$JOB_EMAIL" \
  --role=roles/serviceusage.serviceUsageConsumer --condition=None
gcloud storage buckets add-iam-policy-binding "gs://$INPUT_BUCKET" \
  --member="serviceAccount:$JOB_EMAIL" --role=roles/storage.objectViewer
gcloud storage buckets add-iam-policy-binding "gs://$OUTPUT_BUCKET" \
  --member="serviceAccount:$JOB_EMAIL" --role=roles/storage.objectCreator
```

For a restricted project, your caller also needs **Service Account User** on the
job account to attach it. Running with argument overrides requires
`run.jobs.runWithOverrides`, supplied by **Cloud Run Jobs Executor With
Overrides**. This is separate from the job account's Vertex/Storage access.

</details>

### 4.3 Create the job

1. Open **Cloud Run → Jobs** and choose **Deploy container** / **Create job**.
2. Paste the same public image used in part 2:

   ```text
   cgumb/ac215-translation-demo:lecture14-batch-50d8201
   ```

3. Set **Job name** to `translation-audio`, choose your region, and use **1 task**.
4. Expand the container settings. Set **Container command** to `python`. This
   replaces the image's default command that starts the web server.
5. In **Container arguments**, enter the following as **individual arguments**,
   replacing the two bucket placeholders. Do not paste the whole block into one
   argument field.

   ```text
   -m
   translation_demo
   batch
   --input-uri
   gs://YOUR_INPUT_BUCKET/run-001/passage.txt
   --src
   en
   --dest
   fr
   --output-uri
   gs://YOUR_OUTPUT_BUCKET/run-001/
   ```

6. Set these container environment variables:

   | Name | Value |
   | --- | --- |
   | `ENABLE_SPEECH` | `true` |
   | `GOOGLE_CLOUD_PROJECT` | Your project ID |
   | `GOOGLE_CLOUD_LOCATION` | `us-central1` |

7. Under **Security**, select `translation-audio-job`, the job runtime account.
8. Set **task timeout** to **5 minutes**, **retries** to **0**, **memory** to
   **512 MiB**, and **CPU** to **1**. Keep the first example sequential.
9. Leave **Execute job immediately** unchecked and select **Create**. We will
   launch it explicitly next.

<details>
<summary>Equivalent gcloud commands — create the job</summary>

```bash
gcloud run jobs create "$JOB_NAME" \
  --project="$PROJECT_ID" --region="$REGION" --image="$IMAGE" \
  --service-account="$JOB_EMAIL" --command=python \
  --args="-m,translation_demo,batch,--input-uri,gs://$INPUT_BUCKET/run-001/passage.txt,--src,en,--dest,fr,--output-uri,gs://$OUTPUT_BUCKET/run-001/" \
  --set-env-vars="ENABLE_SPEECH=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1" \
  --tasks=1 --max-retries=0 --task-timeout=300 --memory=512Mi --cpu=1
```

</details>

### 4.4 Execute it and collect the files

1. Open **Cloud Run → Jobs → translation-audio** and select **Execute**.
2. Open the new execution. Wait until its task succeeds, then inspect **Logs**.
   The job prints its output location and exits. It does not provide a web URL.
3. Open **Cloud Storage → Buckets → your output bucket → run-001**. Open the
   uniquely named attempt folder inside it.
4. You should see:

   | File | What it contains |
   | --- | --- |
   | `translated.txt` | The complete translated passage |
   | `speech.wav` | Its generated audio |
   | `manifest.json` | Completion status and output locations |

5. Download the text and WAV using the object list's download action or each
   object's details page. Read the translation and play the WAV locally.

**Checkpoint:** the task finished, the process stopped, and its files remain in
Storage. This is the payoff of a job: collect the outputs later, without keeping
a browser request open.

<details>
<summary>Equivalent gcloud commands — execute, then download</summary>

```bash
gcloud run jobs execute "$JOB_NAME" \
  --project="$PROJECT_ID" --region="$REGION" --wait
mkdir -p results
gcloud storage cp --recursive "gs://$OUTPUT_BUCKET/run-001" ./results \
  --project="$PROJECT_ID"
```

`--wait` waits for completion; it does not stream application logs. If execution
fails, inspect the job's logs instead of assuming that partial output is complete.

</details>

<details>
<summary>More detail — folder names, partial failures, retries, and document limits</summary>

`run-001` is a prefix you selected in the job arguments, not an automatically
numbered directory. Each attempt adds a random UUID folder beneath that prefix.
Re-executing the same job configuration therefore creates another attempt folder
without overwriting previous output. Storage displays these object-name prefixes
as folders; they are not directories on the container's local filesystem.

Each upload uses a create-only generation precondition. The app writes
`manifest.json` with `status: complete` **last**. Partial text/audio files without
a completion manifest do not establish success. Automatic retries can duplicate
paid processing and leave incomplete attempt folders; unique names are not
exactly-once processing. Keep retries at zero for the first walkthrough.

The demo reads a short UTF-8 passage and translates it as a whole, preserving
more context than translating isolated poem lines. Input is limited to 5,000
characters and a 20,000-byte Storage object; speech input is limited to 4,000
UTF-8 bytes after translation. Long-document chunking and parallel tasks are
extensions, not features required for this example.

[Job creation reference](https://docs.cloud.google.com/run/docs/create-jobs).

</details>

### 4.5 Submit another passage from the terminal

Once the job exists, you can submit new work without returning to the console.
The upload and execution are separate operations: a remote container cannot read
a filename on your laptop.

1. If you followed only the console path, expand **Terminal setup** near the top
   now. Set the two bucket variables to the actual names you created:

   ```bash
   export INPUT_BUCKET=YOUR_INPUT_BUCKET
   export OUTPUT_BUCKET=YOUR_OUTPUT_BUCKET
   ```

2. Save a new short UTF-8 passage as `passage.txt` on your laptop and upload it:

   ```bash
   gcloud storage cp ./passage.txt "gs://$INPUT_BUCKET/run-002/passage.txt" \
     --project="$PROJECT_ID"
   ```

3. Execute the **existing** job with new argument overrides:

   ```bash
   gcloud run jobs execute "$JOB_NAME" \
     --project="$PROJECT_ID" --region="$REGION" \
     --args="-m,translation_demo,batch,--input-uri,gs://$INPUT_BUCKET/run-002/passage.txt,--src,en,--dest,es,--output-uri,gs://$OUTPUT_BUCKET/run-002/" \
     --wait
   ```

4. After it succeeds, download the new output folder:

   ```bash
   mkdir -p results
   gcloud storage cp --recursive "gs://$OUTPUT_BUCKET/run-002" ./results \
     --project="$PROJECT_ID"
   ```

This run translates into Spanish, using a new input path and output prefix.
Argument overrides replace the complete argument list for this execution; the
job's saved defaults still point to the first French example. Use a fresh prefix
for each new submission.

### 4.6 Combine upload, execution, and download with the helper

Now that you have seen the underlying steps, use the local helper to combine
them. From the repository root, run:

```bash
python tutorial/run_job.py ./passage.txt \
  --project="$PROJECT_ID" --region="$REGION" --job="$JOB_NAME" \
  --input-bucket="$INPUT_BUCKET" --output-bucket="$OUTPUT_BUCKET" \
  --src=en --dest=fr --download-dir=./results
```

The helper prints each gcloud command, uploads the file, waits for the job to
succeed, downloads its output, and checks for the completion manifest and files.
Open the reported local result folder and play `speech.wav` inside its attempt
folder. You have submitted cloud work and retrieved the result from your laptop.

<details>
<summary>More detail — helper options, naming, and authentication</summary>

- `--dry-run` prints commands without uploads, executions, or local file writes.
- `--no-download` leaves outputs in Storage.
- `--help` lists all options. Supply bucket **names**, without `gs://`.
- The helper generates a run name from a UTC timestamp plus a short random ID,
  used in both buckets. The job adds its separate UUID attempt folder. The
  helper does not currently accept a custom run-name prefix.
- Python and a signed-in gcloud CLI are enough for this helper; it does not
  require the app's Python packages or local application ADC. The cloud job
  obtains ADC from its attached runtime account.
- An upload or execution failure stops the helper before later steps. It retains
  cloud files and partial local downloads for inspection, rather than deleting
  them automatically. A new invocation allocates a new run folder.

For a fuller command reference, see the [job workflow guide](docs/job-workflow.md).

</details>

## Clean up after the tutorial

1. Download any results you want to keep.
2. In **Cloud Run**, delete the function and web service you created, then delete
   the job under **Jobs**. Check the names against your worksheet.
3. In **Cloud Storage**, delete your tutorial input/output objects and buckets
   when you no longer need them. Remove the dedicated tutorial service accounts
   after they are no longer attached to resources.
4. A source-built function also leaves an image in Artifact Registry. Remove its
   unused image when appropriate. Keep unrelated course resources and the shared
   public tutorial image available for others.

## Troubleshooting and further reading

<details>
<summary>Something failed — where to look first</summary>

| Symptom | Check |
| --- | --- |
| A resource is missing | Project ID and region in the console; full bucket name |
| Function build fails | Build logs, runtime, requirements, entry point, and build-account permissions |
| Text translation fails | Service logs and external translation provider availability |
| Play audio is disabled | `ENABLE_SPEECH=true`, deployed revision, and page reload |
| Speech request is denied | Attached identity, Vertex API, inference/quota permissions, model location |
| A local app cannot authenticate | Application ADC setup, impersonation permission, credential mount if containerized |
| Job cannot read or write an object | Exact `gs://` paths and bucket grants for the **job** account |
| Job starts a server instead of finishing | Command `python` and separate batch arguments |
| Output folder is empty or incomplete | Execution status, logs, and whether a completion manifest exists |
| Helper cannot launch with overrides | Your gcloud caller's override permission, not the runtime account's Storage role |

[Function deployment](https://docs.cloud.google.com/run/docs/quickstarts/functions/deploy-functions-console),
[container deployment](https://docs.cloud.google.com/run/docs/deploying),
[service identity](https://docs.cloud.google.com/run/docs/configuring/services/service-identity),
[job execution](https://docs.cloud.google.com/run/docs/execute/jobs).

</details>

<details>
<summary>For instructors and contributors — source, rehearsal records, and image version</summary>

The source and build instructions live in the
[application development guide](tutorial/app/README.md). Source inspection is
optional for the deployment walkthrough. The helper is
[`tutorial/run_job.py`](tutorial/run_job.py).

The public image's tested Linux AMD64 digest is:

```text
sha256:a1d4858aca190421b8aabeb0d5fcc6fda0d0902486ca5f34319adcf42453c6e6
```

It is published under a temporary personal Docker Hub namespace until the
maintainer has course-organization publishing access. Students supply their own
project, runtime accounts, and buckets; the image contains no instructor
credentials. The earlier private Artifact Registry rehearsal image is not the
student distribution path.

The instructor confirmed local and cloud browser playback. Automated live
rehearsals covered public image pull, service translation/speech, two direct job
executions, output retrieval, and the combined helper. The console click-through
still deserves an instructor rehearsal; button labels can vary as Google updates
the UI. Command alternatives have been checked against the matching documentation,
but not every alternative was separately executed on a new student project.

- [Console function rehearsal record](docs/function-rehearsal.md)
- [Cloud Run rehearsal record](docs/cloud-run-rehearsal.md)
- [Job and helper rehearsal record](docs/job-rehearsal.md)
- [Teaching-flow review](docs/flow-review-opus55.md)
- [Original tutorial](docs/original-tutorial.md)

GitHub's native
[collapsed sections](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/organizing-information-with-collapsed-sections)
keep command alternatives and deeper explanations expandable in this README.

</details>
