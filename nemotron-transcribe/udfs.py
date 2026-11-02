"""Call NVIDIA Nemotron 3.5 Transcribe through Hugging Face."""

import pathlib

import pixeltable as pxt
from pixeltable.config import Config

# Checkpoint: https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B
# Hugging Face routes this model to DeepInfra's OpenAI-compatible speech-to-text API.
MODEL_ID = 'nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B'
ROUTER = 'https://router.huggingface.co/deepinfra/v1/openai'


def _hf_token() -> str:
    """The Hugging Face token Pixeltable already reads, or the one `hf auth login` saved."""
    token = Config.get().get_string_value('token', section='hf')
    if token:
        return token
    saved = pathlib.Path.home() / '.cache' / 'huggingface' / 'token'
    if saved.is_file():
        text = saved.read_text().strip()
        if text:
            return text
    raise RuntimeError(
        'A Hugging Face token is required. Set HF_TOKEN, or set token under [hf] in '
        '~/.pixeltable/config.toml. The token needs Inference Providers credits: '
        'https://huggingface.co/settings/inference-providers'
    )


@pxt.udf
def nemotron_transcribe(audio: pxt.Audio, prompt: str) -> str:
    """Transcript of the audio. `prompt` is the instruction sent with it."""
    from openai import OpenAI

    client = OpenAI(api_key=_hf_token(), base_url=ROUTER, timeout=600.0)
    path = pathlib.Path(audio)
    suffix = path.suffix.lower() or '.mp3'
    kwargs: dict[str, str] = {}
    if prompt.strip():
        kwargs['prompt'] = prompt
    with path.open('rb') as audio_file:
        result = client.audio.transcriptions.create(
            model=MODEL_ID,
            file=(f'audio{suffix}', audio_file),
            **kwargs,
        )
    return result.text
