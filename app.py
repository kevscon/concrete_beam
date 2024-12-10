from flask import Flask, request, render_template

app = Flask(__name__)

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
    d_c = float(request.form['d_c'])
    steel_area = float(request.form['steel_area'])
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
    # beam properties
    beam = ConcreteBeam(width, height, d_c, f_c)
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
    f_ct = stress_analyzer.calc_uncracked_stress(M_s)
    f_s = stress_analyzer.calc_steel_stress(M_s)
    f_c = stress_analyzer.calc_conc_stress(M_s)

    # Design Checks
    # flexure reinforcing
    moment_check = design_check_funcs.check_capacity(M_n, M_u, phi_m) >= 1
    gamma_3 = design_check_funcs.determine_gamma_3(f_y)
    M_design = design_check_funcs.calc_design_M(M_u, M_cr, gamma_3=gamma_3)
    min_reinf_check = design_check_funcs.check_capacity(M_n, M_design, phi_m) >= 1
    s_max = design_check_funcs.calc_design_spacing(f_r, f_ct, f_s, f_y, height, d_c)
    crack_control_check = spacing <= s_max
    epsilon_tl = design_check_funcs.calc_epsilon_tl(f_y)
    ductility_check = epsilon_st > epsilon_tl
    # ts_check = design_check_funcs.check_capacity(As_per_ft, A_ts)
    gamma_er = design_check_funcs.calc_excess_reinf(M_design, phi_m * M_n)
    # shear
    shear_check = design_check_funcs.check_capacity(V_n, V_u, phi_v) >= 1
    # requirements
    A_ts = design_check_funcs.calc_dist_reinf(width, height, f_y)

    # Return results to the user
    return render_template('result.html',
                           w_DL=w_DL,
                           M_cr=M_cr,
                           a=a,
                           moment_capacity=phi_m * M_n,
                           epsilon_st=epsilon_st,
                           d_v=d_v,
                           shear_capacity=phi_v * V_n,
                           f_ct=f_ct,
                           f_s=f_s,
                           f_c=f_c,
                           A_ts=A_ts,
                           moment_check=moment_check,
                           shear_check=shear_check,
                           min_reinf_check=min_reinf_check,
                           crack_control_check=crack_control_check,
                           ductility_check=ductility_check,
                           gamma_er=gamma_er
                           )

if __name__ == '__main__':
    app.run(debug=True)