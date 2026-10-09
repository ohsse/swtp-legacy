# 관망해석 (feat. EPA2.2) w/ python

## 환경 설정 

----

### 파이썬 설치

1. 가상환경 작업 디렉토리 생성

    ```commandline
    C:\>cd mindone
    C:\mindone>mkdir venvs
    C:\mindone>cd venvs
    C:\mindone\venvs>python -m venv wntr4wn
    ```

2. 가상환경 진입

    ```commandline
    C:\mindone\venvs> cd wntr4wn/Scripts
    C:\mindone\venvs\wntr4wn\Scripts> activate
    (wntr4wn) C:\mindone\venvs\wntr4wn\Scripts>
    ```

3. 가상환경 종료

    ```commandline
    (wntr4wn) C:\mindone\venvs\wntr4wn\Scripts>deactivate
    C:\mindone\venvs\wntr4wn\Scripts>
    ```

4. 가상환경 플라스크 설치

    ```commandline
    (wntr4wn) C:\mindone\venvs\wntr4wn\Scripts>pip install flask
    ```

5. 가상환경 pip update

    ```commandline
    (wntr4wn) C:\mindone\venvs\wntr4wn\Scripts>python -m pip install --upgrade pip
    ```

6. wntr4wn 프로젝트 생성

    ```commandline
    C:\mindone\venvs\wntr4wn\Scripts>cd /mindone
    C:\mindone>mkdir flask
    C:\mindone>cd flask
    C:\mindone\flask>c:\mindone\venvs\wntr4wn\Scripts\activate
    (wntr4wn) C:\mindone\flask>mkdir wntr4wn
    (wntr4wn) C:\mindone\flask>cd wntr4wn
    (wntr4wn) C:\mindone\flask\wntr4wn>c:\mindone\venvs\wntr4wn\Scripts\deactivate
    ```

7. 가상환경 자동진입 설정

    ```commandline
    C:\mindone>cd /mindone/venvs
    wntr4wn-start.bat 파일 생성
    @echo off
    cd c:/mindone/flask/wntr4wn
    c:/mindone/venvs/wntr4wn/Scripts/activate
    ```

8. 환경변수 등록
   - 윈도우 > 실행 > sysdm.cpl > 고급 > 환경변수 > Path > 편집 > 새로만들기 > C:\mindone\venvs > 확인

9. 배치파일 실행하여 가상환경 진입

    ```commandline
    c:\>wntr4wn-start
    (wntr4wn) c:\mindone\flask\wntr4wn>
    ```

10. 플라스크 디버그모드 설정

    ```commandline
    (wntr4wn) c:\mindone\flask\wntr4wn>set FLASK_DEBUG=true
    ```

11. wntr Lib 설치

    ```commandline
    (wntr4wn) c:\mindone\flask\wntr4wn>pip install numpy
    (wntr4wn) c:\mindone\flask\wntr4wn>pip install pandas
    (wntr4wn) c:\mindone\flask\wntr4wn>pip install scipy
    (wntr4wn) c:\mindone\flask\wntr4wn>pip install networkx
    (wntr4wn) c:\mindone\flask\wntr4wn>pip install matplotlib
    (wntr4wn) c:\mindone\flask\wntr4wn>pip install pyodbc
    (wntr4wn) c:\mindone\flask\wntr4wn>pip install cloudpickle
    (wntr4wn) c:\mindone\flask\wntr4wn>pip install joblib
    (wntr4wn) c:\mindone\flask\wntr4wn>pip install pygad
    (wntr4wn) c:\mindone\flask\wntr4wn>pip install scikit-learn
    (wntr4wn) c:\mindone\flask\wntr4wn>pip install seaborn
    ```

12. 플라스크 실행

    ```commandline
    (wntr4wn) c:\mindone\flask\wntr4wn>flask run
    ```

### 파이썬 티베로 ODBC 설정
1. C:\ 압축풀기
   - `tibero6-bin-FS07_CS_2005-windows64_2008-254895-20221012002446.zip`

2. 환경변수에 'TB_HOME' 추가

    ```commandline
    TB_HOME
    C:\tibero6
    ```
3. tibero odbc 설치

    ```commandline
    C:\tibero6>%TB_HOME%\bin\tbodbc_driver_installer_6_64.exe -i
    ```

## 운영환경 실행

----

```commandline
c:\> flask run --host=0.0.0.0
```

## Build 방법

----

```shell
python setup.py build

```

생성된 build 폴더에 wntr 폴더를 현재위치로 덮어쓰기


## .INP 파일 인코딩 정보 수정 
---

.inp 파일의 인코딩이 UTF-8일 경우의 소스 

```python
# io.py line 285
  with io.open(filename, 'r', encoding='utf-8') as f:

```

.inp 파일의 인코딩이 euc-kr인 경우 

```python
# io.py line 285
  with io.open(filename, 'r') as f:

```
