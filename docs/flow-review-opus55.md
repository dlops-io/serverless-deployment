Independent teaching-flow review requested by the instructor.
Model confirmed by the reviewer CLI: Claude Opus 5.5.
This report contains suggestions, not applied changes. In particular, the actual
configured runtime identity must be checked rather than assumed.

# Review: AC215 Lecture 14 serverless tutorial (teaching flow)

## Verdict

The narrative arc works: function, then image you supply, then runtime identity, then run-to-completion job. Each part builds on an artifact from the previous one. Parts 1–2 are close to "one idea per step."

Parts 3 and 4 each carry three to five new ideas, and the README's claim that "each step introduces one main idea" is not yet true for them. Several problems remain even after the TODOs are implemented:

- The developer workflow appears one part too late.
- Part 3 adds an identity, a feature, and an ADC deep-dive at once.
- Part 4's one-time setup is a wall of IAM.
- Instructor and maintainer notes are mixed into student-facing text.

Splitting Parts 2, 3, and 4 into sub-steps would fix most of this without changing the story.

## Findings (pedagogical, highest priority first)

### High

**1. Part 3 has more than one main idea.** Students meet all of these in one part:
- A new feature (TTS through Vertex AI)
- A dedicated runtime service account and role grant
- ADC
- Invoker vs. runtime separation
- The "How was this developed" subsection, which covers the edit/run loop, user ADC vs. impersonation, three kinds of identity, quota projects, and credential mounts

Two fixes:
- Move invoker vs. runtime to Part 1 or 2, where public invocation is first chosen.
- Make the main text "replace the default runtime identity with a least-privilege one." Parts 1–2 already ran as the default compute service account, so say so. Then Part 3 becomes one idea: *what the running code may access*.

**2. The developer workflow is introduced after the step that depends on it.** Part 2 already says "run the UI locally… build and publish its image… deploy the same image." The "before the prebuilt app feels like magic" explanation only arrives in Part 3, after the app has felt like magic for a whole part. The generic loop (edit → run locally → build container → publish → deploy) belongs at the start of Part 2. Only the ADC-specific part ("same code, credentials come from you locally and from the attached SA in Cloud Run") belongs in Part 3.

**3. Part 2 contradicts the student workflow.** Part 2 tells the reader to "build and publish its image." Part 4 and the app README say students use a prebuilt image and need no rebuild. State plainly that the instructor builds and publishes as a demo, and students deploy the published image. Otherwise students will look for Docker, registry credentials, and `--platform linux/amd64`, none of which are listed as prerequisites.

**4. Part 4 is overloaded, especially "One-time setup."** Part 4 introduces all of the following:
- Jobs
- Two buckets with two different roles
- A second service account
- Caller vs. runtime permissions
- Command/argument overrides
- GCS-URI input instead of a local file
- Console execution
- CLI execution with comma-separated `--args`
- Retries and idempotency
- Timeouts
- A helper
- Parallelism

Setup step 1 alone bundles buckets, a service account, three grants, job creation, and caller permissions. It also does not say whether setup happens in the console or the CLI. Split it:

| Step | New idea | Contents |
| --- | --- | --- |
| 4a | Finite work with persisted output | Run the bundled passage (`--text-file`, already supported) and write to one output bucket. The job SA needs Vertex AI plus `objectCreator`. One task, 0 retries. |
| 4b | Parameterized executions | Upload your own input, then execute with overrides in the console. This is the natural point for caller vs. runtime permissions and the input bucket with `objectViewer`. |
| 4c | Same execution from the terminal | `gcloud storage cp` plus `gcloud run jobs execute`. |
| 4d (optional) | Convenience | Helper, retries/idempotency, parallel tasks. |

**5. Instructor and maintainer notes are interleaved with student instructions.** Examples:
- "The original Python 3.10 instruction is stale"
- "Rehearse a response-only fallback"
- "Validate model and region availability… during rehearsal"
- "Its separate published image has not been inspected here"
- "Settle retry behavior before enabling uploads"

Students reading the README cannot tell what to do from what the instructor should check. Move these into an "Instructor notes / rehearsal" section or callouts. This matters even after the TODOs are done.

### Medium

**6. Concepts are used before they are introduced:**
- **ADC:** the main text of Part 3 uses it ("Use Application Default Credentials from that attached identity") before the subsection that defines it.
- **Revision:** Part 2 says "inspect the… revision" with no definition. Part 3 is the natural place to show it: same image, new revision with the SA attached and audio enabled.
- **Argument overrides and retry-safe naming:** setup step 1 and the bucket paragraph in Part 4 use these before command/args or retries are explained.
- **Input format change:** Part 1 uses query parameters and Part 2 uses a JSON POST. Only the app README mentions this. Add one sentence to Part 2 in the main README.

**7. Hidden prerequisites:**
- **Own project, billing, and APIs:** "Students use their own GCP project" appears only in Part 4, yet Parts 1–3 already need it. Add a Part 0 / prerequisites block with project, billing, region, APIs enabled per part, and gcloud installed (needed by Part 4c).
- **Deploying with a service account:** this requires `iam.serviceAccounts.actAs` (Service Account User) on that SA, which is unmentioned in Parts 3–4.
- **Creating SAs and granting roles:** the steps are absent from the README for Part 3. The specific Vertex role is also unnamed.
- **Public invocation:** it may be blocked by org policy (domain-restricted sharing). Part 1 hedges, but Part 2 needs the same choice and a plan B (authenticated `curl` or the proxy).
- **Pulling the image:** Cloud Run may need to pull from Docker Hub rather than Artifact Registry. Say which registry the published image lives in once that is decided.

**8. Console and developer workflows are not cleanly separated.** Parts 1–3 are implicitly console-only but never say so. Part 4 setup has no stated medium. The local-dev subsection drops CLI commands into a console narrative. Two suggestions:
- Label each step as *Console* or *Developer (terminal)*, and put all CLI equivalents of console setup in an appendix.
- Keep the Part 3 subsection to about three sentences plus a pointer to the guide. Impersonation, quota project, and the container ADC mount are guide-only material.

**9. The console argument entry in Part 4 is error-prone.** Students must type 12 separate argument fields, and the CLI form needs comma-joined `--args` that replace the entire list. Consider:
- Setting fixed arguments at job creation
- Passing only `INPUT_URI` and `OUTPUT_URI` per execution through env-var overrides (`gcloud run jobs execute --update-env-vars`; verify console support)

This shrinks both the console and CLI demos to "change two values." It is a design choice, not a correction.

**10. `objectCreator` interacts badly with retries.** It cannot overwrite, so a retried task that already wrote a file will fail. The doc mentions this, but in student-facing text, simply say "0 retries for this lecture" and defer idempotency to 4d.

### Low

- Headings are inconsistent: "Running App as Cloud Function" and "Running App in Cloud Run" vs. "Part 3: …" and "Part 4: …". Use "Part N: …" throughout and say "Cloud Run functions" to match the console.
- Part 2's sentence "A browser page stays visible without its application instance continuously running" is a scale-to-zero point that reads as a non sequitur. Either name scale-to-zero explicitly or cut it.
- "HTML does not inherently require a custom image" appears twice (intro and Part 2). Keep one.
- The identity distinctions (CLI login, local ADC, invoker, runtime SA, job caller) recur across three files. One small table, introduced in Part 3 and referenced in Part 4, would replace several paragraphs.

## Acknowledged TODOs (not counted against the flow)

- Vertex TTS and the audio button
- Bucket uploads and retry-safe naming
- `--input-uri`
- The helper
- Building and publishing the image, plus the digest
- Rehearsing the googletrans provider
- Verifying public invocation in the teaching project

The scaffold boundaries are clearly marked. One caution: Part 3's teaching value depends on TTS working, so the Part 3a restructure (new revision with SA and audio flag) should be designed alongside that implementation.

## Suggested teaching order

0. **Prerequisites:** own project, billing, region, and which APIs each part needs. One sentence previewing that "Cloud Run runs containers."
1. **Function** *(console).* Supply the handler and dependencies; Google builds the image. Choose public invocation, which introduces *who may call*. Note in one line that it runs as a default identity.
2. **Container service**
   - **2a. Developer workflow** *(instructor demo, terminal):* run locally → containerize → publish. Explain why a container is used here.
   - **2b. Deploy the published image** *(console):* same invocation choice, logs, and the JSON vs. query-parameter note.
3. **Runtime identity**
   - **3a.** *(console):* create the SA, grant Vertex AI, deploy a new revision with the SA attached and audio enabled. New idea: *what the code may access*. Define revision and ADC here.
   - **3b. Same code on a laptop** *(short sidebar):* local ADC from your own credentials, optional impersonation, pointer to the guide.
4. **Job**
   - **4a.** *(console):* same image, batch command, bundled passage, one output bucket, job SA, 1 task, 0 retries.
   - **4b.** *(console):* upload your own input and execute with overrides. Covers caller vs. runtime permissions.
   - **4c.** *(terminal):* `storage cp` plus `jobs execute`, then download.
   - **4d. Optional:** helper, retries/idempotency, parallel passages.
5. **Appendices:** CLI equivalents for all console setup, local container ADC mount, instructor rehearsal checklist, cleanup.
