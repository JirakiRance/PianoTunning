# AudioEngine.py — 最终稳定版
# ==========================================================
# 支持三模式:
# 1. sine：纯合成器
# 2. sample：采样文件夹
# 3. sf2：fluidsynth 独立音频输出（dsound）
#
# 特别说明：
#  - 旧版 pyfluidsynth 不支持 write_float()
#    因此 SF2 必须直接用 fluidsynth 自己的驱动
# ==========================================================

import os
import threading
import time
from dataclasses import dataclass
from typing import Optional, Dict, List

import numpy as np
import soundfile as sf
import sounddevice as sd

# ==========================================================
# fluidsynth 检查
# ==========================================================
# FLUIDSYNTH_AVAILABLE = False
# try:
#     import fluidsynth
#     FLUIDSYNTH_AVAILABLE = True
# except Exception:
#     FLUIDSYNTH_AVAILABLE = False
# ==========================================================
# fluidsynth 检查 - 详细版本
# ==========================================================
# FLUIDSYNTH_AVAILABLE = False
# FLUIDSYNTH_MODULE = None
# FLUIDSYNTH_ERROR = None

# try:
#     # 首先尝试导入 fluidsynth
#     import fluidsynth
#     FLUIDSYNTH_MODULE = fluidsynth
#     print("使用 fluidsynth 包")
#     print(f"fluidsynth 文件路径: {fluidsynth.__file__}")

#     # 检查版本
#     version = getattr(fluidsynth, '__version__', '未知')
#     print(f"fluidsynth 版本: {version}")

#     # 列出所有属性
#     all_attrs = [attr for attr in dir(fluidsynth) if not attr.startswith('_')]
#     print(f"fluidsynth 所有公共属性: {all_attrs}")

#     # 检查是否有 Synth 类
#     if hasattr(fluidsynth, 'Synth'):
#         print("fluidsynth 模块包含 Synth 类")
#         try:
#             # 测试创建 Synth 对象
#             test_synth = fluidsynth.Synth()
#             print("fluidsynth.Synth() 创建成功")

#             # 检查 Synth 对象的方法
#             synth_methods = [method for method in dir(test_synth) if not method.startswith('_')]
#             print(f"Synth 对象方法数量: {len(synth_methods)}")

#             del test_synth
#             FLUIDSYNTH_AVAILABLE = True
#         except Exception as e:
#             FLUIDSYNTH_ERROR = f"测试创建 Synth 失败: {e}"
#             print(f"{FLUIDSYNTH_ERROR}")
#             FLUIDSYNTH_AVAILABLE = False
#     else:
#         FLUIDSYNTH_ERROR = "fluidsynth 模块缺少 Synth 类"
#         print(f"{FLUIDSYNTH_ERROR}")
#         FLUIDSYNTH_AVAILABLE = False

# except ImportError as e1:
#     try:
#         # 如果 fluidsynth 失败，尝试 pyfluidsynth
#         import pyfluidsynth as fluidsynth
#         FLUIDSYNTH_MODULE = fluidsynth
#         print("使用 pyfluidsynth 包")
#         FLUIDSYNTH_AVAILABLE = True
#     except ImportError as e2:
#         FLUIDSYNTH_ERROR = f"两种 fluidsynth 包都不可用: fluidsynth={e1}, pyfluidsynth={e2}"
#         print(f"{FLUIDSYNTH_ERROR}")
#         FLUIDSYNTH_AVAILABLE = False

# ==========================================================
# fluidsynth 检查 - 统一导入逻辑
# ==========================================================
FLUIDSYNTH_AVAILABLE = False
FLUIDSYNTH_MODULE = None
FLUIDSYNTH_ERROR = None

def _import_fluidsynth():
    """统一导入 fluidsynth 的逻辑"""
    global FLUIDSYNTH_MODULE, FLUIDSYNTH_AVAILABLE, FLUIDSYNTH_ERROR

    packages_to_try = [
        'fluidsynth',    # 主要包名
        'pyfluidsynth',  # 备选包名
    ]

    for pkg_name in packages_to_try:
        try:
            if pkg_name == 'fluidsynth':
                import fluidsynth as fs
            else:
                import pyfluidsynth as fs

            FLUIDSYNTH_MODULE = fs
            print(f"成功导入 {pkg_name}")
            print(f"  文件路径: {fs.__file__}")

            # 检查版本
            version = getattr(fs, '__version__', '未知')
            print(f"  版本: {version}")

            # 检查所有属性
            all_attrs = [attr for attr in dir(fs) if not attr.startswith('_')]
            print(f"  属性数量: {len(all_attrs)}")

            return True
        except ImportError as e:
            print(f"  导入 {pkg_name} 失败: {e}")
        except Exception as e:
            print(f"  导入 {pkg_name} 时出错: {e}")

    FLUIDSYNTH_ERROR = "所有 fluidsynth 包导入都失败"
    return False

# 执行导入
if _import_fluidsynth():
    # 检查是否有 Synth 类
    if hasattr(FLUIDSYNTH_MODULE, 'Synth'):
        print("fluidsynth 模块包含 Synth 类")
        try:
            # 测试创建 Synth 对象
            test_synth = FLUIDSYNTH_MODULE.Synth()
            print("fluidsynth.Synth() 创建成功")

            # 检查 Synth 对象的方法
            synth_methods = [method for method in dir(test_synth) if not method.startswith('_')]
            print(f"Synth 对象方法数量: {len(synth_methods)}")

            del test_synth
            FLUIDSYNTH_AVAILABLE = True
        except Exception as e:
            FLUIDSYNTH_ERROR = f"测试创建 Synth 失败: {e}"
            print(f"{FLUIDSYNTH_ERROR}")
    else:
        FLUIDSYNTH_ERROR = "fluidsynth 模块缺少 Synth 类"
        print(f"{FLUIDSYNTH_ERROR}")
        # 列出所有可用的属性
        available_attrs = [attr for attr in dir(FLUIDSYNTH_MODULE) if not attr.startswith('_')]
        print(f"可用属性: {available_attrs}")
else:
    print(f"{FLUIDSYNTH_ERROR}")


# ADSR 默认值
DEFAULT_ATTACK = 0.01
DEFAULT_DECAY = 0.05
DEFAULT_SUSTAIN = 0.85
DEFAULT_RELEASE = 0.10
ANTI_DENORMAL = 1e-18


@dataclass
class Voice:
    note_name: str
    velocity: float
    duration: float
    freq: float
    kind: str            # "sine" / "sample"
    sample_data: Optional[np.ndarray] = None
    sample_pos: int = 0
    phase: float = 0.0
    elapsed_time: float = 0.0

    attack: float = DEFAULT_ATTACK
    decay: float = DEFAULT_DECAY
    sustain: float = DEFAULT_SUSTAIN
    release: float = DEFAULT_RELEASE


class AudioEngine:
    """
    终极稳定引擎：
      - sine & sample 通过 sounddevice 回调输出
      - sf2 通过 fluidsynth 独立驱动输出（dsound），完全不混合
    """

    def __init__(self, piano_generator=None, samplerate=44100, blocksize=512):

        self.sr = samplerate
        self.blocksize = blocksize
        self.piano = piano_generator

        # 采样包
        self.sample_folder = None
        self.sample_map: Dict[str, str] = {}
        self.sample_cache: Dict[str, np.ndarray] = {}

        # 播放中的声部
        self._voices: List[Voice] = []
        self._lock = threading.Lock()

        # 模式
        self.mode = "sine"

        # SF2 引擎
        self.fs = None
        self.sf2_id = None
        self.sf2_channel = 0
        self.sf2_path = None

        # 初始化流
        self._init_fluidsynth()
        self._start_stream()

    # ==========================================================
    # sounddevice 回调（仅 sample / sine）
    # ==========================================================
    def _start_stream(self):
        """启动 sounddevice 流。SF2 不走这个流。"""
        if hasattr(self, "_stream"):
            try:
                self._stream.stop()
                self._stream.close()
            except:
                pass

        self._stream = sd.OutputStream(
            samplerate=self.sr,
            blocksize=self.blocksize,
            channels=1,
            dtype="float32",
            callback=self._callback
        )

        self._stream.start()

    def _callback(self, outdata, frames, time_info, status):
        """SF2 不进来！Sample 与 Sine 在此混音"""
        if self.mode == "sf2":
            outdata[:] = 0
            return

        out = np.zeros(frames, dtype="float32")
        remove = []

        with self._lock:
            for v in self._voices:

                # SAMPLE
                if v.kind == "sample":
                    start = v.sample_pos
                    end = start + frames
                    data = v.sample_data

                    chunk = np.zeros(frames, dtype="float32")
                    if start < len(data):
                        remain = min(frames, len(data) - start)
                        chunk[:remain] = data[start:start + remain]

                    v.sample_pos = end
                    if v.sample_pos >= len(data):
                        remove.append(v)

                    out += chunk * v.velocity
                    continue

                # SINE
                freq = float(v.freq)
                t = np.arange(frames, dtype="float32")
                phase_inc = 2 * np.pi * freq / self.sr
                phase = v.phase + phase_inc * t
                v.phase = float(phase[-1] % (2 * np.pi))

                wave = (
                    0.7 * np.sin(phase)
                    + 0.2 * np.sin(2 * phase)
                    + 0.1 * np.sin(3 * phase)
                )

                # 简化版 ADSR：保证不滋滋
                env = np.ones(frames, dtype="float32") * v.sustain
                out += wave * env * v.velocity

                v.elapsed_time += frames / self.sr
                if v.elapsed_time >= v.duration + v.release:
                    remove.append(v)

            for v in remove:
                self._voices.remove(v)

        # limiter
        peak = np.max(np.abs(out))
        if peak > 0.98:
            out *= (0.98 / peak)

        outdata[:, 0] = out + ANTI_DENORMAL

    # ==========================================================
    # 采样包管理
    # ==========================================================
    def set_sample_folder(self, folder):
        if not os.path.isdir(folder):
            raise ValueError("无效的采样包文件夹")

        self.sample_folder = folder
        self._load_samples(folder)
        self.mode = "sample"

    def _load_samples(self, folder):
        supported = (".wav", ".flac", ".aiff", ".aif", ".ogg", ".mp3")

        files = [f for f in os.listdir(folder) if f.lower().endswith(supported)]

        # 值映射 note 名称
        if self.piano:
            note_names = [k.note_name for k in self.piano.keys.values()]
        else:
            pcs = ["C", "C#", "D", "D#", "E", "F", "F#",
                   "G", "G#", "A", "A#", "B"]
            note_names = [f"{pc}{o}" for o in range(0, 9) for pc in pcs]

        self.sample_map.clear()

        # 按文件名匹配音符
        for fn in files:
            lower = fn.lower()
            for note in note_names:
                if note.lower() in lower:
                    self.sample_map[note] = os.path.join(folder, fn)
                    break

        # 预加载
        self.sample_cache.clear()
        for note, path in self.sample_map.items():
            try:
                data, sr = sf.read(path, dtype="float32")
                if data.ndim > 1:
                    data = data.mean(axis=1)

                # normalize
                mx = np.max(np.abs(data))
                if mx > 0:
                    data = data / mx

                # 重采样
                if sr != self.sr:
                    factor = self.sr / sr
                    idx = np.linspace(0, len(data) - 1,
                                      int(len(data) * factor))
                    data = np.interp(idx, np.arange(len(data)), data).astype("float32")

                self.sample_cache[note] = data

            except Exception as e:
                print(f"[AudioEngine] 加载失败 {path}: {e}")

    # ==========================================================
    # SF2 音源 — 旧版 fluidsynth 完整支持
    # ==========================================================
    # def _init_fluidsynth(self):
    #     if not FLUIDSYNTH_AVAILABLE:
    #         self.fs = None
    #         return

    #     try:
    #         self.fs = fluidsynth.Synth()
    #         # ⭐ 关键：必须使用系统驱动
    #         self.fs.start(driver="dsound")
    #     except Exception as e:
    #         print("Fluidsynth 初始化失败:", e)
    #         self.fs = None
    # def _init_fluidsynth(self):

    #     if not FLUIDSYNTH_AVAILABLE:
    #         self.fs = None
    #         print(f"Fluidsynth不可用")
    #         return

    #     try:
    #         print("正在初始化 Fluidsynth...")
    #         # self.fs = fluidsynth.Synth()
    #         self.fs =FLUIDSYNTH_MODULE.Synth()
    #         print("Fluidsynth Synth 对象创建成功")

    #         # 尝试启动音频驱动
    #         print("正在启动 Fluidsynth 音频驱动...")
    #         self.fs.start(driver="dsound")
    #         print("Fluidsynth 音频驱动启动成功")

    #     except Exception as e:
    #         error_msg = f"Fluidsynth 初始化失败: {e}"
    #         print(error_msg)
    #         self.fs = None
    def _init_fluidsynth(self):

        if not FLUIDSYNTH_AVAILABLE:
            self.fs = None
            return

        print("正在初始化 Fluidsynth...")
        self.fs = FLUIDSYNTH_MODULE.Synth()

        # --- 防止 MIDI/SDL 自动检测 ---
        self.fs.setting("midi.autoconnect", 0)
        self.fs.setting("midi.player", 0)
        self.fs.setting("synth.lock-memory", 0)

        # --- 强制音频输出 ---
        preferred_drivers = ["dsound", "wasapi", "portaudio"]

        for drv in preferred_drivers:
            try:
                print(f"尝试驱动: {drv}")
                self.fs.start(driver=drv)
                print(f"Fluidsynth 音频驱动启动成功: {drv}")
                break
            except Exception as e:
                print(f"驱动 {drv} 启动失败: {e}")
        else:
            print("没有可用音频驱动，使用 dummy 输出")
            self.fs.start(driver="file")  # fallback

        print("Fluidsynth 初始化完成")




    def load_sf2(self, sf2_path, bank=0, preset=0):
        """加载一个独立 SF2，用系统声音直接播放"""
        if not FLUIDSYNTH_AVAILABLE:
            raise RuntimeError("未安装 pyfluidsynth")

        if not os.path.isfile(sf2_path):
            raise ValueError("SF2 文件不存在")

        if self.fs is None:
            self._init_fluidsynth()
        if self.fs is None:
            raise RuntimeError("Fluidsynth 初始化失败")

        try:
            self.sf2_id = self.fs.sfload(sf2_path)
            self.fs.program_select(self.sf2_channel, self.sf2_id, bank, preset)
            self.sf2_path = sf2_path
            self.mode = "sf2"
            print("[AudioEngine] 成功加载 SF2:", sf2_path)

        except Exception as e:
            raise RuntimeError(f"加载 SF2 失败: {e}")

    # ==========================================================
    # note 播放
    # ==========================================================
    def play_note(self, note_name, velocity=1.0, duration=1.5):

        # ==== SF2 模式（独立播放） ====
        if self.mode == "sf2" and self.fs and self.sf2_id is not None:
            midi = self._note_to_midi(note_name)
            if midi is None:
                return

            vel = max(1, min(127, int(velocity * 127)))

            try:
                self.fs.noteon(self.sf2_channel, midi, vel)

                threading.Thread(
                    target=self._sf2_noteoff,
                    args=(midi, duration),
                    daemon=True
                ).start()
            except Exception as e:
                print("SF2 noteon 失败:", e)
            return

        # ==== sample / sine ====
        freq = self._note_to_freq(note_name)

        if self.mode == "sample" and note_name in self.sample_cache:
            v = Voice(note_name, velocity, duration, freq,
                      "sample", self.sample_cache[note_name])
        else:
            v = Voice(note_name, velocity, duration, freq, "sine")

        with self._lock:
            self._voices.append(v)

    def _sf2_noteoff(self, midi, duration):
        time.sleep(max(duration, 0.05))
        try:
            if self.fs:
                self.fs.noteoff(self.sf2_channel, midi)
        except:
            pass

    # ==========================================================
    # 工具函数
    # ==========================================================
    def stop_all(self):
        with self._lock:
            self._voices.clear()
        if self.fs:
            try:
                self.fs.system_reset()
            except:
                pass

    def _note_to_freq(self, note):
        if self.piano:
            k = self.piano.get_key_by_note_name(note)
            if k:
                return k.frequency
        return 440.0

    def _note_to_midi(self, note):
        pcs = {
            "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
            "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
            "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11
        }
        try:
            octave = int(note[-1])
            pc = note[:-1]
            return 12 * (octave + 1) + pcs.get(pc, 9)
        except:
            return None

    # ==========================================================
    # ⭐⭐ 你需要的 set_samplerate ⭐⭐
    # ==========================================================
    def set_samplerate(self, new_sr: int):
        """
        更新采样率（sample + sine），并重启 sounddevice 流。
        SF2 不受影响，因为它走系统音频。
        """
        if new_sr == self.sr:
            return

        self.sr = new_sr

        # 重启 audio stream（sample / sine）
        self._start_stream()

        # 如果当前是 sample 模式，则重采样
        if self.sample_folder:
            self._load_samples(self.sample_folder)

        print(f"[AudioEngine] 采样率切换到 {new_sr}")

    def set_mode(self, mode):
        assert mode in ("sine", "sample", "sf2")
        self.mode = mode
