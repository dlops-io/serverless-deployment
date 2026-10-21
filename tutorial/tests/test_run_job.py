import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('run_job', Path(__file__).resolve().parents[1] / 'run_job.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class HelperContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'passage.txt'
        self.source.write_text('A short passage.')
        self.args = [str(self.source), '--project=demo', '--input-bucket=input', '--output-bucket=output',
                     '--download-dir=' + str(self.root / 'results')]

    @patch.object(helper.subprocess, 'run')
    def test_dry_run_makes_no_calls_or_directories(self, execute):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(helper.main(self.args + ['--dry-run']), 0)
        execute.assert_not_called()
        self.assertFalse((self.root / 'results').exists())

    @patch.object(helper.subprocess, 'run')
    def test_upload_failure_stops_before_execution(self, execute):
        execute.side_effect = subprocess.CalledProcessError(1, ['gcloud'])
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(helper.main(self.args), 1)
        self.assertEqual(execute.call_count, 1)

    @patch.object(helper.subprocess, 'run')
    def test_execution_failure_does_not_download(self, execute):
        execute.side_effect = [None, subprocess.CalledProcessError(1, ['gcloud'])]
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(helper.main(self.args), 1)
        self.assertEqual(execute.call_count, 2)
        self.assertFalse((self.root / 'results').exists())

    @patch.object(helper.subprocess, 'run')
    def test_success_downloads_and_checks_complete_outputs(self, execute):
        def fake(command, check):
            if '--recursive' in command:
                run_id = command[4].rsplit('/', 1)[1]
                folder = self.root / 'results' / run_id / 'attempt'
                folder.mkdir(parents=True)
                (folder / 'manifest.json').write_text(json.dumps({'status': 'complete'}))
                (folder / 'translated.txt').write_text('Bonjour')
                (folder / 'speech.wav').write_bytes(b'WAV')
        execute.side_effect = fake
        with redirect_stdout(io.StringIO()):
            self.assertEqual(helper.main(self.args), 0)
        self.assertEqual(execute.call_count, 3)
        self.assertIn('--wait', execute.call_args_list[1].args[0])

    @patch.object(helper.subprocess, 'run')
    def test_no_download_only_uploads_and_executes(self, execute):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(helper.main(self.args + ['--no-download']), 0)
        self.assertEqual(execute.call_count, 2)


if __name__ == '__main__':
    unittest.main()
