import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch, MagicMock

from translation_demo.__main__ import main
from translation_demo.storage import read_text, save_artifacts


class BatchContracts(unittest.TestCase):
    @patch('translation_demo.storage.client')
    @patch('translation_demo.translation.translate')
    def test_remote_plan_never_downloads_or_calls_provider(self, translate, client):
        with redirect_stdout(io.StringIO()) as output:
            main(['batch', '--plan', '--input-uri', 'gs://input/passage.txt', '--output-uri', 'gs://output/run'])
        self.assertEqual(json.loads(output.getvalue())['status'], 'plan_only')
        translate.assert_not_called()
        client.assert_not_called()

    @patch('translation_demo.storage.save_artifacts', return_value={'status': 'complete'})
    @patch('translation_demo.speech.synthesize', return_value=(b'WAV', 'audio/wav'))
    @patch('translation_demo.translation.translate', return_value='Bonjour')
    @patch('translation_demo.storage.read_text', return_value='Hello')
    def test_remote_batch_reuses_translation_and_speech_then_saves(self, read, translate, speech, save):
        with redirect_stdout(io.StringIO()) as output:
            main(['batch', '--input-uri', 'gs://input/passage.txt', '--output-uri', 'gs://output/run'])
        translate.assert_called_once_with('Hello', 'en', 'fr')
        speech.assert_called_once_with('Bonjour', 'fr')
        save.assert_called_once_with('gs://output/run', 'Bonjour', b'WAV', 'audio/wav')
        self.assertEqual(json.loads(output.getvalue())['status'], 'complete')

    @patch('translation_demo.storage.client')
    def test_uploads_are_create_only_with_manifest_last(self, client):
        bucket = client.return_value.bucket.return_value
        first = save_artifacts('gs://output/run', 'Bonjour', b'audio', 'audio/wav')
        second = save_artifacts('gs://output/run', 'Bonjour', b'audio', 'audio/wav')
        self.assertNotEqual(first['output_uri'], second['output_uri'])
        paths = [call.args[0] for call in bucket.blob.call_args_list]
        self.assertEqual([p.rsplit('/', 1)[1] for p in paths[:3]], ['translated.txt', 'speech.wav', 'manifest.json'])
        for call in bucket.blob.return_value.upload_from_string.call_args_list:
            self.assertEqual(call.kwargs['if_generation_match'], 0)

    @patch('translation_demo.storage.client')
    def test_oversized_input_is_not_downloaded(self, client):
        blob = client.return_value.bucket.return_value.blob.return_value
        blob.size = 20001
        with self.assertRaises(ValueError):
            read_text('gs://input/passage.txt')
        blob.download_as_bytes.assert_not_called()

    @patch('translation_demo.storage.client')
    def test_input_download_is_pinned_to_inspected_generation(self, client):
        blob = client.return_value.bucket.return_value.blob.return_value
        blob.size, blob.generation = 5, 123
        blob.download_as_bytes.return_value = b'Hello'
        self.assertEqual(read_text('gs://input/passage.txt'), 'Hello')
        blob.download_as_bytes.assert_called_once_with(if_generation_match=123)

    @patch('translation_demo.storage.client')
    def test_failed_upload_does_not_write_completion_manifest(self, client):
        bucket = client.return_value.bucket.return_value
        bucket.blob.return_value.upload_from_string.side_effect = RuntimeError('upload failed')
        with self.assertRaises(RuntimeError):
            save_artifacts('gs://output/run', 'Bonjour', b'audio', 'audio/wav')
        self.assertEqual(bucket.blob.call_count, 1)
