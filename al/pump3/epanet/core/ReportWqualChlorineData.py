from .Tibero import Tibero
from wntr.epanet.util import FlowUnits, from_si, QualParam, MassUnits

class ReportWqualChlorineData:

    def __init__(self):
        self.conn = Tibero().conn
        self.cursor = self.conn.cursor()

    def saveReportWqualChlorineData(self, wn, results, titleData, wqualChlorineInputData):
        self.wn = wn
        self.results = results
        self.titleData = titleData
        self.wqualChlorineInputData = wqualChlorineInputData

        try:
            # 01.온라인 관망해석(수질모델-잔류염소) 파이프 별 잔류염소 평균,최소,최대 저장
            self.insertReportWqualChlorinePipe()

            self.conn.commit()
            self.conn.close()
        except Exception as ex:
            print(ex)
            self.conn.rollback()
            self.conn.close()
            raise


    # 01.온라인 관망해석(수질모델-잔류염소) 파이프 별 잔류염소 평균,최소,최대 저장
    def insertReportWqualChlorinePipe(self):
        wn = self.wn
        results = self.results
        result_quality = results.link['quality']
        # result_flowrate = results.link['flowrate']
        # result_velocity = results.link['velocity']
        # result_headloss = results.link['headloss']
        # result_status = results.link['status']
        # result_setting = results.link['setting']
        # result_friction_factor = results.link['friction_factor']
        # result_reaction_rate = results.link['reaction_rate']

        # flow unit
        toDict = wn.to_dict()
        op = toDict.get('options')
        hd = op.get('hydraulic')
        flow_unit = FlowUnits[hd.get('inpfile_units').upper()]

        # mass_units
        mass_units = MassUnits.mg
        if 'mg' in self.wn.options.quality.inpfile_units:
            mass_units = MassUnits.mg
        elif 'ug' in self.wn.options.quality.inpfile_units:
            mass_units = MassUnits.ug
        else:
            raise ValueError('Invalid chemical units in OPTIONS section')

        linkList = wn.link_name_list
        for linkId in linkList:
            liObj = wn.get_link(linkId)

            if liObj.link_type == 'Pipe':
                chlorineMax = 0.0
                chlorineMin = 0.0
                chlorineList = []
                for time in results.link['velocity'].T.dtypes.axes[0]:
                    # chlorine
                    chlorine = from_si(flow_unit, result_quality.loc[time, linkId], QualParam.Concentration, mass_units)
                    chlorineList.append(chlorine)

                    # if linkId == '1984001014':
                    #     print(linkId, ':', time / 3600, '==>', result_quality.loc[time, linkId], ':', chlorine)

                    if chlorine > chlorineMax:
                        chlorineMax = chlorine
                    if chlorine < chlorineMin:
                        chlorineMin = chlorine

                # 링크별 chlorineList 평균
                chlorineAvg = round(sum(chlorineList) / len(chlorineList), 3)
                chlorineMax = round(chlorineMax, 3)
                chlorineMin = round(chlorineMin, 3)
                # print(linkId, ': ', chlorineAvg, chlorineMin, chlorineMax)

                # 관로별 잔류염소 평균, 최소, 최대값 조회
                try:
                    query = ("MERGE "
                             " INTO TD_DC01002 A "
                             "USING dual "
                             " ON (A.RPT_NUMBER = ? AND A.PIPE_ID = ?) "
                             "WHEN MATCHED THEN "
                             "	UPDATE SET "
                             "        A.QUALITY_AVG = ? "
                             "      , A.QUALITY_MIN = ? "
                             "      , A.QUALITY_MAX = ? "
                             "WHEN NOT MATCHED THEN "
                             "	INSERT (A.RPT_NUMBER, A.PIPE_ID, A.QUALITY_AVG, A.QUALITY_MIN, A.QUALITY_MAX) "
                             "	VALUES (?, ?, ?, ?, ?); ")
                    self.cursor.execute(query, self.wqualChlorineInputData.rptNumber, linkId
                                        , str(chlorineAvg), str(chlorineMin), str(chlorineMax)
                                        , self.wqualChlorineInputData.rptNumber, linkId
                                        , str(chlorineAvg), str(chlorineMin), str(chlorineMax))
                except Exception as ex:
                    print(ex)
                    raise

