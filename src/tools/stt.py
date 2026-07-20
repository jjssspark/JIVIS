"""STT — 마이크 녹음 + Whisper 음성 인식 (Day 11)"""
import os
import tempfile
import numpy as np


def record_audio(duration: int = 5, samplerate: int = 16000) -> str:
    """마이크에서 duration초 녹음 → 임시 WAV 파일 경로 반환."""
    import sounddevice as sd
    from scipy.io.wavfile import write as wav_write

    print(f"🎙️  {duration}초 녹음 시작...")
    audio = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="int16",
    )
    sd.wait()  # 녹음 완료 대기
    print("✅ 녹음 완료")

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wav_write(tmp.name, samplerate, audio)
    return tmp.name


def transcribe(audio_path: str, model_size: str = "base") -> str:
    """WAV 파일을 Whisper로 텍스트 변환. 한국어 자동 감지."""
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_path, beam_size=5)

    text = " ".join(seg.text.strip() for seg in segments)

    # 임시 파일 정리
    try:
        os.remove(audio_path)
    except OSError:
        pass

    return text.strip()


def record_and_transcribe(duration: int = 5) -> str:
    """녹음 + 텍스트 변환을 한 번에."""
    path = record_audio(duration)
    return transcribe(path)


if __name__ == "__main__":
    result = record_and_transcribe(duration=5)
    print(f"인식 결과: {result}")
