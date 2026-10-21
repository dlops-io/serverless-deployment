# Cloud Run rehearsal

The instructor confirmed local translation and browser audio playback. Live cloud
checks then returned HTTP 200 for the UI, translation, and speech. The speech
response was valid mono 24 kHz WAV. Cloud browser playback is awaiting manual
confirmation; this record does not claim the batch job is implemented.

- Project: `ac215-project`
- Cloud Run service: `translation-demo`
- Service region: `northamerica-northeast2`
- Vertex model location: `us-central1`
- Runtime identity: `translation-demo@ac215-project.iam.gserviceaccount.com`
- Image: `northamerica-northeast2-docker.pkg.dev/ac215-project/cloud-run-source-deploy/translation-demo@sha256:1837fa5fe52744d22847d9899b9a294eff32141c5f7289af99ba2f9749b69a56`
- Source commit: `4096c0f`
- Public app: https://translation-demo-129349313346.northamerica-northeast2.run.app

The image is in private Artifact Registry, not Docker Hub. Students in other
projects cannot assume they can pull it. Publish a student-accessible version
before replacing the tutorial image placeholders.

The deployed service uses its attached identity through ADC. No local ADC file or
service-account key was included in the image or uploaded to the service.
Public invocation and the runtime's permission to call Vertex AI are separate.
The service has 512 MiB memory, one CPU, zero minimum instances, two maximum
instances, concurrency four, and a 120-second request timeout.

To reproduce deployment with this project's existing image and identity:

```bash
gcloud run deploy translation-demo \
  --project=ac215-project --region=northamerica-northeast2 \
  --image=northamerica-northeast2-docker.pkg.dev/ac215-project/cloud-run-source-deploy/translation-demo@sha256:1837fa5fe52744d22847d9899b9a294eff32141c5f7289af99ba2f9749b69a56 \
  --service-account=translation-demo@ac215-project.iam.gserviceaccount.com \
  --set-env-vars=ENABLE_SPEECH=true,GOOGLE_CLOUD_PROJECT=ac215-project,GOOGLE_CLOUD_LOCATION=us-central1 \
  --allow-unauthenticated --memory=512Mi --cpu=1 \
  --min-instances=0 --max-instances=2 --concurrency=4 --timeout=120
```

[Cloud Run image deployment](https://docs.cloud.google.com/run/docs/deploying)
and [service identity configuration](https://docs.cloud.google.com/run/docs/configuring/services/service-identity).
