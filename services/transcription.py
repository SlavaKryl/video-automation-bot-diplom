from faster_whisper import WhisperModel

model = WhisperModel("base")


def transcribe(audio_path: str) -> str:
    segments, _ = model.transcribe(audio_path)

    text = ""
    for segment in segments:
        text += segment.text + " "

    return text.strip()