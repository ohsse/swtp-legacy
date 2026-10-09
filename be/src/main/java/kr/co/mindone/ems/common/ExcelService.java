package kr.co.mindone.ems.common;
/**
 * packageName    : kr.co.mindone.common
 * fileName       : ExcelService
 * author         : geunwon
 * date           : 24. 9. 23.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 24. 9. 23.        geunwon       최초 생성
 */

import io.swagger.models.auth.In;
import kr.co.mindone.ems.ai.AiService;
import kr.co.mindone.ems.setting.SettingService;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.ss.util.CellRangeAddress;
import org.apache.poi.xssf.streaming.SXSSFSheet;
import org.apache.poi.xssf.streaming.SXSSFWorkbook;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class ExcelService {
    @Autowired
    private SettingService settingService;

    @Autowired
    private AiService aiService;

    @Autowired
    private CommonService commonService;

    @Value("${excel.sheet.title.power.all}")
    private String sheetTitlePowerAll;

    @Value("${excel.sheet.title.power.zone}")
    private String sheetTitlePowerZone;

    @Value("${excel.sheet.title.power.time}")
    private String sheetTitlePowerTime;

    @Value("${excel.sheet.title.pump}")
    private String sheetTitlePump;

    @Value("${excel.sheet.title.tank}")
    private String sheetTitleTank;

    /**
     * Poi라이브러리 WorkBook 생성
     * @param date 데이터 조회 날짜
     * @return workBook
     */
    public SXSSFWorkbook workbookCreate(String date)
    {
        SXSSFWorkbook workbook = new SXSSFWorkbook();
        //전력사용량 시트
        createPowerAllSheet(workbook, date);
        createPowerZoneSheet(workbook, date);
        createPumpSheet(workbook, date);
        createTankSheet(workbook, date);
        createPowerTime(workbook, date);


        // 엑셀 시트에 데이터 쓰기 (예: 간단한 텍스트)
        /*Row row = sheet.createRow(0);
        Cell cell = row.createCell(0);
        cell.setCellValue("Hello, Excel!");*/

        return workbook;
    }

    /**
     * 리포트 페이지 전력 시간대
     * @param workbook csv를 생성할 workBook
     * @param date 데이터 조회 날짜
     */
    public void createPowerTime(SXSSFWorkbook workbook, String date)
    {
       Sheet sheet = workbook.createSheet(sheetTitlePowerTime);
       HashMap<String, Object> params = new HashMap<>();
       params.put("date", date);

       List<HashMap<String, Object>> tankDataList = settingService.selectReport4(params);

    }

    /**
     * 리포트 페이지 배수지 데이터
     * @param workbook csv생성할 workBook
     * @param date 데이터 조회 날짜
     */
    public void createTankSheet(SXSSFWorkbook workbook, String date)
    {
        Sheet sheet = workbook.createSheet(sheetTitleTank);
        HashMap<String, Object> params = new HashMap<>();
        params.put("date", date);

        List<HashMap<String, Object>> tankDataList = settingService.selectReport4(params);

        Row row_0 = sheet.createRow(0);
        row_0.createCell(0).setCellValue("구분");
        sheet.addMergedRegion(new CellRangeAddress(0, 1, 0, 0));

        Row row_1 = sheet.createRow(1);
        row_1.createCell(0).setCellValue("구분");
        Row row_2 = sheet.createRow(2);
        row_2.createCell(0).setCellValue("최대");
        Row row_3 = sheet.createRow(3);
        row_3.createCell(0).setCellValue("최소");
        Row row_4 = sheet.createRow(4);
        row_4.createCell(0).setCellValue("평균");
        
        int startColumnIndex = 1;

        for(HashMap<String, Object> tankItem : tankDataList)
        {
            row_0.createCell(startColumnIndex).setCellValue(tankItem.get("TNK_GRP_NM").toString());
            row_1.createCell(startColumnIndex).setCellValue(tankItem.get("TNK_NM").toString());
            row_2.createCell(startColumnIndex).setCellValue(tankItem.get("max_value").toString());
            row_3.createCell(startColumnIndex).setCellValue(tankItem.get("min_value").toString());
            row_4.createCell(startColumnIndex).setCellValue(tankItem.get("avg_value").toString());
            startColumnIndex++;
        }

        for (int rowIndex = 0; rowIndex < 1; rowIndex++) {
            Row row = sheet.getRow(rowIndex);
            int numCols = row.getPhysicalNumberOfCells();

            for (int colIndex = 0; colIndex < numCols; colIndex++) {
                Cell cell = row.getCell(colIndex);

                if (cell != null) {
                    String cellValue = cell.getStringCellValue();

                    // 현재 셀의 값과 다음 셀의 값을 비교하여 연속 중복 데이터 찾기
                    int mergeEnd = colIndex;
                    while (mergeEnd < numCols - 1) {
                        Cell nextCell = row.getCell(mergeEnd + 1);
                        if (nextCell != null) {
                            String nextCellValue = nextCell.getStringCellValue();
                            if (cellValue.equals(nextCellValue)) {
                                mergeEnd++;
                            } else {
                                break;
                            }
                        } else {
                            break;
                        }
                    }
                    if (mergeEnd > colIndex) {
                        // 연속 중복 데이터를 병합
                        sheet.addMergedRegion(new CellRangeAddress(
                                rowIndex, rowIndex, colIndex, mergeEnd));
                        colIndex = mergeEnd; // 다음 반복에서 건너뛰기
                    }
                }
            }
        }

        sheet = setSheetStyle(workbook, sheet, 12, 1, startColumnIndex);
    }

    /**
     * 리포트페이지 펌프 데이터
     * @param workbook csv생성할 workBook
     * @param date 데이터 조회 날짜
     */
    public void createPumpSheet(SXSSFWorkbook workbook, String date)
    {
        Sheet sheet = workbook.createSheet(sheetTitlePump);
        HashMap<String, Object> params = new HashMap<>();
        params.put("date", date);

        List<HashMap<String, Object>> pumpGrpItem = commonService.selectPumpGroupItem();
        List<HashMap<String, Object>> pumpList = aiService.getPumpUseStatus();
        List<HashMap<String, Object>> pumpDataList = settingService.selectReportPump(params);

        HashMap<String, Object> pumpDataPwrDay = pumpDataList.get(0);
        HashMap<String, Object> pumpDataCtrDay = pumpDataList.get(1);
        HashMap<String, Object> pumpDataPwrMonth = pumpDataList.get(2);
        HashMap<String, Object> pumpDataCtrMonth = pumpDataList.get(3);

        Row row_0 = sheet.createRow(0);
        row_0.createCell(0).setCellValue("구분");
        sheet.addMergedRegion(new CellRangeAddress(0, 1, 0, 0));

        Row row_1 = sheet.createRow(1);

        Row row_2 = sheet.createRow(2); //일누계 전력
        row_2.createCell(0).setCellValue("일누계(전력사용량)");

        Row row_3 = sheet.createRow(3); //일누계 비율
        row_3.createCell(0).setCellValue("일누계(비율)");

        Row row_4 = sheet.createRow(4); //월누계 전력
        row_4.createCell(0).setCellValue("월누계(전력사용량)");

        Row row_5 = sheet.createRow(5); //월누계 비율
        row_5.createCell(0).setCellValue("월누계(비율)");

        boolean isFirstColumn = true;
        int lastRawCoulumn = 1;
        for(HashMap<String, Object> item : pumpGrpItem)
        {
            int nowPumpGrp = Integer.parseInt(item.get("PUMP_GRP").toString());
            if(isFirstColumn)
            {
                int fistLastRawCoulumn = lastRawCoulumn;
                row_0.createCell(lastRawCoulumn).setCellValue(item.get("PUMP_GRP_NM").toString());
                lastRawCoulumn = Integer.parseInt(item.get("GRP_COUNT").toString());
                isFirstColumn = false;
                sheet.addMergedRegion(new CellRangeAddress(0, 0, fistLastRawCoulumn, lastRawCoulumn));

                for(HashMap<String, Object> pumpItem : pumpList)
                {
                    int pumpGrpIdx= Integer.parseInt(pumpItem.get("PUMP_GRP").toString());
                    if(pumpGrpIdx == 1){
                        row_1.createCell(Integer.parseInt(pumpItem.get("PUMP_GRP_IDX").toString())).setCellValue(pumpItem.get("PUMP_NM").toString());

                        for(int i=1; i<=lastRawCoulumn; i++)
                        {
                            row_2.createCell(i).setCellValue(pumpDataPwrDay.get("pump_"+i).toString());
                            row_3.createCell(i).setCellValue(pumpDataCtrDay.get("pump_"+i).toString());
                            row_4.createCell(i).setCellValue(pumpDataPwrMonth.get("pump_"+i).toString());
                            row_5.createCell(i).setCellValue(pumpDataCtrMonth.get("pump_"+i).toString());
                        }
                    }
                }
            }
            else
            {
                int nowFristRawCoulumn = lastRawCoulumn+ 1; //6
                row_0.createCell(nowFristRawCoulumn).setCellValue(item.get("PUMP_GRP_NM").toString());
                lastRawCoulumn += Integer.parseInt(item.get("GRP_COUNT").toString());
                if(nowFristRawCoulumn < lastRawCoulumn)
                {
                    sheet.addMergedRegion(new CellRangeAddress(0, 0, nowFristRawCoulumn, lastRawCoulumn));
                }
                for(HashMap<String, Object> pumpItem : pumpList)
                {
                    int pumpGrpIdx= Integer.parseInt(pumpItem.get("PUMP_GRP").toString());
                    if(pumpGrpIdx == nowPumpGrp){
                        row_1.createCell(Integer.parseInt(pumpItem.get("PUMP_GRP_IDX").toString())+nowFristRawCoulumn-1).setCellValue(pumpItem.get("PUMP_NM").toString());

                        for(int i=nowFristRawCoulumn; i<=lastRawCoulumn; i++)
                        {
                           row_2.createCell(i).setCellValue(pumpDataPwrDay.get("pump_"+i).toString());
                           row_3.createCell(i).setCellValue(pumpDataCtrDay.get("pump_"+i).toString());
                           row_4.createCell(i).setCellValue(pumpDataPwrMonth.get("pump_"+i).toString());
                           row_5.createCell(i).setCellValue(pumpDataCtrMonth.get("pump_"+i).toString());
                       }

                    }
                }
            }
        }
        lastRawCoulumn++;
        row_0.createCell(lastRawCoulumn).setCellValue("유효합계 (kWh)");
        sheet.addMergedRegion(new CellRangeAddress(0, 1, lastRawCoulumn, lastRawCoulumn));
        row_2.createCell(lastRawCoulumn).setCellValue(pumpDataPwrDay.get("pwr_sum").toString());
        row_3.createCell(lastRawCoulumn).setCellValue(pumpDataCtrDay.get("pwr_sum").toString());
        row_4.createCell(lastRawCoulumn).setCellValue(pumpDataPwrMonth.get("pwr_sum").toString());
        row_5.createCell(lastRawCoulumn).setCellValue(pumpDataCtrMonth.get("pwr_sum").toString());

        lastRawCoulumn++;
        row_0.createCell(lastRawCoulumn).setCellValue("용수공급량 (m3)");
        sheet.addMergedRegion(new CellRangeAddress(0, 1, lastRawCoulumn, lastRawCoulumn));
        row_2.createCell(lastRawCoulumn).setCellValue(pumpDataPwrDay.get("frq_value").toString());
        row_3.createCell(lastRawCoulumn).setCellValue(pumpDataCtrDay.get("frq_value").toString());
        row_4.createCell(lastRawCoulumn).setCellValue(pumpDataPwrMonth.get("frq_value").toString());
        row_5.createCell(lastRawCoulumn).setCellValue(pumpDataCtrMonth.get("frq_value").toString());
        lastRawCoulumn++;
        row_0.createCell(lastRawCoulumn).setCellValue("원단위 (kWh/m3)");
        sheet.addMergedRegion(new CellRangeAddress(0, 1, lastRawCoulumn, lastRawCoulumn));
        row_2.createCell(lastRawCoulumn).setCellValue(pumpDataPwrDay.get("basic_unit").toString());
        row_3.createCell(lastRawCoulumn).setCellValue(pumpDataCtrDay.get("basic_unit").toString());
        row_4.createCell(lastRawCoulumn).setCellValue(pumpDataPwrMonth.get("basic_unit").toString());
        row_5.createCell(lastRawCoulumn).setCellValue(pumpDataCtrMonth.get("basic_unit").toString());
        lastRawCoulumn++;
        sheet = setSheetStyle(workbook, sheet, 12, 1, lastRawCoulumn);

    }

    /**
     * 리포트 페이지 설비별 전력 데이터
     * @param workbook csv생성할 workBook
     * @param date 데이터 조회 날짜
     */
    public void createPowerZoneSheet(SXSSFWorkbook workbook, String date)
    {
        Sheet sheet = workbook.createSheet(sheetTitlePowerZone);
        HashMap<String, Object> params = new HashMap<>();
        params.put("date", date);

        Row row_0 = sheet.createRow(0);
        row_0.createCell(0).setCellValue("구분");
        row_0.createCell(1).setCellValue("총전력량");
        int rowTitleDataStrNum = 2;
        int startRow = 1;


        Row row_1 = sheet.createRow(1);
        Row row_2 = sheet.createRow(2);
        Row row_3 = sheet.createRow(3);
        Row row_4 = sheet.createRow(4);

        List<HashMap<String, Object>> zoneList = settingService.selectZone(params);
        List<HashMap<String, Object>> zoneDataList = settingService.selectReportZonePwr(params);



        for(HashMap<String, Object> item : zoneList)
        {
            for (HashMap<String, Object> dataItem : zoneDataList) {
                for (Map.Entry<String, Object> dataEntry : dataItem.entrySet()) {
                    String dataKey = dataEntry.getKey();
                    if(dataKey.equals(item.get("zone_name").toString()))
                    {
                        if(dataItem.get("type").toString().equals("kwh_dayAgo"))
                        {
                            row_1.createCell(0).setCellValue("전일");
                            row_1.createCell(1).setCellValue(dataItem.get("kwh_sum").toString());
                            row_1.createCell(rowTitleDataStrNum).setCellValue(dataItem.get(dataKey).toString());
                        }
                        else if(dataItem.get("type").toString().equals("kwh_day"))
                        {
                            row_2.createCell(0).setCellValue("금일");
                            row_2.createCell(1).setCellValue(dataItem.get("kwh_sum").toString());
                            row_2.createCell(rowTitleDataStrNum).setCellValue(dataItem.get(dataKey).toString());
                        }
                        else if(dataItem.get("type").toString().equals("kwh_month"))
                        {
                            row_3.createCell(0).setCellValue("금월");
                            row_3.createCell(1).setCellValue(dataItem.get("kwh_sum").toString());
                            row_3.createCell(rowTitleDataStrNum).setCellValue(dataItem.get(dataKey).toString());
                        }
                        else if(dataItem.get("type").toString().equals("kwh_year"))
                        {
                            row_4.createCell(0).setCellValue("금년");
                            String tempTotalValue = (Double.parseDouble(dataItem.get("kwh_sum").toString()) * 0.001) + "(mWh)";
                            row_4.createCell(1).setCellValue(tempTotalValue);
                            row_4.createCell(rowTitleDataStrNum).setCellValue(dataItem.get(dataKey).toString());
                        }
                    }
                }
                startRow++;
            }
            row_0.createCell(rowTitleDataStrNum).setCellValue(item.get("zone_name").toString());
            rowTitleDataStrNum++;
        }

        sheet = setSheetStyle(workbook, sheet, 14, 0, rowTitleDataStrNum);

        //return sheet;
    }

    /**
     * 리포트 페이지 전제 전력 데이터
     * @param workbook csv생성할 workBook
     * @param date 데이터 조회 날짜
     */
    public void createPowerAllSheet(SXSSFWorkbook workbook, String date)
    {
        Sheet sheet = workbook.createSheet(sheetTitlePowerAll);

        //전력사용량 title bar
        Row row_0 = sheet.createRow(0);
        row_0.createCell(0).setCellValue("구분");
        //sheet.addMergedRegion(new CellRangeAddress(0, 1, 0, 0));

        row_0.createCell(1).setCellValue("시간대별 전력 사용량 (kWh)");
        //sheet.addMergedRegion(new CellRangeAddress(0, 0, 1, 3));

        Row row_1 = sheet.createRow(1);
        row_1.createCell(0).setCellValue("구분");
        row_1.createCell(1).setCellValue("경부하");
        row_1.createCell(2).setCellValue("중부하");
        row_1.createCell(3).setCellValue("최대부하");

        row_0.createCell(4).setCellValue("시간대별 전력 사용량 비율(%)");
        row_1.createCell(4).setCellValue("경부하");
        row_1.createCell(5).setCellValue("중부하");
        row_1.createCell(6).setCellValue("최대부하");
        //sheet.addMergedRegion(new CellRangeAddress(0, 0, 4, 6));

        row_0.createCell(7).setCellValue("에너지 절감량(kWh)");
        row_1.createCell(7).setCellValue("에너지 절감량(kWh)");
        //sheet.addMergedRegion(new CellRangeAddress(0, 1, 7, 7));

        row_0.createCell(8).setCellValue("탄소 저감량(tCO2)");
        row_1.createCell(8).setCellValue("탄소 저감량(tCO2)");
        //sheet.addMergedRegion(new CellRangeAddress(0, 1, 8, 8));

        Row row_2 = sheet.createRow(2);
        row_2.createCell(0).setCellValue("전일");
        Row row_3 = sheet.createRow(3);
        row_3.createCell(0).setCellValue("금일");
        Row row_4 = sheet.createRow(4);
        row_4.createCell(0).setCellValue("금월");
        Row row_5 = sheet.createRow(5);
        row_5.createCell(0).setCellValue("금년");


        HashMap<String, Object> params = new HashMap<>();
        params.put("date", date);
                
        List<HashMap<String, Object>> tempReturnObjectList = new ArrayList<HashMap<String, Object>>();

        tempReturnObjectList.add(settingService.selectReportPwr(params,"dayAgo"));
        tempReturnObjectList.add(settingService.selectReportPwr(params,"day"));
        tempReturnObjectList.add(settingService.selectReportPwr(params,"month"));
        tempReturnObjectList.add(settingService.selectReportPwr(params,"year"));

        int startDataRow = 2; //데이터 시작 지점

        for(int i=0; i<tempReturnObjectList.size(); i++)
        {
            HashMap<String, Object> tempData = tempReturnObjectList.get(i);
            if(tempData.get("type").equals("kwh_dayAgo"))
            {
                Row tempRow = sheet.getRow(startDataRow);
                tempRow.createCell(1).setCellValue(tempData.get("l_kwh").toString());//경부하
                tempRow.createCell(4).setCellValue(tempData.get("l_kwh_p").toString());//경부하
                tempRow.createCell(2).setCellValue(tempData.get("m_kwh").toString()); //중간부하
                tempRow.createCell(5).setCellValue(tempData.get("m_kwh_p").toString());//경부하
                tempRow.createCell(3).setCellValue(tempData.get("h_kwh").toString()); //최대부하
                tempRow.createCell(6).setCellValue(tempData.get("h_kwh_p").toString());//경부하
                tempRow.createCell(7).setCellValue(tempData.get("savingKwh").toString()); //전력절감량
                tempRow.createCell(8).setCellValue(tempData.get("savingCo2").toString()); //탄소저감량
            }
            else if(tempData.get("type").equals("kwh_day"))
            {
                Row tempRow = sheet.getRow(startDataRow+1);
                tempRow.createCell(1).setCellValue(tempData.get("l_kwh").toString());//경부하
                tempRow.createCell(4).setCellValue(tempData.get("l_kwh_p").toString());//경부하
                tempRow.createCell(2).setCellValue(tempData.get("m_kwh").toString()); //중간부하
                tempRow.createCell(5).setCellValue(tempData.get("m_kwh_p").toString());//경부하
                tempRow.createCell(3).setCellValue(tempData.get("h_kwh").toString()); //최대부하
                tempRow.createCell(6).setCellValue(tempData.get("h_kwh_p").toString());//경부하
                tempRow.createCell(7).setCellValue(tempData.get("savingKwh").toString()); //전력절감량
                tempRow.createCell(8).setCellValue(tempData.get("savingCo2").toString()); //탄소저감량
            }
            else if(tempData.get("type").equals("kwh_month"))
            {
                Row tempRow = sheet.getRow(startDataRow+2);
                tempRow.createCell(1).setCellValue(tempData.get("l_kwh").toString());//경부하
                tempRow.createCell(4).setCellValue(tempData.get("l_kwh_p").toString());//경부하
                tempRow.createCell(2).setCellValue(tempData.get("m_kwh").toString()); //중간부하
                tempRow.createCell(5).setCellValue(tempData.get("m_kwh_p").toString());//경부하
                tempRow.createCell(3).setCellValue(tempData.get("h_kwh").toString()); //최대부하
                tempRow.createCell(6).setCellValue(tempData.get("h_kwh_p").toString());//경부하
                tempRow.createCell(7).setCellValue(tempData.get("savingKwh").toString()); //전력절감량
                tempRow.createCell(8).setCellValue(tempData.get("savingCo2").toString()); //탄소저감량
            }
            else if(tempData.get("type").equals("kwh_year"))
            {
                Row tempRow = sheet.getRow(startDataRow+3);
                tempRow.createCell(1).setCellValue(tempData.get("l_kwh").toString());//경부하
                tempRow.createCell(4).setCellValue(tempData.get("l_kwh_p").toString());//경부하
                tempRow.createCell(2).setCellValue(tempData.get("m_kwh").toString()); //중간부하
                tempRow.createCell(5).setCellValue(tempData.get("m_kwh_p").toString());//경부하
                tempRow.createCell(3).setCellValue(tempData.get("h_kwh").toString()); //최대부하
                tempRow.createCell(6).setCellValue(tempData.get("h_kwh_p").toString());//경부하
                tempRow.createCell(7).setCellValue(tempData.get("savingKwh").toString()); //전력절감량
                tempRow.createCell(8).setCellValue(tempData.get("savingCo2").toString()); //탄소저감량
            }

        }
        sheet = setSheetStyle(workbook, sheet, 14, 1, 9);

        sheet.addMergedRegion(new CellRangeAddress(0, 1, 0, 0)); //구분
        sheet.addMergedRegion(new CellRangeAddress(0, 0, 1, 3)); //시간대별 전력 사용량 (kWh)
        sheet.addMergedRegion(new CellRangeAddress(0, 0, 4, 6)); //시간대별 전력 사용량 비율(%)
        sheet.addMergedRegion(new CellRangeAddress(0, 1, 7, 7)); //에너지 절감량(kWh)
        sheet.addMergedRegion(new CellRangeAddress(0, 1, 8, 8)); //탄소 저감량(tCO2)



        //return sheet;
    }

    /**
     * Poi라이브러리 SXSSFWorkbook 스타일 메서드
     * @param workbook 적용할 workBook
     * @param sheet 적용할 sheet
     * @param defaultWidth 기본 가로 크기
     * @param titleEndRow tileRow 위치
     * @param lastCell 마지막 Cell 위치
     * @return style 적용된 workBook
     */
    public Sheet setSheetStyle(SXSSFWorkbook workbook, Sheet sheet, int defaultWidth, int titleEndRow, int lastCell)
    {
        CellStyle centerAlignmentStyle = workbook.createCellStyle();
        centerAlignmentStyle.setAlignment(HorizontalAlignment.CENTER); // 가로 가운데 정렬
        centerAlignmentStyle.setVerticalAlignment(VerticalAlignment.CENTER); // 세로 가운데 정렬
        centerAlignmentStyle.setBorderTop(BorderStyle.THIN);
        centerAlignmentStyle.setBorderRight(BorderStyle.THIN);
        centerAlignmentStyle.setBorderBottom(BorderStyle.THIN);
        centerAlignmentStyle.setBorderLeft(BorderStyle.THIN);

        CellStyle valueStyle = workbook.createCellStyle();
        valueStyle.setBorderTop(BorderStyle.THIN);
        valueStyle.setBorderRight(BorderStyle.THIN);
        valueStyle.setBorderBottom(BorderStyle.THIN);
        valueStyle.setBorderLeft(BorderStyle.THIN);
        valueStyle.setAlignment(HorizontalAlignment.RIGHT);

        //빈칸이 존재하는 경우 Blank 처리, 셀이 생성되지 않으면 스타일이 적용되지 않음

        //int titleEndColuemIndex = 0;
        for (int rowIndex = 0; rowIndex <= sheet.getLastRowNum(); rowIndex++) {
            Row row = sheet.getRow(rowIndex);
            if (row != null) {
                /*if(titleEndRow == rowIndex)
                {
                   titleEndColuemIndex = row.getLastCellNum();
                }*/
                for (int columnIndex = 0; columnIndex < lastCell; columnIndex++) {
                    Cell cell = row.getCell(columnIndex);
                    if (cell != null) {
                        //System.out.println("lastCell:"+ lastCell+"/ rowIndex:"+ rowIndex +"/ columnIndex:"+ columnIndex+ "//"+cell.getStringCellValue());
                        if(columnIndex > 0 && cell.getRowIndex() > titleEndRow)
                        {
                            cell.setCellStyle(valueStyle); //스타일 적용
                        }
                        else
                        {
                            cell.setCellStyle(centerAlignmentStyle); //스타일 적용, 타이을 부분
                        }
                        //숫자 단위 처리
                        if(cell.getStringCellValue().matches("[-+]?\\d*\\.?\\d+([eE][-+]?\\d+)?"))
                        {
                            double tempCellValue = Double.parseDouble(cell.getStringCellValue());
                            if(tempCellValue > 1000000)
                            {
                                cell.setCellValue((tempCellValue*0.001)+"(mWh)");
                            }
                        }
                        sheet.setColumnWidth(columnIndex,  (defaultWidth + cell.toString().length()) * 256); //적정 넓이 지정
                    }
                    else {
                        //System.out.println("getLastRowNum:"+ sheet.getLastRowNum()+"/ rowIndex:"+ rowIndex +"/ columnIndex:"+ columnIndex+ "// CELL BLANK");
                        row.createCell(columnIndex).setBlank();
                        Cell cell_blank = row.getCell(columnIndex);
                        cell_blank.setCellStyle(valueStyle); //스타일 적용
                        sheet.setColumnWidth(columnIndex,  (defaultWidth) * 256); //적정 넓이 지정
                    }
                }
            }
        }
        return sheet;
    }

}
