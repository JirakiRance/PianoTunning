import json
import os
import numpy as np
from typing import Dict, Any, List
import sys

# 标准88键 MIDI 范围
START_MIDI = 21 # A0
END_MIDI = 108  # C8



# --- 辅助函数：生成静态默认琴弦数据 ---
def _generate_full_static_string_data() -> List[Dict[str, Any]]:
    """生成完整的 88 键 L 和 μ 静态数据，用于文件重建或默认参数。"""
    data = []

    # 模拟长度和密度梯度 (使用对数或线性平滑模拟真实钢琴的渐变)
    num_keys = END_MIDI - START_MIDI + 1

    # 长度从 1.5m 线性递减到 0.008m
    lengths = np.linspace(1.5, 0.008, num_keys)
    # 密度从 0.015 kg/m 模拟对数递减到 0.000004 kg/m
    densities = np.logspace(np.log10(0.015), np.log10(0.000004), num_keys)

    # 标准升号音名表 (从 A0 开始)
    note_names_sharp = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]

    for i, midi in enumerate(range(START_MIDI, END_MIDI + 1)):
        key_id = midi - START_MIDI
        octave = (midi // 12) - 1

        # 修正 A0/A#0/B0 的八度
        if midi <= 23: octave = 0

        note_base = note_names_sharp[(midi - 21) % 12]
        note_name = f"{note_base}{octave}"

        data.append({
            'key_id': key_id,
            'note_name': note_name,
            'length': float(f"{lengths[i]:.4f}"),
            'density': float(f"{densities[i]:.8f}")
        })

    return data

# ----------------------------------------------------


# 静态默认数据（用于文件重建或初始填充）
# STATIC_DEFAULT_STRING_DATA = _generate_full_static_string_data()
STATIC_DEFAULT_STRING_DATA = [
    {"key_id":0,  "note_name":"A0",  "length":1.550,"density":0.01800,"r_string":0.00120},
    {"key_id":1,  "note_name":"A#0", "length":1.540,"density":0.01720,"r_string":0.00118},
    {"key_id":2,  "note_name":"B0",  "length":1.520,"density":0.01650,"r_string":0.00115},

    {"key_id":3,  "note_name":"C1",  "length":1.500,"density":0.01580,"r_string":0.00112},
    {"key_id":4,  "note_name":"C#1", "length":1.480,"density":0.01500,"r_string":0.00110},
    {"key_id":5,  "note_name":"D1",  "length":1.460,"density":0.01430,"r_string":0.00107},
    {"key_id":6,  "note_name":"D#1", "length":1.440,"density":0.01380,"r_string":0.00105},
    {"key_id":7,  "note_name":"E1",  "length":1.420,"density":0.01320,"r_string":0.00102},
    {"key_id":8,  "note_name":"F1",  "length":1.400,"density":0.01270,"r_string":0.00100},
    {"key_id":9,  "note_name":"F#1", "length":1.380,"density":0.01220,"r_string":0.00098},
    {"key_id":10, "note_name":"G1",  "length":1.360,"density":0.01170,"r_string":0.00096},
    {"key_id":11, "note_name":"G#1", "length":1.340,"density":0.01120,"r_string":0.00095},
    {"key_id":12, "note_name":"A1",  "length":1.320,"density":0.01080,"r_string":0.00093},
    {"key_id":13, "note_name":"A#1", "length":1.300,"density":0.01040,"r_string":0.00092},
    {"key_id":14, "note_name":"B1",  "length":1.280,"density":0.01000,"r_string":0.00090},

    {"key_id":15, "note_name":"C2",  "length":1.250,"density":0.00960,"r_string":0.00088},
    {"key_id":16, "note_name":"C#2","length":1.220,"density":0.00920,"r_string":0.00087},
    {"key_id":17, "note_name":"D2",  "length":1.200,"density":0.00880,"r_string":0.00085},
    {"key_id":18, "note_name":"D#2","length":1.180,"density":0.00840,"r_string":0.00084},
    {"key_id":19, "note_name":"E2",  "length":1.150,"density":0.00800,"r_string":0.00083},
    {"key_id":20, "note_name":"F2",  "length":1.130,"density":0.00780,"r_string":0.00082},
    {"key_id":21, "note_name":"F#2","length":1.110,"density":0.00750,"r_string":0.00081},
    {"key_id":22, "note_name":"G2",  "length":1.090,"density":0.00720,"r_string":0.00080},
    {"key_id":23, "note_name":"G#2","length":1.070,"density":0.00700,"r_string":0.00079},
    {"key_id":24, "note_name":"A2",  "length":1.050,"density":0.00680,"r_string":0.00078},
    {"key_id":25, "note_name":"A#2","length":1.030,"density":0.00660,"r_string":0.00077},
    {"key_id":26, "note_name":"B2",  "length":1.000,"density":0.00640,"r_string":0.00076},

    {"key_id":27, "note_name":"C3",  "length":0.970,"density":0.00610,"r_string":0.00075},
    {"key_id":28, "note_name":"C#3","length":0.940,"density":0.00590,"r_string":0.00074},
    {"key_id":29, "note_name":"D3",  "length":0.910,"density":0.00570,"r_string":0.00073},
    {"key_id":30, "note_name":"D#3","length":0.880,"density":0.00555,"r_string":0.00072},
    {"key_id":31, "note_name":"E3",  "length":0.850,"density":0.00540,"r_string":0.00071},
    {"key_id":32, "note_name":"F3",  "length":0.820,"density":0.00520,"r_string":0.00070},
    {"key_id":33, "note_name":"F#3","length":0.795,"density":0.00505,"r_string":0.00070},
    {"key_id":34, "note_name":"G3",  "length":0.770,"density":0.00490,"r_string":0.00069},
    {"key_id":35, "note_name":"G#3","length":0.745,"density":0.00480,"r_string":0.00069},
    {"key_id":36, "note_name":"A3",  "length":0.720,"density":0.00470,"r_string":0.00068},
    {"key_id":37, "note_name":"A#3","length":0.695,"density":0.00460,"r_string":0.00068},
    {"key_id":38, "note_name":"B3",  "length":0.670,"density":0.00450,"r_string":0.00067},

    {"key_id":39, "note_name":"C4",  "length":0.655,"density":0.00430,"r_string":0.00065},
    {"key_id":40, "note_name":"C#4","length":0.630,"density":0.00415,"r_string":0.00063},
    {"key_id":41, "note_name":"D4",  "length":0.605,"density":0.00400,"r_string":0.00061},
    {"key_id":42, "note_name":"D#4","length":0.580,"density":0.00390,"r_string":0.00060},
    {"key_id":43, "note_name":"E4",  "length":0.555,"density":0.00380,"r_string":0.00058},
    {"key_id":44, "note_name":"F4",  "length":0.530,"density":0.00370,"r_string":0.00056},
    {"key_id":45, "note_name":"F#4","length":0.505,"density":0.00360,"r_string":0.00054},
    {"key_id":46, "note_name":"G4",  "length":0.485,"density":0.00350,"r_string":0.00052},
    {"key_id":47, "note_name":"G#4","length":0.465,"density":0.00340,"r_string":0.00050},
    {"key_id":48, "note_name":"A4",  "length":0.450,"density":0.00330,"r_string":0.00049},
    {"key_id":49, "note_name":"A#4","length":0.430,"density":0.00315,"r_string":0.00048},
    {"key_id":50, "note_name":"B4",  "length":0.410,"density":0.00305,"r_string":0.00047},

    {"key_id":51, "note_name":"C5",  "length":0.395,"density":0.00295,"r_string":0.00046},
    {"key_id":52, "note_name":"C#5","length":0.380,"density":0.00285,"r_string":0.00045},
    {"key_id":53, "note_name":"D5",  "length":0.365,"density":0.00275,"r_string":0.00044},
    {"key_id":54, "note_name":"D#5","length":0.350,"density":0.00265,"r_string":0.00043},
    {"key_id":55, "note_name":"E5",  "length":0.335,"density":0.00255,"r_string":0.00042},
    {"key_id":56, "note_name":"F5",  "length":0.320,"density":0.00245,"r_string":0.00041},
    {"key_id":57, "note_name":"F#5","length":0.305,"density":0.00235,"r_string":0.00040},
    {"key_id":58, "note_name":"G5",  "length":0.290,"density":0.00225,"r_string":0.00039},
    {"key_id":59, "note_name":"G#5","length":0.275,"density":0.00215,"r_string":0.00038},
    {"key_id":60, "note_name":"A5",  "length":0.260,"density":0.00205,"r_string":0.00037},
    {"key_id":61, "note_name":"A#5","length":0.245,"density":0.00195,"r_string":0.00036},
    {"key_id":62, "note_name":"B5",  "length":0.230,"density":0.00185,"r_string":0.00035},

    {"key_id":63, "note_name":"C6",  "length":0.215,"density":0.00175,"r_string":0.00034},
    {"key_id":64, "note_name":"C#6","length":0.200,"density":0.00165,"r_string":0.00033},
    {"key_id":65, "note_name":"D6",  "length":0.185,"density":0.00155,"r_string":0.00032},
    {"key_id":66, "note_name":"D#6","length":0.170,"density":0.00145,"r_string":0.00031},
    {"key_id":67, "note_name":"E6",  "length":0.160,"density":0.00135,"r_string":0.00030},
    {"key_id":68, "note_name":"F6",  "length":0.150,"density":0.00130,"r_string":0.00029},
    {"key_id":69, "note_name":"F#6","length":0.145,"density":0.00125,"r_string":0.00028},
    {"key_id":70, "note_name":"G6",  "length":0.140,"density":0.00120,"r_string":0.00027},
    {"key_id":71, "note_name":"G#6","length":0.135,"density":0.00115,"r_string":0.00026},
    {"key_id":72, "note_name":"A6",  "length":0.130,"density":0.00110,"r_string":0.00025},
    {"key_id":73, "note_name":"A#6","length":0.125,"density":0.00105,"r_string":0.00024},
    {"key_id":74, "note_name":"B6",  "length":0.120,"density":0.00100,"r_string":0.00023},

    {"key_id":75, "note_name":"C7",  "length":0.115,"density":0.00095,"r_string":0.00022},
    {"key_id":76, "note_name":"C#7","length":0.110,"density":0.00090,"r_string":0.00021},
    {"key_id":77, "note_name":"D7",  "length":0.105,"density":0.00085,"r_string":0.00020},
    {"key_id":78, "note_name":"D#7","length":0.100,"density":0.00080,"r_string":0.00019},
    {"key_id":79, "note_name":"E7",  "length":0.095,"density":0.00075,"r_string":0.00018},
    {"key_id":80, "note_name":"F7",  "length":0.090,"density":0.00070,"r_string":0.00017},
    {"key_id":81, "note_name":"F#7","length":0.085,"density":0.00065,"r_string":0.00016},
    {"key_id":82, "note_name":"G7",  "length":0.080,"density":0.00060,"r_string":0.00015},
    {"key_id":83, "note_name":"G#7","length":0.075,"density":0.00055,"r_string":0.00014},
    {"key_id":84, "note_name":"A7",  "length":0.070,"density":0.00050,"r_string":0.00013},
    {"key_id":85, "note_name":"A#7","length":0.065,"density":0.00048,"r_string":0.00012},
    {"key_id":86, "note_name":"B7",  "length":0.060,"density":0.00046,"r_string":0.00011},

    {"key_id":87, "note_name":"C8",  "length":0.055,"density":0.00045,"r_string":0.00010},
]

class ConfigManager:
    """
    负责应用程序配置参数的加载和保存。
    同时负责提供静态默认数据。
    """
    CONFIG_FILE_NAME = 'config.json'


    DEFAULT_CONFIG = {
        # 力学参数
        'mech_I': 10.0,
        'mech_r': 0.02,
        'mech_k': 2000.0,
        'mech_Sigma_valid': 210000,
        'mech_Kd': 300,

        'mech_friction_model': "Limit_Friction",
        'mech_fric_limit_0': -10.0,
        'mech_alpha': 0.05,
        # 'mech_kinetic': 0.08,
        'mech_gamma': 0.9,
        'mech_sigma': 0.001,

        'db_file_path': None,

        # 设置菜单（使用枚举的 name 字符串）
        'settings_auto_prompt_save': True,
        'settings_save_recording_file': True,
        'settings_max_recording_time': 10,

        'settings_accidental_type': 'FLAT',     # <-- Enum 名称
        'settings_pitch_algorithm': 'AUTOCORR', # <-- Enum 名称
        'settings_standard_a4': 440,

        # 音频系统
        'audio_sample_rate': 48000,
        'audio_mode': 'sine',
        'audio_tone_path': None,

        # 鼠标平滑
        'mouse_deadzone': 0.5,
        'mouse_alpha': 0.25,
        'mouse_scale': 0.001,
        'mouse_decay_tau': 0.02,

        # 调律完成判断阈值（单位：cents）
        'tuning_done_threshold_cents': 0.5,

        # 调律表盘范围（±多少 cents）
        'tuning_dial_range_cents': 50,

    }







    # def __init__(self, config_dir: str):
    #     self.config_path = os.path.join(config_dir, self.CONFIG_FILE_NAME)
    def __init__(self, config_dir: str):
        # 如果是打包环境，使用用户数据目录
        if getattr(sys, 'frozen', False):
            # 打包后使用用户目录
            if sys.platform == "win32":
                config_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "PianoTuning")
            else:
                config_dir = os.path.join(os.path.expanduser("~"), ".pianotuning")

            # 确保目录存在
            os.makedirs(config_dir, exist_ok=True)

        self.config_path = os.path.join(config_dir, self.CONFIG_FILE_NAME)


    def load_config(self) -> Dict[str, Any]:
        """从文件加载配置，如果缺项则补全默认值。"""
        if not os.path.exists(self.config_path):
            print(f"配置文件未找到，使用默认配置: {self.config_path}")
            return self.DEFAULT_CONFIG.copy()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            merged = self.DEFAULT_CONFIG.copy()
            merged.update(config)

            print(f"配置加载成功: {self.config_path}")
            return merged

        except Exception as e:
            print(f"加载配置文件失败 ({e})，使用默认配置。")
            return self.DEFAULT_CONFIG.copy()


    def save_config(self, config: Dict[str, Any]) -> bool:
        """将当前配置保存到文件。"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                # 使用 copy() 防止在写文件时修改原始字典
                temp_config = config.copy()

                # 额外的安全措施：如果 db_file_path 是 None，为了保持 config.json 清洁，
                # 仅在写入时删除这个键，但不影响 config 字典本身。
                if temp_config.get('db_file_path') is None:
                     del temp_config['db_file_path']

                json.dump(temp_config, f, indent=4)

            print(f"配置保存成功: {self.config_path}")
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
