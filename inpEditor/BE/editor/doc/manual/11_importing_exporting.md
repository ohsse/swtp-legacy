> 원문: [EPANET 2.2 — 11. Importing and Exporting](https://usepa.github.io/EPANET2.2/11_importing_exporting.html)
> EPANET 2.2 공식 매뉴얼을 한국어로 정리한 문서입니다. 섹션 키워드·약어·파일 확장자는 원문을 유지합니다.

# 11. 가져오기 및 내보내기

*이 장에서는 프로젝트 시나리오(Project Scenario)의 개념을 소개하고, EPANET 이 이러한 시나리오 및 네트워크 지도, 전체 프로젝트 데이터베이스와 같은 기타 데이터를 어떻게 가져오기/내보내기 할 수 있는지를 설명한다.*

## 11.1. 프로젝트 시나리오

프로젝트 시나리오(Project Scenario)는 관망(pipe network)이 해석되는 현재 조건을 특징짓는 데이터의 부분집합으로 구성된다. 하나의 시나리오는 다음 데이터 범주 중 하나 이상으로 구성될 수 있다.

- 모든 노드(node)에서의 수요량(Demands; 기준 수요량과 모든 범주에 대한 time pattern)
- 모든 노드에서의 초기 수질(initial water quality)
- 모든 관(pipe)의 직경(diameter)
- 모든 관의 조도계수(roughness coefficient)
- 모든 관의 반응계수(reaction coefficient; bulk 및 wall)
- 단순 제어(simple controls) 및 규칙 기반 제어(rule-based controls)

EPANET 은 위에 나열된 데이터 범주의 일부 또는 전부를 기반으로 시나리오를 구성하고, 그 시나리오를 파일로 저장하며, 나중에 다시 읽어 들일 수 있다.

시나리오는 설계 및 운영 대안을 보다 효율적이고 체계적으로 분석할 수 있게 해 준다. 시나리오는 서로 다른 부하 조건(loading condition)의 영향을 검토하거나, 최적의 매개변수 추정값을 탐색하거나, 운영 정책의 변경을 평가하는 데 사용할 수 있다. 시나리오 파일은 ASCII 텍스트로 저장되며, EPANET 외부에서 텍스트 편집기나 스프레드시트 프로그램을 사용하여 생성하거나 수정할 수 있다.

## 11.2. 시나리오 내보내기

프로젝트 시나리오를 텍스트 파일로 내보내려면 다음과 같이 한다.

1. 메인 메뉴에서 **File >> Export >> Scenario** 를 선택한다.
2. 나타나는 Export Data 대화상자(그림 11.1 참조)에서 저장하려는 데이터의 종류를 선택한다.
3. 저장하려는 시나리오에 대한 설명을 Notes 메모 필드에 선택적으로 입력한다.
4. **OK** 버튼을 눌러 선택 사항을 확정한다.
5. 이어서 나타나는 Save 대화상자에서 시나리오 파일을 저장할 폴더와 이름을 선택한다. 시나리오 파일은 기본 확장자로 .SCN 을 사용한다.
6. **OK** 를 클릭하여 내보내기를 완료한다.

![Export Data Dialog in EPANET](https://usepa.github.io/EPANET2.2/_images/image93.png)

그림 11.1 Export Data 대화상자.

내보낸 시나리오는 다음 절에서 설명하는 것처럼 나중에 프로젝트로 다시 가져올 수 있다.

## 11.3. 시나리오 가져오기

파일로부터 프로젝트 시나리오를 가져오려면 다음과 같이 한다.

1. 메인 메뉴에서 **File >> Import >> Scenario** 를 선택한다.
2. 나타나는 Open File 대화상자를 사용하여 가져올 시나리오 파일을 선택한다. 대화상자의 Contents 패널은 파일을 선택할 때 해당 파일의 처음 몇 줄을 표시하여 원하는 파일을 찾는 데 도움을 준다.
3. **OK** 버튼을 클릭하여 선택을 확정한다.

시나리오 파일에 포함된 데이터는 현재 프로젝트에 있는 동일한 종류의 기존 데이터를 대체한다.

## 11.4. 부분 네트워크 가져오기

EPANET 은 관망의 기하학적 기술(geometric description)을 단순한 텍스트 형식으로 가져올 수 있는 기능을 갖추고 있다. 이 기술은 단순히 노드의 ID 라벨 및 지도 좌표(map coordinate)와, 링크(link)의 ID 라벨 및 끝점 노드(end node)만을 포함한다. 이는 CAD 및 GIS 패키지와 같은 다른 프로그램을 사용하여 네트워크의 기하 데이터를 디지타이징(digitize)한 다음 그 데이터를 EPANET 으로 전송하는 과정을 단순화한다.

부분 네트워크(partial network) 텍스트 파일의 형식은 다음과 같으며, 꺾쇠괄호(< >) 안의 텍스트는 파일의 해당 줄에 어떤 종류의 정보가 나타나는지를 설명한다.

```
[TITLE]

<optional description of the file>

[JUNCTIONS]

<ID label of each junction>

[PIPES]

<ID label of each pipe followed by the ID labels of its end
junctions>

[COORDINATES]

<Junction ID and its X and Y coordinates>

[VERTICES]

<Pipe ID and the X and Y coordinates of an intermediate vertex point>
```

여기서 절점(junction)과 관(pipe)만 표현된다는 점에 유의한다. 저수지(reservoir)나 펌프(pump)와 같은 다른 네트워크 요소는 절점이나 관으로 가져온 뒤 나중에 변환하거나, 또는 단순히 나중에 추가할 수 있다. CAD 나 GIS 패키지에서 생성된 데이터를 위에 제시된 형식의 텍스트 파일로 옮기는 것은 사용자의 책임이다.

이러한 부분적 표현 외에도, 부록 [Command Line EPANET](https://usepa.github.io/EPANET2.2/back_matter.html#command-line) 에 설명된 형식을 사용하여 네트워크의 완전한 명세(complete specification)를 파일에 담을 수도 있다. 이는 프로젝트를 텍스트 파일로 내보낼 때 EPANET 이 사용하는 것과 동일한 형식이다(아래 11.7 절 참조). 이 경우 파일에는 표고(elevation), 수요량(demand), 직경(diameter), 조도(roughness) 등 노드 및 링크 속성에 대한 정보도 포함된다.

## 11.5. 네트워크 지도 가져오기

텍스트 파일에 저장된 네트워크 지도(network map)의 좌표를 가져오려면 다음과 같이 한다.

1. 메인 메뉴에서 **File >> Import >> Map** 을 선택한다.
2. 나타나는 Open File 대화상자에서 지도 정보가 들어 있는 파일을 선택한다.
3. **OK** 를 클릭하여 현재 네트워크 지도를 파일에 기술된 지도로 대체한다.

## 11.6. 네트워크 지도 내보내기

현재 보이는 네트워크 지도(network map)의 화면은 Autodesk 의 DXF(Drawing Exchange Format) 형식, Windows 확장 메타파일(EMF) 형식, 또는 EPANET 자체의 ASCII 텍스트(map) 형식 중 하나를 사용하여 파일로 저장할 수 있다. DXF 형식은 많은 CAD(Computer Aided Design) 프로그램에서 읽을 수 있다. 메타파일은 워드 프로세싱 문서에 삽입하거나 그리기 프로그램에 불러와 크기 재조정(re-scaling) 및 편집을 할 수 있다. 두 형식 모두 벡터 기반이며, 서로 다른 축척으로 표시되더라도 해상도가 저하되지 않는다.

네트워크 지도를 전체 범위(full extent)로 DXF, 메타파일, 또는 텍스트 파일로 내보내려면 다음과 같이 한다.

1. 메인 메뉴에서 **File >> Export >> Map** 을 선택한다.
2. 나타나는 Map Export 대화상자(그림 11.2 참조)에서 지도를 저장할 형식을 선택한다.
3. DXF 형식을 선택하는 경우, DXF 파일에서 절점(junction)을 어떻게 표현할지 선택할 수 있다. 절점은 빈 원(open circle), 채워진 원(filled circle), 또는 채워진 사각형(filled square)으로 그릴 수 있다. 모든 DXF 리더가 채워진 원을 그리기 위해 DXF 파일에서 사용되는 명령을 인식할 수 있는 것은 아니다.
4. 형식을 선택한 후 OK 를 클릭하고, 나타나는 Save As 대화상자에서 파일 이름을 입력한다.

![Map Export Dialog in EPANET](https://usepa.github.io/EPANET2.2/_images/image94.png)

그림 11.2 Map Export 대화상자.

## 11.7. 텍스트 파일로 내보내기

프로젝트의 데이터를 텍스트 파일로 내보내려면 다음과 같이 한다.

1. 메인 메뉴에서 **File >> Export >> Network** 를 선택한다.
2. 나타나는 Save 대화상자에서 저장할 파일의 이름을 입력한다(기본 확장자는 .INP).
3. **OK** 를 클릭하여 내보내기를 완료한다.

생성된 파일은 ASCII 텍스트 형식으로 작성되며, 다양한 데이터 범주와 속성 라벨이 명확하게 식별된다. 이 파일은 **File >> Open** 또는 **File >> Import >> Network** 명령을 사용하여 나중에 해석을 위해 EPANET 으로 다시 읽어 들일 수 있다. 이 입력 형식을 사용한 완전한 네트워크 기술은 임의의 텍스트 편집기나 스프레드시트 프로그램을 사용하여 EPANET 외부에서 생성할 수도 있다. .INP 파일 형식의 완전한 명세는 부록 [Command Line EPANET](https://usepa.github.io/EPANET2.2/back_matter.html#command-line) 에 제시되어 있다.

데이터베이스의 보관용(archive) 버전을 이 형식으로 저장해 두면 사람이 읽을 수 있는 형태의 데이터에 접근할 수 있으므로 좋은 방법이다. 그러나 EPANET 의 일상적인 사용을 위해서는 **File >> Save** 또는 **File >> Save As** 명령을 사용하여 EPANET 의 특수 프로젝트 파일 형식(.NET 파일을 생성)으로 데이터를 저장하는 것이 더 효율적이다. 이 형식은 지도 범례(map legend)에 대해 선택된 색상과 범위, 적용 중인 지도 표시 옵션 집합, 등록된 검·보정(calibration) 데이터 파일의 이름, 선택된 인쇄 옵션 등 추가적인 프로젝트 정보를 포함한다.
