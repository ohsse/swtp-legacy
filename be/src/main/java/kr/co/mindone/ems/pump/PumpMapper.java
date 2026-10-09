package kr.co.mindone.ems.pump;
/**
 * packageName    : kr.co.mindone.ems.pump
 * fileName       : PumpMapper
 * date           : 24. 9. 8.
 * description    : 펌프와 관련된 데이터를 관리하고 조회하는 Mapper 인터페이스
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 8.        -            최초 생성
 */
import org.apache.ibatis.annotations.Mapper;
import org.springframework.context.annotation.Profile;
import org.springframework.context.annotation.PropertySource;

import java.util.HashMap;
import java.util.List;

@Mapper
interface PumpMapper {

    /**
     * 현재 작동 중인 모든 펌프 리스트 조회
     * @return 현재 작동 중인 펌프의 정보를 담은 리스트
     */
    List < HashMap < String, Object >> nowRunAllPumpList();

    /**
     * 현재 작동 중인 주요 펌프 리스트 조회
     * @return 현재 작동 중인 주요 펌프의 정보를 담은 리스트
     */
    List < HashMap < String, Object >> nowRunAllPriPumpList();

    /**
     * 특정 조건에 따른 펌프 생산 ON/OFF 리스트 조회
     * @param map 조회 조건을 담은 매핑 정보
     * @return 조회된 펌프 생산 ON/OFF 정보 리스트
     */
    List < HashMap < String, Object >> selectPumpPrdctOnOffList(HashMap < String, Object > map);

    /**
     * 특정 조건에 따른 최근 펌프 생산 ON/OFF 리스트 조회
     * @param map 조회 조건을 담은 매핑 정보
     * @return 조회된 최근 펌프 생산 ON/OFF 정보 리스트
     */
    List < HashMap < String, Object >> selectPumpPrdctOnOffLastList(HashMap < String, Object > map);

    /**
     * 현재 펌프 생산 ON/OFF 상태 리스트 조회
     * @param map 조회 조건을 담은 매핑 정보
     * @return 조회된 현재 펌프 생산 ON/OFF 정보 리스트
     */
    List < HashMap < String, Object >> selectPumpPrdctNowOnOffList(HashMap < String, Object > map);

    /**
     * 펌프 상태 체크 리스트 조회
     * @param map 조회 조건을 담은 매핑 정보
     * @return 펌프 상태 체크 리스트
     */
    List < HashMap < String, Object >> selectPumpStatusCheck(HashMap < String, Object > map);

    /**
     * 밸브 상태 체크 리스트 조회
     * @param map 조회 조건을 담은 매핑 정보
     * @return 밸브 상태 체크 리스트
     */
    List < HashMap < String, Object >> selectValveStatusCheck(HashMap < String, Object > map);

    HashMap < String, Object > selectVVKStatusCheck();

    /**
     * 제어 태그 리스트 조회
     * @param map 조회 조건을 담은 매핑 정보
     * @return 제어 태그 리스트
     */
    List < HashMap < String, Object >> selectCtrTagList(HashMap < String, Object > map);

    /**
     * AI 상태 조회
     * @return AI 상태 리스트
     */
    List < HashMap < String, Object >> selectAiStatus();

    /**
     * 특정 기본값을 기준으로 AI 펌프 그룹 리스트 조회
     * @param default_value 기준 값
     * @return AI 펌프 그룹 리스트
     */
    List < HashMap < String, Object >> selectAiPumpGrpList(int default_value);

    /**
     * 펌프 그룹 리스트 조회
     * @return 펌프 그룹 리스트
     */
    List < HashMap < String, Object >> selectPumpGrpList();

    /**
     * 현재 인버터 펌프 항목 조회
     * @return 인버터 펌프 항목 리스트
     */
    List < HashMap < String, Object >> nowInverterPumpItem();


    List < HashMap < String, Object >> selectPumpInfList();

    /**
     * 마지막 제어 태그 리스트 조회
     * @return 마지막 제어 태그 리스트
     */
    HashMap < String, Object > selectLastEndCtrTagList();

    /**
     * 테스트 모드 조회
     * @return 테스트 모드 정보
     */
    HashMap < String, Object > selectTestMode();

    /**
     * 제어 테스트 모드 조회
     * @return 제어 테스트 모드 정보
     */
    HashMap < String, Object > selectCtrTestMode();

    /**
     * 특정 조건에 따른 현재 작동 중인 펌프 항목 조회
     * @param map 조회 조건을 담은 매핑 정보
     * @return 현재 작동 중인 펌프 항목
     */
    HashMap < String, Object > nowRunAllPumpItem(HashMap < String, Object > map);

    /**
     * 펌프 주파수 상태 체크 조회
     * @param map 조회 조건을 담은 매핑 정보
     * @return 주파수 상태 체크 결과
     */
    HashMap < String, Object > selectPumpFreqStatusCheck(HashMap < String, Object > map);

    /**
     * 현재 원시 데이터 조회
     * @param map 조회 조건을 담은 매핑 정보
     * @return 원시 데이터
     */
    HashMap < String, Object > selectNowRawData(HashMap < String, Object > map);

    /**
     * 고령 관압 제어 보정값 반환
     * @return 관압 제어 보정 값
     */
    HashMap<String, Object> selectTPPCorrection();

    /**
     * 고령 생활 제어 압력 반환
     * @return 생활 압력
     */
    HashMap < String, Object > selectLifeTPP();

    /**
     * 선남가압장 펌프 제어 모드 확인
     * @return 0(비활성), 1(활성)
     */
    HashMap<String,Object> selectGrSnPumpMode();

    /**
     * 동기화 버튼 상태 반환
     * @return 인버터 상태
     */
    HashMap<String, Object> selectInvStatus();

    HashMap<String, Object> selectCBBStatus(HashMap<String, Object> map);

    /**
     * 리액터 모드 수 반환
     * @return 리액터 모드 수
     */
    int checkREACTModeCount();

    /**
     * 선남가압장 펌프 제어 모드 변경
     * @param map 모드 변경
     */
    void updateGrSnPumpMode(HashMap < String, Object > map);

    /**
     * HMI 태그 로그 삽입
     * @param map 삽입할 데이터
     */
    void insertHmiTagLog(HashMap < String, Object > map);

    /**
     * HMI 태그 삽입
     * @param map 삽입할 데이터
     */
    void insertHmiTag(HashMap < String, Object > map);

    /**
     * 펌프 알람 정보 삽입
     * @param map 삽입할 알람 정보
     */
    void emsPumpAlarmInsert(HashMap < String, Object > map);

    /**
     * 제어 태그 업데이트
     * @param map 업데이트할 데이터
     */
    void updateCtrTag(HashMap < String, Object > map);

    /**
     * 제어 태그 초기화
     */
    void initCtrTag();

    void updateAiStatusForPump(HashMap<String, Object> map);


}