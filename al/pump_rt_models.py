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
        self.KelvinT = 273.15


    def rho_water(self, T):
        rho = 9.998395639 * self.np.power(10, 2) + (6.798299989 / 100) * T
        rho = rho - 9.106025564 / self.np.power(10, 3) * self.np.power(T, 2)
        rho = rho + 1.005272999 / self.np.power(10, 4) * self.np.power(T, 3)
        rho = rho - 1.126713526 / self.np.power(10, 6) * self.np.power(T, 4)
        rho = rho + 6.591795606 / self.np.power(10, 9) * self.np.power(T, 5)
        return rho

    def group_tags(self, name, group):
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
        idx = idx[0] if isinstance(idx, list) else idx
        g = self.pumpAttr[idx]['PUMP_GRP']
        Qnm = self.pumpAttr[idx]['FRI_TAG']
        Hnm = 'tot_diff_head_G%d' % (g)
        Pnm = 'totPWI_G%d' % (g)
        Tnm = self.pumpAttr[idx]['TEI_TAG']
        Fnm = self.pumpAttr[idx]['SPI_TAG']
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

        q = tmp[mask][Qnm];
        h = tmp[mask][Hnm]
        p = tmp[mask][Pnm];
        t = tmp[mask][Tnm]

        p = p.replace(0, self.np.nan)

        data = self.pd.concat([q, h, p, t], axis=1)
        data = data.dropna()
        
        h = data[Hnm];
        p = data[Pnm];
        t = data[Tnm]
        return q.copy(), p.copy(), t.copy(), h.copy()

    def load_masked_qpthf(self, tmp, mask, idx):
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

        accept_tags = []
        for nm in pumpList:
            accept_tags.append(self.pumpAttr[nm]['PMB_TAG'])

        except_tags = set(self.group_tags('PMB_TAG', g)) - set(accept_tags)

        for idx, tag in enumerate(accept_tags):
            if idx == 0:
                mask = (tdf[tag] == 1)
            else:
                mask = mask & (tdf[tag] == 1)

        for idx, tag in enumerate(except_tags):
            mask = mask & (tdf[tag] == 0)

        return mask.copy()

    def __sampling(self, x, y):
        # #############################################################################
        # Generate sample data
        if len(y) < 1000:
            return self.np.array(list(zip(x, y)))
        else:
            X = self.np.array(list(zip(x, y)))
            scaler = self.StandardScaler()
            scaler.fit(X)
            X = scaler.transform(X)

            # #############################################################################
            # Compute DBSCAN
            X[np.isnan(X)]= X[~np.isnan(X)].mean() #TEMP!

            db = self.DBSCAN(eps=0.1, min_samples=10).fit(X)
            core_samples_mask = self.np.zeros_like(db.labels_, dtype=bool)
            core_samples_mask[db.core_sample_indices_] = True

            X = scaler.inverse_transform(X)
            return X[core_samples_mask]

    def __QH_fit_function(self, x, a, b, c, d):
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
        print(_Y)
        e = self.np.poly1d(self.np.polyfit(_X, _Y, 1))
        return e

    def Power_fitting_ftn_inv(self, x, y):
        X = self.__sampling(x, y)
        print(X[:, 0])
        print(X[:, 1])
        e = self.np.poly1d(self.np.polyfit(X[:, 0], X[:, 1], 2))
        return e

    def eta_fitting_ftn(self, x, y):
        X = self.__sampling(x, y)
        e = self.np.poly1d(self.np.polyfit(X[:, 0], X[:, 1], 2))
        return e

    def inv_fitting_ftn(self, x, y):
        from scipy.optimize import curve_fit
        def inv_2nd_head_ftn(x, a, b, c):
            return a * x * x + b * x + c

        X = self.__sampling(x, y)

        bounds = ((-self.np.inf, 0, 55), (0, 0.0001, 100))

        popt, pcov = curve_fit(inv_2nd_head_ftn, X[:, 0], X[:, 1], bounds=bounds)
        return self.np.poly1d(popt)

    def __fitting(self, pi, rq, y, ftype):
        if ftype == 'h':
            dh = self.pumpAttr[pi]['DUTY_H'] or 1
            dq = self.pumpAttr[pi]['DUTY_Q'] or 1
            print(rq)
            print(y[ftype])
            e = self.Head_fitting_ftn(rq, y[ftype], dq, dh)
            e = e if e.coef[0] < 0 else None
        elif ftype == 'p':
            e = self.Power_fitting_ftn(rq, y[ftype])
            print(rq, y[ftype])
            print('e!', e)
            e = e if e.coef[0] > 0 else None
        else:
            e = None

        return e

    def __fitting_inv(self, pi, rq, y, ftype):
        if ftype == 'h':
            e = self.inv_fitting_ftn(rq, y[ftype])
            #e = e if e.coef[0] < 0 else None
        elif ftype == 'p':
            e = self.Power_fitting_ftn_inv(rq, y[ftype])
            #e = e if e.coef[0] > 0 else None
        else:
            e = None

        return e
    
    def calc_diff_head(self, tmp):
        # 개별 펌프의 양정 계산
        for key, val_dic in self.pumpAttr.items():
            nm = 'diff_head-%d' % (key)
            PRId = val_dic['PRI_D_TAG']
            PRIs = val_dic['PRI_S_TAG']
            TEI  = val_dic['TEI_TAG']

            print(val_dic['PRI_T_TAG'])

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
            gtags = self.group_tags('PWI_TAG', g)
            pumpGroup = self.group_tags('PMB_TAG', g)
            t1 = tmp[pumpGroup].copy()
            t1.columns = gtags
            tmp[gNM] = (tmp[gtags] * t1).replace(0, self.np.NaN)[gtags].sum(axis=1) 

        return tmp

    def calc_equationTable_NonInv(self, tmp, ftype='h', pump_list=range(1, 5), st_date='2020-06-01'):
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
        freq_list = []
        for pi in pump_list:
            fTag = self.pumpAttr[pi]['SPI_TAG']
            ref_freq = tmp[fTag].round(1).value_counts().index[0]
            ref_freq = max(ref_freq, 0.1)

            freq_list.append(ref_freq)
        eqTable = self.pd.DataFrame(index=freq_list, columns=pump_list)

        for pi in pump_list:
            fTag = self.pumpAttr[pi]['SPI_TAG']
            ref_freq = tmp[fTag].round(1).value_counts().index[0]
            mask = (tmp[fTag] > ref_freq - 0.1) & (tmp[fTag] < ref_freq + 0.1) & (
                        tmp.index > self.pd.to_datetime(st_date))

            ref_freq = max(ref_freq, 0.1)
            #mask = mask & self.select_pump(tmp, [pi]) #TODO CHEck!
            q, p, t, h, f = self.load_masked_qpthf(tmp, mask, pi)
            ydic = {'p': p, 'h': h}
            print(q)
            if len(q) > 1e+3:
                e = self.__fitting_inv(pi, q, ydic, ftype=ftype)
                eqTable.loc[ref_freq][pi] = e

        return eqTable

    def __fill_equationTable(self, eqTable, pump_list, ftype):
        x = self.np.arange(0, 4000, 50)
        for pi in pump_list:
            TF = True
            for i, tdf in eqTable.iterrows():
                if type(tdf[pi]) == type(self.np.poly1d([1])):
                    reducedQ = x * (self.KelvinT + i) / 290.
                    reducedH = tdf[pi](x * (self.KelvinT + i) / 290.)
                    arr = self.np.array(list(zip(reducedQ, reducedH)))
                    if TF:
                        QH = arr
                        TF = False
                    else:
                        QH = self.np.r_[QH, arr]

            rq = QH[:, 0];
            ydic = {ftype: QH[:, 1]}
            eq = self.__fitting(pi, rq, ydic, ftype=ftype)
            for i, tdf in eqTable.iterrows():
                if not type(tdf[pi]) == type(self.np.poly1d([1])):
                    eqTable[pi][i] = eq

        return eqTable

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
        CondType = 'FREQ' if PumpType == 'Inv' else 'WTR_TEMP'

        eqs = {'QH': QH, 'QP': QP}
        for key, eqT in eqs.items():
            eqT[CondType] = eqT.index
            eqT = eqT.melt(id_vars=CondType, var_name='PMP_IDX', value_name='Eq')
            eqT['PRFRM_COEFF'] = eqT['Eq'].apply(lambda x: self.__coef_to_str(x))
            eqT['DC_NMB'] = 'Docker#1'
            eqT['ANLY_DATE'] = date
            eqT['EQ_TYP'] = key
            if key == 'QH':
                eq = eqT[['ANLY_DATE', 'EQ_TYP', CondType, 'PMP_IDX', 'PRFRM_COEFF', 'DC_NMB']]
            else:
                eq = self.pd.concat([eq, eqT])

        eq = eq[['ANLY_DATE', 'EQ_TYP', CondType, 'PMP_IDX', 'PRFRM_COEFF', 'DC_NMB']].dropna()
        eq.to_csv('./pump_%s_equation.csv' % (PumpType), sep='|', index=False)

        eq.rename(columns={'WTR_TEMP': 'WTR_TE', 'PMP_IDX': 'PUMP_IDX'}, inplace=True)

        return eq

    def __coef_to_str(self, x):
        if x == x:
            return ','.join([str(i) for i in x.coef])
        else:
            return self.np.nan

    def write_eqTable(self, QH, QP, date='2023-01-01', PumpType='NonInv'):
        return self.__write_eqTable(QH, QP, PumpType=PumpType, date=date)