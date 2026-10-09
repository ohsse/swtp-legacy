package com.mindone.editor.pump.repository;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.LinkedHashMap;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * {@code TB_PUMP_CAL} 의 {@code C_ORD=2} 주파수 조합 → 파이썬 {@code pumpHz} 조립 단위 테스트.
 *
 * <p>Spring 컨텍스트·DB 없이 정적 메서드를 직접 호출해 검증한다.</p>
 *
 * <p>검증 대상은 <b>자리 맞추기</b>다. 주파수 값은 조합에 든 모든 펌프가 아니라 가변속
 * ({@code PUMP_TYP=2}) 펌프에만 순서대로 대응하므로, 정속 펌프가 섞이면 한 칸씩 밀리기 쉽다.
 * 밀려도 예외가 나지 않고 "엉뚱한 펌프의 주파수로 거른 그럴듯한 곡선"이 나오기 때문에
 * 운영에서는 알아채기 어렵다 — 그래서 여기서 못박는다.</p>
 */
class PumpCombStatFreqTest {

    private static final int FIXED = 1;      // 정속
    private static final int VARIABLE = 2;   // 가변속

    /** 1·4번은 정속, 2·3번은 가변속인 현장 구성. */
    private static Map<Integer, Integer> mixedPumpTypes() {
        Map<Integer, Integer> types = new LinkedHashMap<>();
        types.put(1, FIXED);
        types.put(2, VARIABLE);
        types.put(3, VARIABLE);
        types.put(4, FIXED);
        return types;
    }

    /** 1~4번 전부 가변속인 현장 구성(군산). */
    private static Map<Integer, Integer> allVariablePumpTypes() {
        Map<Integer, Integer> types = new LinkedHashMap<>();
        for (int i = 1; i <= 4; i++) {
            types.put(i, VARIABLE);
        }
        return types;
    }

    @Test
    @DisplayName("정속 펌프가 섞여 있어도 주파수는 가변속 펌프에만 순서대로 붙는다")
    void skipsFixedSpeedPumps() {
        // 조합 1,2,3 중 가변속은 2·3번뿐 → 주파수 '27,29' 는 2번=27, 3번=29
        String pumpHz = PumpCombStatRepository.buildPumpHz("1,2,3", "27,29", mixedPumpTypes());

        assertThat(pumpHz).isEqualTo("2:27,3:29");
    }

    @Test
    @DisplayName("전부 가변속이면 조합 순서 그대로 1:1 대응한다")
    void mapsOneToOneWhenAllVariable() {
        String pumpHz = PumpCombStatRepository.buildPumpHz("1,3", "45,48", allVariablePumpTypes());

        assertThat(pumpHz).isEqualTo("1:45,3:48");
    }

    @Test
    @DisplayName("주파수 조합이 비어 있으면(미입력) null 을 돌려 주파수 조건 없이 분석하게 한다")
    void returnsNullWhenFreqCombBlank() {
        assertThat(PumpCombStatRepository.buildPumpHz("1,3", "", allVariablePumpTypes())).isNull();
        assertThat(PumpCombStatRepository.buildPumpHz("1,3", null, allVariablePumpTypes())).isNull();
    }

    @Test
    @DisplayName("가변속 펌프가 하나도 없는 조합이면 null 이다")
    void returnsNullWhenNoVariableSpeedPump() {
        String pumpHz = PumpCombStatRepository.buildPumpHz("1,4", "27,29", mixedPumpTypes());

        assertThat(pumpHz).isNull();
    }

    @Test
    @DisplayName("주파수 값이 가변속 펌프 수보다 모자라면 남는 펌프는 미지정으로 둔다")
    void ignoresMissingFreqValues() {
        // 가변속 2대(2·3번)인데 값은 하나뿐 → 2번만 실린다
        String pumpHz = PumpCombStatRepository.buildPumpHz("1,2,3", "27", mixedPumpTypes());

        assertThat(pumpHz).isEqualTo("2:27");
    }

    @Test
    @DisplayName("0·공백·숫자 아닌 주파수는 미지정으로 보고 건너뛰되 뒤 펌프의 자리는 지킨다")
    void skipsUnusableFreqValuesWithoutShifting() {
        // 2번 자리가 0(미지정)이어도 3번은 두 번째 값이 아니라 세 번째 값(31)을 받아야 한다
        Map<Integer, Integer> types = new LinkedHashMap<>();
        types.put(1, VARIABLE);
        types.put(2, VARIABLE);
        types.put(3, VARIABLE);

        assertThat(PumpCombStatRepository.buildPumpHz("1,2,3", "27,0,31", types))
                .isEqualTo("1:27,3:31");
        assertThat(PumpCombStatRepository.buildPumpHz("1,2,3", "27, ,31", types))
                .isEqualTo("1:27,3:31");
        assertThat(PumpCombStatRepository.buildPumpHz("1,2,3", "27,-,31", types))
                .isEqualTo("1:27,3:31");
    }

    @Test
    @DisplayName("소수 주파수는 보존하고 45.0 같은 정수형은 소수점을 뗀다")
    void keepsFractionalHzAndTrimsWholeNumbers() {
        String pumpHz = PumpCombStatRepository.buildPumpHz("1,2", "45.0,48.5", allVariablePumpTypes());

        assertThat(pumpHz).isEqualTo("1:45,2:48.5");
    }

    @Test
    @DisplayName("펌프 마스터에 없는 펌프번호는 구동 방식을 알 수 없으므로 건너뛴다")
    void skipsUnknownPumpIdx() {
        // 9번은 사전에 없다 → 가변속 여부를 알 수 없어 주파수 자리를 차지하지 않는다
        String pumpHz = PumpCombStatRepository.buildPumpHz("9,2,3", "27,29", mixedPumpTypes());

        assertThat(pumpHz).isEqualTo("2:27,3:29");
    }

    @Test
    @DisplayName("펌프조합이 비어 있으면 null 이다")
    void returnsNullWhenPumpCombBlank() {
        assertThat(PumpCombStatRepository.buildPumpHz("", "27,29", mixedPumpTypes())).isNull();
        assertThat(PumpCombStatRepository.buildPumpHz(null, "27,29", mixedPumpTypes())).isNull();
    }
}
