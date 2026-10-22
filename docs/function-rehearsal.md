# Console function rehearsal

The function example was recreated through the GCP console in project
`ac215-project`, using service `translate-function-rehearsal` in
`northamerica-northeast2` with Python 3.12, public invocation, zero minimum
instances, and a maximum of two instances.

The inline editor's default handler was replaced with the tutorial translation
handler, and requirements were set to `functions-framework==3.10.2` and
`googletrans==4.0.0rc1`. The entry point remained `hello_http`.

After selecting **Save and redeploy**, the console reported successful source
build, service update, revision creation, and traffic routing. Opening the public
URL with English text and French as the destination returned **Bonjour à tous**.
The **Observability → Logs** view showed HTTP 200 for that translation request.
A separate browser favicon request returned 404; the app does not supply an icon.

The editor displayed a transient code-editing warning. Contents were verified
in both files before deployment; the build and live request succeeded. Captures
for the README exclude the warning popup, account notifications, and unrelated
project banner. The GIF is assembled from captured UI states, not a continuous
video recording; waiting time is omitted.

Assets:

- `images/console/function-entry.gif`: open function creation from Services.
- `images/console/function-deploy-test.gif`: handler, requirements, completed
  rollout, and browser response.

The rehearsal resource remains available; no cleanup has been performed.
