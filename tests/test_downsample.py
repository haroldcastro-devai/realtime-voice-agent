from rva.audio_io import resample_pcm16


def test_downsample_halves_length() -> None:
    pcm = b"\x01\x00\x02\x00" * 100
    out = resample_pcm16(pcm, 16000, 8000)
    assert 90 <= len(out) // 2 <= 110
