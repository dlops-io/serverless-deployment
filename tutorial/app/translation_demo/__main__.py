"""One image, different startup commands: serve or batch."""

import argparse
import json
import os
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve", help="Start the HTTP service")
    batch = commands.add_parser("batch", help="Plan the proposed translated audio job")
    batch.add_argument("--text-file", type=Path, required=True)
    batch.add_argument("--src", default="en")
    batch.add_argument("--dest", default="fr")
    batch.add_argument("--output-uri", required=True, help="A fresh gs://bucket/prefix")
    batch.add_argument("--plan", action="store_true", help="Show the plan without API calls or uploads")
    args = parser.parse_args(argv)
    if args.command == "serve":
        port = int(os.environ.get("PORT", "8080"))
        os.execvp("gunicorn", ["gunicorn", "--bind", f"0.0.0.0:{port}",
                              "--workers", "1", "--threads", "4", "--timeout", "90",
                              "translation_demo.web:create_app()"])

    from .translation import validate

    try:
        text = args.text_file.read_text(encoding="utf-8")
        validate(text, args.src, args.dest)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if not args.output_uri.startswith("gs://") or len(args.output_uri[5:].split("/", 1)) != 2:
        parser.error("Use an output URI of the form gs://bucket/fresh-prefix")
    bucket, prefix = args.output_uri[5:].split("/", 1)
    if not bucket or not prefix.strip("/"):
        parser.error("Both an output bucket and a fresh prefix are required")
    if not args.plan:
        parser.error("Batch execution is not implemented yet; use --plan. No API calls or uploads were made.")
    print(json.dumps({
        "status": "plan_only", "input_characters": len(text),
        "source_language": args.src, "destination_language": args.dest,
        "output_uri": args.output_uri,
        "steps": ["Translate the complete passage", "Synthesize speech with Vertex AI",
                  "Save translated text and audio to Cloud Storage", "Exit"],
        "implemented": False,
    }, indent=2))


if __name__ == "__main__":
    main()
