# Roughness GA Optimizer

EPANET INP 파일의 Hazen-Williams C값을 GA로 보정하는 최적화 모듈입니다.

## 실행 기준

최적화는 `inp_file_opt_h.hist_id` 기준으로만 실행합니다.

```bat
python run_optimizer.py --config config.prob.json --hist-id 2
```

`hist_id`가 없으면 실행하지 않습니다.

## 동작 흐름

1. `inp_file_opt_h`에서 최적화 요청 이력을 조회합니다.
2. `inp_file_id + prev_rev_no` 기준으로 `inp_file_rev_h`의 원본 INP 파일을 찾습니다.
3. `option_snap`의 분석 매핑으로 demand 주입값과 압력 비교 지점을 구성합니다.
4. GA 최적화를 실행합니다.
5. 완료 후 같은 `inp_file_id`에 `max(rev_no) + 1` 리비전을 생성합니다.
6. `inp_file_m.curr_rev_no`와 `inp_file_opt_h.rev_no/status_cd/result_snap`을 갱신합니다.

## 주요 테이블

- `inp_file_m`: INP 파일 마스터, 현재 리비전 번호 관리
- `inp_file_rev_h`: INP 파일 리비전 이력
- `inp_file_opt_h`: 최적화 이력, 진행 상태, 결과 JSON
- `inp_anal_mapping`: GA 분석용 매핑
- `inp_vis_mapping`: 화면 표시 및 결과 비교용 매핑
- `TB_RAWDATA`: 태그별 실측 데이터

## API

```http
GET http://<internal-host>:30092/optimize/{histId}
GET http://<internal-host>:30092/health
```

