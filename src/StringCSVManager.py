import csv
import os
from typing import List, Dict, Any, Optional
import numpy as np

# 默认数据文件位于项目根目录下的 data/strings_default.csv
DATA_DIR = 'data'
DEFAULT_FILE_NAME = 'strings_default.csv'

from ConfigManager import ConfigManager

# 现在这个功能移交给ConfigManager
# # --- 完整的 88 键静态默认数据 ---
# def _generate_full_static_data():
#     """生成完整的 88 键 L 和 μ 静态数据"""
#     data = []

#     # MIDI 编号范围：A0 (21) 到 C8 (108)
#     start_midi = 21
#     end_midi = 108

#     # 模拟长度和密度梯度 (使用对数或线性平滑模拟真实钢琴的渐变)
#     # 长度从 1.5m 线性递减到 0.008m
#     lengths = np.linspace(1.5, 0.008, end_midi - start_midi + 1)
#     # 密度从 0.015 kg/m 模拟对数递减到 0.000004 kg/m
#     densities = np.logspace(np.log10(0.015), np.log10(0.000004), end_midi - start_midi + 1)

#     # 标准升号音名表 (从 A0 开始)
#     note_names_sharp = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]

#     for i, midi in enumerate(range(start_midi, end_midi + 1)):
#         key_id = midi - start_midi
#         octave = (midi // 12) - 1 # 得到八度数
#         if midi == 21: octave = 0 # 修正 A0 的八度
#         if midi == 22: octave = 0 # 修正 A#0 的八度
#         if midi == 23: octave = 0 # 修正 B0 的八度
#         if midi == 108: octave = 8 # 修正 C8 的八度

#         note_base = note_names_sharp[(midi - 21) % 12]
#         note_name = f"{note_base}{octave}"

#         data.append({
#             'key_id': key_id,
#             'note_name': note_name.replace('A#00', 'A#0').replace('A00', 'A0').replace('B00', 'B0'), # 修正 A0/A#0/B0 的八度显示
#             'length': float(f"{lengths[i]:.4f}"),
#             'density': float(f"{densities[i]:.8f}")
#         })

#     return data

# STATIC_DEFAULT_STRING_DATA = _generate_full_static_data()
# ----------------------------------------------------


class StringCSVManager:
    """
    琴弦参数（长度 L 和线密度 μ）的 CSV 文件管理类。
    用于本地零配置部署。
    先不配置数据库，那个还要账号，有点麻烦
    """
    def __init__(self, file_path: Optional[str] = None):
        self.default_file_path = self._resolve_default_path()
        self.file_path = file_path or self.default_file_path
        self._initialize_file()

    def _resolve_default_path(self) -> str:
        """解析默认的项目根目录下的 data/strings.csv 路径"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        data_dir = os.path.join(project_root, DATA_DIR)

        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)

        return os.path.join(data_dir, DEFAULT_FILE_NAME)

    def get_connected_path(self) -> str:
            """返回当前连接的文件路径 (绝对路径)"""
            return self.file_path

    # def _initialize_file(self):
    #     """如果文件不存在，则创建并写入 CSV 头"""
    #     if not os.path.exists(self.file_path):
    #         try:
    #             with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
    #                 writer = csv.writer(f)
    #                 # key_id: 0-87; length: L (m); density: μ (kg/m)
    #                 writer.writerow(['key_id', 'note_name', 'length', 'density'])
    #             print(f"初始化 CSV 文件成功: {self.file_path}")
    #             # TODO: 可以在这里添加填充 88 键默认数据的逻辑
    #         except Exception as e:
    #             print(f"初始化 CSV 文件失败: {e}")
    def _initialize_file(self):
        """如果文件不存在，则创建文件头，并填充 88 键默认数据"""
        if not os.path.exists(self.file_path):
            try:
                # 1. 写入文件头
                with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['key_id', 'note_name', 'length', 'density']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    # 2. 写入默认数据
                    # writer.writerows(STATIC_DEFAULT_STRING_DATA)
                    writer.writerows(ConfigManager.STATIC_DEFAULT_STRING_DATA)

                print(f"初始化 CSV 文件成功: {self.file_path}")

            except Exception as e:
                print(f"初始化 CSV 文件失败: {e}")

    def get_string_parameters(self) -> List[Dict[str, Any]]:
        """从 CSV 文件中读取所有琴弦参数"""
        if not os.path.exists(self.file_path):
            return []

        data = []
        try:
            with open(self.file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 确保数据类型转换
                    row['key_id'] = int(row['key_id'])
                    row['length'] = float(row['length'])
                    row['density'] = float(row['density'])
                    data.append(row)
        except Exception as e:
            print(f"读取 CSV 文件失败: {e}")
        return data

    def get_string_parameters_by_id(self, key_id: int) -> Optional[Dict[str, Any]]:
        """
        从 CSV 文件中加载所有琴弦参数，并按 key_id 查找单个琴弦的数据。

        :param key_id: 钢琴键的 ID (0 到 87)
        :return: 包含 length 和 density 的字典，如果未找到则返回 None。
        """
        # 1. 从 CSV 文件加载所有数据
        all_params = self.get_string_parameters()

        # 2. 遍历查找匹配的 key_id
        for param in all_params:
            if param.get('key_id') == key_id:
                return param

        return None

    def update_string_parameters(self, params: List[Dict[str, Any]]) -> bool:
        """将所有琴弦参数写入 CSV 文件 (覆盖模式)"""
        try:
            # 始终按 key_id 排序后写入，确保文件有序
            params.sort(key=lambda x: x['key_id'])

            with open(self.file_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['key_id', 'note_name', 'length', 'density']
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                writer.writeheader()
                writer.writerows(params)
            return True
        except Exception as e:
            print(f"写入 CSV 文件失败: {e}")
            return False



