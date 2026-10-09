import os
import wntr
import pandas as pd
import matplotlib.pylab as plt
import pygad
import seaborn as sns
from scipy.stats import pearsonr
from flask import current_app
import matplotlib.dates as DateFormatter

class GaRun:

    # 온라인 유전자 알고리즘
    def __init__(self):
        self.wn = None


    def gaRun(self, wn, gaInputData):
        try:
            df = pd.DataFrame(gaInputData.resultDict)
            df.drop(['Time'], axis=1, inplace=True)
            df = df.set_index(['Case'])

            df_DMA = pd.DataFrame(df)
            df_PSensors = pd.DataFrame(df)

            df_DMA_Columns = df_DMA.columns[0:2]
            df_PSensors.drop(df_DMA_Columns, axis=1, inplace=True)
            df_DMA.drop(df_PSensors.columns, axis=1, inplace=True)
            Logger_name = df_PSensors.columns

            df_DMA = df_DMA.apply(pd.to_numeric, errors='coerce').fillna(0)
            df_PSensors = df_PSensors.apply(pd.to_numeric, errors='coerce').fillna(0)

            analysis_end_time = 0
            wn.options.time.duration = analysis_end_time
            wn.options.hydraulic.demand_model = 'DDA'

            num_generations = int(gaInputData.numGenerations)  # Number of generations. 1000 #########
            num_parents_mating = int(gaInputData.numParentsMating)  # Number of solutions to be selected as parents in the mating pool. ##########

            sol_per_pop = 200  # Number of solutions in the population.
            num_genes = len(Logger_name)  # 절점 개수
            gene_type = [float, 3]

            init_range_low = float(gaInputData.initRangeLow) #############
            init_range_high = float(gaInputData.initRangeHigh) ###################

            parent_selection_type = "sss"

            crossover_type = "single_point"

            mutation_type = "adaptive"
            mutation_probability = gaInputData.mutationProbability #################

            reservoirId = df_DMA_Columns[0].split('_')[0]

            def fitness_func(self, solution, solution_idx):  # maxmize fitness
                # Reset the water network model
                wn.reset_initial_values()

                # print("solution_idx: " + str(solution_idx))

                measured_pressure = df_PSensors[Logger_name].loc[Case]
                measured_flow = float(df_DMA[reservoirId + '_flow'].loc[Case])
                reservoir = wn.get_node(reservoirId)
                reservoir.head_timeseries.base_value = float(df_DMA[reservoirId + '_pressure'][Case])

                if (solution < 0).sum() > 0:
                    fitness = 0
                else:
                    i = 0
                    solution_sum = 0
                    for junction_name in Logger_name:
                        junction = wn.get_node(junction_name)
                        junction.demand_timeseries_list[0].base_value = solution[i] / 3600
                        solution_sum = solution_sum + solution[i]

                    sim = wntr.sim.EpanetSimulator(wn)
                    results = sim.run_sim()
                    estimated_pressure = results.node['pressure']
                    estimated_demand = results.node['demand']

                    if solution_sum > measured_flow:
                        fitness = 0
                    else:
                        fitness = (pearsonr(estimated_pressure[Logger_name].loc[0], measured_pressure)[0]) ** 2
                return fitness

            def on_generation(ga_instance):
                global last_fitness
                last_fitness = ga_instance.best_solution(pop_fitness=ga_instance.last_generation_fitness)[1]

            # number of simulation cases at once
            num_Simultaion_Case = len(df_DMA.index) + 1

            df_solution_fitness = pd.DataFrame({"Case": range(1, num_Simultaion_Case), "fittness": range(1, num_Simultaion_Case)})
            df_solution_fitness.set_index(["Case"])

            for Case in range(1, num_Simultaion_Case):
                last_fitness = 0
                wn.reset_initial_values()

                measured_pressure = df_PSensors[Logger_name].loc[Case]
                measured_flow = float(df_DMA[reservoirId + '_flow'].loc[Case])
                reservoir = wn.get_node(reservoirId)
                reservoir.head_timeseries.base_value = float(df_DMA[reservoirId + '_pressure'][Case])

                ga_instance = pygad.GA(num_generations=num_generations,
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

                # Returning the details of the best solution.
                solution, solution_fitness, solution_idx = ga_instance.best_solution(ga_instance.last_generation_fitness)

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

            df_solution_fitness.set_index(['Case'])

            series_estimated_demand['Time'] = gaInputData.resultDict["Time"]
            series_estimated_demand = series_estimated_demand.set_index(['Time'])

            # result
            self.resultDataFrame = series_estimated_demand[Logger_name] * 3600
            print(self.resultDataFrame)

            # 히트맵을 그릴 격자 생성
            fig, ax = plt.subplots(figsize=(12, 6))

            # dateFmt = DateFormatter('%m-%dT%H:%M')
            # dateFmt = DateFormatter('%Y/%m/%d')
            # ax.yaxis.set_major_formatter(dateFmt)

            sns.heatmap(series_estimated_demand[Logger_name] * 3600,  # 위에서 전처리한 데이터프레임
                        annot=True,  # 숫자 표시 여부
                        ax=ax,  # 히트맵을 그릴 격자
                        linewidths=0.4,  # 선의 굵기
                        linecolor='white',  # 선의 색깔
                        fmt='.1f',  # 소수점 포맷팅 형태
                        cmap='YlOrRd',
                        vmin=0, vmax=25)  # colormap 형태

            plt.title('Estimated Leakage (CMH)', size=15)
            plt.ylabel('Time', size=13)
            plt.xlabel('Sensors', size=13)
            # TODO 폰트 크기 및 종류를 변경해 사진 상 글씨가 잘 보이도록 조정
            plt.xticks(rotation=45, size=12)
            plt.yticks(rotation=45, size=12)
            os.makedirs("/was1/waternet/upload/rpt/ga/", exist_ok=True)
            plt.savefig('/was1/waternet/upload/rpt/ga/' + gaInputData.rptNumber + '.png')
            # plt.show()
        except Exception as ex:
            print("[ERROR] onlineGaRun: ", ex)
            current_app.logger.error(ex)
            raise
