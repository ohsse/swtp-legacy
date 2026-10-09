from pymysql.cursors import DictCursor
import re
import pandas as pd
import numpy as np

class FitPumpPerformanceCurve():
    import pandas as pd
    import numpy as np
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler

    def __init__(self, pumpAttr, pumpTags):
        # get tags used by the pump, all tags used by algorithm
        self.pumpAttr, self.pumpTags = pumpAttr, pumpTags

        # group numbers used by the pump
        self.group = self.pumpAttr.loc['PUMP_GRP'].unique()
        self.group.sort()
        self.KelvinT = 273.15 # 캘빈 온도 상수값 정의


    def rho_water(self, T):
        # 기온에 따른 rho 값 계산 
        rho = 9.998395639 * self.np.power(10, 2) + (6.798299989 / 100) * T
        rho = rho - 9.106025564 / self.np.power(10, 3) * self.np.power(T, 2)
        rho = rho + 1.005272999 / self.np.power(10, 4) * self.np.power(T, 3)
        rho = rho - 1.126713526 / self.np.power(10, 6) * self.np.power(T, 4)
        rho = rho + 6.591795606 / self.np.power(10, 9) * self.np.power(T, 5)
        return rho

    def group_tags(self, name, group):
        # 펌프 그룹별로 태그명 정리
        names = []
        if name in self.pumpAttr.iloc[:, 0].keys():
            isTag = True
        else:
            isTag = False

        for key, val_dic in self.pumpAttr.items():
            if val_dic['PUMP_GRP'] == group:
                val = val_dic[name] if isTag else '%s-%d' % (name, key)
                names.append(val)

        return names

    def load_names(self, idx):
        # totPWI_Gx 는 pumpGroup 별로 총 전력값을 계산한 값임
        # totPWI_G1은 pumpGroup이 1인 모든 펌의 전체 전력값임

        idx = idx[0] if isinstance(idx, list) else idx
        g = self.pumpAttr[idx]['PUMP_GRP']
        Qnm = self.pumpAttr[idx]['FRI_TAG'] # 유량 태그값 가져오기
        Hnm = 'tot_diff_head_G%d' % (g)
        Pnm = 'totPWI_G%d' % (g)
        Tnm = self.pumpAttr[idx]['TEI_TAG']  # 기온 태그값 가져오기
        Fnm = self.pumpAttr[idx]['SPI_TAG'] # 주파수 태그값 가져오기
        # xmin, xmax are temporary vaiable
        xmin = 0
        xmax = 3000
        if g == 1:
            xmax = 8000
        return Qnm, Hnm, Pnm, Tnm, Fnm, xmin, xmax

    def load_qpth(self, tmp, idx):
        Qnm, Hnm, Pnm, Tnm, Fnm, xmin, xmax = self.load_names(idx)
        return tmp[Qnm].copy(), tmp[Pnm].copy(), tmp[Tnm].copy(), tmp[Hnm].copy()

    def load_qpthf(self, tmp, idx):
        Qnm, Hnm, Pnm, Tnm, Fnm, xmin, xmax = self.load_names(idx)
        return tmp[Qnm].copy(), tmp[Pnm].copy(), tmp[Tnm].copy(), tmp[Hnm].copy(), tmp[Fnm].copy()

    def load_masked_qpth(self, tmp, mask, idx):
        Qnm, Hnm, Pnm, Tnm, Fnm, xmin, xmax = self.load_names(idx)

        q = tmp[mask][Qnm]; # 유량 데이터 취합
        h = tmp[mask][Hnm]  # 양정 데이터 취합
        p = tmp[mask][Pnm]; # 전력 데이터 취합
        t = tmp[mask][Tnm]  # 기온 데이터 취합

        p = p.replace(0, self.np.nan)

        # 하나의 데이터프레임으로 취합
        data = self.pd.concat([q, h, p, t], axis=1) 
        data = data.dropna()
        
        h = data[Hnm];
        p = data[Pnm];
        t = data[Tnm]
        return q.copy(), p.copy(), t.copy(), h.copy()

    def load_masked_qpthf(self, tmp, mask, idx):
        # 펌프 마스터 테이블에 들어있는 모든 태그를 시간값(1분단위)를 인덱스로 가지는 데이터프레임 (tmp 변수임) 에서 
        # 알맞은 태그 데이터만 추림 (컬럼별)

        Qnm, Hnm, Pnm, Tnm, Fnm, xmin, xmax = self.load_names(idx)
        q = tmp[mask][Qnm];
        h = tmp[mask][Hnm]
        p = tmp[mask][Pnm];
        t = tmp[mask][Tnm];
        f = tmp[mask][Fnm]
        p = p.replace(0, self.np.nan)

        data = self.pd.concat([q, h, p, t, f], axis=1)
        data = data.dropna()
        q = data[Qnm];
        h = data[Hnm];
        p = data[Pnm];
        t = data[Tnm];
        f = data[Fnm]
        return q.copy(), p.copy(), t.copy(), h.copy(), f.copy()

    def select_pump(self, tdf, pumpList=[1, 2, 3, 4]):
        g = []
        pumpList = [pumpList] if isinstance(pumpList, int) else pumpList

        for i in pumpList:
            g.append(self.pumpAttr[i]['PUMP_GRP'])
        g = list(set(g))

        if len(g) > 1:
            return 'Check input Pump Group!!'
        else:
            g = g[0]

        # 태그 데이터 전처리
        accept_tags = []
        for nm in pumpList:
            accept_tags.append(self.pumpAttr[nm]['PMB_TAG'])
        # 제외할 태그들 목록 산출
        except_tags = set(self.group_tags('PMB_TAG', g)) - set(accept_tags)

        for idx, tag in enumerate(accept_tags):
            if idx == 0:
                mask = (tdf[tag] == 1)
            else:
                mask = mask & (tdf[tag] == 1)

        for idx, tag in enumerate(except_tags):
            mask = mask & (tdf[tag] == 0)
        # 필터하여 해당하는 데이터만 취합
        return mask.copy()

    def __sampling(self, x, y):
        # 불러온 시계열 데이터를 모두 사용하는 것이 아니고, 랜덤하게 샘플링하여 사용함
        # DBSCAN 모델 이용

        # #############################################################################
        # Generate sample data
        
        # 만약 y의 길이가 1000 미만인 경우, 샘플링 하지 않음
        if len(y) < 1000:
            return self.np.array(list(zip(x, y)))

        # 데이터가 충분히 많은 경우, 샘플링을 수행
        else:
            X = self.np.array(list(zip(x, y))) # x, y 데이터를 하나의 배열로 결합
            scaler = self.StandardScaler()  # 데이터 정규화를 위한 StandardScaler를 초기화합니다.
            scaler.fit(X)  # X 데이터에 대해 스케일러를 학습시킵니다.
            X = scaler.transform(X) # 데이터 정규화

            # #############################################################################
            # Compute DBSCAN
            X[np.isnan(X)]= X[~np.isnan(X)].mean() #TEMP!

            db = self.DBSCAN(eps=0.1, min_samples=10).fit(X) # # DBSCAN 알고리즘을 사용하여 클러스터링을 수행
            core_samples_mask = self.np.zeros_like(db.labels_, dtype=bool) # # 핵심 샘플 마스크를 초기화
            core_samples_mask[db.core_sample_indices_] = True # # 핵심 샘플에 대한 마스크를 설정

            X = scaler.inverse_transform(X) # 정규화된 데이터를 원래의 스케일로 복원
            return X[core_samples_mask]  # 핵심 샘플만을 선택하여 반환

    def __QH_fit_function(self, x, a, b, c, d):
        # 유량 전력 예측시 회귀 방정식 정의
        return a * (self.np.power(x, 3) + b * self.np.power(x, 2) + c * x) + d

    def Head_fitting_ftn(self, x, y, dutyQ, dutyH):
        from scipy.optimize import curve_fit
        X = self.__sampling(x, y)

        bounds = (
            (-1 / (2 * self.np.power(dutyQ, 2)), dutyH / (2 * self.np.power(dutyQ, 2)), -dutyH / dutyQ, dutyH), \
            #(0, 2 * dutyH / (2 * self.np.power(dutyQ, 2)), 0, 90)
            (0, 2 * dutyH / (2 * self.np.power(dutyQ, 2)), 0, dutyH * 2) #TEMP!
        )
        #TEMP!
        _X = X[:, 0]
        _Y = X[:, 1]

        _X[np.isnan(_X)] = _X[~np.isnan(_X)].mean()
        _Y[np.isnan(_Y)] = _Y[~np.isnan(_Y)].mean()

        popt, pcov = curve_fit(self.__QH_fit_function, _X, _Y, bounds=bounds)
        _list = popt[0] * self.np.array([1, popt[1], popt[2], popt[3] / popt[0]])

        return self.np.poly1d(_list)

    def Power_fitting_ftn(self, x, y):
        X = self.__sampling(x, y)
        #TEMP!
        _X = X[:, 0]
        _Y = X[:, 1]

        _X[np.isnan(_X)] = _X[~np.isnan(_X)].mean()
        _Y[np.isnan(_Y)] = _Y[~np.isnan(_Y)].mean()
        print(_X)
        print(_Y)
        e = self.np.poly1d(self.np.polyfit(_X, _Y, 1))
        return e

    def Power_fitting_ftn_inv(self, x, y):
        X = self.__sampling(x, y)
        e = self.np.poly1d(self.np.polyfit(X[:, 0], X[:, 1], 2))
        return e

    def eta_fitting_ftn(self, x, y):
        X = self.__sampling(x, y)
        e = self.np.poly1d(self.np.polyfit(X[:, 0], X[:, 1], 2))
        return e

    def inv_fitting_ftn(self, x, y):
        # 주어진 x(유량)와 y(양정 또는 전력) 데이터에 대해 2차 다항식 회귀 적합 수행
        # 적합된 모델은 인버터 펌프의 성능을 나타내는 데 사용
        from scipy.optimize import curve_fit
        def inv_2nd_head_ftn(x, a, b, c):
            # 2차 다항식 모델 함수를 정의합니다.
            # x: 독립 변수 (유량), a, b, c: 다항식의 계수
            return a * x * x + b * x + c

        X = self.__sampling(x, y)

        # 적합할 계수의 범위를 지정합니다. a의 범위는 -무한대부터 0까지, b의 범위는 0부터 0.001까지, c의 범위는 55부터 200까지로 설정합니다.
        bounds = ((-self.np.inf, 0, 55), (0, 0.001, 200))
        # bounds = ((-self.np.inf, 0, 55), (0, 0.001, 500))

        # curve_fit 함수를 사용하여 inv_2nd_head_ftn 모델에 대한 데이터의 적합을 수행합니다.
        # X[:, 0]는 유량 데이터, X[:, 1]은 양정 또는 전력 데이터입니다.
        popt, pcov = curve_fit(inv_2nd_head_ftn, X[:, 0], X[:, 1], bounds=bounds)

         # 적합 결과로 얻은 계수를 사용하여 2차 다항식 객체를 생성하고 반환합니다.
        return self.np.poly1d(popt)

    def __fitting(self, pi, rq, y, ftype):

    #특정 펌프에 대한 데이터 학습을 수행하는 것으로 보임
    # 주어진 유량(rq)과 양정 데이터(y['h'])를 바탕으로 양정 적합 함수(Head_fitting_ftn)를 사용하여 모델을 계산하고, 
    # 이 모델의 첫 번째 계수가 0보다 작은 경우에만 해당 모델을 유효한 것으로 간주합니다. 
    # 'p' 유형(전력)의 경우에는 주어진 유량(rq)과 전력 데이터(y['p'])를 바탕으로 전력 적합 함수(Power_fitting_ftn)를 사용하여 모델을 계산하고, 
    # 이 모델의 첫 번째 계수가 0보다 큰 경우에만 해당 모델을 유효한 것으로 간주합니다. 그 외의 경우에는 적합 모델을 None으로 설정. 
    # 이렇게 계산된 모델은 펌프 성능의 분석 및 예측에 사용
        if ftype == 'h':
            # 'h' 유형의 경우 (양정 학습):
            dh = self.pumpAttr[pi]['DUTY_H'] or 1 
            dq = self.pumpAttr[pi]['DUTY_Q'] or 1 
            e = self.Head_fitting_ftn(rq, y[ftype], dq, dh) # # 양정 적합 함수를 사용하여 모델(e)을 계산
            e = e if e.coef[0] < 0 else None
        elif ftype == 'p':
            # 'p' 유형의 경우 (전력 학습):
            e = self.Power_fitting_ftn(rq, y[ftype])
            e = e if e.coef[0] > 0 else None
        else:
            e = None

        return e

    def __fitting_inv(self, pi, rq, y, ftype):
        if ftype == 'h':
            e = self.inv_fitting_ftn(rq, y[ftype])
            #e = e if e.coef[0] < 0 else None
        elif ftype == 'p':
            print('rq: ', rq) 
            print('y: ', y[ftype])
            e = self.Power_fitting_ftn_inv(rq, y[ftype])
            #e = e if e.coef[0] > 0 else None
        else:
            e = None

        return e
    
    def calc_diff_head(self, tmp):
        # 개별 펌프의 양정 계산
        for key, val_dic in self.pumpAttr.items():
            # 양정 계산하여 저장할 컬럼 이름 파싱
            nm = 'diff_head-%d' % (key)

            # 흡입압력 데이터 취합
            PRId = val_dic['PRI_D_TAG'] 
            # 토출압력 데이터 취합
            PRIs = val_dic['PRI_S_TAG'] 
            # 기온 데이터 취함
            TEI  = val_dic['TEI_TAG'] 

            print(val_dic['PRI_T_TAG'])

            # 압력 데이터가 없으면 LEI 데이터를 이용함
            if (PRId is None or PRId == '') | (PRIs is None or PRIs == ''):
                PRIt = val_dic['PRI_T_TAG']
                LEI = val_dic['LEI_TAG']
                tmp[nm] = tmp[PRIt] * 1e+4 / self.rho_water(tmp[TEI]) - (tmp[LEI] - 3.)
            else :
                tmp[nm] = (tmp[PRId] - tmp[PRIs]) * 1e+4 / self.rho_water(tmp[TEI])

        # 통합 diff. head
        for g in self.group:
            gNM = 'tot_diff_head_G%d' % (g)
            gtags = self.group_tags('diff_head', g)
            pumpGroup = self.group_tags('PMB_TAG', g)
            t1 = tmp[pumpGroup].copy()
            t1.columns = gtags
            tmp[gNM] = (tmp[gtags] * t1).replace(0, self.np.NaN)[gtags].mean(axis=1)
            #tmp[gNM] = (tmp[gtags] * 1).replace(0, self.np.NaN)[gtags].mean(axis=1) #TEMP!

        # 통합 전력 사용량 계산
        for g in self.group:
            gNM = 'totPWI_G%d' % (g)
            # 각 정수지 그룹별로 총 전력 계산
            gtags = self.group_tags('PWI_TAG', g)
            pumpGroup = self.group_tags('PMB_TAG', g)
            # 펌프 동작 유무 데이터 참조하여 0 일시 해당 전력 계산되지 않도록함
            t1 = tmp[pumpGroup].copy()
            t1.columns = gtags
            tmp[gNM] = (tmp[gtags] * t1).replace(0, self.np.NaN)[gtags].sum(axis=1) 

        return tmp

    def calc_equationTable_NonInv(self, tmp, ftype='h', pump_list=range(1, 5), st_date='2020-06-01'):
        # 노말 펌프 성능 계수 산출
        # ftype이 h 인경우 EQ_TYPE 이 QH 계수 산출, p인경우 QP 계수 산출
        # QH: 양정 계산시 사용되는 계수, QP: 전력 계산시 사용되는 계수로 추정됨
        maxT = 35
        eqTable = self.pd.DataFrame(index=self.np.arange(1, maxT, 1), columns=pump_list)

        for temp in self.np.arange(1, maxT, 1): 
            for pi in pump_list:
                tTag = self.pumpAttr[pi]['TEI_TAG']
                mask = (tmp[tTag] > temp - 2) & (tmp[tTag] < temp + 2)  # & (tmp.index > self.pd.to_datetime(st_date)) 임시 제외
                pump_mask = self.select_pump(tmp, [pi])
                # mask = mask & pump_mask
                mask = mask 
                #print(tmp[["780-344-FIT-2501","780-344-TEI-2001"]])
                q, p, t, h = self.load_masked_qpth(tmp, mask, pi)
                #rq = q * (self.KelvinT + t) / 290.
                rq = q #TODO

                ydic = {'p': p, 'h': h}

                if len(q) > 1e+3:
                    e = self.__fitting(pi, rq, ydic, ftype=ftype)
                    eqTable.loc[temp][pi] = e
        
        eqTable = self.__fill_equationTable(eqTable, pump_list=pump_list, ftype=ftype)
        eqTable = self.__reduced_equationTable(eqTable, pump_list=pump_list)
        print(eqTable)
        return eqTable

    def calc_equationTable_Inv(self, tmp, ftype='h', pump_list=range(5, 7), st_date='2020-06-01'):
        # 인버터 펌프 성능 계수 산출
        # ftype이 h 인경우 EQ_TYPE 이 QH 계수 산출, p인경우 QP 계수 산출
        # QH: 양정 계산시 사용되는 계수, QP: 전력 계산시 사용되는 계수로 추정됨
        # 이 함수는 인버터 펌프 성능 계수를 계산합니다.
        # 'pump_list' 매개변수는 계산에 포함할 펌프들을 지정합니다.
        # 'st_date' 매개변수는 데이터를 고려하기 시작하는 날짜를 정의합니다.
        # 실제 계산과 적합은 `__fitting_inv`, `load_masked_qpthf` 같은 메소드에서 처리
        freq_list = []

        # 펌프 리스트에 있는 각 펌프에 대해 반복
        for pi in pump_list:
            fTag = self.pumpAttr[pi]['SPI_TAG'] # # 펌프의 SPI_TAG 속성을 가져옴
            ref_freq = tmp[fTag].round(1).value_counts().index[0] # 주파수 값을 소수 첫째 자리까지 반올림하고 가장 빈도가 높은 값 선택
            ref_freq = max(ref_freq, 0.1)

            freq_list.append(ref_freq)

        #     # 주파수를 인덱스로, 펌프들을 컬럼으로 하는 DataFrame을 생성
        eqTable = self.pd.DataFrame(index=freq_list, columns=pump_list)

        for pi in pump_list:
            fTag = self.pumpAttr[pi]['SPI_TAG']
            ref_freq = tmp[fTag].round(1).value_counts().index[0]

            # 참조 주파수에 가까운 데이터 포인트와 시작 날짜 이후의 데이터에 대한 마스크를 생성
            mask = (tmp[fTag] > ref_freq - 0.1) & (tmp[fTag] < ref_freq + 0.1) & (
                        tmp.index > self.pd.to_datetime(st_date))

            ref_freq = max(ref_freq, 0.1)
            #mask = mask & self.select_pump(tmp, [pi]) #TODO CHEck!
            q, p, t, h, f = self.load_masked_qpthf(tmp, mask, pi)  # 마스킹된 데이터를 로드합니다 (유량, 전력, 시간, 양정, 주파수).
            ydic = {'p': p, 'h': h}
            if len(q) > 1e+3:
                e = self.__fitting_inv(pi, q, ydic, ftype=ftype)
                print(e)
                eqTable.loc[ref_freq][pi] = e  # 적합 결과를 eqTable DataFrame에 저장합니다.

        return eqTable

    def __fill_equationTable(self, eqTable, pump_list, ftype):
        # 주어진 펌프 목록에 대해 QH 값을 계산하고 eqTable을 채움
        # eqTable은 각 펌프 및 해당 주파수에 대한 다항식 계수를 포함
        # ftype은 계산하고자 하는 계수 유형을 지정 ('h' 또는 'p').
        # 각 펌프 별로 QH 값 계산
        x = self.np.arange(0, 4000, 50) # 0부터 4000까지 50 간격의 배열을 생성

        for pi in pump_list:
            TF = True
            for i, tdf in eqTable.iterrows():
                # tdf[pi]가 np.poly1d 타입인 경우 (즉, 다항식 계수가 있는 경우),
                if type(tdf[pi]) == type(self.np.poly1d([1])):
                    reducedQ = x * (self.KelvinT + i) / 290. # # x 값(유량)을 수정합니다 (캘빈값 이용하여 온도 보정).
                    reducedH = tdf[pi](x * (self.KelvinT + i) / 290.)
                    arr = self.np.array(list(zip(reducedQ, reducedH)))
                    if TF:
                        QH = arr
                        TF = False
                    else:
                        QH = self.np.r_[QH, arr]

            # 최종적으로 계산된 QH 데이터에서 Q와 H 값을 분리
            rq = QH[:, 0];
            ydic = {ftype: QH[:, 1]}
            eq = self.__fitting(pi, rq, ydic, ftype=ftype)

            # eqTable의 각 행에 대해 반복하며,
            # tdf[pi]가 np.poly1d 타입이 아닌 경우 (즉, 다항식 계수가 없는 경우),
            # eqTable에 계산된 다항식(eq)을 할당합니다.
            for i, tdf in eqTable.iterrows():
                if not type(tdf[pi]) == type(self.np.poly1d([1])):
                    eqTable[pi][i] = eq

        return eqTable  # 완성된 eqTable을 반환

    def __reduced_equation(self, e, t):
        r = (self.KelvinT + t) / 290.
        coef = []
        l = len(e.coef) - 1
        for i, ecoef in enumerate(e.coef):
            coef.append(ecoef * self.np.power(r, l - i))

        return self.np.poly1d(coef)

    def reduced_equation(self, e, t):
        return self.__reduced_equation(e, t)

    def __reduced_equationTable(self, eqTable, pump_list):
        reducedPP = eqTable.copy()
        for pi in pump_list:
            for i, tdf in eqTable.iterrows():
                reducedPP[pi][i] = self.__reduced_equation(tdf[pi], i)

        return reducedPP

    def __write_eqTable(self, QH, QP, PumpType, date):
        # 이 함수는 계산된 QH(양정 계수) 및 QP(전력 계수)를 CSV 파일로 저장
        # QH와 QP는 각각 양정 및 전력에 대한 성능 계수를 포함하는 DataFrame
        # PumpType은 펌프 유형을 나타내며, 'Inv'인 경우 인버터 펌프를 의미
        # date: 분석 날짜

            # 조건 유형(CondType)을 설정합니다. 인버터 펌프의 경우 'FREQ'(주파수), 그 외는 'WTR_TEMP'(수온)입니다. 
        CondType = 'FREQ' if PumpType == 'Inv' else 'WTR_TEMP'
        eqs = {'QH': QH, 'QP': QP}
        for key, eqT in eqs.items():
            eqT[CondType] = eqT.index
            eqT = eqT.melt(id_vars=CondType, var_name='PMP_IDX', value_name='Eq')
            eqT['PRFRM_COEFF'] = eqT['Eq'].apply(lambda x: self.__coef_to_str(x)) # 성능 계수를 문자열로 변환합니다.
            eqT['DC_NMB'] = 'Docker#1'
            eqT['ANLY_DATE'] = date 
            eqT['EQ_TYP'] = key # 계수 유형(QH 또는 QP)을 설정합니다.
            if key == 'QH':
                eq = eqT[['ANLY_DATE', 'EQ_TYP', CondType, 'PMP_IDX', 'PRFRM_COEFF', 'DC_NMB']]
            else:
                eq = self.pd.concat([eq, eqT]) # QH와 QP 데이터를 하나의 DataFrame으로 결합합니다.

            # 필요한 열만 선택하고 NaN 값을 제거한 후 최종 DataFrame(eq)을 생성합니다.
        eq = eq[['ANLY_DATE', 'EQ_TYP', CondType, 'PMP_IDX', 'PRFRM_COEFF', 'DC_NMB']].dropna()
        eq.to_csv('./pump_%s_equation.csv' % (PumpType), sep='|', index=False)

            # 일부 열 이름을 변경. 'WTR_TEMP'를 'WTR_TE'로, 'PMP_IDX'를 'PUMP_IDX'로 변경
        eq.rename(columns={'WTR_TEMP': 'WTR_TE', 'PMP_IDX': 'PUMP_IDX'}, inplace=True)

        return eq

    def __coef_to_str(self, x):
        if x == x:
            return ','.join([str(i) for i in x.coef])
        else:
            return self.np.nan

    def write_eqTable(self, QH, QP, date='2023-01-01', PumpType='NonInv'):
        return self.__write_eqTable(QH, QP, PumpType=PumpType, date=date)