
# import numpy as np
# from typing import Dict, Any


# class MechanicsEngine:
#     """
#     完整版钢琴弦力学模型（基于报告）
#     用户输入的是弦位移速度 v_user = dD/dt
#     -----------------------------------------------------
#     方程：
#         D = r θ
#         I θ¨ = τ_string + τ_fric + τ_drive
#         τ_string = -k r^2 θ
#         τ_drive = k_d * r * (v_user - r θ̇)
#         f = (1/(2L)) * sqrt(F / μ),   F = 4k r^2 θ
#     """

#     def __init__(self,
#                  L: float = 0.5,          # 弦长 (m)
#                  mu: float = 0.001,       # 线密度 (kg/m)
#                  inertia: float = 0.002,  # 转动惯量 I
#                  stiffness: float = 20.0, # 弦等效刚度 k
#                  lever_arm: float = 0.01, # 旋钮半径 r
#                  viscous_coeff: float = 0.001, # 粘滞摩擦 σ
#                  drive_gain: float = 50       # 驱动增益 k_d
#                  ):
#         # 固定参数
#         self.L = L
#         self.mu = mu
#         self.I = inertia
#         self.k = stiffness
#         self.r = lever_arm
#         self.sigma = viscous_coeff
#         self.k_d = drive_gain

#         # 状态变量
#         self.theta = 0.0
#         self.omega = 0.0  # 角速度 θ̇
#         self.v_user = 0.0 # 用户位移速度输入 dD/dt

#         # 摩擦模型参数
#         self.friction_levels = {
#             "off": (0.0, 0.0),
#             "light": (0.002, 0.0015),
#             "standard": (0.005, 0.003),
#             "realistic": (0.008, 0.005)
#         }
#         self.current_friction = "standard"

#     # ======================================================
#     #  公共接口
#     # ======================================================

#     def set_friction_level(self, level: str):
#         if level in self.friction_levels:
#             self.current_friction = level
#         else:
#             print(f"未知摩擦等级 {level}，使用 standard")
#             self.current_friction = "standard"

#     def reset(self, theta: float = 0.0, omega: float = 0.0):
#         self.theta = theta
#         self.omega = omega

#     # ======================================================
#     #  力学计算
#     # ======================================================

#     def get_displacement(self) -> float:
#         return self.r * self.theta

#     def get_tension(self) -> float:
#         """弦张力 F = 4k r^2 θ"""
#         return max(0.0, 4 * self.k * self.r ** 2 * self.theta)

#     def get_frequency(self) -> float:
#         """f = (1/(2L)) * sqrt(F/μ)"""
#         F = self.get_tension()
#         if F <= 0:
#             return 0.0
#         return (1.0 / (2.0 * self.L)) * np.sqrt(F / self.mu)

#     # ======================================================
#     #  扭矩模型
#     # ======================================================

#     def _string_torque(self, theta: float) -> float:
#         return -self.k * self.r ** 2 * theta

#     # def _friction_torque(self, omega: float, net_torque: float) -> float:
#     #     static_fric, kinetic_fric = self.friction_levels[self.current_friction]
#     #     if abs(omega) < 1e-4 and abs(net_torque) < static_fric:
#     #         return -net_torque
#     #     return -np.sign(omega) * kinetic_fric - self.sigma * omega
#     def _friction_torque(self, omega: float) -> float:
#         static_fric, kinetic_fric = self.friction_levels[self.current_friction]
#         if abs(omega) < 1e-4 :
#             return 0.0
#         return -np.sign(omega) * kinetic_fric - self.sigma * omega

#     def _drive_torque(self, omega: float, v_user: float) -> float:
#         """用户速度输入转换为驱动力矩"""
#         return self.k_d * self.r * (v_user - self.r * omega)

#     # ======================================================
#     #  动力学微分方程 & 积分
#     # ======================================================

#     def _dynamics(self, state, v_user):
#         theta, omega = state
#         # τ_string = self._string_torque(theta)
#         # τ_drive = self._drive_torque(omega, v_user)
#         # τ_net = τ_string + τ_drive
#         # τ_fric = self._friction_torque(omega, τ_net)
#         # α = (τ_string + τ_drive + τ_fric) / self.I
#         τ_string = self._string_torque(theta)
#         τ_drive = self._drive_torque(omega, v_user)
#         τ_fric = self._friction_torque(omega)
#         α = (τ_string + τ_drive + τ_fric) / self.I
#         return np.array([omega, α])

#     def update(self, v_user: float, dt: float = 0.01) -> Dict[str, Any]:
#         """执行一帧积分"""
#         self.v_user = v_user
#         y = np.array([self.theta, self.omega])
#         k1 = self._dynamics(y, v_user)
#         k2 = self._dynamics(y + 0.5 * dt * k1, v_user)
#         k3 = self._dynamics(y + 0.5 * dt * k2, v_user)
#         k4 = self._dynamics(y + dt * k3, v_user)
#         y_next = y + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
#         self.theta, self.omega = y_next

#         return {
#             "theta": self.theta,
#             "omega": self.omega,
#             "displacement": self.get_displacement(),
#             "tension": self.get_tension(),
#             "frequency": self.get_frequency(),
#             "v_user": v_user
#         }

# # ===========================================================
# # 测试
# # ===========================================================
# if __name__ == "__main__":
#     mech = MechanicsEngine()
#     mech.set_friction_level("standard")

#     dt = 0.01
#     for i in range(300):
#         # 模拟鼠标前100帧上拉（正速度），后面停止
#         v_user = 0.002 if i < 100 else 0.0
#         s = mech.update(v_user, dt)
#         if i % 20 == 0:
#             print(f"t={i*dt:.2f}s v_user={v_user:.4f} "
#                   f"θ={s['theta']:.4f} ω={s['omega']:.4f} f={s['frequency']:.2f}Hz")






# MechanicsEngine.py
import numpy as np
from typing import Dict, Any

class MechanicsEngine:
    """
    MechanicsEngine（含静/动摩擦的 stick-slip 行为）
    用户输入：v_user = dD/dt (m/s)
    接口： state = update(v_user, dt)
    返回：{"theta","omega","displacement","tension","frequency","v_user"}
    """

    def __init__(self,
                 L: float = 0.5,             # 弦长 (m)
                 mu: float = 0.001,          # 线密度 (kg/m)
                 inertia: float = 0.002,     # 转动惯量 I
                 stiffness: float = 20.0,    # 等效刚度 k
                 lever_arm: float = 0.01,    # 半径 r
                 viscous_coeff: float = 0.001,# 粘滞阻尼 σ
                 drive_gain: float = 5,     # 驱动增益 k_d
                 v_user:float = 0.0
                 ):
        # 基本物理参数
        self.L = L
        self.mu = mu
        self.I = inertia
        self.k = stiffness
        self.r = lever_arm
        self.sigma = viscous_coeff
        self.k_d = drive_gain

        # 状态
        self.theta = 0.0
        self.omega = 0.0
        self.v_user = v_user

        # 摩擦参数集合： (tau_static, tau_kinetic)
        # 数值单位：N·m （扭矩）
        self.friction_levels = {
            "off":        (0.0,   0.0),
            "light":      (0.002, 0.0015),
            "standard":   (0.008, 0.004),
            "realistic":  (0.02,  0.01)
        }
        self.current_friction = "standard"

        # 其他控制
        self.omega_eps = 1e-6   # 视为静止的角速度阈值

    # -------------------------
    # 公共方法
    # -------------------------
    def set_friction_level(self, level: str):
        if level in self.friction_levels:
            self.current_friction = level
        else:
            self.current_friction = "standard"

    def reset(self, theta: float = 0.0, omega: float = 0.0):
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
        return self.k_d * self.r * (v_user - self.r * omega)

    def _friction_torque_kinetic(self, omega: float, tau_kin: float) -> float:
        # 运动中的摩擦：动摩擦常值 + 粘滞阻尼
        return - np.sign(omega) * tau_kin - self.sigma * omega

    # -------------------------
    # 动力学方程及RK4积分
    # -------------------------
    def _dynamics(self, state, v_user):
        theta, omega = state
        tau_str = self._string_torque(theta)
        tau_drive = self._drive_torque(omega, v_user)

        # 获取静/动摩擦阈值
        tau_static, tau_kin = self.friction_levels[self.current_friction]

        # 若角速度非常小（近静止），尝试判断是否被静摩擦锁住
        if abs(omega) < self.omega_eps:
            # 计算“去摩擦”的合力矩（仅弦力+驱动）
            tau_without_fric = tau_str + tau_drive
            if abs(tau_without_fric) <= tau_static:
                # 被静摩擦锁住：保持不动（θ̇=0，加速度=0）
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


# 简单测试脚本（运行查看输出）
if __name__ == "__main__":
    mech = MechanicsEngine(L=0.5, mu=0.001, inertia=0.002,
                          stiffness=20.0, lever_arm=0.01,
                          viscous_coeff=0.002, drive_gain=0.6)
    mech.set_friction_level("realistic")

    dt = 0.005
    for i in range(400):
        # 前 120 步施加正速度，之后停止
        v = 0.002 if i < 120 else 0.0
        s = mech.update(v, dt)
        if i % 20 == 0:
            print(f"t={i*dt:.3f}s v_user={v:.4f} θ={s['theta']:.6f} ω={s['omega']:.6f} f={s['frequency']:.2f}Hz")

