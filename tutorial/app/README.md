# Application scaffold

Part 2 has a translation UI and HTTP route. Live translation requires outbound
network access and a functioning googletrans provider. Parts 3 and 4 are explicit
integration boundaries: no speech or Cloud Storage uploads are implemented yet.

## Local development

With uv and Python 3.12:

```bash
uv sync --frozen
uv run python -m translation_demo serve
```

Open `http://localhost:8080`. Test the same input that worked in part 1. The browser
sends a JSON POST here; part 1 used URL query parameters. Explain that input-format
change if showing the requests. The disabled audio button is a future feature.

Run offline checks:

```bash
uv run python -m unittest discover -s tests -v
uv run python -m translation_demo batch --plan \
  --text-file examples/passage.txt --src en --dest fr \
  --output-uri gs://YOUR_OUTPUT_BUCKET/fresh-run-prefix
```

The plan command makes no API calls, creates no files, and uploads nothing.
Without `--plan`, the scaffold exits unsuccessfully rather than pretending to run.

## One image, two startup commands

Build from this directory (image build is still a rehearsal task):

```bash
docker build --platform linux/amd64 -t translation-demo:dev .
docker run --rm -p 8080:8080 translation-demo:dev
```

The image defaults to the web server. For a job, override its command:

```bash
docker run --rm translation-demo:dev \
  python -m translation_demo batch --plan \
  --text-file examples/passage.txt --src en --dest fr \
  --output-uri gs://YOUR_OUTPUT_BUCKET/fresh-run-prefix
```

In Cloud Run job settings the **command** would be `python` and the individual
**arguments** would start with `-m`, `translation_demo`, `batch`. Do not paste the
whole command into one argument field. Remove `--plan` only after real execution
is implemented and rehearsed.

## Image publication: not done yet

Maintainers must choose a registry namespace and verify write access before
publishing. Tag a tested image with an explicit version, push it, record its
digest, and test deployment from that digest. Do not overwrite the original
tutorial's `latest` image while developing this branch. No student-ready image
address is claimed by these instructions.

Students can follow the final tutorial using prebuilt images. These source files,
the Dockerfile, and CLI are available for optional inspection; reading them is
not a prerequisite to deploying an image through the console.
