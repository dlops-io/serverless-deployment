"""Private Cloud Storage input and create-only output, using ADC."""

import json
import os
import uuid

from google.cloud import storage


def split_uri(uri):
    if not isinstance(uri, str) or not uri.startswith('gs://'):
        raise ValueError('Use a gs://bucket/object-or-prefix URI.')
    bucket, separator, path = uri[5:].partition('/')
    if not bucket or not separator or not path.strip('/') or '?' in uri or '#' in uri:
        raise ValueError('A bucket and an object path or output prefix are required.')
    return bucket, path


def client():
    return storage.Client(project=os.environ.get('GOOGLE_CLOUD_PROJECT'))


def read_text(input_uri):
    bucket, path = split_uri(input_uri)
    blob = client().bucket(bucket).blob(path)
    blob.reload()
    if blob.size is None or blob.size > 20000:
        raise ValueError('Use an input text file no larger than 20,000 bytes for this demo.')
    # Pin the generation we inspected, so replacing the object mid-read fails.
    return blob.download_as_bytes(if_generation_match=blob.generation).decode('utf-8')


def save_artifacts(output_uri, text, audio, mime_type):
    bucket_name, prefix = split_uri(output_uri)
    # Every attempt gets its own prefix. Retries may duplicate work but cannot
    # overwrite a previous attempt; manifest.json is the completion marker.
    attempt = uuid.uuid4().hex
    prefix = prefix.rstrip('/') + '/' + attempt
    bucket = client().bucket(bucket_name)
    uris = {}
    for name, content, content_type in [
        ('translated.txt', text.encode('utf-8'), 'text/plain; charset=utf-8'),
        ('speech.wav', audio, mime_type),
    ]:
        path = prefix + '/' + name
        bucket.blob(path).upload_from_string(content, content_type=content_type, if_generation_match=0)
        uris[name] = f'gs://{bucket_name}/{path}'
    manifest = {
        'status': 'complete', 'artifacts': uris,
        'execution': os.environ.get('CLOUD_RUN_EXECUTION'),
        'task_attempt': os.environ.get('CLOUD_RUN_TASK_ATTEMPT'),
    }
    path = prefix + '/manifest.json'
    bucket.blob(path).upload_from_string(json.dumps(manifest, indent=2),
        content_type='application/json', if_generation_match=0)
    return {'output_uri': f'gs://{bucket_name}/{prefix}/', 'manifest_uri': f'gs://{bucket_name}/{path}', **manifest}
