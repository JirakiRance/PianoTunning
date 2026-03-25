# 🎹 钢琴调律辅助系统 — 软件使用说明

版本：v1.0
 适用对象：普通用户、调律爱好者、音乐学院学生、演奏者

您可以点击下方链接查看视频教程

[video](https://www.bilibili.com/video/BV17Z27B8EjL/)

------

# 用户操作说明

------

## 1. 软件界面总览

软件界面分为 **三大核心区域**，对应调律实际流程：

------

### **① 左侧：状态与摘要面板（Status Card）**

用于实时显示当前系统状态：

- 当前输入方式（实时 / 文件）
- 当前音频检测算法
- 实时音高检测结果
- 操作提示（如 “正在分析…”）

------

### **② 中间：可视化与钢琴键盘**

包括：

- **频谱波图 SpectrumWidget**（显示实时频谱）
- **88 键钢琴键盘可视化**
- **目标音高选择框（下拉菜单）**

用户可以：

- 直接点击钢琴键选择目标音
- 或使用下拉框选择目标音高

------

### **③ 右侧：调律力学调节面板**

包括：

- 扇形音分指示盘
- 调律参数显示区
- **鼠标速度控制板（核心操作区）**
- 施力模式切换
- 一键修复（校准）

这是整个软件的调律操作区域。

------

## 2. 快速开始

1. **启动软件**
2. 顶部选择输入模式：
   - **实时模式**（使用麦克风调律）
   - **文件分析模式**（对录音文件进行分析）
3. 在钢琴键或下拉菜单选择目标音高
4. 开始调律：
   - 弹奏目标琴键（或播放录音）
   - 观察右侧音分指针
   - 用鼠标速度控制板进行调节
5. 当音分落入设定阈值（默认 ±1 cents）
   → 软件自动弹窗提示“调律完成”

------

## 3. 实时分析模式

实时模式是软件最核心的功能。

#### 🎤 工作流程

1. 软件通过麦克风实时采集钢琴音频
2. 自动估计基频（Fundamental）
3. 更新：
   - 当前频率
   - 音分偏差
   - 置信度
   - 频谱波形
4. 右侧力学引擎同步模拟弦轴的转动效果

------

## 操作步骤

1. 勾选 **实时分析模式**
2. 用手轻敲目标琴键
3. 在右侧拖动鼠标调节弦轴
4. 观察音分表针归零

当满足：

$$
 |\text{cents}| \le \text{threshold}
$$

系统自动提示调好。

------

## 4. 文件分析模式

文件模式用于分析录音文件的调律质量。

------

### 使用方法

1. 点击 **选择文件夹**（批量载入录音）
2. 在文件列表选择一个文件
3. 点击 **开始分析**
4. 软件执行：
   - 实时进度条
   - 全文件波形展示
   - 平均音分偏差统计
   - 置信度评估
5. 右侧调节面板同步更新分析结果（但被锁定，不能操作）

------

### ⚠ 文件分析期间自动锁定操作：

- 右侧力学面板
- 钢琴键盘
- 目标音下拉菜单

避免用户误触导致系统计算紊乱。

------

## 5. 右侧力学调节面板

右侧区域模拟真实钢琴弦轴的力学行为。

------

### **5.1 扇形音分指示盘**

- 指针偏左 → 偏低
- 指针偏右 → 偏高
- 对准中心 → 调准

表盘范围可在设置菜单调整（±100、±50 等）。

------

### **5.2 参数显示区**

实时显示：

- 当前频率
- 目标频率
- 音分偏差
- 弦张力
- 螺丝角度
- 输入速度
- 实际施加扭矩
- 当前 k_d（驱动增益）

------

### **5.3 施力模式**

#### **模式 1：速度映射模式（默认）**

鼠标垂直速度 → 扭矩大小：

$$
 \tau_{\text{drive}} = k_d \cdot v_{\text{user}}
$$

特点：

- 鼠标快 → 扭矩大
- 鼠标慢 → 微调
- 真实调律手感

------

#### **模式 2：预定义力模式**

鼠标只决定方向，力矩恒定：

$$
 |\tau_{\text{drive}}| = \tau_{\text{preset}}
$$

特点：

- 力大小不随鼠标速度变化
- 更容易控制
- 适合初学者

------

### **5.4 一键修复（校准）**

自动计算目标音对应的螺丝角度 θ：

- 若角度过小 → 自动提醒“松弦”
- 若越界 → 自动修正
- 可瞬间将琴弦调到目标位置附近

比人工微调更高效。

------

## 6. 鼠标速度控制板

这是调律操作的核心输入组件。

------

### 特点

- 左键按住 → 开始施力
- 松开 → 力自动衰减到 0
- 上推 = 上紧
- 下拉 = 放松
- 内置防抖、死区、平滑与惯性

------

### 用户可调参数

| 参数        | 说明                           |
| ----------- | ------------------------------ |
| `deadzone`  | 鼠标小幅抖动不计入（避免乱动） |
| `alpha`     | 平滑系数（越小越稳）           |
| `scale`     | 像素 → 速度映射常数            |
| `decay_tau` | 松手后回零的时间常数           |

------

## 7. 调律完成判定系统

软件会自动判断是否达到设定精度：

公式：

$$
 |\text{cents}| \le \text{threshold}
$$

默认 threshold = 1.0 cents。

当满足条件时：

- 自动停止施力
- 自动停止鼠标输入
- 弹窗提示“调律完成”
- 防止用户继续转动导致误差扩大

阈值可在设置菜单调整。

------

## 8. 设置菜单说明

顶部菜单 → **设置**

------

### **8.1 最大录音时长**

控制实时分析缓冲区大小。

------

### **8.2 音名系统**

可选：

- 升号（#）
- 降号（b）

界面所有音名实时切换。

------

### **8.3 音色设置**

可选择：

- 默认合成器（正弦波）
- 采样音色库
- SF2 音色库

当启用采样音色时，“使用合成器”会自动取消勾选。

------

### **8.4 音高检测算法**

例如：

- YIN
- Autocorrelation
- PYIN
- HPS

可自由切换。

------

### **8.5 鼠标控制平滑设置**

调整鼠标 → 力矩映射的手感。

------

### **8.6 调律判定阈值**

控制何时弹窗提示“调律完成”。

------

### **8.7 音分表盘范围**

可设：

- ±100
- ±50
- ±20 cents

影响指针灵敏度。

------

## 9. 帮助菜单与文档

顶部菜单 → **帮助**

包含：

- 软件使用说明（本文件）
- 力学系统说明（md/pdf）
- 音高检测算法说明（md/pdf）
- 项目报告（md / pdf 自动匹配）
- 开题报告（docx）
- 开题答辩 PPT
- 关于（软件信息）





---

---

---

---



# 开发者文档

本章节面向参与开发本项目的开发人员，讲解系统内部结构、模块依赖关系、UI 组件层级、核心逻辑流以及扩展方法。

------

## 1. MainWindow 模块开发者说明

*(对应文件：`mainwindow.py`)*

MainWindow 是整个应用的**根控制器（Root Controller）**，负责：

- 初始化所有核心系统
- 构建 UI 布局（左 / 中 / 右三大区域）
- 连接信号槽
- 实现文件分析 / 实时分析流程
- 提供统一状态管理
- 与力学系统、音频系统、钢琴系统交互
- 管理全局配置与 help 文档路径

开发者可以把 MainWindow 视为：
 ❗ **整个软件的数据流入口 + UI 控制中心**

------

### 1.1 结构总览

MainWindow 内部结构清晰，可分成 **六大逻辑区域**：

```
MainWindow
├── 0. 配置与参数加载（ConfigManager）
├── 1. 核心系统初始化
│     ├── Piano System
│     ├── AudioDetector（音高检测）
│     ├── AudioEngine（发声引擎）
│     ├── MechanicsEngine（力学引擎）
│
├── 2. UI 构建
│     ├── 左侧面板 create_left_panel()
│     ├── 中间面板 create_center_panel()
│     ├── 右侧面板 RightMechanicsPanel
│     ├── 菜单栏 setup_menu_bar()
│
├── 3. 信号槽绑定 connect_signals()
│
├── 4. 分析模式逻辑
│     ├── Realtime Analysis
│     ├── File Analysis
│
├── 5. 状态管理
│     ├── update_status()
│     ├── UserStatusCard 交互
│
└── 6. 设置项、弹窗、帮助文档
```

开发者只需理解上图，就能快速定位 MainWindow 内的任何功能代码入口。

------

### 1.2 配置系统（ConfigManager）

在构造函数开头加载：

```python
self.config_manager = ConfigManager(project_root)
self.config_data = self.config_manager.load_config()
```

所有全局参数（如摩擦、力矩、音名系统、调律阈值、采样率）都从 config.json 统一管理。

🟩 开发者应始终：
 **通过 config_data 读写配置，通过 ConfigManager 保存配置**
 不要散落写入 JSON 文件。

------

### 1.3 核心子系统初始化顺序

MainWindow 初始化顺序非常关键：

#### ① init_piano_system()

加载钢琴数据结构（88 键），初始化音名系统（升号/降号）
 → 其它系统都依赖钢琴系统的频率数据

#### ② init_audio_system()

初始化实时音高检测 AudioDetector
 连接 pitch_signal 自定义信号（线程安全）

#### ③ init_audio_engine()

负责发声（合成器、采样音色、SF2）

> MainWindow 内所有“播放音符”行为都通过 AudioEngine 完成。

#### ④ MechanicsEngine（右侧力学引擎交给 RightMechanicsPanel 控制）

MainWindow 只负责参数同步，不直接处理具体力学更新。

------

### 1.4 UI 构建（三个核心区域）

UI 采用水平三列布局：
 左（控制区）— 中（可视化区）— 右（力学系统）

#### 1.4.1 左侧：模式与状态

包含：

- 实时/文件分析切换
- 录音控制按钮
- 文件列表
- 系统状态卡（UserStatusCard）

所有状态提示、进度条都整合到 **status_card**。

#### 1.4.2 中间：频谱 + 钢琴键盘

包含：

- SpectrumWidget（实时可视化频谱）
- PianoWidget（88 键）
- note_selector（下拉选择目标键）

点击键盘和选择器都会触发：

```python
on_note_selector_changed()
```

并通知右侧力学引擎。

#### 1.4.3 右侧：力学系统面板

由 RightMechanicsPanel 控制，其内部独立管理：

- 力学物理参数
- 扭矩模型
- 摩擦模型
- 指针表盘
- 鼠标速度板
- 物理仿真引擎

MainWindow 使用三个接口与其通信：

```python
inform_right_target_key()
inform_right_current()
inform_right_params()
```

这三个函数是 UI→力学系统的唯一入口。

------

### 1.5 信号槽系统（Qt）

MainWindow 内部通过 connect_signals() 建立所有事件流，包括：

#### 🔹 模式切换

```python
self.mode_realtime.toggled.connect(self.on_mode_changed)
self.mode_file.toggled.connect(self.on_mode_changed)
```

#### 🔹 音频流程

- 开始录音
- 停止
- 实时回调

#### 🔹 文件分析

- 选择文件夹
- 选择音频文件
- 点击开始分析

#### 🔹 钢琴键事件

PianoWidget:

```python
self.piano_widget.key_clicked.connect(self.on_note_selector_changed)
```

------

### 1.6 实时分析逻辑

整体流程：

```
start_recording()
→ audio_detector.start_realtime_analysis(...)
→ 回调 realtime_pitch_callback
→ pitch_signal.pitch_detected
→ 进入主线程：on_pitch_detected_update_ui
→ 更新右侧力学面板 + 状态卡 + 频谱
```

**采用跨线程信号槽，保证 UI 安全更新。**

------

### 1.7 文件分析逻辑

单次分析流程：

```
on_start_file_analysis_clicked()
→ 锁定 UI（避免干扰）
→ audio_detector.analyse_audio_file(path)
→ 返回 MusicalAnalysisResult
→ 显示频谱/置信度/音分偏差
→ 恢复 UI
```

特别注意：

- 文件分析期间会禁用：
  - 键盘
  - note_selector
  - file_list_widget
  - 力学面板

防止用户手滑造成参数注入错误。

------

### 1.8 状态管理

统一用：

```python
self.update_status(text)
```

该函数会：

- 同时更新 DebugStatusWindow（隐藏）
- 更新状态卡 status_card
- 写入状态缓存

开发者调试时只需调用 update_status。

------

### 1.9 帮助文档系统

MainWindow 将所有文档存放于：

```
项目根目录 / help / 
```

菜单栏：

```python
帮助 → 软件使用说明
帮助 → 力学系统说明
帮助 → 音高检测算法说明
帮助 → 项目报告
帮助 → 开题报告
帮助 → 开题PPT
```

统一入口：

```python
open_help_doc(name)
```

会自动判断：

- 有同名 .md → 打开
- 否则打开同名 .pdf
- 否则报错

方便用户跨平台查看文档。

------

### 🔚 MainWindow 小结

MainWindow 主要负责：

- **构建 UI**
- **管理全局配置**
- **处理分析模式**
- **串联音频系统、钢琴系统、力学系统**
- **调度状态与可视化**

开发者扩展功能时，应遵守：

- 不直接修改 RightMechanicsPanel 或音频模块内部状态
- 所有 UI → 力学系统的请求使用 inform_right_* 接口
- 所有配置写入 config_data 并保存



------

## 2. 钢琴管理模块（Piano System）

钢琴管理模块由三个部分构成：

```
PianoGenerator —— 数据模型层（生成 88 键、频率、音名）
PianoWidget —— 绘图展示层（UI 展示键盘，可点击）
PianoConfigWidget —— 钢琴参数设置（如弦长、密度等物理参数）
```

它们一起构成软件中与“钢琴键”相关的全部逻辑。

------

### 2.1 PianoGenerator — 键盘数据模型

（对应文件：/PianoGenerator.py）

PianoGenerator 是 **所有钢琴键数据的来源**，任何与音名、频率、键位、颜色相关的逻辑都必须从这里获取。
 它是一个**纯数据层模型**，没有 UI，只做计算：

- 88 键的频率
- 键盘坐标
- 黑白键判断
- 升号/降号音名系统
- 基准音 A4 变化（随设置切换）
- 键盘查找（按 note/midi/frequency）
- 用于绘图的键宽、键高信息

#### 2.1.1 模块职责

PianoGenerator 的职责可总结为：

| 功能                                 | 说明                                     |
| ------------------------------------ | ---------------------------------------- |
| **生成 88 个 PianoKey 对象**         | 包含 note、freq、color、midi、坐标等信息 |
| **支持 Sharp / Flat 两种音名系统**   | 对应全部 MIDI 表覆盖                     |
| **根据 A4 频率实时重算所有键的频率** | 保证十二平均律一致                       |
| **键盘查找能力**                     | 通过 note / midi / frequency 查找键      |
| **用于鼠标点击的 hit-test**          | get_key_at_position(x,y)                 |
| **可用于声音播放测试**               | play_key_frequency()                     |

所有 MainWindow、PianoWidget、调律面板都依赖此模块。

------

#### 2.1.2 数据结构

每个按键由 PianoKey 描述：

```python
@dataclass
class PianoKey:
    key_id: int
    note_name: str
    frequency: float
    color: KeyColor
    midi_number: int
    position: Tuple[float, float]
    width: float
    height: float
    is_pressed: bool = False
```

其来源代码位于：

##### 说明：

- `note_name` 会根据 accidental_type 自动更新
- `frequency` 与 A4 基准频率绑定
- `position / width / height` 是绘图层使用的元数据
- `is_pressed` 可用于 UI 按下效果（目前由 PianoWidget 管理）

------

#### 2.1.3 关键方法与作用

##### 🚩 `_generate_piano_keys()`

生成全部 88 键，计算：

- 白键位置递增
- 黑键靠两白键之间（并按 key_width * 0.6 缩放）
- 频率按十二平均律公式计算

这里是键盘布局的核心。

##### 🚩 `_get_note_name()`

根据 accidental_type（sharp/flat）选择整张表：

- sharp 表（A#、C#…）
- flat 表（Bb、Db…）

由完整 MIDI → 音名对照表驱动，保证无逻辑误差。

##### 🚩 `set_base_frequency()`

用来响应 A4 变更（设置菜单 → “标准音 A4 频率”）。

此函数会立即重新计算所有键的频率。
 Realtime/文件分析模块都依赖此一致性。

##### 🚩 `find_closest_key(freq)`

用于实时分析 UI：
 当检测频率 ≈ 键频率附近时，系统显示哪一个键最接近。

------

#### 2.1.4 MainWindow 调用方式

MainWindow 永远不手动计算 note_name、频率，而是：

```python
key = piano_generator.get_key_by_note_name("A4")
freq = key.frequency
```

所有 UI 显示、调律基准都通过 PianoGenerator 统一管理。

------

### 2.2 PianoWidget — 88 键钢琴绘图组件

（对应文件：/PianoWidget.py）

PianoWidget 是 UI 层组件，负责：

- 绘制 88 键
- 高亮“目标键”
- 高亮“检测到的音名”
- 响应鼠标点击 → 触发 key_clicked 信号

它不处理任何物理逻辑，也不负责频率计算。
 其所有键数据来源均为 PianoGenerator。

------

#### 2.2.1 模块职责

| 功能                                 | 说明                        |
| ------------------------------------ | --------------------------- |
| 绘制白键、黑键                       | 自动适配 widget 宽高        |
| 绘制目标键高亮                       | 绿色                        |
| 绘制实时检测键高亮                   | 黄色                        |
| 支持鼠标点击                         | emit key_clicked(note_name) |
| 在 accidental_type/A4 改变后自动重绘 | set_piano_generator()       |

------

#### 2.2.2 UI 更新流程

绘制键盘时，PianoWidget 依赖：

```python
self.piano_generator.keys
```

高亮逻辑：

- `detected_note_name` → 黄色（优先级高）
- `target_note_name` → 绿色

##### 示例：

```python
self.piano_widget.set_target_note("A4")
self.piano_widget.set_detected_note("A#4")
```

UI 将自动刷新。

------

#### 2.2.3 点击事件

mousePressEvent：

```
点击黑键（优先） → 找到 note_name → emit(key_clicked)
点击白键 → emit(key_clicked)
```

MainWindow 使用此信号实现：

- 鼠标点击键盘 → 自动切换调律目标键
- 同步右侧力学面板

------

#### 2.2.4 动态更新 PianoGenerator

当用户切换：

- Sharp / Flat 升降号
- A4 基准频率

MainWindow 会执行：

```python
self.piano_widget.set_piano_generator(self.piano_generator)
```

触发：

- 重算键位区域
- 清除旧的高亮
- 强制重绘

保证 UI 与数据完全同步。

------

#### 2.2.5 适配布局

PianoWidget 在 resizeEvent 自动缩放键宽/键高：

```
白键宽度 = widget_width / 白键数量
黑键宽度 = 白键宽度 * 0.6
高度 = 整个 widget 高度
```

你无需手动调整。

------

### 2.3 PianoConfigWidget — 钢琴物理参数配置窗口

这是 MainWindow 中的一个 Dialog，用于设置：

- 弦长（L）
- 线密度（μ）
- 弦材料
- 张力公式参数

这些参数主要提供给 MechanicsEngine 使用。
 *(开发者可在下一章节 MechanicsEngine 中查阅)*

其结构与 FrictionConfigWidget 类似：

- QFormLayout 填写参数
- 点击保存 → emit 配置
- force MechanicsPanel 更新参数

------

### 🔚 钢琴管理模块总结

钢琴系统模块是整个应用的“音乐基础设施层”，实现：

- 88 键数据结构（频率、音名、坐标）
- 目标键 & 检测键的可视化映射
- 属于 UI 与物理引擎之间的桥梁

其内部没有音频检测或物理运算，完全专注于：

- **正确生成钢琴键**
- **提供 UI 可视化定位**
- **根据设置更新音名/频率**

------

## 3. 音频检测与音频生成系统（Audio System）

本章节介绍本软件最核心的音频处理部分，包括：

- **AudioDetector**：录音采集与音高检测流程（实时/文件）
- **PitchDetector**：多算法音高检测模块（PYIN / YIN / HPS / Autocorr / 自适应）
- **AudioEngine**：负责声音播放（合成器、采样库、SF2）
- **ToneLibraryDialog**：音色库加载界面（供用户选择采样包或 SoundFont）

这四个模块共同构成整个软件的声音输入与声音输出系统。

------

### 3.1 AudioDetector 模块（录音采集 & 检测调度）

对应文件：`AudioDetector.py`

AudioDetector 负责：

- 录音数据的实时采集
- 缓冲管理
- 调用 PitchDetector 执行音高检测
- 发射 Qt 信号传回 UI
- 执行文件音频的分析流程
- 处理进度条回调

可以认为：
 🟩 **AudioDetector = 音频输入管线（Input Pipeline）**

------

#### 3.1.1 AudioDetector 内部结构

```
AudioDetector
├── 录音系统：
│     ├── sounddevice.Stream
│     ├── 回调 audio_callback
│
├── 音高检测系统：
│     ├── PitchDetector 实例
│     ├── self.detect_pitch()
│
├── 模式：
│     ├── 实时模式（realtime）
│     ├── 文件分析模式（file-analysis）
│
└── 对外信号：
      ├── pitch_signal (发送频率 + 置信度)
      ├── progress_callback
      └── error_callback
```

AudioDetector 是纯逻辑模块，不负责 UI。
 UI 与检测之间通过 Qt 信号槽通信。

------

#### 3.1.2 实时录音流程

实时检测流程如下：

```
sounddevice.InputStream
→ audio_callback(buffer)
→ accumulate audio into circular buffer
→ 每 hop_len 触发一次 detect_pitch()
→ PitchDetector.detect_xxx()
→ pitch_signal.emit()
→ MainWindow 更新 UI
```

##### **录音采用 sounddevice 异步回调形式**

优点：

- 无阻塞
- 可保持 30~60 FPS 的刷新率
- 缓冲安全（不会阻塞主线程）

这是实时音高检测必须的要求。

------

#### 3.1.3 detect_pitch 调用 PitchDetector

AudioDetector 不直接执行算法，而是：

```python
result = self.pitch_detector.detect_adaptive(audio_buffer, target_freq)
```

结果结构：

```python
PitchDetectionResult(frequency, confidence, method_used)
```

并通过 Qt 信号发送给 MainWindow：

```python
self.pitch_signal.pitch_detected.emit(freq, confidence, method)
```

------

#### 3.1.4 文件分析流程

文件分析采用同步流程：

```
analyse_audio_file()
→ 加载整段音频 librosa.load
→ 分帧并循环检测
→ 统计平均音分偏差 / 平均置信度
→ 返回分析结果 MusicalAnalysisResult
```

并带有进度更新回调：

```python
self.progress_callback(percentage)
```

MainWindow 在文件模式下会：

- 禁用右侧力学系统
- 禁用钢琴键盘与 note_selector
- 禁用文件列表
- 解锁在 finally 中执行

确保文件分析不被用户误操作干扰。

------

### 3.2 PitchDetector 模块（音高检测核心）

对应文件：
 **`PitchDetector.py`**

PitchDetector 是整个软件最复杂的算法模块，包含：

- PYIN 基础版
- PYIN 增强版
- YIN
- HPS（Harmonic Product Spectrum）
- Autocorrelation（自相关）
- Adaptive（综合自适应）

可以认为：
 🟦 **PitchDetector = 音高检测算法集合（Algorithm Bank）**

------

#### 3.2.1 主要结构

```
PitchDetector
├── detect_pyin_basic()
├── detect_pyin_enhanced()
├── detect_yin()
├── detect_hps()
├── detect_autocorr()
└── detect_adaptive()   ← 默认优先使用
```

每种算法都有：

- 输入：音频帧
- 输出：PitchDetectionResult

##### **统一输出结构：**

```python
@dataclass
class PitchDetectionResult:
    frequency: float
    confidence: float
    method_used: str
```

------

#### 3.2.2 PYIN 基础 / 增强版

基于 librosa.pyin。
 基础版主要用于稳定条件下，增强版加入能量判断、去噪策略。

------

#### 3.2.3 YIN 算法

特征：

- 强鲁棒性
- 速度较慢
- 对弱信号敏感

本项目中加入：

- RMS 能量筛选
- IQR 异常值剔除
- Trimmed mean 平滑

用于解决：

- 琴声衰减尾部乱跳
- 环境噪声导致的错误峰值

------

#### 3.2.4 HPS 谐波乘积谱

用于处理：

- 低噪声高采样率信号
- 频谱更清晰的文件分析

算法流程：

```
FFT
→ 移除 DC
→ N 倍频率下采样
→ 乘积得到峰值
→ 二次插值提高精度
```

------

#### 3.2.5 Autocorrelation 自相关算法

适合：

- 容易失真或存在削波的音频
- 人工录音文件

内部加入：

- 中心削波 clipped
- 峰值显著性检测
- 抛物线插值

------

#### 3.2.6 Adaptive 自适应算法

逻辑：

```
依次尝试：
    PYIN_ENHANCED
    YIN
    HPS
    Autocorr
选择置信度最高的结果
```

这是依赖多算法的组合模型，大幅提升：

- 抗噪性
- 弱信号检测
- 对不同录音条件的适配性

MainWindow 调用 AudioDetector 默认使用该算法。

------

### 3.3 AudioEngine 模块（合成器/采样/SF2 发声）

对应文件：`AudioEngine.py`

AudioEngine 是输出声音的系统，用于：

- 演示目标音高
- 播放参考音
- 或调律中的反馈音效

可以看作：
 🟩 **AudioEngine = Output Pipeline（输出音频流）**

它内部支持：

- 正弦波合成器（内建）
- 采样音色文件（WAV/FLAC/OGG…）
- SF2 SoundFont 播放器（依托 fluidsynth）

------

#### 3.3.1 模块结构

```
AudioEngine
├── Mode：["sine", "sample", "sf2"]
├── 正弦波合成器（fallback）
├── SampleLoader（采样包加载器）
├── SF2Engine（SoundFont 播放器）
└── play_note()
```

MainWindow 在切换音色来源时会：

- 打开 ToneLibraryDialog
- 根据用户选择设置 engine.mode
- 设置采样率
- 重新加载音色

------

#### 3.3.2 正弦波合成器

用于：

- 没有加载音色库时
- 或作为 fallback

合成公式：

```python
sin(2π f t) * envelope(ADSR)
```

内部包含：

- Attack
- Decay
- Sustain
- Release

参数可调。

------

#### 3.3.3 采样音色包模式（Sample Pack）

用户指定一个文件夹，例如：

```
piano_samples/
    C4.wav
    C#4.wav
    D4.wav
    ...
```

AudioEngine 将：

- 扫描目录
- 构建映射 `note_name → sample array`
- 播放时回放对应的 wav 数据

采样率保持一致，由用户选择（ToneLibraryDialog 提供）。

------

#### 3.3.4 SF2 SoundFont 模式

使用 fluidsynth 播放 `.sf2` 文件。

特点：

- 播放质量高
- 占用小
- 发声平滑无顿挫
- 内置钢琴音色丰富

------

### 3.4 ToneLibraryDialog（音色库加载面板）

对应文件：
 **`ToneLibraryDialog.py`**

用户可选择：

- **采样音色文件夹（sample mode）**
- **SF2 文件（sf2 mode）**
- 采样率（22k ~ 96k）

##### 对外接口：

```python
get_selected_mode()
get_sample_folder()
get_sf2_file()
get_samplerate()
```

MainWindow 调用示例：

```python
dialog = ToneLibraryDialog(self)
if dialog.exec():
    mode = dialog.get_selected_mode()
    sr   = dialog.get_samplerate()
```

用于音色配置菜单。

------

#### 🔚 音频系统小结

音频系统由四个模块组成：

| 模块              | 作用                         | 备注              |
| ----------------- | ---------------------------- | ----------------- |
| AudioDetector     | 音频采集、调度检测、线程模型 | 实时/文件分析入口 |
| PitchDetector     | 多算法音高检测核心           | 算法复杂度最高    |
| AudioEngine       | 发声系统（sine/sample/sf2）  | 用于播放参考音    |
| ToneLibraryDialog | 采样包/SF2 配置界面          | 与用户交互        |



------

## **4. 力学系统（Mechanics System）**

力学系统是本项目的 **核心物理模拟模块**，用于模拟真实钢琴调律时的：

- 弦轴转动
- 摩擦（静摩擦 + 动摩擦）
- 扭矩施加（鼠标速度 / 预定义力）
- 弦张力变化
- 频率变化响应

在软件的架构中，它由 **“后端物理引擎 + 前端 UI 控制面板”** 两部分共同组成。

------

### **4.1 模块结构概览**

```
Force Input (鼠标速度板)
       ↓
RightMechanicsPanel --------------------------+
       |                                       |
       | 控制参数变化、更新 UI                 |
       ↓                                       |
MechanicsEngine  <------------------------------+
       | 物理仿真：扭矩 → 角度 → 张力 → 频率
       ↓
TuningDialWidget2（扇形音分表盘）
```

换句话说：

#### **RightMechanicsPanel = 控制层**

- 连接 UI 输入（鼠标速度）
- 执行施力模式
- 控制 k_d、τ_preset、摩擦参数等
- 将“目标键”与“实时状态”推送给表盘与 engine

#### **MechanicsEngine = 计算层**

- 所有物理数学逻辑都集中在这里
- 不涉及 UI，仅返回物理量

------

### **4.2 MechanicsEngine — 力学仿真核心**

📄 文件：`MechanicsEngine.py`
 来源：

MechanicsEngine 实现了完整的模拟弦轴微小位移时的力学行为。

------

#### **4.2.1 主要职责**

MechanicsEngine 负责：

- 处理用户输入的扭矩值
- 根据摩擦模型计算实际有效扭矩
- 更新弦轴角度 θ
- 计算对应的弦张力 T
- 最终计算频率 f

公式采用真实钢琴调律模型的简化版：

##### **弦张力与频率的关系**

$$
 f = \frac{1}{2L}\sqrt{\frac{T}{\mu}}
$$

##### **弦轴角度 → 张力变化**

模拟线性逼近：
$$
 \Delta T = k_\theta \cdot \Delta\theta
$$

------

#### **4.2.2 摩擦模型**

这是 MechanicsEngine 最关键部分。

本系统使用 **限幅摩擦模型**（你前面多次讨论过的最终版本）：

##### **静态区：静摩擦完全抵消扭矩**

若角速度几乎为 0：
$$
|\tau_{\text{input}}| \le \tau_{fric_limit}(\theta)
$$
则：
$$
 \tau_{\text{effective}} = 0
$$
即轴保持锁定。

------

##### **达到极限后 → 进入滑动摩擦**

滑动摩擦（动摩擦）模型使用：

$$
 \tau_{\text{fric}} = \tau_{\text{kinetic}} \cdot \text{sign}(\omega)
$$

但必须满足：

> **τ_kinetic 一定小于 τ_fric_limit，否则物理不连续。**

软件允许：
$$
\tau_{kinetic} = \gamma \cdot \tau_{fric_limit}
$$


$\gamma$由用户在 UI 改摩擦参数时隐含调整。

------

#### **4.2.3 扭矩更新流程**

每帧按照：

```
输入扭矩 τ_input
    ↓
静摩擦判定
    ↓
计算有效扭矩 τ_eff
    ↓
更新弦轴角度 θ
    ↓
更新弦张力 T
    ↓
更新频率 f
```

RightMechanicsPanel 定时调用 engine.update(dt)，dt 通常为 1/60 秒。

------

#### **4.2.4 一键校准模式**

RightMechanicsPanel 会调用：

```
engine.set_angle(theta_target)
```

该方法：

- 不经过摩擦模型
- 直接把模型送到稳定的 θ
- 用于瞬时恢复音高

并有安全检查：

- 角度过小 = 松弦 → 弹窗警告
- 角度越界 → 自动 clamp

------

### **4.3 RightMechanicsPanel — 力学 UI 控制层**

📄 文件：`RightMechanicsPanel.py`
 来源：

这是右侧力学区域的 UI 实现。

------

#### **4.3.1 组成结构**

```
RightMechanicsPanel
├── TuningDialWidget2（指针仪表盘）
├── 参数显示区（张力 / 角度 / 施力模式）
├── 鼠标速度控制板（MouseVelocityControl）
├── 施力模式切换（速度映射/预定义）
└── 一键校准按钮
```

------

#### **4.3.2 面板职责**

RightMechanicsPanel 负责：

- 显示当前频率 / 目标频率
- 显示音分偏差（通过 Dial）
- 处理鼠标输入速度
- 将输入映射为扭矩 τ_drive
- 调用 MechanicsEngine 更新物理状态
- 与 MainWindow 同步 UI 状态

它 **不保存物理数据**，仅把 UI 输入传给 engine。

------

#### **4.3.3 输入模式**

##### ❶ **速度映射模式（默认）**

$$
 \tau_{\text{drive}} = k_d \cdot v_{\text{user}}
$$

用于模拟真实调律手感。

##### ❷ **预定义力模式**

$$
 |\tau_{\text{drive}}| = \tau_{\text{preset}}
$$

鼠标只负责方向，适合新手。

------

#### **4.3.4 鼠标速度控制板**

它有 4 个可调 smoothing 参数：

- deadzone（死区）
- alpha（EMA 平滑）
- scale（像素 → 速度转换）
- decay_tau（松手后衰减）

RightMechanicsPanel 会监听：

```
mouse_velocity_changed → apply_velocity()
```

apply_velocity() 是最终扭矩更新入口。

------

### **4.4 TuningDialWidget — 扇形音分指针仪表盘**

📄 文件：`TuningDialWidget.py`
 来源：

这是调律系统最直观的 UI 元件。

------

#### **4.4.1 主要特性**

- 扇形仪表盘（180°）
- ±range_cents 范围可设置（默认 ±50）
- 连续平滑动画
- 自动缩放
- 显示音分偏差与频率

------

#### **4.4.2 输入接口**

```
set_frequencies(current, target)
set_cents(delta_cents)
set_range(cents)
```

RightMechanicsPanel 每次更新都会推送：

```
dial.set_frequencies(f_now, f_target)
```

如果需要快速刷新（文件分析），则用：

```
dial.set_cents()
```

------

### **🔚 力学系统总结**

- MechanicsEngine = **物理计算核心**
- RightMechanicsPanel = **用户操控 + 状态展示**
- TuningDialWidget2 = **频率偏差可视化**
- 鼠标速度控制板 = **唯一输入源**

整个流程如下：

```
鼠标 → RightMechanicsPanel → MechanicsEngine → Dial 表盘
```

所有输入都在 UI 层汇总
 所有物理行为都在 engine 中计算
 所有图形更新都在 Dial 中绘制

------

## **5. 频谱系统（Spectrum System）**

频谱系统负责展示实时分析与文件分析模式下的 **音频波形 + 频谱图**。  
虽然目前实现相对简洁，但内部结构清晰，可在未来轻松扩展为专业级可视化模块。

本系统主要由一个类实现：

📄 **SpectrumWidget.py**（对应文件：`SpectrumWidget.py`）

它由 MainWindow 的 `create_center_panel()` 引入，并实时接收音频分析数据。

------

### **5.1 模块结构概览**

```
AudioDetector → (音频帧) → SpectrumWidget
↓
paintEvent() 绘图
```

SpectrumWidget 完全属于前端显示层，不参与信号处理或音频分析。  
它只做三件事：

1. 接收音频帧 (`update_frame`)
2. 判断“实时模式”还是“文件整体模式”
3. 用 QPainter 绘制波形 + FFT 频谱

------

### **5.2 SpectrumWidget — 实时频谱和波形组件**

📄 文件：`SpectrumWidget.py`  
引用：:contentReference[oaicite:0]{index=0}

SpectrumWidget 是系统的音频可视化核心，包括：

- 波形显示（Time Domain）
- 频谱显示（Frequency Domain）
- 文件整体波形 + 频谱显示（文件分析模式）

------

### **5.2.1 主要职责**

SpectrumWidget 完成以下任务：

- 绘制波形（上半部分）
- 绘制频谱（下半部分）
- 自动缩放波形与频谱
- 自动适配窗口大小
- 对 FFT 结果进行 dB 归一化（增强低幅度细节）
- 根据不同输入模式调整显示方式（实时 / 文件）

其生命周期简单清晰：

```
update_frame() → self.audio_frame = 新数据 → update() → paintEvent()
```

------

### **5.2.2 API 说明**

#### **update_frame(audio_frame, is_full_file=False)**

将新的音频数据写入缓存，并触发重绘。  
`is_full_file=True` 用于文件分析模式，用来显示整个文件的波形。

#### **paintEvent()**

核心绘制逻辑：

```
分为上下两部分：
┌─────────── 上半部分：波形显示 ───────────┐
│ 归一化波形 / 中线 / 平滑贝塞尔路径绘制 │
└─────────────────────────────────────────┘
┌─────────── 下半部分：FFT 频谱 ──────────┐
│ windowing → rfft → dB scaling → 柱状图 │
└─────────────────────────────────────────┘
```

------

### **5.3 数据路径与调用关系**

SpectrumWidget 不会自己拉取音频数据，而是等待外部系统推送：

#### **实时模式：**

MainWindow → AudioDetector → MainWindow → SpectrumWidget

```
audio_detector.pitch_detected → on_pitch_detected_update_ui()
→ spectrum_widget.update_frame(audio_frame)
```

#### **文件分析模式：**

MainWindow → analyse_audio_file → result.full_audio_data → SpectrumWidget

```
spectrum_widget.update_frame(full_audio, is_full_file=True)
```

SpectrumWidget 自身不关心数据来源，只负责展示。

------

### **5.4 绘图细节说明**

#### **5.4.1 波形绘制**

- 数据归一化到 `[0, 1]` 区间
- 通过 `QPainterPath` 逐点绘制折线
- 中间画一条淡蓝色中线（用于视觉参考）

效果：

```
(波形起伏)
───────◣───◢───────
────────│────────── 中线
───────◥───◤───────
```

------

#### **5.4.2 FFT 频谱绘制**

流程：

```
windowed_signal = audio_frame * Hanning
fft = rfft(windowed_signal)
magnitude = |fft|
dB = 20 log10(magnitude)
归一化至 80dB 动态范围
绘制橙色柱状图
```

- 限制最大显示频率 5000 Hz（钢琴频率足够）
- 柱形图宽度自动适应窗口宽度
- 即使数据较短也不会崩溃（有异常处理）

------

### **5.5 设计理念**

SpectrumWidget 的设计目标：

| 目标   | 说明                                               |
| ------ | -------------------------------------------------- |
| 简洁   | 仅负责音频可视化，不参与信号计算                   |
| 灵活   | 可用于实时也可用于文件模式                         |
| 可扩展 | 后续可加入峰值标记、谐波标线、拖拽、缩放等         |
| 美观   | 采用统一颜色主题（深蓝背景 + 蓝色波形 + 橙色频谱） |

未来可以加入：

- Harmonic marker（谐波标记）
- 滚动波形
- 高级 FFT（log freq axis）
- 更精细的音高跟踪轨迹

------

### **5.6 与其他模块的关系**

SpectrumWidget 只依赖：

- numpy（FFT 计算）
- Qt 绘图

并从 MainWindow 接收数据。

它不依赖：

- MechanicsEngine（无物理信息）
- PianoGenerator（无钢琴信息）
- AudioEngine（不用发声）
- RightMechanicsPanel（不接受交互）

因此它是一个 **纯可视化独立组件**。

------

### 🔚 **频谱系统总结**

SpectrumWidget 是整个调律系统的可视化中枢，特点：

- 上半部分显示实时波形
- 下半部分显示实时频谱（带 dB 缩放）
- 支持完整文件波形渲染
- 没有业务逻辑，易于扩展
- 与音频检测系统解耦，数据由 MainWindow 推送

在开发者层面，它是一个简单却关键的可视化组件，对后续迭代（专业版频谱分析）有极高扩展性。

------

## 6. 配置系统（Configuration System）

配置系统是整个软件的 **参数中心（Parameter Hub）**，负责管理：

- 全局可调参数（力学、鼠标平滑、摩擦、调律阈值）
- 音频系统参数（采样率、音色模式）
- 钢琴系统参数（每根琴弦长度、线密度）
- 用户设置（升降号系统、最大录音时长等）
- 88 键琴弦数据库（CSV 文件）
- 文档路径、help 文档路径解析

软件中的所有模块均不直接读取或写入磁盘，而是通过 **ConfigManager** 完成交互。

---

### 6.1 配置系统总体结构

配置系统由三类组件组成：

```
Configuration System
├── ConfigManager.py
│ ├── load_config()
│ ├── save_config()
│ ├── DEFAULT_CONFIG
│ └── STATIC_DEFAULT_STRING_DATA（88键静态数据）
│
├── 各类配置窗口（Config Dialogs）
│ ├── PianoConfigWidget（钢琴物理参数）
│ ├── FrictionConfigWidget（摩擦模型参数）
│ ├── MouseSmoothConfigDialog（鼠标平滑）
│ ├── SampleRateDialog（采样率配置）
│ └── TuneThresholdDialog / DialRangeDialog（调律阈值 / 表盘范围）
│
└── StringCSVManager.py
├── 管理 88 键 L 和 μ 数据
├── CSV 自动初始化
└── update_string_parameters()
```

开发者应确保 **所有参数变动均通过 ConfigManager 保存**，并在各模块使用这些参数时读取它，而不是用硬编码写死默认值。

---

### 6.2 ConfigManager（全局配置文件管理）

**对应文件：`ConfigManager.py`**

ConfigManager 是配置系统的核心。

#### 6.2.1 配置文件路径

- 统一使用：项目根目录 / config.json

- 若 config.json 不存在 → 自动生成
- 若字段缺失 → 自动补全 DEFAULT_CONFIG

#### 6.2.2 DEFAULT_CONFIG 字段说明（核心内容）

主要字段如下（节选关键字段）：

```python
DEFAULT_CONFIG = {
    # 力学参数
    'mech_I': 0.0001,
    'mech_r': 0.005,
    'mech_k': 500000.0,
    'mech_Sigma_valid': 210000,
    'mech_Kd': 0.5,

    # 摩擦模型参数
    'mech_fric_limit_0': -10.0,
    'mech_alpha': 0.05,
    'mech_kinetic': 0.08,
    'mech_sigma': 0.001,

    # 鼠标控制平滑
    'mouse_deadzone': 0.5,
    'mouse_alpha': 0.25,
    'mouse_scale': 0.001,
    'mouse_decay_tau': 0.02,

    # 音色系统
    'audio_sample_rate': 44100,
    'audio_mode': 'sine',
    'audio_tone_path': None,

    # 设置菜单
    'settings_auto_prompt_save': True,
    'settings_accidental_type': 'FLAT',
    'settings_pitch_algorithm': 'AUTOCORR',
    'settings_standard_a4': 440,

    # 文件分析
    'settings_max_recording_time': 10,

    # 琴弦数据文件路径
    'db_file_path': None,
}
```

#### 6.2.3 静态琴弦数据（STATIC_DEFAULT_STRING_DATA）

ConfigManager 内部生成完整的 88 键默认数据：
 （真实物理模拟的长度 L、线密度 μ，随键号递减/递增变化）

```
STATIC_DEFAULT_STRING_DATA = _generate_full_static_string_data()
```

StringCSVManager 在初始化 CSV 时会自动写入这份静态数据。

### 6.3 各类配置窗口（Config Dialogs）

本软件包含多个用于修改配置的 UI 对话框。

所有对话框的设计原则：

- 从 config_data 读取默认值
- 修改后向 MainWindow 发送信号
- MainWindow 更新 right_panel / audio_engine / piano_generator 等系统
- 最终由 MainWindow.save_config() 写回 config.json

------

#### 6.3.1 PianoConfigWidget（钢琴物理参数）

📄 文件：`PianoConfigWidget.py`

管理 **钢琴全局物理参数（并非每根弦）**：

- 弦轴惯量 I
- 弦轴半径 r
- 弦劲度系数 k
- 允许应力 σ_valid
- 施力敏感度 K_d

流程：

```
show dialog → 修改参数 → emit config_saved → mainwindow.update_physics() → save_config()
```

------

#### 6.3.2 FrictionConfigWidget（摩擦模型参数）

📄 文件：`FrictionConfigWidget.py` SampleRateConfigWidget

表单字段：

- 初始静摩擦上限 τ₀
- 静摩擦增长系数 α
- 动摩擦扭矩 τ_kinetic
- 粘性摩擦 σ

修改后会发送：

```
config_saved.emit(new_params)
```

由 MainWindow 调用：

```
right_panel.set_params(...)
```

------

#### 6.3.3 MouseSmoothConfigDialog（鼠标平滑参数配置）

📄 文件：`MouseSmoothConfigDialog.py`

用户可在 UI 中调整鼠标控制手感：

- deadzone
- alpha（EMA 平滑）
- scale（像素→速度映射）
- decay_tau（松手衰减）

应用后更新 MouseAdjustBoard 的配置：

```
self.right_panel.board.apply_settings(...)
```

------

#### 6.3.4 SampleRateDialog（采样率设置）

📄 文件：`SampleRateDialog.py` StringCSVManager

允许选择：

```
44100 / 48000 / 96000 / 22050
```

选择后：

- 调整 AudioEngine 的采样率
- 调整音色库（若使用 sample / sf2）
- 重新初始化音频设备

------

#### 6.3.5 其他配置窗口

包括：

- 调律完成阈值 TuneThresholdDialog
- 表盘范围 DialRangeDialog

格式统一：

```
current_value → QDoubleSpinBox → emit → MainWindow 保存
```

------

### 6.4 StringCSVManager（琴弦数据库管理）

📄 文件：`StringCSVManager.py`

该模块负责管理每根钢琴弦（88 键）的：

- key_id（编号）
- note_name（音名）
- length（长度 L）
- density（线密度 μ）

#### 6.4.1 CSV 文件路径

自动定位：

```
项目根目录 / data / strings_default.csv
```

#### 6.4.2 初始化流程

若 CSV 文件不存在 → 自动创建：

- 写入表头
- 写入 ConfigManager.STATIC_DEFAULT_STRING_DATA

无需用户干预。

#### 6.4.3 常用API

##### 读取所有参数

```
get_string_parameters() → List[Dict]
```

##### 按 key_id 查询

```
get_string_parameters_by_id(id)
```

MainWindow 调用它来设置 MechanicsEngine 的初始参数。

##### 更新全部参数

```
update_string_parameters(list_of_params)
```

用于 PianConfigWidget 批量更新所有键。

------

### 6.5 配置更新与系统同步流程

以“摩擦参数修改”为例说明完整流程：

```
FrictionConfigWidget → config_saved(new_params)
        ↓
MainWindow.on_friction_config_saved()
        ↓
RightMechanicsPanel.set_params(new_params)
        ↓
MechanicsEngine.update_physical_params(new_params)
        ↓
MainWindow.save_config(config)
```

#### 原则：

- **所有参数修改必须通过 ConfigManager 保存**
- **right_panel / audio_engine / piano_generator 不应自己写配置文件**
- **UI 层负责展示与调用，底层系统负责计算**



------

### 🔚 配置系统总结

配置系统是整个软件稳定运行的基础模块，负责：
 **“保存 → 加载 → 同步 → 应用”** 全流程。

开发者扩展新功能时，应优先：

1. 在 `DEFAULT_CONFIG` 添加字段
2. 在 UI 中提供调节窗口（可选）
3. 在 MainWindow 中同步配置
4. 调用 ConfigManager.save_config()

并避免硬编码默认参数，保持随配置动态变化。



------


## **7. 状态监控系统（Status Monitoring System）**

该系统由两个子模块组成：

- **UserStatusCard**：面向用户的可视化状态卡片（主界面左侧）
- **DebugStatusWindow**：面向开发者的调试日志窗口

它们均由 MainWindow 统一调度，用于展示实时处理状态、文件分析进度、音频检测信息等。

---

### **7.1 UserStatusCard — 用户态状态卡片**

📄 文件：`UserStatusCard.py`  
引用：:contentReference[oaicite:0]{index=0}

UserStatusCard 是主界面左侧的**状态显示组件**，用于向用户直观呈现：

- 当前输入设备  
- 当前分析模式  
- 音高检测算法  
- 当前目标音高  
- 实时检测到的频率  
- 当前音分偏差  
- 置信度  
- 文件分析进度（仅文件分析时）

#### **7.1.1 UI 结构层级**

```
UserStatusCard (QFrame)
 ├── 标题 “系统状态概览”
 ├── 信息表格（QGridLayout）
 │     ├── 输入设备
 │     ├── 分析模式
 │     ├── 音高算法
 │     ├── 当前目标
 │     ├── 当前频率
 │     ├── 音分偏差
 │     └── 置信度
 ├── 状态消息（多行自动换行）
 └── 进度条（文件分析模式下激活）

```

该控件本身完全独立，所有内容更新统一由 MainWindow 调用它公开的接口。

---

#### **7.1.2 样式与布局设计**

- 使用卡片风格（圆角、浅灰背景）
- 所有 key 使用 `status-key` 格式（灰色、轻量）
- 所有 value 使用 `status-value` 样式（深色、半粗体）
- 状态消息自动换行，避免撑宽左侧面板
- 进度条有“激活蓝”与“静默灰”两种样式

---

#### **7.1.3 对外接口（MainWindow 调用）**

UserStatusCard 通过以下接口更新：

##### 设置设备 / 模式 / 算法

```python
set_input_device(name)
set_mode(text)
set_algorithm(algo_str)
```

##### 设置目标音高

```python
set_target(note_name, freq)
```

##### 实时更新检测结果

```python
update_realtime(freq, target_freq, cents, confidence)
```

MainWindow 的实时音频回调会直接调用这个接口。

##### 更新状态提示

```python
set_status_message(message)
```

用于显示如：

- “正在分析…”
- “等待输入…”
- “文件处理完成”

##### 控制进度条

```python
set_progress_active(True/False)
show_progress(True/False)
```

文件分析模式中切换可见性与激活样式。

------

#### **7.1.4 使用场景汇总**

UserStatusCard 主要用于向用户反馈系统当前状态，典型调用包括：

| 来源         | 调用场景           | 调用接口                            |
| ------------ | ------------------ | ----------------------------------- |
| 输入设备切换 | 麦克风选择         | set_input_device                    |
| 模式切换     | 实时 / 文件分析    | set_mode                            |
| 改变目标音高 | 点击钢琴键、下拉框 | set_target                          |
| 实时音频检测 | pitch callback     | update_realtime                     |
| 文件分析过程 | 进度回调           | set_progress_active / show_progress |
| 系统提示     | 任何状态变化       | set_status_message                  |

------

### **7.2 DebugStatusWindow — 开发者调试日志窗口**

📄 文件：`UserStatusCard.py`（同文件内定义）

DebugStatusWindow 是一个**独立的 QDialog 窗口**，用于记录 MainWindow 中所有状态信息（调试用途）。

它并不暴露给普通用户，而是绑定在菜单栏的：

```
帮助 → 显示调试日志
```

开发者可随时查看系统内部状态变化。

------

#### **7.2.1 功能定位**

- 追加式日志记录（不会覆盖）
- 自动滚动到末尾
- 时间戳格式：`[HH:MM:SS] message`
- 与旧的“覆盖式状态替换”完全不同

DebugStatusWindow 仅用于：

- 查看内部状态变化
- 查看分析流程
- 监视错误 / 警告
- 调试算法行为

------

#### **7.2.2 主要接口**

##### 追加日志

```python
append_log(message)
```

内部自动加入时间戳。

##### 兼容旧接口（MainWindow 仍调用）

```python
apply_status_update_logic(message)
```

该函数内部直接调用 `append_log()`。

##### 自动同步菜单栏状态

关闭窗口时：

```python
closeEvent → 取消勾选 action_show_debug_status
```

防止菜单栏状态不同步。

------

#### **7.2.3 日志内容示例**

```
[12:30:05] 初始化音频系统完成
[12:30:05] 进入实时分析模式
[12:30:06] 收到频率：439.7 Hz (置信度 0.93)
[12:30:07] 鼠标输入速度 = 0.012 rad/s
[12:30:07] 扭矩 = 0.014 N·m
```

日志窗口完全不影响主界面运行，可持续观察内部状态。

------

### **🔚 状态监控系统总结**

| 模块                  | 作用                                               |
| --------------------- | -------------------------------------------------- |
| **UserStatusCard**    | 面向用户显示系统状态、实时频率、音分偏差和文件进度 |
| **DebugStatusWindow** | 面向开发者，用于记录完整调试日志                   |

它们共同组成软件的数据可视化与调试体系：

```
MainWindow
   ├── update_status() → UserStatusCard（用户）
   └── update_status() → DebugStatusWindow（开发者）
```

通过分离用户态与开发态显示，系统能够同时：

- 给普通用户提供清晰直观的状态反馈
- 给开发者提供足够的信息诊断系统问题



## 8.导出系统（Export System）

该系统基于MechanicsEngine的修复时间计算功能，提供批量修复时间计算服务。

**使用：**

菜单-导出

可以调的参数

| 参数              | 意义                                  |
| ----------------- | ------------------------------------- |
| 预定义力矩（Nm）  | 批量修复施加的用户力矩                |
| 音分范围（cents） | 最大的音分偏差范围                    |
| 步长              | 音分偏差的数据步长                    |
| 模拟时间步长      | 用于MechanicsEngine计算修复时间的步长 |
| 最大模拟时间      | 用于MechanicsEngine计算修复时间的上限 |



可以选择导出csv/图像，并指定路径进行保存数据