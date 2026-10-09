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


# # Import the Water Network File(*.inp)

# ![image.png](attachment:image.png)

# In[2]:


# No 한글, Units of hydraulic analysis is CMS (default)
inp_file = 'example/JeongWoo_GA.inp'
wn = wntr.network.WaterNetworkModel(inp_file)


# ## Check the Network

# In[3]:


num_junctions = wn.num_junctions
num_pipes = wn.num_pipes
print(num_junctions, num_pipes)


# In[4]:


# Graph the network
plt.rcParams["figure.figsize"] = (6,10)
wntr.graphics.plot_network(wn, title=wn.name)


# ## Define the monitoring points
#  - Sensor_list

# In[5]:


Sensing_points_flow = pd.read_csv('example/sample_flow.csv') #Measured Flow
Sensing_points_pressure = pd.read_csv('example/sample_pressure.csv') #Measured Pressure


# In[6]:


Sensing_points_flow.info()


# In[7]:


Sensing_points_pressure.info()


# - Delete unnecessary data

# In[8]:


Sensing_points_pressure.drop(['Unnamed: 0'], axis = 1, inplace = True)
Sensing_points_pressure.drop(['Time'], axis = 1, inplace = True)
Sensing_points_flow.drop(['Time'], axis = 1, inplace = True)


# In[9]:


#Sensing_points = wn.query_node_attribute('base_demand', np.greater, 0)
#Sensing_points = list(Sensing_points.index)
Sensing_points = ['YeDong', 'MaHang', 'KukJeong', 'ChangJeon', 'PoRyong', 'PoRyong2', 'HwangJeon']


# ## Set hydraulic analysis options

# In[10]:


analysis_end_time = 0
wn.options.time.duration = analysis_end_time
wn.options.hydraulic.demand_model = 'PDA'
wn.options.hydraulic.required_pressure = 15
wn.options.hydraulic.minimum_pressure  = 3
wn.options.hydraulic.pressure_exponent = 0.5


# ### Calculate the pressure for whole network

# In[11]:


for i in Sensing_points:
    junction = wn.get_node(i)
    junction.demand_timeseries_list[0].base_value = Sensing_points_flow[i].loc[0]/3600
    
sim = wntr.sim.EpanetSimulator(wn)
results = sim.run_sim()
measured_pressure = results.node['pressure']
measured_demand = results.node['demand']


# In[12]:


measured_demand[Sensing_points]


# In[13]:


def fitness_func(solution, solution_idx):
    # Reset the water network model
    wn.reset_initial_values()
    i = 0
    for junction_name in Sensing_points:
        junction = wn.get_node(junction_name)
        
        if solution[i] >=0:
            junction.demand_timeseries_list[0].base_value = solution[i]
        else:
            junction.demand_timeseries_list[0].base_value = 100
        i = i + 1
        
    sim = wntr.sim.EpanetSimulator(wn)
    results = sim.run_sim()
    estimated_pressure = results.node['pressure']
    estimated_demand = results.node['demand']
    '''
    rms_bomb = 0
    for junction_name in Sensing_points:
        if estimated_pressure[junction_name] < 0:
            rms_bomb = rms_bomb + 1
        else:
            rms_bomb = rms_bomb + 0
            
    if rms_bomb > 0 :
        rms = 1000000
    else:
        rms = sqrt(mean_squared_error(measured_pressure[Sensing_points], estimated_pressure[Sensing_points]))
    '''
    #rms = sqrt(mean_squared_error(measured_pressure[Sensing_points], estimated_pressure[Sensing_points]))
    rms = sqrt(mean_squared_error(measured_pressure, estimated_pressure))
    fitness = 1.0 / (rms + 0.000001)
    
    return fitness


# In[14]:


num_generations = 100 # Number of generations.
num_parents_mating = 20 # Number of solutions to be selected as parents in the mating pool.

sol_per_pop = 200 # Number of solutions in the population.
num_genes = len(Sensing_points)

init_range_low = 0
init_range_high = 0.1

parent_selection_type = "sss"
keep_parents = 1

crossover_type = "single_point"

mutation_type = "random"
mutation_percent_genes = 10


# In[15]:


last_fitness = 0
def on_generation(ga_instance):
    global last_fitness
    print("Generation = {generation}".format(generation=ga_instance.generations_completed))
    print("Fitness    = {fitness}".format(fitness=ga_instance.best_solution(pop_fitness=ga_instance.last_generation_fitness)[1]))
    print("Change     = {change}".format(change=ga_instance.best_solution(pop_fitness=ga_instance.last_generation_fitness)[1] - last_fitness))
    last_fitness = ga_instance.best_solution(pop_fitness=ga_instance.last_generation_fitness)[1]


# In[16]:


ga_instance = pygad.GA(num_generations=num_generations,
                       num_parents_mating=num_parents_mating,
                       sol_per_pop=sol_per_pop,
                       num_genes=num_genes,
                       fitness_func=fitness_func,
                       on_generation=on_generation,
                       init_range_low=init_range_low,
                       init_range_high=init_range_high,
                       parent_selection_type = parent_selection_type,
                       keep_parents = keep_parents,
                       crossover_type = crossover_type,
                       mutation_type = mutation_type,
                       mutation_percent_genes = mutation_percent_genes
                      )


# In[17]:


# Running the GA to optimize the parameters of the function.
ga_instance.run()


# In[18]:


ga_instance.plot_fitness().show()


# In[19]:


# Returning the details of the best solution.
solution, solution_fitness, solution_idx = ga_instance.best_solution(ga_instance.last_generation_fitness)
print("Parameters of the best solution : {solution}".format(solution=solution))
print("Fitness value of the best solution = {solution_fitness}".format(solution_fitness=solution_fitness))
print("Index of the best solution : {solution_idx}".format(solution_idx=solution_idx))


# In[20]:


wn.reset_initial_values()
i = 0
for junction_name in Sensing_points:
    junction = wn.get_node(junction_name)
    junction.demand_timeseries_list[0].base_value = solution[i]
    i = i + 1
    
sim = wntr.sim.EpanetSimulator(wn)
results = sim.run_sim()
estimated_pressure = results.node['pressure']
estimated_demand = results.node['demand']


# # Error

# ## Demand Error

# In[21]:


error_demand = abs((estimated_demand[Sensing_points] - measured_demand[Sensing_points])/
                   (estimated_demand[Sensing_points] + 0.000001)*100)
error_demand


# In[22]:


estimated_demand[Sensing_points]


# In[23]:


measured_demand[Sensing_points]


# ## Pressure Error

# In[24]:


error_pressure = abs((estimated_pressure[Sensing_points] - measured_pressure[Sensing_points])/
                     (estimated_pressure[Sensing_points]+ 0.000001)*100)
error_pressure


# In[25]:


estimated_pressure[Sensing_points]


# In[26]:


measured_pressure[Sensing_points]

