# pitch_detector.py
import numpy as np
import librosa
from enum import Enum
from typing import Optional, List, Tuple,Callable
from dataclasses import dataclass
import time


@dataclass
class PitchDetectionResult:
    """音高检测结果"""
    frequency: float
    confidence: float
    method_used: str = ""
@dataclass
class DetectionTiming:
    """检测计时信息"""
    algorithm_name: str
    detection_time: float
    timestamp: float


class PitchDetector:
    """音高检测算法集合"""

    def __init__(self, sample_rate=44100, frame_length=8192, hop_length=512,
                 f_min=20.0, f_max=5000.0, global_confidence=0.7):
        self.sample_rate = sample_rate
        self.frame_length = frame_length
        self.hop_length = hop_length
        self.f_min = f_min
        self.f_max = f_max
        self.global_confidence = global_confidence
        self.detection_timings = []  # 存储每次检测的计时信息

    # 进度检测相关
    """===================进度检测相关======================="""
    def get_detection_timings(self) -> List[DetectionTiming]:
        """获取所有检测计时信息"""
        return self.detection_timings

    def clear_timings(self):
        """清空计时记录"""
        self.detection_timings.clear()

    def get_algorithm_performance(self) -> dict:
        """获取算法性能统计"""
        performance = {}
        for timing in self.detection_timings:
            algo = timing.algorithm_name
            if algo not in performance:
                performance[algo] = {
                    'total_time': 0.0,
                    'count': 0,
                    'average_time': 0.0
                }
            performance[algo]['total_time'] += timing.detection_time
            performance[algo]['count'] += 1

        for algo, stats in performance.items():
            stats['average_time'] = stats['total_time'] / stats['count']

        return performance

    """===================进度检测相关======================="""

    # 各种音高检测算法
    """============各种音高检测算法================="""
    def detect_pyin_basic(self, audio_data: np.ndarray, target_freq: Optional[float] = None) -> Optional[
        PitchDetectionResult]:
        """基础PYIN算法"""
        try:
            f0, voiced_flag, voiced_probs = librosa.pyin(
                y=audio_data,
                fmin=self.f_min,
                fmax=self.f_max,
                sr=self.sample_rate,
                frame_length=self.frame_length,
                hop_length=self.hop_length,
                fill_na=0.0
            )

            valid_f0 = f0[voiced_flag & (f0 > 0)]
            valid_probs = voiced_probs[voiced_flag & (f0 > 0)]

            if len(valid_f0) == 0:
                return None

            best_idx = np.argmax(valid_probs)
            frequency = valid_f0[best_idx]
            confidence = valid_probs[best_idx]

            if confidence > self.global_confidence and self.f_min <= frequency <= self.f_max:
                return PitchDetectionResult(frequency, confidence, "pyin_basic")
            return None
        except Exception as e:
            print(f"PYIN基础算法错误: {e}")
            return None

    def detect_pyin_enhanced(self, audio_data: np.ndarray, target_freq: Optional[float] = None) -> Optional[
        PitchDetectionResult]:
        """增强PYIN算法"""
        try:
            if len(audio_data) < self.frame_length:
                return None

            rms_energy = np.sqrt(np.mean(audio_data ** 2))
            if rms_energy < 0.000005:
                return None

            f0, voiced_flag, voiced_probs = librosa.pyin(
                y=audio_data,
                fmin=self.f_min,
                fmax=self.f_max,
                sr=self.sample_rate,
                frame_length=self.frame_length,
                hop_length=self.hop_length,
                fill_na=0.0,
                center=False
            )

            if f0 is None or len(f0) == 0:
                return None

            valid_mask = voiced_flag & (f0 > self.f_min) & (f0 < self.f_max)
            if not np.any(valid_mask):
                return None

            valid_f0 = f0[valid_mask]
            valid_probs = voiced_probs[valid_mask]

            best_idx = np.argmax(valid_probs)
            frequency = valid_f0[best_idx]
            confidence = valid_probs[best_idx]

            return PitchDetectionResult(frequency, confidence, "pyin_enhanced")
        except Exception as e:
            print(f"PYIN增强算法错误: {e}")
            return None

    def detect_yin(self, audio_data: np.ndarray, target_freq: Optional[float] = None) -> Optional[PitchDetectionResult]:
        """YIN算法"""
        try:
            if len(audio_data) < self.frame_length:
                padding = np.zeros(self.frame_length - len(audio_data))
                audio_data = np.concatenate([audio_data, padding])

            rms_energy = np.sqrt(np.mean(audio_data ** 2))
            if rms_energy < 0.000001:
                return None

            f0 = librosa.yin(
                y=audio_data,
                fmin=self.f_min,
                fmax=self.f_max,
                sr=self.sample_rate,
                frame_length=self.frame_length,
                hop_length=self.hop_length,
                trough_threshold=0.2
            )

            valid_f0 = f0[(f0 > self.f_min) & (f0 < self.f_max) & (f0 > 0)]
            if len(valid_f0) == 0:
                return None

            # 异常值过滤
            if len(valid_f0) > 3:
                Q1 = np.percentile(valid_f0, 25)
                Q3 = np.percentile(valid_f0, 75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                filtered_f0 = valid_f0[(valid_f0 >= lower_bound) & (valid_f0 <= upper_bound)]
                if len(filtered_f0) > 0:
                    valid_f0 = filtered_f0

            # 使用trimmed mean
            if len(valid_f0) >= 5:
                trim_count = max(1, len(valid_f0) // 10)
                sorted_f0 = np.sort(valid_f0)
                trimmed_f0 = sorted_f0[trim_count:-trim_count]
                frequency = np.mean(trimmed_f0)
            else:
                frequency = np.median(valid_f0)

            if not (self.f_min <= frequency <= self.f_max):
                return None

            # 计算置信度
            if len(valid_f0) > 1:
                consistency = 1.0 - min(1.0, np.std(valid_f0) / frequency)
                confidence = max(0.1, consistency * 0.8)
            else:
                confidence = 0.5

            return PitchDetectionResult(frequency, confidence, "yin")
        except Exception as e:
            print(f"YIN算法错误: {e}")
            return None

    def detect_hps(self, audio_data: np.ndarray, target_freq: Optional[float] = None) -> Optional[PitchDetectionResult]:
        """谐波乘积谱算法"""
        try:
            if len(audio_data) < self.frame_length:
                return None

            rms_energy = np.sqrt(np.mean(audio_data ** 2))
            if rms_energy < 0.000005:
                return None

            # 加窗
            window = np.hanning(len(audio_data))
            windowed_data = audio_data * window

            # 计算FFT
            fft_data = np.abs(np.fft.rfft(windowed_data))
            freqs = np.fft.rfftfreq(len(audio_data), 1.0 / self.sample_rate)

            # 移除DC分量
            min_bin = max(1, int(self.f_min * len(audio_data) / self.sample_rate))
            fft_data[:min_bin] = 0

            # 谐波乘积谱
            hps = fft_data.copy()
            for harmonic in [2, 3, 4]:
                decimated = self._decimate_spectrum(fft_data, harmonic)
                min_len = min(len(hps), len(decimated))
                hps[:min_len] *= decimated[:min_len]

            # 在合理范围内寻找峰值
            valid_mask = (freqs >= 50) & (freqs <= 2000)
            valid_freqs = freqs[valid_mask]
            valid_hps = hps[valid_mask]

            if len(valid_freqs) == 0:
                return None

            peak_idx = np.argmax(valid_hps)
            frequency = valid_freqs[peak_idx]

            # 二次插值
            if 0 < peak_idx < len(valid_hps) - 1:
                alpha = valid_hps[peak_idx - 1]
                beta = valid_hps[peak_idx]
                gamma = valid_hps[peak_idx + 1]
                if alpha - 2 * beta + gamma != 0:
                    p = 0.5 * (alpha - gamma) / (alpha - 2 * beta + gamma)
                    frequency = valid_freqs[peak_idx] + p * (valid_freqs[1] - valid_freqs[0])

            if not (80 <= frequency <= 1000):
                return None

            # 计算置信度
            sorted_peaks = np.sort(valid_hps)
            if len(sorted_peaks) >= 2:
                peak_prominence = (valid_hps[peak_idx] - sorted_peaks[-2]) / (valid_hps[peak_idx] + 1e-8)
                confidence = 0.3 + min(0.7, peak_prominence * 2)
            else:
                confidence = 0.5

            return PitchDetectionResult(frequency, confidence, "hps")
        except Exception as e:
            print(f"HPS算法错误: {e}")
            return None

    def _decimate_spectrum(self, spectrum: np.ndarray, factor: int) -> np.ndarray:
        """降采样频谱"""
        new_length = len(spectrum) // factor
        return spectrum[:new_length * factor].reshape(new_length, factor).max(axis=1)

    def detect_autocorr(self, audio_data: np.ndarray, target_freq: Optional[float] = None) -> Optional[
        PitchDetectionResult]:
        """自相关算法"""
        try:
            if len(audio_data) < self.frame_length:
                return None

            rms_energy = np.sqrt(np.mean(audio_data ** 2))
            if rms_energy < 0.000005:
                return None

            # 中心削波
            threshold = 0.1 * np.max(np.abs(audio_data))
            clipped_data = np.clip(audio_data, -threshold, threshold)

            # 计算自相关
            autocorr = np.correlate(clipped_data, clipped_data, mode='full')
            autocorr = autocorr[len(autocorr) // 2:]

            # 寻找基频峰值
            min_period = max(1, int(self.sample_rate / 1000))
            max_period = min(len(autocorr) // 2, int(self.sample_rate / 50))

            if max_period <= min_period:
                return None

            search_region = autocorr[min_period:max_period]
            peak_idx = np.argmax(search_region) + min_period

            # 验证峰值显著性
            main_peak = autocorr[peak_idx]
            noise_floor = np.mean(autocorr[max_period:min(max_period + 100, len(autocorr))])

            if main_peak < noise_floor * 1.5:
                return None

            # 抛物线插值
            if peak_idx > 0 and peak_idx < len(autocorr) - 1:
                alpha = autocorr[peak_idx - 1]
                beta = autocorr[peak_idx]
                gamma = autocorr[peak_idx + 1]
                denominator = alpha - 2 * beta + gamma
                if denominator != 0:
                    p = 0.5 * (alpha - gamma) / denominator
                    period = peak_idx + p
                else:
                    period = peak_idx
            else:
                period = peak_idx

            frequency = self.sample_rate / period if period > 0 else 0

            if not (80 <= frequency <= 1000):
                return None

            confidence = 0.4 + 0.3 * min(1.0, (main_peak - noise_floor) / main_peak)

            return PitchDetectionResult(frequency, confidence, "autocorr")
        except Exception as e:
            print(f"自相关算法错误: {e}")
            return None

    def detect_adaptive(self, audio_data: np.ndarray, target_freq: Optional[float] = None) -> Optional[
        PitchDetectionResult]:
        """自适应算法 - 组合多种方法"""
        # 尝试多种算法
        results = []

        methods = [
            self.detect_pyin_enhanced,
            self.detect_yin,
            self.detect_hps,
            self.detect_autocorr
        ]

        for method in methods:
            result = method(audio_data, target_freq)
            if result and result.confidence > 0.5:
                results.append(result)

        if not results:
            return None

        # 返回置信度最高的结果
        best_result = max(results, key=lambda x: x.confidence)
        best_result.method_used = f"adaptive({best_result.method_used})"
        return best_result