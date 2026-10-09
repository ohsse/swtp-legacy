package kr.co.mindone.ems.epa;

import kr.co.mindone.ems.drvn.DrvnMapper;
import kr.co.mindone.ems.drvn.DrvnService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Set;

@Slf4j
@Service
public class EpaService {
	@Autowired
	private EpaMapper epaMapper;

	@Autowired
	private DrvnMapper drvnMapper;

	private final DrvnService drvnService;

	public EpaService(DrvnService drvnService) {
		this.drvnService = drvnService;
	}


	public Integer getEpaModeInfo() {
		return epaMapper.getEpaModeInfo();
	}

	public void setEpaMode(int mode) {
		epaMapper.setEpaMode(mode);
	}


	public double getEpaFlow(double gosanFlow, String ts, int pump_grp) {
		//개발용 수두손실 그룹(현재 고산 하나만 있음)
//		String setHeadLossCode = "A4";
//		double retrunFlow = 0;
		HashMap<String, Object> param = new HashMap<>();
		param.put("startDate", ts);
		param.put("first", true);
		param.put("opt_idx", "PRE");
		param.put("link_id", "10");


//		HashMap<Integer, HashMap<String, List<String>>> headLossGrpMap = drvnService.getHeadLossGrpMap();
//		Set<String> grp_nm = headLossGrpMap.get(pump_grp).keySet();
//		HashMap<Integer, HashMap<String, List<String>>> headLossFlowIdMap = drvnService.getHeadLossFlowIdMap();
//		for (String grp_str : grp_nm) {
//			List<String> headLossFlowId = headLossFlowIdMap.get(pump_grp).get(grp_str);
//			List<Double> headLossFlowFirst = new ArrayList<>();
//			if (!headLossFlowId.isEmpty()) {
//				param.put("dstrbList", headLossFlowId);
//				headLossFlowFirst = drvnMapper.selectHeadLossTargetCurFlow(param);
//			}
//
//			retrunFlow = headLossFlowFirst.isEmpty() ? 0 : headLossFlowFirst.get(0);
//			if(grp_str.equals(setHeadLossCode)){
//				break;
//			}
//		}
		return drvnMapper.selectGsAllLinkFirst(param);

	}

	public double getEpaPressure(double gosanPressure, String ts, int pump_grp) {
//		String setHeadLossCode = "A4";
//		double retrunPressure = 0;
//		param.put("startDate", ts);
//		param.put("first", true);
//
//		HashMap<Integer, HashMap<String, List<String>>> headLossGrpMap = drvnService.getHeadLossGrpMap();
//		Set<String> grp_nm = headLossGrpMap.get(pump_grp).keySet();
//		for (String grp_str : grp_nm) {
//			List<String> grpList = headLossGrpMap.get(pump_grp).get(grp_str);
//			param.put("grpList", grpList);
//			param.put("GRP_NM", grp_str);
//			Double selectHeadLossFirst = drvnMapper.selectHeadLoss(param);
//			if(selectHeadLossFirst != null){
//
//				retrunPressure = drvnService.getH(selectHeadLossFirst,pump_grp, grp_str);
//			}
//
//			if(grp_str.equals(setHeadLossCode)){
//				break;
//			}
//		}
//		return retrunPressure;

		HashMap<String, Object> param = new HashMap<>();
		param.put("startDate", ts);
		param.put("first", true);
		param.put("opt_idx", "PRE");
		param.put("node_id", "고산(정)유출");

		return drvnMapper.selectGsAllNodeFirst(param) / 10;
	}
}
