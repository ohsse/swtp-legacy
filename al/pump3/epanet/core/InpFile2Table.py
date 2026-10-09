from .Tibero import Tibero
from wntr.epanet.util import FlowUnits, from_si, HydParam

class Inpfile2Table:

    def __init__(self):
        self.conn = Tibero().conn
        self.cursor = self.conn.cursor()

    def saveInpFileData(self, wn, titleData):
        self.wn = wn
        self.titleData = titleData

        try:
            # 01. InpData 데이터 삭제
            self.deleteInpData()

            # 01. InpFile Nodes 등록
            self.insertInpFileNodes()

            # 02.InpFile Links 등록
            self.insertInpFileLinks()

            self.conn.commit()
            self.conn.close()
        except Exception as ex:
            print(ex)
            self.conn.rollback()
            self.conn.close()
            raise

    # 01. InpData 데이터 삭제
    def deleteInpData(self):
        try:
            # JUNCTIONS
            query = ("DELETE FROM WH_JUNCTIONS WHERE INP_NUMBER = ?;")
            self.cursor.execute(query, self.titleData.inpNumber)

            # RESERVOIRS
            query = ("DELETE FROM WH_RESERVOIRS WHERE INP_NUMBER = ?;")
            self.cursor.execute(query, self.titleData.inpNumber)

            # TANKS
            query = ("DELETE FROM WH_TANKS WHERE INP_NUMBER = ?;")
            self.cursor.execute(query, self.titleData.inpNumber)

            # PIPES
            query = ("DELETE FROM WH_PIPES WHERE INP_NUMBER = ?;")
            self.cursor.execute(query, self.titleData.inpNumber)

            # PUMPS
            query = ("DELETE FROM WH_PUMPS WHERE INP_NUMBER = ?;")
            self.cursor.execute(query, self.titleData.inpNumber)

            # VALVES
            query = ("DELETE FROM WH_VALVES WHERE INP_NUMBER = ?;")
            self.cursor.execute(query, self.titleData.inpNumber)

            # COORDINATES
            query = ("DELETE FROM WH_COORDINATES WHERE INP_NUMBER = ?;")
            self.cursor.execute(query, self.titleData.inpNumber)

        except Exception as ex:
            print(ex)
            raise

    # 01. InpFile Nodes 등록
    def insertInpFileNodes(self):
        wn = self.wn

        # flow unit
        toDict = wn.to_dict()
        op = toDict.get('options')
        hd = op.get('hydraulic')
        flow_unit = FlowUnits[hd.get('inpfile_units').upper()]

        nodeList = wn.node_name_list
        for nodeId in nodeList:
            noObj = wn.get_node(nodeId)

            if noObj.node_type == 'Junction':
                elevation = noObj.elevation
                base_demand = 0.0
                pattern_id = ''
                x = 0.0
                y = 0.0

                demands = noObj.demand_timeseries_list
                if len(demands) > 0:
                    # basedemand
                    base_demand = from_si(flow_unit, demands[0].base_value, HydParam.Demand)
                    # pattern_id
                    pattern_id = demands[0].pattern_name

                try:
                    query = ("INSERT INTO WH_JUNCTIONS ( "
                             "      INP_NUMBER, ID, ELEVATION "
                             "    , BASE_DEMAND, PATTERN_ID "
                             ") VALUES ( "
                             "      ?, ?, ?"
                             "    , ?, ? "
                             ");")
                    self.cursor.execute(query, self.titleData.inpNumber, nodeId, str(elevation),
                                        str(base_demand), pattern_id)
                except Exception as ex:
                    print(ex)
                    raise
            elif noObj.node_type == 'Reservoir':
                head = noObj.base_head
                pattern_id = noObj.head_timeseries.pattern_name

                try:
                    query = ("INSERT INTO WH_RESERVOIRS ( "
                             "      INP_NUMBER, ID, HEAD, PATTERN_ID "
                             ") VALUES ( "
                             "      ?, ?, ?, ? "
                             ");")
                    self.cursor.execute(query, self.titleData.inpNumber, nodeId, str(head), pattern_id)
                except Exception as ex:
                    print(ex)
                    raise
            elif noObj.node_type == 'Tank':
                elevation = noObj.elevation
                initlvl = noObj.init_level
                minlvl = noObj.min_level
                maxlvl = noObj.max_level
                diam = noObj.diameter
                minvol = noObj.min_vol

                try:
                    query = ("INSERT INTO WH_TANKS ( "
                             "      INP_NUMBER, ID, ELEVATION "
                             "    , INITLVL, MINLVL, MAXLVL "
                             "    , DIAM, MINVOL "
                             ") VALUES ( "
                             "      ?, ?, ? "
                             "    , ?, ?, ? "
                             "    , ?, ? "
                             ");")
                    self.cursor.execute(query, self.titleData.inpNumber, nodeId, str(elevation)
                                        , str(initlvl), str(minlvl), str(maxlvl)
                                        , str(diam), str(minvol))
                except Exception as ex:
                    print(ex)
                    raise
            else:
                print('::new_node_type: ' + noObj.node_type)

            # coordinates
            if len(noObj.coordinates) == 2:
                x = noObj.coordinates[0]
                y = noObj.coordinates[1]

                try:
                    query = ("INSERT INTO WH_COORDINATES ( "
                             "      INP_NUMBER, ID, X, Y "
                             ") VALUES ( "
                             "      ?, ?, ?, ? "
                             ");")
                    self.cursor.execute(query, self.titleData.inpNumber, nodeId, str(x), str(y))

                except Exception as ex:
                    print(ex)
                    raise

    # 02.InpFile Links 등록
    def insertInpFileLinks(self):
        wn = self.wn

        # flow unit
        toDict = wn.to_dict()
        op = toDict.get('options')
        hd = op.get('hydraulic')
        flow_unit = FlowUnits[hd.get('inpfile_units').upper()]

        linkList = wn.link_name_list
        for linkId in linkList:
            liObj = wn.get_link(linkId)

            diameter = 0.0
            length = 0.0
            roughness = 0.0

            if liObj.link_type == 'Pipe':
                node1 = liObj.start_node_name
                node2 = liObj.end_node_name
                length = liObj.length
                diam = liObj. diameter
                roughness = liObj.roughness
                mloss = liObj.minor_loss
                status = liObj.status

                try:
                    query = ("INSERT INTO WH_PIPES ( "
                             "      INP_NUMBER, ID, NODE1 "
                             "    , NODE2, LENGTH, DIAM "
                             "    , ROUGHNESS, MLOSS, STATUS "
                             ") VALUES ( "
                             "      ?, ?, ? "
                             "    , ?, ?, ? "
                             "    , ?, ?, ? "
                             ");")
                    self.cursor.execute(query, self.titleData.inpNumber, linkId, node1
                                        , node2, str(length), str(diam)
                                        , str(roughness), str(mloss), status)

                except Exception as ex:
                    print(ex)
                    raise

            elif liObj.link_type == 'Pump':
                node1 = liObj.start_node_name
                node2 = liObj.end_node_name

                try:
                    query = ("INSERT INTO WH_PUMPS ( "
                             "      INP_NUMBER, ID, NODE1, NODE2 "
                             ") VALUES ( "
                             "      ?, ?, ?, ? "
                             ");")
                    self.cursor.execute(query, self.titleData.inpNumber, linkId, node1, node2)

                except Exception as ex:
                    print(ex)
                    raise

            elif liObj.link_type == 'Valve':
                node1 = liObj.start_node_name
                node2 = liObj.end_node_name
                diameter = from_si(flow_unit, liObj.diameter, HydParam.PipeDiameter)
                type = liObj.valve_type
                setting = liObj.setting
                minorloss = liObj.minor_loss

                try:
                    query = ("INSERT INTO WH_VALVES ( "
                             "      INP_NUMBER, ID, NODE1 "
                             "    , NODE2, DIAMETER, TYPE "
                             "    , SETTING, MINORLOSS "
                             ") VALUES ( "
                             "      ?, ?, ? "
                             "    , ?, ?, ? "
                             "    , ?, ? "
                             ");")
                    self.cursor.execute(query, self.titleData.inpNumber, linkId, node1
                                        , node2, str(diameter), type, str(setting), str(minorloss))

                except Exception as ex:
                    print(ex)
                    raise
            else:
                print('::new_link_type: ' + liObj.link_type)
