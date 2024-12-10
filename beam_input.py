import rebar_props
from conc_analysis_classes import ConcreteBeam, BeamCapacity, BeamStress
from conc_analysis_classes import calc_fr
import design_check_funcs
    
if __name__ == "__main__":
    #---Input---
    # beam dimensions
    width = 42
    height = 20
    # reinforcing
    bar_size = '#5'
    num_bars = 2.33
    bottom_cover = 2
    side_cover = 1.5
    # material properties
    f_c = 4
    f_y = 60
    E_s = 29000
    conc_density = 150
    # loads
    M_u = 41.3
    M_s = 33.75
    V_u = 13.8
    # resistance factors
    phi_m = 0.9
    phi_v = 0.9

    # rebar properties
    rebar = rebar_props.RebarProperties(bar_size)
    bar_area = rebar.bar_area
    bar_diameter = rebar.bar_diameter
    # d_c = rebar_props.calc_position(bottom_cover, bar_diameter)
    # offset = rebar_props.calc_position(side_cover, bar_diameter)
    # steel_area = bar_area * num_bars
    # spacing = rebar_props.calc_spacing(width, num_bars)

    d_c = 2.25
    steel_area = 0.6
    spacing = 18

    As_per_ft = rebar_props.calc_As_per_ft(bar_area, spacing)

    # analysis output
    print("---Beam Analysis---")
    beam = ConcreteBeam(width, height, d_c, f_c)
    print("Beam Dead Load (w_DL)", beam.calc_self_load(conc_density), "k/ft")
    M_cr = beam.calc_Mcr()
    print("Cracking Moment (M_cr):", M_cr, "k-ft")

    capacity_analyzer = BeamCapacity(width, height, d_c, f_c, steel_area, f_y)
    print("Stress Block Depth (a):", capacity_analyzer.calc_comp_block_depth(), "in")
    M_n = capacity_analyzer.calc_moment_capacity()
    print("Factored Moment Capacity (ϕM_n):", phi_m * M_n, "k-ft")
    epsilon_st = capacity_analyzer.calc_epsilon_t()
    print("Design Steel Strain:", epsilon_st)
    print("Effective Shear Depth (d_v):", capacity_analyzer.calc_dv(), "in")
    V_n = capacity_analyzer.calc_shear_capacity()
    print("Factored Shear Capacity (ϕV_n)", phi_v * V_n, "k")

    stress_analyzer = BeamStress(width, height, d_c, f_c, steel_area, E_s, conc_density)
    f_ct = stress_analyzer.calc_uncracked_stress(M_s)
    f_s = stress_analyzer.calc_steel_stress(M_s)
    print("Uncracked Stress:", f_ct, "ksi")
    print("Tensile Stress (f_s):", f_s, "ksi")
    print("Max Compressive Stress (f_c):", stress_analyzer.calc_conc_stress(M_s), "ksi")

    # design check output
    A_ts = design_check_funcs.calc_dist_reinf(width, height, f_y)
    moment_check = design_check_funcs.check_capacity(M_n, M_u, phi_m) >= 1
    shear_check = design_check_funcs.check_capacity(V_n, V_u, phi_v) >= 1
    gamma_3 = design_check_funcs.determine_gamma_3(f_y)
    M_design = design_check_funcs.calc_design_M(M_u, M_cr, gamma_3=gamma_3)
    min_reinf_check = design_check_funcs.check_capacity(M_n, M_design, phi_m) >= 1
    f_r = calc_fr(f_c)
    s_max = design_check_funcs.calc_design_spacing(f_r, f_ct, f_s, f_y, height, d_c)
    crack_control_check = spacing <= s_max
    epsilon_tl = design_check_funcs.calc_epsilon_tl(f_y)
    ductility_check = epsilon_st > epsilon_tl
    gamma_er = design_check_funcs.calc_excess_reinf(M_design, phi_m * M_n)

    print("\n---Design Checks---")
    print("Distribution reinf.:", A_ts, "in²/ft")
    print("Moment Check:", moment_check)
    print("Shear Check:", shear_check)
    print("Minimum Reinforcement:", min_reinf_check)
    print("Crack Control:", crack_control_check)
    print("Ductility:", ductility_check)
    print("Temp. and shrink.:", As_per_ft / A_ts >= 1)
    print("Excess Reinforcement Factor (gamma_er):", gamma_er)