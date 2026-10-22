**No blockers. All five GIFs and `agent-platform-api.png` pass and are ready to show students.** This pass was run as Opus 5.5 (`claude-opus-5-5`). I made no edits and ran no cloud commands. I viewed every holdframe in `/tmp/ac215-opus-pass2/` at native size and checked the transition frames on contact sheets. In the transition frames only the pointer and click ring move over the same screenshot, and none of them shows an error, popup or notification badge.

The account details stay the same in every scoped frame:

- **Project:** `ac215-project`.
- **Project number:** `129349313346` in every function URL. It matches `docs/cloud-run-rehearsal.md:16`.
- **Runtime account:** email `translation-demo-runtime@ac215-project.iam.gserviceaccount.com`, with unique ID `109390927667184259705` in both identity GIFs.
- **Image tag:** `container-local-app` f000 shows `lecture14-agent-platform-20261022`, which matches README 57.

## Earlier findings re-checked against the current frames

- **#8 (function GIFs): fixed.**
  - `function-setup` records the whole creation:
    - f005 types `translate-function` while the region still reads **europe-west1 (Belgium)**.
    - f010 and f011 select **northamerica-northeast2 (Toronto)**.
    - f016 changes the runtime from Node.js 22 to Python 3.12.
    - f021 has a click ring on **Allow public access**.
    - f026 clicks **Create**, and f027 shows **Creating…**.
    - f032 opens **Source**, where the sample `hello_http` code is still in place.
  - `function-deploy-test` records the edit, rebuild and test:
    - f005 shows the replaced `main.py`.
    - f010 shows `requirements.txt` before the change (`functions-framework==3.*`), and f015 shows it after.
    - f015 and f016 click **Save and redeploy**.
    - f017 shows the build in progress. In f018 all four stages are **Completed**.
    - The page text reads **Bienvenido a AC215** in f019, **Bonjour à tous** in f020 and **Καλησπέρα σε όλους** in f021.
    - f026 and f031 open **Observability → Logs**. In f032 the log row reads GET **200**, and its URL ends in `?text=Good%20afternoon%20everyone&src=en&dest=fr`.
- **#4 (`identity-create`): fixed.**
  - The name, ID and description are the same in f009 and f045.
  - f014–f039 use the real wizard step **2 Permissions (optional)**, with **Agent Platform User** and **Service Usage Consumer**.
  - f039 clicks **Continue** and f044 clicks **Done**. In f045 the account is **Enabled** and shows **No keys**.
- **#9 (Vertex AI text): fixed in this scope.** The footer in `container-local-app` f005 and f006 reads "Speech is disabled in this deployment." A grep of `tutorial/app/translation_demo/` finds no "Vertex AI" string. I did not audit the speech GIF.
- **#13 (`identity-impersonation`): fixed.**
  - The order is principal first, then role (f015→f020→f025), as the README says.
  - The preselected **Service Account Admin** in f020 is replaced by Token Creator in f030.
  - f030 clicks **Save**, and f031 shows **Service Account Token Creator** on the account.
- **#15: fixed for 3.2.** README 421–423 now states the `actAs` prerequisite.
- **#19: partly fixed, and acceptable.** API enablement is still only a static already-enabled PNG, but README 117 and 393 disclose that.

## Remaining findings, highest priority first (none blocks use)

1. **The instructor's personal email is on screen.** `identity-impersonation` f020, f030 and f031 show `chrisgumb@gmail.com`, and f031 also shows the **Owner** role. README 522–523 tells students to use their own email, so this won't mislead them. It's a privacy decision for you. **Fix (optional):** blur the email or recapture with a course account.
2. **`identity-create` uses two controls the README doesn't name.**
   - f009 fills **Service account description** with "Calls Gemini speech for the translation app", and the description shows again in f045 and in impersonation f005. README 362–364 doesn't mention it.
   - f024 clicks **Add another role** before the second role. README 365–366 doesn't name that button.
   - **Fix:** in step 3 add "Description is optional." In step 4 add "select **Add another role** for the second."
3. **Step 3 of the wizard has no principal field.** In `identity-create` f044 the step contains **Service account users role** and **Service account admins role**. README 367–368 says "Do not add a principal here." **Fix:** reword to "leave both role fields empty."
4. **The terminal frame reads like a command.** `container-local-app` f007 shows `$ Ctrl+C` styled as a shell prompt, so a student may try to type it. **Fix:** render it as "(press Ctrl+C)" without the `$`.
5. **A `container-local-app` caption describes choices that weren't made.** The f001 caption says "choose text and languages". The text and English→French are the page defaults (`templates/index.html:41,45`), so nothing was chosen. **Fix:** "defaults: English → French."
6. **Some clicks have no ring.**
   - In `function-deploy-test` f018 the pointer sits on the URL with no ring. README 154 says "copy the URL", and the copy icon is never clicked.
   - In `identity-impersonation` f000→f005 the click on the account row isn't shown.
   - **Fix:** add rings, or leave as is because the captions carry the action.
7. **Filters appear without being typed.** `identity-create` f045 has a `translation-demo-runtime` filter chip, and `identity-impersonation` f031 has a `chrisgumb@gmail.com` chip. Students without a filter will see a longer list. **Fix (optional):** add "(filtered)" to the caption.
8. **A clipped bar appears in every console frame of both function GIFs.** It's light blue, has no text, and sits at about x 826–1256, y 736–744. It's probably a cut-off console toast or panel. The effect is cosmetic.
9. **`agent-platform-api.png` splits its status label.** "API" sits to the right of **Purchase commitments**, and "Enabled" wraps under **Manage**. No project selector is visible, so the image doesn't show which project it belongs to. The effect is cosmetic.
10. **The editor's `main.py` doesn't match the README snippet exactly.** In `function-deploy-test` f005 the editor shows the docstring line from `tutorial/function/main.py:1`, which the snippet at README 128–138 leaves out. The GIF matches the file, so this is harmless.

Every finding above comes from frames I viewed directly. I didn't run the published image or the browser playback, so the earlier "live passed" result still rests on that earlier run.
