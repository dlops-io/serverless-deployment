#!/usr/bin/env python3
"""Upload a local passage, execute an existing Cloud Run job, download outputs."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import uuid


def run(command, dry_run=False):
    print('$ ' + shlex.join(command), flush=True)
    if not dry_run:
        subprocess.run(command, check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('text_file', type=Path, help='A short local UTF-8 passage')
    parser.add_argument('--project', required=True)
    parser.add_argument('--region', default='northamerica-northeast2')
    parser.add_argument('--job', default='translation-audio')
    parser.add_argument('--input-bucket', required=True, help='Bucket name, without gs://')
    parser.add_argument('--output-bucket', required=True, help='Bucket name, without gs://')
    parser.add_argument('--src', default='en')
    parser.add_argument('--dest', default='fr')
    parser.add_argument('--download-dir', type=Path, default=Path('results'))
    parser.add_argument('--no-download', action='store_true', help='Leave results in Storage')
    parser.add_argument('--dry-run', action='store_true', help='Print commands; upload and execute nothing')
    args = parser.parse_args(argv)
    # Commas delimit gcloud --args. Keep configuration values unambiguous and
    # never interpolate user input into a shell command.
    for name in ('project', 'region', 'job', 'input_bucket', 'output_bucket', 'src', 'dest'):
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', getattr(args, name)):
            parser.error(f'{name.replace("_", "-")} must be a plain name, without slashes or commas')
    try:
        passage = args.text_file.read_text(encoding='utf-8')
        if not passage.strip() or len(passage) > 5000 or len(passage.encode('utf-8')) > 20000:
            parser.error('Use a nonempty UTF-8 passage of at most 5,000 characters and 20,000 bytes')
    except (OSError, UnicodeError) as exc:
        parser.error(str(exc))

    run_id = 'run-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:12]
    input_uri = f'gs://{args.input_bucket}/{run_id}/passage.txt'
    output_uri = f'gs://{args.output_bucket}/{run_id}'
    local_dir = args.download_dir / run_id
    if not args.no_download and local_dir.exists():
        parser.error('The generated local result directory already exists; rerun to allocate a fresh one')
    batch_args = ','.join(['-m', 'translation_demo', 'batch', '--input-uri', input_uri,
                           '--src', args.src, '--dest', args.dest, '--output-uri', output_uri + '/'])
    try:
        run(['gcloud', 'storage', 'cp', str(args.text_file.resolve()), input_uri,
             '--project=' + args.project, '--quiet'], args.dry_run)
        run(['gcloud', 'run', 'jobs', 'execute', args.job, '--project=' + args.project,
             '--region=' + args.region, '--args=' + batch_args, '--wait', '--quiet'], args.dry_run)
        print('Cloud outputs: ' + output_uri + '/', flush=True)
        if not args.no_download:
            if not args.dry_run:
                args.download_dir.mkdir(parents=True, exist_ok=True)
            run(['gcloud', 'storage', 'cp', '--recursive', output_uri,
                 str(args.download_dir.resolve()), '--project=' + args.project, '--quiet'], args.dry_run)
            if not args.dry_run:
                manifests = list(local_dir.rglob('manifest.json'))
                complete = [p for p in manifests if json.loads(p.read_text())['status'] == 'complete'
                            and (p.parent / 'translated.txt').is_file() and (p.parent / 'speech.wav').is_file()]
                if not complete:
                    raise ValueError('No complete output set was found in the downloaded results')
                print('Downloaded results: ' + str(local_dir.resolve()), flush=True)
        return 0
    except subprocess.CalledProcessError as exc:
        print(f'Helper stopped: gcloud failed with exit status {exc.returncode}. Later steps were not run.', file=sys.stderr)
    except (OSError, ValueError, KeyError) as exc:
        print('Helper stopped: ' + str(exc), file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
