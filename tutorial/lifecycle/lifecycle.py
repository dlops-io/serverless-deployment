#!/usr/bin/env python3
"""Plan or apply isolated tutorial resource creation and removal."""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IMAGE = 'cgumb/ac215-translation-demo@sha256:c17b6db09f7402febb582bf327920ec9ca4eee113f5ddefa38e9da5619dbe72e'
APIS = ['run.googleapis.com', 'cloudbuild.googleapis.com', 'artifactregistry.googleapis.com',
        'aiplatform.googleapis.com', 'storage.googleapis.com', 'iam.googleapis.com',
        'iamcredentials.googleapis.com']
ROLES = ['roles/aiplatform.user', 'roles/serviceusage.serviceUsageConsumer']
LABEL = 'ac215-tutorial-owner'


class Cloud:
    def __init__(self, project, apply=False):
        self.project, self.apply = project, apply

    def command(self, *args):
        return ['gcloud', *args, '--project=' + self.project, '--quiet']

    def mutate(self, *args):
        command = self.command(*args)
        print('$ ' + shlex.join(command), flush=True)
        if self.apply:
            if 'add-iam-policy-binding' not in args:
                # Preserve build/deploy progress instead of hiding a long operation.
                subprocess.run(command, check=True)
                return
            for attempt in range(6):
                result = subprocess.run(command, capture_output=True, text=True)
                if result.returncode == 0:
                    return
                retryable = ('add-iam-policy-binding' in args
                    and not re.search(r'PERMISSION_DENIED|\b403\b', result.stderr, re.I)
                    and re.search(r'(?:service account|serviceAccount:)\s*[^\n]*?\bdoes not exist\b',
                                  result.stderr, re.I))
                if not retryable or attempt == 5:
                    if result.stdout:
                        print(result.stdout, file=sys.stderr)
                    if result.stderr:
                        print(result.stderr, file=sys.stderr)
                    raise subprocess.CalledProcessError(result.returncode, command)
                delay = 2 ** attempt
                print(f'New IAM principal is propagating; retrying in {delay}s.', flush=True)
                time.sleep(delay)

    def warn_orphaned_bindings(self, email):
        command = self.command('projects', 'get-iam-policy', self.project, '--format=json')
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        for binding in json.loads(result.stdout).get('bindings', []):
            if binding.get('role') not in ROLES:
                continue
            for member in binding.get('members', []):
                if member.startswith('deleted:serviceAccount:' + email + '?uid='):
                    print('Manual IAM cleanup: ' + binding['role'] + ' still names ' + member,
                          file=sys.stderr)

    def project_roles(self, email):
        command = self.command('projects', 'get-iam-policy', self.project, '--format=json')
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        policy = json.loads(result.stdout)
        return {binding['role'] for binding in policy.get('bindings', [])
                if 'serviceAccount:' + email in binding.get('members', [])
                and not binding.get('condition')}

    def describe(self, kind, name, region):
        args = {'account': ['iam', 'service-accounts', 'list', '--filter=email=' + name],
                'bucket': ['storage', 'buckets', 'describe', 'gs://' + name],
                'service': ['run', 'services', 'describe', name, '--region=' + region],
                'job': ['run', 'jobs', 'describe', name, '--region=' + region]}[kind]
        command = self.command(*args, '--format=json')
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            # Never interpret authorization, transport or generic failures as absence.
            denied = re.search(r'PERMISSION_DENIED|FORBIDDEN|\b403\b', result.stderr, re.I)
            missing = re.search(
                r'NOT_FOUND|\bnot found\b|does not exist|status=404|HTTPError 404|Cannot find (?:service|job) \[',
                result.stderr, re.I)
            if kind != 'account' and missing and not denied:
                return None
            raise RuntimeError('Cannot inspect resource: ' + shlex.join(command) + '\n' + result.stderr)
        data = json.loads(result.stdout)
        if kind == 'account':
            # IAM describe can return 403 for a deleted account. An authorized
            # non-deleted-account listing distinguishes absence without guessing from errors.
            return next((account for account in data if account.get('email') == name), None)
        return data


def save(path, manifest):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(manifest, indent=2) + '\n')
    temporary.replace(path)


def make_manifest(args):
    prefix = args.prefix
    resources = []
    for suffix in ('function', 'web', 'job'):
        resources.append({'kind': 'account', 'name': f'{prefix}-{suffix}@{args.project}.iam.gserviceaccount.com',
                          'state': 'planned'})
    resources += [{'kind': 'bucket', 'name': f'{args.project}-{prefix}-{suffix}', 'state': 'planned'}
                  for suffix in ('input', 'output')]
    resources += [{'kind': 'service', 'name': f'{prefix}-{suffix}', 'state': 'planned'}
                  for suffix in ('function', 'web')]
    resources += [{'kind': 'job', 'name': f'{prefix}-audio', 'state': 'planned'}]
    return {'schema': 1, 'owner': uuid.uuid4().hex, 'project': args.project,
            'prefix': prefix, 'region': args.region, 'model_location': args.model_location,
            'image': args.image, 'resources': resources, 'complete': False}


def setup(args, cloud):
    if args.manifest.exists():
        raise ValueError('Manifest already exists. Tear down that stack or choose a new manifest and prefix.')
    manifest = make_manifest(args)
    # A fresh project needs these APIs before resource describe calls work.
    # Enabling APIs is the only cloud mutation permitted before collision checks.
    cloud.mutate('services', 'enable', *APIS)
    # Check all names before creating any resource. Existing resources are never adopted.
    if cloud.apply:
        for item in manifest['resources']:
            if cloud.describe(item['kind'], item['name'], args.region) is not None:
                raise ValueError('Refusing to adopt existing ' + item['kind'] + ': ' + item['name'])
        save(args.manifest, manifest)
    owner = manifest['owner']
    label = LABEL + '=' + owner
    marker = 'Managed AC215 tutorial stack ' + owner

    def create(kind, name, *command):
        item = next(r for r in manifest['resources'] if r['kind'] == kind and r['name'] == name)
        # A failed command may have created a cloud resource. Preserve intent for recovery.
        item['state'] = 'creating'
        if cloud.apply:
            save(args.manifest, manifest)
        cloud.mutate(*command)
        if kind == 'bucket':
            cloud.mutate('storage', 'buckets', 'update', 'gs://' + name, '--update-labels=' + label)
        item['state'] = 'created'
        if cloud.apply:
            save(args.manifest, manifest)

    emails = {}
    for suffix in ('function', 'web', 'job'):
        account_id = args.prefix + '-' + suffix
        email = account_id + '@' + args.project + '.iam.gserviceaccount.com'
        emails[suffix] = email
        create('account', email, 'iam', 'service-accounts', 'create', account_id,
               '--display-name=AC215 ' + args.prefix + ' ' + suffix,
               '--description=' + marker)
    for suffix in ('web', 'job'):
        for role in ROLES:
            cloud.mutate('projects', 'add-iam-policy-binding', args.project,
                         '--member=serviceAccount:' + emails[suffix], '--role=' + role, '--condition=None')
    input_bucket = args.project + '-' + args.prefix + '-input'
    output_bucket = args.project + '-' + args.prefix + '-output'
    for bucket in (input_bucket, output_bucket):
        create('bucket', bucket, 'storage', 'buckets', 'create', 'gs://' + bucket,
               '--location=' + args.region, '--default-storage-class=STANDARD',
               '--uniform-bucket-level-access', '--public-access-prevention', '--soft-delete-duration=7d')
    for bucket, role in ((input_bucket, 'roles/storage.objectViewer'),
                         (output_bucket, 'roles/storage.objectCreator')):
        cloud.mutate('storage', 'buckets', 'add-iam-policy-binding', 'gs://' + bucket,
                     '--member=serviceAccount:' + emails['job'], '--role=' + role)
    if args.developer_member:
        cloud.mutate('iam', 'service-accounts', 'add-iam-policy-binding', emails['web'],
                     '--member=' + args.developer_member,
                     '--role=roles/iam.serviceAccountTokenCreator', '--condition=None')
    cloud.mutate('storage', 'cp', str(ROOT / 'tutorial/app/examples/passage.txt'),
                 'gs://' + input_bucket + '/run-001/passage.txt')
    create('service', args.prefix + '-function', 'run', 'deploy', args.prefix + '-function',
           '--region=' + args.region, '--source=' + str(ROOT / 'tutorial/function'),
           '--function=hello_http', '--base-image=python312',
           '--service-account=' + emails['function'], '--no-invoker-iam-check',
           '--min-instances=0', '--max-instances=3', '--labels=' + label)
    env = 'ENABLE_SPEECH=true,GOOGLE_CLOUD_PROJECT=' + args.project + ',GOOGLE_CLOUD_LOCATION=' + args.model_location
    create('service', args.prefix + '-web', 'run', 'deploy', args.prefix + '-web',
           '--region=' + args.region, '--image=' + args.image,
           '--service-account=' + emails['web'], '--no-invoker-iam-check',
           '--min-instances=0', '--max-instances=2', '--concurrency=4', '--timeout=120',
           '--memory=512Mi', '--cpu=1',
           '--set-env-vars=' + env, '--labels=' + label)
    batch_args = ','.join(['-m', 'translation_demo', 'batch', '--input-uri',
                          'gs://' + input_bucket + '/run-001/passage.txt', '--src', 'en', '--dest', 'fr',
                          '--output-uri', 'gs://' + output_bucket + '/run-001/'])
    create('job', args.prefix + '-audio', 'run', 'jobs', 'create', args.prefix + '-audio',
           '--region=' + args.region, '--image=' + args.image, '--service-account=' + emails['job'],
           '--command=python', '--args=' + batch_args, '--set-env-vars=' + env,
           '--tasks=1', '--max-retries=0', '--task-timeout=300', '--memory=512Mi', '--cpu=1',
           '--labels=' + label)
    manifest['complete'] = True
    if cloud.apply:
        save(args.manifest, manifest)
    print('Setup ' + ('completed' if cloud.apply else 'plan only; nothing created') + '.')
    print('Names: ' + args.prefix + '-function, ' + args.prefix + '-web, ' + args.prefix + '-audio')
    print('The job is created but not executed. No model request is made by this script.')


def load_manifest(path, project):
    manifest = json.loads(path.read_text())
    if manifest.get('schema') != 1 or manifest.get('project') != project:
        raise ValueError('Unsupported manifest or project mismatch.')
    if not re.fullmatch(r'[0-9a-f]{32}', manifest.get('owner', '')):
        raise ValueError('Invalid ownership token.')
    validate_name('prefix', manifest.get('prefix', ''), r'[a-z][a-z0-9-]{2,19}')
    validate_name('region', manifest.get('region', ''), r'[a-z]+[0-9]?(?:-[a-z0-9]+)+')
    # Do not trust arbitrary resource names even in a local manifest.
    p = manifest['prefix']
    expected = {('account', f'{p}-{s}@{project}.iam.gserviceaccount.com') for s in ('function', 'web', 'job')}
    expected |= {('bucket', f'{project}-{p}-{s}') for s in ('input', 'output')}
    expected |= {('service', f'{p}-{s}') for s in ('function', 'web')}
    expected.add(('job', p + '-audio'))
    entries = [(r.get('kind'), r.get('name')) for r in manifest.get('resources', [])]
    if len(entries) != len(expected) or set(entries) != expected:
        raise ValueError('Manifest resource list does not match its project and prefix.')
    for item in manifest['resources']:
        if item.get('state') not in ('planned', 'creating', 'created', 'deleted'):
            raise ValueError('Unknown manifest resource state.')
    return manifest


def owned(item, remote, owner):
    if item['kind'] == 'account':
        return remote.get('description') == 'Managed AC215 tutorial stack ' + owner
    labels = remote.get('labels', remote.get('metadata', {}).get('labels', {}))
    return labels.get(LABEL) == owner


def teardown(args, cloud):
    manifest = load_manifest(args.manifest, args.project)
    region, owner = manifest['region'], manifest['owner']
    items = [r for r in manifest['resources'] if r['state'] not in ('deleted', 'planned')]
    # Complete every ownership check before the first destructive action.
    if cloud.apply:
        for item in items:
            remote = cloud.describe(item['kind'], item['name'], region)
            if remote is None:
                if item['kind'] == 'account' and item['name'].split('@')[0].endswith(('-web', '-job')):
                    cloud.warn_orphaned_bindings(item['name'])
                item['state'] = 'deleted'
            elif not owned(item, remote, owner):
                raise ValueError('Ownership cannot be verified for ' + item['name'] + '. No resources deleted.')
        save(args.manifest, manifest)
    items = [r for r in items if r['state'] != 'deleted']
    if any(r['kind'] == 'bucket' for r in items) and not args.delete_objects:
        raise ValueError('Buckets contain tutorial inputs/results. Add --delete-objects to explicitly authorize removing them.')
    # Read grants before deletion too; partial setup might not have added both roles.
    grants = {r['name']: (cloud.project_roles(r['name']) if cloud.apply else set(ROLES))
              for r in items if r['kind'] == 'account'
              and r['name'].split('@')[0].endswith(('-web', '-job'))}
    # Stop compute first, then data, then identities. On failure leave a resumable manifest.
    for kind in ('job', 'service', 'bucket', 'account'):
        for item in [r for r in items if r['kind'] == kind]:
            name = item['name']
            if kind == 'job':
                cloud.mutate('run', 'jobs', 'delete', name, '--region=' + region)
            elif kind == 'service':
                cloud.mutate('run', 'services', 'delete', name, '--region=' + region)
            elif kind == 'bucket':
                cloud.mutate('storage', 'rm', '--recursive', '--all-versions', 'gs://' + name)
            else:
                if name.split('@')[0].endswith(('-web', '-job')):
                    for role in ROLES:
                        if role not in grants[name]:
                            continue
                        cloud.mutate('projects', 'remove-iam-policy-binding', args.project,
                                     '--member=serviceAccount:' + name, '--role=' + role, '--condition=None')
                cloud.mutate('iam', 'service-accounts', 'delete', name)
            item['state'] = 'deleted'
            if cloud.apply:
                save(args.manifest, manifest)
    manifest['complete'] = False
    manifest['torn_down'] = True
    if cloud.apply:
        save(args.manifest, manifest)
    print('Teardown ' + ('completed' if cloud.apply else 'plan only; nothing deleted') + '.')
    print('Enabled APIs, build logs and generated source-build images are retained; see docs/lifecycle.md.')


def validate_name(label, value, pattern):
    if not re.fullmatch(pattern, value):
        raise ValueError('Invalid ' + label + ': ' + value)


def main(mode, argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True)
    parser.add_argument('--manifest', type=Path, required=True, help='Local ownership journal; retain until teardown')
    parser.add_argument('--apply', action='store_true', help='Execute commands; default only prints a plan')
    if mode == 'up':
        parser.add_argument('--prefix', required=True, help='3–20 lowercase letters/digits/hyphens; begin with a letter')
        parser.add_argument('--region', default='northamerica-northeast2')
        parser.add_argument('--model-location', default='us-central1')
        parser.add_argument('--image', default=DEFAULT_IMAGE)
        parser.add_argument('--developer-member', help='Optional user:EMAIL receiving web-account impersonation only')
    else:
        parser.add_argument('--delete-objects', action='store_true', help='Remove all versions in owned input/output buckets')
    args = parser.parse_args(argv)
    try:
        validate_name('project', args.project, r'[a-z][a-z0-9-]{4,28}[a-z0-9]')
        if mode == 'up':
            validate_name('prefix', args.prefix, r'[a-z][a-z0-9-]{2,19}')
            validate_name('region', args.region, r'[a-z]+[0-9]?(?:-[a-z0-9]+)+')
            validate_name('model location', args.model_location, r'(?:global|[a-z]+[0-9]?(?:-[a-z0-9]+)+)')
            if len(args.project + '-' + args.prefix + '-output') > 63:
                raise ValueError('Project/prefix combination makes bucket names too long.')
            if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._/:@-]+', args.image):
                raise ValueError('Invalid image reference.')
            if args.developer_member and not re.fullmatch(r'user:[^\s,@]+@[^\s,@]+', args.developer_member):
                raise ValueError('--developer-member must be user:EMAIL')
        cloud = Cloud(args.project, args.apply)
        (setup if mode == 'up' else teardown)(args, cloud)
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print('Stopped: ' + str(exc), file=sys.stderr)
        print('Keep the manifest for recovery; later steps were not run.', file=sys.stderr)
        return 1
