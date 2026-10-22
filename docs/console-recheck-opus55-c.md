**Not ready to publish.** `container-setup.gif` fails on one blocking defect: the frame captioned as a successful translation shows the app's "Failed to fetch" error. `identity-speech-settings.gif` passes once one caption and one README instruction are fixed. `web-translation-speech.gif` passes, and its README caption needs one sentence removed.

I looked at all 34 hold frames, which is every frame held for 1.9 s or more. The 120–240 ms frames between them only move the pointer. I made no edits, ran no cloud commands and published nothing. I am Claude Opus 5.5 (`claude-opus-5-5`).

## container-setup.gif (54 frames, 45.0 s): FAIL

These match the README: the image tag and `translation-demo` (f005, 2.5 s); the region change to Toronto (f010); Allow public access before (f015) and after (f016); Request-based billing (f016); Auto scaling with 0 and 2 instances (f021); port 8080 with blank command and arguments (f022); 512 MiB and 1 CPU (f023). In f028, Done is clicked while the timeout still reads 300, and f033 then shows 120 and 4 with the pointer on Create. The creation is fresh: f039 shows all three stages Completed and revision `00001-67d` deployed "Just now". The log entries in f052 are dated 2026-10-22 between 01:52:50 and 01:53:03, which fits a new service.

Defects:

1. **Blocking.** f045 (32.5 s) is captioned "The public web app returns Bonjour à tous", but the screen shows an empty Translation box and the red error "Failed to fetch". No hold frame in this GIF shows a successful part 2 translation. This contradicts README step 9 (l.290–291) and the caption's "translation" (l.302). The f052 log does show `POST 200 /api/translate` at 01:53:03, so the server answered; the browser capture still recorded the failure. **Fix:** recapture with "Bonjour à tous" and the disabled "Play audio · enable in part 3" button both visible.
2. f051 (38.1 s) shows four "An error occurred requesting data. An unknown error occurred" banners on the Metrics charts, plus an "Explore data" tooltip. These break the no-error-popups rule. **Fix:** recapture once metrics have loaded, or crop to the sub-navigation and click Logs.
3. f015 (8.1 s) is captioned "select Allow public access", but the ring and pointer sit on **Require authentication** at y≈406 instead of Allow public access at y≈362. **Fix:** move the annotation to the Allow public access radio.
4. f004 (0.6 s) is a strip about 1130×220 px with the rest of the canvas empty, so it looks broken. **Fix:** recapture full size.
5. Minor: in f033 the collapsed container row says "(Not saved)". That is real Console wording on an unsaved create form and can stay.
6. The README caption (l.301–303) says waiting is shortened but never says the GIF is a sequence of screenshots with an added pointer. **Fix:** add "Screenshots of the real Console; pointer and click rings are added."

## identity-speech-settings.gif (44 frames, 30.0 s): PASS after fixes

These match the README: Security shows Allow public access and the Compute Engine default account (f004); the filter selects `translation-demo-runtime@ac215-project.iam.gserviceaccount.com` (f009); "Translation demo runtime" is selected with `Security *` (f014); the three variables go in (f025, f030, f031). In f041 the diff shows the service account changing from `129349313346-compute@…` to `translation-demo-runtime@…`, environment variables changing from None to all three, Serve this revision immediately ticked, and the pointer on Deploy changes. Redeploying appears in f042 and three Completed stages in f043. The change is stamped 1:59 am, after the 01:52 creation, so it is a fresh change. This fixes old-audit finding 6, which said the identity change was not recorded.

Defects:

1. f019 (8.1 s) is captioned "select Add variable", but the frame shows a loading spinner, the pointer over empty space, and `Security *` still underlined. f020 then shows that **the Name 1 / Value 1 row already exists without an Add variable click**. Add variable is clicked only twice (f025, f030). README step 3 (l.431) says "Select Add variable for each of these three rows", which is wrong. **Fix the README:** "Fill the empty Name 1 / Value 1 row, then select Add variable for each of the other two." **Fix the caption on f019:** "Containers tab loading", or drop the frame.
2. In f025, f030 and f031, the floating label overlaps the typed value ("Value 1" over "true", and likewise for the others). It is readable, and f036 shows the fields cleanly. This is cosmetic.
3. f042 and f043 show a stray "Explore Cloud Run Release Notes" hover tooltip in the lower left. It is not an error, but cropping it out or recapturing would be cleaner.
4. README l.430 says "scroll to Variables & Secrets", and l.440 says "Scroll back to the top". The frames show Variables & Secrets as a card beside Container settings with no scrolling, and View diff & redeploy sits in the fixed header. **Fix:** replace "scroll to" with "find" and cut "Scroll back to the top and".
5. The caption (l.459–461) does not say that the rollout wait is shortened. Add that sentence.

## web-translation-speech.gif (16 frames, 10.0 s): PASS

f004 shows "Good afternoon everyone", English to French, an enabled Play audio button and the footer "Speech uses Agent Platform". This fixes old-audit finding 8, where the footer said "Vertex AI". f009 shows "Bonjour à tous", "Translation complete." and the pointer on Play audio. f014 shows the audio player and "Audio ready." with the pointer on play. f015 shows the pause icon and the progress bar moving. The player reading 0:01 / 0:01 in f014 means the clip had already auto-played once, which matches "Use the browser's audio controls to replay it" (l.446).

One README fix: l.470–471 says "The first three frames also show the translation interaction used in part 2." Only two frames show translation, and both show the part 3 UI, with Play audio enabled and the Agent Platform footer, not part 2's disabled button. Delete the sentence, because the fixed container-setup GIF will show part 2's own translation.

## To reach ready

Recapture f045 and f051 in container-setup, re-annotate f015, and replace f004. Then make the README edits at l.301–303, 430–431, 440, 459–461 and 470–471. No Vertex AI labels remain in any of the three GIFs, and both public-access confirmations now show Allow public access (container-setup f053, identity f004).
