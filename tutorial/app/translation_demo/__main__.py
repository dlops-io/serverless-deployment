"""One image, different startup commands: serve or batch."""

import argparse
import json
import os
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve", help="Start the HTTP service")
    batch = commands.add_parser("batch", help="Translate a passage, generate speech, save outputs, and exit")
    source = batch.add_mutually_exclusive_group(required=True)
    source.add_argument("--text-file", type=Path, help="A UTF-8 file available inside the container")
    source.add_argument("--input-uri", help="A UTF-8 object in Cloud Storage")
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

    from .translation import validate, translate
    from .speech import synthesize
    from .storage import split_uri, read_text, save_artifacts

    try:
        split_uri(args.output_uri)
        if args.input_uri:
            split_uri(args.input_uri)
        # A remote plan deliberately does not download its input or look up ADC.
        text = None if args.input_uri else args.text_file.read_text(encoding="utf-8")
        validate(text if text is not None else "Planned remote input", args.src, args.dest)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if args.plan:
        print(json.dumps({
            "status": "plan_only", "input_characters": len(text) if text is not None else None,
            "input_uri": args.input_uri, "source_language": args.src,
            "destination_language": args.dest, "output_uri": args.output_uri,
            "steps": ["Read the passage", "Translate the complete passage", "Synthesize speech with Agent Platform",
                      "Save text, audio, and completion manifest to a unique attempt prefix", "Exit"],
            "implemented": True,
        }, indent=2))
        return
    try:
        if text is None:
            text = read_text(args.input_uri)
        validate(text, args.src, args.dest)
        translated = translate(text, args.src, args.dest)
        audio, mime_type = synthesize(translated, args.dest)
        result = save_artifacts(args.output_uri, translated, audio, mime_type)
    except Exception as exc:
        # A failing job must exit unsuccessfully so execution status is truthful.
        print("Batch failed: " + str(exc), file=__import__("sys").stderr)
        raise SystemExit(1) from exc
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
