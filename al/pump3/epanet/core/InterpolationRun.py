import os
import numpy as np
from matplotlib import pyplot as plt
from scipy.interpolate import griddata
from sklearn.neighbors import KNeighborsRegressor


class InterpolationRun:

    # 수용가 안심확인제 보간법
    def __init__(self):
        self.masterDict = {}
        self.safetyConfirmMinMaxXyDict = {}
        self.safetyConfirmList = []
        self.reportDict = {}
        self.grid_size = 100 # 파라미터 정의 필요함

    def interpolationRun(self, safetyConfirmData):
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] = False

        self.masterDict = safetyConfirmData.masterDict
        self.safetyConfirmMinMaxXyDict = safetyConfirmData.safetyConfirmMinMaxXyDict
        self.safetyConfirmList = safetyConfirmData.safetyConfirmList

        xList = safetyConfirmData.xList
        yList = safetyConfirmData.yList
        tList = safetyConfirmData.tList
        cList = safetyConfirmData.cList
        gList = safetyConfirmData.gList
        pList = safetyConfirmData.pList
        jList = safetyConfirmData.jList
        aList = safetyConfirmData.aList
        zList = []
        try:
            measurementUnitList = ["t", "c", "g", "p", "j", "a"]
            measurementUnitNameList = ["탁도", "철", "구리", "PH", "잔류염소", "아연"]

            ## 관측된 데이터를 이용하여 격자 데이터 생성
            x_range = np.linspace(float(self.safetyConfirmMinMaxXyDict["maxX"]), float(self.safetyConfirmMinMaxXyDict["minX"]), self.grid_size)  ## x 범위
            y_range = np.linspace(float(self.safetyConfirmMinMaxXyDict["maxY"]), float(self.safetyConfirmMinMaxXyDict["minY"]), self.grid_size)  ## y 범위
            X, Y = np.meshgrid(x_range, y_range)  ## XY 격자 데이터

            self.reportDict["analsNo"] = safetyConfirmData.analsNo
            self.reportDict["x"] = X
            self.reportDict["y"] = Y

            mIndex = 0
            for measurementUnit in measurementUnitList:
                zList = eval(measurementUnit + "List")
                print(zList)

                x = np.array(xList, float)
                y = np.array(yList, float)
                z = np.array(zList, float)

                points = np.c_[x, y]
                Z = griddata(points, z, (X, Y), method='linear')  ## Z 격자 데이터

                reg = KNeighborsRegressor(n_neighbors=5, weights='distance').fit(np.c_[X[Z == Z], Y[Z == Z]], Z[Z == Z])
                fill_z = reg.predict(np.c_[X[Z != Z], Y[Z != Z]])
                Z[Z != Z] = fill_z

                fig = plt.figure(figsize=(8, 8))
                fig.set_facecolor('white')
                ax = fig.add_subplot()
                contour1 = ax.contour(X, Y, Z, levels=10, colors='k', linewidths=1, linestyles='--')  ## 등고선
                contour2 = ax.contourf(X, Y, Z, levels=256, cmap='jet')

                ax.clabel(contour1, contour1.levels, inline=True)  ## contour 라벨
                fig.colorbar(contour2, shrink=0.5)  ## 컬러바 크기 축소 shrink
                ax.scatter(x, y, color='k', alpha=0.5, s=10)

                plt.title('안심확인제-' + measurementUnitNameList[mIndex] + ' 보간 데이터', pad=10)
                plt.xlabel('X 좌표', labelpad=10)
                plt.ylabel('Y 좌표', labelpad=10)

                plt.grid()
                os.makedirs("/was1/waternet/upload/rpt/interpolation/", exist_ok=True)
                plt.savefig('/was1/waternet/upload/rpt/interpolation/' + safetyConfirmData.analsNo + '_' + measurementUnit + '.png')
                mIndex = mIndex + 1

                # repostDict 수질결과 set
                self.reportDict[measurementUnit] = Z.tolist()
        except Exception as ex:
            print("[ERROR] interpolationRun: ", ex)
            raise
