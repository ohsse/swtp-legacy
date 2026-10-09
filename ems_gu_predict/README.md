# deepEMS — 군산 EMS 수위 예측/추천 시스템

오식도배수지 수위(H7) 관리를 위한 예측·추천 파이프라인. Stage1(Stage1 NN,
O7/Q7 등 목표 변수 예측) → Stage2(H7 = 물리 질량보존 + GBR 잔차보정
하이브리드) → Stage3(목표수위 대비 레버 조정값 추천, `Q_GunS`/`V2`/`V4`)
3단계로 구성된다.

## 실행 전 준비

1. `configs/db_connections.json` — 원본 데이터 읽기용 DB 접속정보 (prod/dev/dev-server/local)
2. `configs/db_upload_connections.json` — 결과 업로드용 DB 접속정보 (dev-server/prod, `db_upload_connections.example.json` 참고)
3. `pip install -r requirements.txt` (외부망일 때)
4. 운영 DB `tb_ctr_tnk_rst` 테이블이 최신 wide 스키마(`DSTRB_ID, RGSTR_TIME, VALUE_5min..VALUE_6h`)인지 확인 — 아니면 재생성 필요 (`readme.txt` 참고)

## 실행

```powershell
# 실제 운영 (5분 주기 무한 루프, tb_ctr_tnk_rst에 업로드)
python scripts\harness\schedule.py --mode prod `
  --stage1-run-dir .\runs\gu_db_noq8_h6 `
  --source-cfg configs\gu_db_noq8_h6.yaml `
  --offline-artifacts models\offline_artifacts.joblib

# 백테스트 (DB에 안 씀, 과거 구간 재현)
python scripts\harness\schedule.py --mode dev `
  --stage1-run-dir .\runs\gu_db_noq8_h6 `
  --source-cfg configs\gu_db_noq8_h6.yaml `
  --offline-artifacts models\offline_artifacts.joblib `
  --backtest-start 2025-06-01 --backtest-end 2025-06-02 `
  --stride-minutes 60 --out-csv backtest_dev.csv
```

`--mode dev`는 `upload.py` 자체를 import하지 않아 DB에 절대 쓰지 않는다.
`--mode dev-server`는 실시간 루프 + 실제 업로드까지 하되 dev-server DB로
보낸다(운영 배포 전 최종 검증용). 옵션 전체는 `python scripts\harness\
schedule.py --help` 참고.

## 구조

```
DeepEMS_GU/
├── configs/                  # 학습/DB 접속 설정 (db_*connections.json은 git 제외)
├── models/offline_artifacts.joblib   # Stage2/3 산출물 (면적/레버게인/잔차모델, scripts/train.py가 생성)
├── runs/gu_db_noq8_h6/       # Stage1 NN 학습 산출물 (가중치/config)
├── scripts/
│   ├── harness/              # 실시간 스케줄러 (preprocess/analysis/upload/schedule/train)
│   ├── candidates/           # 후보 모델(Informer 등) 학습 하네스
│   ├── ALGORITHM.md          # 사이클마다 어떤 함수가 무엇을 계산하는지 요약
│   └── DEVNOTES.md           # scripts/ 변경 이력
├── src/deepems/               # 학습/추론/추천 핵심 라이브러리
└── taglist/GU_taglist.xlsx   # 태그 정의 (feature/target/레버 역할)
```

## 자세한 내용

- 알고리즘 설계 근거/실측 검증: `scripts/ALGORITHM.md`
- `scripts/` 변경 이력(버전별): `scripts/DEVNOTES.md`
- 정확한 실행 명령 예시: `readme.txt`
