
import numpy as np
from typing import Dict, Any
import math

class MechanicsEngine:
    """
    MechanicsEngine（含静/动摩擦的 stick-slip 行为，静动联动版）
    用户输入：v_user = dD/dt (m/s)
    接口： state = update(v_user, dt)
    返回：{"theta","omega","displacement","tension","frequency","v_user"}
    """

    def __init__(self,
                 L:float =  0.54,
                 mu:float = 0.00042,
                 I: float = 0.002,        # 转动惯量 I
                 k: float = 20.0,         # 等效刚度 k
                 r: float = 0.01,         # 半径 r
                 Sigma_valid:float = 210000,
                 k_d: float = 5,
                 sigma: float = 0.001,    # 粘滞阻尼 σ
                 tau_fric_limit_0:float = -0.1,
                 alpha:float = 0.05,
                 gamma:float = 0.9,       # ⬅ 新增：动摩擦比例 γ
                 v_user:float = 0.0
                 ):

        # 基本物理参数
        self.L = L
        self.mu = mu
        self.I = I
        self.k = k
        self.r = r
        self.Sigma_valid= Sigma_valid
        self.k_d = k_d

        # 摩擦参数
        self.sigma = sigma
        self.tau_fric_limit_0 = tau_fric_limit_0
        self.alpha = alpha
        self.gamma = gamma   # ⬅ 动摩擦比例（0.6~0.95）

        # 状态
        self.theta = 0.0
        self.omega = 0.0
        self.v_user = v_user
        self.theta_init = 0.0

        self.omega_eps = 1e-3   # 静止阈值


    # ======================================================
    # 公共方法
    # ======================================================

    def update_physical_params(self, params: Dict[str, Any]):
        """从 MainWindow 更新全局物理参数"""

        self.I = params.get('mech_I', self.I)
        self.r = params.get('mech_r', self.r)
        self.k = params.get('mech_k', self.k)
        self.Sigma_valid = params.get('mech_Sigma_valid', self.Sigma_valid)
        self.k_d = params.get('mech_Kd', self.k_d)

        # 摩擦参数
        self.tau_fric_limit_0 = params.get('mech_fric_limit_0', self.tau_fric_limit_0)
        self.alpha = params.get('mech_alpha', self.alpha)
        self.gamma = params.get('mech_gamma', self.gamma)   # ← 新增
        self.sigma = params.get('mech_sigma', self.sigma)

        # 保持当前频率不变
        current_freq = self.get_frequency()
        if current_freq > 0.0:
            self.set_initial_state_by_frequency(current_freq)

    def set_initial_state_by_frequency(self, target_freq: float):
        """
        根据目标频率 f_target (Hz)，计算所需的初始弦轴角度 theta。
        计算公式：theta = (L^2 * f^2 * mu) / (k * r^2)
        """
        if target_freq <= 0.0:
            # 目标频率无效，重置到零角度
            self.theta_init = 0.0
        else:
            # 计算目标频率所需的 theta
            try:
                # 使用公式：theta = (L^2 * f^2 * mu) / (k * r^2)
                numerator = (self.L**2) * (target_freq**2) * self.mu
                denominator = self.k * (self.r**2)

                if denominator == 0:
                    self.theta_init = 0.0
                else:
                    self.theta_init = numerator / denominator
            except ZeroDivisionError:
                self.theta_init = 0.0

        # 设置当前状态为新的初始状态（即目标频率）
        self.reset(theta=self.theta_init, omega=0.0)


    def reset(self, theta: float = 0.0, omega: float = 0.0):
        if theta == 0.0 and self.theta_init != 0.0:
            self.theta = self.theta_init
        else:
            self.theta = theta
        self.omega = omega


    def calculate_theta_for_frequency(self,freq:float):
        if freq <= 0.0:
            return 0.0
        denom = self.k * (self.r ** 2)
        if denom == 0:
            return 0.0
        return (self.L ** 2) * (freq ** 2) * self.mu / denom

    def _compute_theta_loose_threshold(self):
        """
        根据静态松弦条件 kr^2 * theta < tau0 + alpha * theta
        → (k r^2 - alpha) * theta < tau0
        注意：我们必须满足 (k r^2 - alpha) < 0 才会出现松弦区
        """
        den = self.k * (self.r ** 2) - self.alpha
        if den >= 0:
            return None  # 永远不会松弦
        return self.tau_fric_limit_0 / den  # 正数阈值（因为 tau0<0, den<0）


    # ======================================================
    # 基本物理转换
    # ======================================================

    def get_displacement(self) -> float:
        return self.r * self.theta

    def get_tension(self) -> float:
        return max(0.0, 4 * self.k * (self.r**2) * abs(self.theta))

    def get_frequency(self) -> float:
        F = self.get_tension()
        if F <= 0.0:
            return 0.0
        return (1.0 / (2.0 * self.L)) * np.sqrt(F / self.mu)


    # ======================================================
    # 摩擦模型（统一版本）
    # ======================================================

    def _string_torque(self, theta: float) -> float:
        return - self.k * (self.r ** 2) * theta

    def _drive_torque(self, omega: float, v_user: float) -> float:
        return self.k_d * v_user

    def _compute_friction_limits(self, theta: float):
        """
        计算静摩擦极限与动摩擦（联动）
        """
        tau_static_limit = abs(self.tau_fric_limit_0 + self.alpha * theta)
        tau_kinetic_limit = self.gamma * tau_static_limit
        return tau_static_limit, tau_kinetic_limit


    # ======================================================
    # 内部动力学（stick-slip 核心）
    # ======================================================

    def _dynamics(self, state, v_user):
        theta, omega = state

        tau_str = self._string_torque(theta)
        tau_input = self._drive_torque(omega, v_user)
        tau_net = tau_str + tau_input

        tau_static_limit, tau_kinetic_limit = self._compute_friction_limits(theta)
        viscous = self.sigma * omega

        # ======= 静止区 =======
        if abs(omega) < self.omega_eps:

            # 静摩擦可以完全抵消 → 维持静止
            if abs(tau_net) <= tau_static_limit:
                return np.array([0.0, 0.0])

            # 超过静摩擦极限 → 滑动
            tau_fric = -np.sign(tau_net) * tau_kinetic_limit - viscous
            alpha = (tau_net + tau_fric) / self.I
            return np.array([omega, alpha])

        # ======= 运动区 =======
        else:
            tau_fric = -np.sign(omega) * tau_kinetic_limit - viscous
            alpha = (tau_net + tau_fric) / self.I
            return np.array([omega, alpha])


    # ======================================================
    # 主更新接口
    # ======================================================

    def update(self, v_user: float, dt: float = 0.01) -> Dict[str, Any]:

        self.v_user = v_user
        y = np.array([self.theta, self.omega], dtype=float)

        # RK4
        k1 = self._dynamics(y, v_user)
        k2 = self._dynamics(y + 0.5 * dt * k1, v_user)
        k3 = self._dynamics(y + 0.5 * dt * k2, v_user)
        k4 = self._dynamics(y + dt * k3, v_user)

        y_next = y + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        self.theta, self.omega = float(y_next[0]), float(y_next[1])

        # 钳制 theta >= 0
        if self.theta < 0.0:
            self.theta = 0.0
            self.omega = 0.0

        if abs(self.omega) < 1e-8:
            self.omega = 0.0

        # 松弦判据
        den = self.k * (self.r ** 2) - self.alpha
        if den < 0:
            theta_loose = self.tau_fric_limit_0 / den
            loose = self.theta < theta_loose
        else:
            theta_loose = None
            loose = False

        # 断弦
        tension_limit = self.Sigma_valid * math.pi * (self.r ** 2)
        broken = (self.get_tension() > tension_limit)

        return {
            "theta": self.theta,
            "omega": self.omega,
            "displacement": self.get_displacement(),
            "tension": self.get_tension(),
            "frequency": self.get_frequency(),
            "v_user": v_user,
            "loose": loose,
            "theta_loose_threshold": theta_loose,
            "broken": broken,
            "max_tension": tension_limit
        }

