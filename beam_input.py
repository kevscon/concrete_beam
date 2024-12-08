from conc_analysis_classes import ConcreteBeam, BeamCapacity, BeamStress
from conc_analysis_classes import calc_fr
    
if __name__ == "__main__":
    # input
    width = 42
    height = 20
    d_c = 2.25
    steel_area = 0.6
    spacing = 18
    f_c = 4
    f_y = 60
    phi_m = 0.9
    phi_v = 0.9

    E_s = 29000
    conc_density = 150
    M_u = 33.75
    M_s = 20
    V_u = 18 

    # analysis output
    print("---Beam Analysis---")
    beam = ConcreteBeam(width, height, d_c, f_c)
    print("Beam Dead Load (w_DL)", beam.calc_self_load(conc_density), "k/ft")
    M_cr = beam.calc_Mcr()
    print("Cracking Moment (M_cr):", M_cr, "k-ft")

    capacity_analyzer = BeamCapacity(width, height, d_c, f_c, steel_area, f_y)
    print("Stress Block Depth (a):", capacity_analyzer.calc_comp_block_depth(), "in")
    M_n = capacity_analyzer.calc_moment_capacity()
    print("Moment Capacity (M_n):", M_n, "k-ft")
    epsilon_st = capacity_analyzer.calc_epsilon_t()
    print("Design Steel Strain:", epsilon_st)
    V_n = capacity_analyzer.calc_shear_capacity(epsilon_st)
    print("Shear Capacity (V_n)", V_n, "k")

    stress_analyzer = BeamStress(width, height, d_c, f_c, steel_area, E_s, conc_density)
    f_ct = stress_analyzer.calc_uncracked_stress(M_s)
    f_s = stress_analyzer.calc_steel_stress(M_s)
    print("Uncracked Stress:", f_ct, "ksi")
    print("Tensile Stress (f_s):", f_s, "ksi")
    print("Max Compressive Stress (f_c):", stress_analyzer.calc_conc_stress(M_s), "ksi")

    # design check output
    import design_check_funcs
    A_TS = design_check_funcs.calc_dist_reinf(width, height, f_y)
    moment_check = design_check_funcs.check_capacity(M_n, M_u, phi_m) >= 1
    shear_check = design_check_funcs.check_capacity(V_n, V_u, phi_v) >= 1
    M_design = design_check_funcs.calc_design_M(M_u, M_cr)
    min_reinf_check = design_check_funcs.check_capacity(M_n, M_design, phi_m) >= 1
    f_r = calc_fr(f_c)
    s_max = design_check_funcs.calc_design_spacing(f_r, f_ct, f_s, f_y, height, d_c)
    crack_control_check = spacing <= s_max
    epsilon_tl = design_check_funcs.calc_epsilon_tl(f_y)
    ductility_check = epsilon_st > epsilon_tl
    gamma_er = design_check_funcs.calc_excess_reinf(M_design, phi_m * M_n)

    print("\n---Design Checks---")
    print("Distribution reinf.:", A_TS, "in²/ft")
    print("Moment Check:", moment_check)
    print("Shear Check:", shear_check)
    print("Minimum Reinforcement:", min_reinf_check)
    print("Crack Control:", crack_control_check)
    print("Ductility:", ductility_check)
    print("Excess Reinforcement Factor (gamma_er):", gamma_er)