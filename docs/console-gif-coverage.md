# Console GIF coverage

These GIFs use real screenshots, with added pointer/click guides. They are not
continuous recordings. Never include loading failures or unrelated warning popups.

| Tutorial section | Current coverage |
| --- | --- |
| 1.1 Function setup | Steps 1–6; API enablement conditional and not prompted. Creation form replay plus earlier successful Source screenshot. |
| 1.2 Code, deploy, test | Handler, dependencies, completed rollout, response. |
| 2.1 Local app | Still needs its own local-to-cloud comparison capture. |
| 2.2 Container setup | Configuration steps 1–5; revision/log inspection still needs capture. |
| 3.1 API and identity | Still needs capture. |
| 3.2 Runtime identity and speech | Browser translation/audio checkpoint captured; account and environment configuration still needs capture. |
| 3.3 Local ADC | Still needs capture; exclude credentials and sign-in details. |
| 4.1 Buckets and input | Still needs capture. |
| 4.2 Bucket permissions | Still needs capture. |
| 4.3 Job configuration | Still needs capture. |
| 4.4 Execute and collect output | Still needs capture. |
| 4.5–4.6 Terminal and helper | Still needs capture. |

The latest capture session encountered a Cloud Run “Failed to load” page, an
unavailable function source fetch, and an IAM page whose project selector and
content did not finish loading. Those screens were excluded. The already
published setup/checkpoint clips do not establish complete coverage of the
remaining sections.
