#!/usr/bin/env python
# coding: utf-8

# # Import Libraries

# In[1]:


import wntr
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
from math import sqrt
import matplotlib.pylab as plt
import pygad

# get_ipython().run_line_magic('matplotlib', 'inline')
import seaborn as sns
from scipy.stats import pearsonr

# # Load the Water Network File(*.inp)

# ![image.png](attachment:image.png)

# In[2]:


# No 한글, Units of hydraulic analysis is CMS (default)
# Encoding, UTF-8
# inp_file = 'calibrated_example/case1.inp'
inp_file = 'example/JeongWoo_GA2.inp'
wn = wntr.network.WaterNetworkModel(inp_file)

# ## Check the Water Network File

# In[3]:


num_junctions = wn.num_junctions
num_pipes = wn.num_pipes
print(num_junctions, num_pipes)

# In[4]:


# Graph the network
plt.rcParams["figure.figsize"] = (6, 10)
wntr.graphics.plot_network(wn, title=wn.name)

# ## Define the monitoring points and Check/Split the measured data
#  - Sensor_list

# In[5]:


# 소소구역 유량/압력 및 데이터로거 수집 데이터
df = pd.read_csv('example/FieldTest1.csv')  # Measured Pressure

# In[6]:


df.info()

# In[7]:


df = df.set_index(['Case'])

# In[8]:


df_DMA = pd.DataFrame(df)
df_PSensors = pd.DataFrame(df)
df_PSensors.drop(['DMA_Flow', 'DMA_Pressure'], axis=1, inplace=True)
df_DMA.drop(df_PSensors.columns, axis=1, inplace=True)

# In[9]:


df_DMA

# In[10]:


df_PSensors

# In[11]:


Logger_name = df_PSensors.columns
Logger_name1 = df_PSensors.columns[0:-1]
Logger_name2 = df_PSensors.columns[-1]

print(Logger_name1, "\n")
print(Logger_name2)

# ## Set hydraulic analysis options using WNTR

# In[12]:


analysis_end_time = 0
wn.options.time.duration = analysis_end_time
wn.options.hydraulic.demand_model = 'DDA'
"""
wn.options.hydraulic.required_pressure = 15
wn.options.hydraulic.minimum_pressure  = 3
wn.options.hydraulic.pressure_exponent = 0.5
"""

# # Set GA using GaPYD

# ## Define fitness function

# In[13]:


num_generations = 1000  # Number of generations. 1000
num_parents_mating = 100  # Number of solutions to be selected as parents in the mating pool.

sol_per_pop = 200  # Number of solutions in the population.
num_genes = len(Logger_name)  #
gene_type = [float, 3]

init_range_low = 0
init_range_high = 10

parent_selection_type = "sss"

crossover_type = "single_point"

mutation_type = "adaptive"
mutation_probability = [0.2, 0.1]


# In[17]:
def fitness_func(self, solution, solution_idx):  # maxmize fitness
    global SumErr

    print("solution_idx: " + str(solution_idx))

    # Reset the water network model
    wn.reset_initial_values()
    measured_pressure = df_PSensors[Logger_name].loc[Case]
    measured_flow = df_DMA['DMA_Flow'].loc[Case]
    reservoir = wn.get_node('1')
    reservoir.head_timeseries.base_value = df_DMA['DMA_Pressure'][Case]

    if (solution < 0).sum() > 0:
        fitness = 0
    else:
        i = 0
        solution_sum = 0
        for junction_name in Logger_name:
            junction = wn.get_node(junction_name)
            junction.demand_timeseries_list[0].base_value = solution[i] / 3600
            solution_sum = solution_sum + solution[i]
            i = i + 1

        sim = wntr.sim.EpanetSimulator(wn)
        results = sim.run_sim()
        estimated_pressure = results.node['pressure']
        estimated_demand = results.node['demand']

        # tempSumErr = abs(measured_pressure - estimated_pressure[Logger_name])**2
        # SumErr = tempSumErr.sum(axis=1)
        # fitness = 1.0 * (num_genes+1) / (SumErr[0] + 0.000001)

        if solution_sum > measured_flow:
            fitness = 0
        else:
            fitness = (pearsonr(estimated_pressure[Logger_name].loc[0], measured_pressure)[0]) ** 2
    # print("solution_idx: ",solution_idx)
    # print("solution: ", solution)
    # print("SumErr :", SumErr[0], "fitness: ", fitness)
    return fitness


# In[18]:


def on_generation(ga_instance):
    global last_fitness
    print("Generation = {generation}".format(generation=ga_instance.generations_completed))
    print("Fitness    = {fitness}".format(fitness=ga_instance.best_solution(pop_fitness=ga_instance.last_generation_fitness)[1]))
    print("Change     = {change}".format(change=ga_instance.best_solution(pop_fitness=ga_instance.last_generation_fitness)[1] - last_fitness))
    last_fitness = ga_instance.best_solution(pop_fitness=ga_instance.last_generation_fitness)[1]


# In[19]:


# number of simulation cases at once
# num_Simultaion_Case = 9 + 1
num_Simultaion_Case = 1 + 1

df_solution_fitness = pd.DataFrame({"Case": range(1, num_Simultaion_Case), "fittness": range(1, num_Simultaion_Case)})
df_solution_fitness.set_index(["Case"])

for Case in range(1, num_Simultaion_Case):
    last_fitness = 0
    print("Case_" + str(Case))
    wn.reset_initial_values()

    measured_pressure = df_PSensors[Logger_name].loc[Case]
    measured_flow = df_DMA['DMA_Flow'].loc[Case]
    reservoir = wn.get_node('1')
    reservoir.head_timeseries.base_value = df_DMA['DMA_Pressure'][Case]

    ga_instance = pygad.GA(num_generations=2,
                           num_parents_mating=num_parents_mating,
                           sol_per_pop=sol_per_pop,
                           num_genes=num_genes,
                           gene_type=gene_type,
                           fitness_func=fitness_func,
                           on_generation=on_generation,
                           init_range_low=init_range_low,
                           init_range_high=init_range_high,
                           parent_selection_type=parent_selection_type,
                           crossover_type=crossover_type,
                           mutation_type=mutation_type,
                           mutation_probability=mutation_probability,
                           stop_criteria=["saturate_7"]
                           )

    ga_instance.run()
    ga_instance.plot_fitness()

    # Returning the details of the best solution.
    solution, solution_fitness, solution_idx = ga_instance.best_solution(ga_instance.last_generation_fitness)
    print("Parameters of the best solution : {solution}".format(solution=solution))
    print("Fitness value of the best solution = {solution_fitness}".format(solution_fitness=solution_fitness))
    print("Index of the best solution : {solution_idx}".format(solution_idx=solution_idx))

    if ga_instance.best_solution_generation != -1:
        print("Best fitness value reached after {best_solution_generation} generations.".format(best_solution_generation=ga_instance.best_solution_generation))

    i = 0
    for junction_name in Logger_name:
        junction = wn.get_node(junction_name)
        junction.demand_timeseries_list[0].base_value = solution[i] / 3600
        i = i + 1

    sim = wntr.sim.EpanetSimulator(wn)
    estimated_results = sim.run_sim()
    estimated_pressure = estimated_results.node['pressure']
    estimated_demand = estimated_results.node['demand']

    if Case == 1:
        series_estimated_pressure = estimated_pressure
        series_estimated_demand = estimated_demand
    else:
        series_estimated_pressure = pd.concat([series_estimated_pressure, estimated_pressure], ignore_index=True)
        series_estimated_demand = pd.concat([series_estimated_demand, estimated_demand], ignore_index=True)

    df_solution_fitness['fittness'].loc[Case] = solution_fitness
    print(sep='\n')

# # Error Analysis

# ## Percent Errors of Demand

# In[20]:


df_solution_fitness.set_index(['Case'])

# In[21]:


series_estimated_demand['Case'] = range(1, num_Simultaion_Case)
series_estimated_demand = series_estimated_demand.set_index(['Case'])

# In[22]:


Total_estimated_demand = series_estimated_demand[Logger_name].sum(axis=1) * 3600
print(Total_estimated_demand)

# In[23]:


series_measured_flow = df_DMA['DMA_Flow'].loc[1:num_Simultaion_Case - 1]
print(series_measured_flow)

# In[24]:


error_demand = abs(Total_estimated_demand - series_measured_flow) / series_measured_flow * 100
error_demand

# In[25]:

print('result:::')
print(series_estimated_demand[Logger_name] * 3600)

# 히트맵을 그릴 격자 생성
fig, ax = plt.subplots(figsize=(12,6))

sns.heatmap(series_estimated_demand[Logger_name]*3600, # 위에서 전처리한 데이터프레임
            annot = True, # 숫자 표시 여부
            ax = ax, # 히트맵을 그릴 격자
            linewidths = 0.4, # 선의 굵기
            linecolor = 'white', # 선의 색깔
            fmt = '.1f', # 소수점 포맷팅 형태
            cmap = 'YlOrRd',
            vmin = 0, vmax = 25) # colormap 형태

plt.title('Estimated Leakage (CMH)', size = 15)
plt.ylabel('Hours', size = 13)
plt.xlabel('Sensors', size = 13)

plt.xticks(rotation=45, size = 12)
plt.yticks(size=12)
plt.show()

# ## Percent Errors of Pressure

# In[27]:


series_estimated_pressure['Case'] = range(1, num_Simultaion_Case)
series_estimated_pressure = series_estimated_pressure.set_index(['Case'])
series_estimated_pressure[Logger_name]

# In[28]:


series_measured_pressure = df_PSensors[Logger_name].loc[1:num_Simultaion_Case - 1]
print(series_measured_pressure)

# In[29]:


error_pressure = abs(series_estimated_pressure[Logger_name] - series_measured_pressure[Logger_name]) / series_measured_pressure[Logger_name] * 100
error_pressure

# In[30]:


for i in range(1, num_Simultaion_Case):
    rmse = sqrt(mean_squared_error(series_estimated_pressure[Logger_name].loc[i], series_measured_pressure.loc[i]))
    print("Case_", i, ":", rmse)

# # 히트맵을 그릴 격자 생성
# fig, ax = plt.subplots(figsize=(12,6))
#
# sns.heatmap(error_pressure, # 위에서 전처리한 데이터프레임
#             annot = True, # 숫자 표시 여부
#             ax = ax, # 히트맵을 그릴 격자
#             linewidths = 0.4, # 선의 굵기
#             linecolor = 'white', # 선의 색깔
#             fmt = '.1f', # 소수점 포맷팅 형태
#             cmap = 'YlOrRd',
#             vmin = 0, vmax = 20) # colormap 형태
#
# plt.title('Residual Error of Pressure (%)', size = 15)
# plt.ylabel('Hours', size = 13)
# plt.xlabel('Sensors', size = 13)
#
# plt.xticks(rotation=45, size = 12)
# plt.yticks(size=12)
# plt.show()
