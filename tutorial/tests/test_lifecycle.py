"""Offline lifecycle checks: no Google credentials or network needed."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / 'lifecycle/lifecycle.py'
spec = importlib.util.spec_from_file_location('lifecycle', MODULE)
lifecycle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lifecycle)


class FakeCloud:
    def __init__(self, apply=True, remotes=None, fail_contains=None):
        self.apply = apply
        self.commands = []
        self.inspections = []
        self.remotes = remotes or {}
        self.fail_contains = fail_contains

    def describe(self, kind, name, region):
        self.inspections.append((kind, name, region))
        return self.remotes.get((kind, name))

    def warn_orphaned_bindings(self, email):
        pass

    def project_roles(self, email):
        return set(lifecycle.ROLES)

    def mutate(self, *args):
        self.commands.append(args)
        if self.fail_contains and self.fail_contains in args:
            raise subprocess.CalledProcessError(1, args)


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.args = SimpleNamespace(project='example-project', prefix='lecture14-test',
            region='northamerica-northeast2', model_location='us-central1',
            image=lifecycle.DEFAULT_IMAGE, developer_member=None,
            manifest=Path(self.tmp.name) / 'stack.json', delete_objects=True)
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)
        self.errors = contextlib.redirect_stderr(io.StringIO())
        self.errors.__enter__()
        self.addCleanup(self.errors.__exit__, None, None, None)

    def setup_stack(self):
        cloud = FakeCloud()
        lifecycle.setup(self.args, cloud)
        return json.loads(self.args.manifest.read_text()), cloud

    def remotes(self, manifest):
        result = {}
        for item in manifest['resources']:
            if item['kind'] == 'account':
                remote = {'description': 'Managed AC215 tutorial stack ' + manifest['owner']}
            elif item['kind'] in ('service', 'job'):
                remote = {'metadata': {'labels': {lifecycle.LABEL: manifest['owner']}}}
            else:
                remote = {'labels': {lifecycle.LABEL: manifest['owner']}}
            result[(item['kind'], item['name'])] = remote
        return result

    def test_dry_run_has_no_network_or_manifest_writes(self):
        with patch.object(subprocess, 'run', side_effect=AssertionError('network call')):
            lifecycle.setup(self.args, lifecycle.Cloud(self.args.project))
        self.assertFalse(self.args.manifest.exists())

    def test_setup_checks_all_names_and_separates_runtime_permissions(self):
        manifest, cloud = self.setup_stack()
        self.assertEqual(len(cloud.inspections), 8)
        self.assertTrue(manifest['complete'])
        grants = [c for c in cloud.commands if c[:3] == ('storage', 'buckets', 'add-iam-policy-binding')]
        self.assertEqual(len(grants), 2)
        self.assertTrue(all('--member=serviceAccount:lecture14-test-job@example-project.iam.gserviceaccount.com' in c for c in grants))
        self.assertIn('--role=roles/storage.objectViewer', grants[0])
        self.assertIn('--role=roles/storage.objectCreator', grants[1])
        jobs = [c for c in cloud.commands if c[:3] == ('run', 'jobs', 'create')]
        self.assertEqual(len(jobs), 1)
        self.assertIn('--command=python', jobs[0])
        self.assertIn('--max-retries=0', jobs[0])
        self.assertTrue(any(c.startswith('--args=-m,translation_demo,batch,--input-uri,gs://example-project-lecture14-test-input/run-001/') for c in jobs[0]))
        services = [c for c in cloud.commands if c[:2] == ('run', 'deploy')]
        self.assertTrue(all('--no-invoker-iam-check' in c and '--allow-unauthenticated' not in c for c in services))
        self.assertFalse(any('execute' in c for c in cloud.commands))
        self.assertFalse(any('keys' in c for c in cloud.commands))

    def test_existing_resource_prevents_resource_creation(self):
        fake = FakeCloud(remotes={('bucket', 'example-project-lecture14-test-output'): {'labels': {}}})
        with self.assertRaisesRegex(ValueError, 'Refusing to adopt'):
            lifecycle.setup(self.args, fake)
        self.assertEqual(len(fake.commands), 1)
        self.assertEqual(fake.commands[0][:2], ('services', 'enable'))
        self.assertFalse(self.args.manifest.exists())

    def test_failed_create_preserves_recovery_journal(self):
        fake = FakeCloud(fail_contains='--source=' + str(lifecycle.ROOT / 'tutorial/function'))
        with self.assertRaises(subprocess.CalledProcessError):
            lifecycle.setup(self.args, fake)
        manifest = json.loads(self.args.manifest.read_text())
        states = {r['name']: r['state'] for r in manifest['resources']}
        self.assertEqual(states['lecture14-test-function'], 'creating')
        self.assertEqual(states['lecture14-test-web'], 'planned')
        self.assertFalse(manifest['complete'])

    def test_ownership_checked_for_every_resource_before_any_delete(self):
        manifest, _ = self.setup_stack()
        remotes = self.remotes(manifest)
        remotes[('job', 'lecture14-test-audio')] = {'metadata': {'labels': {}}}
        fake = FakeCloud(remotes=remotes)
        with self.assertRaisesRegex(ValueError, 'Ownership'):
            lifecycle.teardown(self.args, fake)
        self.assertEqual(fake.commands, [])
        self.assertEqual(len(fake.inspections), 8)

    def test_object_deletion_requires_explicit_opt_in(self):
        manifest, _ = self.setup_stack()
        self.args.delete_objects = False
        fake = FakeCloud(remotes=self.remotes(manifest))
        with self.assertRaisesRegex(ValueError, '--delete-objects'):
            lifecycle.teardown(self.args, fake)
        self.assertEqual(fake.commands, [])

    def test_teardown_order_and_resumability(self):
        manifest, _ = self.setup_stack()
        fake = FakeCloud(remotes=self.remotes(manifest), fail_contains='lecture14-test-web')
        with self.assertRaises(subprocess.CalledProcessError):
            lifecycle.teardown(self.args, fake)
        journal = json.loads(self.args.manifest.read_text())
        deleted = {r['name'] for r in journal['resources'] if r['state'] == 'deleted'}
        self.assertEqual(deleted, {'lecture14-test-audio', 'lecture14-test-function'})
        second = FakeCloud(remotes=self.remotes(manifest))
        lifecycle.teardown(self.args, second)
        self.assertEqual(second.commands[0][:4], ('run', 'services', 'delete', 'lecture14-test-web'))
        buckets = [c for c in second.commands if c[:2] == ('storage', 'rm')]
        self.assertEqual(len(buckets), 2)
        self.assertTrue(all('--all-versions' in c and '--recursive' in c for c in buckets))
        journal = json.loads(self.args.manifest.read_text())
        self.assertTrue(journal['torn_down'])
        self.assertTrue(all(r['state'] == 'deleted' for r in journal['resources']))

    def test_missing_resources_do_not_prevent_cleanup(self):
        self.setup_stack()
        fake = FakeCloud(remotes={})
        lifecycle.teardown(self.args, fake)
        self.assertEqual(fake.commands, [])

    def test_unlabeled_bucket_after_interrupted_setup_requires_manual_recovery(self):
        manifest, _ = self.setup_stack()
        remotes = self.remotes(manifest)
        remotes[('bucket', 'example-project-lecture14-test-input')] = {'labels': {}}
        fake = FakeCloud(remotes=remotes)
        with self.assertRaisesRegex(ValueError, 'Ownership'):
            lifecycle.teardown(self.args, fake)
        self.assertEqual(fake.commands, [])

    def test_partial_setup_missing_role_binding_is_not_removed(self):
        manifest, _ = self.setup_stack()
        fake = FakeCloud(remotes=self.remotes(manifest))
        fake.project_roles = lambda email: set()
        lifecycle.teardown(self.args, fake)
        self.assertFalse(any(c[:2] == ('projects', 'remove-iam-policy-binding')
                             for c in fake.commands))
        self.assertEqual(sum(c[:3] == ('iam', 'service-accounts', 'delete')
                             for c in fake.commands), 3)

    def test_tampered_manifest_rejected_before_cloud_calls(self):
        manifest, _ = self.setup_stack()
        manifest['resources'][0]['name'] = 'unrelated@example-project.iam.gserviceaccount.com'
        self.args.manifest.write_text(json.dumps(manifest))
        fake = FakeCloud()
        with self.assertRaisesRegex(ValueError, 'resource list'):
            lifecycle.teardown(self.args, fake)
        self.assertEqual(fake.inspections, [])

    def test_inspection_auth_failure_is_not_absence(self):
        response = subprocess.CompletedProcess([], 1, '', 'PERMISSION_DENIED 403: resource does not exist or you lack access')
        with patch.object(subprocess, 'run', return_value=response):
            with self.assertRaisesRegex(RuntimeError, 'Cannot inspect'):
                lifecycle.Cloud(self.args.project, True).describe('job', 'a-job', self.args.region)

    def test_inspection_missing_resource_is_absence(self):
        response = subprocess.CompletedProcess([], 1, '', 'NOT_FOUND: job does not exist')
        with patch.object(subprocess, 'run', return_value=response):
            self.assertIsNone(lifecycle.Cloud(self.args.project, True).describe('job', 'a-job', self.args.region))

    def test_account_inspection_uses_authorized_active_list(self):
        email = 'lecture14-test-job@example-project.iam.gserviceaccount.com'
        for data, exists in (([], False), ([{'email': email, 'description':'managed'}], True),
                             ([{'email':'unrelated@example-project.iam.gserviceaccount.com'}], False)):
            response = subprocess.CompletedProcess([], 0, json.dumps(data), '')
            with self.subTest(data=data), patch.object(subprocess, 'run', return_value=response) as run:
                account = lifecycle.Cloud(self.args.project, True).describe('account', email, self.args.region)
                self.assertEqual(account is not None, exists)
                self.assertIn('list', run.call_args.args[0])
                self.assertIn('--filter=email=' + email, run.call_args.args[0])
        for error in ('PERMISSION_DENIED: cannot list accounts',
                      'NOT_FOUND: project does not exist', 'HTTPError 404: project not found'):
            response = subprocess.CompletedProcess([], 1, '', error)
            with self.subTest(error=error), patch.object(subprocess, 'run', return_value=response):
                with self.assertRaises(RuntimeError):
                    lifecycle.Cloud(self.args.project, True).describe('account', email, self.args.region)

    def test_real_cloud_run_missing_messages_are_absence(self):
        for kind in ('service', 'job'):
            response = subprocess.CompletedProcess([], 1, '',
                f'ERROR: (gcloud.run.{kind}s.describe) Cannot find {kind} [demo].')
            with self.subTest(kind=kind), patch.object(subprocess, 'run', return_value=response):
                self.assertIsNone(lifecycle.Cloud(self.args.project, True).describe(kind, 'demo', self.args.region))

    def test_iam_propagation_retry_is_bounded_and_specific(self):
        unavailable = subprocess.CompletedProcess([], 1, '',
            'INVALID_ARGUMENT: Service account new@example-project.iam.gserviceaccount.com does not exist.')
        success = subprocess.CompletedProcess([], 0, '', '')
        cloud = lifecycle.Cloud(self.args.project, True)
        with patch.object(subprocess, 'run', side_effect=[unavailable, unavailable, success]) as run, patch.object(lifecycle.time, 'sleep') as sleep:
            cloud.mutate('projects', 'add-iam-policy-binding', self.args.project)
            self.assertEqual(run.call_count, 3)
            self.assertEqual([x.args[0] for x in sleep.call_args_list], [1, 2])
        with patch.object(subprocess, 'run', return_value=unavailable) as run, patch.object(lifecycle.time, 'sleep') as sleep:
            with self.assertRaises(subprocess.CalledProcessError):
                cloud.mutate('projects', 'add-iam-policy-binding', self.args.project)
            self.assertEqual(run.call_count, 6)
            self.assertEqual(sleep.call_count, 5)

    def test_generic_403_is_never_retried(self):
        response = subprocess.CompletedProcess([], 1, '',
            'PERMISSION_DENIED 403: Service account missing does not exist or caller lacks access')
        with patch.object(subprocess, 'run', return_value=response) as run, patch.object(lifecycle.time, 'sleep') as sleep:
            with self.assertRaises(subprocess.CalledProcessError):
                lifecycle.Cloud(self.args.project, True).mutate('projects', 'add-iam-policy-binding', self.args.project)
            self.assertEqual(run.call_count, 1)
            sleep.assert_not_called()

    def test_global_model_location_and_web_flags(self):
        self.args.model_location = 'global'
        manifest, cloud = self.setup_stack()
        web = next(c for c in cloud.commands if c[:3] == ('run', 'deploy', 'lecture14-test-web'))
        for flag in ('--max-instances=2', '--concurrency=4', '--timeout=120'):
            self.assertIn(flag, web)
        self.assertTrue(any('GOOGLE_CLOUD_LOCATION=global' in c for c in web))
        with patch.object(lifecycle, 'setup') as setup:
            self.assertEqual(lifecycle.main('up', ['--project=example-project', '--prefix=demo',
                '--model-location=global', '--manifest=' + str(self.args.manifest)]), 0)
            setup.assert_called_once()

    def test_orphaned_binding_warning_never_mutates_policy(self):
        email = 'lecture14-test-job@example-project.iam.gserviceaccount.com'
        deleted = 'deleted:serviceAccount:' + email + '?uid=123'
        policy = {'bindings': [
            {'role': 'roles/aiplatform.user', 'members': [deleted]},
            {'role': 'roles/owner', 'members': [deleted]},
            {'role': 'roles/aiplatform.user', 'members': ['deleted:serviceAccount:someone-else@example-project.iam.gserviceaccount.com?uid=456']} ]}
        response = subprocess.CompletedProcess([], 0, json.dumps(policy), '')
        warnings = io.StringIO()
        with patch.object(subprocess, 'run', return_value=response) as run, contextlib.redirect_stderr(warnings):
            lifecycle.Cloud(self.args.project, True).warn_orphaned_bindings(email)
        self.assertEqual(run.call_count, 1)
        self.assertIn('get-iam-policy', run.call_args.args[0])
        self.assertIn(deleted, warnings.getvalue())
        self.assertNotIn('roles/owner', warnings.getvalue())
        self.assertNotIn('someone-else', warnings.getvalue())

    def test_commands_use_argv_and_explicit_project(self):
        cloud = lifecycle.Cloud('example-project', True)
        with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')) as run:
            cloud.mutate('iam', 'service-accounts', 'create', 'demo', '--display-name=A demo account')
        argv = run.call_args.args[0]
        self.assertIn('--display-name=A demo account', argv)
        self.assertIn('--project=example-project', argv)
        self.assertNotIn('shell', run.call_args.kwargs)
        self.assertNotIn('capture_output', run.call_args.kwargs)


if __name__ == '__main__':
    unittest.main()
