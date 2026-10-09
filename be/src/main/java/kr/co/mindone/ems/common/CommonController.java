package kr.co.mindone.ems.common;
/**
 * packageName    : kr.co.mindone.common
 * fileName       : CommonController
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
import kr.co.mindone.ems.energy.EnerSpendService;
import org.apache.ibatis.annotations.Param;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.xssf.streaming.SXSSFWorkbook;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.config.KafkaListenerEndpointRegistry;
import org.springframework.kafka.listener.MessageListenerContainer;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

import javax.servlet.http.HttpServletResponse;
import java.text.DecimalFormat;
import java.time.LocalDate;
import java.time.YearMonth;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.io.IOException;

import static kr.co.mindone.ems.common.SavingService.*;

@RequestMapping("cm")
@RestController
public class CommonController extends BaseController {

    @Autowired
    private CommonService commonService;
    @Autowired
    private EnerSpendService enerSpendService;

    @Autowired
    private ExcelService excelService;

    @Autowired SavingService savingService;

    @Autowired
    private KafkaListenerEndpointRegistry kafkaListenerEndpointRegistry;

    /**
     * Kafka 리스너 시작/정지
     * @param mode 리스너 모드 (start/stop)
     * @return 리스너 상태 메시지
     */
    @GetMapping("/startListener")
    public String startListener(@Param("mode") String mode) {
        // 리스너 ID는 @KafkaListener 어노테이션의 id 속성으로 지정
        MessageListenerContainer listenerContainer = kafkaListenerEndpointRegistry.getListenerContainer("listenFromBeginning");

        if (listenerContainer != null && mode.equals("start")) {
            //autoStartup 상태가 false인 상태의 리스너를 동작 시킴
            listenerContainer.start();
            return "Listener started";
        } else {
            listenerContainer.stop();
            return "Listener started";
        }
    }

    /**
     * 정수장 태그 단위 정보 조회
     * @param map 태그 정보 파라미터
     * @return 태그 정보 목록
     */
    @Operation(summary = "정수장 태그 단위 정보", description = "selectWppTagInfoList?tag_typ=pump,tnk")
    @GetMapping("/selectTagInfo")
    public ResponseObject < List < HashMap < String, Object >>> selectTagInfo(@RequestParam HashMap < String, Object > map) {
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, commonService.selectTagInfo(map));
    }

    /**
     * WPP 태그 코드 목록 조회
     * @param func_typ 기능 타입
     * @return 태그 코드 목록
     */
    @Operation(summary = "정수장 태그 단위 정보", description = "selectWppTagInfoList?func_typ=page_url")
    @GetMapping("/selectWppTagCodeList")
    public ResponseObject < List < HashMap < String, Object >>> selectWppTagCodeList(@Param("func_typ") String func_typ) {
        //System.out.println("func_typ:"+func_typ);
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, commonService.selectWppTagCodeList(func_typ));
    }

    /**
     * 대시보드 시설별 전력사용률 조회
     * @param map 시설별 데이터 파라미터
     * @return 전력사용률 목록
     */
    @Operation(summary = "대시보드 시설별 전력사용률", description = "selectWppPwrPercentList")
    @GetMapping("/selectWppPwrPercentList")
    public ResponseObject < List < HashMap < String, Object >>> selectWppPwrList(@RequestParam HashMap < String, Object > map) {
        DecimalFormat df = new DecimalFormat("0.00");
        List < HashMap < String, Object >> tempReturnObjectList = new ArrayList < HashMap < String, Object >> ();
        List < HashMap < String, Object >> nowPeakList = enerSpendService.nowPeak();
        List < HashMap < String, Object >> zonePeakList = enerSpendService.sisul_sunsi(map);

        double nowAllPwr = 0.0;

        if (nowPeakList.size() == 1) {
            nowAllPwr = Double.parseDouble(nowPeakList.get(0).get("kWVALUE").toString());
        } else {
            nowAllPwr = 2000;
        }
        //System.out.println("nowPeakList:"+nowPeakList.toString());
        //System.out.println("zonePeakList:"+zonePeakList.toString());

        double nowAllPwrZone = 0.0;

        for (HashMap < String, Object > item: zonePeakList) {
            if (!item.get("zone_name").toString().equals("태양광")) {
                nowAllPwrZone += Double.parseDouble(item.get("y").toString());
            }

        }

        //System.out.println("nowAllPwrZone:"+nowAllPwrZone);

        for (HashMap < String, Object > item: zonePeakList) {
            if (!item.get("zone_name").toString().equals("태양광")) {
                HashMap < String, Object > resultItem = new HashMap < > ();
                double nowPerCent = 0.0;
                nowPerCent = (Double.parseDouble(item.get("y").toString()) / nowAllPwrZone) * 100;
                //nowPerCent = (Double.parseDouble(item.get("y").toString()) / nowAllPwr ) * 100;
                resultItem.put(item.get("zone_name").toString(), df.format(nowPerCent));
                tempReturnObjectList.add(resultItem);
            }
        }
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, tempReturnObjectList);
    }

    /**
     * 엑셀 파일 다운로드
     * @param response HTTP 응답 객체
     * @param date 조회할 날짜
     * @throws IOException 파일 다운로드 시 발생할 수 있는 예외
     */
    @GetMapping("/download")
    public void downloadExcel(HttpServletResponse response, @RequestParam String date) throws IOException {
        // 엑셀 워크북 생성
        try (SXSSFWorkbook workbook = excelService.workbookCreate(date)) {
            workbook.getSheetAt(0).trackAllColumnsForAutoSizing(); // 또는 trackColumnForAutoSizing(columnIndex)
            // HTTP 응답으로 엑셀 파일 다운로드
            response.setContentType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
            response.setHeader("Content-Disposition", "attachment; filename=sample.xlsx");

            workbook.write(response.getOutputStream());
        }
    }

    /**
     * 전력 절감량 수동 계산
     * @param map 계산을 위한 파라미터 (func_type: ago, month, year, all)
     * @return 계산 결과
     */
    @Operation(summary = "전력절감량 수동 계산", description = "?func_typ=page_url")
    @GetMapping("/saving")
    public ResponseObject < HashMap < String, Object >> saving(@RequestParam HashMap < String, Object > map) {
        //System.out.println("func_typ:"+func_typ);
        String func_type = map.get("func_type").toString();
        HashMap < String, Object > result = new HashMap < > ();
        if (func_type.equals("ago")) {
            result = savingService.savingCalculationInsert(RANGE_DAY_AGO, "none");
        } else if (func_type.equals("month")) {
            result = savingService.savingCalculationInsert(RANGE_MONTH, "none");
        } else if (func_type.equals("year")) {
            result = savingService.savingCalculationInsert(RANGE_YEAR, "none");
        } else if (func_type.equals("all") && !map.get("date").toString().isEmpty()) {
            String startDateStr = map.get("date").toString(); // 문자열로 제공된 시작 날짜
            DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");

            try {
                LocalDate startDate = LocalDate.parse(startDateStr, formatter);
                LocalDate endDate = LocalDate.now();

                // 일별 날짜 출력
                System.out.println("Daily Dates:");
                for (LocalDate date = startDate; !date.isAfter(endDate); date = date.plusDays(1)) {
                    String formattedDate = date.format(formatter);
                    System.out.println(formattedDate);

                    result = (savingService.savingCalculationInsert(RANGE_DAY, formattedDate));
                }

                // 월의 마지막 날 출력
                /*
                System.out.println("\nLast Day of Each Month:");
                LocalDate currentMonth = startDate.withDayOfMonth(1);  // 시작 월의 첫 날
                while (!currentMonth.isAfter(endDate.withDayOfMonth(1))) {
                    YearMonth yearMonth = YearMonth.from(currentMonth);
                    LocalDate lastDayOfMonth = yearMonth.atEndOfMonth();
                    if (!lastDayOfMonth.isAfter(endDate)) {
                        System.out.println("lastDayOfMonth:"+lastDayOfMonth.format(formatter));
                        result = (savingService.savingCalculationInsert(RANGE_MONTH, lastDayOfMonth.format(formatter)));
                    }
                    currentMonth = currentMonth.plusMonths(1);
                }*/
            } catch (DateTimeParseException e) {
                System.err.println("Invalid date format: " + startDateStr);
            }
        } else {
            result = savingService.savingCalculationInsert(RANGE_DAY, "none");
        }

        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, result);
    }

    /**
     * 테스트 API 호출
     * @param func_typ 기능 타입 파라미터
     * @return 테스트 API 결과 데이터
     */
    @GetMapping("/test/{params}")
    public ResponseObject < HashMap < String, Object >> testApi(@PathVariable("params") String func_typ) {
        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, commonService.selectTestApi(func_typ));
    }


    /**
     * 전력 절감량 수동 계산
     * @param map 계산을 위한 파라미터 (func_type: ago, month, year, all)
     * @return 계산 결과
     */
    @Operation(summary = "전력절감량 수동 계산", description = "?date=2024-01-01")
    @GetMapping("/savingCal")
    public ResponseObject<HashMap<String, Object>> savingCal(@RequestParam HashMap<String, Object> map) {
        String dateStr = map.get("date").toString();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");
        HashMap<String, Object> result = new HashMap<>();

        try {
            LocalDate startDate = LocalDate.of(2024, 1, 1); // 시작 날짜를 2024-01-01로 설정
            LocalDate endDate = LocalDate.parse(dateStr, formatter); // 입력받은 dateStr을 종료 날짜로 설정
            LocalDate currentDate = LocalDate.now();

            if (endDate.isBefore(currentDate)) {
                // dateStr이 오늘 날짜 이전인 경우 2024-01-01부터 dateStr까지 일별로 수행
                System.out.println("Daily Dates:");
                for (LocalDate date = startDate; !date.isAfter(endDate); date = date.plusDays(1)) {
                    String formattedDate = date.format(formatter);
                    System.out.println(formattedDate);
                    result = savingService.savingCalculationInsert(RANGE_DAY, formattedDate);
                }
            } else {
                // dateStr이 오늘과 같은 경우
                System.out.println("Calculating for today only: " + currentDate.format(formatter));
                result = savingService.savingCalculationInsert(RANGE_DAY, "none");
            }
        } catch (DateTimeParseException e) {
            System.err.println("Invalid date format: " + dateStr);
        }

        return makeSuccessObj(ResponseMessage.SELECT_SUCCESS, result);
    }


}