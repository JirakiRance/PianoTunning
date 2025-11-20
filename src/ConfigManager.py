import json
import os
import numpy as np
from typing import Dict, Any, List

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


class ConfigManager:
    """
    负责应用程序配置参数的加载和保存。
    同时负责提供静态默认数据。
    """
    CONFIG_FILE_NAME = 'config.json'

    # 定义应用程序的默认配置
    # DEFAULT_CONFIG: Dict[str, Any] = {
    #     # 核心物理参数 (全局)
    #     'mech_I': 0.0001,      # 转动惯量 I (kg·m²)
    #     'mech_r': 0.005,       # 弦轴半径 r (m)
    #     'mech_k': 500000.0,    # 弦劲度系数 k (N/m)
    #     'mech_Sigma_valid': 2100000, #许用应力 [σ]
    #     'mech_Kd': 0.5,        # 施力敏感度 K_D (N·m·s/rad)

    #     # 摩擦模型参数 (全局)
    #     'mech_friction_model': "Limit_Friction",
    #     'mech_fric_limit_0': 0.1, # 初始静摩擦 τ_fric_limit_0
    #     'mech_alpha': 0.05,       # 静摩擦增长系数 α
    #     'mech_kinetic': 0.08,     # 动摩擦扭矩 τ_kinetic
    #     'mech_sigma': 0.001,      # 粘性摩擦系数 σ

    #     # 琴弦数据文件路径
    #     'db_file_path': None,
    # }
    DEFAULT_CONFIG = {
        # 力学参数
        'mech_I': 0.0001,
        'mech_r': 0.005,
        'mech_k': 500000.0,
        'mech_Sigma_valid': 210000,
        'mech_Kd': 0.5,

        'mech_friction_model': "Limit_Friction",
        'mech_fric_limit_0': -10.0,
        'mech_alpha': 0.05,
        'mech_kinetic': 0.08,
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
        'audio_sample_rate': 44100,
        'audio_mode': 'sine',
        'audio_tone_path': None,
    }




    # 静态默认数据（用于文件重建或初始填充）
    STATIC_DEFAULT_STRING_DATA = _generate_full_static_string_data()

    def __init__(self, config_dir: str):
        self.config_path = os.path.join(config_dir, self.CONFIG_FILE_NAME)

    # def load_config(self) -> Dict[str, Any]:
    #     """从文件加载配置，如果文件不存在或加载失败，则返回默认配置。"""
    #     if not os.path.exists(self.config_path):
    #         print(f"配置文件未找到，使用默认配置: {self.config_path}")
    #         return self.DEFAULT_CONFIG.copy()

    #     try:
    #         with open(self.config_path, 'r', encoding='utf-8') as f:
    #             config = json.load(f)

    #         merged_config = self.DEFAULT_CONFIG.copy()
    #         merged_config.update(config)
    #         print(f"配置加载成功: {self.config_path}")
    #         return merged_config

    #     except Exception as e:
    #         print(f"加载配置文件失败 ({e})，使用默认配置。")
    #         return self.DEFAULT_CONFIG.copy()
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
