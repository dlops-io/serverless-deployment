I'm Claude Opus 5.5 (`claude-opus-5-5`, per my runtime; I can't verify that independently). **No blockers. All eight Part 4 GIFs pass.** Every README action from 4.1 to 4.6 now has a matching frame with the same label, order, value, principal, role and command. The P1/P2 findings from the 396668f audit that fall in scope (1, 2, 3, 5, 7, 10, 11, 14) are fixed in the new frames. Seven minor issues remain, and one prior doc finding (20) is still open.

## Claims checked against frames and transcripts

- **Execution and outputs match.** `job-execution-results.gif` f8 (t=6.30 s) clicks **Execute** from the ⋮ menu. f9 shows `translation-audio-hq9f5`, created 1:27:48 AM. f16 shows 1 Succeeded and **View logs**. f22 (t=18.90 s) shows `output_uri: "gs://ac215-project-lecture14-output/run-001/de2f41cba890487bbc15f64fde9d8249/"`, and f17 shows `"execution": "translation-audio-hq9f5"` and `exit(0)`. f43 (t=35.10 s) opens that same folder, which holds manifest.json (338 B), speech.wav (538.2 KB) and translated.txt (162 B). f60 shows the French text, which is 162 bytes when I re-encode it as UTF-8, so the size matches.
- **The job used the uploaded input.** `job-command-settings.gif` f28 (t=43.20 s) has 13 chips in README order, ending in `gs://ac215-project-lecture14-input/run-001/passage.txt … gs://ac215-project-lecture14-output/run-001/`. `storage-input-uri.gif` f16 (t=10.80 s) shows "1 file successfully uploaded" with `passage.txt` at 131 B, the same size as `tutorial/app/examples/passage.txt`. f21 shows the copy icon's **Copied** tooltip.
- **Job creation is complete.** `job-identity-limits.gif` f10 rings **Done** and f11 shows 5 / minute / 0 retries. f23 (t=22.50 s) puts the ring on the **Translation audio job** row, which fixes prior finding 1. f28 rings **Create** with **Execute job immediately** unchecked. f29 shows the created job, Last updated 1:27:12 AM, with "No history".
- **Image tag.** It reads in full as `cgumb/ac215-translation-demo:lecture14-agent-platform-20261022` from f17 of `job-command-settings` onward.
- **Permissions.** `storage-job-permissions.gif` rings **Save** for Storage Object Viewer on the input bucket (f29) and Storage Object Creator on the output bucket (f60). The saved rows appear in f30 and f61, with principal `translation-audio-job@ac215-project.iam.gserviceaccount.com`.
- **Terminal commands are verbatim.** All three `steps.json` commands match README 918–936 exactly once the list indent is removed. The helper command matches README 961–964. Every scene has `exit_code: 0`, and the executions were `translation-audio-8mw6k` (es) and `translation-audio-jnlmc` (fr). The downloaded manifests in `/tmp/ac215-terminal-live/work/results` both show `"status": "complete"` and name those executions. The work copy of `run_job.py` is identical to the repo's. `Cloud outputs:` now appears in helper f43.

## Remaining findings (all P3)

1. **The Download claim at README 848–849 isn't supported by the frames.** The caption says "The media-tab **⋮ → Download** action saved the WAV locally." f55 (t=44.10 s) rings **Download**, but no frame shows a saved file, and `~/Downloads` has no speech.wav. **Fix:** change it to "selects **⋮ → Download**", or add a frame of the browser's download confirmation.
2. **A console error toast appears in `job-execution-results.gif`.** f31–f34 (t=25.2–30.6 s) show "Failed to load pinned buckets. Try again later." over the bucket list. It doesn't affect the flow. **Fix:** crop it, or add a caption note that students can dismiss it.
3. **Two steps are cut in `storage-job-permissions.gif`.**
   - The email is never seen being typed. f19 (t=7.50 s), captioned "enter the job service account email", shows an empty **New principals** field. The role popup then hides the field, and the email chip first appears in f29. f50 → f60 has the same cut.
   - f9 and f40 show only the top 40% of the page with the rest blank. Unlike the other cropped frames, they aren't captioned "(detail)".
   - Separately, README 690 says the GIF "restores" the roles. Students will read that as an odd verb, so say "grants".
   - **Fix:** add one frame with the email typed, and mark f9 and f40 as detail.
4. **Two steps are cut in `storage-input-uri.gif` and `job-command-settings.gif`.** These are jump cuts, but the end state is shown each time.
   - In `storage-input-uri`, the cut from f16 to f17 skips opening `passage.txt`. README 609 names **Object details → Live object**, and that tab label never appears.
   - In `job-command-settings`, the cut from f15 to f16 skips the **Containers** tab and the container-row chevron that README 734–735 describes. The region dialog's **OK** (f11) is never clicked on screen either.
   - **Fix:** add one frame for each skipped step, or leave as is.
5. **The `terminal-job-steps.gif` rendering misleads someone copying from the image.**
   - In f30 (t=11.04 s), `gcloud storage cp …` sits indented under `$ mkdir -p results` without its own `$`, so the two commands read as one.
   - In f19 (t=6.22 s), the line breaks between `--dest` and `,es`.
   - The README code blocks are correct.
   - **Fix:** in `render.py`, give each line of a multi-command scene its own `$` and wrap only at commas.
6. **`terminal-job-helper.gif` is too fast to read.**
   - The output scrolls at 140 ms per frame, and only the last frame is held (3 s).
   - The upload and execute commands are on screen for roughly a second before they scroll.
   - "Execution [translation-audio-jnlmc] has successfully completed" scrolls off before the final hold.
   - The caption's "validation of the completion manifest" is true by implication only: `run_job.py:67–72` prints `Downloaded results:` only after it finds a complete manifest.
   - **Fix:** hold for about 1.5 s after each `$` command and after the success line. Change the caption to "prints `Downloaded results` only after finding a complete manifest."
7. **README 816 doesn't match the History row.** It says "Wait for **Succeeded** in **History**", but the row in f9 shows only a green check icon. The word appears on the execution page ("1 Succeeded", f16). **Fix:** "Wait for the green check in **History**."

The prior doc finding 20 is still open: `docs/job-workflow.md:128` uses `--dest,fr` for `run-002`, while README 927 uses `es`. On finding 21, README 1073–1074 now marks both links as historical, but `function-entry.gif` and `function-deploy-complete.png` are still unembedded.

## Pass/fail per GIF

| GIF | Result | Residual |
|---|---|---|
| storage-bucket-setup | Pass | Unchanged since 396668f. I re-read f9–f71, f123 and f145 and they still match README 585–603 |
| storage-input-uri | Pass | #4 (Live object tab not visible); file picker is an instruction only, as disclosed |
| storage-job-permissions | Pass | #3 |
| job-command-settings | Pass | #4 (container-row expansion, region OK) |
| job-identity-limits | Pass | "(Not saved)" in f11, which the caption discloses |
| job-execution-results | Pass | #1, #2, #7 |
| terminal-job-steps | Pass | #5 |
| terminal-job-helper | Pass | #6 |

## Not visible in the frames

- **Capture order.** The terminal executions (GIF mtimes 01:18–01:19, executions 8mw6k and jnlmc) ran against a `translation-audio` job before the console capture created a new one at 1:27:12. Each GIF is a real run on its own, but they weren't recorded in README order. Students can't see this.
- **The 4.5 passage.** The transcript uploaded the original 131-byte sample text, while README 915 says to save a new passage. The GIF doesn't show the file contents, so nothing on screen contradicts the README.
- **README 4.2 steps 1–2** (creating the job account and granting its project roles) are still unrecorded. The caption doesn't claim them.

I made no edits, ran no cloud commands and pushed nothing. The extra frames and contact sheets I extracted are in `/tmp/ac215-opus-pass3/`.
