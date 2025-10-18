# PianoDebugger.py
from PianoGenerator import PianoGenerator, PianoKey, KeyColor, AccidentalType


class PianoDebugger:
    """钢琴调试器 - 用于测试PianoGenerator的功能"""

    def __init__(self):
        # 创建钢琴实例
        self.piano = PianoGenerator(
            base_frequency=440.0,
            accidental_type=AccidentalType.SHARP
        )
        self.setup_callbacks()

    def setup_callbacks(self):
        """设置回调函数用于调试输出"""

        def on_key_press(key: PianoKey):
            print(f"🎹 按下: {key.note_name} (ID: {key.key_id}, 频率: {key.frequency:.2f}Hz, MIDI: {key.midi_number})")

        def on_key_release(key: PianoKey):
            print(f"🔄 释放: {key.note_name}")

        self.piano.set_key_press_callback(on_key_press)
        self.piano.set_key_release_callback(on_key_release)

    def interactive_test(self):
        """交互式测试模式"""
        print("=" * 60)
        print("🎹 钢琴调试器 - 交互测试模式")
        print("=" * 60)
        print("命令说明:")
        print("  play [音名]    - 播放指定音符 (如: play C4)")
        print("  press [ID]     - 按下指定ID的键 (0-87)")
        print("  release [ID]   - 释放指定ID的键")
        print("  find [频率]    - 查找最接近频率的键")
        print("  info [音名]    - 显示键的详细信息")
        print("  list [范围]    - 列出指定范围的键 (如: list C4-E4)")
        print("  test [类型]    - 运行测试 (all, white, black, chord)")
        print("  quit           - 退出调试器")
        print("=" * 60)

        while True:
            try:
                command = input("\n🎵 输入命令: ").strip().split()
                if not command:
                    continue

                cmd = command[0].lower()

                if cmd == 'quit' or cmd == 'exit':
                    print("退出调试器")
                    break

                elif cmd == 'play' and len(command) > 1:
                    self.cmd_play(command[1])

                elif cmd == 'press' and len(command) > 1:
                    self.cmd_press(command[1])

                elif cmd == 'release' and len(command) > 1:
                    self.cmd_release(command[1])

                elif cmd == 'find' and len(command) > 1:
                    self.cmd_find_frequency(command[1])

                elif cmd == 'info' and len(command) > 1:
                    self.cmd_key_info(command[1])

                elif cmd == 'list' and len(command) > 1:
                    self.cmd_list_keys(command[1])

                elif cmd == 'test' and len(command) > 1:
                    self.cmd_run_test(command[1])

                else:
                    print("❌ 未知命令或参数不足")

            except KeyboardInterrupt:
                print("\n\n退出调试器")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")

    def cmd_play(self, note_param: str):
        """播放音符命令"""
        # 尝试作为音名处理
        key = self.piano.get_key_by_note_name(note_param)
        if key:
            print(f"🔊 播放 {key.note_name} - {key.frequency:.2f}Hz")
            self.piano.play_key_frequency(key.key_id, duration=1.0, volume=0.3)
            return

        # 尝试作为ID处理
        try:
            key_id = int(note_param)
            if 0 <= key_id < 88:
                key = self.piano.keys[key_id]
                print(f"🔊 播放 {key.note_name} (ID:{key_id}) - {key.frequency:.2f}Hz")
                self.piano.play_key_frequency(key_id, duration=1.0, volume=0.3)
            else:
                print("❌ 键ID必须在0-87范围内")
        except ValueError:
            print(f"❌ 未找到音符 '{note_param}'")

    def cmd_press(self, key_param: str):
        """按下键命令"""
        self._key_operation(key_param, "press")

    def cmd_release(self, key_param: str):
        """释放键命令"""
        self._key_operation(key_param, "release")

    def _key_operation(self, key_param: str, operation: str):
        """通用的键操作"""
        # 尝试作为音名处理
        key = self.piano.get_key_by_note_name(key_param)
        if key:
            if operation == "press":
                self.piano.press_key(key.key_id)
            else:
                self.piano.release_key(key.key_id)
            return

        # 尝试作为ID处理
        try:
            key_id = int(key_param)
            if 0 <= key_id < 88:
                if operation == "press":
                    self.piano.press_key(key_id)
                else:
                    self.piano.release_key(key_id)
            else:
                print("❌ 键ID必须在0-87范围内")
        except ValueError:
            print(f"❌ 未找到键 '{key_param}'")

    def cmd_find_frequency(self, freq_param: str):
        """查找最接近频率的键"""
        try:
            frequency = float(freq_param)
            closest_key = self.piano.find_closest_key(frequency)
            deviation = self.piano.get_key_frequency_deviation(frequency, closest_key.key_id)

            print(f"🎯 频率 {frequency}Hz 最接近:")
            print(f"   音符: {closest_key.note_name}")
            print(f"   频率: {closest_key.frequency:.2f}Hz")
            print(f"   偏差: {deviation:.1f} 音分")
            print(f"   MIDI: {closest_key.midi_number}")
            print(f"   键ID: {closest_key.key_id}")

        except ValueError:
            print("❌ 请输入有效的频率数字")

    def cmd_key_info(self, note_param: str):
        """显示键的详细信息"""
        key = self.piano.get_key_by_note_name(note_param)
        if not key:
            print(f"❌ 未找到音符 '{note_param}'")
            return

        print(f"🎹 键信息 - {key.note_name}:")
        print(f"   键ID: {key.key_id}")
        print(f"   MIDI编号: {key.midi_number}")
        print(f"   频率: {key.frequency:.2f}Hz")
        print(f"   颜色: {key.color.value}")
        print(f"   位置: ({key.position[0]:.1f}, {key.position[1]:.1f})")
        print(f"   尺寸: {key.width:.1f} x {key.height:.1f}")
        print(f"   按下状态: {'是' if key.is_pressed else '否'}")

    def cmd_list_keys(self, range_param: str):
        """列出指定范围的键"""
        try:
            if '-' in range_param:
                start_note, end_note = range_param.split('-')
                start_key = self.piano.get_key_by_note_name(start_note.strip())
                end_key = self.piano.get_key_by_note_name(end_note.strip())

                if not start_key or not end_key:
                    print("❌ 无效的音符范围")
                    return

                print(f"📋 键列表 {start_note} 到 {end_note}:")
                for key_id in range(start_key.key_id, end_key.key_id + 1):
                    key = self.piano.keys[key_id]
                    status = "●" if key.is_pressed else "○"
                    print(f"   {status} {key.note_name}: {key.frequency:.2f}Hz (ID:{key_id})")
            else:
                # 列出单个八度
                key = self.piano.get_key_by_note_name(range_param)
                if key:
                    octave = range_param[-1]  # 获取八度数字
                    print(f"📋 {octave}八度键列表:")
                    for note in ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]:
                        note_name = f"{note}{octave}"
                        key = self.piano.get_key_by_note_name(note_name)
                        if key:
                            status = "●" if key.is_pressed else "○"
                            print(f"   {status} {key.note_name}: {key.frequency:.2f}Hz (ID:{key.key_id})")
                else:
                    print("❌ 无效的音符或范围")

        except Exception as e:
            print(f"❌ 解析范围时出错: {e}")

    def cmd_run_test(self, test_type: str):
        """运行测试"""
        test_type = test_type.lower()

        if test_type == "all":
            self.test_all_octaves()
        elif test_type == "white":
            self.test_white_keys()
        elif test_type == "black":
            self.test_black_keys()
        elif test_type == "chord":
            self.test_chords()
        else:
            print("❌ 未知测试类型: all, white, black, chord")

    def test_all_octaves(self):
        """测试所有八度的C音"""
        print("🎵 测试所有八度的C音:")
        for octave in range(1, 8):
            note_name = f"C{octave}"
            key = self.piano.get_key_by_note_name(note_name)
            if key:
                print(f"  播放 {note_name} - {key.frequency:.2f}Hz")
                self.piano.play_key_frequency(key.key_id, duration=0.5, volume=0.2)

    def test_white_keys(self):
        """测试白键"""
        print("🎵 测试C大调音阶 (白键):")
        c_major_scale = ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
        for note in c_major_scale:
            key = self.piano.get_key_by_note_name(note)
            if key:
                print(f"  播放 {note}")
                self.piano.play_key_frequency(key.key_id, duration=0.3, volume=0.2)

    def test_black_keys(self):
        """测试黑键"""
        print("🎵 测试黑键 (升C大调音阶):")
        black_keys = ["C#4", "D#4", "F#4", "G#4", "A#4"]
        for note in black_keys:
            key = self.piano.get_key_by_note_name(note)
            if key:
                print(f"  播放 {note}")
                self.piano.play_key_frequency(key.key_id, duration=0.4, volume=0.2)

    def test_chords(self):
        """测试和弦"""
        print("🎵 测试常用和弦:")
        chords = {
            "C大三和弦": ["C4", "E4", "G4"],
            "G大三和弦": ["G4", "B4", "D5"],
            "A小调和弦": ["A4", "C5", "E5"]
        }

        for chord_name, notes in chords.items():
            print(f"  播放 {chord_name}: {notes}")
            for note in notes:
                key = self.piano.get_key_by_note_name(note)
                if key:
                    self.piano.play_key_frequency(key.key_id, duration=1.0, volume=0.15)


if __name__ == "__main__":
    """主函数"""
    print("🎹 钢琴调试器启动中...")

    # 创建调试器
    debugger = PianoDebugger()

    # 显示钢琴信息
    debugger.piano.print_keyboard_info()
    print()

    # 启动交互测试
    debugger.interactive_test()