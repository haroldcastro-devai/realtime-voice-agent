import array

from rva.vad import is_speech, rms


def test_silence_is_not_speech() -> None:
    pcm = b"\x00\x00" * 160
    assert rms(pcm) == 0
    assert not is_speech(pcm, 100)


def test_tone_is_speech() -> None:
    samples = array.array("h", [8000, -8000] * 80)
    assert is_speech(samples.tobytes(), 100)
