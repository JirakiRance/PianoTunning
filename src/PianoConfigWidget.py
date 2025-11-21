# This Python file uses the following encoding: utf-8
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit,
                              QPushButton, QGroupBox, QHBoxLayout, QLabel,
                              QMessageBox, QDoubleSpinBox, QSizePolicy,QGridLayout,
                              QFileDialog)
from PySide6.QtCore import Qt, Signal
from typing import Dict, Any,Optional,List
import os
import csv
import sys
import subprocess # 用来打开excel

# 导入数据管理类(csv，先不做mysql)
try:
    from StringCSVManager import StringCSVManager
    DB_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"导入 StringCSVManager 失败: {e}")
    DB_MANAGER_AVAILABLE = False


class PianoConfigWidget(QWidget):
    """钢琴物理参数配置界面"""
    config_saved = Signal(dict) # 信号：当配置参数被保存时发出
    db_config_updated = Signal(str) # 信号：数据库文件路径已更改
    request_close = Signal(bool) # 信号：请求退出 (用于拦截父级对话框的关闭)

    def __init__(self, current_params: Dict[str, Any],db_manager: Optional['StringCSVManager'], parent=None):
        """
        :param current_params: 包含当前所有力学参数的字典。
        """
        super().__init__(parent)
        self.setWindowTitle("钢琴物理参数配置")
        self.current_params = current_params
        self.db_manager = db_manager # 接收 CSV 管理器实例
        self._setup_ui()
        self._update_db_display() # 初始化文件路径显示

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # 1. 核心参数组 (General Physics Parameters)
        general_group = QGroupBox("核心物理参数 (全局)")
        form_layout = QFormLayout(general_group)

        # 参数列表: I, r, k (劲度系数)

        # a. 弦轴转动惯量 I (kg·m²)
        self.input_I = self._create_double_spin_box(self.current_params.get('mech_I', 0.0001), 0.0, 1000.0, 5)
        form_layout.addRow(QLabel("转动惯量 I (kg·m²):"), self.input_I)

        # b. 弦轴半径 r (m)
        self.input_r = self._create_double_spin_box(self.current_params.get('mech_r', 0.005), 0.001, 0.5, 4)
        form_layout.addRow(QLabel("弦轴半径 r (m):"), self.input_r)

        # c. 弦劲度系数 k (N/m) (用于计算张力变化)
        self.input_k = self._create_double_spin_box(self.current_params.get('mech_k', 500000.0), 1.0, 100000000.0, 0)
        form_layout.addRow(QLabel("弦劲度系数 k (N/m):"), self.input_k)


        # d. 许用应力 \sigma_valid (MGa) 计算弦断
        self.input_sigma_valid = self._create_double_spin_box(self.current_params.get('mech_Sigma_valid', 210000), 0.0,100000000, 5)
        form_layout.addRow(QLabel("琴弦许用应力 [σ] (MPa):"), self.input_sigma_valid)

        main_layout.addWidget(general_group)

        # 2. 琴弦数据库入口 (L 和 μ)
        database_group = QGroupBox("琴弦参数文件 (L&μ)")
        db_layout = QVBoxLayout(database_group)

        # # 占位符：用于未来加载/编辑数据库
        # self.btn_open_db = QPushButton("📂 打开琴弦数据库 (L 和 μ)")
        # db_layout.addWidget(self.btn_open_db)
        # db_layout.addWidget(QLabel("注：琴弦长度 L 和线密度 μ 需针对每根琴弦配置，目前数据库功能待实现。"))

        # a. 数据库文件路径显示 (绝对路径)
        path_layout = QGridLayout()
        self.label_db_path_static = QLabel("当前数据文件：")
        self.label_db_path = QLineEdit("未指定") # 使用 QLineEdit 显示路径
        self.label_db_path.setReadOnly(True)

        # # 按钮：更改文件 (打开文件对话框)
        # self.btn_change_db = QPushButton("📂 更改文件/创建新文件")
        # # 按钮：打开编辑器 (用于编辑 L 和 μ 的表格)
        # self.btn_open_db = QPushButton("📝 编辑琴弦参数 (L 和 μ)")

        # path_layout.addWidget(self.label_db_path_static, 0, 0)
        # path_layout.addWidget(self.label_db_path, 0, 1)
        # path_layout.addWidget(self.btn_change_db, 1, 0)
        # path_layout.addWidget(self.btn_open_db, 1, 1)

        # 按钮容器
        btn_container = QVBoxLayout()
        self.btn_new_file = QPushButton("🆕 新建参数文件")
        self.btn_select_file = QPushButton("📁 选择现有文件")
        self.btn_edit_file = QPushButton("📝 修改当前参数") # 取代旧的 btn_open_db

        btn_container.addWidget(self.btn_new_file)
        btn_container.addWidget(self.btn_select_file)

        path_layout.addWidget(self.label_db_path_static, 0, 0)
        path_layout.addWidget(self.label_db_path, 0, 1)
        path_layout.addLayout(btn_container, 1, 0) # 按钮组放在左侧
        path_layout.addWidget(self.btn_edit_file, 1, 1) # 编辑按钮放在右侧

        db_layout.addLayout(path_layout)
        db_layout.addWidget(QLabel("注：文件存储了每根琴弦的长度 L 和线密度 μ。"))

        main_layout.addWidget(database_group)

        # 3. 控制按钮
        button_layout = QHBoxLayout()
        self.btn_save = QPushButton("保存配置")
        self.btn_cancel = QPushButton("取消")

        self.btn_save.clicked.connect(self._save_config)
        # self.btn_cancel.clicked.connect(self.close)
        # self.btn_cancel.clicked.connect(self._cancel_config) # 连接到取消方法
        # --- 修正：统一连接到退出请求方法 ---
        # self.btn_cancel.clicked.connect(self.request_close_action)
        self.btn_cancel.clicked.connect(self._cancel_and_exit)
        # self.btn_cancel.clicked.connect(self.close)
        # ----------------------------------------

        button_layout.addStretch(1)
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_cancel)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # --- 连接数据库按钮的槽函数 ---
        if DB_MANAGER_AVAILABLE:
            # self.btn_change_db.clicked.connect(self._open_file_dialog) # <-- 连接到文件选择
            # self.btn_open_db.clicked.connect(self._open_string_editor)
            self.btn_new_file.clicked.connect(self._create_new_file)
            self.btn_select_file.clicked.connect(self._select_existing_file)
            self.btn_edit_file.clicked.connect(self._open_string_editor)
        else:
            self.btn_change_db.setEnabled(False)
            self.btn_open_db.setEnabled(False)
        self._update_db_display()


    def _is_file_valid(self, file_path: str) -> bool:
        """
        校验 CSV 文件头是否包含所需的字段。
        我们跳过默认文件 (strings.csv) 的校验，方便测试。
        """
        if not os.path.exists(file_path):
            return False

        # 获取默认文件路径 (用于跳过校验)
        default_path = self.db_manager.default_file_path if self.db_manager else None

        # --- 校验豁免：如果是默认文件，则假定有效 (方便测试) ---
        # if file_path == default_path:
        #     return True
        # -----------------------------------------------------------

        # 必需字段列表
        required_fields = ['key_id', 'note_name', 'length', 'density']

        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                # 只读取第一行（文件头）
                reader = csv.reader(f)

                try:
                    header = next(reader)
                except StopIteration:
                    # 文件为空
                    return False

                # 移除可能存在的 BOM 字符并清理空格
                if header and header[0].startswith('\ufeff'):
                    header[0] = header[0].lstrip('\ufeff')

                header = [col.strip() for col in header]

                # --- 诊断输出 ---
                print("-" * 30)
                print(f"校验文件: {os.path.basename(file_path)}")
                print(f"期望字段: {required_fields}")
                print(f"实际读取: {header}")
                print("-" * 30)
                # -----------------

                # 检查所有必需字段是否都存在于文件头中
                return all(field in header for field in required_fields)
                # if all(field in header for field in required_fields):
                #      return self._is_data_valid(file_path, required_fields)
                # else:
                #      if len(header) == 1 and all(field in header[0] for field in required_fields):
                #          print("诊断: 可能是分隔符错误，文件头被读成一个长字符串。")
                #      return False
        except Exception as e:
            print(f"校验文件 {file_path} 失败: {e}")
            return False


    def _is_data_valid(self, file_path: str, required_fields: List[str]) -> bool:
        """
        校验 CSV 文件中的数据内容是否完整（无漏项）。
        假设文件头已经通过 _is_file_valid 校验。
        """
        try:
            # 使用 DictReader 逐行读取，方便按字段名检查
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                row_count = 0

                for row in reader:
                    row_count += 1

                    # 检查每一行中所有必需字段的值是否为空、None 或只含空格
                    for field in required_fields:
                        value = row.get(field)
                        if value is None or (isinstance(value, str) and value.strip() == ""):
                            print(f"数据校验失败: 第 {row_count + 1} 行，字段 '{field}' 缺失或为空。")
                            return False

                    # 额外校验：尝试进行类型转换，防止非数字字符
                    try:
                        int(row['key_id'])
                        float(row['length'])
                        float(row['density'])
                    except ValueError:
                        print(f"数据校验失败: 第 {row_count + 1} 行，'key_id', 'length', 或 'density' 包含无效的非数字字符。")
                        return False

                # 至少要有 88 个键的校验 (可选，但推荐)
                # if row_count < 88:
                #     print(f"数据校验警告: 文件只包含 {row_count} 条记录，标准钢琴应有 88 键。")
                #     # 这里不返回 False，仅作为警告，允许不完整的库使用
                # 88键校验
                REQUIRED_KEYS = 88
                if row_count < REQUIRED_KEYS:
                     print(f"数据校验失败: 文件只包含 {row_count} 条记录。标准钢琴需要 {REQUIRED_KEYS} 键数据。")
                     QMessageBox.critical(None, "校验失败",
                                          f"琴弦数据不完整: 仅发现 {row_count} 条记录，必须有 {REQUIRED_KEYS} 键数据才能保存。")
                     return False # 校验失败

            return True
        except Exception as e:
            print(f"数据内容读取失败: {e}")
            return False

    def _cancel_and_exit(self):
            """处理 '取消' 按钮点击。"""
            # 确保调用 reject()，这是模态对话框的标准退出方式
            parent_dialog = self.parent()
            if parent_dialog and isinstance(parent_dialog, QDialog):
                print("有父亲")
                parent_dialog.reject()
            else:
                self.close()


    def _switch_to_safe_file(self) -> bool:
        """尝试切换到有效的默认文件或重建，并返回成功状态"""

        # 1. 检查有效的默认文件
        if os.path.exists(self.db_manager.default_file_path) and self._is_file_valid(self.db_manager.default_file_path):
            self._set_active_file(self.db_manager.default_file_path, update_manager=True)
            return True

        # 2. 尝试重建
        elif self._rebuild_default_string_file():
            return True

        return False


    def _set_active_file(self, file_path: str, update_manager: bool = True):
        """设置当前活动的 CSV 文件，并更新 UI 和 Manager"""
        if update_manager and self.db_manager:
            self.db_manager.file_path = file_path
            self.db_manager._initialize_file() # 确保文件存在且有头

        self._update_db_display()
        self.db_config_updated.emit(file_path) # 通知 MainWindow


    def _create_new_file(self):
        """新建文件：让用户输入文件名，并创建文件"""
        if not self.db_manager: return

        # 默认起始路径为当前活动路径或默认路径
        initial_path = os.path.dirname(self.db_manager.file_path)
        default_name = "custom_strings.csv"

        # 弹出保存对话框让用户指定路径和名称 (SaveFileName)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "新建琴弦参数文件",
            os.path.join(initial_path, default_name),
            "CSV 文件 (*.csv)"
        )

        if file_path:
            # 1. 创建文件并初始化头部
            temp_manager = StringCSVManager(file_path)
            temp_manager._initialize_file()

            # 2. 校验创建是否成功
            if self._is_file_valid(file_path):
                QMessageBox.information(self, "新建成功", f"新参数文件已创建：\n{file_path}\n您可以开始编辑。")
            else:
                 QMessageBox.critical(self, "创建失败", "无法创建或校验新建文件，请检查权限。")

    def _select_existing_file(self):
        """选择文件：选择一个现有的 CSV 文件并更改当前选中的文件"""
        if not self.db_manager: return

        # 弹出打开文件对话框 (OpenFileNames)
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择琴弦参数文件",
            os.path.dirname(self.db_manager.file_path),
            "CSV 文件 (*.csv)"
        )

        if file_path:
            # 2. 设置为活动文件
            self._set_active_file(file_path, update_manager=True)
            QMessageBox.information(self, "文件已切换", f"当前使用的文件已切换为:\n{file_path}")

    # 更新文件路径显示
    def _update_db_display(self):
        """从 CSVManager 获取文件路径并显示"""

        if self.db_manager:
            current_path = self.db_manager.get_connected_path()
            file_exists = os.path.exists(current_path)
            # is_valid = self._is_file_valid(current_path) if file_exists else False

            self.label_db_path.setText(current_path)
            self.label_db_path.setToolTip(current_path)

            # 只有当文件存在且合法时，才允许修改参数
            # self.btn_edit_file.setEnabled(file_exists and is_valid)
            self.btn_edit_file.setEnabled(file_exists)

            # if file_exists and is_valid:
            if file_exists:
                 self.btn_edit_file.setText("📝 修改当前参数")
            # elif file_exists and not is_valid:
            #      self.btn_edit_file.setText("❌ 文件格式错误")
            else:
                 self.btn_edit_file.setText("❌ 文件不存在")
        else:
            self.label_db_path.setText("数据管理器不可用")
            self.btn_edit_file.setEnabled(False)

    def _open_string_editor(self):
        """
        打开琴弦参数编辑器（L 和 μ）的占位方法。
        实际表格编辑器将在未来迭代中实现。
        """    

        if not self.db_manager:
            QMessageBox.critical(self, "错误", "CSV 管理器未初始化。")
            return
        # --- 校验：文件是否存在 ---
        current_path = self.db_manager.get_connected_path()
        if not os.path.exists(current_path):
            QMessageBox.warning(self, "文件不存在", "当前数据文件不存在，请先 '新建' 或 '选择现有文件'。")
            return
        try:
            # 启动外部程序打开文件
            if sys.platform == "win32":
                # Windows 使用 os.startfile
                os.startfile(current_path)
            elif sys.platform == "darwin":
                # macOS 使用 open
                subprocess.call(['open', current_path])
            else:
                # Linux/Unix-like 系统使用 xdg-open
                subprocess.call(['xdg-open', current_path])
            # 3. 给出提示
            QMessageBox.information(self, "已打开外部编辑器",
                                    f"文件已在系统默认程序中打开：\n{os.path.basename(current_path)}\n"
                                    f"请在外部修改并保存文件。修改后无需重启软件即可生效，但请务必在保存参数配置时确保数据完整性！")
        except Exception as e:
            QMessageBox.critical(self, "打开文件失败",
                                 f"无法使用系统默认程序打开文件。请手动打开以下路径：\n{current_path}\n错误信息: {e}")




    # 文件修改方法：打开文件选择对话框
    def _open_file_dialog(self):
        """打开文件对话框，选择或创建 CSV 文件"""
        if not self.db_manager: return

        # 使用 QFileDialog.getSaveFileName 既可以指定路径，又可以创建不存在的文件
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择琴弦参数 CSV 文件",
            self.db_manager.file_path, # 默认路径
            "CSV 文件 (*.csv);;所有文件 (*)"
        )

        if file_path:
            self.db_manager.file_path = file_path # 更新管理器中的路径
            self.db_manager._initialize_file()   # 尝试初始化文件 (创建头或确保存在)

            self._update_db_display() # 更新 UI 显示

            # 发出信号，通知 MainWindow 文件路径已更改
            self.db_config_updated.emit(file_path)

            QMessageBox.information(self, "文件已设置", f"数据文件已更改为:\n{file_path}")


    def _create_double_spin_box(self, value, minimum, maximum, decimals=3):
        """创建 QDoubleSpinBox 的辅助函数"""
        spinbox = QDoubleSpinBox()
        spinbox.setRange(minimum, maximum)
        spinbox.setDecimals(decimals)
        spinbox.setValue(value)
        spinbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        return spinbox

    def _save_config(self):
        """收集参数，发出信号并关闭窗口"""

        # .强制校验当前琴弦数据文件
        current_path = self.db_manager.get_connected_path()
        required_fields = ['key_id', 'note_name', 'length', 'density']

        # 1. 校验文件头
        if not self._is_file_valid(current_path):
            QMessageBox.critical(self, "保存失败", "琴弦参数文件头格式错误，缺少 'key_id', 'length' 等关键字段！")
            return

        # 2. 校验数据内容和数量 (文件头通过后，才执行)
        if not self._is_data_valid(current_path, required_fields):
            # _is_data_valid 内部会弹出具体的错误信息（如缺失 88 键），此处只需阻止保存。
            return
        # ------------------------------------------

        new_params = {
            'mech_I': self.input_I.value(),
            'mech_r': self.input_r.value(),
            'mech_k': self.input_k.value(),
            'mech_Sigma_valid': self.input_sigma_valid.value(),
            'db_file_path': current_path
        }

        # 发出信号，将新参数字典传递给 MainWindow
        self.config_saved.emit(new_params)
        print(f"PianoWidget发出_save_config\n{new_params}")
        if self.parent():
            self.parent().accept() # 关闭对话框，通知 MainWindow 保存成功

    def _cancel_config(self):
        """取消操作，关闭父级对话框"""
        if self.parent():
             self.parent().reject() # 使用 reject() 告诉父级 Dialog 数据未保存


    # --- 关闭请求方法 ---
    def request_close_action(self):
        """当用户尝试关闭窗口时调用的方法"""
        current_path = self.db_manager.get_connected_path()
        # 1. 执行最终校验
        required_fields = ['key_id', 'note_name', 'length', 'density']
        if self._is_file_valid(current_path) and self._is_data_valid(current_path,required_fields):
            # 校验成功，允许关闭
            self.request_close.emit(True)
            return
        # 2. 校验失败：执行静默恢复流程
        # 尝试恢复到默认路径或重建
        if os.path.exists(self.db_manager.default_file_path) and self._is_file_valid(self.db_manager.default_file_path):
            # 找到有效的默认文件，静默切换过去
            self._set_active_file(self.db_manager.default_file_path, update_manager=True)
            QMessageBox.warning(self, "数据恢复", "当前配置的数据文件无效，已切换回默认安全文件。")
            self.request_close.emit(True) # 允许关闭
            return
        else:
            # 默认文件无效或不存在，尝试重建
            if self._rebuild_default_string_file():
                QMessageBox.information(self, "数据恢复", "当前数据文件无效，已使用静态数据创建新的默认文件。")
                # _rebuild_default_string_file 已经将活动文件切换到默认路径
                self.request_close.emit(True) # 允许关闭
                return
            else:
                # 无法恢复，拒绝关闭并给出明确提示
                QMessageBox.critical(self, "致命错误", "当前文件和默认文件均不可用，且无法重建！请手动修复文件。")
                self.request_close.emit(False) # 拒绝关闭

    # --- 重建文件逻辑（依赖 StringCSVManager 的 update_string_parameters） ---
    def _rebuild_default_string_file(self):
        """使用内部静态数据重建默认的 strings.csv 文件"""
        try:
         # 假设 STATIC_DEFAULT_STRING_DATA 在 StringCSVManager.py 中被导入或定义
         from StringCSVManager import STATIC_DEFAULT_STRING_DATA

         # 确保重建到默认路径
         self.db_manager.file_path = self.db_manager.default_file_path

         success = self.db_manager.update_string_parameters(STATIC_DEFAULT_STRING_DATA)

         if success:
             QMessageBox.information(self, "重建成功", "已使用静态数据成功重建文件。")
             return True
         else:
             QMessageBox.critical(self, "重建失败", "写入默认文件失败。")
             return False

        except Exception as e:
         QMessageBox.critical(self, "致命错误", f"重建默认文件时发生致命错误: {e}")
         return False






