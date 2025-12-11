
import numpy as np
from typing import Dict, Any
import math
import pandas as pd



# ============================================================
# MatCal C++ 插值模块
# ============================================================
try:
    import matcal_interp as mc
    MATCAL_AVAILABLE = True
    print("[MatCal] 已成功载入 matcal_interp.pyd")
except Exception as e:
    MATCAL_AVAILABLE = False
    print("[MatCal] WARNING: MatCal 未加载，将使用 numpy/scipy 插值 →", e)

# ============================================================
# MatCal 插值统一接口（自动 fallback）
# ============================================================
class MatCalInterpBuilder:

    @staticmethod
    def build_linear(xs, ys):
        xs = np.asarray(xs, float)
        ys = np.asarray(ys, float)

        if MATCAL_AVAILABLE:
            interp_cpp = mc.LinearInsert(xs.tolist(), ys.tolist())
            def f(x): return float(interp_cpp.calculate(float(x)))
            return f, interp_cpp

        # fallback
        def f(x): return float(np.interp(x, xs, ys))
        return f, None

    @staticmethod
    def build_cubic(xs, ys):
        xs = np.asarray(xs, float)
        ys = np.asarray(ys, float)

        if MATCAL_AVAILABLE:
            interp_cpp = mc.CubicSpline(xs.tolist(), ys.tolist())
            def f(x): return float(interp_cpp.calculate(float(x)))
            return f, interp_cpp

        from scipy.interpolate import CubicSpline
        spline = CubicSpline(xs, ys)
        def f(x): return float(spline(x))
        return f, None

    @staticmethod
    def build_newton(xs, ys):
        xs = np.asarray(xs, float)
        ys = np.asarray(ys, float)

        if MATCAL_AVAILABLE:
            pts = list(zip(xs.tolist(), ys.tolist()))
            interp_cpp = mc.NewtonInsert(pts)
            def f(x): return float(interp_cpp.calculate(float(x)))
            return f, interp_cpp

        deg = min(len(xs) - 1, 6)
        poly = np.poly1d(np.polyfit(xs, ys, deg))
        def f(x): return float(poly(x))
        return f, None



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
                 I: float = 10.0,        # 转动惯量 I
                 k: float = 20.0,         # 等效刚度 k
                 r: float = 0.01,         # 半径 r
                 r_string: float = None,  # 琴弦半径 r_string (m) —— 新增
                 Sigma_valid:float = 210000,
                 k_d: float = 5,
                 sigma: float = 0.001,    # 粘滞阻尼 σ
                 tau_fric_limit_0:float = -0.1,
                 alpha:float = 0.05,
                 gamma:float = 0.9,       # 动摩擦比例 γ
                 v_user:float = 0.0
                 ):

        # 基本物理参数
        self.L = L
        self.mu = mu
        # 如果没传 r_string，就默认等于 r（向后兼容）
        self.r_string = r if (r_string is None) else r_string
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

        # 修复时间计算参数
        self.repair_simulation_dt = 0.01      # 修复时间模拟步长 (s)
        self.max_repair_time = 1000.0           # 最大修复模拟时间 (s)

        # --- 摩擦模型扩展 ---
        self.friction_model = "linear"          # "linear" 或 "custom"
        self.custom_fric_csv_path = None
        self.custom_interp_method=None
        self.custom_interp_func = None       # 自定义 τ = f(theta)
        self.custom_interp_cpp_obj =None    # 防止gc回收



    # ======================================================
    # 公共方法
    # ======================================================

    # ============================================================
    # 加载自定义摩擦曲线 (CSV + MatCal)
    # ============================================================
    def copy_from(self, other):
        """
        将其他 MechanicsEngine 的全部参数完整复制到当前对象
        （不复制 Python 对象引用导致相互污染）
        """
        # ---- 基本物理参数 ----
        self.L = other.L
        self.mu = other.mu
        self.r_string = other.r_string
        self.I = other.I
        self.k = other.k
        self.r = other.r
        self.Sigma_valid = other.Sigma_valid
        self.k_d = other.k_d

        # ---- 摩擦参数 ----
        self.sigma = other.sigma
        self.tau_fric_limit_0 = other.tau_fric_limit_0
        self.alpha = other.alpha
        self.gamma = other.gamma

        # ---- 模型类型 ----
        self.friction_model = other.friction_model
        self.custom_fric_csv_path = other.custom_fric_csv_path
        self.custom_interp_method = other.custom_interp_method

        # ---- 自定义插值函数复制 ----
        self.custom_interp_func = other.custom_interp_func
        self.custom_interp_cpp_obj = other.custom_interp_cpp_obj

        # ---- 状态复制 ----
        self.theta = other.theta
        self.omega = other.omega
        self.v_user = other.v_user
        self.theta_init = other.theta_init

        # ---- 修复时间参数复制 ----
        self.repair_simulation_dt = other.repair_simulation_dt
        self.max_repair_time = other.max_repair_time

        # 无返回值



    def load_custom_friction(self, csv_path: str, interp_method: str):
        """
        interp_method:  "线性插值" / "三次样条插值" / "牛顿插值"
        """
        try:
            df = pd.read_csv(csv_path)
            if not {"theta", "tau_fric"}.issubset(df.columns):
                raise ValueError("CSV 必须包含列：theta, tau_fric")

            xs = df["theta"].astype(float).tolist()
            ys = df["tau_fric"].astype(float).tolist()

            # ---- 选择插值方式 ----
            if interp_method == "linear":
                f, cpp_obj = MatCalInterpBuilder.build_linear(xs, ys)
            elif interp_method == "cubic":
                f, cpp_obj = MatCalInterpBuilder.build_cubic(xs, ys)
            else:
                f, cpp_obj = MatCalInterpBuilder.build_newton(xs, ys)

            # 保存
            self.custom_interp_func = f
            self.custom_interp_cpp_obj = cpp_obj
            self.custom_fric_interp_method = interp_method
            self.friction_model = "custom"

            print(f"[Mechanics] 自定义摩擦曲线加载成功: {csv_path}")

        except Exception as e:
            print("[Mechanics] 自定义摩擦加载失败 → 回退到线性模型:", e)
            self.friction_model = "linear"
            self.custom_interp_func = None
            self.custom_interp_cpp_obj = None

    def set_friction_model(self, mode: str):
        """
        选择摩擦模型：
        mode = "linear"（默认）
        mode = "custom"
        """
        if mode.upper() not in ["linear", "custom"]:
            raise ValueError("Invalid friction model")
        self.friction_model = mode.upper()

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

        # 步长参数
        self.repair_simulation_dt = params.get('repair_simulation_dt',self.repair_simulation_dt)
        self.max_repair_time = params.get('max_repair_time',self.max_repair_time)

        # 保持当前频率不变
        current_freq = self.get_frequency()
        if current_freq > 0.0:
            self.set_initial_state_by_frequency(current_freq)

        # 摩擦模型
        if params.get('friction_model',None) is not None and params['friction_model']=="custom":
            path = params.get('custom_fric_csv_path',self.custom_fric_csv_path)
            method = params.get('custom_interp_method',self.custom_interp_method)
            self.load_custom_friction(path,method)

    def set_initial_state_by_frequency(self, target_freq: float):
        """
        根据目标频率 f_target (Hz)，计算所需的初始弦轴角度 theta。
        计算公式：theta = 4*(L^2 * f^2 * mu) / (k * r)
        """
        if target_freq <= 0.0:
            # 目标频率无效，重置到零角度
            self.theta_init = 0.0
        else:
            # 计算目标频率所需的 theta
            try:
                # 使用公式：theta = 4*(L^2 * f^2 * mu) / (k * r)
                numerator = 4*(self.L**2) * (target_freq**2) * self.mu
                denominator = self.k * (self.r)

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
        denom = self.k * (self.r)
        if denom == 0:
            return 0.0
        return 4*(self.L ** 2) * (freq ** 2) * self.mu / denom

    def _compute_theta_loose_threshold(self):
        """
        根据静态松弦条件 kr^2 * theta < tau0 + alpha * theta
        → (k r^2 - alpha) * theta < tau0
        注意：我们必须满足 (k r^2 - alpha) < 0 才会出现松弦区
        """
        # 修改成了弦半径
        den = self.k * (self.r_string ** 2) - self.alpha
        if den >= 0:
            return None  # 永远不能静止
        return self.tau_fric_limit_0 / den  # 正数阈值（因为 tau0<0, den<0）


    # ======================================================
    # 基本物理转换
    # ======================================================

    def get_displacement(self) -> float:
        return self.r * self.theta

    def get_tension(self) -> float:
        return max(0.0,  self.k * (self.r**2) * abs(self.theta))

    def get_F_string(self)->float:
        return max(0.0,  self.k * (self.r) * abs(self.theta))

    def get_frequency(self) -> float:
        F = self.get_F_string()
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

    # def _compute_friction_limits(self, theta: float):
    #     """
    #     计算静摩擦极限与动摩擦（联动）
    #     """
    #     tau_static_limit = abs(self.tau_fric_limit_0 + self.alpha * theta)
    #     tau_kinetic_limit = self.gamma * tau_static_limit
    #     return tau_static_limit, tau_kinetic_limit
    def _compute_friction_limits(self, theta: float):
        """
        计算静摩擦极限与动摩擦极限。
        支持两种模型：
        1. 线性模型（原版）
        2. 自定义插值模型（CSV）
        """
        # --- 自定义模型 ---
        if self.friction_model == "custom" and self.custom_interp_func is not None:
            try:
                tau_static = abs(float(self.custom_interp_func(theta)))
            except Exception:
                # 插值函数错误 → 回退到线性模型
                tau_static = abs(self.tau_fric_limit_0 + self.alpha * theta)
        else:
            # --- 原线性模型 ---
            tau_static = abs(self.tau_fric_limit_0 + self.alpha * theta)

        tau_kinetic = self.gamma * tau_static
        return tau_static, tau_kinetic


    def _compute_friction_torque(self, theta: float, omega: float) -> float:
        """
        计算摩擦力矩（用于修复时间模拟）
        基于现有的摩擦模型逻辑
        """
        tau_static_limit, tau_kinetic_limit = self._compute_friction_limits(theta)

        # 静止状态
        if abs(omega) < self.omega_eps:
            # 在修复模拟中，我们假设系统总是处于运动状态
            # 所以返回动摩擦力矩
            return -np.sign(omega) * tau_kinetic_limit - self.sigma * omega
        # 运动状态
        else:
            return -np.sign(omega) * tau_kinetic_limit - self.sigma * omega

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

    def update(self, v_user: float) -> Dict[str, Any]:

        # ======================================================
        # 立即停止机制：鼠标静止时不再积分，也不再惯性滑行
        # ======================================================
        if abs(v_user) <1e-8:
            # 直接冻结角速度，防止继续冲
            self.omega = 0.0
            return {
                "theta": self.theta,
                "omega": 0.0,
                "displacement": self.get_displacement(),
                "tension": self.get_tension(),
                "frequency": self.get_frequency(),
                "v_user": 0.0,
                "loose": False,
                "theta_loose_threshold": None,
                "broken": False,
                "max_F": self.Sigma_valid * math.pi * (self.r_string **2 ) *1e6
            }

        self.v_user = v_user
        y = np.array([self.theta, self.omega], dtype=float)

        dt=self.repair_simulation_dt

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
            if self.friction_model=="custom":
                tau_0 = self.custom_interp_func(0)
            else:
                tau_0=self.tau_fric_limit_0
            theta_loose = tau_0 / den
            loose = self.theta < theta_loose
        else:
            theta_loose = None
            loose = False

        # 断弦
        F_limit = self.Sigma_valid * math.pi * (self.r_string **2 ) *1e6
        broken = (self.get_F_string() > F_limit)

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
            "max_F": F_limit
        }

    # ======================================================
    # 修复时间计算相关方法
    # ======================================================

    def set_repair_time_params(self, simulation_dt: float, max_time: float):
        """设置修复时间计算参数"""
        self.repair_simulation_dt = max(0.0001, simulation_dt)  # 最小0.1ms
        self.max_repair_time = max(10, max_time)              # 最小10s

    def get_repair_time_params(self) -> dict:
        """获取修复时间计算参数"""
        return {
            'repair_simulation_dt': self.repair_simulation_dt,
            'max_repair_time': self.max_repair_time
        }

    def calculate_repair_time(self, target_theta: float, max_torque: float) -> float:
        """
        计算从当前状态到目标角度在最大力矩下的修复时间
        """
        # 使用类内部维护的参数
        dt = self.repair_simulation_dt
        max_time = self.max_repair_time

        # 创建模拟用的临时状态
        temp_theta = self.theta
        temp_omega = self.omega

        elapsed_time = 0.0

        while elapsed_time < max_time:
            # 计算角度误差
            theta_error = target_theta - temp_theta

            # 如果已经很接近目标，结束模拟
            if abs(theta_error) < 1e-6:
                break

            # 确定施加力矩的方向
            torque_direction = 1.0 if theta_error > 0 else -1.0
            torque_applied = torque_direction * abs(max_torque)

            # 计算角加速度
            alpha = self._compute_angular_acceleration(temp_theta, temp_omega, torque_applied)

            # 更新角速度（欧拉积分）
            temp_omega += alpha * dt

            # 更新角度
            temp_theta += temp_omega * dt

            # 更新时间
            elapsed_time += dt

            # 检查是否过冲
            if (torque_direction > 0 and temp_theta > target_theta) or \
               (torque_direction < 0 and temp_theta < target_theta):
                break

        return elapsed_time
    # def calculate_repair_time(self, target_theta: float, max_torque: float) -> float:
    #     """
    #     优化后的修复时间计算（比原版更快）
    #     """
    #     dt = self.repair_simulation_dt
    #     max_time = self.max_repair_time

    #     theta = self.theta
    #     omega = self.omega

    #     # 力矩方向
    #     direction = 1.0 if target_theta > theta else -1.0
    #     torque = abs(max_torque) * direction

    #     # --- 静摩擦检查：如果最大力矩不足以推动，直接返回无穷大 ---
    #     tau_static, _ = self._compute_friction_limits(theta)
    #     if abs(torque) <= tau_static:
    #         return float("inf")

    #     time_elapsed = 0.0
    #     steps = int(max_time / dt)

    #     for _ in range(steps):

    #         # 计算摩擦、恢复力矩、角加速度
    #         tau_restoring = -self._compute_tension_for_simulation(theta) * self.r
    #         tau_friction = self._compute_friction_torque(theta, omega)
    #         alpha = (torque + tau_restoring + tau_friction) / self.I

    #         # 更新角速度和角度
    #         omega += alpha * dt
    #         theta += omega * dt
    #         time_elapsed += dt

    #         # 收敛判定
    #         if direction > 0:
    #             if theta >= target_theta:
    #                 return time_elapsed
    #         else:
    #             if theta <= target_theta:
    #                 return time_elapsed

    #     return float("inf")
    # def calculate_repair_time(self, target_theta: float, max_torque: float) -> float:
    #     """
    #     使用 MatCal C++ RK4 加速的修复时间计算
    #     """
    #     dt = self.repair_simulation_dt
    #     max_time = self.max_repair_time

    #     theta = self.theta
    #     omega = self.omega

    #     # 力矩方向
    #     direction = 1.0 if target_theta > theta else -1.0
    #     torque_applied = abs(max_torque) * direction

    #     # —— 静摩擦检查：扭不动就返回 ∞ ——
    #     tau_static, _ = self._compute_friction_limits(theta)
    #     if abs(torque_applied) <= tau_static:
    #         return float("inf")

    #     # =====================================================
    #     #                MatCal RK4 加速计算
    #     # =====================================================
    #     if MATCAL_AVAILABLE:
    #         rk4 = mc.RK4()   # ← 这里正式实例化 C++ RK4Wrapper

    #         def dyn(th, om):
    #             """
    #             MatCal RK4 的右端函数 f(th, om) → (dθ/dt, dω/dt)
    #             必须返回 pair 或 tuple(double,double)
    #             """
    #             # 恢复力矩：张力 * 半径
    #             tau_restoring = -self._compute_tension_for_simulation(th) * self.r

    #             # 摩擦力矩
    #             tau_friction = self._compute_friction_torque(th, om)

    #             # 角加速度
    #             alpha = (torque_applied + tau_restoring + tau_friction) / self.I

    #             # 返回 dθ/dt 与 dω/dt
    #             return (om, alpha)

    #         time_elapsed = 0.0
    #         steps = int(max_time / dt)

    #         for _ in range(steps):
    #             # ⭐⭐ 核心调用：C++ RK4 计算一个 dt 的积分 ⭐⭐
    #             theta, omega = rk4.step(theta, omega, dt, dyn)

    #             time_elapsed += dt

    #             # 收敛判定
    #             if (direction > 0 and theta >= target_theta) or \
    #                (direction < 0 and theta <= target_theta):
    #                 return time_elapsed

    #         return float("inf")

    #     # =====================================================
    #     # fallback：MatCal 未加载时，回退到欧拉法
    #     # =====================================================
    #     time_elapsed = 0.0
    #     steps = int(max_time / dt)

    #     for _ in range(steps):
    #         tau_restoring = -self._compute_tension_for_simulation(theta) * self.r
    #         tau_friction = self._compute_friction_torque(theta, omega)
    #         alpha = (torque_applied + tau_restoring + tau_friction) / self.I

    #         omega += alpha * dt
    #         theta += omega * dt
    #         time_elapsed += dt

    #         if (direction > 0 and theta >= target_theta) or \
    #            (direction < 0 and theta <= target_theta):
    #             return time_elapsed

    #     return float("inf")
    # def calculate_repair_time(self, target_theta: float, max_torque: float) -> float:
    #     dt = self.repair_simulation_dt
    #     max_time = self.max_repair_time

    #     theta = self.theta
    #     omega = self.omega

    #     direction = 1.0 if target_theta > theta else -1.0
    #     torque_applied = abs(max_torque) * direction

    #     # 静摩擦检查
    #     tau_static, _ = self._compute_friction_limits(theta)
    #     if abs(torque_applied) <= tau_static:
    #         return float("inf")

    #     # ========================================
    #     #    使用 C++ Euler（结果与原版本一致）
    #     # ========================================
    #     if MATCAL_AVAILABLE:
    #         euler = mc.Euler()

    #         def dyn(th, om):
    #             tau_restoring = -self._compute_tension_for_simulation(th) * self.r
    #             tau_friction  = self._compute_friction_torque(th, om)
    #             alpha = (torque_applied + tau_restoring + tau_friction) / self.I
    #             return (om, alpha)

    #         time_elapsed = 0.0
    #         steps = int(max_time / dt)

    #         for _ in range(steps):
    #             theta, omega = euler.step(theta, omega, dt, dyn)
    #             time_elapsed += dt

    #             if (direction > 0 and theta >= target_theta) or \
    #                (direction < 0 and theta <= target_theta):
    #                 return time_elapsed

    #         return float("inf")

    #     # ========================================
    #     # fallback: Python 半隐式 Euler
    #     # ========================================
    #     time_elapsed = 0.0
    #     steps = int(max_time / dt)

    #     for _ in range(steps):
    #         tau_restoring = -self._compute_tension_for_simulation(theta) * self.r
    #         tau_friction  = self._compute_friction_torque(theta, omega)
    #         alpha = (torque_applied + tau_restoring + tau_friction) / self.I

    #         omega += alpha * dt
    #         theta += omega * dt
    #         time_elapsed += dt

    #         if (direction > 0 and theta >= target_theta) or \
    #            (direction < 0 and theta <= target_theta):
    #             return time_elapsed

    #     return float("inf")




    def _compute_angular_acceleration(self, theta: float, omega: float, torque_applied: float) -> float:
        """计算角加速度（用于时间模拟）"""
        # 计算弦张力产生的恢复力矩
        T = self._compute_tension_for_simulation(theta)
        tau_restoring = -T * self.r

        # 计算摩擦力矩
        tau_friction = self._compute_friction_torque(theta, omega)

        # 总力矩
        total_torque = torque_applied + tau_restoring + tau_friction

        # 角加速度
        alpha = total_torque / self.I

        return alpha

    def _compute_tension_for_simulation(self, theta: float) -> float:
        """
        用于修复时间模拟的张力计算
        与get_tension()保持一致，但接受外部theta参数
        """
        return max(0.0, self.k * (self.r) * abs(theta))

