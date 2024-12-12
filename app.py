from flask import Flask, request, render_template

app = Flask(__name__)

import rebar_props
from conc_analysis_classes import ConcreteBeam, BeamCapacity, BeamStress
from conc_analysis_classes import calc_fr
import design_check_funcs

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    #---Input---
    # beam dimensions
    width = float(request.form['width'])
    height = float(request.form['height'])
    # reinforcing
    cover = float(request.form['cover'])
    bar_size = str(request.form['bar_size'])
    spacing = float(request.form['spacing'])
    # material properties
    f_c = float(request.form['f_c'])
    f_y = float(request.form['f_y'])
    E_s = float(request.form['E_s'])
    conc_density = float(request.form['conc_density'])
    # loads
    M_u = float(request.form['M_u'])
    M_s = float(request.form['M_s'])
    V_u = float(request.form['V_u'])
    # resistance factors
    phi_m = float(request.form['phi_m'])
    phi_v = float(request.form['phi_v'])

    # Analysis
    # steel area
    rebar = rebar_props.RebarProperties(bar_size)
    bar_area = rebar.bar_area
    bar_diameter = rebar.bar_diameter
    d_c = rebar_props.calc_position(cover, bar_diameter)
    num_bars = width / spacing
    steel_area = num_bars * bar_area
    As_per_ft = rebar_props.calc_As_per_ft(bar_area, spacing)
    # beam properties
    beam = ConcreteBeam(width, height, d_c, f_c)
    d_s = beam.d
    w_DL = beam.calc_self_load(conc_density)
    M_cr = beam.calc_Mcr()
    f_r = calc_fr(f_c)
    # beam capacity
    capacity_analyzer = BeamCapacity(width, height, d_c, f_c, steel_area, f_y)
    a = capacity_analyzer.calc_comp_block_depth()
    M_n = capacity_analyzer.calc_moment_capacity()
    epsilon_st = capacity_analyzer.calc_epsilon_t()
    d_v = capacity_analyzer.calc_dv()
    V_c = capacity_analyzer.calc_Vc()
    V_n = capacity_analyzer.calc_shear_capacity()
    # beam service stress
    stress_analyzer = BeamStress(width, height, d_c, f_c, steel_area, E_s, conc_density)
    cracking_ratio = M_u / M_cr
    f_ct = stress_analyzer.calc_uncracked_stress(M_s)
    if cracking_ratio < 1:
        f_c = stress_analyzer.calc_uncracked_stress(M_s)
        # update for uncracked steel stress
        f_s = stress_analyzer.calc_steel_stress(M_s)
    else:
        f_s = stress_analyzer.calc_steel_stress(M_s)
        f_c = stress_analyzer.calc_conc_stress(M_s)

    # Design Checks
    # flexure reinforcing
    moment_check = design_check_funcs.check_capacity(M_n, M_u, phi_m) >= 1
    moment_ratio = design_check_funcs.calc_demand_ratio(M_u, M_n, phi_m)
    gamma_3 = design_check_funcs.determine_gamma_3(f_y)
    M_design = design_check_funcs.calc_design_M(M_u, M_cr, gamma_3=gamma_3)
    min_reinf_check = design_check_funcs.check_capacity(M_n, M_design, phi_m) >= 1
    min_reinf_ratio = design_check_funcs.calc_demand_ratio(M_design, M_n, phi_m)
    s_max = design_check_funcs.calc_design_spacing(f_r, f_ct, f_s, f_y, height, d_c)
    crack_control_check = spacing <= s_max
    crack_control_ratio = spacing / s_max
    epsilon_tl = design_check_funcs.calc_epsilon_tl(f_y)
    ductility_check = epsilon_st > epsilon_tl
    ductility_ratio = epsilon_tl / epsilon_st
    A_ts = design_check_funcs.calc_dist_reinf(width, height, f_y)
    distr_reinf_check = As_per_ft / A_ts >= 1
    dist_reinf_ratio = A_ts / As_per_ft
    gamma_er = design_check_funcs.calc_excess_reinf(M_design, phi_m * M_n)
    # shear
    shear_check = design_check_funcs.check_capacity(V_n, V_u, phi_v) >= 1
    shear_ratio = design_check_funcs.calc_demand_ratio(V_u, V_n, phi_v)


    # Return results to the user
    return render_template('result.html',
                           d_s=d_s,
                           w_DL=w_DL,
                           M_cr=M_cr,
                           a=a,
                           moment_capacity=phi_m * M_n,
                           epsilon_st=epsilon_st,
                           d_v=d_v,
                           shear_capacity=phi_v * V_n,
                           f_s=f_s,
                           f_c=f_c,
                           A_ts=A_ts,
                           moment_check=moment_check,
                           shear_check=shear_check,
                           min_reinf_check=min_reinf_check,
                           crack_control_check=crack_control_check,
                           ductility_check=ductility_check,
                           distr_reinf_check=distr_reinf_check,
                           gamma_er=gamma_er,
                           moment_ratio=moment_ratio,
                           shear_ratio=shear_ratio,
                           min_reinf_ratio=min_reinf_ratio,
                           crack_control_ratio=crack_control_ratio,
                           ductility_ratio=ductility_ratio,
                           dist_reinf_ratio=dist_reinf_ratio
                           )

if __name__ == '__main__':
    app.run(debug=True)