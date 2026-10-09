> 원문: [EPANET 2.2 — Units of Measurement / Error Messages / Command Line EPANET](https://usepa.github.io/EPANET2.2/back_matter.html)
> EPANET 2.2 공식 매뉴얼의 부록을 한국어로 정리한 문서입니다.
> **이 문서의 부록 C는 INP 입력 파일의 각 섹션 포맷 명세를 포함하며, INP 파서/컴포저 구현의 1차 근거입니다.**
> INP 섹션 키워드·컬럼명·키워드 값·예제 코드블록은 원문을 그대로 유지합니다.

# 부록 A. 측정 단위 (Units of Measurement)

Table 1 은 EPANET 의 파라미터와 그에 대응하는 미국 단위(US) 및 SI 단위를 나열한다.

| *PARAMETER* | *US CUSTOMARY* | *SI METRIC* |
| --- | --- | --- |
| Concentration | mg/L or ug/L | mg/L or ug/L |
| Demand | (see Flow units) | (see Flow units) |
| Diameter (Pipes) | inch | millimeter |
| Diameter (Tanks) | foot | meter |
| Efficiency | percent | percent |
| Elevation | foot | meter |
| Emitter Coefficient | flow unit/ (psi)1/2 | flow unit/ (meter)1/2 |
| Energy | kilowatt - hour | kilowatt - hour |
| Flow | CFS (cu foot/sec) GPM (gal/min) MGD (Million gal/day) IMGD (Imperial MGD) AFD (ac-foot/day) | LPS (liter/sec) LPM (liter/min) MLD (Megaliter/day) CMH (cubic meter/hr) CMD (cubic meter/day) |
| Friction Factor | unitless | unitless |
| Hydraulic Head | foot | meter |
| Length | foot | meter |
| Minor Loss Coefficient | unitless | unitless |
| Power | horsepower | kilowatt |
| Pressure | pounds per square inch | meter |
| Reaction Coefficient (Bulk) | 1st-order 1/day | 1st-order 1/day |
| Reaction Coefficient (Wall) | 0-order mass/L/day 1st-order ft/day | 0-order mass/L/day 1st-order meter/day |
| Roughness Coefficient | Darcy-Weisbach 10-3foot Otherwise unitless | Darcy-Weisbach millimeter Otherwise unitless |
| Source Mass Injection | mass/minute | mass/minute |
| Velocity | foot/second | meter/second |
| Volume | cubic foot | cubic meter |
| Water Age | hour | hour |

**참고**: 유량 단위로 CFS, GPM, AFD, MGD 를 선택하면 US Customary(미국 관용) 단위가 적용된다. 유량 단위를 리터 또는 세제곱미터로 표현하면 SI Metric(SI 미터법) 단위가 적용된다.

# 부록 B. 오류 메시지 (Error Messages)

Table 2 는 EPANET 의 오류 코드와 그 설명을 나열한다.

| *ID* | *EXPLANATION* |
| --- | --- |
| 101 | 사용 가능한 메모리가 부족하여 해석이 중단되었다. |
| 110 | 관망 수리 방정식을 풀 수 없어 해석이 중단되었다. 탱크나 저수지로 물리적으로 연결되지 않은 관망 부분이 있는지, 또는 관망 입력 데이터에 비현실적인 값이 있는지 확인하라. |
| 200 | 입력 데이터에서 하나 이상의 오류가 검출되었다. 오류의 성격은 아래에 나열된 200번대 오류 메시지로 설명된다. |
| 201 | 관망 데이터로부터 생성된 입력 파일의 한 줄에 구문 오류가 있다. 이는 EPANET 외부에서 사용자가 작성한 .INP 텍스트에서 발생할 가능성이 가장 높다. |
| 202 | 속성에 부적절한 숫자 값이 할당되었다. |
| 203 | 어떤 객체가 정의되지 않은 노드를 참조한다. |
| 204 | 어떤 객체가 정의되지 않은 링크를 참조한다. |
| 205 | 어떤 객체가 정의되지 않은 시간패턴을 참조한다. |
| 206 | 어떤 객체가 정의되지 않은 곡선을 참조한다. |
| 207 | 체크밸브를 제어하려는 시도가 있었다. 속성편집기(Property Editor)에서 관에 Check Valve 상태가 한 번 할당되면, 단순 제어(simple control)나 규칙 기반 제어(rule-based control) 어느 것으로도 그 상태를 변경할 수 없다. |
| 208 | 정의되지 않은 노드가 참조되었다. 예를 들어 제어 구문에서 발생할 수 있다. |
| 209 | 노드 속성에 부적절한 값이 할당되었다. |
| 210 | 정의되지 않은 링크가 참조되었다. 예를 들어 제어 구문에서 발생할 수 있다. |
| 211 | 링크 속성에 부적절한 값이 할당되었다. |
| 212 | 공급원 추적(source tracing) 해석이 정의되지 않은 추적 노드(trace node)를 참조한다. |
| 213 | 해석 옵션이 부적절한 값을 가진다(예: 음수 시간 간격 값). |
| 214 | 입력 파일에서 읽은 한 줄에 문자가 너무 많다. .INP 파일의 각 줄은 255자로 제한된다. |
| 215 | 둘 이상의 노드 또는 링크가 동일한 ID 라벨을 공유한다. |
| 216 | 정의되지 않은 펌프에 대해 에너지 데이터가 제공되었다. |
| 217 | 펌프에 대해 유효하지 않은 에너지 데이터가 제공되었다. |
| 219 | 밸브가 저수지나 탱크에 부적절하게 연결되었다. PRV, PSV, FCV 는 저수지나 탱크에 직접 연결될 수 없다. 둘 사이를 분리하기 위해 일정 길이의 관(pipe)을 사용하라. |
| 220 | 밸브가 다른 밸브에 부적절하게 연결되었다. PRV 는 동일한 하류 노드를 공유하거나 직렬로 연결될 수 없으며, PSV 는 동일한 상류 노드를 공유하거나 직렬로 연결될 수 없고, PSV 는 PRV 의 하류 노드에 직접 연결될 수 없다. |
| 221 | 규칙 기반 제어에 잘못 배치된 절(clause)이 포함되어 있다. |
| 223 | 해석할 노드가 관망에 충분하지 않다. 유효한 관망은 최소한 하나의 탱크/저수지와 하나의 절점 노드를 포함해야 한다. |
| 224 | 관망에 탱크 또는 저수지가 하나도 없다. |
| 225 | 탱크에 대해 유효하지 않은 하한/상한 수위가 지정되었다(예: 하한 수위가 상한 수위보다 높음). |
| 226 | 펌프에 대해 펌프 곡선(pump curve)이나 정격 출력(power rating)이 제공되지 않았다. 펌프는 Pump Curve 속성에 곡선 ID 가 할당되거나 Power 속성에 정격 출력이 할당되어야 한다. 두 속성이 모두 할당된 경우 Pump Curve 가 사용된다. |
| 227 | 펌프에 유효하지 않은 펌프 곡선이 있다. 유효한 펌프 곡선은 유량이 증가할수록 수두가 감소해야 한다. |
| 230 | 곡선의 X 값이 증가하지 않는다(non-increasing). |
| 233 | 어떤 노드가 어떤 링크에도 연결되어 있지 않다. |
| 302 | 시스템이 임시 입력 파일을 열 수 없다. 선택된 EPANET 임시 폴더(Temporary Folder)에 쓰기 권한이 부여되어 있는지 확인하라. |
| 303 | 시스템이 상태 보고서 파일(status report file)을 열 수 없다. Error 302 참조. |
| 304 | 시스템이 이진 출력 파일(binary output file)을 열 수 없다. Error 302 참조. |
| 308 | 결과를 파일에 저장할 수 없다. 디스크가 가득 찼을 때 발생할 수 있다. |
| 309 | 결과를 보고서 파일(report file)에 쓸 수 없다. 디스크가 가득 찼을 때 발생할 수 있다. |

# 부록 C. 커맨드라인 EPANET 및 입력 파일 포맷 (Command Line EPANET)

## 일반 지침 (General Instructions)

EPANET 은 DOS 창 안의 커맨드라인에서 콘솔 애플리케이션으로 실행할 수도 있다. 이 경우 관망 입력 데이터는 텍스트 파일에 담기고 결과는 텍스트 파일로 기록된다. 이 방식으로 EPANET 을 실행하는 커맨드라인은 다음과 같다.

```
runepanet  inpfile  rptfile  outfile
```

여기서 **inpfile** 은 입력 파일의 이름, **rptfile** 은 출력 보고서 파일(output report file)의 이름, **outfile** 은 결과를 특수한 이진 형식으로 저장하는 선택적 이진 출력 파일(binary output file)의 이름이다. 후자의 파일이 필요 없으면 입력 파일과 보고서 파일 이름만 제공하면 된다. 위 명령은 작성된 그대로, 사용자가 EPANET 이 설치된 디렉터리에서 작업하고 있거나 그 디렉터리가 시스템 PATH 변수에 추가되어 있다고 가정한다. 그렇지 않으면 실행 파일 **runepanet.exe** 와 커맨드라인의 파일들에 대해 전체 경로명(full pathname)을 사용해야 한다. 커맨드라인 EPANET 의 오류 메시지는 Windows EPANET 의 것과 동일하며 부록 Error Messages 에 나열되어 있다.

## 입력 파일 형식 (Input File Format)

커맨드라인 EPANET 의 입력 파일은 Windows EPANET 이 **File >> Export >> Network** 명령으로 생성하는 텍스트 파일과 동일한 형식을 가진다. 입력 파일은 섹션(section) 단위로 구성되며, 각 섹션은 대괄호로 묶인 키워드로 시작한다. 다양한 키워드는 아래 Table 3 에 나열되어 있다.

| *Network* *Components* | *System* *Operation* | *Water* *Quality* | *Options* | *Network* *Map/Tags* |
| --- | --- | --- | --- | --- |
| [TITLE] [JUNCTIONS] [RESERVOIRS] [TANKS] [PIPES] [PUMPS] [VALVES] [EMITTERS] | [CURVES] [PATTERNS] [ENERGY] [STATUS] [CONTROLS] [RULES] [DEMANDS] | [QUALITY] [REACTIONS] [SOURCES] [MIXING] | [OPTIONS] [TIMES] [REPORT] | [COORDINATES] [VERTICES] [LABELS] [BACKDROP] [TAGS] |

섹션의 순서는 중요하지 않다. 그러나 어떤 섹션에서 노드나 링크가 참조될 때에는 그 노드/링크가 이미 [JUNCTIONS], [RESERVOIRS], [TANKS], [PIPES], [PUMPS], [VALVES] 섹션에서 정의되어 있어야 한다. 따라서 이 섹션들은 [TITLE] 섹션 바로 다음에 맨 앞에 배치하는 것을 권장한다. 관망 지도(network map) 및 태그(tags) 섹션은 커맨드라인 EPANET 에서는 사용되지 않으며 파일에서 제거할 수 있다.

각 섹션은 한 줄 이상의 데이터를 포함할 수 있다. 빈 줄은 파일 어디에나 나타날 수 있으며, 세미콜론(;)은 그 뒤에 오는 내용이 데이터가 아니라 주석(comment)임을 나타내는 데 사용할 수 있다. 한 줄에는 최대 255자가 나타날 수 있다. 노드, 링크, 곡선, 시간패턴을 식별하는 데 사용되는 ID 라벨은 최대 31개의 문자와 숫자의 조합일 수 있다.

Listing 1 은 [Quick Start Tutorial](https://usepa.github.io/EPANET2.2/2_quickstart.html#quickstart) 장에서 논의된 튜토리얼 관망을 나타내는 입력 파일을 보여준다.

Listing 1 EPANET 입력 파일 예제.

```
[TITLE]
EPANET TUTORIAL

[JUNCTIONS]
;ID   Elev   Demand
;------------------
2     0      0
3     710    650
4     700    150
5     695    200
6     700    150

[RESERVOIRS]
;ID   Head
;---------
1     700

[TANKS]
;ID  Elev  InitLvl  MinLvl  MaxLvl  Diam  Volume
;-----------------------------------------------
7    850   5        0       15      70    0

[PIPES]
;ID  Node1  Node2  Length  Diam  Roughness
;-----------------------------------------
1    2      3      3000    12    100
2    3      6      5000    12    100
3    3      4      5000    8     100
4    4      5      5000    8     100
5    5      6      5000    8     100
6    6      7      7000    10    100

[PUMPS]
;ID  Node1  Node2  Parameters
;---------------------------------
7    1      2      HEAD  1

[PATTERNS]
;ID   Multipliers
;-----------------------
1       0.5  1.3  1  1.2

[CURVES]
;ID  X-Value  Y-Value
;--------------------
1    1000     200

[QUALITY]
;Node InitQual
;-------------
1     1

[REACTIONS]
Global Bulk -1
Global Wall 0

[TIMES]
Duration           24:00
Hydraulic Timestep 1:00
Quality Timestep   0:05
Pattern Timestep   6:00

[REPORT]
Page      55
Energy    Yes
Nodes     All
Links     All

[OPTIONS]
Units           GPM
Headloss        H-W
Pattern         1
Quality         Chlorine mg/L
Tolerance       0.01

[END]
```

이어지는 페이지에서는 각 키워드 섹션의 내용과 형식을 알파벳 순서로 설명한다.

### [BACKDROP]

**용도(Purpose):**

관망 지도의 배경 이미지(backdrop image)와 치수를 지정한다.

**형식(Format):**

| **DIMENSIONS** | *LLx LLy URx URy* |
| --- | --- |
| **UNITS** | **FEET/METERS/DEGREES/NONE** |
| **FILE** | *filename* |
| **OFFSET** | *X Y* |

**정의(Definitions):**

**DIMENSIONS** 는 지도의 경계 사각형(bounding rectangle)의 좌측 하단(lower-left) 및 우측 상단(upper-right) 모서리의 X, Y 좌표를 제공한다. 기본값은 [COORDINATES] 섹션에 제공된 노드 좌표의 범위(extents)이다.

**UNITS** 는 지도 치수가 주어지는 단위를 지정한다. 기본값은 NONE 이다.

**FILE** 은 배경 이미지를 담고 있는 파일의 이름이다.

**OFFSET** 은 배경 이미지의 좌측 상단(upper-left) 모서리가 지도 경계 사각형의 좌측 상단 모서리로부터 떨어진 X, Y 거리를 나열한다. 기본값은 오프셋 없음(zero offset)이다.

**비고(Remarks):**

1. [BACKDROP] 섹션은 선택(옵션)이며 EPANET 을 콘솔 애플리케이션으로 실행할 때는 전혀 사용되지 않는다.
2. 배경으로는 Windows Enhanced Metafile 과 비트맵(bitmap) 파일만 사용할 수 있다.

### [CONTROLS]

**용도(Purpose):**

단일 조건에 기반하여 링크를 수정하는 단순 제어(simple control)를 정의한다.

**형식(Format):**

각 제어마다 한 줄씩이며, 다음 형태 중 하나일 수 있다.

| LINK | *linkID* | *status* | IF | NODE | *nodeID* | ABOVE/BELOW | *value* |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LINK | *linkID* | *status* | AT | TIME | *time* |  |  |
| LINK | *linkID* | *status* | AT | CLOCKTIME | *time* | AM/PM |  |

여기서:

*linkID* = 링크 ID 라벨 *status* = OPEN 또는 CLOSED, 펌프 속도 설정값(pump speed setting), 또는 제어밸브 설정값(control valve setting) *nodeID* = 노드 ID 라벨 *value* = 절점에 대한 압력 또는 탱크에 대한 수위 *time* = 모의 시작 이후의 시간으로 십진 시간(decimal hours) 또는 hours:minutes 형식 *time* = 12시간제 시각(hours:minutes)

**비고(Remarks):**

1. 단순 제어는 탱크 수위, 절점 압력, 모의 경과 시간, 하루 중 시각에 기반하여 링크 상태나 설정값을 변경하는 데 사용된다.
2. 링크 상태와 설정값을 지정하는 규약, 특히 제어밸브에 대한 규약은 [STATUS] 섹션의 비고를 참조하라.

**예제(Examples):**

```
[CONTROLS]
;Close Link 12 if the level in Tank 23 exceeds 20 ft.
LINK 12 CLOSED IF NODE 23 ABOVE 20

;Open Link 12 if pressure at Node 130 is under 30 psi
LINK 12 OPEN IF NODE 130 BELOW 30

;Pump PUMP02's speed is set to 1.5 at 16 hours into
;the simulation
LINK PUMP02 1.5 AT TIME 16

;Link 12 is closed at 10 am and opened at 8 pm
;throughout the simulation
LINK 12 CLOSED AT CLOCKTIME 10 AM
LINK 12 OPEN AT CLOCKTIME 8 PM
```

### [COORDINATES]

**용도(Purpose):**

관망 노드에 지도 좌표를 할당한다.

**형식(Format):**

각 노드마다 한 줄씩 다음을 포함한다.

- Node ID label
- X-coordinate
- Y-coordinate

**비고(Remarks):**

1. 지도에 표시되는 각 노드마다 한 줄씩 포함한다.
2. 좌표는 지도 좌측 하단의 임의의 원점(origin)으로부터 노드까지의 거리를 나타낸다. 이 거리에는 편리한 측정 단위를 무엇이든 사용할 수 있다.
3. 모든 노드를 지도에 포함할 필요는 없으며, 그 위치가 실제 축척(scale)에 맞을 필요도 없다.
4. [COORDINATES] 섹션은 선택(옵션)이며 EPANET 을 콘솔 애플리케이션으로 실행할 때는 전혀 사용되지 않는다.

**예제(Example):**

```
[COORDINATES]
;Node     X-Coord.     Y-Coord
;-------------------------------
  1       10023        128
  2       10056        95
```

### [CURVES]

**용도(Purpose):**

데이터 곡선과 그 X,Y 점들을 정의한다.

**형식(Format):**

각 곡선의 각 X,Y 점마다 한 줄씩 다음을 포함한다.

- Curve ID label
- X value
- Y value

**비고(Remarks):**

1. 곡선은 다음 관계를 나타내는 데 사용할 수 있다.
  - 펌프의 Head v. Flow(수두 대 유량)
  - 펌프의 Efficiency v. Flow(효율 대 유량)
  - 탱크의 Volume v. Depth(체적 대 수심)
  - 범용밸브(General Purpose Valve)의 Headloss v. Flow(수두손실 대 유량)
2. 곡선의 점들은 X 값이 증가하는 순서(낮은 값에서 높은 값으로)로 입력해야 한다.
3. 입력 파일을 Windows 버전 EPANET 에서 사용할 경우, 곡선의 첫 항목 바로 위에 곡선 유형(curve type)과 설명을 콜론으로 구분한 주석을 추가하면 이 항목들이 EPANET 의 Curve Editor 에 올바르게 표시된다. 곡선 유형에는 PUMP, EFFICIENCY, VOLUME, HEADLOSS 가 있다. 아래 예제를 참조하라.

**예제(Example):**

```
[CURVES]
;ID   Flow    Head
;PUMP: Curve for Pump 1 C1 0 200
C1    1000    100
C1    3000    0

;ID   Flow    Effic.
;EFFICIENCY:
E1    200     50
E1    1000    85
E1    2000    75
E1    3000    65
```

### [DEMANDS]

**용도(Purpose):**

절점 노드에서 다중 수요량(multiple water demands)을 정의하기 위한 [JUNCTIONS] 섹션의 보충 섹션이다.

**형식(Format):**

절점에서의 각 수요량 범주(category)마다 한 줄씩 다음을 포함한다.

- Junction ID label
- Base demand (flow units)
- Demand pattern ID (optional)
- 세미콜론을 앞에 붙인 수요량 범주명(Name of demand category) (optional)

**비고(Remarks):**

1. [JUNCTIONS] 섹션의 항목에서 수요량을 변경하거나 보충해야 하는 절점에 대해서만 사용한다.
2. 이 섹션의 데이터는 동일한 절점에 대해 [JUNCTIONS] 섹션에 입력된 수요량을 대체한다.
3. 절점당 무제한 개수의 수요량 범주를 입력할 수 있다.
4. 수요량 시간패턴(demand pattern)이 제공되지 않으면 절점 수요량은 [OPTIONS] 섹션에 지정된 Default Demand Pattern 을 따르며, 기본 패턴이 지정되지 않은 경우 Pattern 1 을 따른다. 기본 패턴(또는 Pattern 1)이 존재하지 않으면 수요량은 일정하게 유지된다.

**예제(Example):**

```
[DEMANDS]
;ID    Demand   Pattern   Category
;---------------------------------
J1     100      101       ;Domestic
J1     25       102       ;School
J256   50       101       ;Domestic
```

### [EMITTERS]

**용도(Purpose):**

이미터(emitter, 스프링클러 또는 오리피스)로 모델링되는 절점을 정의한다.

**형식(Format):**

각 이미터마다 한 줄씩 다음을 포함한다.

- Junction ID label
- 유량 계수(Flow coefficient), 1 psi(1 meter) 압력 강하 시의 유량 단위

**비고(Remarks):**

1. 이미터는 스프링클러 헤드를 통한 유출이나 관 누수(pipe leak)를 모델링하는 데 사용된다.
2. 이미터로부터의 유출량은 유량 계수와 절점 압력을 어떤 지수로 거듭제곱한 값의 곱과 같다.
3. 지수는 [OPTIONS] 섹션의 EMITTER EXPONENT 옵션으로 지정할 수 있다. 기본 지수는 0.5 이며, 이는 보통 스프링클러와 노즐에 적용된다.
4. 프로그램 결과로 보고되는 실제 수요량(actual demand)에는 절점의 정상 수요량과 이미터를 통한 유출량이 모두 포함된다.
5. [EMITTERS] 섹션은 선택(옵션)이다.

### [ENERGY]

**용도(Purpose):**

펌프 에너지 및 비용 계산에 사용되는 파라미터를 정의한다.

**형식(Format):**

| **GLOBAL** |  | **PRICE/PATTERN/EFFIC** | *value* |
| --- | --- | --- | --- |
| **PUMP** | *PumpID* | **PRICE/PATTERN/EFFIC** | *value* |
| **DEMAND** | **CHARGE** | *value* |  |

**비고(Remarks):**

1. 키워드 **GLOBAL** 로 시작하는 줄은 모든 펌프에 대한 에너지 가격(energy price), 가격 패턴(price pattern), 펌핑 효율(pumping efficiency)의 전역 기본값을 설정하는 데 사용된다.
2. 키워드 **PUMP** 로 시작하는 줄은 특정 펌프에 대해 전역 기본값을 재정의하는 데 사용된다.
3. 파라미터는 다음과 같이 정의된다.
  - **PRICE** = kW-시간당 평균 비용,
  - **PATTERN** = 에너지 가격이 시간에 따라 어떻게 변하는지를 기술하는 시간패턴의 ID 라벨,
  - **EFFIC** = 전역 설정의 경우 단일 퍼센트 효율(percent efficiency), 특정 펌프의 경우 효율 곡선(efficiency curve)의 ID 라벨,
  - **DEMAND CHARGE** = 모의 기간 중 최대 kW 사용량에 대해 추가되는 비용.
4. 기본 전역 펌프 효율은 75% 이고 기본 전역 에너지 가격은 0 이다.
5. 이 섹션의 모든 항목은 선택(옵션)이다. 슬래시(/)로 구분된 항목은 허용되는 선택지를 나타낸다.

**예제(Example):**

```
[ENERGY]
GLOBAL  PRICE      0.05   ;Sets global energy price
GLOBAL  PATTERN    PAT1   ;and time-of-day pattern
PUMP    23 PRICE   0.10   ;Overrides price for Pump 23
PUMP    23 EFFIC   E23    ;Assigns effic. curve to Pump 23
```

### [JUNCTIONS]

**용도(Purpose):**

관망에 포함된 절점 노드(junction nodes)를 정의한다.

**형식(Format):**

각 절점마다 한 줄씩 다음을 포함한다.

- ID label
- Elevation, ft (m)
- Base demand flow (flow units) (optional)
- Demand pattern ID (optional)

**비고(Remarks):**

1. 최소한 하나의 절점을 가진 [JUNCTIONS] 섹션이 필수이다.
2. 수요량 시간패턴이 제공되지 않으면 절점 수요량은 [OPTIONS] 섹션에 지정된 Default Demand Pattern 을 따르며, 기본 패턴이 지정되지 않은 경우 Pattern 1 을 따른다. 기본 패턴(또는 Pattern 1)이 존재하지 않으면 수요량은 일정하게 유지된다.
3. 수요량은 [DEMANDS] 섹션에서도 입력할 수 있으며, 절점당 다중 수요량 범주를 포함할 수 있다.

**예제(Example):**

```
[JUNCTIONS]
;ID    Elev.   Demand   Pattern
;------------------------------
J1     100     50       Pat1
J2     120     10              ;Uses default demand pattern
J3     115                     ;No demand at this junction
```

### [LABELS]

**용도(Purpose):**

지도 라벨(map labels)에 좌표를 할당한다.

**형식(Format):**

각 라벨마다 한 줄씩 다음을 포함한다.

- X-coordinate
- Y-coordinate
- 큰따옴표로 묶인 라벨의 텍스트(Text of label in double quotes)
- 앵커 노드(anchor node)의 ID 라벨 (optional)

**비고(Remarks):**

1. 지도의 각 라벨마다 한 줄씩 포함한다.
2. 좌표는 라벨의 좌측 상단 모서리를 가리키며 지도 좌측 하단의 임의의 원점을 기준으로 한다.
3. 선택적 앵커 노드는 줌인(zoom-in) 작업 중 지도가 재축척(re-scale)될 때 라벨을 해당 노드에 고정한다.
4. [LABELS] 섹션은 선택(옵션)이며 EPANET 을 콘솔 애플리케이션으로 실행할 때는 전혀 사용되지 않는다.

**예제(Example):**

```
[LABELS]
;X-Coord.    Y-Coord.    Label            Anchor
;-----------------------------------------------
1230         3459        “Pump 1”
34.57        12.75       “North Tank”     T22
```

### [MIXING]

**용도(Purpose):**

저장 탱크 내부의 혼합(mixing)을 지배하는 모델을 지정한다.

**형식(Format):**

탱크마다 한 줄씩 다음을 포함한다.

- Tank ID label
- 혼합 모델(Mixing model) (MIXED, 2COMP, FIFO, 또는 LIFO)
- 구획 체적(Compartment volume) (fraction)

**비고(Remarks):**

1. 혼합 모델에는 다음이 있다.
  - 완전 혼합(Completely Mixed) (MIXED)
  - 2구획 혼합(Two-Compartment Mixing) (2COMP)
  - 압출 흐름(Plug Flow) (FIFO)
  - 적층 압출 흐름(Stacked Plug Flow) (LIFO)

b. 구획 체적(compartment volume) 파라미터는 2구획 모델에만 적용되며, 전체 탱크 체적 중 유입/유출 구획(inlet/outlet compartment)에 할당되는 비율을 나타낸다.

c. [MIXING] 섹션은 선택(옵션)이다. 이 섹션에 기술되지 않은 탱크는 완전 혼합되는 것으로 가정한다.

**예제(Example):**

```
[MIXING]
;Tank       Model
;-----------------------
T12         LIFO
T23         2COMP    0.2
```

### [OPTIONS]

**용도(Purpose):**

다양한 모의 옵션(simulation options)을 정의한다.

**형식(Formats):**

| **UNITS** | **CFS/GPM/MGD/IMGD/AFD/** **LPS/LPM/MLD/CMH/CMD** |  |
| --- | --- | --- |
| **HEADLOSS** | **H-W/D-W/C-M** |  |
| **HYDRAULICS** | **USE/SAVE** | filename |
| **QUALITY** | **NONE/CHEMICAL/AGE/TRACE** | id |
| **VISCOSITY** | value |  |
| **DIFFUSIVITY** | value |  |
| **SPECIFIC GRAVITY** | value |  |
| **TRIALS** | value |  |
| **ACCURACY** | value |  |
| **HEADERROR** | value |  |
| **FLOWCHANGE** | value |  |
| **UNBALANCED** | **STOP/CONTINUE/CONTINUE** | n |
| **PATTERN** | id |  |
| **DEMAND MODEL** | **DDA/PDA** |  |
| **MINIMUM PRESSURE** | value |  |
| **REQUIRED PRESSURE** | value |  |
| **PRESSURE EXPONENT** | value |  |
| **DEMAND MULTIPLIER** | value |  |
| **EMITTER EXPONENT** | value |  |
| **TOLERANCE** | value |  |
| **MAP** | filename |  |

**정의(Definitions):**

**UNITS** 는 유량(flow rates)이 표현되는 단위를 설정하며, 다음과 같다.

**CFS** = cubic feet per second **GPM** = gallons per minute **MGD** = million gallons per day **IMGD** = Imperial MGD **AFD** = acre-feet per day **LPS** = liters per second **LPM** = liters per minute **MLD** = million liters per day **CMH** = cubic meters per hour **CMD** = cubic meters per day

**CFS, GPM, MGD, IMGD, AFD** 의 경우 다른 입력량들은 US Customary Units 로 표현된다. 유량 단위가 리터나 세제곱미터인 경우 다른 모든 입력량들도 Metric Units 를 사용해야 한다. (부록 A. 측정 단위 참조). 기본 유량 단위는 **GPM** 이다.

**HEADLOSS** 는 관을 통한 흐름의 수두손실을 계산하는 데 사용할 공식을 선택한다. 선택지는 Hazen-Williams (**H-W**), Darcy-Weisbach (**D-W**), 또는 Chezy-Manning (**C-M**) 공식이다. 기본값은 **H-W** 이다.

**HYDRAULICS** 옵션은 현재 수리 해(hydraulics solution)를 파일에 **SAVE**(저장)하거나, 이전에 저장된 수리 해를 **USE**(사용)할 수 있게 한다. 이는 수질 거동(water quality behavior)에만 영향을 미치는 요인들을 연구할 때 유용하다.

**QUALITY** 는 수행할 수질 해석(water quality analysis)의 유형을 선택한다. 선택지는 **NONE, CHEMICAL, AGE, TRACE** 이다. **CHEMICAL** 대신 실제 화학물질 이름을 그 농도 단위와 함께 사용할 수 있다(예: **CHLORINE mg/L**). **TRACE** 를 선택하면 추적할 노드의 ID 라벨이 뒤따라야 한다. 기본 선택은 **NONE**(수질 해석 없음)이다.

**VISCOSITY** 는 모델링 대상 유체의 동점성계수(kinematic viscosity)로, 20 deg. C 에서 물의 동점성계수(1.0 centistoke)에 대한 상대값이다. 기본값은 1.0 이다.

**DIFFUSIVITY** 는 해석 대상 화학물질의 분자 확산계수(molecular diffusivity)로, 물 속 염소(chlorine)의 확산계수에 대한 상대값이다. 기본값은 1.0 이다. 확산계수는 관 벽면 반응(pipe wall reaction)에서 물질전달 제한(mass transfer limitation)을 고려할 때만 사용된다. 값이 0 이면 EPANET 은 물질전달 제한을 무시한다.

**SPECIFIC GRAVITY** 는 모델링 대상 유체의 밀도와 4 deg. C 에서 물의 밀도의 비(unitless)이다.

**TRIALS** 는 모의의 각 수리 시간 간격(hydraulic time step)에서 관망 수리를 푸는 데 사용되는 최대 시도(trial) 횟수이다. 기본값은 200 이다.

**ACCURACY** 는 수리 해에 도달했는지를 판정하는 수렴 기준(convergence criterion)을 규정한다. 이전 해로부터의 모든 유량 변화의 합을 모든 링크의 총 유량으로 나눈 값이 이 수치보다 작아지면 시도가 종료된다. 기본값은 0.001 이다.

**HEADERROR** 는 **ACCURACY** 옵션을 보강한다. 수리 수렴(hydraulic convergence)이 이루어지기 위해 어떤 관망 링크가 가질 수 있는 최대 수두손실 오차(head loss error)를 설정한다. 링크의 수두손실 오차란 링크의 계산된 유량의 함수로 구한 수두손실(예: 관에 대한 Hazen-Williams 식)과 링크 양단 노드의 계산된 수두 차이 사이의 차이이다. 이 파라미터의 단위는 feet(US) 또는 meters(SI)이다. 기본값 0 은 수두 오차 제한이 적용되지 않음을 의미한다.

**FLOWCHANGE** 는 **ACCURACY** 옵션을 보강한다. 수리 수렴이 이루어지기 위해 어떤 관망 요소(링크, 이미터, 또는 압력 구동 수요량)가 가질 수 있는 최대 유량 변화(largest change in flow)를 설정한다. 이는 프로젝트가 사용하는 유량 단위로 지정된다. 기본값 0 은 유량 변화 제한이 적용되지 않음을 의미한다.

**UNBALANCED** 는 모의 중 어떤 수리 시간 간격에서 규정된 **TRIALS** 횟수 내에 수리 해에 도달할 수 없을 때 어떻게 처리할지를 결정한다. **“STOP”** 은 그 지점에서 전체 해석을 중단한다. **“CONTINUE”** 는 경고 메시지를 발생시키면서 해석을 계속한다. **“CONTINUE n”** 은 모든 링크의 상태를 현재 설정값으로 고정한 채 추가로 “n” 번의 시도 동안 해를 계속 탐색한다. 그 시점부터는 수렴 달성 여부에 대한 메시지를 발생시키면서 모의를 계속한다. 기본 선택은 **“STOP”** 이다.

**PATTERN** 은 수요량 시간패턴이 지정되지 않은 모든 절점에 적용될 기본 수요량 시간패턴(default demand pattern)의 ID 라벨을 제공한다. [PATTERNS] 섹션에 해당 패턴이 존재하지 않으면 기본적으로 그 패턴은 1.0 인 단일 곱수(multiplier)로 구성된다. 이 옵션을 사용하지 않으면 전역 기본 수요량 시간패턴의 라벨은 “1” 이다.

**DEMAND MULTIPLIER** 는 모든 절점과 모든 수요량 범주의 기준 수요량(baseline demand) 값을 조정하는 데 사용된다. 예를 들어 값이 2 이면 모든 기준 수요량을 두 배로, 0.5 이면 절반으로 만든다. 기본값은 1.0 이다.

**DEMAND MODEL** 은 절점 수요량 모델 — 수요량 구동 해석(Demand Driven Analysis, **DDA**) 또는 압력 구동 해석(Pressure Driven Analysis, **PDA**) — 을 결정한다. DDA 는 주어진 시점의 절점 수요량을 고정값 `D` 로 가정한다. 이는 때때로 음압(negative pressure, 물리적으로 불가능)을 갖는 수리 해를 초래한다. PDA 는 공급되는 수요량 `d` 를 절점 압력 `p` 의 함수로 다음과 같이 가정한다.

d=D[p−PminPreq−Pmin]Pexp

여기서 `D` 는 요구되는 전체 수요량, `Pmin` 은 그 아래에서 수요량이 0 이 되는 압력, `Preq` 는 요구되는 전체 수요량을 공급하기 위해 필요한 압력, `Pexp` 는 지수이다. 압력의 단위는 psi(US) 또는 meters(SI)이다. `p<Pmin` 일 때 수요량은 0 이고, `p>Preq` 일 때 수요량은 `D` 와 같다. 기본값은 **DDA** 이다.

**MINIMUM PRESSURE** 는 `Pmin` 값을 지정한다. 기본값은 0.0 이다.

**REQUIRED PRESSURE** 는 `Preq` 값을 지정한다. 기본값은 0.1 이다.

**PRESSURE EXPONENT** 는 `Pexp` 값을 지정한다. 기본값은 0.5 이다.

**EMITTER EXPONENT** 는 이미터로부터 나오는 유출량을 계산할 때 절점 압력을 거듭제곱하는 지수를 지정한다. 기본값은 0.5 이다.

**MAP** 는 관망의 지도를 그릴 수 있도록 관망 노드의 좌표를 담은 파일의 이름을 제공하는 데 사용된다. 수리나 수질 계산에는 사용되지 않는다.

**TOLERANCE** 는 한 물 덩어리(parcel of water)가 본질적으로 다른 물 덩어리와 같다고 말할 수 있는 수질 수준의 차이값이다. 기본값은 모든 유형의 수질 해석(화학물질, 물나이(age, 시간 단위), 또는 공급원 추적(source tracing, 퍼센트 단위))에 대해 0.01 이다.

**비고(Remarks):**

1. 이 섹션에서 명시적으로 지정되지 않은 모든 옵션은 기본값을 가정한다.
2. 슬래시(/)로 구분된 항목은 허용되는 선택지를 나타낸다.

**예제(Example):**

```
[OPTIONS]
UNITS        CFS
HEADLOSS     D-W
QUALITY      TRACE   Tank23
UNBALANCED   CONTINUE   10
```

### [PATTERNS]

**용도(Purpose):**

시간패턴(time patterns)을 정의한다.

**형식(Format):**

각 패턴마다 한 줄 이상으로 다음을 포함한다.

- Pattern ID label
- 하나 이상의 곱수(One or more multipliers)

**비고(Remarks):**

곱수(multiplier)는 각 시간 주기에 대해 어떤 기준량(예: 수요량)이 어떻게 조정되는지를 정의한다.

1. 모든 패턴은 [TIMES] 섹션에 정의된 동일한 시간 주기 간격(time period interval)을 공유한다.
2. 각 패턴은 서로 다른 개수의 시간 주기를 가질 수 있다.
3. 모의 시간이 패턴 길이를 초과하면 패턴은 첫 주기로 되돌아간다(wrap around).
4. 각 패턴의 모든 곱수를 포함하는 데 필요한 만큼 여러 줄을 사용한다.

**예제(Example):**

```
[PATTERNS]
;Pattern P1
P1    1.1    1.4    0.9    0.7
P1    0.6    0.5    0.8    1.0
;Pattern P2
P2    1      1      1      1
P2    0      0      1
```

### [PIPES]

**용도(Purpose):**

관망에 포함된 모든 관 링크(pipe links)를 정의한다.

**형식(Format):**

각 관마다 한 줄씩 다음을 포함한다.

- ID label of pipe
- ID of start node
- ID of end node
- Length, ft (m)
- Diameter, inches (mm)
- Roughness coefficient
- Minor loss coefficient
- Status (OPEN, CLOSED, or CV)

**비고(Remarks):**

1. 조도 계수(Roughness coefficient)는 Hazen-Williams 및 Chezy-Manning 수두손실 공식에서는 무차원(unitless)이며, Darcy-Weisbach 공식에서는 millifeet(mm) 단위를 가진다. 수두손실 공식의 선택은 [OPTIONS] 섹션에서 제공된다.
2. Status 를 CV 로 설정하면 관에 흐름을 한 방향으로만 제한하는 체크밸브(check valve)가 포함됨을 의미한다.
3. Minor loss coefficient 가 0 이고 관이 OPEN 이면, 이 두 항목은 입력 줄에서 생략할 수 있다.

**예제(Example):**

```
[PIPES]
;ID   Node1  Node2   Length   Diam.   Roughness  Mloss   Status
;-------------------------------------------------------------
 P1    J1     J2     1200      12       120       0.2    OPEN
 P2    J3     J2      600       6       110       0      CV
 P3    J1     J10    1000      12       120
```

### [PUMPS]

**용도(Purpose):**

관망에 포함된 모든 펌프 링크(pump links)를 정의한다.

**형식(Format):**

각 펌프마다 한 줄씩 다음을 포함한다.

- ID label of pump
- ID of start node
- ID of end node
- 키워드와 값(Keyword and Value) (반복 가능)

**비고(Remarks):**

1. 키워드는 다음으로 구성된다.   **POWER** – 정출력 펌프(constant energy pump)의 출력 값, hp (kW) **HEAD** - 펌프의 수두 대 유량(head versus flow)을 기술하는 곡선의 ID **SPEED** - 상대 속도 설정값(relative speed setting, 정상 속도는 1.0, 0 은 펌프 정지를 의미) **PATTERN** - 속도 설정값이 시간에 따라 어떻게 변하는지를 기술하는 시간패턴의 ID
2. 각 펌프에는 **POWER** 또는 **HEAD** 중 하나가 반드시 제공되어야 한다. 나머지 키워드는 선택(옵션)이다.

**예제(Example):**

```
[PUMPS]
;ID    Node1    Node2    Properties
;---------------------------------------------
Pump1   N12      N32     HEAD Curve1
Pump2   N121     N55     HEAD Curve1  SPEED 1.2
Pump3   N22      N23     POWER 100
```

### [QUALITY]

**용도(Purpose):**

노드에서의 초기 수질(initial water quality)을 정의한다.

**형식(Format):**

노드마다 한 줄씩 다음을 포함한다.

- Node ID label
- Initial quality

**비고(Remarks):**

1. 나열되지 않은 노드의 수질은 0 으로 가정한다.
2. Quality 는 화학물질의 경우 농도(concentration), 물나이(water age)의 경우 시간(hours), 공급원 추적(source tracing)의 경우 퍼센트(percent)를 나타낸다.
3. [QUALITY] 섹션은 선택(옵션)이다.

### [REACTIONS]

**용도(Purpose):**

관망에서 발생하는 화학 반응(chemical reactions)과 관련된 파라미터를 정의한다.

**형식(Format):**

| **ORDER** | **BULK/WALL/TANK** | value |
| --- | --- | --- |
| **GLOBAL** | **BULK/WALL** | value |
| **BULK/WALL/TANK** | pipeID | value |
| **LIMITING POTENTIAL** | value |  |
| **ROUGHNESS CORRELATION** | value |  |

**정의(Definitions):**

**ORDER** 는 각각 벌크 유체(bulk fluid), 관 벽면(pipe wall), 탱크(tank)에서 발생하는 반응의 차수(order)를 설정하는 데 사용된다. 벽면 반응(wall reaction)의 값은 0 또는 1 이어야 한다. 제공되지 않으면 기본 반응 차수는 1.0 이다.

**GLOBAL** 은 모든 벌크 반응 계수(bulk reaction coefficient, 관과 탱크) 또는 모든 관 벽면 계수(pipe wall coefficient)에 대한 전역 값을 설정하는 데 사용된다. 기본값은 0 이다.

**BULK**, **WALL**, **TANK** 는 특정 관과 탱크에 대해 전역 반응 계수를 재정의하는 데 사용된다.

**LIMITING POTENTIAL** 은 반응 속도(reaction rate)가 현재 농도와 어떤 한계 잠재값(limiting potential value)의 차이에 비례하도록 지정한다.

**ROUGHNESS CORRELATION** 은 모든 기본 관 벽면 반응 계수가 다음과 같은 방식으로 관 조도(pipe roughness)와 관련되도록 한다.

| Head Loss Equation | Roughness Correlation |
| --- | --- |
| Hazen-Williams | `F/C` |
| Darcy-Weisbach | `F/log(e/D)` |
| Chezy-Manning | `F∗n` |

여기서 `F` = 조도 상관값(roughness correlation), `C` = Hazen-Williams C-factor, `e` = Darcy-Weisbach 조도, `D` = 관 직경, `n` = Chezy-Manning 조도 계수이다. 이렇게 계산된 기본값은 **WALL** 형식을 사용하여 해당 관에 특정 값을 제공함으로써 어떤 관에 대해서도 재정의할 수 있다.

**비고(Remarks):**

1. 성장 반응 계수(growth reaction coefficient)에는 양수를, 감쇠 계수(decay coefficient)에는 음수를 사용하는 것을 기억하라.
2. 모든 반응 계수의 시간 단위는 1/days 이다.
3. 이 섹션의 모든 항목은 선택(옵션)이다. 슬래시(/)로 구분된 항목은 허용되는 선택지를 나타낸다.

**예제(Example):**

```
[REACTIONS]
ORDER WALL    0    ;Wall reactions are zero-order
GLOBAL BULK  -0.5  ;Global bulk decay coeff.
GLOBAL WALL  -1.0  ;Global wall decay coeff.
WALL   P220  -0.5  ;Pipe-specific wall coeffs.
WALL   P244  -0.7
```

### [REPORT]

**용도(Purpose):**

모의로부터 생성되는 출력 보고서(output report)의 내용을 기술한다.

**형식(Format):**

| **PAGESIZE** | value |  |
| --- | --- | --- |
| **FILE** | filename |  |
| **STATUS** | **YES/NO/FULL** |  |
| **SUMMARY** | **YES/NO** |  |
| **ENERGY** | **YES/NO** |  |
| **NODES** | **NONE/ALL/**/node1 node2 … |  |
| **LINKS** | **NONE/ALL/**/link1 link2 … |  |
| parameter | **YES/NO** |  |
| parameter | **BELOW/ABOVE/PRECISION** | value |

**정의(Definitions):**

**PAGESIZE** 는 출력 보고서의 페이지당 기록되는 줄 수를 설정한다. 기본값은 0 으로, 페이지당 줄 수 제한이 적용되지 않음을 의미한다.

**FILE** 은 출력 보고서를 기록할 파일의 이름을 제공한다(Windows 버전 EPANET 에서는 무시됨).

**STATUS** 는 수리 상태 보고서(hydraulic status report)를 생성할지 여부를 결정한다. **YES** 를 선택하면 보고서는 모의의 각 시간 간격마다 상태가 변하는 모든 관망 구성요소를 식별한다. **FULL** 을 선택하면 상태 보고서에는 각 수리 해석의 각 시도(trial) 정보까지 포함된다. 이 수준의 상세 정보는 수리적으로 불균형(unbalanced)이 되는 관망을 디버깅할 때만 유용하다. 기본값은 **NO** 이다.

**SUMMARY** 는 관망 구성요소 수와 주요 해석 옵션에 대한 요약 표(summary table)를 생성할지 여부를 결정한다. 기본값은 **YES** 이다.

**ENERGY** 는 각 펌프의 평균 에너지 사용량과 비용을 보고하는 표를 제공할지 여부를 결정한다. 기본값은 NO 이다.

**NODES** 는 어느 노드를 보고할지를 식별한다. 개별 노드 ID 라벨을 나열하거나 키워드 **NONE** 또는 **ALL** 을 사용할 수 있다. 목록을 이어가기 위해 추가 **NODES** 줄을 사용할 수 있다. 기본값은 **NONE** 이다.

**LINKS** 는 어느 링크를 보고할지를 식별한다. 개별 링크 ID 라벨을 나열하거나 키워드 **NONE** 또는 **ALL** 을 사용할 수 있다. 목록을 이어가기 위해 추가 **LINKS** 줄을 사용할 수 있다. 기본값은 **NONE** 이다.

“parameter” 보고 옵션은 어떤 수량을 보고할지, 소수점 자리수를 몇 개 표시할지, 출력 보고를 제한하기 위해 어떤 종류의 필터링을 사용할지를 식별하는 데 사용된다. 보고할 수 있는 노드 파라미터에는 다음이 포함된다.

- **Elevation**
- **Demand**
- **Head**
- **Pressure**
- **Quality.**

링크 파라미터에는 다음이 포함된다.

- **Length**
- **Diameter**
- **Flow**
- **Velocity**
- **Headloss**
- **Position** (status 와 동일 – open, active, closed)
- **Setting** (관의 경우 Roughness, 펌프의 경우 speed, 밸브의 경우 pressure/flow setting)
- **Reaction** (반응 속도, reaction rate)
- **F-Factor** (마찰계수, friction factor).

기본으로 보고되는 수량은 노드의 경우 **Demand, Head, Pressure, Quality** 이고 링크의 경우 **Flow, Velocity, Headloss** 이다. 기본 정밀도(precision)는 소수점 둘째 자리이다.

**비고(Remarks):**

1. 이 섹션에서 명시적으로 지정되지 않은 모든 옵션은 기본값을 가정한다.
2. 슬래시(/)로 구분된 항목은 허용되는 선택지를 나타낸다.
3. 기본값은 어떤 노드나 링크도 보고하지 않는 것이므로, 이 항목들의 결과를 보고하려면 **NODES** 또는 **LINKS** 옵션을 제공해야 한다.
4. Windows 버전 EPANET 에서는 [REPORT] 옵션 중 **STATUS** 만 인식되며, 나머지는 모두 무시된다.

**예제(Example):**

다음 예제는 노드 N1, N2, N3, N17 과 속도가 3.0 을 초과하는 모든 링크를 보고한다. 노드에는 표준 노드 파라미터(Demand, Head, Pressure, Quality)가 보고되고, 링크에는 Flow, Velocity, F-Factor(마찰계수)만 표시된다.

```
[REPORT]
NODES N1 N2 N3 N17
LINKS ALL
FLOW YES
VELOCITY PRECISION 4
F-FACTOR PRECISION 4
VELOCITY ABOVE 3.0
```

### [RESERVOIRS]

**용도(Purpose):**

관망에 포함된 모든 저수지 노드(reservoir nodes)를 정의한다.

**형식(Format):**

각 저수지마다 한 줄씩 다음을 포함한다.

- ID label
- Head, ft (m)
- Head pattern ID (optional)

**비고(Remarks):**

1. Head 는 저수지 내 물의 수리 수두(hydraulic head, 표고 + 압력 수두)이다.
2. 수두 패턴(head pattern)을 사용하여 저수지 수두가 시간에 따라 변하도록 할 수 있다.
3. 관망에는 최소한 하나의 저수지 또는 탱크가 포함되어야 한다.

**예제(Example):**

```
[RESERVOIRS]
;ID    Head    Pattern
;---------------------
R1     512               ;Head stays constant
R2     120     Pat1      ;Head varies with time
```

### [RULES]

**용도(Purpose):**

조건들의 조합에 기반하여 링크를 수정하는 규칙 기반 제어(rule-based controls)를 정의한다.

**형식(Format):**

각 규칙은 다음 형태의 일련의 구문이다.

| **RULE** | ruleID |
| --- | --- |
| **IF** | condition_1 |
| **AND** | condition_2 |
| **OR** | condition_3 |
| **AND** | condition_4 |
| etc. |  |
| **THEN** | action_1 |
| **AND** | action_2 |
| etc. |  |
| **ELSE** | action_3 |
| **AND** | action_4 |
| etc. |  |
| **PRIORITY** | value |

여기서: ruleID = 규칙에 할당된 ID 라벨 conditon_n = 조건 절(condition clause) action_n = 행동 절(action clause) Priority = 우선순위 값(예: 1 에서 5 사이의 숫자)

**조건 절 형식(Condition Clause Format):**

규칙 기반 제어의 조건 절은 다음 형태를 취한다.

| object | id | attribute | relation | value |
| --- | --- | --- | --- | --- |

여기서: object = 관망 객체의 범주(category) id = 객체의 ID 라벨 attribute = 객체의 속성(attribute or property) relation = 관계 연산자(relational operator) value = 속성 값(attribute value)

조건 절의 몇 가지 예는 다음과 같다.

```
JUNCTION 23 PRESSURE > 20
TANK T200 FILLTIME BELOW 3.5
LINK 44 STATUS IS OPEN
SYSTEM DEMAND >= 1500
SYSTEM CLOCKTIME = 7:30 AM
```

Object 키워드는 다음 중 어느 것이든 될 수 있다.

| **NODE** | **LINK** | **SYSTEM** |
| --- | --- | --- |
| **JUNCTION** | **PIPE** |  |
| **RESERVOIR** | **PUMP** |  |
| **TANK** | **VALVE** |  |

조건에서 **SYSTEM** 이 사용될 때는 ID 를 제공하지 않는다.

Node 유형 객체에는 다음 속성을 사용할 수 있다.

- **DEMAND**
- **HEAD**
- **PRESSURE**

Tank 에는 다음 속성을 사용할 수 있다.

- **LEVEL**
- **FILLTIME** (탱크를 채우는 데 필요한 시간)
- **DRAINTIME** (탱크를 비우는 데 필요한 시간)

Link 유형 객체에는 다음 속성을 사용할 수 있다.

- **FLOW**
- **STATUS** (**OPEN**, **CLOSED**, 또는 **ACTIVE**)
- **SETTING** (펌프 속도 또는 밸브 설정값)

**SYSTEM** 객체는 다음 속성을 사용할 수 있다.

- **DEMAND** (전체 시스템 수요량)
- **TIME** (모의 시작으로부터의 시간으로, 십진수 또는 hours:minutes 형식으로 표현)
- **CLOCKTIME** (**AM** 또는 **PM** 이 붙은 24시간제 시각)

관계 연산자는 다음으로 구성된다.

| **=** | **IS** |
| --- | --- |
| **<>** | **NOT** |
| **<** | **BELOW** |
| **>** | **ABOVE** |
| **<=** | **>=** |

**행동 절 형식(Action Clause Format):**

규칙 기반 제어의 행동 절은 다음 형태를 취한다.

| object | id | STATUS/SETTING | IS | value |
| --- | --- | --- | --- | --- |

여기서:

object = LINK, PIPE, PUMP, 또는 VALVE 키워드 id = 객체의 ID 라벨 value = 상태 조건(OPEN 또는 CLOSED), 펌프 속도 설정값, 또는 밸브 설정값

행동 절의 몇 가지 예는 다음과 같다.

```
LINK 23 STATUS IS CLOSED
PUMP P100 SETTING IS 1.5
VALVE 123 SETTING IS 90
```

**비고(Remarks):**

1. 규칙에서 **RULE**, **IF**, **THEN** 부분만 필수이며, 나머지 부분은 선택(옵션)이다.
2. **AND** 와 **OR** 절을 혼용할 때 **OR** 연산자가 **AND** 보다 높은 우선순위를 가진다. 즉, IF A or B and C   는 IF (A or B) and C   와 동등하다. 만약 의도한 해석이 IF A or (B and C)   라면, 이는 다음과 같이 두 개의 규칙으로 표현할 수 있다: IF A THEN ... IF B and C THEN ...
3. **PRIORITY** 값은 둘 이상의 규칙이 한 링크에 대해 상충하는 행동을 요구할 때 어느 규칙을 적용할지 결정하는 데 사용된다. 우선순위 값이 없는 규칙은 항상 우선순위 값이 있는 규칙보다 낮은 우선순위를 가진다. 동일한 우선순위 값을 가진 두 규칙의 경우, 먼저 나타나는 규칙이 더 높은 우선순위를 가진다.

**예제(Example):**

```
[RULES]
RULE 1
IF TANK 1 LEVEL ABOVE 19.1
THEN PUMP 335 STATUS IS CLOSED
AND PIPE 330 STATUS IS OPEN

RULE 2
IF SYSTEM CLOCKTIME >= 8 AM
AND SYSTEM CLOCKTIME < 6 PM
AND TANK 1 LEVEL BELOW 12
THEN PUMP 335 STATUS IS OPEN

RULE 3
IF SYSTEM CLOCKTIME >= 6 PM
OR SYSTEM CLOCKTIME < 8 AM
AND TANK 1 LEVEL BELOW 14
THEN PUMP 335 STATUS IS OPEN
```

### [SOURCES]

**용도(Purpose):**

수질 공급원(water quality sources)의 위치를 정의한다.

**형식(Format):**

각 수질 공급원마다 한 줄씩 다음을 포함한다.

- Node ID label
- 공급원 유형(Source type) (**CONCEN, MASS, FLOWPACED**, 또는 **SETPOINT**)
- 기준 공급원 강도(Baseline source strength)
- Time pattern ID (optional)

**비고(Remarks):**

1. **MASS** 유형 공급원의 경우 강도(strength)는 분당 질량 유량(mass flow per minute)으로 측정된다. 다른 모든 유형은 공급원 강도를 농도 단위(concentration units)로 측정한다.
2. 시간패턴을 지정하여 공급원 강도가 시간에 따라 변하도록 할 수 있다.
3. **CONCEN** 공급원은:   노드로 유입되는 임의의 외부 공급원 유입(external source inflow)의 농도를 나타낸다. 노드가 순(net) 음의 수요량을 가질 때(즉, 물이 그 노드에서 관망으로 유입될 때)만 적용된다. 노드가 절점이면, 보고되는 농도는 공급원 흐름과 관망 나머지 부분에서 유입되는 흐름의 혼합 결과이다. 노드가 저수지이면, 보고되는 농도는 공급원 농도이다. 노드가 탱크이면, 보고되는 농도는 탱크의 내부 농도이다. 공급 수원이나 정수처리장(treatment works)을 나타내는 노드(예: 저수지 또는 음의 수요량이 할당된 노드)에 사용하는 것이 가장 적합하다. 유입/유출이 동시에 일어나는 저장 탱크에는 사용해서는 안 된다.
4. **MASS, FLOWPACED**, 또는 **SETPOINT** 공급원은:   부스터 공급원(booster source)을 나타내며, 노드의 수요량과 무관하게 물질이 관망에 직접 주입된다. 노드에서 관망 나머지 부분으로 나가는 물에 다음과 같은 방식으로 영향을 미친다:  **MASS** 부스터는 노드 유입 흐름으로부터 발생한 것에 고정된 질량 유량을 추가한다. **FLOWPACED** 부스터는 노드의 결과 유입 농도에 고정된 농도를 추가한다. **SETPOINT** 부스터는 노드를 떠나는 임의의 흐름의 농도를 (유입으로부터 발생한 농도가 setpoint 아래인 한) 고정한다.   절점이나 저수지 부스터 공급원에서 보고되는 농도는 부스팅이 적용된 후 발생하는 농도이고, 부스터 공급원이 있는 탱크의 보고 농도는 탱크의 내부 농도이다. 관망에 추적자(tracer)나 소독제(disinfectant)를 직접 주입하는 것을 모델링하거나 오염물질 침투(contaminant intrusion)를 모델링하는 데 사용하는 것이 가장 적합하다.
5. 물나이(water age)나 공급원 추적(source tracing)을 모의할 때는 [SOURCES] 섹션이 필요 없다.

**예제(Example):**

```
[SOURCES]
;Node   Type   Strength  Pattern
;--------------------------------
  N1      CONCEN   1.2      Pat1    ;Concentration varies with time
  N44     MASS     12               ;Constant mass injection
```

### [STATUS]

**용도(Purpose):**

모의 시작 시점에 선택된 링크들의 초기 상태(initial status)를 정의한다.

**형식(Format):**

제어되는 링크마다 한 줄씩 다음을 포함한다.

- Link ID label
- Status or setting

**비고(Remarks):**

1. 이 섹션에 나열되지 않은 링크는 기본 상태로 **OPEN**(관과 펌프의 경우) 또는 **ACTIVE**(밸브의 경우)를 가진다.
2. status 값은 **OPEN** 또는 **CLOSED** 가 될 수 있다. 제어밸브(예: PRV, FCV 등)의 경우 이는 밸브가 완전히 열리거나 닫힌 상태이며, 제어 설정값에서 active 상태가 아님을 의미한다.
3. setting 값은 펌프의 속도 설정값(speed setting)이거나 밸브의 밸브 설정값(valve setting)일 수 있다.
4. 관의 초기 상태는 [PIPES] 섹션에서도 설정할 수 있다.
5. 체크밸브는 그 상태를 미리 설정할 수 없다.
6. 모의의 미래 어느 시점에 상태나 설정값을 변경하려면 [CONTROLS] 또는 [RULES] 를 사용하라.
7. **CLOSED** 또는 **OPEN** 상태의 제어밸브를 다시 **ACTIVE** 로 만들려면, 그것을 재활성화하는 제어나 규칙에서 그 압력 또는 유량 설정값을 지정해야 한다.

**예제(Example):**

```
[STATUS]
; Link   Status/Setting
;----------------------
  L22     CLOSED         ;Link L22 is closed
  P14     1.5            ;Speed for pump P14
  PRV1    OPEN           ;PRV1 forced open
                         ;(overrides normal operation)
```

### [TAGS]

**용도(Purpose):**

특정 노드 및 링크에 범주 라벨(category label, 태그)을 연결한다.

**형식(Format):**

태그가 있는 각 노드 및 링크마다 한 줄씩 다음을 포함한다.

- 키워드 NODE 또는 LINK
- 노드 또는 링크 ID 라벨
- 태그 라벨의 텍스트(공백 없음, with no spaces)

**비고(Remarks):**

1. 태그는 노드를 서로 다른 압력 구역(pressure zone)에 할당하거나 관을 재질(material)이나 연식(age)별로 분류하는 데 유용할 수 있다.
2. 어떤 노드나 링크의 태그가 이 섹션에서 식별되지 않으면 공백(blank)으로 가정한다.
3. [TAGS] 섹션은 선택(옵션)이며 수리나 수질 계산에 영향을 미치지 않는다.

**예제(Example):**

```
[TAGS]
;Object  ID       Tag
;------------------------------
 NODE    1001     Zone_A
 NODE    1002     Zone_A
 NODE    45       Zone_B
 LINK    201      UNCI-1960
 LINK    202      PVC-1985
```

### [TANKS]

**용도(Purpose):**

관망에 포함된 모든 탱크 노드(tank nodes)를 정의한다.

**형식(Format):**

각 탱크마다 한 줄씩 다음을 포함한다.

- ID label
- Bottom elevation, ft (m)
- Initial water level, ft (m)
- Minimum water level, ft (m)
- Maximum water level, ft (m)
- Nominal diameter, ft (m)
- Minimum volume, cubic ft (cubic meters)
- Volume curve ID (optional)

**비고(Remarks):**

1. 수면 표고(Water surface elevation)는 바닥 표고(bottom elevation)에 수위(water level)를 더한 값과 같다.
2. 비원통형 탱크(Non-cylindrical tank)는 [CURVES] 섹션에 수심 대 체적(volume versus water depth) 곡선을 지정하여 모델링할 수 있다.
3. 체적 곡선(volume curve)이 제공되면 직경 값은 0 이 아닌 임의의 수가 될 수 있다.
4. 최소 체적(Minimum volume, 최소 수위에서의 탱크 체적)은 원통형 탱크의 경우 또는 체적 곡선이 제공된 경우 0 이 될 수 있다.
5. 관망에는 최소한 하나의 탱크 또는 저수지가 포함되어야 한다.

**예제(Example):**

```
[TANKS]
;ID   Elev.  InitLvl  MinLvl  MaxLvl  Diam  MinVol  VolCurve
;-----------------------------------------------------------
;Cylindrical tank
T1    100     15       5       25     120    0
;Non-cylindrical tank with arbitrary diameter
T2    100     15       5       25      1     0      VC1
```

### [TIMES]

**용도(Purpose):**

모의에 사용되는 다양한 시간 간격 파라미터(time step parameters)를 정의한다.

**형식(Format):**

| **DURATION** | Value (units) |
| --- | --- |
| **HYDRAULIC TIMESTEP** | Value (units) |
| **QUALITY TIMESTEP** | Value (units) |
| **RULE TIMESTEP** | Value (units) |
| **PATTERN TIMESTEP** | Value (units) |
| **PATTERN START** | Value (units) |
| **REPORT TIMESTEP** | Value (units) |
| **REPORT START** | Value (units) |
| **START CLOCKTIME** | Value (**AM/PM**) |
| **STATISTIC** | **NONE/AVERAGED/MINIMUM/MAXIMUM/RANGE** |

**정의(Definitions):**

**DURATION** 은 모의의 지속 시간이다. 단일 시점 스냅샷 해석(single period snapshot analysis)을 실행하려면 0 을 사용한다. 기본값은 0 이다.

**HYDRAULIC TIMESTEP** 은 관망의 새로운 수리 상태(hydraulic state)를 얼마나 자주 계산할지를 결정한다. **PATTERN** 또는 **REPORT** 시간 간격보다 크면 자동으로 줄어든다. 기본값은 1 시간이다.

**QUALITY TIMESTEP** 은 관망 전체의 수질 변화를 추적하는 데 사용되는 시간 간격이다. 기본값은 수리 시간 간격(hydraulic time step)의 1/10 이다.

**RULE TIMESTEP** 은 수리 시간 간격 사이에 규칙 기반 제어의 활성화로 인한 시스템 상태 변화를 점검하는 데 사용되는 시간 간격이다. 기본값은 수리 시간 간격의 1/10 이다.

**PATTERN TIMESTEP** 은 모든 시간패턴의 시간 주기 사이의 간격이다. 기본값은 1 시간이다.

**PATTERN START** 는 모든 패턴이 시작되는 시간 오프셋(time offset)이다. 예를 들어 6 시간 값은 각 패턴이 6시에 해당하는 시간 주기에서 모의를 시작하도록 한다. 기본값은 0 이다.

**REPORT TIMESTEP** 은 출력 결과가 보고되는 시간 간격을 설정한다. 기본값은 1 시간이다.

**REPORT START** 는 출력 결과 보고가 시작되는, 모의 경과 시간의 길이이다. 기본값은 0 이다.

**START CLOCKTIME** 은 모의가 시작되는 하루 중 시각(예: 3:00 PM)이다. 기본값은 자정인 12:00 AM 이다.

**STATISTIC** 은 생성된 모의 결과 시계열(time series)에 대해 어떤 종류의 통계 후처리(statistical post-processing)를 수행할지를 결정한다. **AVERAGED** 는 시간 평균(time-averaged) 결과 집합을 보고하고, **MINIMUM** 은 최솟값만, **MAXIMUM** 은 최댓값만 보고하며, **RANGE** 는 최솟값과 최댓값의 차이를 보고한다. **NONE** 은 모든 노드와 링크의 모든 수량에 대한 전체 시계열을 보고하며 기본값이다.

**비고(Remarks):**

1. 단위는 **SECONDS (SEC), MINUTES (MIN), HOURS**, 또는 **DAYS** 가 될 수 있다. 기본값은 시간(hours)이다.
2. 단위가 제공되지 않으면 시간 값은 십진 시간(decimal hours) 또는 hours:minutes 표기로 입력할 수 있다.
3. [TIMES] 섹션의 모든 항목은 선택(옵션)이다. 슬래시(/)로 구분된 항목은 허용되는 선택지를 나타낸다.

**예제(Example):**

```
[TIMES]
DURATION           240 HOURS
QUALITY TIMESTEP   3 MIN
REPORT START       120
STATISTIC          AVERAGED
START CLOCKTIME    6:00 AM
```

### [TITLE]

**용도(Purpose):**

해석 대상 관망에 설명적인 제목(descriptive title)을 붙인다.

**형식(Format):**

임의의 수의 텍스트 줄.

**비고(Remarks):**

[TITLE] 섹션은 선택(옵션)이다.

### [VALVES]

**용도(Purpose):**

관망에 포함된 모든 제어밸브 링크(control valve links)를 정의한다.

**형식(Format):**

각 밸브마다 한 줄씩 다음을 포함한다.

- ID label of valve
- ID of start node
- ID of end node
- Diameter, inches (mm)
- Valve type
- Valve setting
- Minor loss coefficient

**비고(Remarks):**

1. 밸브 유형과 설정값에는 다음이 있다.

| Valve Type | Setting |
| --- | --- |
| PRV (pressure reducing valve) | Pressure, psi (m) |
| PSV (pressure sustaining valve) | Pressure, psi (m) |
| PBV (pressure breaker valve) | Pressure, psi (m) |
| FCV (flow control valve) | Flow (flow units) |
| TCV (throttle control valve) | Loss Coefficient |
| GPV (general purpose valve) | ID of head loss curve |

1. 차단밸브(Shutoff valve)와 체크밸브(check valve)는 별도의 제어밸브 구성요소가 아니라 관(pipe)의 일부로 간주된다([PIPES] 참조).

### [VERTICES]

**용도(Purpose):**

관망 링크에 내부 정점(interior vertex points)을 할당한다.

**형식(Format):**

그러한 점을 포함하는 각 링크의 각 점마다 한 줄씩 다음을 포함한다.

- Link ID label
- X-coordinate
- Y-coordinate

**비고(Remarks):**

1. 정점(Vertex point)은 링크를 양 끝 노드 사이의 단순 직선이 아니라 폴리라인(polyline)으로 그릴 수 있게 한다.
2. 좌표는 노드 및 라벨 좌표에 사용된 것과 동일한 좌표계를 가리킨다.
3. [VERTICES] 섹션은 선택(옵션)이며 EPANET 을 콘솔 애플리케이션으로 실행할 때는 전혀 사용되지 않는다.

**예제(Example):**

```
[VERTICES]
;Link      X-Coord.     Y-Coord
;-------------------------------
 1          10023       128
 2          10056       95
```

## 보고서 파일 형식 (Report File Format)

입력 파일의 [REPORT] 섹션에 제공된 구문은 EPANET 의 커맨드라인 실행으로 생성되는 보고서 파일(report file)의 내용을 제어한다. Listing 1 의 입력 파일로부터 생성된 보고서의 일부가 Listing 2 에 나와 있다. 일반적으로 보고서는 다음 섹션들을 포함할 수 있다.

- Status Section
- Energy Section
- Nodes Section
- Links Section

Listing 2 EPANET 보고서 파일의 발췌.

```

  ******************************************************************
  *                           E P A N E T                          *
  *                   Hydraulic and Water Quality                  *
  *                   Analysis for Pipe Networks                   *
  *                         Version 2.2                            *
  ******************************************************************

  EPANET TUTORIAL

      Input Data File ................... docs\tutorial.inp
      Number of Junctions................ 5
      Number of Reservoirs............... 1
      Number of Tanks ................... 1
      Number of Pipes ................... 6
      Number of Pumps ................... 1
      Number of Valves .................. 0
      Headloss Formula .................. Hazen-Williams
      Nodal Demand Model ................ DDA
      Hydraulic Timestep ................ 1.00 hrs
      Hydraulic Accuracy ................ 0.001000
      Status Check Frequency ............ 2
      Maximum Trials Checked ............ 10
      Damping Limit Threshold ........... 0.000000
      Maximum Trials .................... 200
      Quality Analysis .................. Chlorine
      Water Quality Time Step ........... 5.00 min
      Water Quality Tolerance ........... 0.01 mg/L
      Specific Gravity .................. 1.00
      Relative Kinematic Viscosity ...... 1.00
      Relative Chemical Diffusivity ..... 1.00
      Demand Multiplier ................. 1.00
      Total Duration .................... 24.00 hrs
      Reporting Criteria:
         All Nodes
         All Links

  Energy Usage:
  ----------------------------------------------------------------
             Usage   Avg.     Kw-hr      Avg.      Peak      Cost
  Pump      Factor Effic.     /Mgal        Kw        Kw      /day
  ----------------------------------------------------------------
  7         100.00  75.00    745.97     51.35     51.59      0.00
  ----------------------------------------------------------------
                                         Demand Charge:      0.00
                                         Total Cost:         0.00

  Node Results at 0:00:00 hrs:
  --------------------------------------------------------
                     Demand      Head  Pressure  Chlorine
  Node                  gpm        ft       psi      mg/L
  --------------------------------------------------------
  2                    0.00    893.19    387.02      0.00
  3                  325.00    879.67     73.52      0.00
  4                   75.00    874.36     75.55      0.00
  5                  100.00    872.62     76.96      0.00
  6                   75.00    872.65     74.81      0.00
  1                -1049.81    700.00      0.00      1.00  Reservoir
  7                  474.81    855.00      2.17      0.00  Tank

  Link Results at 0:00:00 hrs:
  ----------------------------------------------
                       Flow  Velocity  Headloss
  Link                  gpm       fps   /1000ft
  ----------------------------------------------
  1                 1049.81      2.98      4.51
  2                  559.25      1.59      1.40
  3                  165.56      1.06      1.06
  4                   90.56      0.58      0.35
  5                   -9.44      0.06      0.01
  6                  474.81      1.94      2.52
  7                 1049.81      0.00   -193.19  Pump

  Node Results at 1:00:00 hrs:
  --------------------------------------------------------
                     Demand      Head  Pressure  Chlorine
  Node                  gpm        ft       psi      mg/L
  --------------------------------------------------------
  2                    0.00    893.74    387.26      1.00
  3                  325.00    880.31     73.80      0.99
  4                   75.00    875.05     75.85      0.00
  5                  100.00    873.33     77.27      0.00
  6                   75.00    873.36     75.12      0.00
  1                -1045.87    700.00      0.00      1.00  Reservoir
  7                  470.87    855.99      2.60      0.00  Tank
```

### Status Section

출력 보고서의 Status Section 은 모든 저수지, 탱크, 펌프, 밸브, 닫힌 관(closed pipe)의 초기 상태와, 연장 기간 모의(extended period simulation)에서 시간이 지남에 따라 발생하는 이 구성요소들의 상태 변화를 나열한다. 저수지와 탱크의 상태는 채워지고 있는지 비워지고 있는지를 나타낸다. 링크의 상태는 열려 있는지 닫혀 있는지를 나타내며, 펌프의 상대 속도 설정값과 제어밸브의 압력/유량 설정값을 포함한다. 보고서에 Status Section 을 포함하려면 입력 파일의 [REPORT] 섹션에서 **STATUS YES** 명령을 사용한다.

**STATUS FULL** 을 사용하면 모의 중에 수행된 각 수리 해석의 모든 반복(iteration)에 대한 수렴 결과의 전체 목록도 생성된다. 이 목록은 또한 반복 중에 어떤 구성요소가 상태를 변경하는지도 보여준다. 이 수준의 상세 정보는 어떤 구성요소의 상태가 순환(cycling)하여 수렴에 실패하는 실행을 디버깅하려 할 때만 유용하다.

### Energy Section

출력 보고서의 Energy Section 은 관망 내 각 펌프의 전체 에너지 소비량과 비용을 나열한다. 각 펌프에 대해 나열되는 항목은 다음과 같다.

- Percent Utilization (펌프가 가동되는 시간의 비율)
- Average Efficiency (평균 효율)
- Kilowatt-hours consumed per million gallons (or cubic meters) pumped (펌핑된 백만 갤런(또는 세제곱미터)당 소비된 킬로와트시)
- Average Kilowatts consumed (소비된 평균 킬로와트)
- Peak Kilowatts used (사용된 최대 킬로와트)
- Average cost per day (일평균 비용)

또한 펌핑에 대한 일일 총비용과 발생한 총 수요 요금(demand charge, 최대 에너지 사용량에 기반한 비용)도 나열된다. 보고서에 Energy Section 을 포함하려면 입력 파일의 [REPORT] 섹션에 **ENERGY YES** 명령이 나타나야 한다.

### Nodes Section

출력 보고서의 Nodes Section 은 입력 파일의 [REPORT] 섹션에서 식별된 노드 및 파라미터에 대한 모의 결과를 나열한다. 결과는 연장 기간 모의의 각 보고 시간 간격(reporting time step)마다 나열된다. 보고 시간 간격은 입력 파일의 [TIMES] 섹션에서 지정된다. 펌프가 켜지거나 꺼지는 경우, 또는 탱크가 비거나 차서 닫히는 경우 등 특정 수리 사건(hydraulic event)이 발생하는 중간 시점의 결과는 보고되지 않는다.

절점 결과를 보고하려면 입력 파일의 [REPORT] 섹션에 키워드 **NODES** 와 보고서에 포함할 노드의 ID 라벨 목록이 포함되어야 한다. 파일에는 그러한 **NODES** 줄이 여러 개 있을 수 있다. 모든 노드에 대한 결과를 보고하려면 **NODES ALL** 명령을 사용한다.

노드에 대해 기본으로 보고되는 수량 집합에는 Demand, Head, Pressure, Water Quality 가 포함된다. **PRESSURE PRECISION 3** 와 같은 명령을 입력 파일에 사용하여 파라미터의 결과를 나열할 때 소수점 자리수를 몇 개 사용할지 지정할 수 있다(즉, 압력 결과를 보고할 때 소수점 3 자리 사용). 기본 정밀도는 모든 수량에 대해 소수점 2 자리이다. **PRESSURE BELOW 20** 형태의 구문을 입력 파일에 추가하여 특정 값보다 낮거나 높은 값의 발생만 나열하도록 보고서를 필터링할 수 있다.

### Links Section

출력 보고서의 Links Section 은 입력 파일의 [REPORT] 섹션에서 식별된 링크 및 파라미터에 대한 모의 결과를 나열한다. 보고 시점은 앞 절에서 노드에 대해 설명한 것과 동일한 규약을 따른다.

노드와 마찬가지로, 링크에 대한 결과를 보고하려면 입력 파일의 [REPORT] 섹션에 키워드 **LINKS** 와 링크 ID 라벨 목록을 포함해야 한다. 모든 링크에 대한 결과를 보고하려면 **LINKS ALL** 명령을 사용한다.

링크에 대해 기본으로 보고되는 파라미터에는 Flow, Velocity, Headloss 가 포함된다. **DIAMETER YES** 또는 **DIAMETER PRECISION 0** 와 같은 명령을 사용하여 Diameter, Length, Water Quality, Status, Setting, Reaction Rate, Friction Factor 를 여기에 추가할 수 있다. 보고 정밀도와 필터를 지정하기 위해 노드 파라미터에 사용된 동일한 규약이 링크에도 적용된다.

## 이진 출력 파일 형식 (Binary Output File Format)

EPANET 을 실행하는 커맨드라인에 세 번째 파일 이름이 제공되면, 모든 보고 시간 주기에 대한 모든 노드와 링크의 모든 파라미터 결과가 특수한 이진 형식(binary format)으로 이 파일에 저장된다. 이 파일은 특수한 후처리(post-processing) 목적으로 사용될 수 있다. 파일에 기록되는 데이터는 4바이트 정수(integer), 4바이트 실수(float), 또는 크기가 4바이트의 배수인 고정 크기 문자열(fixed-size string)이다. 이를 통해 파일을 4바이트 레코드로 편리하게 분할할 수 있다. 파일은 Table 4 에 나열된 네 개의 섹션으로 구성된다.

| *SECTION* | *SIZE in BYTES* |
| --- | --- |
| Prolog | 852 + 20*Nnodes + 36*Nlinks + 8*Ntanks |
| Energy Use | 28*Npumps + 4 |
| Extended Period | (16*Nnodes + 32*Nlinks)*Nperiods |
| Epilog | 28 |

여기서

Nnodes = 노드 수(절점 + 저수지 + 탱크) Nlinks = 링크 수(관 + 펌프 + 밸브) Ntanks = 탱크 및 저수지 수

Npumps = 펌프 수

Nperiods = 보고 주기 수

이고, 이 개수들 자체도 파일의 Prolog 또는 Epilog 섹션에 기록된다.

### Prolog Section

이진 출력 파일의 prolog 섹션은 Table 5 에 나열된 다음 데이터를 포함한다.

| *ITEM* | *TYPE* | *NUMBER of BYTES* |
| --- | --- | --- |
| Magic Number ( = 516114521) | Integer | 4 |
| Version (= 200) | Integer | 4 |
| Number of Nodes (Junctions + Reservoirs + Tanks) | Integer | 4 |
| Number of Reservoirs & Tanks | Integer | 4 |
| Number of Links (Pipes + Pumps + Valves) | Integer | 4 |
| Number of Pumps | Integer | 4 |
| Number of Valves | Integer | 4 |
| Water Quality Option   0 = none 1 = chemical 2 = age 3 = source trace | Integer | 4 |
| Index of Node for Source Tracing | Integer | 4 |
| Flow Units Option   0 = cfs 1 = gpm 2 = mgd 3 = Imperial mgd 4 = acre-ft/day 5 = liter/sec 6 = liter/min 7 = megaliter/day 8 = cubic meter/hr 9 = cubic meter/day | Integer | 4 |
| Pressure Units Option   0 = psi 1 = meters 2 = kPa | Integer | 4 |
| Statistics Flag   0 = no statistics 1 = time-averaged 2 = minimums 3 = maximums 4 = ranges | Integer | 4 |
| Reporting Start Time (seconds) | Integer | 4 |
| Reporting Time Step (seconds) | Integer | 4 |
| Simulation Duration (seconds) | Integer | 4 |
| Problem Title (1st line) | Char | 80 |
| Problem Title (2nd line) | Char | 80 |
| Problem Title (3rd line) | Char | 80 |
| Name of Input File | Char | 260 |
| Name of Report File | Char | 260 |
| Name of Chemical | Char | 16 |
| Chemical Concentration Units | Char | 16 |
| ID Label of Each Node | Char | 16 |
| ID Label of Each Link | Char | 16 |
| Index of Start Node of Each Link | Integer | 4*Nlinks |
| Index of End Node of Each Link | Integer | 4*Nlinks |
| Type Code of Each Link   0 = Pipe with CV 1 = Pipe 2 = Pump 3 = PRV 4 = PSV 5 = PBV 6 = FCV 7 = TCV 8 = GPV | Integer | 4*Nlinks |
| Node Index of Each Tank | Integer | 4*Ntanks |
| Cross-Sectional Area of Each Tank | Float | 4*Ntanks |
| Elevation of Each Node | Float | 4*Nnodes |
| Length of Each Link | Float | 4*Nlinks |
| Diameter of Each Link | Float | 4*Nlinks |

노드와 링크의 ID 라벨이 파일에 기록되는 순서와 이 구성요소들의 인덱스 번호(index number)는 일대일로 대응된다. 또한 저수지(reservoir)는 단면적(cross-sectional area)이 0 으로 설정됨으로써 탱크(tank)와 구별된다.

### Energy Use Section

이진 출력 파일의 energy use 섹션은 prolog 섹션 바로 다음에 온다. 이는 Table 6 에 나열된 데이터를 포함한다.

| *ITEM* | *TYPE* | *NUMBER of BYTES* |
| --- | --- | --- |
| Repeated for each pump: Pump Index in List of Links Pump Utilization (%) Average Efficiency (%) Average Kwatts/MGal (/meter 3) Average Kwatts Average Cost Per Day | Float Float Float Float Float Float | 4 4 4 4 4 4 |
| Overall Peak Energy Usage | Float | 4 |

이 섹션에 보고되는 통계는 출력 보고 기간의 시작부터 모의 종료까지의 시간 구간을 가리킨다.

### Extended Period Section

이진 출력 파일의 extended period 섹션은 해석의 각 보고 주기(reporting period)에 대한 모의 결과를 포함한다(보고 시작 시각과 시간 간격은 출력 파일의 prolog 섹션에 기록되고, 단계 수는 epilog 섹션에 기록된다). 각 보고 주기에 대해 Table 7 은 파일에 기록되는 값들을 나열한다.

| *ITEM* | *TYPE* | *SIZE in BYTES* |
| --- | --- | --- |
| Demand at Each Node | Float | 4*Nnodes |
| Hydraulic Head at Each Node | Float | 4*Nnodes |
| Pressure at Each Node | Float | 4*Nnodes |
| Water Quality at Each Node | Float | 4*Nnodes |
| Flow in Each Link (negative for reverse flow) | Float | 4*Nlinks |
| Velocity in Each Link | Float | 4*Nlinks |
| Headloss per 1000 Units of Length for Each Link (Negative of head gain for pumps and total head loss for valves) | Float | 4*Nlinks |
| Average Water Quality in Each Link | Float | 4*Nlinks |
| Status Code for Each Link   0 = closed (max head exceeded) 1 = temporarily closed 2 = closed 3 = open 4 = active (partially open) 5 = open (max flow exceeded) 6 = open (flow setting not met) 7 = open (press setting not met) | Float | 4*Nlinks |
| Setting for Each Link:   Roughness Coefficient for Pipes Speed for pumps Setting for Valves | Float | 4*Nlinks |
| Reaction Rate for Each Link (mass/L/day) | Float | 4*Nlinks |
| Friction Factor for Each Link Each Link | Float | 4*Nlinks |

### Epilogue Section

이진 출력 파일의 epilogue 섹션은 Table 8 에 나열된 다음 데이터를 포함한다.

| *ITEM* | *TYPE* | *NUMBER of BYTES* |
| --- | --- | --- |
| Average bulk reaction rate (mass/hr) | Float | 4 |
| Average wall reaction rate (mass/hr) | Float | 4 |
| Average tank reaction rate (mass/hr) | Float | 4 |
| Average source inflow rate (mass/hr) | Float | 4 |
| Number of Reporting Periods | Integer | 4 |
| Warning Flag:   0 = no warnings 1 = warnings were generated | Integer | 4 |
| Magic Number ( = 516114521) | Integer | 4 |

여기와 Extended Period 출력에서 반응 속도(reaction rate)의 질량 단위(mass units)는 모델링되는 화학물질에 할당된 농도 단위에 따라 달라진다. 이 섹션에 나열된 반응 속도는 모의의 전체 보고 기간에 걸쳐 모든 관(또는 모든 탱크)에서 관찰된 속도의 평균을 가리킨다.
