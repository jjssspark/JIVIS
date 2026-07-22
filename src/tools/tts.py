"""TTS — 텍스트 → 음성 (Day 13)"""
import os
import subprocess
import tempfile

from gtts import gTTS


def speak(text: str, lang: str = "ko") -> None:
    """텍스트를 gTTS로 mp3 변환 후 afplay로 재생."""
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    gTTS(text=text, lang=lang).save(tmp.name)

    subprocess.run(["afplay", tmp.name])

    try:
        os.remove(tmp.name)
    except OSError:
        pass


if __name__ == "__main__":
    speak("JIVIS 시작합니다")
