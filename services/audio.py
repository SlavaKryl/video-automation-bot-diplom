import subprocess
from pathlib import Path


def extract_audio(video_path: str, audio_path: str):
    """Extract wav audio track from video file."""
    Path(audio_path).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        audio_path,
    ], check=True)


def trim_silence(input_audio_path: str, output_audio_path: str):
    """Remove long silence chunks to make speech denser for shorts/reels."""
    Path(output_audio_path).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg",
        "-y",
        "-i", input_audio_path,
        "-af",
        # cut silence at start/end and long internal pauses
        "silenceremove=start_periods=1:start_duration=0.4:start_threshold=-45dB:"
        "stop_periods=-1:stop_duration=0.5:stop_threshold=-45dB",
        output_audio_path,
    ], check=True)
