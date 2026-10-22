I'm Claude Opus 5.5 (`claude-opus-5-5`). That's how my runtime identifies me; I have no separate way to verify it.

# Audit: README.md and embedded GIFs at `396668f` (`codex/four-part-tutorial`)

## Verdict

**The written steps are mostly right, but the GIFs do not show the full workflow.** Three of the four fixes you asked me to check hold up in the frames. The Agent Platform labels and `storage-bucket-setup.gif` are clean. The section 3.2 GIF does show the inline **View diff & redeploy → Review changes to be deployed → Deploy changes** flow. However, that recording changed only the environment variables, because the service account was already attached. Its Security tab also shows **Require authentication** on the service Part 2 says to make public.

Apart from the bucket wizard and the 3.2 deploy, no GIF ends with a submitted action. The function and service **Create**, the service-account creation, every IAM **Save**, the job **Done** and **Create**, the job **Execute**, the file upload and the Logs view are all missing. The execution GIF also pairs one execution with the output files of a different one.

Three problems would mislead a student who copies the GIF:

- `job-identity-limits.gif` puts the click ring on **Create new service account** instead of the job account.
- `identity-create.gif` shows the IAM **Edit access** dialog in place of the wizard's **Permissions (optional)** step, with a different display name from the one the README asks for.
- `terminal-job-steps.gif` shows commands that differ from the ones in section 4.5.

The only obsolete human-facing "Vertex AI" text is inside the shipped app image, not in the README.

Method: I extracted every hold frame (≥1 s) from all 16 embedded GIFs to `/tmp/ac215-opus-gif-audit/<gif>/f###_t##.##s_hold.png`, plus contact sheets and selected intermediate frames, and read them at full size where text was uncertain. Frame indices and timestamps below are GIF frame numbers and cumulative display times. I edited nothing and ran no cloud commands.

---

## Prioritized findings

### P1: the GIF contradicts the step or would mislead someone copying it

**1. `job-identity-limits.gif`: click ring on the wrong item (README 733–735, step 4.3.7)**
- **Observed:** frame 15 (t=3.72 s) has the dropdown open with **Translation audio job / translation-audio-job@ac215-project…** listed. The click ring sits at about (520, 465), on the boundary between **Create new service account** and **Enter manually**, below the option. The next hold (f21, t=6.27 s) shows "Translation audio job" selected anyway.
- **Fix:** move the ring onto the "Translation audio job" row (about y=418).

**2. `job-identity-limits.gif` and `job-command-settings.gif`: Done and Create are never clicked, and the container stays "(Not saved)" (README 723–741, steps 6 and 9)**
- **Observed:** f5 (t=0.45 s) shows the three variables and a visible **Done** button with no click. The next state jumps to the Security tab. f27 and f33 (t=9.18 s, 12.09 s) still read **Container: ac215-translation-demo-1 … (Not saved)**. In f33 the caption says "select Create", but the pointer is on the **Execute job immediately** checkbox and Create is never clicked.
- **Written:** "Select **Done** after adding all three", then "select **Create**."
- **Fix:** recapture with a Done click, a saved container card and a Create click followed by the created-job page. If that isn't possible, have the caption say Done and Create were not performed.

**3. `job-command-settings.gif`: the expand click would collapse the section, and the container-row expansion is missing (README 701–703, step 4.3.4)**
- **Observed:** f11 (t=3.36 s) already shows **Containers, Connections, Security** expanded, with the Containers tab and the collapsed row **Container: ac215-translation-demo-1 (Not saved)** visible. f21 (t=6.63 s), captioned "3. Expand Containers, Connections, Security", puts the click ring on that already-expanded header; clicking it would collapse the section. f27 then shows **Edit Container** open, but no frame shows the row chevron being clicked.
- **Written:** "Expand **Containers, Connections, Security**. In **Containers → Edit Container → Settings**…" The README never says to expand the container row.
- **Fix:** add "expand the container row (chevron) to open **Edit Container**" to step 4. Recapture or retime f21 so the expand click happens before the section is open.
- **Also:** f0 shows Region **europe-west1 (Belgium)** and f11 shows Toronto. The region selection is not recorded.

**4. `identity-create.gif`: wrong dialog and changing values (README 356–379, steps 3.1.2–5)**
- **Observed:**
  - f15 (t=3.66 s): **Service account name** = `translation-demo`, and **Service account description** = "Calls Gemini speech for the translation app".
  - f33 (t=13.29 s): the final account details page shows Name **Translation demo runtime** and an empty Description, so the values change between stages.
  - f27 (t=10.08 s), captioned "4. Project roles…": the dialog is **Edit access to "ac215-project"** with a Principal/Project header, **Save / Test changes / Cancel**, and **Help me choose roles**. That is the IAM-page edit-principal dialog, not the create wizard's **2 Permissions (optional)** step, and Save is not clicked.
  - f21: the pointer rests on **Create and continue** without a click ring.
  - The wizard's own **Create and close** button is visible in f15, but the README never names a finishing button ("then finish creation").
- **Written:** name `Translation demo runtime`; "In **Permissions (optional)**, add…"; "Continue past **Principals with access (optional)**… then finish creation." The README caption says only "creation form is an unsubmitted preview."
- **Fix:** recapture with a throwaway ID going through Create and continue → Permissions (optional) with both roles → Continue → the finishing button. Alternatively, keep this GIF but caption f27 as "the same roles as seen later on the IAM page (Edit access)". Also name the final button in step 4 (it shows **Create and close** at the bottom of the wizard; the button after step 3 is not recorded). Remove the description from the capture or add it to the README.

**5. `job-execution-results.gif`: execution and outputs don't match, and a capture failure isn't disclosed (README 780–811)**
- **Observed:** f15 (t=3.72 s) clicks into **translation-audio-4wkb9**, created Oct 21 2026 at 1:40:29 AM. f27 (t=9.18 s) shows outputs in `rehearsal-001/46cd63c6…` created at 1:26:09–1:26:10 AM. Those times match execution **v4r7d** (1:25:48 AM), not 4wkb9. f5 (t=0.45 s) shows the pointer on **Execute** with no click ring. `docs/console-gif-coverage.md` says "pressing Execute returned a generic console failure" during this capture session.
- **Not shown:** Logs (step 4.4.2), the navigation from Cloud Run to Cloud Storage → bucket → `run-001` → attempt folder (step 3), and an actual Download click. f33 has the pointer near Download but no ring, and f39 plays the audio in the console rather than downloading it.
- **Fix:**
  - Open v4r7d in f15, or show 4wkb9's own output prefix.
  - Add to the caption: "Execute was not run successfully in this capture; results are from execution v4r7d."
  - Either add a Logs frame or state that logs aren't shown. The caption's "task-log inspection is not shown" covers it only partly.

**6. `identity-speech-settings.gif`: the identity change isn't really recorded, and the access setting conflicts with Part 2 (README 405–442)**
- **Observed:**
  - f4 (t=2.75 s), Security tab: Authentication has **Require authentication** selected and **Identity and Access Management (IAM)** checked. Frames 5–9 show a yellow banner with an **Allow public access** button; its text is scrolled off.
  - f30 (t=34.35 s): the tab strip reads **Containers \*** with an asterisk, while **Security** has none.
  - f31–34: **Review changes to be deployed** lists only **Container → Environment variables: Current None → New ENABLE_SPEECH / GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION**. The values column is clipped.
  - So the service account was already attached and selecting it changed nothing. The coverage doc confirms the service was "redeployed with its speech variables."
- **Effect:** a student doing this fresh will see a Security asterisk and a service-account row in the diff that the GIF never shows. The visible "Require authentication" also conflicts with Part 2's **Allow public access** (README 283) and could prompt a student to change it.
- **Written:** "check the new environment variables" (the values aren't visible in the recording). The caption says "select the runtime identity, add all three variables, review the diff."
- **Fix:** recapture starting from the default compute identity so the diff includes the service account. Scroll the diff horizontally so the values show. Crop or explain the Authentication panel, and confirm with `gcloud run services get-iam-policy` that `allUsers` has `roles/run.invoker`.

**7. Section 4.5's commands don't match `terminal-job-steps.gif` (README 868–906)**
- **Observed:** f3 (t=0.72 s) uploads `/home/chris/teaching/AC215/serverless-deployment/tutorial/app/examples/passage.txt` to `gs://ac215-project-lecture14-input/run-20261022-040025-72b301aae030/passage.txt --quiet`. f8 (t=5.88 s) executes with `--dest,fr`, and f12 downloads to an absolute `/home/chris/...` path.
- **Written:** `./passage.txt` → `run-002/passage.txt`, `--dest,es`, prefix `run-002`, download to `./results`.
- The caption does say the clip comes from the helper's printed commands, but the GIF is placed under the steps it doesn't match, and it shows the instructor's home path.
- **Fix:** render the exact section 4.5 commands with `$INPUT_BUCKET`-style placeholders. If that's not done, move this GIF to 4.6 and drop it from 4.5.

**8. The function GIFs don't show code being replaced (README 105–107 and 128–154; `function-setup.gif` and `function-deploy-test.gif`)**
- **Observed in `function-setup.gif`:**
  - f49 (t=15.0 s), "Select Create": the pointer is on Create with no ring, and no creation follows.
  - f55 (t=17.91 s): the service is **translate-function-rehearsal**, not the `translate-function` typed in f15. The banner reads **Creating service**, and the editor already contains the googletrans handler. The caption says "replace the sample handler next."
- **Observed in `function-deploy-test.gif`:** f0–f38 show files that already contain the final code, and no edit or paste happens. f47–f59 show a completed rollout and a click on the URL. f68 (t=13.96 s) shows the page text "Bonjour à tous" with no address bar, so the query string can't be seen. The Logs/HTTP 200 check in step 1.3.5 is asserted in the caption (README 185–186) but isn't in the GIF. The no-argument call and the `el`/`hi`/`zh-cn` calls aren't shown either.
- **Fix:** add the name mismatch and "code already replaced" to the 1.1 caption. Change the 1.2 caption to "the files after replacement; editing not recorded." Either add a Logs frame or say "200 was observed in the rehearsal log (`docs/function-rehearsal.md`), not shown here."

**9. Obsolete human-facing "Vertex AI" text in the shipped image**
- **Observed:** `web-translation-speech.gif` f37 (t=12.09 s) shows "Translation uses an external provider. Speech uses Vertex AI."
- **Sources:**
  - `tutorial/app/translation_demo/templates/index.html:51` (tooltip) and `:55`
  - `speech.py:76, 88, 113, 115, 119` (user-visible error messages)
  - `__main__.py:46` (step text)
- The README itself has no human-facing "Vertex AI" labels. The technical identifiers (`roles/aiplatform.user`, `aiplatform.googleapis.com`, `VERTEX_TTS_*`, `vertexai`) are used correctly and should stay.
- **Fix:** change the strings to "Agent Platform," rebuild, publish a new tag and update README 57/75/279/697 and the digest at 1004. Until then, recapture f37 or add a caption note.

### P2: actions the GIF omits that the step requires

**10. `storage-input-uri.gif` (README 582–614)**
- **Observed:**
  - f0–f5: the **Create folder** dialog is already open with `run-001` typed, and **Create** is never clicked; the pointer stops at about (740, 400).
  - f15: the **Upload ▾** menu shows **Upload files / Upload folder**, with the ring on Upload files but no file chooser.
  - It then cuts to the existing `rehearsal-001/passage.txt` (created Oct 21 1:24:03 AM).
  - f31: the pointer sits next to the **Cloud Storage URI** copy icon with no click ring.
- The bucket is `ac215-project-lecture14-input`, not the `…-capture-input…` bucket visible at the top of `storage-bucket-setup.gif` f0. The caption admits the preview but not the bucket switch.
- **Fix:** add "a different, pre-existing input bucket" to the caption, and add a ring on the copy icon.

**11. `storage-job-permissions.gif` (README 641–664)**
- **Observed:** all three holds (f5, f11, f17) show only the filled-in **Grant access to "ac215-project-lecture14-input/-output"** dialog. Bucket → **Permissions** → **Grant access** navigation is missing, and so is **Save**. Steps 4.2.1–2 (create the job account and grant its project roles) have no recording at all.
- **Fix:** say in the caption that the account creation and project grants aren't shown, or add frames for them.

**12. `container-setup.gif` (README 274–299, section 2.2)**
- **Observed:**
  - f15: **Deploy one revision from an existing container image** is already selected, with no click.
  - f31: **Service scaling** is cut off at the bottom, so the "zero minimum instances" in step 4 is never shown.
  - f35: the pointer is on **Create** with no ring.
  - The startup-command check in step 5 ("Leave the image's startup command unchanged") has no frame; the Container(s) section is never opened.
- **Fix:** add a frame of Service scaling (min 0). Drop "Keep the startup command" from the f35 caption, or show the container section.

**13. `identity-impersonation.gif` (README 489–504)**
- **Observed:** f29 picks the role through **Quick access → Service Accounts → Service Account Token Creator**. The caption on f35 (t=10.08 s) reads "Add your own user email… then Save (preview)", but **New principals** is empty and Save is off-screen. The order (role, then principal) is the reverse of the README's.
- **Fix:** match the caption to what's shown, and mention the **Service Accounts** category in the role picker.

**14. `terminal-job-helper.gif` is not verbatim helper output (README 913–932)**
- **Observed:** f4 runs `python tutorial/run_job.py tutorial/app/examples/passage.txt` without `--region` or `--job` (they fall back to the defaults at `run_job.py:25–26`). README 914–917 passes both and uses `./passage.txt`. The GIF goes straight from the execute command (f13) to the download command (f17), but `run_job.py:60` prints `Cloud outputs: gs://…/` between them, even in dry-run.
- The caption says "This is actual helper **dry-run output**," but the frames are edited.
- **Fix:** use the README's invocation and include the `Cloud outputs:` line, or call it "excerpted."

### P3: text precision, student flow and consistency

15. **Required caller permissions are only in collapsed alternatives.** Attaching a service account in the console also needs `iam.serviceAccounts.actAs` (**Service Account User**); see README 395–399 and 683–684. Section 4.5's override execution needs **Cloud Run Jobs Executor With Overrides** (685–686). Both live in "Equivalent gcloud commands" boxes that the README tells students to skip (19–21). Students who only follow the console will reach 3.2, 4.3 or 4.5 without being told about these. **Fix:** add a one-line prerequisite to 3.2, 4.3 and 4.5.

16. **The 2.2 gcloud alternative is not equivalent to the console steps.** README 311–312 sets `--max-instances=2 --cpu=1 --memory=512Mi --concurrency=4 --timeout=120`, and none of these appear in the console steps (283–286). Either add them to step 4 or say the console keeps the defaults.

17. **Section 4.1 step 3 verification (README 580).** The README says to check private access on the **Configuration** tab. In `storage-bucket-setup.gif`, f139/f145 show public access only in the header ("Public access: Not public"); the visible Configuration overview rows don't include it. Reword to "the header shows **Public access: Not public**." The wizard also shows **Enable Rapid Cache**, **IP filtering (optional) → Configure** and **Add cross-bucket replication** (f55, f81, f97), which the README doesn't mention. They're harmless defaults, but a single "leave the other options at their defaults" would cover them.

18. **Resource names change between GIFs.** The bucket GIF creates `ac215-project-lecture14-capture-output-20261022`. Later GIFs use `ac215-project-lecture14-input/-output`, `rehearsal-001` (URI GIF) and `run-001` (job arguments, `job-command-settings.gif` f33). The job is named `translation-audio-rehearsal` in the create GIF and `translation-audio` in the execution GIF. The README names only some of these switches.

19. **API enablement is never recorded.** That covers **Agent Platform API** (README 354), **IAM Service Account Credentials API** (494) and the conditional prompt in 1.1. The Library display names can't be verified from the recordings. Line 494 also doesn't say where to search ("APIs & Services → Library").

20. **`docs/job-workflow.md:128` doesn't match the README.** It uses `--dest,fr` for `run-002`, while README 880 uses `es`.

21. **Orphaned assets.** `images/console/function-entry.gif` and `function-deploy-complete.png` aren't embedded anywhere, and `docs/function-rehearsal.md` still lists `function-entry.gif`. README 1023–1024 links the historical `flow-review-opus55.md` and `original-tutorial.md` without marking them as historical.

### Fixes that check out

- **Bucket wizard.** All 18 holds match README 563–580 in order: **Create** → name → **Continue** → **Region** → Toronto → **Continue** → Standard → hierarchical namespace unchecked → **Continue** → public-access prevention plus **Uniform** → **Continue** → soft delete default, versioning and retention unchecked → **Create** (f113, ring on Create) → **Public access will be prevented** with the checkbox checked → **Confirm** (f123, background "Processing…") → bucket details → **Configuration** showing Region/Toronto/Standard (f145). Values stay the same across stages.
- **3.2 labels.** **View diff & redeploy**, **Review changes to be deployed**, **Serve this revision immediately**, **Deploy changes**, and "Update service: Updating service / Creating revision / Routing traffic: Completed" all match README 419–423 exactly (f30–f36).
- **Agent Platform labels in the README.** `identity-create.gif` f27 shows **Agent Platform User** with the help text "Grants access to use all resource in Agent Platform." The technical IDs are kept correctly.
- **Job argument chips.** `job-command-settings.gif` f33 shows 13 separate argument chips, matching README 709–720 one for one. `job-identity-limits` f27 shows Task timeout 5 / **minute** / retries 0, and the Settings tab (f27 of `job-command-settings`) shows 512 MiB / 1 CPU.

---

## Per-GIF coverage

| GIF (README line) | What's recorded | What's missing or only previewed |
|---|---|---|
| function-setup (112) | Write a function; name; region picker; Python 3.12; Allow public access; pointer on Create | API prompt; Create click (no ring, nothing created); wait. Source frame is a different service (`-rehearsal`) with code already replaced |
| function-deploy-test (180) | Existing handler/requirements; Save and redeploy click; Completed rollout; URL click; "Bonjour à tous" | Edit source; the actual edit/paste; entry-point setting; the query URL (no address bar); no-arg/el/hi calls; Logs/200 |
| container-local-app (265) | Translate English→French with audio disabled | `docker run`; localhost URL (no address bar); Ctrl+C |
| container-setup (294) | Deploy container; image URL; name and region; public access; request-based billing; pointer on Create | Radio click; min instances; container command; Create; ready state; URL; Revision History; Logs |
| identity-create (374) | Create service account; name/ID preview (wrong display name); Create and continue (no ring); IAM **Edit access** dialog with both roles; existing account email | Real wizard Permissions step; Continue/finish; any Save; API enablement |
| identity-speech-settings (436) | Security → service-account picker (no actual change); Containers → three variables; View diff & redeploy; diff; Deploy changes; Completed | A real identity change in the diff; variable values in the diff; Authentication shown as Require authentication |
| web-translation-speech (447) | Translate; Play audio; audio player; "Speech uses Vertex AI." | Cloud URL (no address bar); reload; error/Logs path |
| identity-impersonation (499) | Principals with access; Grant access; role picker; Token Creator selected | Principal email; Save; API enablement; ADC login |
| storage-bucket-setup (597) | Complete output-bucket wizard, including Confirm and Configuration | Input bucket (README acknowledges) |
| storage-input-uri (608) | Create folder dialog (unsubmitted); Upload menu; open existing `rehearsal-001/passage.txt`; URI row | Create click; file chooser; upload; copy click; uses a different bucket from the wizard |
| storage-job-permissions (659) | Two filled Grant access dialogs | Navigation; Save ×2; job account creation; project role grants |
| job-command-settings (746) | Create job; image/name/Toronto/1 task; Edit Container command and 13 argument chips; 512 MiB/1 CPU | Jobs list → Deploy container; region pick; container-row expansion; misleading expand ring |
| job-identity-limits (757) | Three env vars; job account selected (ring misplaced); timeout 5 min; retries 0; Execute immediately unchecked | Done; container saved; Create; created job |
| job-execution-results (803) | Job page with History; open 4wkb9 (1 Succeeded); output files from a different execution; speech.wav details; console playback | Execute click (failed in capture per coverage doc); Logs; Storage navigation; Download |
| terminal-job-steps (900) | Dry-run text of helper-generated commands | The section 4.5 commands themselves (run-002/es); any execution |
| terminal-job-helper (928) | Edited dry-run output | `--region/--job` as written; `Cloud outputs:` line; any real run or download |

---

## Remaining uncertainties

- **Public access in 3.2.** The banner text in `identity-speech-settings` f5–f9 is never visible. "Require authentication + IAM" may be how this console version displays an `allUsers` invoker binding. `docs/cloud-run-rehearsal.md` records `--allow-unauthenticated`. Running `gcloud run services get-iam-policy translation-demo --region=northamerica-northeast2` would settle it.
- **Creating a job with "(Not saved)".** I can't tell from the frames whether clicking **Create** while the container card says "(Not saved)" keeps the edits. Only a recorded Create would answer that.
- **Unrecorded labels.** The API Library names (**Agent Platform API**, **IAM Service Account Credentials API**), the service-account wizard's finishing button, the service **Observability → Logs** tab and the Jobs list **Deploy container** button never appear in a frame.
- **Where the app was running.** No address bar appears in `container-local-app` or `web-translation-speech`, so I can't confirm localhost:8086 versus the Cloud Run URL.
- **ADC quota project.** Whether `gcloud auth application-default set-quota-project` behaves as described after an impersonated ADC login (README 515–516) can't be checked from the recordings.
- **Job output permissions.** Whether `roles/storage.objectCreator` alone is enough for the job's output writes is supported by `docs/job-rehearsal.md`, but it isn't shown in any GIF.