import matplotlib.pyplot as plt
import numpy as np
import sympy as sy
import pandas as pd

# =============== data set ===============
# # ref data
# g = 9.81
# CL_alpha = 5.7
# solidity = 0.075
# gamma = 6
# C_d_fus = 1.5
# m = 2200
# rho = 1.225
# vtip = 200
# r = 7.32
# rpm_rad = vtip / r
# I_yy = 10615
# mast = 1
# S = np.pi * r ** 2
# tau = 0.1  # time constant for lambdi_i

# own data set
g = 9.81
CL_alpha = 5.7
solidity = 0.075
gamma = 9       #lock number
C_d_fus = 1.2
m = 3600
rho = 1.225
r = 5.5
rpm_rad = 375 * 2 * np.pi /60
vtip = rpm_rad * r
I_yy = 12615
mast = 1
S = np.pi * r ** 2
tau = 0.1 #time constant for lambdi_i

# =============== Control scenarios ===============
def StopHover(u, w, q, theta_f, h, x, delta_theta, delta_cyclic):
    # height control

    K3 = 0.2  # gain on ascent rate
    C_des = K3 * (h_des - h)

    # Ascent rate control
    # collective
    theta_gen = 5 * np.pi / 180
    K1 = 0.01  # proportional
    K2 = 0.01  # integral

    # change in C:
    C_actual = u * np.sin(theta_f) - w * np.cos(theta_f)
    dC = C_des - C_actual

    theta_collective = theta_gen + K1 * dC + K2 * delta_theta

    # horizontal speed control
    V_horizontal = u * np.cos(theta_f) - w * np.sin(theta_f)


    K4 = 0.8  # pitch angle
    K5 = 1  # pitch rate
    K6 = 0.025  # horizontal speed
    K7 = 0.175       # distance
    K8 = 0.002      # Integral

    # change in V
    V_des = K7 * (x_des - x)
    dV = V_des - V_horizontal
    theta_cyclic = K4 * theta_f + K5 * q + K6 * dV + K8 * delta_cyclic

    return theta_cyclic, theta_collective, dC, dV


# time series data & settings
t0 = 0
tmax = 100
dt = 0.1

# initial settings state variables
u_init = 10  # velocity X relative to body
w_init = 0.0  # velocity Y relative to body
q_init = 0.0  # pitch rate positive nose up
theta_f_init = 0.00 * np.pi/180  # fuselage pitch angle positive pitch up
lambda_i_init = np.sqrt(m * 9.81 / (S * 2 * rho)) / vtip  # nondim inst ind velocity
x_init = 0  # position relative to horizon
z_init = -30  # postive downwards relative to horizon

# environment settings
headwind = 7 * 0.514444
x_des = 100
h_des = 20 * 0.3048   # stay at same altitude
# initial settings input variables
theta_cyclic_init = 0
theta_collective_init = 6 * np.pi / 180

# setting up state, control vectors, and position vectors
state_init = np.array([u_init,
                       w_init,
                       q_init,
                       theta_f_init,
                       lambda_i_init])

control_init = np.array([theta_cyclic_init,
                         theta_collective_init])

pos_init = np.array([x_init,
                     z_init])  # positive downwards

# altitude control
delta_theta_range = np.array([w_init])
delta_cyclic_range = np.array([u_init])

# Creating time range for maneuver
t_range = np.arange(t0, tmax + dt, dt)

# initializing arrays for storing state data
state_range = np.array([state_init])
control_range = np.array([control_init])
position_range = np.array([pos_init])

for i, t in enumerate(t_range[:-1]):

    # getting previous state
    state_v = state_range[-1]
    control_v = control_range[-1]
    pos_v = position_range[-1]

    # getting state & control variables
    u = state_v[0]
    w = state_v[1]
    q = state_v[2]
    theta_f = state_v[3]
    lambda_i = state_v[4]

    # getting position variables
    x = pos_v[0]
    z = pos_v[1]
    c = u * np.sin(theta_f) - w * np.cos(theta_f)
    h = -z

    # height control
    delta_theta = delta_theta_range[-1]
    delta_cyclic = delta_cyclic_range[-1]

    # checking quadrant angle
    if u == 0:
        if w > 0:
            phi = np.pi / 2
        else:
            phi = -np.pi / 2
    else:
        phi = np.arctan(w / u)

        if u < 0:
            phi = phi + np.pi

    # setting control laws (PID)
    theta_cyclic, theta_collective, dC, dV = StopHover(u, w, q, theta_f, h, x, delta_theta, delta_cyclic)

    # calculating coefficients
    V = np.sqrt((u ** 2) + (w ** 2))
    alpha_c = theta_cyclic - phi
    mu = (V / vtip) * np.cos(alpha_c)
    lambda_c = (V / vtip) * np.sin(alpha_c)
    qdiml = q / rpm_rad

    # calculating tip path plane angle
    teller = -16 / gamma * qdiml + 8 / 3 * mu * theta_collective - 2 * mu * (lambda_c + lambda_i)
    a1 = teller / (1 - .5 * mu ** 2)

    # CT calculation
    CT_bem = 0.25 * CL_alpha * solidity * ((2 / 3) * theta_collective * (1 + (3 / 2) * mu ** 2) -
                                           (lambda_c + lambda_i))

    CT_glau = 2 * lambda_i * np.sqrt(((V / vtip) * np.cos(alpha_c - a1)) ** 2 +
                                     ((V / vtip) * np.sin(alpha_c - a1) + lambda_i) ** 2)

    T = CT_bem * rho * vtip ** 2 * S

    # eq of motion
    u_dot = -g * np.sin(theta_f) - 0.5 * (C_d_fus / m) * rho * u * V + \
            (T / m) * np.sin(theta_cyclic - a1) - q * w - headwind * np.cos(theta_f)

    w_dot = g * np.cos(theta_f) - 0.5 * (C_d_fus / m) * rho * w * V - \
            (T / m) * np.cos(theta_cyclic - a1) + q * u - headwind * np.sin(theta_f)

    q_dot = - (T / I_yy) * mast * np.sin(theta_cyclic - a1)

    theta_f_dot = q

    x_dot = u * np.cos(theta_f) + w * np.sin(theta_f)

    z_dot = - c

    # updating state vector
    state_v_new = np.array([u + u_dot * dt,
                            w + w_dot * dt,
                            q + q_dot * dt,
                            theta_f + theta_f_dot * dt,
                            lambda_i + ((CT_bem - CT_glau) / tau) * dt])

    # updating position vector
    pos_v_new = np.array([x + x_dot * dt,
                          z + z_dot * dt])

    # updating state vector
    control_v_new = np.array([theta_cyclic,
                              theta_collective])

    # altitude hold
    delta_theta_range = np.append(delta_theta_range, [delta_theta + dC * dt])
    delta_cyclic_range = np.append(delta_cyclic_range, [delta_cyclic + dV * dt])

    # adding to range for plotting
    state_range = np.append(state_range, [state_v_new], axis=0)
    control_range = np.append(control_range, [control_v_new], axis=0)
    position_range = np.append(position_range, [pos_v_new], axis=0)

# plotting results
fig1 = plt.figure()
plt.plot(t_range, state_range[:, 3] * 180 / np.pi, label='theta_f [degr]')
plt.plot(t_range, position_range[:, 1] * -1, label='y_pos [m]')
plt.plot(t_range, position_range[:, 0], label='x_pos [m[')
plt.xlabel("time [s]")
plt.legend()

# fig2 = plt.figure()
# plt.plot(t_range, control_range[:,1] * 180 / np.pi, label='collective')
# plt.plot(t_range, control_range[:,0] * 180 / np.pi, label='cyclic')
# plt.legend()

plt.show()

