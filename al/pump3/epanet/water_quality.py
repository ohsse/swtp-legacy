import wntr

#날짜 리스트 만들기
import pandas as pd

start_date='20230620'
end_date='20231201'
date_list=pd.date_range(start=start_date, end=end_date, freq='W-MON') # D, W, M
print(date_list)





# wn = wntr.network.WaterNetworkModel('file/yc5.inp')
# # wn = wntr.network.WaterNetworkModel('file/wntr-sample-yecheon.inp')
# sim = wntr.sim.EpanetSimulator(wn)
# results = sim.run_sim()
# pressure = results.node['pressure']
# # print(pressure)
# print(results.node['pressure'].T.dtypes.axes)
# for time in pressure.T.dtypes.axes[0]:
#     print(pressure.loc[time, '1000'])
#
#     second = time % 60  # 초에서 60으로 나눈 나머지
#     minute = (time // 60) % 60  # 초를 분으로 환산하여 60으로 나눈 나머지
#     hour = time // 60 // 60  # 초를 분으로 환산하고, 그 분을 시간으로 환산한 몫
#     print(str(hour).rjust(2, '0') + ':' + str(minute).rjust(2, '0') + ':' + str(second).rjust(2, '0'))
#
# print('-----------------------')
#
# velocity = results.link['velocity']
# for time in velocity.T.dtypes.axes[0]:
#     print(velocity.loc[time, '2017075213'])
#
#     second = time % 60  # 초에서 60으로 나눈 나머지
#     minute = (time // 60) % 60  # 초를 분으로 환산하여 60으로 나눈 나머지
#     hour = time // 60 // 60  # 초를 분으로 환산하고, 그 분을 시간으로 환산한 몫
#     print(str(hour).rjust(2, '0') + ':' + str(minute).rjust(2, '0') + ':' + str(second).rjust(2, '0'))
#


# wn = wntr.network.WaterNetworkModel()
# wn.add_pattern('Head', [
#                  135.360000,135.450000,136.440000,136.760000,136.460000,135.880000,135.560000,135.520000,134.180000,133.220000,134.660000,134.610000
#                 ,135.170000,134.720000,135.510000,135.000000,135.360000,134.630000,133.870000,134.050000,134.470000,135.230000,135.240000,134.970000
#                 ,135.270000,134.320000,135.410000,135.500000,135.660000,134.730000,133.870000,134.850000,134.970000,135.130000,135.240000,134.370000
#                 ,135.170000,134.220000,135.310000,135.400000,135.560000,134.630000,133.770000,134.850000,134.970000,135.030000,135.140000,134.270000
#                 ])
# wn.add_pattern('demand', [
#                  0.750000, 0.640000, 0.270000, 0.260000, 0.360000, 0.670000,0.850000,1.110000,1.410000,1.720000,1.120000,1.280000
#                 ,1.050000,0.960000,0.840000,1.260000,1.280000,1.310000,1.190000,1.590000,1.160000,0.880000,1.300000,0.760000
#                 ,1.150000,0.360000,0.520000,1.760000,1.980000,1.110000,1.390000,1.570000,1.760000,0.980000,1.210000,0.460000
#                 ,1.250000,0.460000,0.640000,1.860000,1.080000,1.210000,1.490000,1.690000,1.860000,0.180000,1.320000,0.560000
#                 ])
#
# wn.add_junction('1000', base_demand=4.57, demand_pattern='demand', elevation=90, coordinates=(327715.75,447143.53))
# wn.add_junction('1003', base_demand=10.33, demand_pattern='demand', elevation=80.6, coordinates=(327792.10,447207.78))
#
# wn.add_reservoir('R1', base_head=1, head_pattern='Head', coordinates=(330200.56,451739.25))
#
# wn.add_pipe('2012192635', '1000', '1003', length=191.5, diameter=50, roughness=100, minor_loss=0.0, initial_status='OPEN')
# wn.add_pipe('2021329337', 'R1', '1000', length=400.5, diameter=150, roughness=100, minor_loss=0.0, initial_status='OPEN')
#
# # wn.options.hydraulic.demand_model = 'DD'	# 수요중심 유압 시뮬레이션
# wn.options.hydraulic.demand_model = 'PDD'	# 압력종속 수질 시뮬레이션
#
# sim = wntr.sim.EpanetSimulator(wn)
# results = sim.run_sim()
#
# pressure = results.node['pressure']
# pressure_at_node123 = pressure.loc[:, '1000']
# print(pressure_at_node123)
# print(pressure_at_node123.head())

