# Tutorial audit resolution — 2026-10-22

This report concerns the local working tree after commit `396668f`. The older
[original audit](console-audit-opus55.md) is retained as evidence of what needed
fixing, rather than as a description of the current tutorial.

## Changes verified live

- Re-recorded function creation, source replacement, deployment, endpoint tests
  and matching request logs.
- Created the new web runtime identity in the real wizard, including both roles,
  Continue and Done. Recorded account-scoped developer impersonation and bucket
  grants through their actual Save actions.
- Recreated the job in the Console, executed it, opened its matching task logs,
  and followed its output URI to the exact text, WAV and completion manifest.
- Recorded real CLI upload/execute/download and helper runs. Terminal clips
  animate their saved output; they are not dry-run examples.
- Published and anonymously pulled the current Agent Platform app image.
  Verified public translation and audio with the attached runtime identity.
- Added isolated spin-up and teardown helpers; exercised live deployment,
  finite jobs, helper submission, cleanup and interrupted-setup recovery.
  See [lifecycle evidence](lifecycle-live-check.md).

## Independent review history

Claude Opus 5.5 was invoked with `claude-opus-5-5` for each review. It inspected
native-size extracted GIF frames and the written steps, not captions alone.

- [Function, local app and identity recheck](console-recheck-opus55-a.md): no
  blockers; smaller wording, pointer and caption corrections requested.
- [Storage, jobs and CLI recheck](console-recheck-opus55-b.md): no blockers;
  smaller capture and pacing corrections requested.
- [Web creation and speech recheck](console-recheck-opus55-c.md): caught a real
  browser error in the Part 2 result, despite a successful server log, plus a
  metrics error view and mismatched annotations. These findings require a
  corrected recording and another visual review; both are now complete.
- [Web follow-up](console-final-opus55-web.md): all three GIFs passed visually;
  it additionally identified that the replacement baseline result and older
  request log were different rehearsals. The README now discloses this and
  the GIF no longer calls that log a matching request.
- [Final visual sign-off](console-signoff-opus55.md): ready, with no blocking
  capture defects. Its final small corrections are applied: coverage text no
  longer claims a browser download confirmation, the grants use student-facing
  wording, all linked reports are staged, and the pointer covering HTTP 200 is
  removed. Unembedded old assets and clipped bottom notification strips are
  removed.
- [Closeout check](console-closeout-opus55.md): Opus independently verified
  all four final findings closed, optional strip/orphan cleanups complete, and
  no blockers. Its optional “opening” wording improvement is also applied.
- Lifecycle helpers received three code reviews, culminating in
  [the final review](lifecycle-final-opus55.md), plus live integration checks.

## Recording boundaries

Recordings are annotated real screenshots with shortened waits. Platform-specific
file pickers and interactive sign-in are not recorded. The already-enabled API
is shown as enabled rather than pretending to enable it again. Bucket-creation
captures use disclosed instructor capture names; students consistently use their
own input and output names. Terminal runs are independently real, but were not
captured in the same chronological session as Console setup.

The coverage table is maintained in [console-gif-coverage.md](console-gif-coverage.md).

## Git handoff

All changes are saved locally and staged on `codex/four-part-tutorial`.
A normal signed commit reached the GPG PIN prompt and was cancelled because the
instructor is away. Repository signing settings were preserved. No overnight
Git commit or push succeeded; unlocking the signing key is the remaining handoff.
