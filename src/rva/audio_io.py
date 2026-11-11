"""PCM16 mono resample without audioop (Python 3.13+)."""


def resample_pcm16(pcm: bytes, src_rate: int, dst_rate: int) -> bytes:
    if src_rate == dst_rate or len(pcm) < 4:
        return pcm
    step = src_rate / dst_rate
    n_src = len(pcm) // 2
    n_dst = max(1, int(n_src / step))
    out = bytearray(n_dst * 2)
    for i in range(n_dst):
        src_index = min(n_src - 1, int(i * step))
        out[i * 2 : i * 2 + 2] = pcm[src_index * 2 : src_index * 2 + 2]
    return bytes(out)
