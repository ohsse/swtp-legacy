from __future__ import annotations

import copy
from dataclasses import dataclass
import logging
from pathlib import Path
import re
import tempfile
from typing import Callable, Optional

import numpy as np
import pandas as pd
import pygad
import wntr
from wntr.epanet.util import FlowUnits, HydParam, to_si

from models import ObservationPoint


logger = logging.getLogger(__name__)


@dataclass
class MultiplierConfig:
    low: float = 0.7
    high: float = 1.3
    steps: int = 121


@dataclass
class RoughnessConfig:
    low: float = 60.0
    high: float = 160.0


@dataclass
class GaConfig:
    generations: int = 30
    population: int = 24
    seed: int = 0
    mutation_probability: float = 0.2
    crossover_probability: float = 0.8


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def capture_original_roughness(
    wn: wntr.network.WaterNetworkModel,
    groups: dict[str, list[str]],
) -> dict[str, float]:
    original: dict[str, float] = {}
    for pipe_ids in groups.values():
        for pipe_id in pipe_ids:
            model_id = alias_for(pipe_id)
            if model_id not in wn.link_name_list:
                continue
            link = wn.get_link(model_id)
            if getattr(link, "link_type", "") == "Pipe":
                original[pipe_id] = float(link.roughness)
    return original


def apply_multipliers(
    wn: wntr.network.WaterNetworkModel,
    groups: dict[str, list[str]],
    original_roughness: dict[str, float],
    multipliers: dict[str, float],
    roughness_config: RoughnessConfig,
) -> dict[str, float]:
    applied: dict[str, float] = {}
    for group_name, pipe_ids in groups.items():
        multiplier = float(multipliers.get(group_name, 1.0))
        for pipe_id in pipe_ids:
            if pipe_id not in original_roughness:
                continue
            link = wn.get_link(alias_for(pipe_id))
            new_c = original_roughness[pipe_id] * multiplier
            new_c = clamp(new_c, roughness_config.low, roughness_config.high)
            link.roughness = new_c
            applied[pipe_id] = new_c
    return applied


def run_epanet(wn: wntr.network.WaterNetworkModel):
    sim = wntr.sim.EpanetSimulator(wn)
    return sim.run_sim()


def flow_cmh_to_si(value: float) -> float:
    return to_si(FlowUnits.CMH, float(value), HydParam.Flow)


def apply_demand_overrides(
    wn: wntr.network.WaterNetworkModel,
    demand_overrides_si: dict[str, float],
) -> list[str]:
    skipped: list[str] = []
    for node_id, demand_si in demand_overrides_si.items():
        model_id = alias_for(node_id)
        if model_id not in wn.junction_name_list:
            skipped.append(node_id)
            continue
        junction = wn.get_node(model_id)
        demand_list = getattr(junction, "demand_timeseries_list", None)
        if demand_list and len(demand_list) > 0:
            demand_list[0].base_value = float(demand_si)
        else:
            junction.add_demand(base=float(demand_si), pattern=None, category="MeasuredDemand")
    return skipped


# EPANET 2.2 의 ID 최대 길이(MAXID). C 문자열 기준이라 "글자 수"가 아니라 "바이트 수"다.
EPANET_MAX_ID_BYTES = 31

# 결과 INP 를 쓸 때 사용하는 인코딩. 업로드 원본·BE(InpWriter) 와 동일하게 CP949 다.
# (한글 ID 의 바이트 길이가 원본과 같아져야 EPANET MAXID 를 넘지 않는다. write_inp() 참조)
OUTPUT_ENCODING = "cp949"

# INP 한 줄에서 ID 가 될 수 있는 토큰(공백/탭/세미콜론이 구분자).
TOKEN_PATTERN = re.compile(r"[^\s;]+")

# ID 를 정의하는 섹션. 이 섹션 데이터 행의 첫 토큰이 다른 섹션에서 참조되는 ID 다.
ID_DEFINING_SECTIONS = frozenset(
    {
        "[JUNCTIONS]",
        "[RESERVOIRS]",
        "[TANKS]",
        "[PIPES]",
        "[PUMPS]",
        "[VALVES]",
        "[PATTERNS]",
        "[CURVES]",
    }
)

# 원본 ID ↔ 짧은 ASCII 별칭. 1회 실행 = 1개 INP 기준이라 모듈 전역으로 누적한다.
_alias_by_id: dict[str, str] = {}
_id_by_alias: dict[str, str] = {}


def alias_for(object_id: str) -> str:
    """길이 초과로 치환된 ID 면 별칭을, 아니면 원래 ID 를 그대로 돌려준다."""

    return _alias_by_id.get(object_id, object_id)


def find_long_ids(text: str) -> list[str]:
    """UTF-8 기준으로 EPANET ID 길이 제한을 넘는 ID 를 정의 순서대로 모은다."""

    section = ""
    long_ids: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("["):
            section = line.upper()
            continue
        if section not in ID_DEFINING_SECTIONS:
            continue
        object_id = line.split()[0]
        if len(object_id.encode("utf-8")) <= EPANET_MAX_ID_BYTES:
            continue
        if object_id not in long_ids:
            long_ids.append(object_id)
    return long_ids


def replace_ids(text: str, mapping: dict[str, str]) -> str:
    """공백/탭/세미콜론으로 끊긴 토큰 단위로만 치환한다(부분 문자열 오치환 방지)."""

    if not mapping:
        return text
    return re.sub(TOKEN_PATTERN, lambda m: mapping.get(m.group(0), m.group(0)), text)


def shorten_long_ids(text: str) -> str:
    """
    EPANET 이 거부하는 '너무 긴 ID' 를 짧은 ASCII 별칭으로 바꾼다.

    WNTR 은 EPANET 에 넘길 임시 INP 를 항상 UTF-8 로 쓴다. 한글은 CP949 에서 2바이트,
    UTF-8 에서 3바이트라 원본에서는 멀쩡하던 한글 11자 ID(CP949 22바이트)가 UTF-8 로는
    33바이트가 되어 MAXID(31바이트)를 넘고, ENopen 이 (Error 252) invalid ID name 으로
    실패한다. 해석 결과는 ID 이름에 의존하지 않으므로 여기서 별칭으로 바꾸고,
    결과 INP 를 쓸 때 write_inp() 가 원래 이름으로 되돌린다.

    ※ 이 치환은 GA 가 돌리는 EPANET 실행에만 적용되는 우회책이다. 결과 INP 에는 원래 이름이
      돌아가므로, 그 파일을 UTF-8 로 남기면 같은 문제가 읽는 쪽에서 재현된다.
      그래서 write_inp() 는 결과를 CP949 로 기록한다.
    """

    long_ids = find_long_ids(text)
    if not long_ids:
        return text

    mapping: dict[str, str] = {}
    index = 0
    for object_id in long_ids:
        while True:
            index += 1
            alias = f"LONGID{index:04d}"
            if alias not in _id_by_alias and alias not in text:
                break
        mapping[object_id] = alias

    _alias_by_id.update(mapping)
    _id_by_alias.update({alias: object_id for object_id, alias in mapping.items()})
    logger.warning(
        "EPANET ID 길이 제한(%s바이트) 초과 ID %s건을 임시 치환: %s",
        EPANET_MAX_ID_BYTES,
        len(mapping),
        mapping,
    )
    return replace_ids(text, mapping)


def make_wntr_readable_inp(inp_path: str) -> str:
    """
    WNTR reads INP files as UTF-8.

    Many Korean EPANET files are saved as CP949/EUC-KR, so create a temporary
    UTF-8 copy before passing the file to WNTR. The original file is untouched.
    """

    source = Path(inp_path)
    data = source.read_bytes()
    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = data.decode("utf-8", errors="replace")

    temp_dir = Path(tempfile.gettempdir()) / "roughness_ga_optimizer"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"{source.stem}_utf8.inp"
    temp_path.write_text(shorten_long_ids(text), encoding="utf-8")
    return str(temp_path)


def comparison_result_time(results) -> object:
    """Use the final EPANET result time for measured/simulated comparison."""

    return results.node["pressure"].index[-1]


def nearest_result_time(results, requested_time: int) -> object:
    """Return the requested EPANET result time, or the nearest available time."""

    index = results.node["pressure"].index
    if requested_time in index:
        return requested_time
    return min(index, key=lambda result_time: abs(int(result_time) - int(requested_time)))


class RoughnessGaOptimizer:
    def __init__(
        self,
        inp_path: str,
        groups: dict[str, list[str]],
        observations: list[ObservationPoint],
        multiplier_config: MultiplierConfig,
        roughness_config: RoughnessConfig,
        ga_config: GaConfig,
        pressure_compare_scale: float = 0.1,
        objective_metric: str = "rmse",
        comparison_times_sec: Optional[list[int]] = None,
        demand_overrides_si: Optional[dict[str, float]] = None,
        progress_callback: Optional[Callable[[int, int, float, float, float], None]] = None,
    ):
        self.inp_path = inp_path
        self.groups = {name: ids for name, ids in groups.items() if ids}
        self.group_list = sorted(self.groups.keys())
        self.observations = observations
        self.multiplier_config = multiplier_config
        self.roughness_config = roughness_config
        self.ga_config = ga_config
        self.pressure_compare_scale = pressure_compare_scale
        self.comparison_times_sec = sorted(
            int(time_sec) for time_sec in (comparison_times_sec or [])
        )
        self.objective_metric = objective_metric.lower()
        self.demand_overrides_si = demand_overrides_si or {}
        self.progress_callback = progress_callback
        if self.objective_metric not in {"rmse", "r2", "corr_r2"}:
            raise ValueError("objective_metric must be 'rmse', 'r2', or 'corr_r2'.")

        self.wntr_inp_path = make_wntr_readable_inp(inp_path)
        logger.info("wntr_readable_inp_path=%s", self.wntr_inp_path)
        self.wn_base = wntr.network.WaterNetworkModel(self.wntr_inp_path)
        if self.comparison_times_sec:
            self.wn_base.options.time.duration = max(self.comparison_times_sec)
            logger.info("comparison_times_sec=%s", self.comparison_times_sec)
        if self.demand_overrides_si:
            skipped = [
                node_id
                for node_id in self.demand_overrides_si
                if alias_for(node_id) not in self.wn_base.junction_name_list
            ]
            if skipped:
                logger.warning("demand_override_nodes_not_found=%s", skipped)
            logger.info(
                "demand_override_count=%s",
                len(self.demand_overrides_si) - len(skipped),
            )
        self.original_roughness = capture_original_roughness(self.wn_base, self.groups)

        if not self.original_roughness:
            raise ValueError("최적화 대상 관로 C값을 찾지 못했습니다. 그룹 pipe_id와 INP link_id를 확인하세요.")

        self.best_multipliers: dict[str, float] = {}
        self.best_rmse: float = float("inf")
        self.best_applied_roughness: dict[str, float] = {}
        self._last_logged_generation = -1
        np.random.seed(self.ga_config.seed)

    def solution_to_multipliers(self, solution) -> dict[str, float]:
        return {
            group_name: float(solution[index])
            for index, group_name in enumerate(self.group_list)
        }

    def evaluate_solution(self, solution) -> float:
        measured, simulated = self.solution_pressure_arrays(solution)
        if measured.size == 0:
            return float("inf")

        residuals = simulated - measured
        return float(np.sqrt(np.mean(np.square(residuals))))

    def r2_solution(self, solution) -> float:
        measured, simulated = self.solution_pressure_arrays(solution)
        if measured.size == 0:
            return float("-inf")

        ss_res = float(np.sum(np.square(simulated - measured)))
        ss_tot = float(np.sum(np.square(measured - np.mean(measured))))
        if ss_tot == 0:
            return float("-inf")

        return 1.0 - ss_res / ss_tot

    def corr_r2_solution(self, solution) -> float:
        measured, simulated = self.solution_pressure_arrays(solution)
        if measured.size < 2:
            return float("-inf")
        if np.std(measured) == 0 or np.std(simulated) == 0:
            return float("-inf")

        corr = float(np.corrcoef(measured, simulated)[0, 1])
        return corr * corr

    def solution_pressure_arrays(self, solution) -> tuple[np.ndarray, np.ndarray]:
        multipliers = self.solution_to_multipliers(solution)
        wn = self.evaluation_network()
        apply_multipliers(
            wn=wn,
            groups=self.groups,
            original_roughness=self.original_roughness,
            multipliers=multipliers,
            roughness_config=self.roughness_config,
        )

        results = run_epanet(wn)
        result_times = self.result_times(results)

        measured_values: list[float] = []
        simulated_values: list[float] = []
        for requested_time, result_time in result_times:
            pressure_row = results.node["pressure"].loc[result_time]
            for obs in self.observations:
                if not obs.pressure_node_id:
                    continue
                node_id = alias_for(obs.pressure_node_id)
                if node_id not in pressure_row.index:
                    continue
                measured = self.observed_pressure(obs, requested_time)
                if measured is None:
                    continue

                sim_pressure = float(pressure_row[node_id]) * self.pressure_compare_scale
                simulated_values.append(sim_pressure)
                measured_values.append(float(measured))

        return np.array(measured_values), np.array(simulated_values)

    def evaluation_network(self) -> wntr.network.WaterNetworkModel:
        wn = copy.deepcopy(self.wn_base)
        if self.demand_overrides_si:
            apply_demand_overrides(wn, self.demand_overrides_si)
        return wn

    def result_times(self, results) -> list[tuple[int, object]]:
        if not self.comparison_times_sec:
            result_time = comparison_result_time(results)
            return [(int(result_time), result_time)]
        return [
            (requested_time, nearest_result_time(results, requested_time))
            for requested_time in self.comparison_times_sec
        ]

    def observed_pressure(self, obs: ObservationPoint, result_time: int) -> Optional[float]:
        if obs.observed_pressure_by_time:
            return obs.observed_pressure_by_time.get(int(result_time))
        return obs.observed_pressure

    def observed_flow(self, obs: ObservationPoint, result_time: int) -> Optional[float]:
        if obs.observed_flow_by_time:
            return obs.observed_flow_by_time.get(int(result_time))
        return obs.observed_flow

    def objective_score(self, solution) -> float:
        if self.objective_metric == "corr_r2":
            return self.corr_r2_solution(solution)

        if self.objective_metric == "r2":
            return self.r2_solution(solution)

        rmse = self.evaluate_solution(solution)
        return -rmse if np.isfinite(rmse) else -1e12

    def baseline_solution(self) -> list[float]:
        """Return the no-change multiplier solution."""

        return [1.0 for _ in self.group_list]

    def baseline_rmse(self) -> float:
        """Calculate RMSE before optimization, using original C values."""

        return self.evaluate_solution(self.baseline_solution())

    def baseline_r2(self) -> float:
        """Calculate R-squared before optimization, using original C values."""

        return self.r2_solution(self.baseline_solution())

    def baseline_corr_r2(self) -> float:
        """Calculate correlation R-squared before optimization."""

        return self.corr_r2_solution(self.baseline_solution())

    def fitness_func(self, ga_instance, solution, solution_idx):
        score = self.objective_score(solution)
        return score if np.isfinite(score) else -1e12

    def run(self) -> tuple[dict[str, float], float]:
        before_rmse = self.baseline_rmse()
        before_r2 = self.baseline_r2()
        before_corr_r2 = self.baseline_corr_r2()
        logger.info(
            "GA start: inp=%s groups=%s tagged_pipes=%s observations=%s generations=%s population=%s objective_metric=%s",
            self.inp_path,
            len(self.group_list),
            len(self.original_roughness),
            self.pressure_observation_count(),
            self.ga_config.generations,
            self.ga_config.population,
            self.objective_metric,
        )
        logger.info("baseline_rmse=%.6f", before_rmse)
        logger.info("baseline_standard_r2=%.6f", before_r2)
        logger.info("baseline_corr_r2=%.6f", before_corr_r2)

        gene_space = [
            np.linspace(
                self.multiplier_config.low,
                self.multiplier_config.high,
                self.multiplier_config.steps,
            )
            for _ in self.group_list
        ]

        ga = pygad.GA(
            num_generations=self.ga_config.generations,
            sol_per_pop=self.ga_config.population,
            num_parents_mating=max(2, self.ga_config.population // 3),
            num_genes=len(self.group_list),
            gene_space=gene_space,
            fitness_func=self.fitness_func,
            mutation_probability=self.ga_config.mutation_probability,
            crossover_probability=self.ga_config.crossover_probability,
            allow_duplicate_genes=True,
            random_seed=self.ga_config.seed,
            on_generation=self._on_generation,
        )
        ga.run()
        solution, _fitness, _idx = ga.best_solution()

        self.best_multipliers = self.solution_to_multipliers(solution)
        self.best_rmse = self.evaluate_solution(solution)
        best_r2 = self.r2_solution(solution)
        best_corr_r2 = self.corr_r2_solution(solution)
        best_objective_score = self.objective_score(solution)
        improvement = before_rmse - self.best_rmse
        improvement_pct = 0.0 if before_rmse == 0 else improvement / before_rmse * 100.0
        logger.info(
            "GA completed: baseline_rmse=%.6f best_rmse=%.6f baseline_standard_r2=%.6f best_standard_r2=%.6f baseline_corr_r2=%.6f best_corr_r2=%.6f objective_metric=%s best_objective_score=%.6f improvement=%.6f improvement_pct=%.2f",
            before_rmse,
            self.best_rmse,
            before_r2,
            best_r2,
            before_corr_r2,
            best_corr_r2,
            self.objective_metric,
            best_objective_score,
            improvement,
            improvement_pct,
        )
        return self.best_multipliers, self.best_rmse

    def _on_generation(self, ga_instance) -> None:
        generation = int(ga_instance.generations_completed)
        if generation == self._last_logged_generation:
            return

        self._last_logged_generation = generation
        solution, fitness, _idx = ga_instance.best_solution()
        rmse = self.evaluate_solution(solution)
        r2 = self.r2_solution(solution)
        corr_r2 = self.corr_r2_solution(solution)
        logger.info(
            "GA generation %s/%s: best_rmse=%.6f best_standard_r2=%.6f best_corr_r2=%.6f best_fitness=%.6f",
            generation,
            self.ga_config.generations,
            rmse,
            r2,
            corr_r2,
            fitness,
        )
        if self.progress_callback:
            self.progress_callback(
                generation,
                self.ga_config.generations,
                rmse,
                r2,
                corr_r2,
            )

    def final_network(self) -> wntr.network.WaterNetworkModel:
        if not self.best_multipliers:
            raise RuntimeError("run()을 먼저 실행해야 합니다.")
        wn = copy.deepcopy(self.wn_base)
        if self.demand_overrides_si:
            skipped = apply_demand_overrides(wn, self.demand_overrides_si)
            logger.info(
                "final_inp_demand_overrides_applied=%s skipped=%s",
                len(self.demand_overrides_si) - len(skipped),
                skipped,
            )
        self.best_applied_roughness = apply_multipliers(
            wn=wn,
            groups=self.groups,
            original_roughness=self.original_roughness,
            multipliers=self.best_multipliers,
            roughness_config=self.roughness_config,
        )
        return wn

    def build_pipe_change_table(self) -> pd.DataFrame:
        rows = []
        for group_name, pipe_ids in self.groups.items():
            multiplier = self.best_multipliers.get(group_name, 1.0)
            for pipe_id in pipe_ids:
                if pipe_id not in self.original_roughness:
                    continue
                original_c = self.original_roughness[pipe_id]
                optimized_c = self.best_applied_roughness.get(pipe_id)
                if optimized_c is None:
                    optimized_c = clamp(
                        original_c * multiplier,
                        self.roughness_config.low,
                        self.roughness_config.high,
                    )
                rows.append(
                    {
                        "pipe_id": pipe_id,
                        "group": group_name,
                        "multiplier": multiplier,
                        "original_c": original_c,
                        "optimized_c": optimized_c,
                        "delta_c": optimized_c - original_c,
                    }
                )
        return pd.DataFrame(rows)

    def build_error_tables(
        self,
        wn: wntr.network.WaterNetworkModel,
        observations: Optional[list[ObservationPoint]] = None,
        apply_demand: bool = True,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        eval_wn = copy.deepcopy(wn)
        if apply_demand and self.demand_overrides_si:
            apply_demand_overrides(eval_wn, self.demand_overrides_si)
        results = run_epanet(eval_wn)
        result_times = self.result_times(results)
        target_observations = observations or self.observations

        pressure_rows = []
        flow_rows = []
        for requested_time, result_time in result_times:
            pressure_row = results.node["pressure"].loc[result_time]
            flow_row = results.link["flowrate"].loc[result_time]
            for obs in target_observations:
                node_id = alias_for(obs.pressure_node_id) if obs.pressure_node_id else None
                if node_id and node_id in pressure_row.index:
                    sim = float(pressure_row[node_id]) * self.pressure_compare_scale
                    measured = self.observed_pressure(obs, requested_time)
                    pressure_rows.append(
                        {
                            "analysis_time_sec": requested_time,
                            "location_name": obs.location_name,
                            "node_id": obs.pressure_node_id,
                            "tag": obs.pressure_tag,
                            "measured": measured,
                            "simulated": sim,
                            "error": None if measured is None else sim - measured,
                            "error_rate_pct": None if not measured else (sim - measured) / measured * 100.0,
                        }
                    )

                link_id = alias_for(obs.flow_link_id) if obs.flow_link_id else None
                if link_id and link_id in flow_row.index:
                    sim_cmh = float(flow_row[link_id]) * 3600.0
                    measured = self.observed_flow(obs, requested_time)
                    flow_rows.append(
                        {
                            "analysis_time_sec": requested_time,
                            "location_name": obs.location_name,
                            "link_id": obs.flow_link_id,
                            "tag": obs.flow_tag,
                            "measured": measured,
                            "simulated": sim_cmh,
                            "error": None if measured is None else sim_cmh - measured,
                            "error_rate_pct": None if not measured else (sim_cmh - measured) / measured * 100.0,
                        }
                    )

        return pd.DataFrame(pressure_rows), pd.DataFrame(flow_rows)

    def pressure_observation_count(self) -> int:
        if not self.comparison_times_sec:
            return sum(1 for obs in self.observations if obs.observed_pressure is not None)
        return sum(
            1
            for obs in self.observations
            for result_time in self.comparison_times_sec
            if self.observed_pressure(obs, result_time) is not None
        )


def restore_long_ids(text: str) -> str:
    """shorten_long_ids() 가 붙인 별칭을 원래 ID 로 되돌린다."""

    if not _id_by_alias:
        return text
    return replace_ids(text, _id_by_alias)


def write_inp(wn: wntr.network.WaterNetworkModel, output_path: str) -> None:
    """
    최적화 결과 INP 를 기록한다(별칭 원복 + CP949 인코딩).

    WNTR 은 INP 를 항상 UTF-8 로 쓰지만, 결과 파일은 원본·BE(InpWriter) 와 동일하게
    CP949 로 남긴다. 한글이 CP949 2바이트 / UTF-8 3바이트이기 때문이다 — UTF-8 로 두면
    원본에서 멀쩡하던 한글 11자 ID(CP949 22바이트)가 33바이트가 되어 EPANET
    MAXID(31바이트)를 넘는다. 이 파일을 읽는 쪽이 shorten_long_ids() 같은 별칭 치환 없이
    그대로 EPANET 에 넘기면 (Error 252) invalid ID name 으로 실패한다.
    CP949 로 쓰면 원본과 바이트 길이가 같아져 그 문제가 생기지 않는다.

    ※ 읽는 쪽이 EPANET 에 넘기기 전에 UTF-8 로 재작성한다면 이 조치만으로는 부족하다
      (그쪽에서도 CP949 를 유지하거나 별칭 치환을 해야 한다).
    """

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    wntr.network.write_inpfile(wn, output_path)

    text = restore_long_ids(path.read_text(encoding="utf-8"))
    try:
        path.write_bytes(text.encode(OUTPUT_ENCODING))
    except UnicodeEncodeError as exc:
        # 오래 걸린 최적화 결과를 통째로 잃지 않도록 UTF-8 로 대체하되, 조용히 넘어가지 않는다.
        logger.error(
            "결과 INP 를 %s 로 기록할 수 없어 UTF-8 로 대체한다(문자 %r, 위치 %s). "
            "UTF-8 INP 는 긴 한글 ID 에서 EPANET MAXID(%s바이트)를 넘을 수 있다.",
            OUTPUT_ENCODING,
            text[exc.start:exc.end],
            exc.start,
            EPANET_MAX_ID_BYTES,
        )
        path.write_bytes(text.encode("utf-8"))
