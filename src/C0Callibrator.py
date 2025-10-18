import numpy as np
from typing import Optional, Callable, Tuple
from AudioDetector import AudioDetector, PitchResult,PitchDetectionAlgorithm
from MechanicsEngine import SimplePianoMechanics


class C0Calibrator:
    """C0参数校准器 - 通过两个数据点计算C0"""
    def __init__(self, audio: AudioDetector, mechanics: SimplePianoMechanics,string_length:float,string_density:float):
        self.audio = audio
        self.mechanics = mechanics
        self.string_length = string_length
        self.string_density = string_density

        # 校准数据
        self.first_frequency: Optional[float] = None
        self.second_frequency: Optional[float] = None
        self.C0: Optional[float] = None

        # 回调函数
        self.on_frequency_detected: Optional[Callable[[float, float, str], None]] = None  # (频率, 置信度, 步骤)
        self.on_calibration_complete: Optional[Callable[[float], None]] = None

    def start_first_measurement(self) -> bool:
        """开始第一次频率测量"""
        print("🎵 开始第一次频率测量...")
        print("请弹奏琴键...")

        success = self.audio.start_realtime_analysis(
            pitch_callback=lambda result: self._on_first_frequency_detected(result),
            save_recording=False
        )

        return success

    def start_second_measurement(self) -> bool:
        """开始第二次频率测量"""
        print("🎵 开始第二次频率测量...")
        print("请弹奏调律后的琴键...")

        success = self.audio.start_realtime_analysis(
            pitch_callback=lambda result: self._on_second_frequency_detected(result),
            save_recording=False
        )

        return success

    def _on_first_frequency_detected(self, pitch_result: PitchResult):
        """第一次频率检测回调"""
        if pitch_result.confidence < self.audio.global_confidence:
            return

        self.first_frequency = pitch_result.frequency
        self.audio.stop_realtime_analysis()

        print(f"✅ 第一次测量完成:")
        print(f"   频率: {self.first_frequency:.2f}Hz")
        print(f"   置信度: {pitch_result.confidence:.3f}")

        if self.on_frequency_detected:
            self.on_frequency_detected(self.first_frequency, pitch_result.confidence, "first")

    def _on_second_frequency_detected(self, pitch_result: PitchResult):
        """第二次频率检测回调"""
        if pitch_result.confidence < 0.7:
            return

        self.second_frequency = pitch_result.frequency
        self.audio.stop_realtime_analysis()

        print(f"✅ 第二次测量完成:")
        print(f"   频率: {self.second_frequency:.2f}Hz")
        print(f"   置信度: {pitch_result.confidence:.3f}")

        if self.on_frequency_detected:
            self.on_frequency_detected(self.second_frequency, pitch_result.confidence, "second")

    def calculate_C0(self, first_displacement: float, second_displacement: float,
                     string_length: float, string_density: float) -> Optional[float]:
        """
        计算C0参数

        参数:
            first_displacement: 第一次测量的虚拟位移
            second_displacement: 第二次测量的虚拟位移  
            string_length: 弦长 (m)
            string_density: 弦线密度 (kg/m)
        """
        if self.first_frequency is None or self.second_frequency is None:
            print("❌ 缺少频率数据，请先完成两次测量")
            return None

        try:
            self.C0= ( (self.first_frequency-self.second_frequency) / (np.sqrt(first_displacement)-np.sqrt(second_displacement)) ) * self.string_length * np.sqrt(self.string_length)
            # 传递给力学引擎
            self.mechanics.set_calibration(self.C0)

            print(f"✅ C0计算完成!")
            print(f"   点1: D={first_displacement}, f={self.first_frequency:.2f}Hz")
            print(f"   点2: D={second_displacement}, f={self.second_frequency:.2f}Hz")
            print(f"   C0 = {self.C0:.6f}")

            if self.on_calibration_complete:
                self.on_calibration_complete(self.C0)

            return self.C0

        except Exception as e:
            print(f"❌ C0计算错误: {e}")
            return None

    def get_measurement_status(self) -> dict:
        """获取测量状态"""
        return {
            "first_frequency": self.first_frequency,
            "second_frequency": self.second_frequency,
            "C0": self.C0
        }

    def reset_measurements(self):
        """重置测量数据"""
        self.first_frequency = None
        self.second_frequency = None
        self.C0 = None
        self.audio.stop_realtime_analysis()
        print("🔃 测量数据已重置")

    def stop_measurement(self):
        """停止当前测量"""
        self.audio.stop_realtime_analysis()
        print("⏹️ 测量已停止")


# 使用示例
def demo_simple_calibration():
    """演示简单的C0校准流程"""

    audio = AudioDetector(input_device=2,pitch_algorithm=PitchDetectionAlgorithm.AUTOCORR)
    mechanics_engine = SimplePianoMechanics()
    calibrator = C0Calibrator(audio, mechanics_engine,string_length=0.5,string_density=0.0001)

    # 设置回调
    def on_frequency_detected(frequency, confidence, step):
        print(f"[{step}] 检测到频率: {frequency:.2f}Hz (置信度: {confidence:.3f})")

    def on_calibration_complete(C0):
        print(f"🎉 校准完成! C0 = {C0:.6f}")
        # 现在力学引擎已经设置了C0，可以进行频率预测等操作

    calibrator.on_frequency_detected = on_frequency_detected
    calibrator.on_calibration_complete = on_calibration_complete

    # 模拟用户操作：
    # 1. 第一次测量
    # calibrator.start_first_measurement()
    # 用户弹奏琴键...
    # 自动获取 first_frequency

    # 2. 第二次测量  
    # calibrator.start_second_measurement()
    # 用户调律后弹奏琴键...
    # 自动获取 second_frequency

    # 3. 计算C0 (用户手动输入两个位移值)
    # C0 = calibrator.calculate_C0(
    #     first_displacement=100.0,    # 用户设置的第一个位移
    #     second_displacement=110.0,   # 用户设置的第二个位移  
    #     string_length=0.112,
    #     string_density=0.00095
    # )


if __name__ == "__main__":
    demo_simple_calibration()