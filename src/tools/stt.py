"""STT — 마이크 녹음 + Whisper 음성 인식 (Day 11)"""
import os
import tempfile
import threading
import numpy as np

_model = None
_model_lock = threading.Lock()


def _get_model(model_size: str = "small"):
    """Whisper 모델을 최초 1회만 로딩해 재사용. 매번 새로 만들면 변환할 때마다
    모델 로딩 시간이 그대로 추가돼 체감 속도가 크게 느려진다.
    local_files_only=True로 고정 — 캐시된 모델이 있어도 매번 허깅페이스 허브에
    갱신 여부를 확인하러 네트워크를 타면서 응답이 20초 이상 멈추는 원인이 됐다."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from faster_whisper import WhisperModel
                _model = WhisperModel(
                    model_size, device="cpu", compute_type="int8", local_files_only=True
                )
    return _model


def warm_up_model(model_size: str = "small") -> None:
    """앱 시작 시 한 번 동기 호출 — 첫 녹음 완료 시점에 모델을 새로 로딩하느라
    발생하는 대기 시간을 없앤다. (백그라운드 스레드로 돌리면 모델 로딩이 CPU를
    많이 써서 메인 스레드의 버튼 클릭 처리가 멈춘 것처럼 보이는 문제가 있었음)"""
    _get_model(model_size)


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
    """녹음 스트림 중지 및 해제. abort()는 남은 버퍼 처리를 기다리지 않고
    즉시 중단해 stop()보다 멈춤 없이 빠르게 반환된다."""
    stream.abort()
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
    model = _get_model(model_size)
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
