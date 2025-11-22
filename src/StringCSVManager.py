import csv
import os
from typing import List, Dict, Any, Optional
import numpy as np
import sys,os


# 修改：添加打包环境检测函数
def get_app_data_dir():
    """获取应用数据目录，适配打包环境"""
    if getattr(sys, 'frozen', False):
        # 打包环境
        if sys.platform == "win32":
            base_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "PianoTuning")
        elif sys.platform == "darwin":
            base_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "PianoTuning")
        else:
            base_dir = os.path.join(os.path.expanduser("~"), ".pianotuning")

        # 创建目录
        os.makedirs(base_dir, exist_ok=True)
        return base_dir
    else:
        # 开发环境使用当前目录
        return os.path.dirname(os.path.abspath(__file__))




# 默认数据文件位于项目根目录下的 data/strings_default.csv
DATA_DIR = 'data'
DEFAULT_FILE_NAME = 'strings_default.csv'

from ConfigManager import ConfigManager



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

    # 别删，这个是旧版，不打包时用的
    # def _resolve_default_path(self) -> str:
    #     """解析默认的项目根目录下的 data/strings.csv 路径"""
    #     current_dir = os.path.dirname(os.path.abspath(__file__))
    #     project_root = os.path.dirname(current_dir)
    #     data_dir = os.path.join(project_root, DATA_DIR)

    #     if not os.path.exists(data_dir):
    #         os.makedirs(data_dir, exist_ok=True)

    #     return os.path.join(data_dir, DEFAULT_FILE_NAME)
    def _resolve_default_path(self) -> str:
        """解析默认路径 - 适配打包环境"""
        # 修改：使用统一的应用程序数据目录
        app_data_dir = get_app_data_dir()
        data_dir = os.path.join(app_data_dir, DATA_DIR)

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



