import numpy as np
from typing import Dict, Any, Optional,Tuple
from dataclasses import dataclass
import time

# 定义状态空间变量
@dataclass
class TuningState:
    """拧弦轴的当前状态"""
    theta: float = 0.0              # 角度 (rad)
    omega: float = 0.0              # 角速度 (rad/s)
    string_tension: float = 0.0     # 弦张力 (N)


class MechanicalEngine:
    """
    基于完整物理模型的钢琴调律力学引擎。
    使用四阶龙格-库塔法 (RK4) 进行数值积分。
    """
    def __init__(self, dt: float = 1 / 60):
        self.dt = dt  # 时间步长 (秒)

        # 从 MainWindow 加载的参数 (使用默认值)
        self.I = 0.0001  # 转动惯量 (kg·m²)
        self.r = 0.005  # 弦轴半径 (m)
        self.k = 500000.0  # 弦劲度系数 (N/m) (报告中F_string=-k * ΔL，这里简化为张力随角度变化)
        self.Kd = 0.5  # 施力敏感度 K_D

        # 摩擦参数 (限幅摩擦模型)
        self.tau_fric_limit_0 = 0.1  # 初始静摩擦极限
        self.alpha = 0.05  # 静摩擦增长系数
        self.tau_kinetic = 0.08  # 动摩擦扭矩
        self.sigma = 0.001  # 粘性摩擦系数
        self.epsilon = 1e-3  # 静止速度阈值

        # 状态
        self.state = TuningState()
        self.initial_tension = 0.0  # 初始张力 (调律开始时的张力)

        # 钢琴物理参数 (由外部提供，每次调律会改变)
        self.L = 0.54  # 弦长 (m) (A4 示例值)
        self.mu = 0.00042  # 线密度 (kg/m) (A4 示例值)

    def update_physical_params(self, params: Dict[str, Any]):
        """从 MainWindow 更新全局物理参数"""
        self.I = params.get('mech_I', self.I)
        self.r = params.get('mech_r', self.r)
        self.k = params.get('mech_k', self.k)
        self.Kd = params.get('mech_Kd', self.Kd)

        self.tau_fric_limit_0 = params.get('mech_fric_limit_0', self.tau_fric_limit_0)
        self.alpha = params.get('mech_alpha', self.alpha)
        self.tau_kinetic = params.get('mech_kinetic', self.tau_kinetic)
        self.sigma = params.get('mech_sigma', self.sigma)

    def initialize_tuning(self, current_freq: float, target_freq: float, target_key_L: float, target_key_mu: float):
        """
        开始调律前初始化状态。
        根据当前频率反推初始张力，并计算初始角度 theta_initial。
        """
        self.L = target_key_L
        self.mu = target_key_mu

        # 1. 计算初始张力 F_initial
        self.initial_tension = self.mu * (2 * self.L * current_freq) ** 2

        # 2. 计算目标张力 F_target
        F_target = self.mu * (2 * self.L * target_freq) ** 2

        # 3. 计算产生 F_initial 所需的初始角度 theta_initial (相对于零张力状态)
        # F = k * ΔL = k * r * θ  => θ = F / (k * r)
        if self.k * self.r == 0:
            theta_initial = 0.0
        else:
            theta_initial = self.initial_tension / (self.k * self.r)

        # 4. 计算产生 F_target 所需的目标角度 theta_target
        self.theta_target = F_target / (self.k * self.r)

        # 5. 重置状态
        self.state = TuningState(
            theta=theta_initial,
            omega=0.0,
            string_tension=self.initial_tension
        )
        print(
            f"力学引擎初始化: F_init={self.initial_tension:.1f}N, θ_init={np.degrees(theta_initial):.2f}°, θ_target={np.degrees(self.theta_target):.2f}°")

    def _calculate_tension_torque(self, theta: float) -> float:
        """
        计算弦张力 F_string 和由此产生的扭矩 τ_string。
        张力始终为：F_string = k * r * θ
        扭矩 τ_string = -F_string * r
        """
        # F_string = k * r * θ
        current_tension = self.k * self.r * theta
        # τ_string = -F_string * r
        tau_string = -current_tension * self.r
        # 更新状态中的张力
        self.state.string_tension = current_tension
        return tau_string

    def _calculate_friction_torque(self, theta: float, omega: float, tau_net_no_fric: float) -> float:
        """
        计算限幅摩擦扭矩 (Stribeck 模型简化版 - 仅限幅)。
        根据报告中的摩擦模型。
        """
        tau_fric_limit = self.tau_fric_limit_0 + self.alpha * abs(theta)  # 摩擦极限随角度/张力增加
        if abs(omega) < self.epsilon:
            # 静止情况
            if abs(tau_net_no_fric) <= tau_fric_limit:
                # 摩擦抵消合力，保持静止
                return -tau_net_no_fric
            else:
                # 摩擦达到极限，系统开始运动
                return -np.sign(tau_net_no_fric) * tau_fric_limit
        else:
            # 运动情况
            # 动摩擦扭矩 = -sign(omega) * τ_kinetic - σ * ω
            return -np.sign(omega) * self.tau_kinetic - self.sigma * omega

    def _calculate_derivatives(self, state: TuningState, tau_input: float) -> Tuple[float, float]:
        """
        计算状态空间微分项：d(theta)/dt 和 d(omega)/dt。
        控制方程：I * d²θ/dt² = τ_input + τ_string + τ_fric
        """
        theta, omega = state.theta, state.omega

        # 1. 计算弦张力扭矩
        tau_string = self._calculate_tension_torque(theta)

        # 2. 计算无摩擦时的合扭矩 (用于摩擦判断)
        tau_net_no_fric = tau_input + tau_string

        # 3. 计算摩擦扭矩
        tau_fric = self._calculate_friction_torque(theta, omega, tau_net_no_fric)

        # 4. 计算总合扭矩
        tau_net = tau_net_no_fric + tau_fric

        # 5. 计算角加速度
        d2theta_dt2 = tau_net / self.I if self.I > 0 else 0.0

        dtheta_dt = omega
        domega_dt = d2theta_dt2

        return dtheta_dt, domega_dt

    def step_rk4(self, tau_input: float) -> TuningState:
        """
        使用四阶龙格-库塔法 (RK4) 进行一步积分。

        """
        dt = self.dt

        # 准备初始状态向量 [theta, omega]
        y = np.array([self.state.theta, self.state.omega])

        # RK4 计算步骤
        def f(state_vec, tau_input):
            state = TuningState(theta=state_vec[0], omega=state_vec[1])
            dtheta, domega = self._calculate_derivatives(state, tau_input)
            return np.array([dtheta, domega])

        k1 = dt * f(y, tau_input)
        k2 = dt * f(y + 0.5 * k1, tau_input)
        k3 = dt * f(y + 0.5 * k2, tau_input)
        k4 = dt * f(y + k3, tau_input)

        y_next = y + (k1 + 2 * k2 + 2 * k3 + k4) / 6.0

        # 更新状态
        self.state.theta = y_next[0]
        self.state.omega = y_next[1]

        # 额外更新张力（确保状态完整）
        self._calculate_tension_torque(self.state.theta)

        # 检查是否因为摩擦而停止
        if abs(self.state.omega) < self.epsilon:
            # 如果合扭矩低于静摩擦极限，强制 omega=0
            # 这一步保证了物理静止的精确性，但需要重新计算合扭矩
            # 简化：如果RK4结果已经接近静止，我们接受静止
            if abs(y_next[1]) < self.epsilon:
                self.state.omega = 0.0

        return self.state

    def get_current_frequency(self) -> float:
        """根据当前张力计算琴弦频率"""
        # 弦振动方程：f = 1/(2L) * sqrt(F_string / μ)
        if self.state.string_tension <= 0 or self.mu <= 0 or self.L <= 0:
            return 0.0

        frequency = (1.0 / (2.0 * self.L)) * np.sqrt(self.state.string_tension / self.mu)
        return frequency
