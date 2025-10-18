from itertools import count

import numpy as np
import sounddevice as sd
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum


BlackArray= (1, 4, 6, 9, 11)        # 黑键在12个键中的位置（A开始
WhiteArray=(0, 2, 3, 5, 7, 8, 10)   # 白键位置

class KeyColor(Enum):
    """琴键颜色枚举"""
    WHITE = "white"
    BLACK = "black"

class AccidentalType(Enum):
    """升降号类型"""
    SHARP = "#"         # 升号
    FLAT = "b"          # 降号

@dataclass
class PianoKey:
    """钢琴键信息"""
    key_id: int                     # 键ID（从0开始，A0=0）
    note_name: str                  # 音名（如 "A0", "C#4" 或 "Db4"）
    frequency: float                # 频率（Hz）
    color: KeyColor                 # 键颜色
    midi_number: int                # MIDI音符编号（A0=21, C8=108）
    position: Tuple[float, float]   # 在界面中的位置 (x, y)
    width: float                    # 键宽度
    height: float                   # 键高度
    is_pressed: bool = False        # 是否被按下


class PianoGenerator:
    """88键钢琴生成器类"""

    def __init__(self, base_frequency: float = 440.0,
                 accidental_type: AccidentalType = AccidentalType.SHARP,
                 key_width: float = 20.0,
                 key_height_white: float = 120.0,
                 key_height_black: float = 80.0):
        """
        :param base_frequency:      基础频率（A4的频率）
        :param accidental_type:     升降号类型（# 或 b）
        :param key_width:           白键宽度
        :param key_height_white:    白键高度
        :param key_height_black:    黑键高度
        """
        self.base_frequency = base_frequency
        self.accidental_type = accidental_type
        self.key_width = key_width
        self.key_height_white = key_height_white
        self.key_height_black = key_height_black

        # 标准88键钢琴范围：A0 到 C8
        self.start_midi = 21    # A0
        self.end_midi = 108     # C8
        self.total_keys = 88

        # 生成钢琴键
        self.keys: Dict[int, PianoKey] = {}
        self._generate_piano_keys()
        self._setup_note_names()

        # 回调函数
        self.key_press_callback: Optional[Callable[[PianoKey], None]] = None
        self.key_release_callback: Optional[Callable[[PianoKey], None]] = None

    def _setup_note_names(self):
        """设置音名"""
        if len(self.keys) > 0:
            for midi_num in range(self.start_midi, self.end_midi + 1):
                key_id = midi_num - self.start_midi
                if key_id in self.keys:
                    self.keys[key_id].note_name = self._get_note_name(midi_num)


    def _generate_piano_keys(self):
        """生成88键钢琴的完整信息"""
        white_key_count = 0

        for midi_number in range(self.start_midi, self.end_midi + 1):
            key_id = midi_number - self.start_midi  # 0-87

            # 计算频率
            frequency = self._calculate_frequency(midi_number)

            # 计算音名和八度
            note_name = self._get_note_name(midi_number)

            # 确定键颜色和位置
            note_index = (midi_number - 21) % 12  # 在八度内的位置(0-11)

            if note_index in BlackArray:  # 黑键
                color = KeyColor.BLACK
                # 黑键位置计算
                white_before = self._count_white_keys_before(midi_number)
                x_pos = (white_before - 0.25) * self.key_width
                y_pos = 0
                width = self.key_width * 0.6
                height = self.key_height_black
            else:  # 白键
                color = KeyColor.WHITE
                # 白键位置计算
                x_pos = white_key_count * self.key_width
                y_pos = 0
                width = self.key_width
                height = self.key_height_white
                white_key_count += 1

            # 创建钢琴键对象
            key = PianoKey(
                key_id=key_id,
                note_name=note_name,
                frequency=frequency,
                color=color,
                midi_number=midi_number,
                position=(x_pos, y_pos),
                width=width,
                height=height
            )

            self.keys[key_id] = key

    def _count_white_keys_before(self, midi_number: int) -> int:
        """计算在某个MIDI编号之前有多少个白键"""
        count = 0
        for i in range(self.start_midi, midi_number):
            note_index = (i - 21) % 12
            if note_index not in BlackArray:  # 不是黑键
                count += 1
        return count

    def _get_note_name(self, midi_number: int) -> str:
        """根据MIDI编号获取音名，直接打表"""
        # 升号表示法对照表
        sharp_table = {
            21: "A0", 22: "A#0", 23: "B0",
            24: "C1", 25: "C#1", 26: "D1", 27: "D#1", 28: "E1", 29: "F1", 30: "F#1", 31: "G1", 32: "G#1", 33: "A1",
            34: "A#1", 35: "B1",
            36: "C2", 37: "C#2", 38: "D2", 39: "D#2", 40: "E2", 41: "F2", 42: "F#2", 43: "G2", 44: "G#2", 45: "A2",
            46: "A#2", 47: "B2",
            48: "C3", 49: "C#3", 50: "D3", 51: "D#3", 52: "E3", 53: "F3", 54: "F#3", 55: "G3", 56: "G#3", 57: "A3",
            58: "A#3", 59: "B3",
            60: "C4", 61: "C#4", 62: "D4", 63: "D#4", 64: "E4", 65: "F4", 66: "F#4", 67: "G4", 68: "G#4", 69: "A4",
            70: "A#4", 71: "B4",
            72: "C5", 73: "C#5", 74: "D5", 75: "D#5", 76: "E5", 77: "F5", 78: "F#5", 79: "G5", 80: "G#5", 81: "A5",
            82: "A#5", 83: "B5",
            84: "C6", 85: "C#6", 86: "D6", 87: "D#6", 88: "E6", 89: "F6", 90: "F#6", 91: "G6", 92: "G#6", 93: "A6",
            94: "A#6", 95: "B6",
            96: "C7", 97: "C#7", 98: "D7", 99: "D#7", 100: "E7", 101: "F7", 102: "F#7", 103: "G7", 104: "G#7",
            105: "A7", 106: "A#7", 107: "B7",
            108: "C8"
        }

        # 降号表示法对照表
        flat_table = {
            21: "A0", 22: "Bb0", 23: "B0",
            24: "C1", 25: "Db1", 26: "D1", 27: "Eb1", 28: "E1", 29: "F1", 30: "Gb1", 31: "G1", 32: "Ab1", 33: "A1",
            34: "Bb1", 35: "B1",
            36: "C2", 37: "Db2", 38: "D2", 39: "Eb2", 40: "E2", 41: "F2", 42: "Gb2", 43: "G2", 44: "Ab2", 45: "A2",
            46: "Bb2", 47: "B2",
            48: "C3", 49: "Db3", 50: "D3", 51: "Eb3", 52: "E3", 53: "F3", 54: "Gb3", 55: "G3", 56: "Ab3", 57: "A3",
            58: "Bb3", 59: "B3",
            60: "C4", 61: "Db4", 62: "D4", 63: "Eb4", 64: "E4", 65: "F4", 66: "Gb4", 67: "G4", 68: "Ab4", 69: "A4",
            70: "Bb4", 71: "B4",
            72: "C5", 73: "Db5", 74: "D5", 75: "Eb5", 76: "E5", 77: "F5", 78: "Gb5", 79: "G5", 80: "Ab5", 81: "A5",
            82: "Bb5", 83: "B5",
            84: "C6", 85: "Db6", 86: "D6", 87: "Eb6", 88: "E6", 89: "F6", 90: "Gb6", 91: "G6", 92: "Ab6", 93: "A6",
            94: "Bb6", 95: "B6",
            96: "C7", 97: "Db7", 98: "D7", 99: "Eb7", 100: "E7", 101: "F7", 102: "Gb7", 103: "G7", 104: "Ab7",
            105: "A7", 106: "Bb7", 107: "B7",
            108: "C8"
        }

        if self.accidental_type == AccidentalType.SHARP:
            return sharp_table[midi_number]
        else:
            return flat_table[midi_number]

    def _calculate_frequency(self, midi_number: int) -> float:
        """
        根据MIDI编号计算频率（十二平均律）
        :param midi_number: MIDI音符编号
        :return: 频率（Hz）
        """
        # A4 = 69, 频率 = base_frequency
        return self.base_frequency * (2 ** ((midi_number - 69) / 12))

    def set_base_frequency(self, new_base_freq: float):
        """
        设置新的基础频率并重新计算所有键的频率
        :param new_base_freq: 新的基础频率
        """
        self.base_frequency = new_base_freq
        # 重新计算所有键的频率
        for key in self.keys.values():
            key.frequency = self._calculate_frequency(key.midi_number)

    def set_accidental_type(self, accidental_type: AccidentalType):
        """
        设置升降号类型并更新所有音名
        :param accidental_type: 新的升降号类型
        """
        self.accidental_type = accidental_type
        self._setup_note_names()

        # 更新所有键的音名
        for key in self.keys.values():
            key.note_name = self._get_note_name(key.midi_number)

    def get_key_by_midi(self, midi_number: int) -> Optional[PianoKey]:
        """根据MIDI编号获取钢琴键"""
        key_id = midi_number - self.start_midi
        return self.keys.get(key_id)

    def get_key_by_note_name(self, note_name: str) -> Optional[PianoKey]:
        """根据音名获取钢琴键"""
        for key in self.keys.values():
            if key.note_name == note_name:
                return key
        return None

    def get_key_at_position(self, x: float, y: float) -> Optional[PianoKey]:
        """
        根据屏幕位置获取钢琴键（用于鼠标点击检测）
        :param x: x坐标
        :param y: y坐标
        :return: 对应的钢琴键
        """
        # 先检查黑键（因为黑键在白键上面）
        for key in self.keys.values():
            if key.color == KeyColor.BLACK:
                key_x, key_y = key.position
                if (key_x <= x <= key_x + key.width and
                        key_y <= y <= key_y + key.height):
                    return key

        # 再检查白键
        for key in self.keys.values():
            if key.color == KeyColor.WHITE:
                key_x, key_y = key.position
                if (key_x <= x <= key_x + key.width and
                        key_y <= y <= key_y + key.height):
                    return key

        return None

    def press_key(self, key_id: int) -> bool:
        """
        按下指定键
        :param key_id: 键ID (0-87)
        :return: 是否成功按下
        """
        if 0 <= key_id < self.total_keys:
            key = self.keys[key_id]
            key.is_pressed = True

            # 触发回调
            if self.key_press_callback:
                self.key_press_callback(key)

            return True
        return False

    def release_key(self, key_id: int) -> bool:
        """
        释放指定键
        :param key_id: 键ID (0-87)
        :return: 是否成功释放
        """
        if 0 <= key_id < self.total_keys:
            key = self.keys[key_id]
            key.is_pressed = False

            # 触发回调
            if self.key_release_callback:
                self.key_release_callback(key)

            return True
        return False

    def play_key_frequency(self, key_id: int, duration: float = 2.0, volume: float = 0.3):
        """
        播放指定键的频率
        :param key_id: 键ID (0-87)
        :param duration: 持续时间（秒）
        :param volume: 音量（0-1）
        """
        if 0 <= key_id < self.total_keys:
            key = self.keys[key_id]
            self._play_tone(key.frequency, duration, volume)

    def _play_tone(self, frequency: float, duration: float, volume: float):
        """播放指定频率的音调"""
        try:
            sample_rate = 44100
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            wave_data = volume * np.sin(2 * np.pi * frequency * t)

            # 添加淡入淡出
            fade_samples = int(0.05 * sample_rate)
            if len(wave_data) > 2 * fade_samples:
                fade_in = np.linspace(0, 1, fade_samples)
                fade_out = np.linspace(1, 0, fade_samples)
                wave_data[:fade_samples] *= fade_in
                wave_data[-fade_samples:] *= fade_out

            sd.play(wave_data, samplerate=sample_rate)

        except Exception as e:
            print(f"播放音调失败: {e}")

    def set_key_press_callback(self, callback: Callable[[PianoKey], None]):
        """设置键按下回调函数"""
        self.key_press_callback = callback

    def set_key_release_callback(self, callback: Callable[[PianoKey], None]):
        """设置键释放回调函数"""
        self.key_release_callback = callback

    def get_keyboard_range(self) -> Tuple[float, float]:
        """获取键盘的频率范围"""
        frequencies = [key.frequency for key in self.keys.values()]
        return min(frequencies), max(frequencies)

    def get_key_count(self) -> Tuple[int, int]:
        """获取白键和黑键的数量"""
        white_count = len([k for k in self.keys.values() if k.color == KeyColor.WHITE])
        black_count = len([k for k in self.keys.values() if k.color == KeyColor.BLACK])
        return white_count, black_count

    def find_closest_key(self, frequency: float) -> PianoKey:
        """
        找到最接近指定频率的钢琴键
        :param frequency: 目标频率
        :return: 最接近的钢琴键
        """
        closest_key = None
        min_diff = float('inf')

        for key in self.keys.values():
            diff = abs(key.frequency - frequency)
            if diff < min_diff:
                min_diff = diff
                closest_key = key

        return closest_key

    def get_key_frequency_deviation(self, measured_freq: float, target_key_id: int) -> float:
        """
        计算测量频率与目标键频率的音分偏差
        :param measured_freq: 测量频率
        :param target_key_id: 目标键ID (0-87)
        :return: 音分偏差
        """
        if target_key_id not in self.keys:
            return 0.0

        target_key = self.keys[target_key_id]
        target_freq = target_key.frequency

        if measured_freq <= 0 or target_freq <= 0:
            return 0.0

        return 1200 * np.log2(measured_freq / target_freq)

    def export_key_frequencies(self) -> Dict[str, float]:
        """导出所有键的频率字典"""
        return {key.note_name: key.frequency for key in self.keys.values()}

    def print_keyboard_info(self):
        """打印键盘信息"""
        white_count, black_count = self.get_key_count()
        min_freq, max_freq = self.get_keyboard_range()

        print(f"88键钢琴信息:")
        print(f"  基础频率: {self.base_frequency}Hz (A4)")
        print(f"  升降号类型: {self.accidental_type.value}")
        print(f"  键数: {white_count}个白键 + {black_count}个黑键 = {self.total_keys}个键")
        print(f"  音域: A0 - C8")
        print(f"  MIDI范围: {self.start_midi} - {self.end_midi}")
        print(f"  频率范围: {min_freq:.1f}Hz - {max_freq:.1f}Hz")

        # 显示一些重要键的信息
        important_notes = ["A0", "C4", "A4", "C8"]
        print(f"  重要键频率:")
        for note in important_notes:
            key = self.get_key_by_note_name(note)
            if key:
                print(f"    {note}: {key.frequency:.2f}Hz")

    def get_keyboard_width(self) -> float:
        """获取整个键盘的宽度"""
        white_count, _ = self.get_key_count()
        return white_count * self.key_width


# 使用示例
def demo_88_key_piano():
    # 创建标准88键钢琴（升号表示法）
    piano_sharp = PianoGenerator(base_frequency=440.0, accidental_type=AccidentalType.SHARP)
    piano_sharp.print_keyboard_info()

    print("\n" + "=" * 50)

    # 创建降号表示法的钢琴
    piano_flat = PianoGenerator(base_frequency=440.0, accidental_type=AccidentalType.FLAT)

    # 显示不同表示法的对比
    print("升降号表示法对比:")
    test_notes = ["C4", "C#4", "D4", "D#4", "E4", "F4"]
    for note_sharp in test_notes:
        key_sharp = piano_sharp.get_key_by_note_name(note_sharp)
        if key_sharp:
            # 找到对应的降号表示
            if "#" in note_sharp:
                note_flat = note_sharp.replace("C#", "Db").replace("D#", "Eb").replace("F#", "Gb").replace("G#",
                                                                                                           "Ab").replace(
                    "A#", "Bb")
            else:
                note_flat = note_sharp

            key_flat = piano_flat.get_key_by_note_name(note_flat)
            if key_flat:
                print(f"  {note_sharp} = {note_flat}: {key_sharp.frequency:.2f}Hz")

    # 测试播放
    print("\n测试播放A4 (440Hz):")
    a4_key = piano_sharp.get_key_by_note_name("A4")
    if a4_key:
        print(f"播放 {a4_key.note_name} - {a4_key.frequency:.2f}Hz")
        piano_sharp.play_key_frequency(a4_key.key_id, duration=1.0)

    # 测试频率匹配
    print("\n测试频率匹配:")
    test_freq = 445.0
    closest_key = piano_sharp.find_closest_key(test_freq)
    deviation = piano_sharp.get_key_frequency_deviation(test_freq, closest_key.key_id)
    print(f"频率 {test_freq}Hz 最接近 {closest_key.note_name}")
    print(f"音分偏差: {deviation:.1f} cents")


if __name__ == "__main__":
    demo_88_key_piano()