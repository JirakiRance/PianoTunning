
import os
import threading
import math
import numpy as np
import sounddevice as sd
import soundfile as sf
from typing import Dict, Optional, List
from dataclasses import dataclass, field
import time

# 简单 ADSR 包络参数（可外部调整）
DEFAULT_ATTACK = 0.005
DEFAULT_DECAY = 0.05
DEFAULT_SUSTAIN = 0.8
DEFAULT_RELEASE = 0.08

@dataclass
class Voice:
    """活跃声音：合成器或样本回放"""
    note_name: str
    start_time: float
    duration: float
    velocity: float
    kind: str  # 'sine' or 'sample'
    sample_data: Optional[np.ndarray] = None  # 单声道 float32
    sample_sr: Optional[int] = None
    sample_pos: int = 0
    freq: Optional[float] = None  # for synth
    released: bool = False
    release_start: Optional[float] = None

class AudioEngine:
    def __init__(self, piano_generator=None, samplerate=44100, blocksize=512, channels=1):
        self.piano = piano_generator  # PianoGenerator instance (can be None)
        self.sr = samplerate
        self.blocksize = blocksize
        self.channels = channels
        self.mode = "sine"  # "sine" or "sample"
        self.sample_folder: Optional[str] = None
        self.sample_map: Dict[str, str] = {}  # note_name -> filepath
        self._voices: List[Voice] = []
        self._lock = threading.Lock()

        # envelope params
        self.attack = DEFAULT_ATTACK
        self.decay = DEFAULT_DECAY
        self.sustain = DEFAULT_SUSTAIN
        self.release = DEFAULT_RELEASE

        # start output stream with callback mixer
        self._stream = sd.OutputStream(
            samplerate=self.sr,
            blocksize=self.blocksize,
            channels=self.channels,
            dtype='float32',
            callback=self._callback,
            latency='low'
        )
        self._stream.start()

    # ---------------------------
    # 配置与样本扫描
    # ---------------------------
    def set_mode(self, mode: str):
        assert mode in ("sine", "sample")
        self.mode = mode

    def set_sample_folder(self, folder: Optional[str]):
        self.sample_folder = folder
        self.scan_sample_folder()

    def scan_sample_folder(self):
        """扫描 sample_folder，将文件映射到 note 名称（尽量精确匹配）"""
        self.sample_map.clear()
        folder = self.sample_folder
        if not folder or not os.path.isdir(folder):
            return
        # 遍历文件并匹配 note names from piano generator (if available)
        files = []
        for root, _, filenames in os.walk(folder):
            for fn in filenames:
                lower = fn.lower()
                if lower.endswith(('.wav', '.flac', '.aiff', '.aif')):
                    files.append(os.path.join(root, fn))

        # 如果有 piano generator，优先匹配它的 note names
        note_names = []
        if self.piano:
            note_names = [k.note_name for k in self.piano.keys.values()]
        else:
            # fallback: common note names A0..C8
            octaves = range(0,9)
            pcs = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
            for o in octaves:
                for pc in pcs:
                    note_names.append(f"{pc}{o}")

        for fp in files:
            base = os.path.splitext(os.path.basename(fp))[0].lower()
            for note in note_names:
                if note.lower() in base:
                    # prefer exact match or first found
                    if note not in self.sample_map:
                        self.sample_map[note] = fp
                        break

    # ---------------------------
    # 播放接口
    # ---------------------------
    def play_note(self, note_name: str, velocity: float = 1.0, duration: float = 1.5):
        """外部调用：立即触发一个 note（polyphonic）"""
        # resolve frequency if piano generator provided
        freq = None
        if self.piano:
            key = self.piano.get_key_by_note_name(note_name)
            if key:
                freq = key.frequency

        # decide kind: if sample mode and sample found -> sample, else synth
        kind = "sine"
        sample_fp = None
        if self.mode == "sample" and note_name in self.sample_map:
            sample_fp = self.sample_map[note_name]
            kind = "sample"

        voice = Voice(
            note_name=note_name,
            # start_time=sd.get_stream_time(),
            start_time=time.time(),
            duration=duration,
            velocity=max(0.0, min(1.0, velocity)),
            kind=kind,
            sample_data=None,
            sample_sr=None,
            sample_pos=0,
            freq=freq
        )

        # 如果 sample，尝试 preload sample (in background)
        if kind == "sample" and sample_fp:
            try:
                data, sr = sf.read(sample_fp, dtype='float32')
                # convert to mono
                if data.ndim > 1:
                    data = np.mean(data, axis=1)
                # if sample rate mismatch: resample simply (fast nearest)
                if sr != self.sr:
                    # crude resample (for better quality, use resampy)
                    factor = float(self.sr) / float(sr)
                    nframes = int(np.ceil(data.shape[0] * factor))
                    indices = (np.arange(nframes) / factor).astype(int)
                    indices = np.clip(indices, 0, data.shape[0] - 1)
                    data = data[indices]
                voice.sample_data = data.astype('float32')
                voice.sample_sr = self.sr
            except Exception as e:
                print("load sample failed", e)
                voice.kind = "sine"
        # add voice thread-safely
        with self._lock:
            self._voices.append(voice)

    def stop_all(self):
        with self._lock:
            self._voices.clear()
        sd.stop()

    # ---------------------------
    # Mixer callback
    # ---------------------------
    def _callback(self, outdata, frames, time_info, status):
        """sounddevice 输出回调：混音所有活跃 voices 到 outdata"""
        out = np.zeros((frames,), dtype='float32')
        t0 = time_info.outputBufferDacTime  # absolute time of first sample in buffer
        t = (np.arange(frames) / float(self.sr)).astype('float32')

        remove_list = []
        with self._lock:
            for vi, voice in enumerate(self._voices):
                # compute local time base for this voice
                voice_elapsed = t0 - voice.start_time
                sample_indices = (voice_elapsed * self.sr + np.arange(frames)).astype(int)

                if voice.kind == 'sample' and voice.sample_data is not None:
                    # sample mixing (clip at length)
                    data = voice.sample_data
                    pos = int(max(0, voice.sample_pos))
                    # slice from pos for frames
                    end = pos + frames
                    chunk = data[pos:end]
                    # pad if short
                    if chunk.shape[0] < frames:
                        chunk = np.pad(chunk, (0, frames - chunk.shape[0]), mode='constant')
                    # apply velocity scalar and simple linear release if voice ended
                    out += (chunk * voice.velocity).astype('float32')
                    voice.sample_pos = end
                    # if sample finished, mark remove
                    if voice.sample_pos >= len(data):
                        remove_list.append(voice)
                else:
                    # synth mixing (simple harmonic stack with ADSR)
                    # generate sample for this buffer
                    freq = voice.freq if voice.freq else self._note_to_freq(voice.note_name)
                    # local_time array for voice
                    local_t = (voice_elapsed + np.arange(frames) / float(self.sr)).astype('float32')
                    # sine + some harmonics
                    wave = 0.7*np.sin(2*np.pi*freq*local_t) \
                           + 0.2*np.sin(2*np.pi*(freq*2)*local_t)*0.5 \
                           + 0.1*np.sin(2*np.pi*(freq*3)*local_t)*0.25
                    # envelope (attack/decay/sustain/release) simple per-sample
                    env = self._adsr_envelope(local_t, voice.duration, voice.velocity)
                    out += (wave * env).astype('float32')
                    # if voice duration exceeded and release finished -> remove
                    if local_t[0] > voice.duration + self.release + 0.1:
                        remove_list.append(voice)

            # remove finished voices
            for v in remove_list:
                if v in self._voices:
                    self._voices.remove(v)

        # normalize to prevent clipping (simple limiter)
        max_val = np.max(np.abs(out)) if out.size else 0.0
        if max_val > 1.0:
            out /= max_val

        # write to outdata (mono)
        outdata[:] = out.reshape(-1, 1)

    # ---------------------------
    # Helper methods
    # ---------------------------
    def _adsr_envelope(self, t_array: np.ndarray, duration: float, velocity: float):
        """返回长度 = t_array 的包络值（0..1）"""
        env = np.zeros_like(t_array)
        for i, tt in enumerate(t_array):
            if tt < 0:
                env[i] = 0.0
            elif tt < self.attack:
                env[i] = (tt / self.attack) * velocity
            elif tt < self.attack + self.decay:
                # linear decay to sustain
                frac = (tt - self.attack) / self.decay
                env[i] = (1.0 - frac * (1.0 - self.sustain)) * velocity
            elif tt < duration:
                env[i] = self.sustain * velocity
            elif tt < duration + self.release:
                # release phase
                env[i] = max(0.0, (1.0 - (tt - duration) / self.release)) * self.sustain * velocity
            else:
                env[i] = 0.0
        return env

    def _note_to_freq(self, note_name: str) -> float:
        # if piano present, use it
        if self.piano:
            key = self.piano.get_key_by_note_name(note_name)
            if key:
                return key.frequency
        # fallback estimate
        pitch_class_map = {"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11}
        try:
            # parse like C#4 or A4
            octave = int(note_name[-1])
            pc = note_name[:-1]
            midi = 12 * (octave + 1) + pitch_class_map.get(pc, 9)
            return 440.0 * (2.0 ** ((midi - 69) / 12.0))
        except Exception:
            return 440.0
