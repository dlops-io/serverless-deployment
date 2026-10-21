import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from translation_demo.__main__ import main
from translation_demo.web import create_app


class ApplicationContracts(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_ui_is_available_without_a_provider_call(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"source-language", response.data)
        self.assertIn(b"Play audio", response.data)

    @patch("translation_demo.web.translate", return_value="Bonjour")
    def test_translation_returns_provider_output(self, provider):
        response = self.client.post("/api/translate", json={"text": "Hello", "src": "en", "dest": "fr"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["text"], "Bonjour")
        provider.assert_called_once_with("Hello", "en", "fr")

    @patch("translation_demo.web.translate")
    def test_bad_input_does_not_reach_provider(self, provider):
        for payload in [[], {"text": ""}, {"text": "hello", "dest": "missing"}, {"text": "x" * 5001}]:
            with self.subTest(payload_type=type(payload).__name__):
                self.assertEqual(self.client.post("/api/translate", json=payload).status_code, 400)
        provider.assert_not_called()

    @patch.dict(os.environ, {"ENABLE_SPEECH": "false"})
    def test_speech_does_not_fake_success(self):
        response = self.client.post("/api/speech", json={"text": "Bonjour", "src": "en", "dest": "fr"})
        self.assertEqual(response.status_code, 503)

    def test_batch_plan_makes_no_provider_calls(self):
        with patch("translation_demo.translation.translate") as translate, patch("translation_demo.speech.synthesize") as speech:
            output = io.StringIO()
            with redirect_stdout(output):
                main(["batch", "--plan", "--text-file", "examples/passage.txt", "--output-uri", "gs://demo/fresh"])
            self.assertIn('"plan_only"', output.getvalue())
            translate.assert_not_called()
            speech.assert_not_called()

    @patch("translation_demo.translation.translate", side_effect=RuntimeError("Provider unavailable"))
    def test_batch_execution_failure_exits_unsuccessfully(self, provider):
        with redirect_stdout(io.StringIO()), patch("sys.stderr", new_callable=io.StringIO):
            with self.assertRaises(SystemExit) as error:
                main(["batch", "--text-file", "examples/passage.txt", "--output-uri", "gs://demo/fresh"])
        self.assertEqual(error.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
