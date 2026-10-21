import base64
import io
import os
import unittest
import wave
from unittest.mock import MagicMock, patch

from translation_demo.speech import SpeechConfigurationError, SpeechProviderError, decode_response, synthesize
from translation_demo.web import create_app


def response_audio(pcm=b'\x00\x00\x01\x00', mime='audio/L16;codec=pcm;rate=24000'):
    return {'candidates': [{'content': {'parts': [{'inlineData': {
        'mimeType': mime, 'data': base64.b64encode(pcm).decode()
    }}]}}]}


class SpeechContracts(unittest.TestCase):
    def test_pcm_is_wrapped_in_playable_wav(self):
        with wave.open(io.BytesIO(decode_response(response_audio())), 'rb') as audio:
            self.assertEqual((audio.getnchannels(), audio.getsampwidth(), audio.getframerate()), (1, 2, 24000))
            self.assertEqual(audio.readframes(2), b'\x00\x00\x01\x00')

    def test_missing_or_incompatible_audio_is_rejected(self):
        for data in [{}, response_audio(b'x'), response_audio(mime='audio/mpeg'), response_audio(mime='audio/L16;rate=16000')]:
            with self.subTest(data=data), self.assertRaises(SpeechProviderError):
                decode_response(data)

    @patch.dict(os.environ, {'ENABLE_SPEECH': 'true', 'GOOGLE_CLOUD_PROJECT': 'demo-project', 'GOOGLE_CLOUD_LOCATION': 'us-central1'})
    @patch('translation_demo.speech.AuthorizedSession')
    @patch('translation_demo.speech.google.auth.default')
    def test_adc_call_uses_selected_project_and_language(self, adc, session_factory):
        adc.return_value = (object(), 'ignored-project')
        response = MagicMock(status_code=200, ok=True)
        response.json.return_value = response_audio()
        session = session_factory.return_value.__enter__.return_value
        session.post.return_value = response
        audio, mime = synthesize('Bonjour', 'fr')
        self.assertEqual(mime, 'audio/wav')
        self.assertTrue(audio.startswith(b'RIFF'))
        args, kwargs = session.post.call_args
        self.assertIn('/projects/demo-project/locations/us-central1/', args[0])
        self.assertEqual(kwargs['json']['generationConfig']['speechConfig']['languageCode'], 'fr-FR')
        self.assertEqual(adc.call_args.kwargs['quota_project_id'], 'demo-project')
        response.status_code = 403
        with self.assertRaises(SpeechConfigurationError):
            synthesize('Bonjour', 'fr')

    @patch('translation_demo.web.synthesize', return_value=(b'RIFFexample', 'audio/wav'))
    def test_http_route_returns_audio_without_storage(self, provider):
        response = create_app().test_client().post('/api/speech', json={'text': 'Bonjour', 'dest': 'fr'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'audio/wav')
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        provider.assert_called_once_with('Bonjour', 'fr')

    @patch.dict(os.environ, {'ENABLE_SPEECH': 'true', 'GOOGLE_CLOUD_PROJECT': 'demo-project'})
    @patch('translation_demo.speech.google.auth.default')
    def test_byte_limit_is_checked_before_authentication(self, adc):
        with self.assertRaises(ValueError):
            synthesize('界' * 1400, 'zh-cn')
        adc.assert_not_called()
