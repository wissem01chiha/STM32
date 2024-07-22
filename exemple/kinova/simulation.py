##########################################################################
# tghis script for robot data visulization adn the static simulation of the robt models 
# with pataerts stored in config.yml file
# all figures are saved in figure/pyDynamapp 
#
#
#
#
# TODO: replace all models computing function with 
# 'computeIdentificationModel' function from class Robot.
# Author: Wissem CHIHA ©
# 2024
##########################################################################
import sys
import os
import matplotlib.pyplot as plt 
import numpy as np 
import logging

figureFolderPath="C:/Users/chiha/OneDrive/Bureau/Dynamium/dynamic-identification/figure/kinova"
config_file_path="C:/Users/chiha/OneDrive/Bureau/Dynamium/dynamic-identification/exemple/kinova/config.yml"
src_folder = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)),'../src'))
sys.path.append(src_folder)
if not os.path.exists(figureFolderPath):
    os.makedirs(figureFolderPath)

from dynamics import Robot, Regressor, StateSpace
from utils import RobotData,  plot2Arrays, plotElementWiseArray, yaml2dict, RMSE, MAE

mlogger  = logging.getLogger('matplotlib')
logging.basicConfig(level='INFO')
mlogger.setLevel(logging.WARNING)

cutoff_frequency  = 3
config_params  = yaml2dict(config_file_path)
data           = RobotData(config_params['identification']['dataFilePath'])
fildata        = data.lowPassfilter(cutoff_frequency)
kinova         = Robot()
q_f            = fildata ['position']
qp_f           = fildata['velocity']
qpp_f          = fildata['desiredAcceleration']
current_f      = fildata['current']
torque_f       = fildata['torque']

q              = data.position
qp             = data.velocity
qpp            = data.desiredAcceleration
current        = data.current
torque         = data.torque


# Visualize the recorded trajectory data of the system.
plot2Arrays(q, q_f, "true", "filtred", f"Joints Positions, cutoff frequency = {cutoff_frequency} Hz")
plt.savefig(os.path.join(figureFolderPath,'joints_positions'))
plot2Arrays(qp, qp_f, "true", "filtred", f"Joints Velocity, cutoff frequency = {cutoff_frequency} Hz")
plt.savefig(os.path.join(figureFolderPath,'joints_velocity'))
plot2Arrays(qpp, qpp_f, "true", "filtred", f"Joints Acceleration, cutoff frequency = {cutoff_frequency} Hz")
plt.savefig(os.path.join(figureFolderPath,'joints_acceleration'))
plot2Arrays(torque, torque_f , "true", "filtred", f"Joints Torques, cutoff frequency = {cutoff_frequency} Hz")
plt.savefig(os.path.join(figureFolderPath,'joints_torques'))
plot2Arrays(current, current_f , "true", "filtred", f"Joints Current, cutoff frequency = {cutoff_frequency} Hz")
plt.savefig(os.path.join(figureFolderPath,'joints_current'))

# Visualize the Correlation between torques data
data.visualizeCorrelation('torque')
plt.savefig(os.path.join(figureFolderPath,'sensor_torques_correlation'))
data.visualizeCorrelation('torque_rne')
plt.savefig(os.path.join(figureFolderPath,'blast_rne_torques_correlation'))
data.visualizeCorrelation('torque_cur')
plt.savefig(os.path.join(figureFolderPath,'current_torques_correlation'))

# Compute and plot the RMSE between the actual RNEA model (Blast) and the 
# torque sensor output. 
rmse_joint = RMSE(torque, data.torque_rne).flatten()
rmse_time  = RMSE(torque, data.torque_rne,axis=1) 
plotElementWiseArray(rmse_joint,'Error between Blast RNEA and Sensor Torques per Joint'\
    ,'Joint Index','RMSE')
plt.savefig(os.path.join(figureFolderPath,'blast_RNEA_vs_sensor_torques'))


# Compute and plot the standard manipulator model : 
# τ = M(Θ)Θddot + C(Θ,Θp)Θp+ G(Θ) 
tau_sim = np.zeros_like(torque)
for i  in range(data.numRows):
    tau_sim[i,:] = 3*(kinova.computeDifferentialModel(q_f[i,:],qp_f[i,:],qpp_f[i,:]))
rmse_per_joint = RMSE(tau_sim,torque).flatten()
plotElementWiseArray(rmse_per_joint,"Standard Manipulator Model Error per Joint"\
    ,'Joint Index','RMSE')
plt.savefig(os.path.join(figureFolderPath,'standard_model_error_joint'))
plot2Arrays(torque_f,tau_sim,"true","simulation","Standard Manipulator Model")
plt.savefig(os.path.join(figureFolderPath,'standard_model'))


# Compute and plot the standard manipulator model with friction effect:
# τ = M(Θ)Θddot + C(Θ,Θp)Θp + G(Θ) + τf
tau_f = kinova.computeFrictionTorques(qp,q)
tau_sim = np.zeros_like(torque)
for i  in range(data.numRows):
    tau_sim[i,:] = 3*(kinova.computeDifferentialModel(q_f[i,:],qp_f[i,:],qpp_f[i,:]) + tau_f[i,:])
rmse_per_joint = RMSE(tau_sim,torque).flatten()
plotElementWiseArray(rmse_per_joint,"Standard Manipulator Model with Friction Error per Joint"\
    ,'Joint Index','RMSE')
plt.savefig(os.path.join(figureFolderPath,'standard_model_friction_error_joint'))
plot2Arrays(torque_f,tau_sim,"true","simulation","Standard manipulator model with friction")
plt.savefig(os.path.join(figureFolderPath,'standard_model_with_friction'))


# Compute and plot the standard manipulator model with stiffness:
# τ = M(Θ)Θddot + C(Θ,Θp)Θp + [k]Θ + G(Θ) 
tau_sim = np.zeros_like(torque)
for i  in range(data.numRows):
    tau_s = kinova.computeStiffnessTorques(q[i,:])
    tau_sim[i,:] = kinova.computeDifferentialModel(q_f[i,:],qp_f[i,:],qpp_f[i,:]) + tau_s
rmse_per_joint = RMSE(tau_sim,torque).flatten()
plotElementWiseArray(rmse_per_joint,"Standard Manipulator Model with Stiffness Error per Joint"\
    ,'Joint Index','RMSE')
plot2Arrays(torque_f,tau_sim,"true","simulation","Standard manipulator model with stiffness")
plt.savefig(os.path.join(figureFolderPath,'standard_model_stiffness_error_joint'))
plt.savefig(os.path.join(figureFolderPath,'standard_model_stiffness'))


# Compute and plot the standard manipulator model with stiffness and friction:
# τ = M(Θ)Θddot + C(Θ,Θp)Θp + [k]Θ + G(Θ) + τf
tau_sim = np.zeros_like(torque)
tau_f = kinova.computeFrictionTorques(qp,q)
for i  in range(data.numRows):
    tau_s = kinova.computeStiffnessTorques(q[i,:])
    tau_sim[i,:] = 3*(kinova.computeDifferentialModel(q_f[i,:],qp_f[i,:],qpp_f[i,:]) + tau_s + tau_f[i,:])
plot2Arrays(torque_f,tau_sim,"true","simulation","Standard model with stiffness and friction")
plt.savefig(os.path.join(figureFolderPath,'standard_model_stiffness_friction'))


# Compute and plot the standard manipulator model with actuator and friction:
# No torsional elastic effects Θ = q 
# τ = τm -  τf - Jm Θddot
tau_sim =np.zeros_like(torque)
tau_f = kinova.computeFrictionTorques(qp,q)
tau_m = kinova.computeActuatorTorques(q,qp,qpp)
tau_sim = tau_m - tau_f
Jm = kinova.getActuatorInertiasMatrix()
for i in range(tau_sim.shape[0]):
    tau_sim[i,:] -= Jm @ qpp[i,:]
plot2Arrays(torque_f,tau_sim,"true","simulation","Standard model with actuator and friction")
plt.savefig(os.path.join(figureFolderPath,'standard_model_actuator_friction'))


# Compute and plot the standard manipulator model with actuator, friction and stiffness
# τj = τm(q,qdot,qddot) -  τf(qdot,q) - Jm qddot
# τj = M(Θ)Θddot + C(Θ,Θp)Θp + [k](Θ-q) + G(Θ)
# solve for Θ given q from data , them simulate (2)and compare τj_sim with the real one 
# from data
K = kinova.getStiffnessMatrix()
 
# Compute and plot the standard manipulator regression model:
# τ = W Θ
reg = Regressor(kinova)
x = np.random.rand(reg.param_vector_max_size)
W = reg.computeFullRegressor(q_f,qp_f,qpp_f) 
tau_sim = (W @ x).reshape((torque.shape[0],kinova.model.nq))
plot2Arrays(torque_f,tau_sim,"true","simulation","Standard regression model")
plt.savefig(os.path.join(figureFolderPath,'standard_regression_model'))

# Compute and plot the non linear manipultaor  regression model 
# τ = f(q,qp,qpp,x) 
kinova.setIdentificationModelData(q_f,qp_f,qpp_f)
x = np.random.rand(209)
tau_sim = kinova.computeIdentificationModel(x)
plot2Arrays(torque_f,tau_sim,"true","simulation","Manipulator Non Linear model")
plt.savefig(os.path.join(figureFolderPath,'non_Linear_model'))


# Show all figures
#plt.show()

 
































""" 
tau = kinova.computeTrajectoryTorques(q,qp,qpp,-0.11*np.ones((q.shape[0],q.shape[1],6)))
plot2Arrays(data.torque_rne,tau,"blast","Pinocchoi","Blast RNEA vs Pinnochoi RNEA ")
plot2Arrays(fildata['torque'],tau,"Sensor","Pinocchoi","Sensor vs Pinnochoi RNEA ")
    def kalmanFilter(self,variable='torque'):
        Filtering Robot Data torques uisng an adaptive kalman filter
        if variable =='torque_cur':
            observations = np.transpose(self.torque_cur)
            x0 = self.torque_cur[0,:]
        elif variable == 'torque_rne':
            observations = np.transpose(self.torque_rne)
            x0 = self.torque_rne[0,:]
        elif variable =='torque':
            observations = np.transpose(self.torque)
            x0 = self.torque[0,:]
        else:
            logger.error('variable type not supported yet')
        F = np.eye(self.ndof)
        H = np.random.randn(self.ndof, self.ndof)
        Q = np.eye(self.ndof) * 0.01   
        R = np.eye(self.ndof) * 0.1   
        P = np.eye(self.ndof)   
        kf = Kalman(F, H, Q, R, P, x0)
        estimated_states, innovations = kf.filter(observations)
        
        return estimated_states, innovations
"""

 


 
