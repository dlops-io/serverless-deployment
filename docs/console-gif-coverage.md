# Console GIF coverage

These are annotated real screenshots with animated pointer/click guides, not
continuous screen recordings. Forms can be revisited without creating duplicate
resources; captions distinguish unsubmitted previews, live app interactions, and
previously completed job results. Account bars and unrelated errors are excluded.

| Tutorial block | GIF coverage |
| --- | --- |
| 1.1 Function setup | Navigation, name, region, runtime, public invocation, Create control, earlier Source destination. |
| 1.2 Code/deploy/test | Handler, requirements, completed rollout, live response. |
| 2.1 Local container | Actual public image run locally, real translation, speech disabled. |
| 2.2 Container deployment | Existing image, name/region, public access, Create control; no duplicate deployed. |
| 3.1 Runtime account | IAM entry, creation form preview, existing project grants and account email. |
| 3.2 Speech configuration | Existing service Security selector → Containers → all three environment variables → View diff & redeploy → Deploy changes → completed rollout; live app checkpoint. |
| 3.3 Local identity | Principals with access → Grant access → Token Creator preview. Credential login and files intentionally remain text-only. |
| 4.1 Storage | Complete private bucket creation through every Continue, Create, PAP Confirm, and resulting Configuration; separate folder/upload controls and existing object URI. |
| 4.2 Storage grants | Job principal plus input Object Viewer/output Object Creator previews; grants not saved. |
| 4.3 Job | Image/name/region, separate command/argument chips, environment, runtime identity, timeout/retries and Create control. |
| 4.4 Execution/results | Execute control, historical successful executions, success summary, all three private output files, audio Download and playback. |
| 4.5 Terminal submission | Explicitly labeled dry-run command preview: upload → execute → download. |
| 4.6 Helper | Actual helper dry-run output animated with a persistent dry-run label. |

## Intentional omissions and capture limitations

- Conditional API enablement was not recorded; the project was already configured
  and the API details page intermittently failed to load.
- The speech-settings clip now records the actual inline existing-service workflow;
  there is no Edit & deploy new revision action in this observed console.
- Identity creation/grant forms are previews combined with inspection of existing
  permissions. They do not establish that a new identity or grant was submitted.
- The local file chooser, upload wait, deployed-revision/log inspection, and task
  log contents are not recorded. Screens with errors or indefinite loading were
  excluded rather than passed off as useful tutorial frames.
- Job results come from earlier successful rehearsals. In this capture session,
  pressing Execute returned a generic console failure. No fresh successful run
  is claimed. Historical status and the private output objects were inspected;
  console listing errors required recovery before clean result captures.
- The console displays roles/aiplatform.user as Agent Platform User in the role
  drawer. The existing runtime grants were independently checked with gcloud;
  the role IDs remain aiplatform.user and serviceusage.serviceUsageConsumer.
- Rehearsal bucket names/prefixes and a unique preview job name appear in the
  images. Students must substitute their own project, identity, and Storage paths.
- Cleanup remains text-only; no demo resources were deleted for illustration.

The short-lived local capture container was stopped after the local app capture.
Two private capture buckets were created on October 22 to record the complete
wizard, and the existing web service was redeployed with its speech variables.
No new IAM grants or public exposure were added.
