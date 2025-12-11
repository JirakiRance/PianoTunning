# audio_detector.py
import numpy as np
import librosa
import sounddevice as sd
import wave
import time
import os
import numpy as np
import threading
from queue import Queue
from datetime import datetime
from typing import Optional, Callable, List, Dict, Any,Tuple
from enum import Enum
from dataclasses import dataclass

from PitchDetector import PitchDetector, PitchDetectionResult,DetectionTiming


class ProcessingMode(Enum):
    """处理模式枚举"""
    REALTIME_RECORDING = "realtime_recording"
    FILE_ANALYSIS = "file_analysis"


class PitchDetectionAlgorithm(Enum):
    """音高检测算法枚举"""
    PYIN_BASIC = "pyin_basic"
    PYIN_ENHANCED = "pyin_enhanced"
    YIN = "yin"
    HPS = "hps"
    AUTOCORR = "autocorr"
    ADAPTIVE = "adaptive"


@dataclass
class PitchResult:
    """音高检测结果"""
    frequency: float
    confidence: float
    timestamp: float
    target_frequency: Optional[float] = None
    cents_deviation: Optional[float] = None
    method_used: str = ""

@dataclass
class RealtimeData:
    """实时传输的数据包"""
    pitch_result: PitchResult
    audio_frame: np.ndarray # 当前音频帧数据 (用于波形和频谱)

@dataclass
class MusicalAnalysisResult:
    """音乐分析结果 - 替代原来的AudioAnalysisResult"""
    file_path: str
    duration: float
    sample_rate: float
    pitch_results: List[PitchResult]
    dominant_frequency: float  # 主导频率替代平均频率
    stability: float  # 稳定性 0-1
    tuning_quality: float  # 调音质量 0-1 (如果有目标频率)
    confidence_level: float  # 总体置信度
    valid_frame_ratio: float  # 有效帧比例
    # --- 新增：用于整体波形绘制 ---
    full_audio_data: Optional[np.ndarray] = None

@dataclass
class AnalysisTiming:
    """分析计时结果"""
    total_time: float
    algorithm_times: dict
    frames_processed: int
    average_fps: float

@dataclass
class AnalysisProgress:
    """分析进度信息"""
    current_frame: int
    total_frames: int
    progress_percentage: float
    elapsed_time: float
    estimated_remaining_time: float
    current_algorithm: str


class AudioDetector:
    """音频检测主类"""

    def __init__(self, sample_rate=44100, frame_length=8192, hop_length=512,
                 output_dir="recordings", global_confidence=0.7,
                 f_min=20.0, f_max=5000.0, input_device=None,
                 pitch_algorithm=PitchDetectionAlgorithm.PYIN_ENHANCED):
        self.analysis_start_time = 0    # 新增的进度功能
        self.progress_callback = None
        self.target_frequency: Optional[float] = None
        # 音高检测器
        self.pitch_detector = PitchDetector(
            sample_rate=sample_rate,
            frame_length=frame_length,
            hop_length=hop_length,
            f_min=f_min,
            f_max=f_max,
            global_confidence=global_confidence
        )

        # 音频参数
        self.sample_rate = sample_rate
        self.frame_length = frame_length
        self.hop_length = hop_length
        self.global_confidence = global_confidence
        self.f_min = f_min
        self.f_max = f_max
        self.input_device = input_device

        # 状态标志
        self.is_recording = False
        self.is_processing = False
        self.current_mode = None

        # 音频流和缓冲区
        self.audio_stream = None
        self.audio_buffer = Queue()

        # 线程管理
        self.recording_thread = None
        self.process_thread = None

        # 回调函数
        self.pitch_callback = None

        # 文件管理
        self.output_dir = output_dir
        self.current_recording_file = None
        self._ensure_output_dir()

        # 分析结果缓存
        self.analysis_results = {}

        # 算法映射
        self.algorithm_map = {
            PitchDetectionAlgorithm.PYIN_BASIC: self.pitch_detector.detect_pyin_basic,
            PitchDetectionAlgorithm.PYIN_ENHANCED: self.pitch_detector.detect_pyin_enhanced,
            PitchDetectionAlgorithm.YIN: self.pitch_detector.detect_yin,
            PitchDetectionAlgorithm.HPS: self.pitch_detector.detect_hps,
            PitchDetectionAlgorithm.AUTOCORR: self.pitch_detector.detect_autocorr,
            PitchDetectionAlgorithm.ADAPTIVE: self.pitch_detector.detect_adaptive,
        }

        self.current_algorithm = pitch_algorithm

    # ==================== 公共方法 ====================

    def start_realtime_analysis(self, pitch_callback: Callable[[PitchResult], None],
                                save_recording: bool = True,
                                target_frequency: Optional[float] = None) -> bool:
        """开始实时分析"""
        try:
            if self.is_recording:
                print("当前正在录音")
                return False

            self.current_mode = ProcessingMode.REALTIME_RECORDING

            # 不再检查 save_recording，始终创建文件
            self._create_recording_file()
            # ---------------------------------

            self.is_recording = True
            self.pitch_callback = pitch_callback
            self.target_frequency = target_frequency    # 新增的AudioDetecot的目标频率

            if save_recording:
                self._create_recording_file()

            self._start_audio_stream()
            self._start_processing_thread()

            print("实时录音分析已启动！")
            return True
        except Exception as e:
            print(f"启动实时分析失败: {e}")
            return False

    def stop_realtime_analysis(self) -> Optional[str]:
        """停止实时分析"""
        try:
            if self.is_recording:
                self.is_recording = False

                if self.audio_stream:
                    self.audio_stream.stop()
                    self.audio_stream.close()
                    self.audio_stream = None

                if self.process_thread and self.process_thread.is_alive():
                    self.process_thread.join(timeout=2.0)

                recording_file = None
                if self.current_recording_file:
                    recording_file = self.current_recording_file
                    self.current_recording_file = None

                print("实时录音已结束!")
                return recording_file
            else:
                print("当前未在录音!")
                return None
        except Exception as e:
            print(f"停止实时分析失败: {e}")
            return None

    def analyse_audio_file(self, file_path: str, target_frequency: Optional[float] = None) -> Optional[
        MusicalAnalysisResult]:
        """分析音频文件"""
        try:
            if not os.path.exists(file_path):
                print(f"文件不存在: {file_path}")
                return None

            self.current_mode = ProcessingMode.FILE_ANALYSIS
            self.is_processing = True

            print(f"开始分析音频文件: {file_path}")

            # 加载音频
            audio_data, sr = librosa.load(file_path, sr=self.sample_rate)
            duration = len(audio_data) / sr

            # 音高检测
            pitch_results = self._analyse_audio_data(audio_data, sr, target_frequency)

            # 音乐统计分析
            analysis_result = self._calculate_musical_statistics(
                pitch_results, file_path, duration, sr, target_frequency,
                full_audio_data=audio_data
            )
            # 附加完整音频数据
            analysis_result.full_audio_data = audio_data

            self.analysis_results[file_path] = analysis_result
            self.is_processing = False

            self._print_analysis_summary(analysis_result)
            print(f"音频文件分析完成: {file_path}")
            return analysis_result

        except Exception as e:
            print(f"分析音频文件失败: {e}")
            self.is_processing = False
            return None

    def generate_reference_tone(self, frequency: float, duration: float = 2.0,
                                volume: float = 0.3, save_to_file: bool = False) -> Optional[str]:
        """生成参考音"""
        try:
            t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
            wave_data = volume * np.sin(2 * np.pi * frequency * t)

            # 淡入淡出
            fade_samples = int(0.05 * self.sample_rate)
            if len(wave_data) > 2 * fade_samples:
                fade_in = np.linspace(0, 1, fade_samples)
                fade_out = np.linspace(1, 0, fade_samples)
                wave_data[:fade_samples] *= fade_in
                wave_data[-fade_samples:] *= fade_out

            sd.play(wave_data, samplerate=self.sample_rate)
            sd.wait()

            if save_to_file:
                filename = f"reference_{frequency}Hz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                filepath = os.path.join(self.output_dir, filename)
                self._save_wave_file(filepath, wave_data, self.sample_rate)
                print(f"参考音已保存: {filepath}")
                return filepath
            return None
        except Exception as e:
            print(f"生成参考音失败: {e}")
            return None

    # ==================== 辅助方法 ====================

    def calculate_cents_deviation(self, measured_freq: float, target_freq: float) -> float:
        """计算音分偏差"""
        if measured_freq <= 0 or target_freq <= 0:
            return 0.0
        return 1200 * np.log2(measured_freq / target_freq)

    def get_audio_devices(self) -> List[Dict[str, Any]]:
        """获取音频设备列表"""
        return sd.query_devices()

    def set_pitch_algorithm(self, algorithm: PitchDetectionAlgorithm):
        """设置音高检测算法"""
        self.current_algorithm = algorithm
        print(f"已切换到算法: {algorithm.value}")

    def get_current_algorithm(self) -> PitchDetectionAlgorithm:
        """获取当前算法"""
        return self.current_algorithm

    # ======================1129新增设备选择接口==========================
    @staticmethod
    def get_audio_input_devices():
        """获取所有可用的音频输入设备"""
        try:
            devices = sd.query_devices()
            input_devices = []

            for i, device in enumerate(devices):
                # 检查是否是输入设备（输入通道数 > 0）
                if device.get('max_input_channels', 0) > 0:
                    input_devices.append({
                        'index': i,
                        'name': device.get('name', f'Device {i}'),
                        'channels': device.get('max_input_channels', 1),
                        'sample_rate': device.get('default_samplerate', 44100),
                        'hostapi': device.get('hostapi', 0)
                    })
            return input_devices
        except Exception as e:
            print(f"获取音频设备列表失败: {e}")
            return []

    @staticmethod
    def get_default_input_device():
        """获取默认输入设备索引"""
        try:
            return sd.default.device[0]  # 输入设备索引
        except:
            return 0

    def set_input_device(self, device_index):
        """设置输入设备"""
        try:
            # 验证设备是否存在
            devices = self.get_audio_input_devices()
            device_exists = any(device['index'] == device_index for device in devices)

            if not device_exists:
                print(f"设备 {device_index} 不存在")
                return False

            self.input_device = device_index

            # 如果正在录音，需要重启音频流
            if self.is_recording and self.audio_stream:
                was_recording = True
                self.stop_realtime_analysis()
                time.sleep(0.1)  # 短暂延迟确保完全停止
                self.start_realtime_analysis(self.pitch_callback, True, self.target_frequency)
            else:
                was_recording = False

            print(f"输入设备已切换到: {device_index}")
            return True

        except Exception as e:
            print(f"设置输入设备失败: {e}")
            return False

    # ==================== 私有方法 ====================

    def _ensure_output_dir(self):
        """确保输出目录存在"""
        try:
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
        except Exception as e:
            print(f"创建输出目录失败: {e}")

    def _create_recording_file(self) -> str:
        """创建录音文件"""
        filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        filepath = os.path.join(self.output_dir, filename)
        self.current_recording_file = filepath
        return filepath

    def _start_audio_stream(self):
        """启动音频流"""

        def audio_callback(indata, frames, time_info, status):
            if status:
                print(f"音频流状态: {status}")

            audio_data = indata[:, 0] if indata.ndim > 1 else indata

            # 保存到文件
            if self.current_recording_file and not os.path.exists(self.current_recording_file):
                self._save_wave_file(self.current_recording_file, audio_data, self.sample_rate)
            elif self.current_recording_file:
                self._append_to_wave_file(self.current_recording_file, audio_data)

            # 放入缓冲区
            self.audio_buffer.put(audio_data.copy())

        self.audio_stream = sd.InputStream(
            callback=audio_callback,
            samplerate=self.sample_rate,
            channels=1,
            blocksize=self.hop_length,
            dtype='float32',
            device=self.input_device
        )
        self.audio_stream.start()

    def _start_processing_thread(self):
        """启动处理线程"""
        self.process_thread = threading.Thread(target=self._processing_loop)
        self.process_thread.daemon = True
        self.process_thread.start()

    def _processing_loop(self):
        """处理循环"""
        buffer_duration = 0.1
        buffer_size = int(self.sample_rate * buffer_duration)
        audio_accumulator = np.array([], dtype=np.float32)

        while self.is_recording:
            try:
                if not self.audio_buffer.empty():
                    chunk = self.audio_buffer.get_nowait()
                    audio_accumulator = np.concatenate([audio_accumulator, chunk])

                #     if len(audio_accumulator) >= buffer_size:
                #         process_data = audio_accumulator[:buffer_size]
                #         audio_accumulator = audio_accumulator[buffer_size:]

                #         pitch_result = self._detect_pitch(process_data)
                #         if pitch_result and self.pitch_callback:
                #             self.pitch_callback(pitch_result)
                # time.sleep(0.01)
                # 修改了返回逻辑，需要原始数据以绘制频谱
                    if len(audio_accumulator) >= buffer_size:
                        process_data = audio_accumulator[:buffer_size]
                        audio_accumulator = audio_accumulator[buffer_size:]

                        # 接收修改后的返回
                        detection_output = self._detect_pitch(
                            audio_data=process_data,
                            target_freq=self.target_frequency
                        )

                        if detection_output and self.pitch_callback:
                            pitch_result, audio_frame = detection_output # <-- 解包

                            # 封装 RealtimeData
                            realtime_data = RealtimeData(
                                pitch_result=pitch_result,
                                audio_frame=audio_frame
                            )
                            self.pitch_callback(realtime_data) # <-- 传递 RealtimeData
                time.sleep(0.01)
            except Exception as e:
                print(f"处理循环错误: {e}")
                time.sleep(0.1)

    def _detect_pitch(self, audio_data: np.ndarray, target_freq: Optional[float] = None,
                      frame_index: int = 0, total_frames: int = 0) -> Optional[Tuple[PitchResult, np.ndarray]]:
        """音高检测 - 带进度和计时"""
        start_time = time.time()

        detector = self.algorithm_map.get(self.current_algorithm, self.pitch_detector.detect_pyin_enhanced)
        result = detector(audio_data, target_freq)

        detection_time = time.time() - start_time

        # 记录计时信息
        if result:
            timing_info = DetectionTiming(
                algorithm_name=result.method_used,
                detection_time=detection_time,
                timestamp=time.time()
            )
            self.pitch_detector.detection_timings.append(timing_info)

        # 进度回调
        if self.progress_callback and total_frames > 0:
            elapsed_time = time.time() - self.analysis_start_time
            progress_percentage = (frame_index + 1) / total_frames * 100

            if frame_index > 0:
                estimated_remaining = elapsed_time / frame_index * (total_frames - frame_index)
            else:
                estimated_remaining = 0

            progress = AnalysisProgress(
                current_frame=frame_index + 1,
                total_frames=total_frames,
                progress_percentage=progress_percentage,
                elapsed_time=elapsed_time,
                estimated_remaining_time=estimated_remaining,
                current_algorithm=self.current_algorithm.value
            )
            self.progress_callback(progress)

        if result:
            cents = self.calculate_cents_deviation(result.frequency, target_freq) if target_freq else None
            pitch_result = PitchResult(
                frequency=result.frequency,
                confidence=result.confidence,
                timestamp=time.time(),
                target_frequency=target_freq,
                cents_deviation=cents,
                method_used=result.method_used
            )
            # 返回 PitchResult 和 原始音频数据
            return (pitch_result, audio_data) # <-- 修改返回类型
        return None

    def _analyse_audio_data(self, audio_data: np.ndarray, sample_rate: int,
                            target_freq: Optional[float] = None) -> List[PitchResult]:
        """分析音频数据 - 带进度跟踪"""
        pitch_results = []
        frame_size = self.frame_length
        hop_size = self.hop_length

        # 计算总帧数
        total_frames = (len(audio_data) - frame_size) // hop_size + 1
        self.analysis_start_time = time.time()

        for frame_index, start_idx in enumerate(range(0, len(audio_data) - frame_size, hop_size)):
            end_idx = start_idx + frame_size
            frame = audio_data[start_idx:end_idx]

            # pitch_result = self._detect_pitch(frame, target_freq, frame_index, total_frames)
            # if pitch_result:
            #     pitch_result.timestamp = start_idx / sample_rate
            #     pitch_results.append(pitch_result)
            # _detect_pitch 现在返回 (PitchResult, audio_data) 或 None
            detection_output = self._detect_pitch(frame, target_freq, frame_index, total_frames)
            if detection_output:
                pitch_result, _ = detection_output # <-- 关键修改：正确解包，忽略 audio_data
                # 在文件分析模式下，重新计算时间戳
                pitch_result.timestamp = start_idx / sample_rate
                pitch_results.append(pitch_result)

        return pitch_results

    # 添加新方法：
    def set_progress_callback(self, callback: Optional[Callable[[AnalysisProgress], None]]):
        """设置进度回调函数"""
        self.progress_callback = callback

    def get_analysis_timing(self) -> AnalysisTiming:
        """获取分析计时结果"""
        total_time = 0.0
        algorithm_times = {}
        total_frames = 0

        # 从pitch_detector获取计时信息
        performance = self.pitch_detector.get_algorithm_performance()

        for algo, stats in performance.items():
            total_time += stats['total_time']
            algorithm_times[algo] = stats
            total_frames += stats['count']

        average_fps = total_frames / total_time if total_time > 0 else 0

        return AnalysisTiming(
            total_time=total_time,
            algorithm_times=algorithm_times,
            frames_processed=total_frames,
            average_fps=average_fps
        )

    def clear_timing_data(self):
        """清空计时数据"""
        self.pitch_detector.clear_timings()

    def _calculate_musical_statistics(self, pitch_results: List[PitchResult], file_path: str,
                                      duration: float, sample_rate: float,
                                      target_frequency: Optional[float] = None,
                                      full_audio_data: Optional[np.ndarray] = None) -> MusicalAnalysisResult:
        """计算音乐统计信息"""
        if not pitch_results:
            return MusicalAnalysisResult(
                file_path=file_path,
                duration=duration,
                sample_rate=sample_rate,
                pitch_results=pitch_results,
                dominant_frequency=0.0,
                stability=0.0,
                tuning_quality=0.0,
                confidence_level=0.0,
                valid_frame_ratio=0.0,
                full_audio_data=full_audio_data
            )

        # 有效结果筛选
        valid_results = [r for r in pitch_results if r.confidence > 0.3 and self.f_min <= r.frequency <= self.f_max]
        valid_frame_ratio = len(valid_results) / len(pitch_results) if pitch_results else 0.0

        if not valid_results:
            return MusicalAnalysisResult(
                file_path=file_path,
                duration=duration,
                sample_rate=sample_rate,
                pitch_results=pitch_results,
                dominant_frequency=0.0,
                stability=0.0,
                tuning_quality=0.0,
                confidence_level=0.0,
                valid_frame_ratio=valid_frame_ratio,
                full_audio_data=full_audio_data
            )

        # 提取频率和置信度
        frequencies = np.array([r.frequency for r in valid_results])
        confidences = np.array([r.confidence for r in valid_results])

        # 主导频率计算（使用加权直方图）
        dominant_freq = self._find_dominant_frequency(frequencies, confidences)

        # 稳定性计算
        stability = self._calculate_stability(frequencies, confidences, dominant_freq)

        # 调音质量计算
        tuning_quality = 0.0
        if target_frequency:
            tuning_quality = self._calculate_tuning_quality(frequencies, confidences, target_frequency)

        # 总体置信度
        confidence_level = np.mean(confidences)

        return MusicalAnalysisResult(
            file_path=file_path,
            duration=duration,
            sample_rate=sample_rate,
            pitch_results=pitch_results,
            dominant_frequency=dominant_freq,
            stability=stability,
            tuning_quality=tuning_quality,
            confidence_level=confidence_level,
            valid_frame_ratio=valid_frame_ratio,
            full_audio_data=full_audio_data
        )

    def _find_dominant_frequency(self, frequencies: np.ndarray, confidences: np.ndarray) -> float:
        """找到主导频率"""
        if len(frequencies) == 0:
            return 0.0

        if len(frequencies) == 1:
            return frequencies[0]

        # 使用加权直方图找到最密集区域
        hist, bin_edges = np.histogram(frequencies, bins=20, weights=confidences)
        max_bin = np.argmax(hist)
        dominant_range = (bin_edges[max_bin], bin_edges[max_bin + 1])

        # 在该范围内找到加权中位数
        in_range_mask = (frequencies >= dominant_range[0]) & (frequencies <= dominant_range[1])
        if np.any(in_range_mask):
            range_freqs = frequencies[in_range_mask]
            range_confs = confidences[in_range_mask]

            # 计算加权中位数
            sorted_indices = np.argsort(range_freqs)
            sorted_freqs = range_freqs[sorted_indices]
            sorted_confs = range_confs[sorted_indices]

            cumsum = np.cumsum(sorted_confs)
            median_idx = np.searchsorted(cumsum, cumsum[-1] / 2)
            return sorted_freqs[median_idx]

        # 备用方法：高置信度的中位数
        high_conf_mask = confidences > np.median(confidences)
        if np.any(high_conf_mask):
            return np.median(frequencies[high_conf_mask])

        return np.median(frequencies)

    def _calculate_stability(self, frequencies: np.ndarray, confidences: np.ndarray, dominant_freq: float) -> float:
        """计算稳定性"""
        if len(frequencies) <= 1:
            return 1.0 if len(frequencies) == 1 else 0.0

        # 基于与主导频率的偏差计算稳定性
        relative_errors = np.abs(frequencies - dominant_freq) / dominant_freq
        weighted_errors = relative_errors * confidences
        mean_error = np.mean(weighted_errors)

        # 转换为稳定性分数 (0-1)
        stability = 1.0 / (1.0 + 10.0 * mean_error)  # 使用sigmoid-like函数
        return max(0.0, min(1.0, stability))

    def _calculate_tuning_quality(self, frequencies: np.ndarray, confidences: np.ndarray,
                                  target_frequency: float) -> float:
        """计算调音质量"""
        if len(frequencies) == 0:
            return 0.0

        # 计算与目标频率的平均偏差
        relative_errors = np.abs(frequencies - target_frequency) / target_frequency
        weighted_errors = relative_errors * confidences
        mean_error = np.mean(weighted_errors)

        # 转换为质量分数 (0-1)
        quality = 1.0 / (1.0 + 50.0 * mean_error)  # 对调音要求更严格
        return max(0.0, min(1.0, quality))

    def _print_analysis_summary(self, result: MusicalAnalysisResult):
        """打印分析摘要"""
        print(f"\n=== 分析结果摘要 ===")
        print(f"测试算法:{self.current_algorithm}")
        print(f"文件: {result.file_path}")
        print(f"时长: {result.duration:.2f}秒")
        print(f"主导频率: {result.dominant_frequency:.1f}Hz")
        print(f"稳定性: {result.stability:.3f}")
        print(f"调音质量: {result.tuning_quality:.3f}")
        print(f"总体置信度: {result.confidence_level:.3f}")
        print(f"有效帧比例: {result.valid_frame_ratio:.3f}")
        print(f"总检测帧数: {len(result.pitch_results)}")
        print("======end======")

        if result.pitch_results:
            # 显示使用的算法分布
            methods = {}
            for r in result.pitch_results:
                methods[r.method_used] = methods.get(r.method_used, 0) + 1

            print("算法使用分布:")
            for method, count in methods.items():
                percentage = count / len(result.pitch_results) * 100
                print(f"  {method}: {count}帧 ({percentage:.1f}%)")

    def _save_wave_file(self, filepath: str, data: np.ndarray, sample_rate: int):
        """保存WAV文件"""
        try:
            data_normalized = np.clip(data, -1.0, 1.0)
            data_int16 = (data_normalized * 32767).astype(np.int16)

            with wave.open(filepath, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(data_int16.tobytes())
        except Exception as e:
            print(f"保存WAV文件失败: {e}")

    def _append_to_wave_file(self, filepath: str, data: np.ndarray):
        """追加数据到WAV文件"""
        try:
            data_normalized = np.clip(data, -1.0, 1.0)
            data_int16 = (data_normalized * 32767).astype(np.int16)
            new_frames = data_int16.tobytes()

            with wave.open(filepath, 'rb') as wav_file:
                params = wav_file.getparams()
                existing_frames = wav_file.readframes(wav_file.getnframes())

            combined_frames = existing_frames + new_frames
            with wave.open(filepath, 'wb') as wav_file:
                wav_file.setparams(params)
                wav_file.writeframes(combined_frames)
        except Exception as e:
            print(f"追加WAV文件失败: {e}")

"""=================================class AudioDetector====================================="""


def progress_callback(progress: AnalysisProgress):
    """进度回调函数"""
    print(f"\r进度: {progress.progress_percentage:5.1f}% | "
          f"帧: {progress.current_frame:3d}/{progress.total_frames:3d} | "
          f"已用: {progress.elapsed_time:5.1f}s | "
          f"剩余: {progress.estimated_remaining_time:5.1f}s | "
          f"算法: {progress.current_algorithm:12s}", end="", flush=True)


def test_all_algorithms(test_file: str, target_frequency: float = 440.0):
    """测试所有算法 """
    if not os.path.exists(test_file):
        print(f"测试文件不存在: {test_file}")
        return

    print("=== 算法比较测试 ===")
    print(f"测试文件: {os.path.basename(test_file)}")
    print(f"目标频率: {target_frequency}Hz")
    print("=" * 80)

    algorithms = [
        PitchDetectionAlgorithm.PYIN_BASIC,
        PitchDetectionAlgorithm.PYIN_ENHANCED,
        PitchDetectionAlgorithm.YIN,
        PitchDetectionAlgorithm.HPS,
        PitchDetectionAlgorithm.AUTOCORR,
        PitchDetectionAlgorithm.ADAPTIVE
    ]

    all_results = []

    for algo in algorithms:
        print(f"\n--- 测试算法: {algo.value} ---")

        # 创建检测器并设置进度回调
        detector = AudioDetector(input_device=2, pitch_algorithm=algo)
        detector.set_progress_callback(progress_callback)
        detector.clear_timing_data()  # 清空之前的计时数据

        print("开始分析...")
        start_time = time.time()

        # 执行分析
        result = detector.analyse_audio_file(test_file, target_frequency=target_frequency)

        analysis_time = time.time() - start_time
        print("\n")  # 换行，结束进度显示

        if result:
            # 获取计时信息
            timing = detector.get_analysis_timing()

            # 保存结果
            algo_result = {
                'algorithm': algo.value,
                'result': result,
                'timing': timing,
                'analysis_time': analysis_time
            }
            all_results.append(algo_result)

            # 显示结果
            print(f"✓ 分析完成 - 总耗时: {analysis_time:.2f}s")
            print(f"  主导频率: {result.dominant_frequency:.1f}Hz")
            print(f"  稳定性: {result.stability:.3f}")
            if target_frequency:
                print(f"  调音质量: {result.tuning_quality:.3f}")
            print(f"  检测帧数: {len(result.pitch_results)}")
            print(f"  有效帧比例: {result.valid_frame_ratio:.3f}")
            print(f"  总体置信度: {result.confidence_level:.3f}")

            # 显示性能信息
            print(f"  性能统计:")
            print(f"    - 总处理时间: {timing.total_time:.2f}s")
            print(f"    - 平均FPS: {timing.average_fps:.1f}")
            print(f"    - 处理帧数: {timing.frames_processed}")

            # 显示各算法耗时（对于自适应算法）
            if algo == PitchDetectionAlgorithm.ADAPTIVE and timing.algorithm_times:
                print(f"    - 算法分布:")
                for algo_name, stats in timing.algorithm_times.items():
                    percentage = stats['count'] / timing.frames_processed * 100
                    print(
                        f"      {algo_name}: {stats['count']}帧 ({percentage:.1f}%) - 平均{stats['average_time'] * 1000:.1f}ms/帧")

        else:
            print("✗ 分析失败")

    # 显示总结比较
    if all_results:
        print("\n" + "=" * 80)
        print("算法性能总结:")
        print("-" * 80)
        print(f"{'算法':<15} {'主导频率':<10} {'稳定性':<8} {'质量':<6} {'总耗时':<8} {'FPS':<6} {'置信度':<8}")
        print("-" * 80)

        for algo_result in all_results:
            algo = algo_result['algorithm']
            result = algo_result['result']
            timing = algo_result['timing']

            freq_str = f"{result.dominant_frequency:.1f}Hz"
            stability_str = f"{result.stability:.3f}"
            quality_str = f"{result.tuning_quality:.3f}" if target_frequency else "N/A"
            time_str = f"{algo_result['analysis_time']:.2f}s"
            fps_str = f"{timing.average_fps:.1f}"
            confidence_str = f"{result.confidence_level:.3f}"

            print(
                f"{algo:<15} {freq_str:<10} {stability_str:<8} {quality_str:<6} {time_str:<8} {fps_str:<6} {confidence_str:<8}")

        # 找出最佳算法
        best_stability = max(all_results, key=lambda x: x['result'].stability)
        best_confidence = max(all_results, key=lambda x: x['result'].confidence_level)
        fastest = min(all_results, key=lambda x: x['analysis_time'])

        print("-" * 80)
        print(f"最佳稳定性: {best_stability['algorithm']} ({best_stability['result'].stability:.3f})")
        print(f"最佳置信度: {best_confidence['algorithm']} ({best_confidence['result'].confidence_level:.3f})")
        print(f"最快算法: {fastest['algorithm']} ({fastest['analysis_time']:.2f}s)")


if __name__ == "__main__":
    test_file_440 = "E:\\Ducuments\\pycharm\\PianoTunning\\recordings\\reference_440.0Hz_20251002_151936.wav"
    test_file_1614 = "E:\\Ducuments\\pycharm\\PianoTunning\\recordings\\recording_20251002_161417.wav"

    # 测试有目标频率的情况
    print("测试开始")
    test_all_algorithms(test_file_1614, 440.0)

    # print("\n\n" + "=" * 80)
    # print("测试2: 无目标频率分析")
    # # 测试无目标频率的情况
    # test_all_algorithms(test_file_1614)  # 不传入target_frequency
