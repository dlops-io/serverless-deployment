"""Part 4 integration boundary. The scaffold never uploads files."""


def save_artifacts(output_uri: str, text: str, audio: bytes, mime_type: str):
    """TODO: upload text/audio with ADC and a retry-safe create-only policy.

    Restrict the job's identity to its output bucket. Use object-generation
    preconditions and define how a retry recognizes already completed outputs.
    Keep retrieval permission separate from job write permission.
    """
    raise NotImplementedError("Cloud Storage artifact uploads are not implemented yet.")
