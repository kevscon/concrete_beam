from flask import Flask, request, render_template

app = Flask(__name__)

from conc_analysis_classes import ConcreteBeam, BeamCapacity, BeamStress
from conc_analysis_classes import calc_fr

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    width = float(request.form['width'])
    height = float(request.form['height'])
    d_c = float(request.form['d_c'])
    steel_area = float(request.form['steel_area'])
    spacing = float(request.form['spacing'])
    f_c = float(request.form['f_c'])
    f_y = float(request.form['f_y'])
    phi_m = float(request.form['phi_m'])
    phi_v = float(request.form['phi_v'])
    E_s = float(request.form['E_s'])
    conc_density = float(request.form['conc_density'])
    M_u = float(request.form['M_u'])
    M_s = float(request.form['M_s'])
    V_u = float(request.form['V_u'])

    # Analysis
    beam = ConcreteBeam(width, height, d_c, f_c)
    w_DL = beam.calc_self_load(conc_density)
    M_cr = beam.calc_Mcr()

    capacity_analyzer = BeamCapacity(width, height, d_c, f_c, steel_area, f_y)
    a = capacity_analyzer.calc_comp_block_depth()
    M_n = capacity_analyzer.calc_moment_capacity()
    epsilon_st = capacity_analyzer.calc_epsilon_t()
    V_n = capacity_analyzer.calc_shear_capacity(epsilon_st)

    stress_analyzer = BeamStress(width, height, d_c, f_c, steel_area, E_s, conc_density)
    f_ct = stress_analyzer.calc_uncracked_stress(M_s)
    f_s = stress_analyzer.calc_steel_stress(M_s)
    f_c = stress_analyzer.calc_conc_stress(M_s)

    # Design Checks
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

    # Return results to the user
    return render_template('result.html',
                           w_DL=w_DL,
                           M_cr=M_cr,
                           a=a,
                           moment_capacity=M_n,
                           epsilon_st=epsilon_st,
                           shear_capacity=V_n,
                           f_ct=f_ct,
                           f_s=f_s,
                           f_c=f_c,
                           A_TS=A_TS,
                           moment_check=moment_check,
                           shear_check=shear_check,
                           min_reinf_check=min_reinf_check,
                           crack_control_check=crack_control_check,
                           ductility_check=ductility_check,
                           gamma_er=gamma_er
                           )

if __name__ == '__main__':
    app.run(debug=True)