"""STT — 마이크 녹음 + Whisper 음성 인식 (Day 11)"""
import os
import tempfile
import numpy as np


def start_stream(samplerate: int = 16000):
    """비블로킹 마이크 스트림 시작. (stream, frames) 반환 — frames는 콜백이 채워나가는 리스트."""
    import sounddevice as sd

    frames = []

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    stream = sd.InputStream(
        samplerate=samplerate,
        channels=1,
        dtype="int16",
        callback=callback,
    )
    stream.start()
    return stream, frames


def stop_stream(stream) -> None:
    """녹음 스트림 중지 및 해제."""
    stream.stop()
    stream.close()


def save_frames_to_wav(frames, samplerate: int = 16000) -> str:
    """콜백으로 모은 프레임을 WAV 임시 파일로 저장."""
    from scipy.io.wavfile import write as wav_write

    audio = np.concatenate(frames, axis=0) if frames else np.zeros((0, 1), dtype="int16")
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wav_write(tmp.name, samplerate, audio)
    return tmp.name


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


def transcribe(audio_path: str, model_size: str = "small") -> str:
    """WAV 파일을 Whisper로 텍스트 변환. 한국어 고정 + VAD로 무음/잡음 구간 제거."""
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        audio_path,
        language="ko",
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
    )

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
