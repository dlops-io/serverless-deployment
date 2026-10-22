# Console walkthrough recording coverage

The GIFs combine real screenshots with added pointer/click guides. They are not
continuous videos. Long build/deploy waits and accidental navigation/recovery
are shortened; no submitted action is inferred from an unsubmitted preview.
Cropped toolbar or navigation details are labeled as details. Terminal clips
animate actual saved command output, rather than simulated successful runs.

| Tutorial block | Recorded actions and verification |
| --- | --- |
| 1.1 Function setup | Services → Write a function → name → Toronto → Python 3.12 → Allow public access → actual Create → created Source editor. |
| 1.2 Code/deploy/test | Actual replacement of main.py and requirements.txt; hello_http; Save and redeploy; completed rollout; default, French and Greek requests; matching HTTP 200 request log. |
| 2.1 Local container | Actual Docker startup output for the README image/port; localhost app; visible Translate action; French result and disabled speech; actual Ctrl+C shutdown. |
| 2.2 Container service | Actual public service creation, all advanced controls, Done, Create and ready rollout; separate speech-disabled baseline translation recapture; representative revision/log views. |
| 3.1 Runtime identity | Actual new translation-demo-runtime account, both project roles in the creation wizard, Continue and Done; resulting account email and no keys. Agent Platform API Enabled is separately shown in a current console screenshot. |
| 3.2 Speech setup | Default identity → new runtime identity → three variables → full review diff → Deploy changes → ready rollout → actual browser translation and audio playback. |
| 3.3 Local identity | Actual developer principal and Service Account Token Creator selection/replacement → Save; account-scoped binding verified. |
| 4.1 Bucket creation | Complete private output-bucket creation: every Continue, Toronto/Standard/Uniform/public-access prevention, default soft delete, Create, public-access Confirm, resulting configuration. |
| 4.1 Input upload | Actual run-001 folder creation → Upload files → passage.txt selected through file chooser → successful upload → same object's Storage URI copied. |
| 4.2 Storage grants | Input/output Permissions → Grant access → job principal → the respective Viewer/Creator role → actual Save; scoped grant verified in the filtered Permissions list. |
| 4.3 Job creation | Jobs → Deploy container → image/name/region → each command/argument chip → all variables → Done → timeout/retries → job identity → actual Create → empty History. |
| 4.4 Execution/results | Actual console Execute → translation-audio-hq9f5 succeeded → task View logs → exact output_uri → matching run-001/de2f41… attempt → all three files → media-tab ⋮ → Download selected and French text response. |
| 4.5 Terminal commands | Exact README upload → Spanish execution → download commands; successful execution translation-audio-8mw6k and verified files. |
| 4.6 Helper | Actual helper invocation, upload → French execution translation-audio-jnlmc → download → manifest/file validation; complete output retained. |

## Boundaries and substitutions

- Required APIs were already enabled. The conditional Enable button is described
  for a new project; the current Agent Platform API page and enabled state were
  verified directly. APIs are not disabled in a shared project just to film them.
- The system file picker differs by OS and is not part of the browser screenshot
  surface. Its selection step is stated in the GIF caption and performed with
  the real file; the successful upload and exact resulting object are shown.
- Browser sign-in and credential JSON contents are intentionally not recorded.
  The ADC commands remain in the optional local-development instructions.
- The bucket-creation clip creates the instructor's private
  `ac215-project-lecture14-capture-output-20261022`; the upload/job clips use the
  instructor's `ac215-project-lecture14-input` and `-output`. These are independent
  demonstrations of the same controls, not a claim that the capture bucket was
  the job's input. Students must consistently use the two names on their worksheet.
- Job execution, task logs and output timestamps/paths in the results GIF all
  belong to **translation-audio-hq9f5**. No historical execution is paired with
  another execution's artifacts.
- Part 2 combines separate rehearsals at the same public URL. The successful
  translation result was recaptured with speech temporarily disabled after the
  runtime identity had been attached. Its HTTP 200 log is an earlier request,
  not the recaptured request. Translation does not use the runtime identity.
- Static navigation details are labeled; the job Containers/row-chevron and
  upload Live object tab details are cropped actual earlier Console captures
  of those controls, with unrelated older values excluded.
- Console listing failures were recovered before useful captures; unrelated
  failed project resources and notification overlays are excluded from toolbar
  details. There is no fabricated console UI or substituted success message.
- Browser download behavior varies. In this browser the WAV link opened a media
  tab; its menu offers Download. The text link opened the translated text
  directly. The CLI and helper recordings verify the saved files.
- Cleanup remains text/CLI based. The isolated lifecycle helper has live setup,
  functional, same-name recreation, interrupted-setup recovery and cleanup
  evidence in [lifecycle-live-check.md](lifecycle-live-check.md).

The original audit is a snapshot of commit `396668f` in
[console-audit-opus55.md](console-audit-opus55.md). The replacement recordings
passed the [final Opus 5.5 visual review](console-signoff-opus55.md). Its remaining
wording and annotation corrections are recorded in
[the resolution report](console-audit-resolution.md).

## README step headers

Each GIF has a top ribbon identifying the current README step, changing as the
action changes. Unnumbered sections 3.3 and 4.6 use their section number. The
original captions, cursor guides, all 714 screenshot/terminal frames and every
frame duration are unchanged. Pixel-for-pixel body comparison verified this
across all 16 GIFs.

The mapping is in `tutorial/gif_steps.json`. With Pillow installed, run
`python tutorial/label_gifs.py` to update the ribbons. Rerunning replaces the
ribbon rather than stacking another one. Update the mapping when recording
timelines or README numbering change.
