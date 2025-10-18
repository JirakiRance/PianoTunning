import numpy as np
from typing import Dict, Any


class SimplePianoMechanics:
    """简化版钢琴力学引擎"""

    def __init__(self,inertia:float=1.0,viscous_coeff:float=0.1,init_displacement:float=100.0):
        # 力学参数
        self.__inertia=inertia  # 转动惯量 I
        self.__viscous_coeff=viscous_coeff  # 粘滞摩擦系数 σ
        # 摩擦等级参数
        self.friction_levels = {
            "off": {"static_scale": 0.0, "kinetic_scale": 0.0},
            "light": {"static_scale": 0.3, "kinetic_scale": 0.2},
            "standard": {"static_scale": 0.6, "kinetic_scale": 0.4},
            "realistic": {"static_scale": 1.0, "kinetic_scale": 0.6}
        }
        # 状态变量
        self.__displacement = init_displacement  # 虚拟位移 D
        self.__velocity = 0.0  # 速度
        self.__current_friction_level = "standard"
        # 校准参数
        self.__C0 = None  # 全局校准常数(只能单键校准)

    def set_calibration(self, C0: float):
        """设置校准参数"""
        self.__C0 = C0

    def set_friction_level(self, level: str):
        """设置摩擦等级"""
        if level in self.friction_levels:
            self.__current_friction_level = level
        else:
            print(f"未知摩擦等级: {level}，使用标准模式")
            self.__current_friction_level = "standard"

    def compute_string_torque(self) -> float:
        """计算弦张力扭矩 T_string = -4 × C₀² × D"""
        if self.__C0 is None:
            return 0.0
        return -4 * self.__C0 ** 2 * self.__displacement

    def compute_friction_torque(self, user_torque: float) -> float:
        """计算摩擦力矩 - 简化模型"""
        if self.__current_friction_level == "off":
            return 0.0
        # 摩擦模型的参数 static_scale和kinetic_scale
        friction_params = self.friction_levels[self.__current_friction_level]
        # 计算弦张力
        string_torque = self.compute_string_torque()
        # 基础摩擦值（基于当前张力）
        base_friction = 0.5 + 0.1 * abs(string_torque)
        kinetic_friction = base_friction * friction_params["kinetic_scale"]
        static_threshold = base_friction * friction_params["static_scale"]

        # 静止状态
        if abs(self.__velocity) < 0.01:
            net_force = user_torque + string_torque
            if abs(net_force) < static_threshold:
                # 完全锁死
                return -net_force
            else:
                # 突破静摩擦
                return -kinetic_friction * (1 if net_force > 0 else -1)
        # 运动状态
        else:
            return (-kinetic_friction * (1 if self.__velocity > 0 else -1)
                    - self.__viscous_coeff * self.__velocity)

    def update(self, user_torque: float, dt: float) -> Dict[str, Any]:
        """更新力学状态"""
        # 计算各项扭矩
        string_torque = self.compute_string_torque()
        friction_torque = self.compute_friction_torque(user_torque)
        # 总扭矩
        total_torque = user_torque + string_torque + friction_torque
        # 更新运动状态（欧拉积分）
        acceleration = total_torque / self.__inertia
        self.__velocity += acceleration * dt
        self.__displacement += self.__velocity * dt

        # 确保位移不为负
        self.__displacement = max(0.0, self.__displacement)

        # 小速度时自动停止（避免数值振荡）
        if abs(self.__velocity) < 0.001 and abs(total_torque) < 0.1:
            self.__velocity = 0.0

        return {
            "displacement": self.__displacement,
            "velocity": self.__velocity,
            "acceleration": acceleration,
            "string_torque": string_torque,
            "friction_torque": friction_torque,
            "total_torque": total_torque
        }
    # 频率预测
    def predict_frequency(self, string_length: float, string_density: float) -> float:
        """预测当前位移对应的频率 - 修正版"""
        if self.__C0 is None:
            print("错误: 系统未校准，无法预测频率")
            return 0.0
        try:
            # 正确公式: f = (C₀ / (L × √μ)) × √D
            frequency = (self.__C0 / (string_length * np.sqrt(string_density))) * np.sqrt(self.__displacement)
            # 调试信息
            print(f"频率预测调试:")
            print(f"  C0 = {self.__C0:.4f}")
            print(f"  L = {string_length:.4f}m")
            print(f"  μ = {string_density:.6f} kg/m")
            print(f"  D = {self.__displacement:.2f}")
            print(f"  √D = {np.sqrt(self.__displacement):.4f}")
            print(f"  预测频率 = {frequency:.2f}Hz")
            return frequency

        except Exception as e:
            print(f"频率预测错误: {e}")
            return 0.0

    def get_tension(self) -> float:
        """获取当前弦张力"""
        if self.__C0 is None:
            return 0.0
        return 4 * self.__C0 ** 2 * self.__displacement
    def __get_displacement(self):
        return self.__displacement
    def set_displacement(self, displacement: float):
        self.__displacement=displacement
    def set_velocity(self, velocity: float):
        self.__velocity=velocity

    def reset(self, initial_displacement: float = 100.0):
        """重置状态"""
        self.__displacement = initial_displacement
        self.__velocity = 0.0


"""==========================class MechanicsEngine====================================="""

# 测试代码
def test_simple_mechanics():
    """测试简化力学模型"""
    mechanics = SimplePianoMechanics()

    # 设置校准参数（假设通过校准得到）
    mechanics.set_calibration(C0=0.02)  # 示例值

    print("测试简化力学模型")
    print("=" * 50)

    # 测试不同摩擦等级
    for level in ["off", "light", "standard", "realistic"]:
        print(f"\n摩擦等级: {level}")
        mechanics.set_friction_level(level)
        mechanics.reset(100.0)

        # 模拟拧紧过程
        dt = 0.01
        print("时间(s) | 位移 | 速度 | 张力(N)")
        print("-" * 40)

        for i in range(50):
            # 前0.2秒施加扭矩，后0.3秒释放
            user_torque = 8.0 if i < 20 else 0.0
            state = mechanics.update(user_torque, dt)

            if i % 10 == 0:
                tension = mechanics.get_tension()
                print(f"{i * dt:5.2f} | {state['displacement']:6.1f} | {state['velocity']:6.2f} | {tension:6.1f}")

    # 测试频率预测
    print(f"\n频率预测测试:")
    mechanics.set_displacement(200.0)
    frequency = mechanics.predict_frequency(string_length=0.5, string_density=0.001)
    print(f"位移 {mechanics.__displacement:.1f} -> 频率 {frequency:.1f}Hz")
    print(f"弦张力: {mechanics.get_tension():.1f}N")


if __name__ == "__main__":
    test_simple_mechanics()