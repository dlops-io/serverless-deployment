**Verdict: not ready yet, but the only blocker is wording.** All three GIFs pass visually, and every fix you listed is present in the frames. The problem is provenance in `container-setup.gif`. The Part 2 translation result and the log entry captioned "matching" come from different service instances, and the README says the GIF records one continuous session. Fix two lines of text, or recapture one frame, and it's ready.

I am Claude Opus 5.5 (`claude-opus-5-5`). I read all 33 native PNGs and the three `index.json` files under `/tmp/ac215-opus-final`. I also decoded every raw frame of the three GIFs (54 + 39 + 16) and checked the in-between frames on contact sheets, where only the pointer moves. I made no repo edits and ran no cloud commands. To trace provenance I read local files only: the `build.py` and `frames.json` for the frames, and the local gcloud logs in `~/.config/gcloud/logs/2026.10.22/`. My scratch output is in `/tmp/opus-delta-audit/`.

## Blocker: container-setup provenance

f045 does show a real success. The page reads "Bonjour à tous" and "Translation complete.", the button reads "Play audio · enable in part 3", and the footer reads "Speech is disabled in this deployment." `build.py` maps that frame to `baseline-translated-clean.jpg`, which has an mtime of 02:17:01. The local gcloud logs show how the service got into that state:

- 01:57:44: `Deleted service [translation-demo]`
- 02:15:45: `gcloud run services update ... --update-env-vars ENABLE_SPEECH=false`. By this point the service already had the runtime identity attached; the identity GIF records that change at 1:59.
- 02:17:23: `--update-env-vars ENABLE_SPEECH=true`

So the Part 2 baseline was captured from the public URL, but on a service with the runtime identity attached and speech switched off. It wasn't the freshly created revision `00001-67d` running as the default compute account. On screen the result looks the same as a student's Part 2, because translation doesn't use the identity.

The bigger problem is f052, captioned "Expand the **matching** POST /api/translate entry". Its entries (CreateService at 01:52:50, POST 200 at 01:53:03) come from the service instance that was deleted at 01:57:44. That POST belongs to the earlier capture that showed "Failed to fetch", not to the request shown in f045. f051 is cut from `11-observability.jpg`, which has an mtime of 01:53:25, so it comes from the same deleted instance.

Two pieces of text are therefore false:

1. The f052 caption's word "matching".
2. README l.301–302: "This records a fresh public service creation, including … translation, and revision/log inspection."

Either of these clears the blocker:

- **Text only:** change the f052 caption to "Expand a POST /api/translate entry and verify 200". Add to the README caption: "The translation and log frames were recaptured from the same public URL in a separate session."
- **Recapture:** take a new f052 showing the 02:16:5x POST on the current service, and keep the disclosure sentence for the speech-off toggle.

## container-setup.gif (54 frames, 45.0 s): pass visually

- **f015:** the ring is now on the Allow public access radio, and Require authentication is still selected before the click. Fixed.
- **f045:** a real success with speech disabled (see above). Fixed.
- **f051:** cropped to the Observability sub-navigation with the ring on Logs. No metrics error banners are visible. Fixed.
- **f004 and f051:** both are still small crops (about 1130×141 and 485×416) on an empty 1280×798 canvas. The captions now say "detail", so they read as deliberate. That's acceptable.
- **f034:** a 2.5 s hold on a bare Console spinner, captioned "Create submitted: Cloud Run provisions…". The caption is accurate. This is minor and optional to fix.
- **f044 → f045:** the app layout jumps about 1%. The right box edge moves from x=1098 to x=1111 between these consecutive frames. It's cosmetic.
- **Everything else:** f005–f039, f046 and f053 match README steps 1–10. The image tag, Toronto region, public access, Request-based billing, 0/2 instances, port 8080 with blank overrides, 512 MiB with 1 CPU, Done, 120/4 then Create, three Completed stages, and Security showing Allow public access are all visible.

## identity-speech-settings.gif (39 frames, 27.5 s): pass

- **Spinner:** gone. The sequence goes straight from the Security frame (f014, ring on Containers) to the empty Name 1 row (f015).
- **Add variable:** f015 shows an empty Name 1 / Value 1 row with no Add variable click. Add variable is clicked in f020 and f025. This matches README l.434–436: "Fill the empty Name 1 / Value 1 row, then select Add variable for each of the other two rows."
- **Diff:** f036 shows the service account changing from `129349313346-compute@…` to `translation-demo-runtime@…`, environment variables changing from None to all three, Serve this revision immediately ticked, and the ring on Deploy changes.
- **Tooltip:** f037 and f038 are cropped at x=272, which removes the lower-left "Explore Cloud Run Release Notes" tooltip. The crop leaves an empty right band, which is cosmetic.
- **Floating labels:** these still overlap the value being typed in f020, f025 and f026 ("Value 1" over "true", for example). f031 shows all three fields cleanly. This is the same cosmetic issue as last pass.
- **README 3.2:** the section has no "scroll" instructions, and the caption now says rollout waiting is shortened.

## web-translation-speech.gif (16 frames, 10.0 s): pass

- **f004:** Play audio is enabled and the footer reads "Speech uses Agent Platform."
- **f009:** shows "Bonjour à tous" and "Translation complete." with the ring on Play audio.
- **f014:** shows "Audio ready." with the player at 0:01 / 0:01.
- **f015:** shows the pause icon with the progress bar moving.
- **README l.474–475:** the sentence claiming these frames show Part 2 is gone. No "Vertex AI" text appears in any frame of the three GIFs.

To reach ready, apply the two text fixes above or recapture f052, then rebuild `container-setup.gif`.
