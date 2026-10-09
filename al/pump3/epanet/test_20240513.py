from datetime import datetime
import wntr
import pandas as pd
from wntr.epanet.util import FlowUnits, to_si, HydParam, from_si
import argparse
import copy
from db_manager.db_manager import DbManager


def test():
    dbmanager = DbManager()
    parser = argparse.ArgumentParser()    
    parser.add_argument('--startDt', default='2024-05-09 10:00:00')
    parser.add_argument('--endDt', default='2024-05-09 10:00:00')
    parser.add_argument('--pre', default=False) # True or False (예측값일땐 True)
    args = parser.parse_args()
    
    cur = dbmanager.connection()

    wn = wntr.network.WaterNetworkModel("/home/app/pump3/epanet/file/Gosan_SC1_22_08_01_23Hour.inp")
    toDict = wn.to_dict()
    op = toDict.get('options')
    hd = op.get('hydraulic')
    flow_unit = FlowUnits[hd.get('inpfile_units').upper()]
    isPreTs = ''
    isPreVal = ''
    sql = ''
    sql2=''
    if(str(args.pre) == 'False'):
        # dm(유량값)에 해당하는 데이터를 가져옴
        sql =   """
                select * from TB_RAWDATA tr
                join TB_NODE_TAG tnv on  tnv.FR_TAGNAME = tr.tagname 
                where ts >= %s and ts <= %s;
                """
        isPreTs = 'TS'
        isPreVal = 'VALUE'
    else:
        sql =   """
                select * from TB_CTR_TNK_RST ctr
                join TB_NODE_TAG tnt on ctr.DSTRB_ID = tnt.DSTRB_Q_ID 
                where tnt.DSTRB_Q_ID like 'Q%%'
                and ctr.RGSTR_TIME >= %s and ctr.RGSTR_TIME <= %s
                """
                
        sql2 =   """
                select tnt.*, tr.tagname as DSTRB_ID,tr.ts as RGSTR_TIME, tr.value as PRDCT_VALUE, tr.tagname from TB_RAWDATA tr
                join TB_NODE_TAG tnt on tr.tagname = tnt.DSTRB_Q_ID 
                where tnt.DSTRB_Q_ID like '7%%'
                and tr.ts >= %s and tr.ts <= %s
                """
        isPreTs = 'RGSTR_TIME' 
        isPreVal = 'PRDCT_VALUE'
    data = (args.startDt, args.endDt)
    res = dbmanager.sqlSelect(sql, data)
    if(str(args.pre)== 'True'):
        res.extend(dbmanager.sqlSelect(sql2, data))
        # print('res',pd.DataFrame(res))
    res1 = copy.deepcopy(res)

    # Demand Set
    # db에서 가져온 유량(demands)를 inp 파일에 입력
    # 각 시간에 해당하는 유량값을 가져오기 위한 전처리 : 중복되는 시간을 제거해 list로 저장
    res1 = list({item[isPreTs]: item for item in res1}.values())
    # 전처리된 res1의 ts와 res의 ts가 같은 값을 가져와서 list로 저장 
    for item in res1:
        # df 변환
        value = pd.DataFrame(res)
        value = value[value[isPreTs]==item[isPreTs]]
        cur_time = value[isPreTs].values[0]
        # print('curTime : ',cur_time)
        for junction_name in wn.junction_name_list:
            # junction_name와 value['NODE']가 동일한 value를 가져옴
            node = value[value['NODE_ID'] == junction_name] 
            noObj = wn.get_node(junction_name)
            demands = noObj.demand_timeseries_list 
            # node가 빈값이면 0으로, 값이 있으면 적절한 값으로 바꿔준다 (node id=199인 태그의 유량 값에 *6)
            if node.empty:
                demands[0].base_value = 0
            else:
                if junction_name =='이서배수지':
                    chun_ma = value[value['NODE_ID'] == '이서배수지'] 
                    demands[0].base_value = to_si(flow_unit, float(chun_ma.iloc[0][isPreVal]) * 0.8, HydParam.Demand)
                # elif junction_name =='봉동배수지':
                #     chun_ma = value[value['NODE_ID'] == '천마배수지'] 
                #     demands[0].base_value = to_si(flow_unit, float(chun_ma.iloc[0][isPreVal]) / 3, HydParam.Demand)
                # elif junction_name =='완주산단배수지':
                #     chun_ma = value[value['NODE_ID'] == '천마배수지'] 
                #     demands[0].base_value = to_si(flow_unit, float(chun_ma.iloc[0][isPreVal]) / 3 , HydParam.Demand)
                elif junction_name =='대야배수지':
                    chun_ma = value[value['NODE_ID'] == '328'] 
                    # print('328',chun_ma)
                    demands[0].base_value = to_si(flow_unit, float(chun_ma.iloc[0][isPreVal]) * 2, HydParam.Demand)
                elif junction_name =='199':
                    chun_ma = value[value['NODE_ID'] == '천마배수지'] 
                    demands[0].base_value = to_si(flow_unit, float(chun_ma.iloc[0][isPreVal]) * 0.8, HydParam.Demand)
                elif junction_name =='282':
                    chun_ma = value[value['NODE_ID'] == '천마배수지'] 
                    demands[0].base_value = to_si(flow_unit, float(chun_ma.iloc[0][isPreVal]) / 10, HydParam.Demand)
                else:
                    demands[0].base_value = to_si(flow_unit, float(node.iloc[0][isPreVal]), HydParam.Demand)
        sim = wntr.sim.EpanetSimulator(wn)
        results = sim.run_sim()
        # simulator를 통해 link의 headloss, node의 pressure를 가져옴
        lossArr = results.link['headloss']
        nodeArr = results.node['pressure']
        linkArr = results.link['flowrate']
        
        if (isPreTs=='TS'):
            print('cur_timmme', cur_time)
            # headloss값을 db에 insert
            sql = """
                    INSERT IGNORE INTO EMS_DB.TB_FR_VAL
                    (LINK_ID, HH_LOSS_VAL, RGSTR_TIME, LINK_VAL, FLW_ALG_RST_VAL)
                    VALUES(%s,%s,%s,(SELECT value from TB_RAWDATA tr 
                                    join TB_LINK_GRP tlg on tr.tagname = tlg.FLW_TAGNAME 
                                    where tr.ts = %s and tlg.LINK_ID =%s), %s);  
                """
            for loss in lossArr:
                pipes=wn.get_link(loss)
                if pipes.link_type == 'Pipe':
                    data = (loss, float(lossArr[loss].values[1]) * pipes.length , cur_time,cur_time, loss ,from_si(flow_unit,float(linkArr[loss].values[1]),HydParam.Demand))
                    cur.execute(sql, data)
                    
              # node id, 해당시간에 일치하는 기존 압력태그의 압력값, 계산된 압력값, 예측시간을 테이블에 저장 
            sql = """
                    INSERT IGNORE INTO EMS_DB.TB_FP_VAL
                    (NODE_ID, FP_VAL, FP_ALG_RST_VAL, RGSTR_TIME)
                    VALUES(%s,(select value from TB_RAWDATA tr 
                                join TB_NODE_TAG tnt on tnt.FP_TAGNAME = tr.tagname 
                                where 1=1
                                and tr.ts = %s
                                and tnt.NODE_ID = %s
                                ),%s,%s);  
                    """

            for node in nodeArr:
                data = (node,cur_time,node ,float(nodeArr[node].values[1]), cur_time)
                # print(sql % data)
                cur.execute(sql,data)                    
        elif(isPreTs=='RGSTR_TIME'):
            print('cur_timmme', cur_time)
            sql = """
                    INSERT IGNORE INTO EMS_DB.TB_FR_VAL
                    (LINK_ID, HH_LOSS_VAL, RGSTR_TIME, FLG, FLW_ALG_RST_VAL)
                    VALUES(%s,%s,%s,%s,%s);  
                """
            for loss in lossArr:
                pipes=wn.get_link(loss)
                if pipes.link_type == 'Pipe':
                    data = (loss, float(lossArr[loss].values[1]) * pipes.length,cur_time,'PRE',from_si(flow_unit,float(linkArr[loss].values[1]),HydParam.Demand))
                    cur.execute(sql, data)

            sql = """
                    INSERT IGNORE INTO EMS_DB.TB_FP_VAL
                    (NODE_ID, FP_ALG_RST_VAL, RGSTR_TIME, FLG)
                    VALUES(%s,%s,%s,%s);  
                    """
            for node in nodeArr:
                data = (node, float(nodeArr[node].values[1]), cur_time, 'PRE')
                cur.execute(sql,data)                    
            
        # link id 그룹별로 loss value를 합산
        sql = """
            select sum(tlv.HH_LOSS_VAL) as SUM, tlg.GRP_NM from TB_FR_VAL tlv 
            join TB_LINK_GRP tlg  on tlv.LINK_ID = tlg.LINK_ID 
            where tlv.RGSTR_TIME = %s
            GROUP BY tlg.GRP_NM 
            """
        data = (cur_time)
        res2 = dbmanager.sqlSelect(sql,data)

        # 현재 시간(value['ts'])에 맞는 최신데이터 하나를 가져옴
        sql = """
        if
            (select tga.STN_FLW_VAL from TB_AVL_GRP tga 
            where tga.STN_FLW_VAL > 
            (select (sum(value)/60) as SUM from TB_RAWDATA tr 
            where tagname in('701-367-FRI-4004','701-367-FRI-4001')
            and ts = %s) limit 1) THEN	
            select * from TB_AVL_GRP tga 
            where tga.STN_FLW_VAL > 
                (select (sum(value)/60) as SUM from TB_RAWDATA tr 
                where tagname in('701-367-FRI-4004','701-367-FRI-4001')
                and ts = %s) limit 1;
        ELSE 
            select * from TB_AVL_GRP tga order by tga.STN_FLW_VAL desc limit 1;
        END IF;

        """
        data = (cur_time,cur_time)
        res3 = dbmanager.sqlSelect(sql, data)

        # res2에서 grp 비교하기
        # value == 1인 값을 체크
        # 해당 값을 모두 sum 
        sum_val = 0
        for item in res2:
            if res3[0].get('GRP_'+ item['GRP_NM']+'_YN'):
                grp = res3[0]['GRP_'+item['GRP_NM']+'_YN']
                if grp == 1:
                    sum_val += item['SUM']
                    

        # 전체 유량값, 압력값(실제) 합산
        sql = """
            SELECT SUM(value) as FR_SUM from TB_RAWDATA 
            WHERE ts = %s and tagname in (%s, %s)
              """        
        data = (cur_time,'701-367-FRI-4004','701-367-FRI-4001')
        fr_res = dbmanager.sqlSelect(sql, data)
        
        data = (cur_time,'701-367-PRI-4019','701-367-PRI-4010')
        pr_res = dbmanager.sqlSelect(sql, data)

        if (isPreTs=='TS'):
            # 시간에 맞는 합산 결과(시간, 합산된 loss_val, 실제 유량값, 실제 압력값, 압력결과) TB_TOT_ALG에 저장
            sql = """
                INSERT IGNORE INTO EMS_DB.TB_TOT_ALG
                (RGSTR_TIME, HH_LOSS_VAL_TOT, FLW_VAL, FP_VAL, FP_ALG_RST_VAL)
                VALUES(%s,%s, %s,%s,%s);
                """
            data = (cur_time, sum_val,fr_res[0]['FR_SUM'],pr_res[0]['FR_SUM'],float(nodeArr['13'].values[1]))
            cur.execute(sql, data)
        elif(isPreTs=='RGSTR_TIME'):
            sql = """
                INSERT IGNORE INTO EMS_DB.TB_TOT_ALG
                (RGSTR_TIME, HH_LOSS_VAL_TOT, FP_ALG_RST_VAL, FLG)
                VALUES(%s,%s, %s,%s);
                """
            data = (cur_time, sum_val,float(nodeArr['13'].values[1]),'PRE')
            cur.execute(sql,data)
        # print('end')
        dbmanager.sqlCommit()
    
    # sql =   """
    #         select * from TB_FP_VAL where FP_VAL is not null order by RGSTR_TIME asc;
    #         """
    # node_val = dbmanager.sqlSelect(sql)

    # sql =   """
    #         select * from TB_FR_VAL order by RGSTR_TIME, LINK_ID asc;
    #         """
    # link_val = dbmanager.sqlSelect(sql)
    dbmanager.sqlClose()
    
    # node_df = pd.DataFrame(node_val)
    # loss_df = pd.DataFrame(link_val)
    # node_df['RGSTR_TIME'] = pd.to_datetime(node_df['RGSTR_TIME'])
    # loss_df['RGSTR_TIME']= loss_df['RGSTR_TIME'].apply(lambda _ : datetime.strptime(_,'%Y-%m-%d %H:%M:%S'))
    # node_df.to_csv('C:\\epanet\\node_val.csv', sep=',',na_rep='NaN')
    # loss_df.to_csv('C:\\epanet\\loss_val.csv', sep=',',na_rep='NaN')

    print('end')

    wntr.network.write_inpfile(wn, '/home/app/pump3/epanet/file/Gosan_SC1_22_08_01_23Hour.rpt', version=2.2)

test()