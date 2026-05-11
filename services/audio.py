import subprocess


def extract_audio(video_path: str, audio_path: str):
    subprocess.run([
        "ffmpeg",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        audio_path
    ])