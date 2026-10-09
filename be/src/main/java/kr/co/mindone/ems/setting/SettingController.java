package kr.co.mindone.ems.setting;
/**
 * packageName    : kr.co.mindone.ems.setting
 * fileName       : SettingController
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */
import io.swagger.v3.oas.annotations.Operation;
import kr.co.mindone.ems.config.base.BaseController;
import kr.co.mindone.ems.config.response.ResponseMessage;
import kr.co.mindone.ems.config.response.ResponseObject;
import org.apache.ibatis.annotations.Param;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.text.DecimalFormat;
import java.util.*;

@RequestMapping("st")
@RestController
public class SettingController extends BaseController {

    @Autowired
    private SettingService settingService;

    /**
     * 월간 사용 전력량 조회
     * @param map 년도 등의 조건을 포함한 요청 파라미터
     * @return 월간 사용 전력량 데이터
     */
    @Operation(summary = "월간 사용 전력량", description = "getUsageData?year=2023")
    @GetMapping("/getUsageData")
    public ResponseObject<List<HashMap<String, Object>>> getUsageData(@RequestParam HashMap<String, Object> map){
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, settingService.getUsageData(map));
    }
    /**
     * 월간 목표 사용 전력량 조회
     * @param map 년도 등의 조건을 포함한 요청 파라미터
     * @return 월간 목표 사용 전력량 데이터
     */
    @Operation(summary = "월간 목표 사용 전력량", description = "getGoalData?year=2023")
    @GetMapping("/getGoalData")
    public ResponseObject<List<HashMap<String, Object>>> getGoalData(@RequestParam HashMap<String, Object> map){
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, settingService.getGoalData(map));
    }
    /**
     * 시설 목록 조회
     * @param map 시설명을 포함한 선택적 요청 파라미터
     * @return 시설 목록 데이터
     */
    @Operation(summary = "시설 목록", description = "selectZone?zone_name=약품동 (옵션, 없으면 전체를 반환)")
    @GetMapping("/selectZone")
    public ResponseObject<List<HashMap<String, Object>>> selectZone(@RequestParam HashMap<String, Object> map){
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, settingService.selectZone(map));
    }
    /**
     * 태그 목록 조회
     * @param map 구역 코드와 시설명 등의 조건을 포함한 요청 파라미터
     * @return 태그 목록 데이터
     */
    @Operation(summary = "태그 목록", description = "selectTagList?zone_code=zone&fac_name=fac&tagname=tagname")
    @GetMapping("/selectTagList")
    public ResponseObject<List<HashMap<String, Object>>> selectTagList(@RequestParam HashMap<String, Object> map){
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, settingService.selectTagList(map));
    }
    /**
     * 사용 전기 요금제 정보 조회
     * @param params 요금제 정보 조건을 포함한 요청 파라미터
     * @return 요금제 정보 데이터
     */
    @Operation(summary = "사용 전기요금제 정보", description = "selectRtInfo")
    @GetMapping("/selectRtInfo")
    public ResponseObject<List<HashMap<String, Object>>> selectRtInfo(@RequestParam HashMap<String , Object> params) throws Exception {
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, settingService.selectRtInfo(params));
    }
    /**
     * 계절별 요금 정보 조회
     * @param params 계절 정보 등을 포함한 요청 파라미터
     * @return 계절별 요금 정보 데이터
     */
    @Operation(summary = "계절별 요금정보", description = "selectRT_RATE_INF?rate_idx=[1~4]&ssn=[봄철,여름철,가을철,겨울철]")
    @GetMapping("/selectRT_RATE_INF")
    public ResponseObject<List<HashMap<String, Object>>> selectRT_RATE_INF(@RequestParam HashMap<String , Object> params) throws Exception {
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, settingService.selectRT_RATE_INF(params));
    }
    /**
     * 순시 전력 정보 조회
     * @param params 요청 파라미터
     * @return 순시 전력 정보 데이터
     */
    @GetMapping("/selectSuji")
    public ResponseObject<List<HashMap<String, Object>>> selectSuji(@RequestParam HashMap<String , Object> params) throws Exception {
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, settingService.selectSuji(params));
    }
    /**
     * 펌프 정보 조회
     * @return 펌프 정보 데이터
     */
    @GetMapping(value="/selectCTR_PRF_PUMPMST_INF")
    public ResponseObject<List<HashMap<String, Object>>> selectCTR_PRF_PUMPMST_INF(Model model) throws Exception {
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, settingService.selectCTR_PRF_PUMPMST_INF());
    }

    /**
     * 태그 정보 갱신
     * @param maps 갱신할 태그 정보 리스트
     * @return 갱신된 태그 정보의 수
     */
    @Operation(summary = "태그정보 갱신", description = "updateTagInfo?json_RequestBody")
    @PostMapping("/updateTagInfo")
    public ResponseObject<Integer>  updateTagInfo(@RequestBody List<HashMap<String, Object>> maps) {
        for(HashMap<String, Object> map:maps){
            settingService.updateTagInfo(map);
            settingService.updateFac(map);
        }
        return makeSuccessObj(ResponseMessage.SAVE_SUCCESS, maps.size());
    }
    /**
     * 전기 요금 정보 갱신
     * @param params 요금 정보
     * @return 성공 메시지
     */
    @Operation(summary = "태그정보 갱신", description = "updateRT_RATE_INF?ssn=&stn_tm=&timezone=")
    @PostMapping(value="/updateRT_RATE_INF")
    public ResponseObject<String> updateRT_RATE_INF(@RequestBody HashMap<String , Object> params) throws Exception {
        ArrayList<HashMap<String, Object>>times = (ArrayList<HashMap<String, Object>>) params.get("time");
        //System.out.println("params:"+times.size());
        Set<String> keySet = params.keySet();
        for (String key : keySet) {
            System.out.println(key + " : " + params.get(key));
        }
        HashMap time = new HashMap();
        for(int i = 0 ; i < 24; i++) {
//            time.put("season", params.get("ssn"));
//            time.put("stn_tm", times.get(i).get("stn_tm"));
//            time.put("timezone", times.get(i).get("timezone"));
            time.put("season", params.get("season"));
            time.put("stn_tm", times.get(i).get("stn_tm"));
            time.put("timezone", times.get(i).get("timezone"));
            settingService.updateRT_RATE_INF(params,time);
            //System.out.println("time:"+time);
        }

        return makeSuccessObj(ResponseMessage.SAVE_SUCCESS, "ok");
    }
    /**
     * 월간 절약 목표 사용량 조회
     * @return 절약 목표 설정 데이터
     */
    @Operation(summary = "월간 절약 목표 사용량", description = "selectGetSetting")
    @GetMapping(value="/selectGetSetting")
    public ResponseObject<List<HashMap<String, Object>>>  selectGetSetting() throws Exception {
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, settingService.selectGetSetting());
    }
    /**
     * 월간 목표 사용량 갱신
     * @param params 월별 목표 사용량 데이터
     * @return 성공 메시지
     */
    @Operation(summary = "월간 목표 사용량 갱신", description = "updateGoal?month[1-12]=value")
    @PostMapping(value="/updateGoal")
    public ResponseObject<String> updateGoal(Model model, @RequestBody HashMap<String , Object> params) throws Exception {
        System.out.println(params);
        settingService.updateGoal(params);
        return makeSuccessObj(ResponseMessage.SAVE_SUCCESS, "ok");
    }
    /**
     * 펌프 운영정보 등록 및 갱신
     * @param maps 펌프 전략 정보 리스트
     * @return 성공 메시지
     */
    @Operation(summary = "펌프 운영정보 등록 및 갱신", description = "mergePTR_STRTG_INF?no=&value=&ssn_id=&ssn=")
    @PostMapping("/mergePTR_STRTG_INF")
    public ResponseObject<String> mergePTR_STRTG_INF(@RequestBody List<HashMap<String , String>> maps) throws Exception {
        settingService.mergePTR_STRTG_INF(maps);
        return makeSuccessObj(ResponseMessage.SAVE_SUCCESS, "ok");
    }

    /**
     * 펌프 계절, 시간대 사용여부 갱신
     * @param params 운영 정보 파라미터
     * @return 성공 메시지
     */
    @Operation(summary = "펌프 계절,시간대 사용여부 저장 및 갱신", description = "mergeOPER_INF?oper_idx=&ssn=&c0~c23=")
    @PostMapping("/mergeOPER_INF")
    public ResponseObject<String>  mergeOPER_INF(@RequestBody HashMap<String , Object> params) throws Exception {
        settingService.mergeOPER_INF(params);
        return makeSuccessObj(ResponseMessage.SAVE_SUCCESS, "ok");
    }
    /**
     * 펌프 우선순위 정보 저장 및 갱신
     * @param list 펌프 정보 리스트
     * @return 성공 메시지
     */

    @Operation(summary = "펌프 우선순위 저장 및 갱신", description = "updateSetCTR_PRF_PUMPMST_INF?PUMP_IDX=&flag=&PRRT_RNK=&USE_YN=")
    @PostMapping(value="/updateSetCTR_PRF_PUMPMST_INF")
    public ResponseObject<String> updateCTR_PRF_PMPMST_INF(@RequestBody List<HashMap<String, Object>> list) throws Exception {
        settingService.updateSetCTR_PRF_PUMPMST_INF(list);
        return makeSuccessObj(ResponseMessage.SAVE_SUCCESS, "ok");
    }

    /**
     * 리포트 데이터 조회
     * @param params 조회 필터 조건
     * @param type 리포트 타입
     * @return 리포트 데이터
     */
    @GetMapping(value="/selectReport")
    public ResponseObject<List<HashMap<String, Object>>> selectReport(@RequestParam HashMap<String, Object> params, @RequestParam String type) throws Exception {
        List<HashMap<String, Object>> returnObject = new ArrayList<HashMap<String, Object>>();
        DecimalFormat df = new DecimalFormat("0.00");
        switch (type) {
            case "1":

                List<HashMap<String, Object>> tempReturnObjectList = new ArrayList<HashMap<String, Object>>();

                tempReturnObjectList.add(settingService.selectReportPwr(params,"dayAgo"));
                tempReturnObjectList.add(settingService.selectReportPwr(params,"day"));
                tempReturnObjectList.add(settingService.selectReportPwr(params,"month"));
                tempReturnObjectList.add(settingService.selectReportPwr(params,"year"));

                returnObject = tempReturnObjectList;

                break;
            case "2":

                returnObject = settingService.selectReportZonePwr(params);

                break;
            case "3":
                //returnObject = settingService.selectReport3(params);

                returnObject = settingService.selectReportPump(params);

                break;
            case "4":
                returnObject = settingService.selectReport4(params);
                break;
            case "5":
                returnObject = settingService.selectReport5(params);
                break;
            case "6":
                returnObject = settingService.selectReport6(params);
                break;
            case "7":
                returnObject = settingService.selectReport7(params);
                break;
            default:
                returnObject = null;
                break;
        }
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, returnObject);
     }
    /**
     * 목표 피크 설정
     * @param params 피크 목표 설정 값
     * @return 성공 메시지
     */
    @Operation(summary = "목표 피크 설정", description = "insertPeakGoal?peakValue=2500")
    @PostMapping("/insertPeakGoal")
	public ResponseObject<String> insertPeakGoal(@RequestParam Map<String , Object> params) throws Exception {
		//System.out.println("insertPeakGoal params:"+params.get("peakValue"));
		settingService.insertPeakGoal(params);
		return makeSuccessObj(ResponseMessage.INSERT_SUCCESS, "ok");
	}
    /**
     * 목표 피크 확인
     * @return 설정된 피크 목표 값
     */
    @Operation(summary = "목표 피크 확인", description = "selectPeakGoal")
    @GetMapping("/selectPeakGoal")
	public ResponseObject<List<HashMap<String, Object>>> selectPeakGoal() throws Exception {
		return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, settingService.selectPeakGoal());
	}
    /**
     * 월별 계절 설정 확인
     * @return 월별 계절 설정 정보
     */
    @Operation(summary = "월별 계절설정 확인", description = "selectMonthSeason")
    @GetMapping("/selectMonthSeason")
    public ResponseObject<List<HashMap<String, Object>>> selectMonthSeason(){
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, settingService.selectMonthSeason());
    }
    /**
     * 월별 계절 설정 업데이트
     * @param updateList 업데이트할 정보
     * @return 성공 메시지
     */
    @Operation(summary = "월별 계절설정 업데이트", description = "setMonthSeason")
    @PostMapping("/setMonthSeason")
    public ResponseObject<String> setMonthSeason(@RequestBody List<HashMap<String, Object>> updateList){
        settingService.setMonthSeason(updateList);
        return makeSuccessObj(ResponseMessage.INSERT_SUCCESS, "월별 계절설정 업데이트");
    }
    /**
     * 선택 계절 부하 요금제 및 시간대 부하 출력
     * @param ssn 계절 정보 (예: 겨울철)
     * @return 계절에 따른 부하 요금제 및 시간대 부하 정보
     */
    @Operation(summary = "선택 계절 부하 요금제 및 시간대 부하 출력", description = "selectRateSeason?ssn=겨울철")
    @GetMapping("/selectRateSeason")
    public ResponseObject<HashMap<String, Object>> selectRateSeason(@RequestParam String ssn){
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, settingService.selectRateSeason(ssn));
    }
    /**
     * 계절 시간대 부하 업데이트
     * @param updateList 업데이트할 시간대 부하 정보 리스트
     * @return 업데이트 성공 메시지
     */
    @Operation(summary = "계절 시간대 부하 업데이트", description = "setSeasonLoad")
    @PostMapping("/setSeasonLoad")
    public ResponseObject<String> setSeasonLoad(@RequestBody List<HashMap<String, Object>> updateList){
        settingService.setSeasonLoad(updateList);
        return makeSuccessObj(ResponseMessage.INSERT_SUCCESS, "계절 시간대 부하 업데이트");
    }
    /**
     * 전력요금제 업데이트
     * @param updateMap 업데이트할 요금제 정보
     * @return 업데이트 성공 메시지
     */
    @Operation(summary = "전력요금제 업데이트", description = "setRateCost")
    @PostMapping("/setRateCost")
    public ResponseObject<String> setRateCost(@RequestBody HashMap<String, Object> updateMap){
        settingService.setRateCost(updateMap);
        return makeSuccessObj(ResponseMessage.INSERT_SUCCESS, "전력 요금제 업데이트");
    }



}
