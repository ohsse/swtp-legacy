> 원문: [EPANET 2.2 — 6. Working with Objects](https://usepa.github.io/EPANET2.2/6_objects.html)
> EPANET 2.2 공식 매뉴얼을 한국어로 정리한 문서입니다. 섹션 키워드·약어·UI 라벨은 원문을 유지합니다.

# 6. 객체 다루기 (Working with Objects)

*EPANET 은 상수도 배급 시스템을 모델링하기 위해 다양한 종류의 객체를 사용한다. 이러한 객체는 지도(Network Map) 위에서 직접 접근하거나 Browser 창의 Data 페이지에서 접근할 수 있다. 이 장에서는 이러한 객체가 무엇인지, 그리고 어떻게 생성·선택·편집·삭제·재배치하는지를 설명한다.*

## 6.1. 객체의 종류 (Types of Objects)

EPANET 은 지도에 표시될 수 있는 물리적 객체와, 설계·운영 정보를 담는 비물리적 객체를 모두 포함한다. 이러한 객체는 다음과 같이 분류할 수 있다.

1. 노드(Nodes) — 절점(Junctions), 저수지(Reservoirs), 탱크(Tanks)
2. 링크(Links) — 관(Pipes), 펌프(Pumps), 밸브(Valves)
3. 지도 라벨(Map Labels)
4. 시간패턴(Time Patterns)
5. 곡선(Curves)
6. 제어(Controls) — 단순 제어(Simple), 규칙 기반 제어(Rule-Based)

## 6.2. 객체 추가 (Adding Objects)

**노드 추가 (Adding a Node)**

Map Toolbar 를 사용해 노드를 추가하려면:

1. Map Toolbar 에서 추가할 노드 종류 버튼(절점 ![image78](https://usepa.github.io/EPANET2.2/_images/image6.png), 저수지 ![image79](https://usepa.github.io/EPANET2.2/_images/image5.png), 탱크 ![image80](https://usepa.github.io/EPANET2.2/_images/image7.png))이 아직 눌려 있지 않다면 클릭한다.
2. 지도 위에서 원하는 위치로 마우스를 옮긴 뒤 클릭한다.

Browser 를 사용해 노드를 추가하려면:

1. Data Browser 의 Object 목록에서 노드 종류(절점, 저수지, 탱크)를 선택한다.
2. Add 버튼 ![image81](https://usepa.github.io/EPANET2.2/_images/image16.jpeg) 을 클릭한다.
3. Property Editor 에서 지도 좌표를 입력한다(선택 사항).

**링크 추가 (Adding a Link)**

Map Toolbar 를 사용해 직선 또는 곡선 형태의 링크를 추가하려면:

1. Map Toolbar 에서 추가할 링크 종류 버튼(관 ![image82](https://usepa.github.io/EPANET2.2/_images/image9.png), 펌프 ![image83](https://usepa.github.io/EPANET2.2/_images/image10.png), 밸브 ![image84](https://usepa.github.io/EPANET2.2/_images/image52.png))이 아직 눌려 있지 않다면 클릭한다.
2. 지도 위에서 링크의 시작 노드 위를 마우스로 클릭한다.
3. 링크의 끝 노드 방향으로 마우스를 이동하면서, 링크의 방향을 바꿔야 하는 중간 지점마다 클릭한다.
4. 마지막으로 링크의 끝 노드 위를 마우스로 클릭한다.

링크를 그리는 도중 마우스 오른쪽 버튼이나 Escape 키를 누르면 작업이 취소된다.

Browser 를 사용해 직선 링크를 추가하려면:

1. Data Browser 의 Object 목록에서 추가할 링크 종류(관, 펌프, 밸브)를 선택한다.
2. Add 버튼을 클릭한다.
3. Property Editor 에서 링크의 From(시작) 노드와 To(끝) 노드를 입력한다.

**지도 라벨 추가 (Adding a Map Label)**

지도에 라벨을 추가하려면:

1. Map Toolbar 의 Text 버튼 ![image85](https://usepa.github.io/EPANET2.2/_images/image11.png) 을 클릭한다.
2. 라벨이 표시될 지도 위 위치를 마우스로 클릭한다.
3. 라벨의 텍스트를 입력한다.
4. **Enter** 키를 누른다.

**곡선 추가 (Adding a Curve)**

네트워크 데이터베이스에 곡선을 추가하려면:

1. Data Browser 의 객체 카테고리 목록에서 Curve 를 선택한다.
2. Add 버튼을 클릭한다.
3. Curve Editor 로 곡선을 편집한다(아래 참조).

**시간패턴 추가 (Adding a Time Pattern)**

네트워크에 시간패턴을 추가하려면:

1. Data Browser 의 객체 카테고리 목록에서 Patterns 를 선택한다.
2. Add 버튼을 클릭한다.
3. Pattern Editor 로 패턴을 편집한다(아래 참조).

**텍스트 파일 사용 (Using a Text File)**

객체를 하나씩 대화식으로 추가하는 방법 외에도, 노드 ID 와 그 좌표 목록, 그리고 링크 ID 와 그것을 연결하는 노드 목록을 담은 텍스트 파일을 가져올 수 있다([Section 11.4](https://usepa.github.io/EPANET2.2/11_importing_exporting.html#sec-import-partial-net) 참조).

## 6.3. 객체 선택 (Selecting Objects)

지도에서 객체를 선택하려면:

1. 지도가 Selection(선택) 모드인지 확인한다(마우스 커서가 왼쪽 위를 가리키는 화살표 모양). 이 모드로 전환하려면 Map Toolbar 의 Select Object 버튼 ![image86](https://usepa.github.io/EPANET2.2/_images/image12.png) 을 클릭하거나 **Edit** 메뉴에서 **Select Object** 를 선택한다.
2. 지도에서 원하는 객체 위를 마우스로 클릭한다.

Browser 를 사용해 객체를 선택하려면:

1. Data Browser 의 드롭다운 목록에서 객체 카테고리를 선택한다.
2. 카테고리 헤딩 아래 목록에서 원하는 객체를 선택한다.

## 6.4. 가시 객체 편집 (Editing Visual Objects)

Property Editor([Section 4.8](https://usepa.github.io/EPANET2.2/4_EPANET_workspace.html#sec-prop-ed) 참조)는 지도(Network Map)에 표시될 수 있는 객체(절점, 저수지, 탱크, 관, 펌프, 밸브, 라벨)의 속성을 편집하는 데 사용된다. 이러한 객체 중 하나를 편집하려면, 지도나 Data Browser 에서 객체를 선택한 뒤 Data Browser 의 Edit 버튼 ![image87](https://usepa.github.io/EPANET2.2/_images/image14.jpeg) 을 클릭한다(또는 지도에서 객체를 더블클릭한다). 이러한 각 객체 유형에 연관된 속성은 Table 6.1 부터 Table 6.7 까지 설명되어 있다.

참고: 객체 속성이 표현되는 단위 체계는 유량(flow rate) 단위 선택에 따라 달라진다. 유량을 cubic feet, gallons, acre-feet 로 표현하면 모든 수치에 US 단위가 사용된다. 유량을 liters 나 cubic meters 로 표현하면 SI 미터법 단위가 사용된다. 유량 단위는 프로젝트의 Hydraulic Options 에서 선택하며, **Project >> Defaults** 메뉴를 통해 접근할 수 있다. 모든 속성에 사용되는 단위는 부록 [Units of Measurement](https://usepa.github.io/EPANET2.2/back_matter.html#units) 에 정리되어 있다.

절점(Junction) 속성은 Table 6.1 에 정리되어 있다.

| *PROPERTY* | *DESCRIPTION* |
| --- | --- |
| Junction ID | 절점을 식별하는 데 사용하는 고유한 라벨. 최대 15 자의 숫자 또는 문자 조합으로 구성할 수 있다. 다른 어떤 노드의 ID 와도 같을 수 없다. 필수 속성이다. |
| X-Coordinate | 지도상 절점의 수평 위치로, 지도의 거리 단위로 측정된다. 비워 두면 절점이 지도에 표시되지 않는다. |
| Y-Coordinate | 지도상 절점의 수직 위치로, 지도의 거리 단위로 측정된다. 비워 두면 절점이 지도에 표시되지 않는다. |
| Description | 절점에 대한 그 밖의 중요한 정보를 설명하는 선택적 텍스트 문자열. |
| Tag | 절점을 압력대(pressure zone) 같은 카테고리에 할당하는 데 사용하는 선택적 텍스트 문자열(공백 없음). |
| Elevation | 공통 기준면을 기준으로 한 절점의 표고(feet 또는 meters). 필수 속성이다. 표고는 절점의 압력 계산에만 사용되며, 다른 계산값에는 영향을 주지 않는다. |
| Base Demand | 현재 유량 단위로 측정된, 절점에서 주요 소비자 카테고리의 평균 또는 공칭 물 수요량. 음수 값은 절점으로 유입되는 외부 유량원을 나타낸다. 비워 두면 수요량은 0 으로 간주된다. |
| Demand Pattern | 절점에서 주요 소비자 카테고리의 수요량 시간 변동을 나타내는 데 사용하는 시간패턴의 ID 라벨. 이 패턴은 Base Demand 에 적용되는 배율(multiplier)을 제공하여 특정 시간대의 실제 수요량을 결정한다. 비워 두면 Hydraulic Options 에 지정된 **Default Time Pattern** 이 사용된다([Section 8.1](https://usepa.github.io/EPANET2.2/8_analyzing_network.html#sec-analysis-ops) 참조). |
| Demand Categories | 절점에 정의된 서로 다른 물 사용자 카테고리의 수. ellipsis 버튼(말줄임표 버튼)을 클릭하거나 Enter 키를 누르면 전용 Demands Editor 가 나타나, 절점의 여러 사용자 카테고리에 base demand 와 시간패턴을 할당할 수 있다. 단일 수요 카테고리로 충분하다면 무시한다. |
| Emitter Coefficient | 절점에 설치된 이미터(Emitter, 스프링클러 또는 노즐)의 토출 계수. 이 계수는 1 psi(또는 meter)의 압력 강하에서 발생하는 유량(현재 유량 단위)을 나타낸다. 이미터가 없으면 비워 둔다. 자세한 내용은 [Section 3.1](https://usepa.github.io/EPANET2.2/3_network_model.html#sec-physical-comps) 의 Emitters 항목을 참조한다. |
| Initial Quality | 시뮬레이션 기간 시작 시점의 절점 수질 수준. 수질 분석을 하지 않거나 수준이 0 이면 비워 둘 수 있다. |
| Source Quality | 이 위치에서 네트워크로 유입되는 물의 수질. ellipsis 버튼을 클릭하거나 Enter 키를 누르면 Source Quality Editor 가 나타난다(아래 6.5 절 참조). |

저수지(Reservoir) 속성은 Table 6.2 에 정리되어 있다.

| *PROPERTY* | *DESCRIPTION* |
| --- | --- |
| Reservoir ID | 저수지를 식별하는 데 사용하는 고유한 라벨. 최대 15 자의 숫자 또는 문자 조합으로 구성할 수 있다. 다른 어떤 노드의 ID 와도 같을 수 없다. 필수 속성이다. |
| X-Coordinate | 지도상 저수지의 수평 위치로, 지도의 거리 단위로 측정된다. 비워 두면 저수지가 지도에 표시되지 않는다. |
| Y-Coordinate | 지도상 저수지의 수직 위치로, 지도의 거리 단위로 측정된다. 비워 두면 저수지가 지도에 표시되지 않는다. |
| Description | 저수지에 대한 그 밖의 중요한 정보를 설명하는 선택적 텍스트 문자열. |
| Tag | 저수지를 압력대(pressure zone) 같은 카테고리에 할당하는 데 사용하는 선택적 텍스트 문자열(공백 없음). |
| Total Head | 저수지 내 물의 수리수두(표고 + 압력수두)로, 단위는 feet(meters). 필수 속성이다. |
| Head Pattern | 저수지의 수두 시간 변동을 모델링하는 데 사용하는 시간패턴의 ID 라벨. 해당 사항이 없으면 비워 둔다. 이 속성은 저수지가 시간에 따라 압력이 변하는 다른 시스템과의 연결점(tie-in)을 나타낼 때 유용하다. |
| Initial Quality | 저수지의 수질 수준. 수질 분석을 하지 않거나 수준이 0 이면 비워 둘 수 있다. |
| Source Quality | 이 위치에서 네트워크로 유입되는 물의 수질. ellipsis 버튼을 클릭하거나 Enter 키를 누르면 Source Quality Editor 가 나타난다(아래 Fig. 6.5 참조). |

탱크(Tank) 속성은 Table 6.3 에 정리되어 있다.

| *PROPERTY* | *DESCRIPTION* |
| --- | --- |
| Tank ID | 탱크를 식별하는 데 사용하는 고유한 라벨. 최대 15 자의 숫자 또는 문자 조합으로 구성할 수 있다. 다른 어떤 노드의 ID 와도 같을 수 없다. 필수 속성이다. |
| X-Coordinate | 지도상 탱크의 수평 위치로, 지도의 스케일링 단위로 측정된다. 비워 두면 탱크가 지도에 표시되지 않는다. |
| Y-Coordinate | 지도상 탱크의 수직 위치로, 지도의 스케일링 단위로 측정된다. 비워 두면 탱크가 지도에 표시되지 않는다. |
| Description | 탱크에 대한 그 밖의 중요한 정보를 설명하는 선택적 텍스트 문자열. |
| Tag | 탱크를 압력대(pressure zone) 같은 카테고리에 할당하는 데 사용하는 선택적 텍스트 문자열(공백 없음). |
| Elevation | 공통 기준면(datum)을 기준으로 한 탱크 바닥 쉘의 표고(feet 또는 meters). 필수 속성이다. |
| Initial Level | 시뮬레이션 시작 시점에 탱크 바닥 표고로부터의 수면 높이(feet 또는 meters). 필수 속성이다. |
| Minimum Level | 유지될 수 있는, 바닥 표고로부터의 최소 수면 높이(feet 또는 meters). 탱크는 이 수위 아래로 내려갈 수 없다. 필수 속성이다. |
| Maximum Level | 유지될 수 있는, 바닥 표고로부터의 최대 수면 높이(feet 또는 meters). 탱크는 이 수위 위로 올라갈 수 없다. 필수 속성이다. |
| Diameter | 탱크의 직경(feet 또는 meters). 원통형 탱크의 경우 실제 직경이다. 정사각형 또는 직사각형 탱크의 경우 단면적의 제곱근에 1.128 을 곱한 등가 직경을 사용할 수 있다. 형상을 곡선(아래 참조)으로 기술하는 탱크의 경우 임의의 값으로 설정할 수 있다. 필수 속성이다. |
| Minimum Volume | 탱크가 최소 수위에 있을 때의 물 부피(cubic feet 또는 cubic meters). 선택적 속성으로, 부피-수심 곡선 전체를 제공하지 않는 비원통형 탱크의 바닥 형상을 기술할 때 주로 유용하다(아래 참조). |
| Volume Curve | 탱크 부피와 수위의 관계를 기술하는 데 사용하는 곡선의 ID 라벨. 값을 제공하지 않으면 탱크는 원통형으로 간주된다. |
| Mixing Model | 탱크 내에서 발생하는 수질 혼합 유형. 선택지는 다음과 같다.  MIXED(완전 혼합) 2COMP(2 구획 혼합) FIFO(선입선출 압출류) LIFO(후입선출 압출류)  자세한 내용은 [Section 3.4](https://usepa.github.io/EPANET2.2/3_network_model.html#sec-wq-sim-model) 의 Mixing Models 항목을 참조한다. |
| Mixing Fraction | 2 구획(2COMP) 혼합 모델에서 입출구 구획이 차지하는, 탱크 전체 부피에 대한 비율(fraction). 다른 유형의 혼합 모델을 사용하는 경우 비워 둘 수 있다. |
| Reaction Coefficient | 탱크 내 화학 반응에 대한 벌크 반응 계수(bulk reaction coefficient). 시간 단위는 1/days. 성장 반응에는 양수 값을, 감쇠 반응에는 음수 값을 사용한다. 프로젝트의 Reactions Options 에 지정된 Global Bulk 반응 계수를 적용하려면 비워 둔다. 자세한 내용은 [Section 3.4](https://usepa.github.io/EPANET2.2/3_network_model.html#sec-wq-sim-model) 의 Water Quality Reactions 를 참조한다. |
| Initial Quality | 시뮬레이션 시작 시점의 탱크 수질 수준. 수질 분석을 하지 않거나 수준이 0 이면 비워 둘 수 있다. |
| Source Quality | 이 위치에서 네트워크로 유입되는 물의 수질. ellipsis 버튼을 클릭하거나 Enter 키를 누르면 Source Quality Editor 가 나타난다(아래 Fig. 6.5 참조). |

관(Pipe) 속성은 Table 6.4 에 정리되어 있다.

| *PROPERTY* | *DESCRIPTION* |
| --- | --- |
| Pipe ID | 관을 식별하는 데 사용하는 고유한 라벨. 최대 15 자의 숫자 또는 문자 조합으로 구성할 수 있다. 다른 어떤 링크의 ID 와도 같을 수 없다. 필수 속성이다. |
| Start Node | 관이 시작되는 노드의 ID. 필수 속성이다. |
| End Node | 관이 끝나는 노드의 ID. 필수 속성이다. |
| Description | 관에 대한 그 밖의 중요한 정보를 설명하는 선택적 텍스트 문자열. |
| Tag | 관을 카테고리(예: 사용 연수나 재질 기반)에 할당하는 데 사용하는 선택적 텍스트 문자열(공백 없음). |
| Length | 관의 실제 길이(feet 또는 meters). 필수 속성이다. |
| Diameter | 관의 직경(inches 또는 mm). 필수 속성이다. |
| Roughness | 관의 조도 계수(roughness coefficient). Hazen-Williams 또는 Chezy-Manning 조도의 경우 무차원이며, Darcy-Weisbach 조도의 경우 단위는 millifeet(mm) 이다. 필수 속성이다. |
| Loss Coefficient | 굴곡부, 이음쇠 등과 관련된 무차원 미소손실 계수(minor loss coefficient). 비워 두면 0 으로 간주된다. |
| Initial Status | 관이 초기에 열림(open), 닫힘(closed)인지, 또는 체크밸브(check valve)를 포함하는지를 결정한다. 체크밸브가 지정되면 관 내 유동 방향은 항상 Start 노드에서 End 노드로 향한다. |
| Bulk Coefficient | 관의 벌크 반응 계수. 시간 단위는 1/days. 성장에는 양수 값을, 감쇠에는 음수 값을 사용한다. 프로젝트의 Reaction Options 에 지정된 Global Bulk 반응 계수를 적용하려면 비워 둔다. 자세한 내용은 [Section 3.4](https://usepa.github.io/EPANET2.2/3_network_model.html#sec-wq-sim-model) 의 Water Quality Reactions 를 참조한다. |
| Wall Coefficient | 관의 벽면 반응 계수(wall reaction coefficient). 시간 단위는 1/days. 성장에는 양수 값을, 감쇠에는 음수 값을 사용한다. 프로젝트의 Reactions Options 에 지정된 Global Wall 반응 계수를 적용하려면 비워 둔다. 자세한 내용은 [Section 3.4](https://usepa.github.io/EPANET2.2/3_network_model.html#sec-wq-sim-model) 의 Water Quality Reactions 를 참조한다. |

**참고**: **Auto-Length** 설정이 켜져 있으면, 지도에서 관을 추가하거나 재배치할 때 관 길이가 자동으로 계산될 수 있다. 이 설정을 켜고/끄려면 다음 중 하나를 수행한다.

- **Project >> Defaults** 를 선택하고 Defaults 대화상자의 Properties 페이지에서 Auto-Length 필드를 편집한다.
- Status Bar 의 Auto-Length 영역을 마우스 오른쪽 버튼으로 클릭한 뒤, 나타나는 팝업 메뉴 항목을 클릭한다.

Auto-Length 기능을 사용하기 전에 네트워크 지도에 의미 있는 치수(dimensions)를 반드시 지정해야 한다([Section 7.2](https://usepa.github.io/EPANET2.2/7_map.html#sec-set-map-dimensions) 참조).

펌프(Pump) 속성은 Table 6.5 에 정리되어 있다.

| *PROPERTY* | *DESCRIPTION* |
| --- | --- |
| Pump ID | 펌프를 식별하는 데 사용하는 고유한 라벨. 최대 15 자의 숫자 또는 문자 조합으로 구성할 수 있다. 다른 어떤 링크의 ID 와도 같을 수 없다. 필수 속성이다. |
| Start Node | 펌프의 흡입(suction) 측 노드의 ID. 필수 속성이다. |
| End Node | 펌프의 토출(discharge) 측 노드의 ID. 필수 속성이다. |
| Description | 펌프에 대한 그 밖의 중요한 정보를 설명하는 선택적 텍스트 문자열. |
| Tag | 펌프를 카테고리(예: 사용 연수, 크기, 위치 기반)에 할당하는 데 사용하는 선택적 텍스트 문자열(공백 없음). |
| Pump Curve | 펌프가 공급하는 수두와 펌프를 통과하는 유량의 관계를 기술하는 펌프 곡선(pump curve)의 ID 라벨. 펌프가 정전력(constant energy) 펌프인 경우 비워 둔다(아래 참조). |
| Power | 펌프가 공급하는 출력(horsepower 또는 kw). 유량에 관계없이 펌프가 동일한 양의 에너지를 공급한다고 가정한다. 대신 펌프 곡선을 사용하려면 비워 둔다. 펌프 곡선 정보를 사용할 수 없을 때 사용한다. |
| Speed | 펌프의 상대 속도 설정값(무차원). 예를 들어 속도 설정값 1.2 는 펌프의 회전 속도가 정상 설정보다 20% 높음을 의미한다. |
| Pattern | 펌프의 작동을 제어하는 데 사용하는 시간패턴의 ID 라벨. 패턴의 배율(multiplier)은 속도 설정값과 동등하다. 배율 0 은 해당 시간대에 펌프가 정지됨을 의미한다. 해당 사항이 없으면 비워 둔다. |
| Initial Status | 시뮬레이션 기간 시작 시점의 펌프 상태(open 또는 closed). |
| Efficiency Curve | 유량의 함수로서 펌프의 wire-to-water 효율(백분율)을 나타내는 곡선의 ID 라벨. 이 정보는 에너지 사용량 계산에만 사용된다. 해당 사항이 없거나 프로젝트의 Energy Options 에 제공된 전역 펌프 효율을 사용하려면 비워 둔다([Section 8.1](https://usepa.github.io/EPANET2.2/8_analyzing_network.html#sec-analysis-ops) 참조). |
| Energy Price | kw-hr 당 화폐 단위로 표시한 평균 또는 공칭 에너지 가격. 에너지 사용 비용 계산에만 사용된다. 해당 사항이 없거나 프로젝트의 Energy Options 에 제공된 전역 값을 사용하려면 비워 둔다([Section 8.1](https://usepa.github.io/EPANET2.2/8_analyzing_network.html#sec-analysis-ops) 참조). |
| Price Pattern | 하루 동안의 에너지 가격 변동을 기술하는 데 사용하는 시간패턴의 ID 라벨. 패턴의 각 배율은 펌프의 Energy Price 에 적용되어 해당 시간대의 시간대별 가격(time-of-day pricing)을 결정한다. 해당 사항이 없거나 프로젝트의 Energy Options 에 지정된 전역 가격 패턴을 사용하려면 비워 둔다([Section 8.1](https://usepa.github.io/EPANET2.2/8_analyzing_network.html#sec-analysis-ops) 참조). |

밸브(Valve) 속성은 Table 6.6 에 정리되어 있다.

| *PROPERTY* | *DESCRIPTION* |
| --- | --- |
| ID Label | 밸브를 식별하는 데 사용하는 고유한 라벨. 최대 15 자의 숫자 또는 문자 조합으로 구성할 수 있다. 다른 어떤 링크의 ID 와도 같을 수 없다. 필수 속성이다. |
| Start Node | 밸브의 공칭 상류 또는 유입(inflow) 측 노드의 ID. (PRV 와 PSV 는 단일 방향으로만 유동을 유지한다.) 필수 속성이다. |
| End Node | 밸브의 공칭 하류 또는 토출(discharge) 측 노드의 ID. 필수 속성이다. |
| Description | 밸브에 대한 그 밖의 중요한 정보를 설명하는 선택적 텍스트 문자열. |
| Tag | 밸브를 카테고리(예: 유형이나 위치 기반)에 할당하는 데 사용하는 선택적 텍스트 문자열(공백 없음). |
| Diameter | 밸브의 직경(inches 또는 mm). 필수 속성이다. |
| Type | 밸브 유형(PRV, PSV, PBV, FCV, TCV, GPV). 다양한 밸브 유형에 대한 설명은 [Section 3.1](https://usepa.github.io/EPANET2.2/3_network_model.html#sec-physical-comps) 의 Valves 를 참조한다. 필수 속성이다. |
| Setting | 각 밸브 유형의 운영 설정값을 기술하는 필수 매개변수.  PRV - Pressure(psi 또는 m) PSV - Pressure(psi 또는 m) PBV - Pressure(psi 또는 m) FCV - Flow(유량 단위) TCV - Loss Coeff(무차원) GPV - 수두손실 곡선의 ID |
| Loss Coefficient | 밸브가 완전히 열려 있을 때 적용되는 무차원 미소손실 계수. 비워 두면 0 으로 간주된다. |
| Fixed Status | 시뮬레이션 시작 시점의 밸브 상태. OPEN 또는 CLOSED 로 설정하면 밸브의 제어 설정값이 무시되고 밸브는 각각 열린 링크 또는 닫힌 링크처럼 동작한다. NONE 으로 설정하면 밸브가 의도된 대로 동작한다. 밸브의 고정 상태와 설정값은 control 문(control statements)을 사용해 시뮬레이션 전반에 걸쳐 변하게 할 수 있다. 밸브 상태가 OPEN/CLOSED 로 고정되어 있더라도, 새로운 수치 설정값을 할당하는 제어를 사용하면 다시 활성화할 수 있다. |

지도 라벨(Map Label) 속성은 Table 6.7 에 정리되어 있다.

| *PROPERTY* | *DESCRIPTION* |
| --- | --- |
| Text | 라벨의 텍스트. |
| X-Coordinate | 지도상 라벨 좌측 상단 모서리의 수평 위치로, 지도의 스케일링 단위로 측정된다. 필수 속성이다. |
| Y-Coordinate | 지도상 라벨 좌측 상단 모서리의 수직 위치로, 지도의 스케일링 단위로 측정된다. 필수 속성이다. |
| Anchor Node | 라벨의 앵커 지점(anchor point) 역할을 하는 노드의 ID(아래 참고 1 참조). 라벨을 앵커링하지 않으려면 비워 둔다. |
| Meter Type | 라벨이 계측(metering)할 객체의 유형(아래 참고 2 참조). 선택지는 None, Node, Link 이다. |
| Meter ID | 계측 대상 객체(Node 또는 Link)의 ID. |
| Font | 라벨의 글꼴, 크기, 스타일을 선택할 수 있는 Font 대화상자를 띄운다. |

참고:

1. 라벨의 anchor node 속성은 지도상의 특정 위치를 기준으로 라벨을 고정하는 데 사용된다. 지도를 확대하면, 라벨은 전체 범위(full extent) 보기에서와 동일한 거리만큼 앵커 노드로부터 떨어져 표시된다. 이 기능은 지도를 확대할 때 라벨이 설명 대상 객체로부터 너무 멀리 떨어지는 것을 방지한다.
2. Meter Type 과 ID 속성은 라벨이 계측기(meter) 역할을 할지 여부를 결정한다. 계측 라벨(meter label)은 라벨 텍스트 아래에 현재 표시 매개변수(Map Browser 에서 선택)의 값을 표시한다. Meter Type 과 ID 는 네트워크에 실제로 존재하는 노드 또는 링크를 가리켜야 한다. 그렇지 않으면 라벨 텍스트만 표시된다.

## 6.5. 비가시 객체 편집 (Editing Non-Visual Objects)

곡선(Curves), 시간패턴(Time Patterns), 제어(Controls)는 속성을 정의하는 데 사용하는 전용 편집기를 가지고 있다. 이러한 객체 중 하나를 편집하려면, Data Browser 에서 객체를 선택한 뒤 Edit 버튼 ![image88](https://usepa.github.io/EPANET2.2/_images/image14.jpeg) 을 클릭한다. 또한 절점용 Property Editor 의 Demand Categories 필드에는 클릭 시 전용 Demand Editor 를 띄우는 ellipsis 버튼이 있다. 마찬가지로 절점, 저수지, 탱크의 Property Editor 에 있는 Source Quality 필드에는 전용 Source Quality 편집기를 실행하는 버튼이 있다. 이러한 각 전용 편집기를 다음에서 설명한다.

**Curve Editor (곡선 편집기)**

Curve Editor 는 Fig. 6.1 과 같은 대화상자 형태이다. Curve Editor 를 사용하려면 다음 항목의 값을 입력한다(Table 6.8).

| *ITEM* | *DESCRIPTION* |
| --- | --- |
| Curve ID | 곡선의 ID 라벨(최대 15 자의 숫자 또는 문자) |
| Description | 곡선이 나타내는 바에 대한 선택적 설명 |
| Curve Type | 곡선의 유형 |
| X-Y Data | 곡선의 X-Y 데이터 포인트 |

X-Y 데이터 표의 셀 사이를 이동하면(또는 Enter 키를 누르면) 미리보기 창에 곡선이 다시 그려진다. 1 점 및 3 점 펌프 곡선의 경우, 곡선에 대해 생성된 방정식이 Equation 박스에 표시된다. **OK** 버튼을 클릭하면 곡선을 적용하고, **Cancel** 버튼을 클릭하면 입력을 취소한다. 또한 **Load** 버튼을 클릭하면 이전에 파일로 저장한 곡선 데이터를 불러올 수 있고, **Save** 버튼을 클릭하면 현재 곡선 데이터를 파일로 저장할 수 있다.

![Curve Editor in EPANET](https://usepa.github.io/EPANET2.2/_images/image17.png)

Fig. 6.1 Curve Editor (곡선 편집기).

**Pattern Editor (패턴 편집기)**

Fig. 6.2 에 표시된 Pattern Editor 는 시간패턴 객체의 속성을 편집한다. Pattern Editor 를 사용하려면 다음 항목의 값을 입력한다(Table 6.9).

| *ITEM* | *DESCRIPTION* |
| --- | --- |
| Pattern ID | 패턴의 ID 라벨(최대 15 자의 숫자 또는 문자) |
| Description | 패턴이 나타내는 바에 대한 선택적 설명 |
| Multipliers | 패턴의 각 시간대(time period)에 대한 배율(multiplier) 값. |

배율을 입력하면 미리보기 차트가 다시 그려져 패턴을 시각적으로 보여준다. 배율을 입력하는 도중 사용 가능한 Time Periods 의 끝에 도달하면, **Enter** 키를 누르기만 하면 시간대가 하나 더 추가된다. 편집을 마치면 **OK** 버튼을 클릭하여 패턴을 적용하거나 **Cancel** 버튼을 클릭하여 입력을 취소한다. 또한 **Load** 버튼을 클릭하면 이전에 파일로 저장한 패턴 데이터를 불러올 수 있고, **Save** 버튼을 클릭하면 현재 패턴 데이터를 파일로 저장할 수 있다.

![Pattern Editor in EPANET](https://usepa.github.io/EPANET2.2/_images/image22.png)

Fig. 6.2 Pattern Editor (패턴 편집기).

**Controls Editor (제어 편집기)**

Fig. 6.3 에 표시된 Controls Editor 는 단순 제어와 규칙 기반 제어를 모두 편집하는 데 사용하는 텍스트 편집기 창이다. 편집기 내 아무 곳에서나 마우스 오른쪽 버튼을 클릭하면 활성화되는 표준 텍스트 편집 메뉴를 가지고 있다. 이 메뉴에는 Undo, Cut, Copy, Paste, Delete, Select All 명령이 포함되어 있다.

![Controls Editor in EPANET](https://usepa.github.io/EPANET2.2/_images/image62.png)

Fig. 6.3 Controls Editor (제어 편집기).

**Demand Editor (수요 편집기)**

Demand Editor 는 Fig. 6.4 에 묘사되어 있다. 한 절점에 둘 이상의 물 사용자 카테고리가 있을 때 base demand 와 시간패턴을 할당하는 데 사용된다. 이 편집기는 Demand Categories 필드에 포커스가 있는 상태에서 ellipsis 버튼을 클릭하거나(또는 Enter 키를 눌러) Property Editor 로부터 호출된다.

편집기는 세 개의 열을 가진 표이다. 각 수요 카테고리는 표에 새 행으로 입력된다. 각 열은 다음 정보를 담는다.

- *Base Demand*: 해당 카테고리의 기준 또는 평균 수요량(필수)
- *Time Pattern*: 수요량이 시간에 따라 변하도록 하는 데 사용하는 시간패턴의 ID 라벨(선택)
- *Category*: 수요 카테고리를 식별하는 데 사용하는 텍스트 라벨(선택)

![Demand Editor in EPANET](https://usepa.github.io/EPANET2.2/_images/image63.png)

Fig. 6.4 Demand Editor (수요 편집기).

표는 처음에 10 개 행 크기로 설정된다. 추가 행이 필요하면 마지막 행의 아무 셀이나 선택한 뒤 **Enter** 키를 누른다.

**참고**: 관례상, 편집기의 첫 번째 행에 입력된 수요량이 해당 절점의 주요 카테고리로 간주되며, Property Editor 의 Base Demand 필드에 표시된다.

**Source Quality Editor (소스 수질 편집기)**

Source Quality Editor 는 특정 노드에서 네트워크로 유입되는 소스(공급원) 유량의 수질을 기술하는 데 사용하는 팝업 대화상자이다. 이 소스는 주요 정수처리장, 우물 취수정이나 위성 정수시설(satellite treatment facility), 또는 원치 않는 오염물질 침입(contaminant intrusion)을 나타낼 수 있다. Fig. 6.5 에 표시된 대화상자에는 다음 필드가 포함되어 있다(Table 6.10).

![Source Quality Editor in EPANET](https://usepa.github.io/EPANET2.2/_images/image64.png)

Fig. 6.5 Source Quality Editor (소스 수질 편집기).

| *FIELD* | *DESCRIPTION* |
| --- | --- |
| Source Type | 다음 중 하나를 선택: - Concentration - Mass Booster - Flow Paced Booster - Setpoint Booster |
| Source Quality | 소스의 기준 또는 평균 농도(또는 분당 질량유량) – 소스를 제거하려면 비워 둔다 |
| Quality Pattern | 소스 수질이 시간에 따라 변하도록 하는 데 사용하는 시간패턴의 ID 라벨 – 해당 사항이 없으면 비워 둔다 |

수질 소스(공급원)는 농도(concentration) 소스 또는 부스터(booster) 소스로 지정할 수 있다.

- **concentration source**(농도 소스)는 저수지로부터의 유량이나 절점에 부여된 음(-)의 수요량 등, 네트워크로 유입되는 모든 외부 유입의 농도를 고정한다.
- **mass booster source**(질량 부스터 소스)는 네트워크의 다른 지점에서 노드로 유입되는 양에 고정된 질량유량을 추가한다.
- **flow paced booster source**(유량 비례 부스터 소스)는 네트워크의 다른 지점에서 노드로 유입되는 모든 유량이 혼합되어 생기는 농도에 고정된 농도를 추가한다.
- **setpoint booster source**(설정점 부스터 소스)는 노드로 유입되는 모든 유입의 혼합 결과 농도가 설정점(setpoint) 미만인 한, 노드를 떠나는 모든 유량의 농도를 고정한다.

농도 유형 소스는 원수 공급원이나 정수처리장을 나타내는 노드(예: 저수지 또는 음의 수요량이 할당된 노드)에 사용하는 것이 가장 적합하다. 부스터 유형 소스는 추적자(tracer)나 추가 소독제를 네트워크에 직접 주입하는 것을 모델링하거나, 오염물질 침입을 모델링하는 데 사용하는 것이 가장 적합하다.

## 6.6. 객체 복사 및 붙여넣기 (Copying and Pasting Objects)

지도(Network Map)에 표시된 객체의 속성을 복사하여 같은 카테고리의 다른 객체에 붙여넣을 수 있다. 객체의 속성을 EPANET 내부 클립보드로 복사하려면:

1. 지도에서 객체를 마우스 오른쪽 버튼으로 클릭한다.
2. 나타나는 팝업 메뉴에서 **Copy** 를 선택한다.

복사한 속성을 객체에 붙여넣으려면:

1. 지도에서 객체를 마우스 오른쪽 버튼으로 클릭한다.
2. 나타나는 팝업 메뉴에서 **Paste** 를 선택한다.

## 6.7. 링크 형태 변경 및 방향 반전 (Shaping and Reversing Links)

링크는 방향 변화와 곡률을 더하는, 임의 개수의 직선 구간(straight-line segments)으로 이루어진 폴리라인(polyline)으로 그릴 수 있다. 지도에 링크를 한 번 그린 뒤에는, 이러한 구간을 정의하는 내부 점들을 추가·삭제·이동할 수 있다(Fig. 6.6 참조). 링크의 내부 점을 편집하려면:

1. Network Map 에서 편집할 링크를 선택하고 Map Toolbar 의 ![image94](https://usepa.github.io/EPANET2.2/_images/image13.png) 을 클릭한다(또는 Menu Bar 에서 **Edit >> Select Vertex** 를 선택하거나, 링크를 마우스 오른쪽 버튼으로 클릭하고 팝업 메뉴에서 **Vertices** 를 선택한다).
2. 마우스 포인터가 화살촉(arrow tip) 모양으로 바뀌고, 링크에 존재하는 정점(vertex)들이 주위에 작은 핸들(handle)과 함께 표시된다. 특정 정점을 선택하려면 그 위를 마우스로 클릭한다.
3. 링크에 새 정점을 추가하려면 마우스 오른쪽 버튼을 클릭하고 팝업 메뉴에서 **Add Vertex** 를 선택한다(또는 키보드의 **Insert** 키를 누른다).
4. 현재 선택된 정점을 삭제하려면 마우스 오른쪽 버튼을 클릭하고 팝업 메뉴에서 **Delete Vertex** 를 선택한다(또는 키보드의 **Delete** 키를 누른다).
5. 정점을 다른 위치로 이동하려면 마우스 왼쪽 버튼을 누른 채 새 위치로 드래그한다.
6. Vertex Selection(정점 선택) 모드에 있는 동안 다른 링크를 클릭하면 그 링크의 정점 편집을 시작할 수 있다. Vertex Selection 모드를 종료하려면 지도에서 마우스 오른쪽 버튼을 클릭하고 팝업 메뉴에서 **Quit Editing** 을 선택하거나, Map Toolbar 의 다른 버튼을 선택한다.

![Reshaping a Link in EPANET](https://usepa.github.io/EPANET2.2/_images/image65.png)

Fig. 6.6 Reshaping a Link (링크 형태 변경).

링크는 마우스 오른쪽 버튼으로 클릭하고 나타나는 팝업 메뉴에서 **Reverse** 를 선택하여 방향을 반전(즉, 양 끝 노드를 서로 바꿈)할 수도 있다. 이는 처음에 잘못된 방향으로 추가된 펌프와 밸브를 다시 정렬하는 데 유용하다.

## 6.8. 객체 삭제 (Deleting an Object)

객체를 삭제하려면:

1. 지도나 Data Browser 에서 객체를 선택한다.
2. 다음 중 하나를 수행한다.   Standard Toolbar 의 ![image96](https://usepa.github.io/EPANET2.2/_images/image44.png) 을 클릭 Data Browser 의 동일한 버튼을 클릭 키보드의 **Delete** 키를 누름

**참고**: 모든 삭제가 적용되기 전에 확인(confirmation)을 거치도록 요구할 수 있다. [Section 4.9](https://usepa.github.io/EPANET2.2/4_EPANET_workspace.html#sec-prog-pref) 에서 설명하는 Program Preferences 대화상자의 General Preferences 페이지를 참조한다.

## 6.9. 객체 이동 (Moving an Object)

노드나 라벨을 지도상의 다른 위치로 이동하려면:

1. 노드나 라벨을 선택한다.
2. 객체 위에서 마우스 왼쪽 버튼을 누른 채 새 위치로 드래그한다.
3. 왼쪽 버튼을 놓는다.

또는 Property Editor 에서 객체의 새 X, Y 좌표를 직접 입력할 수도 있다. 노드를 이동할 때마다 그에 연결된 모든 링크도 함께 이동한다.

## 6.10. 객체 그룹 선택 (Selecting a Group of Objects)

네트워크 지도의 불규칙한 영역 내에 있는 객체 그룹을 선택하려면:

1. **Edit >> Select Region** 을 선택하거나 Map Toolbar 의 ![image97](https://usepa.github.io/EPANET2.2/_images/image47.png) 을 클릭한다.
2. 지도에서 마우스 왼쪽 버튼을 다각형의 각 꼭짓점마다 차례로 클릭하여 관심 영역 주위에 다각형 경계선(polygon fence line)을 그린다.
3. 마우스 오른쪽 버튼을 클릭하거나 **Enter** 키를 눌러 다각형을 닫는다. **Escape** 키를 누르면 선택이 취소된다.

지도에서 현재 보이는 모든 객체를 선택하려면 **Edit >> Select All** 을 선택한다. (지도의 현재 보기 범위 밖에 있는 객체는 선택되지 않는다.)

객체 그룹을 선택한 뒤에는, 공통 속성을 편집하거나(다음 절 참조) 선택한 객체를 네트워크에서 삭제할 수 있다. 후자의 경우 ![image98](https://usepa.github.io/EPANET2.2/_images/image44.png) 을 클릭하거나 **Delete** 키를 누른다.

## 6.11. 객체 그룹 편집 (Editing a Group of Objects)

객체 그룹에 대해 속성을 편집하려면:

1. 앞 절에서 설명한 방법으로 편집할 객체 그룹이 포함될 지도 영역을 선택한다.
2. Menu Bar 에서 **Edit >> Group Edit** 를 선택한다.
3. 나타나는 Group Edit 대화상자에서 무엇을 편집할지 정의한다.

Fig. 6.7 에 표시된 Group Edit 대화상자는 선택된 객체 그룹에 대해 속성을 수정하는 데 사용된다. 이 대화상자를 사용하려면:

1. 편집할 객체 카테고리(Junctions 또는 Pipes)를 선택한다.
2. 편집 대상 객체를 제한하는 필터를 추가하려면 “with” 박스를 체크한다. 필터를 정의하는 속성(property), 관계(relation), 값(value)을 선택한다. 예를 들면 “with Diameter below 12” 와 같다.
3. 변경 유형을 선택한다 - Replace, Multiply, 또는 Add To.
4. 변경할 속성을 선택한다.
5. 기존 값을 대체(replace)·곱(multiply)·더할(add to) 값을 입력한다.
6. **OK** 를 클릭하여 그룹 편집을 실행한다.

![Group Edit Dialog Window in EPANET](https://usepa.github.io/EPANET2.2/_images/image66.png)

Fig. 6.7 Group Edit Dialog (그룹 편집 대화상자).
