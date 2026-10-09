from wntr.epanet.util import FlowUnits, to_si, HydParam
from wntr.network.model import LinkStatus

from .Tibero import Tibero

class MeasureCaseSimulationData:
    def __init__(self):
        self.conn = Tibero().conn
        self.cursor = self.conn.cursor()

    def getMeasureData(self, wn, caseSimulationInputData):
        try:
            self.wn = wn
            self.caseSimulationInputData = caseSimulationInputData

            # 01.실시간 데이터 셋팅
            self.setWnMeasureData()

            self.conn.close()
        except Exception as ex:
            print(ex)
            self.conn.close()
            raise


    # 01.실시간 데이터 셋팅
    def setWnMeasureData(self):
        # Pump status Set
        linkList = self.wn.link_name_list
        for linkId in linkList:
            liObj = self.wn.get_link(linkId)

            if linkId in self.caseSimulationInputData.caseSimulationDict:
                linkVal = self.caseSimulationInputData.caseSimulationDict[linkId]

                # if linkVal == LinkStatus.Open:
                if linkVal == 'Y':
                    liObj._user_status = LinkStatus.Open
                    liObj.initial_status = LinkStatus.Open
                else:
                    liObj._user_status = LinkStatus.Closed
                    liObj.initial_status = LinkStatus.Closed
