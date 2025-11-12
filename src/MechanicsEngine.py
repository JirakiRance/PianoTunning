
import numpy as np
from typing import Dict, Any
from PianoGenerator import PianoKey

class MechanicsEngine:
    """
    MechanicsEngine（含静/动摩擦的 stick-slip 行为）
    用户输入：v_user = dD/dt (m/s)
    接口： state = update(v_user, dt)
    返回：{"theta","omega","displacement","tension","frequency","v_user"}
    """

    def __init__(self,
                 L:float =  0.54,
                 mu:float = 0.00042,
                 I: float = 0.002,     # 转动惯量 I
                 k: float = 20.0,    # 等效刚度 k
                 r: float = 0.01,    # 半径 r
                 k_d: float = 5,     # 驱动增益 k_d
                 sigma: float = 0.001,# 粘滞阻尼 σ
                 tau_fric_limit_0:float=-0.1,
                 alpha:float =0.05,
                 tau_kinetic:float=0.08,
                 v_user:float = 0.0
                 ):
        # 基本物理参数
        self.L = L
        self.mu = mu
        self.I = I
        self.k = k
        self.r = r
        self.k_d = k_d
        # 摩擦参数
        self.sigma = sigma
        self.tau_fric_limit_0 =tau_fric_limit_0
        self.tau_kinetic=tau_kinetic
        self.alpha = alpha
        # 状态
        self.theta = 0.0
        self.omega = 0.0
        self.v_user = v_user
        self.theta_init=0.0

        # 其他控制
        self.omega_eps = 1e-3   # 视为静止的角速度阈值

    # -------------------------
    # 公共方法
    # -------------------------

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

    def update_physical_params(self, params: Dict[str, Any]):
        """从 MainWindow 更新全局物理参数"""
        self.I = params.get('mech_I', self.I)
        self.r = params.get('mech_r', self.r)
        self.k = params.get('mech_k', self.k)
        self.k_d = params.get('mech_Kd', self.k_d)

        self.tau_fric_limit_0 = params.get('mech_fric_limit_0', self.tau_fric_limit_0)
        self.alpha = params.get('mech_alpha', self.alpha)
        self.tau_kinetic = params.get('mech_kinetic', self.tau_kinetic)
        self.sigma = params.get('mech_sigma', self.sigma)

        current_freq = self.get_frequency()
        if current_freq > 0.0:
            # 尝试保持当前频率不变，重新计算 theta_init
            self.set_initial_state_by_frequency(current_freq)

    def reset(self, theta: float = 0.0, omega: float = 0.0):
        """重置状态：允许指定一个初始 theta，否则使用计算出的 self.theta_init"""
        if theta == 0.0 and self.theta_init != 0.0:
             self.theta = self.theta_init
        else:
             self.theta = theta
        self.omega = omega

    def get_displacement(self) -> float:
        return self.r * self.theta

    def get_tension(self) -> float:
        # 保证非负张力（物理上不能为负）
        return max(0.0, 4.0 * self.k * (self.r ** 2) * self.theta)

    def get_frequency(self) -> float:
        F = self.get_tension()
        if F <= 0.0:
            return 0.0
        return (1.0 / (2.0 * self.L)) * np.sqrt(F / self.mu)

    # -------------------------
    # 内部力矩计算
    # -------------------------
    def _string_torque(self, theta: float) -> float:
        # 回复力矩（让 theta 趋向于某个值，由弦张力决定）
        # 负号：theta 正则弦产生拉回力矩为负
        return - self.k * (self.r ** 2) * theta

    def _drive_torque(self, omega: float, v_user: float) -> float:
        # 速度差控制：驱动力矩 = k_d * r * (v_user - r * omega)
        # return self.k_d * self.r * (v_user - self.r * omega)
        return self.k_d * v_user

    def _friction_torque_kinetic(self, omega: float, tau_kin: float) -> float:
        # 运动中的摩擦：动摩擦常值 + 粘滞阻尼
        return - np.sign(omega) * tau_kin - self.sigma * omega
    def _friction_torque_static(self, theta: float) -> float:
        return self.tau_fric_limit_0 + alpha * self.theta

    # -------------------------
    # 动力学方程及RK4积分
    # -------------------------
    def _dynamics(self, state, v_user):
        theta, omega = state
        tau_str = self._string_torque(theta)
        tau_drive = self._drive_torque(omega, v_user)

        # 获取静/动摩擦阈值
        tau_static, tau_kin = self.tau_fric_limit_0 + self.alpha * theta,self.tau_kinetic

        # 若角速度非常小（近静止），尝试判断是否被静摩擦锁住
        if abs(omega) < self.omega_eps:
            # 计算“去摩擦”的合力矩（仅弦力+驱动）
            tau_without_fric = tau_str + tau_drive
            if abs(tau_without_fric) <= tau_static:
                # 被静摩擦锁住：保持不动（omega=0，alpha=0）
                return np.array([0.0, 0.0])
            else:
                # 超过静摩擦阈值 -> 开始运动，采用动摩擦方向与动摩擦量
                tau_fric = - np.sign(tau_without_fric) * tau_kin - self.sigma * omega
                alpha = (tau_str + tau_drive + tau_fric) / self.I
                return np.array([omega, alpha])
        else:
            # 运动状态（正常计算动摩擦）
            tau_fric = self._friction_torque_kinetic(omega, tau_kin)
            alpha = (tau_str + tau_drive + tau_fric) / self.I
            return np.array([omega, alpha])

    def update(self, v_user: float, dt: float = 0.01) -> Dict[str, Any]:
        """
        以 v_user (m/s) 为输入，做一次 RK4 积分步，返回状态字典
        注意：当静摩擦锁住时，返回的 omega 会被保持为0，theta不改变。
        """
        self.v_user = v_user
        y = np.array([self.theta, self.omega], dtype=float)

        # RK4
        k1 = self._dynamics(y, v_user)
        k2 = self._dynamics(y + 0.5 * dt * k1, v_user)
        k3 = self._dynamics(y + 0.5 * dt * k2, v_user)
        k4 = self._dynamics(y + dt * k3, v_user)

        y_next = y + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

        # 如果静摩擦条件在步骤里被判定为锁定，_dynamics 已返回 [0,0]，RK4 结果也会保持
        self.theta, self.omega = float(y_next[0]), float(y_next[1])

        # 🚨 关键修正：角度钳位 - 弦轴角度 theta 必须非负，防止张力归零
        if self.theta < 0.0:
            self.theta = 0.0
            self.omega = 0.0 # 角度归零时，角速度也应归零

        # 小阈值修正：极小速度认为静止（避免数值残留）
        if abs(self.omega) < 1e-8:
            self.omega = 0.0

        return {
            "theta": self.theta,
            "omega": self.omega,
            "displacement": self.get_displacement(),
            "tension": self.get_tension(),
            "frequency": self.get_frequency(),
            "v_user": v_user
        }


# # 简单测试脚本（运行查看输出）
# if __name__ == "__main__":
#     mech = MechanicsEngine(L=0.5, mu=0.001, inertia=0.002,
#                           stiffness=20.0, lever_arm=0.01,
#                           viscous_coeff=0.002, drive_gain=0.6)
#     mech.set_friction_level("realistic")

#     dt = 0.005
#     for i in range(400):
#         # 前 120 步施加正速度，之后停止
#         v = 0.002 if i < 120 else 0.0
#         s = mech.update(v, dt)
#         if i % 20 == 0:
#             print(f"t={i*dt:.3f}s v_user={v:.4f} θ={s['theta']:.6f} ω={s['omega']:.6f} f={s['frequency']:.2f}Hz")

