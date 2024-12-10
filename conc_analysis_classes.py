
def calc_fr(f_c):
    """
    Calculates concrete modulus of rupture.

    Parameters:
    - f_c: Compressive strength of concrete (ksi).

    Returns:
    - Modulus of rupture (ksi).
    """
    return 0.24 * f_c ** 0.5

def calc_beta1(f_c):
    """
    Calculates concrete stress block factor.

    Parameters:
    - f_c: Compressive strength of concrete (ksi).
    """
    if f_c <= 4:
        beta_1 = 0.85
    else:
        beta_1 = max(0.85 - (f_c - 4) * 0.05, 0.65)
    return beta_1

def calc_n(E_s, E_c):
    """
    Calculates the modular ratio of steel to concrete.

    Parameters:
    - E_s: Elastic modulus of steel (ksi).
    - E_c: Elastic modulus of concrete (ksi).

    Returns:
    - Modular ratio, n.
    """
    return E_s / E_c


class ConcreteBeam:
    def __init__(self, width: float, height: float, d_c: float, f_c: float):
        """
        Base class for concrete beam properties.
        
        Parameters:
        - width: Beam width (in).
        - height: Beam height (in).
        - d_c: Concrete face in tension to center of reinforcing (in).
        - f_c: Compressive strength of concrete (ksi).

        - d: Effective depth (in).
        """
        self.b = width
        self.h = height
        self.d_c = d_c
        self.f_c = f_c
        self.d = height - d_c

    def calc_Ec(self, conc_density: float) -> float:
        """
        Calculates the elastic modulus of concrete.

        Parameters:
        - conc_density: Concrete density (pcf).

        Returns:
        - Elastic modulus, E_c (ksi).
        """
        return 33000 * (conc_density / 1000) ** 1.5 * self.f_c ** 0.5
    
    def calc_self_load(self, conc_density: float) -> float:
        """
        Calculates the dead load due to self-weight of beam.

        Parameters:
        - conc_density: Concrete density (pcf).

        Returns:
        - Dead load, w_DL (k/ft).
        """
        w_DL = conc_density / 1000 * self.b / 12 * self.h / 12
        return round(w_DL, 2)

    def calc_Ig(self) -> float:
        """
        Returns:
        - Moment of inertia (in⁴).
        """
        return self.b * self.h ** 3 / 12
    
    def calc_Sc(self) -> float:
        """
        Returns:
        - Section modulus (in³)
        """
        return (1/12 * self.b * self.h ** 3) / (self.h / 2)
    
    def calc_Mcr(self) -> float:
        """
        Returns:
        - Cracking moment (k-ft).
        """
        f_r = calc_fr(self.f_c)
        S_c = self.calc_Sc()
        M_cr = f_r * S_c / 12
        return round(M_cr, 1)

class BeamCapacity(ConcreteBeam):
    def __init__(self, width, height, d_c, f_c, steel_area: float, f_y: float):
        """
        Subclass to calculate beam capacity.

        Parameters:
        - steel_area, A_s: Area of steel reinforcement (in²).
        - f_y: Yield strength of steel (ksi).
        """
        super().__init__(width, height, d_c, f_c)
        self.A_s = steel_area
        self.f_y = f_y

    def calc_comp_block_depth(self) -> float:
        """
        Calculates the depth of the compressive stress block (a).

        Returns:
        - Stress block depth (in).
        """
        self.a = (self.A_s * self.f_y) / (0.85 * self.f_c * self.b)
        return round(self.a, 3)

    def calc_moment_capacity(self) -> float:
        """
        Returns:
        - Moment capacity, M_n (k-ft).
        """
        M_n = self.A_s * self.f_y * (self.d - self.a / 2) / 12
        return round(M_n, 1)
    
    def calc_epsilon_t(self, epsilon_c=0.003):
        """
        Calculates design tensile strain in steel.

        Parameters:
        - epsilon_c: Design concrete compressive strain.
        """
        beta_1 = calc_beta1(self.f_c)
        c = self.a / beta_1
        epsilon_t = epsilon_c * (self.d - c) / c
        return round(epsilon_t, 3)

    def calc_dv(self):
        """
        Returns:
        Effective shear depth, d_v (in).
        """
        beta_1 = calc_beta1(self.f_c)
        c = self.a / beta_1
        self.d_v = max(self.d - c / 2, 0.9 * self.d, 0.72 * self.h)
        return round(self.d_v, 2)

    def calc_Vc(self, gamma=1, beta=2) -> float:
        """
        Parameters:
        - lambda: Concrete density modification factor.
        - beta: Tension and shear transmission factor.

        Returns:
        - Concrete shear capacity, V_c (kips).
        """
        V_c = 0.0316 * beta * gamma * self.f_c ** 0.5 * self.b * self.d_v
        return V_c

    def calc_shear_capacity(self, V_s=0):
        """
        Returns:
        - Shear capacity, V_n (kips).
        """
        V_c = self.calc_Vc()
        max_V_n = 0.25 * self.f_c * self.b * self.d_v
        V_n = min(V_c + V_s, max_V_n)
        return round(V_n, 1)

class BeamStress(ConcreteBeam):
    def __init__(self, width, height, d_c, f_c, steel_area: float, E_s: float, conc_density: float):
        """
        Subclass to calculate beam stresses.

        Parameters:
        - steel_area, A_s: Area of steel reinforcement (in²).
        - E_s: Elastic modulus of steel (ksi).
        - conc_density: Cubic weight of concrete (pcf).
        """
        super().__init__(width, height, d_c, f_c)
        self.A_s = steel_area
        self.E_s = E_s
        self.conc_density = conc_density

    def calc_uncracked_stress(self, M):
        """
        Calculates tensile stress in uncracked concrete section (ksi).
        """
        I_g = self.calc_Ig()
        f_ct = M * 12 * self.h / 2 / I_g
        return round(f_ct, 2)

    def calc_rho(self) -> float:
        """
        Calculates the reinforcement ratio, rho.
        """
        rho = self.A_s / (self.b * self.d)
        return rho

    def calc_k(self) -> float:
        """
        Calculates the compressive depth factor, k.
        """
        E_c = self.calc_Ec(self.conc_density)
        n = calc_n(self.E_s, E_c)
        rho = self.calc_rho()
        k = -rho * n+((rho * n)**2 + 2 * rho * n)**0.5
        return k

    def calc_j(self) -> float:
        """
        Calculates the moment arm factor, j.
        """
        k = self.calc_k()
        return 1 - k / 3

    def calc_steel_stress(self, M) -> float:
        """
        Calculates the tensile stress in reinforcing steel.

        Parameters:
        - M: Service moment (k-ft).
        - j: Moment arm factor.

        Returns:
        - Stress in reinforcing steel, f_s (ksi).
        """
        j = self.calc_j()
        f_s = M * 12 / (self.A_s * j * self.d)
        return round(f_s, 3)

    def calc_conc_stress(self, M) -> float:
        """
        Calculates the maximum compressive stress in concrete.

        Parameters:
        - M: Service moment (k-ft).
        - j: Moment arm factor.
        - k: Compressive depth factor.

        Returns:
        - Stress in concrete, f_c (ksi).
        """
        j = self.calc_j()
        k = self.calc_k()
        f_c = 2 * M * 12 / (j * k * self.b * self.d**2)
        return round(f_c, 3)