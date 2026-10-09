from wntr.epanet.util import FlowUnits, to_si, HydParam, QualParam, MassUnits
import pandas as pd

from .Tibero import Tibero

class MeasureWqualChlorineData:
    def __init__(self):
        self.conn = Tibero().conn
        self.cursor = self.conn.cursor()
        self.wn = None

        self.reservoirList = [] # 선택된 최초염소 배수지 목록
        self.initialQualityList = [] # 선택된 배수지의 초기 염소값
        self.bulk_coeff = None # options > Reactions > Global Buld Coeff.
        self.wall_coeff = None # options > Reactions > Global Wall Coeff.
        self.tankJunctionList = []  # 선택된 추가염소 탱크, 절점 목록
        self.sourceQualityList = []  # 선택된 탱크, 절점의 추가 염소값

    def getMeasureWqualChlorineData(self, wn, titleData, wqualChlorineInputData):
        try:
            self.wn = wn
            self.reservoirList = wqualChlorineInputData.reservoirList
            self.initialQualityList = wqualChlorineInputData.initialQualityList
            self.bulk_coeff = wqualChlorineInputData.globalBulkCoeff
            self.wall_coeff = wqualChlorineInputData.globalWallCoeff
            self.tankJunctionList = wqualChlorineInputData.tankJunctionList
            self.sourceQualityList = wqualChlorineInputData.sourceQualityList

            # 01.데이터 셋팅
            self.setWnMeasureData()

            self.conn.close()
        except Exception as ex:
            print(ex)
            self.conn.close()
            raise

    # 01.데이터 셋팅
    def setWnMeasureData(self):
        # flow unit
        toDict = self.wn.to_dict()
        op = toDict.get('options')
        hd = op.get('hydraulic')
        flow_units = FlowUnits[hd.get('inpfile_units').upper()]

        # mass_units
        mass_units = MassUnits.mg
        if 'mg' in self.wn.options.quality.inpfile_units:
            mass_units = MassUnits.mg
        elif 'ug' in self.wn.options.quality.inpfile_units:
            mass_units = MassUnits.ug
        else:
            raise ValueError('Invalid chemical units in OPTIONS section')

        # options - quality
        self.wn.options.quality.parameter = 'CHLORINE'

        # 기존 등록된 reservoir initial quality 초기화
        for reservoirId in self.wn.reservoir_name_list:
            reObj = self.wn.get_node(reservoirId)
            reObj.initial_quality = 0.0

        # reservoir - initQuality
        chloDict = {
            "reservoirId": self.reservoirList,
            "initialQuality": self.initialQualityList
        }
        df = pd.DataFrame(chloDict)
        for dfDict in df.itertuples():
            if self.wn.options.quality.parameter == 'CHEMICAL':
                quality = to_si(flow_units, float(dfDict.initialQuality), QualParam.Concentration, mass_units=mass_units)
            elif self.wn.options.quality.parameter == 'AGE':
                quality = to_si(flow_units, float(dfDict.initialQuality), QualParam.WaterAge)
            else:
                quality = float(dfDict.initialQuality)

            reObj = self.wn.get_node(dfDict.reservoirId)
            reObj.initial_quality = float(quality)

        # options > reactions > bulk coeff, wall coeff
        self.wn.options.reaction.bulk_coeff = to_si(flow_units, float(self.bulk_coeff), QualParam.BulkReactionCoeff,
                                               mass_units=mass_units, reaction_order=self.wn.options.reaction.bulk_order)
        self.wn.options.reaction.wall_coeff = to_si(flow_units, float(self.wall_coeff), QualParam.WallReactionCoeff,
                                               mass_units=mass_units, reaction_order=self.wn.options.reaction.wall_order)

        # 기존 등록된 source quality 초기화
        for sourceId in self.wn.source_name_list:
            self.wn.remove_source(sourceId)

        # tank, junction - sourceQuality
        chloAddDict = {
            "tankJunctionId": self.tankJunctionList,
            "sourceQuality": self.sourceQualityList
        }
        df = pd.DataFrame(chloAddDict)
        source_num = 0
        for dfDict in df.itertuples():
            source_num = source_num + 1
            strength = to_si(flow_units, float(dfDict.sourceQuality), QualParam.Concentration, mass_units)
            self.wn.add_source('INP' + str(source_num), dfDict.tankJunctionId, 'SETPOINT', strength, None)
