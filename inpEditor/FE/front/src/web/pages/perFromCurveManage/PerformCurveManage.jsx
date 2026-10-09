import CommonButton from '@/web/components/common/CommonButton.jsx';
import CommonCard from '@/web/components/common/CommonCard.jsx';
import CommonChart from '@/web/components/common/CommonChart.jsx';
import CommonDateTimeRangePicker from '@/web/components/common/CommonDateTimeRangePicker.jsx';
import CommonTable from '@/web/components/common/CommonTable.jsx';
import { showToast } from '@/web/components/common/CommonToast.jsx';
import performApi from '@/web/js/apis/performApi.js';
import PerformCurveCustomLegend, {
	performCurveCustomLegendConfig,
	performCurveLegendShapePlugin,
} from '@/web/pages/perFromCurveManage/components/PerformCurveCustomLegend.jsx';
import dayjs from 'dayjs';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ChartWrapper } from 'stz-chart-maker';

const DATE_INPUT_FORMAT = 'YYYY-MM-DD';
const MAX_CURVE_INPUT_POINT_COUNT = 5;

const metricColSeq = [
	{ key: 'beforeLabel', colNm: '', flex: 0.8, minWidth: 98 },
	{ key: 'beforeValue', colNm: '', flex: 1, minWidth: 112, editable: false },
	{ key: 'afterLabel', colNm: '', flex: 0.8, minWidth: 98 },
	{
		key: 'afterValue',
		colNm: '',
		flex: 1,
		minWidth: 112,
		editable: false,
	},
];

const metricRows = [
	{ id: 'data', beforeLabel: '데이터 수', beforeValue: null, afterLabel: '', afterValue: '' },
	{ id: 'rmse', beforeLabel: '갱신 전 평균 오차', beforeValue: '7.1%', afterLabel: '갱신 후 평균 오차', afterValue: '' },
	{
		id: 'power',
		beforeLabel: '갱신 전 전력 원단위',
		beforeValue: '0.182 kWh/m³',
		afterLabel: '갱신 후 전력 원단위',
		afterValue: '',
	},
	{
		id: 'loss',
		beforeLabel: '갱신 전 부하비 단위',
		beforeValue: '16.1원/m³',
		afterLabel: '갱신 후 부하비 단위',
		afterValue: '',
	},
	{
		id: 'priority',
		beforeLabel: '갱신 전 우선순위',
		beforeValue: '2순위',
		afterLabel: '갱신 후 우선순위',
		afterValue: '',
	},
];

const curveFlowStatusLabel = {
	READY: '조합 선택',
	DATA_LOADED: '데이터 갱신',
	EDITING: '편집 중',
	EXTRACTED: '추출 완료',
	SAVED: '저장 완료',
};

// 펌프조합 식별자는 대리키가 아니라 TB_PUMP_CAL 의 (PUMP_GRP, C_IDX) 두 값이다.
const OPERATION_PUMP_GRP_KEYS = ['pumpGrp', 'pump_grp', 'PUMP_GRP'];
const OPERATION_COMB_IDX_KEYS = ['combIdx', 'comb_idx', 'cIdx', 'C_IDX'];
const OPERATION_RUN_COUNT_KEYS = ['runCount', 'pumpCount', 'operPumpCnt', 'operPumpCount', 'pumpCnt'];
const OPERATION_PUMP_SET_KEYS = ['pumpSet', 'pumpComb', 'pumpCombination', 'combNm', 'combName', 'pumpCombNm'];
const OPERATION_RUN_MINUTES_KEYS = ['runMinutes'];
const OPERATION_POWER_UNIT_KEYS = ['powerUnit'];
const OPERATION_POWER_COST_UNIT_KEYS = ['powerCostUnit'];
const OPERATION_AVG_ERROR_RATE_KEYS = ['avgErrorRate'];
const OPERATION_PRIORITY_KEYS = ['priority', 'pumpPriority'];
// 가변속 펌프의 목표 주파수(펌프IDX:Hz 콤마 문자열, 예 "2:27,3:29"). 갱신/추출 호출 때는 원문을
// 그대로 되돌려 보낸다 — 펌프번호를 붙이는 규칙은 BE 에만 두기 위해서다. 화면에는 펌프 조합 순서대로
// Hz 값만 뽑아 '펌프 주파수' 열에 보인다(2026-10-01, formatPumpHzLabel).
const OPERATION_PUMP_HZ_KEYS = ['pumpHz', 'pump_hz'];
const RENEWAL_ACTUAL_CURVE_KEYS = ['currCurve', 'currentCurve', 'actualCurve', 'actual'];
const RENEWAL_NEW_CURVE_KEYS = ['newCurve', 'renewCurve', 'renewalCurve'];
const RENEWAL_AVG_ERROR_KEYS = ['avgError', 'avgErrorRate'];
const RENEWAL_POWER_UNIT_KEYS = ['powerUnit'];
const RENEWAL_POWER_COST_UNIT_KEYS = ['powerCostUnit'];
const RENEWAL_PRIORITY_KEYS = ['priority', 'pumpPriority'];
const RENEWAL_DATA_COUNT_KEYS = ['dataCount', 'dataCnt', 'count', 'sampleCount', 'n'];
const CURVE_QUAD_COEF_KEYS = ['quadCoef', 'quad_coef', 'pAddVal', 'P_ADD_VAL'];
const CURVE_LINEAR_COEF_KEYS = ['linearCoef', 'linear_coef', 'pMulVal', 'P_MUL_VAL'];
const CURVE_CONST_COEF_KEYS = ['constCoef', 'const_coef', 'pSqrtMulVal', 'P_SQRT_MUL_VAL'];
const CURVE_FC_MIN_KEYS = ['fcMin', 'fc_min', 'minFlow', 'FC_MIN_VAL'];
const CURVE_FC_MAX_KEYS = ['fcMax', 'fc_max', 'maxFlow', 'FC_MAX_VAL'];
const CURVE_SAVE_NUMBER_KEYS = [
	'quadCoef',
	'linearCoef',
	'constCoef',
	'fcMin',
	'fcMax',
	'avgErrorRate',
	'powerUnit',
	'powerCostUnit',
];

const ARRAY_PAYLOAD_KEYS = ['list', 'items', 'rows', 'content', 'result', 'data'];

function truncateDecimal(value, digits = 4) {
	const numberValue = Number(value);
	if (!Number.isFinite(numberValue)) return value;

	const factor = 10 ** digits;
	return String(Math.trunc(numberValue * factor) / factor);
}

// 펌프 조합("2,3")과 주파수 문자열("2:27,3:29")을 짝지어 조합 순서대로 Hz 만 나열한다 → "27, 29".
// 주파수가 없는 펌프는 '-' 로 두고, 주파수 자체가 없으면 '-' 한 글자만 돌려 다른 열과 표기를 맞춘다.
function formatPumpHzLabel(pumpHz, pumpSet) {
	if (pumpHz === undefined || pumpHz === null || String(pumpHz).trim() === '') return '-';

	const hzByPump = {};
	String(pumpHz)
		.split(',')
		.map(token => token.trim())
		.filter(Boolean)
		.forEach(token => {
			const [pumpIdx, hz] = token.split(':').map(part => part.trim());
			if (pumpIdx && hz !== undefined && hz !== '') hzByPump[pumpIdx] = hz;
		});

	const pumpIdxSeq =
		pumpSet !== undefined && pumpSet !== null && String(pumpSet).trim() !== ''
			? String(pumpSet).split(',').map(token => token.trim()).filter(Boolean)
			: Object.keys(hzByPump);

	const labelSeq = pumpIdxSeq.map(pumpIdx => hzByPump[pumpIdx] ?? '-');
	return labelSeq.length ? labelSeq.join(', ') : '-';
}

const operationColSeq = [
	{ key: 'rank', colNm: '순번', flex: 0.45, minWidth: 26 },
	{ key: 'runCount', colNm: '운영 대수', flex: 0.7, minWidth: 36 },
	{ key: 'pumpSet', colNm: '펌프 조합', flex: 1.25, minWidth: 68 },
	{ key: 'pumpHzLabel', colNm: '펌프 주파수\n(Hz)', flex: 1.0, minWidth: 56 },
	{ key: 'runMinutes', colNm: '운영건수\n(분)', flex: 0.72, minWidth: 40 },
	{ key: 'powerUnit', colNm: '전력원단위', flex: 0.78, minWidth: 42, valueFormatter: value => truncateDecimal(value, 4) },
	{ key: 'priority', colNm: '우선순위', flex: 0.72, minWidth: 42 },
];

function formatApiDateTime(value) {
	if (!value) return undefined;
	return String(value).replace('T', ' ');
}

function unwrapResponseData(response) {
	if (!response || typeof response !== 'object') return response;
	return response.data ?? response.result ?? response.body ?? response;
}

function readFirstValue(source, keys, fallback = undefined) {
	if (!source || typeof source !== 'object') return fallback;

	for (const key of keys) {
		if (source[key] !== undefined && source[key] !== null) return source[key];
	}

	return fallback;
}

function readFirstNestedValue(source, keys, fallback = undefined) {
	if (!source || typeof source !== 'object') return fallback;
	const sourceSeq = [source, source.coef, source.coeff, source.curveCoef, source.coefficients].filter(
		value => value && typeof value === 'object'
	);

	for (const targetSource of sourceSeq) {
		const value = readFirstValue(targetSource, keys);
		if (value !== undefined && value !== null) return value;
	}

	return fallback;
}

function resolveArrayPayload(payload) {
	if (Array.isArray(payload)) return payload;
	if (!payload || typeof payload !== 'object') return [];

	for (const key of ARRAY_PAYLOAD_KEYS) {
		if (Array.isArray(payload[key])) return payload[key];
	}

	return [];
}

function formatNullableValue(value) {
	if (value === undefined || value === null || value === '') return '-';
	return value;
}

function formatMetricNumber(value) {
	if (value === undefined || value === null || value === '') return '-';
	const numberValue = Number(value);
	if (!Number.isFinite(numberValue)) return String(value);
	return Number.isInteger(numberValue) ? numberValue.toLocaleString() : String(Math.trunc(numberValue * 10000) / 10000);
}

function formatMetricValue(value, unit = '') {
	if (value === undefined || value === null || value === '') return '-';
	const numberValue = Number(value);
	if (!Number.isFinite(numberValue)) return String(value);

	const formattedValue = formatMetricNumber(value);
	return `${formattedValue}${unit}`;
}

function formatMetricPercent(value) {
	if (value === undefined || value === null || value === '') return '-';
	const numberValue = Number(value);
	if (!Number.isFinite(numberValue)) return String(value);

	return `${formatMetricNumber(value)}%`;
}

function toFiniteNumber(value) {
	const numberValue = Number(value);
	return Number.isFinite(numberValue) ? numberValue : null;
}

function toNullableInteger(value) {
	const numberValue = Number(value);
	return Number.isFinite(numberValue) ? Math.trunc(numberValue) : null;
}

function solveLinear3(matrix, vector) {
	const [a, b, c] = matrix;
	const determinant =
		a[0] * (b[1] * c[2] - b[2] * c[1]) -
		a[1] * (b[0] * c[2] - b[2] * c[0]) +
		a[2] * (b[0] * c[1] - b[1] * c[0]);

	if (Math.abs(determinant) < Number.EPSILON) return null;

	const determinantFor = columnIndex => {
		const nextMatrix = matrix.map((row, rowIndex) =>
			row.map((value, valueIndex) => (valueIndex === columnIndex ? vector[rowIndex] : value))
		);
		const [nextA, nextB, nextC] = nextMatrix;

		return (
			nextA[0] * (nextB[1] * nextC[2] - nextB[2] * nextC[1]) -
			nextA[1] * (nextB[0] * nextC[2] - nextB[2] * nextC[0]) +
			nextA[2] * (nextB[0] * nextC[1] - nextB[1] * nextC[0])
		);
	};

	return [determinantFor(0) / determinant, determinantFor(1) / determinant, determinantFor(2) / determinant];
}

function resolveQuadraticCoefficients(pointSeq) {
	if (!Array.isArray(pointSeq) || pointSeq.length < 3) return null;

	const sum = pointSeq.reduce(
		(acc, point) => {
			const x = Number(point.x);
			const y = Number(point.y);
			if (!Number.isFinite(x) || !Number.isFinite(y)) return acc;

			const x2 = x * x;
			const x3 = x2 * x;
			const x4 = x2 * x2;

			acc.count += 1;
			acc.x += x;
			acc.x2 += x2;
			acc.x3 += x3;
			acc.x4 += x4;
			acc.y += y;
			acc.xy += x * y;
			acc.x2y += x2 * y;
			return acc;
		},
		{ count: 0, x: 0, x2: 0, x3: 0, x4: 0, y: 0, xy: 0, x2y: 0 }
	);

	if (sum.count < 3) return null;

	const solution = solveLinear3(
		[
			[sum.x4, sum.x3, sum.x2],
			[sum.x3, sum.x2, sum.x],
			[sum.x2, sum.x, sum.count],
		],
		[sum.x2y, sum.xy, sum.y]
	);

	if (!solution) return null;
	const [quadCoef, linearCoef, constCoef] = solution;

	return { quadCoef, linearCoef, constCoef };
}

function resolvePointRange(pointSeq) {
	let fcMin = Infinity;
	let fcMax = -Infinity;

	for (const point of pointSeq) {
		const x = point?.x;
		if (!Number.isFinite(x)) continue;
		if (x < fcMin) fcMin = x;
		if (x > fcMax) fcMax = x;
	}

	if (!Number.isFinite(fcMin)) return null;

	return {
		fcMin,
		fcMax,
	};
}

function createCurveSaveRequest(previewPayload) {
	if (!previewPayload || typeof previewPayload !== 'object') return null;

	const newCurvePointSeq = normalizeCurvePointRows(resolveCurvePointPayloadByKeys(previewPayload, RENEWAL_NEW_CURVE_KEYS));
	const fallbackCoefficients = resolveQuadraticCoefficients(newCurvePointSeq);
	const fallbackRange = resolvePointRange(newCurvePointSeq);
	const requestBody = {
		quadCoef:
			toFiniteNumber(readFirstNestedValue(previewPayload, CURVE_QUAD_COEF_KEYS)) ?? fallbackCoefficients?.quadCoef ?? null,
		linearCoef:
			toFiniteNumber(readFirstNestedValue(previewPayload, CURVE_LINEAR_COEF_KEYS)) ??
			fallbackCoefficients?.linearCoef ??
			null,
		constCoef:
			toFiniteNumber(readFirstNestedValue(previewPayload, CURVE_CONST_COEF_KEYS)) ?? fallbackCoefficients?.constCoef ?? null,
		fcMin: toFiniteNumber(readFirstNestedValue(previewPayload, CURVE_FC_MIN_KEYS)) ?? fallbackRange?.fcMin ?? null,
		fcMax: toFiniteNumber(readFirstNestedValue(previewPayload, CURVE_FC_MAX_KEYS)) ?? fallbackRange?.fcMax ?? null,
		avgErrorRate: toFiniteNumber(readFirstValue(previewPayload, RENEWAL_AVG_ERROR_KEYS)),
		powerUnit: toFiniteNumber(readFirstValue(previewPayload, RENEWAL_POWER_UNIT_KEYS)),
		powerCostUnit: toFiniteNumber(readFirstValue(previewPayload, RENEWAL_POWER_COST_UNIT_KEYS)),
		priority: toNullableInteger(readFirstValue(previewPayload, RENEWAL_PRIORITY_KEYS)),
		dataCount: toNullableInteger(readFirstValue(previewPayload, RENEWAL_DATA_COUNT_KEYS)),
	};

	const hasRequiredNumber = CURVE_SAVE_NUMBER_KEYS.every(key => Number.isFinite(requestBody[key]));
	return hasRequiredNumber && requestBody.fcMin < requestBody.fcMax ? requestBody : null;
}

function normalizeOperationRows(payload) {
	const rowSeq = resolveArrayPayload(payload);

	return rowSeq.map((row, index) => {
		const pumpGrp = readFirstValue(row, OPERATION_PUMP_GRP_KEYS);
		const combIdx = readFirstValue(row, OPERATION_COMB_IDX_KEYS);

		return {
			// 조합 식별자가 두 값이라 그리드 행 키는 둘을 합성해 만든다(선택 행 비교에 쓰이므로 유일해야 함).
			id: pumpGrp !== undefined && combIdx !== undefined ? `${pumpGrp}-${combIdx}` : index + 1,
			pumpGrp,
			combIdx,
			// 표출용이 아니라 전달용이라 formatNullableValue 를 태우지 않고 원값을 그대로 들고 있는다.
			pumpHz: readFirstValue(row, OPERATION_PUMP_HZ_KEYS) ?? null,
			// 표출용 주파수. 펌프 조합 순서에 맞춰 Hz 만 나열한다("27, 29").
			pumpHzLabel: formatPumpHzLabel(readFirstValue(row, OPERATION_PUMP_HZ_KEYS), readFirstValue(row, OPERATION_PUMP_SET_KEYS)),
			rank: index + 1,
			runCount: formatNullableValue(readFirstValue(row, OPERATION_RUN_COUNT_KEYS)),
			pumpSet: formatNullableValue(readFirstValue(row, OPERATION_PUMP_SET_KEYS)),
			runMinutes: formatNullableValue(readFirstValue(row, OPERATION_RUN_MINUTES_KEYS)),
			powerUnit: formatNullableValue(readFirstValue(row, OPERATION_POWER_UNIT_KEYS)),
			powerCostUnit: formatNullableValue(readFirstValue(row, OPERATION_POWER_COST_UNIT_KEYS)),
			avgErrorRate: formatNullableValue(readFirstValue(row, OPERATION_AVG_ERROR_RATE_KEYS)),
			priority: formatNullableValue(readFirstValue(row, OPERATION_PRIORITY_KEYS)),
			raw: row,
		};
	});
}

function createMetricRowsFromOperationRow(row, renewalPayload = null) {
	if (!row) return metricRows;
	const renewalActualCurveSeq = renewalPayload ? resolveCurvePointPayloadByKeys(renewalPayload, RENEWAL_ACTUAL_CURVE_KEYS) : [];

	return metricRows.map(metricRow => {
		if (metricRow.id === 'data') {
			return {
				...metricRow,
				beforeValue: renewalPayload
					? formatMetricValue(
							readFirstValue(renewalPayload, RENEWAL_DATA_COUNT_KEYS, renewalActualCurveSeq.length || undefined),
							'개'
						)
					: '',
				afterValue: '',
			};
		}

		if (metricRow.id === 'rmse') {
			return {
				...metricRow,
				beforeValue: formatMetricPercent(readFirstValue(row.raw, OPERATION_AVG_ERROR_RATE_KEYS, row.avgErrorRate)),
				afterValue: renewalPayload
					? formatMetricPercent(readFirstValue(renewalPayload, RENEWAL_AVG_ERROR_KEYS))
					: metricRow.afterValue,
			};
		}

		if (metricRow.id === 'power') {
			return {
				...metricRow,
				beforeValue: formatMetricValue(readFirstValue(row.raw, OPERATION_POWER_UNIT_KEYS, row.powerUnit), ' kWh/m³'),
				afterValue: renewalPayload
					? formatMetricValue(readFirstValue(renewalPayload, RENEWAL_POWER_UNIT_KEYS), ' kWh/m³')
					: metricRow.afterValue,
			};
		}

		if (metricRow.id === 'loss') {
			return {
				...metricRow,
				beforeValue: formatMetricValue(
					readFirstValue(row.raw, OPERATION_POWER_COST_UNIT_KEYS, row.powerCostUnit),
					'원/m³'
				),
				afterValue: renewalPayload
					? formatMetricValue(readFirstValue(renewalPayload, RENEWAL_POWER_COST_UNIT_KEYS), '원/m³')
					: metricRow.afterValue,
			};
		}

		if (metricRow.id === 'priority') {
			return {
				...metricRow,
				beforeValue: formatMetricValue(readFirstValue(row.raw, OPERATION_PRIORITY_KEYS, row.priority), '순위'),
				afterValue: renewalPayload
					? formatMetricValue(readFirstValue(renewalPayload, RENEWAL_PRIORITY_KEYS), '순위')
					: metricRow.afterValue,
			};
		}

		return metricRow;
	});
}

function resolveCurvePointPayload(payload) {
	if (Array.isArray(payload)) return payload;
	if (Array.isArray(payload?.data)) return payload.data;
	return resolveArrayPayload(payload);
}

function normalizeCurvePointRows(payload) {
	return resolveCurvePointPayload(payload)
		.map(point => {
			const x = toFiniteNumber(point?.flow);
			const y = toFiniteNumber(point?.head);

			return x === null || y === null ? null : { x, y };
		})
		.filter(Boolean);
}

function resolveCurvePointPayloadByKeys(payload, keys) {
	if (!payload || typeof payload !== 'object') return [];

	for (const key of keys) {
		if (Array.isArray(payload[key])) return payload[key];
	}

	return [];
}

function normalizeCurveFlowRange(payload) {
	const minFlow = toFiniteNumber(payload?.minFlow);
	const maxFlow = toFiniteNumber(payload?.maxFlow);

	return minFlow === null || maxFlow === null || minFlow >= maxFlow ? null : { minFlow, maxFlow };
}

function buildOperationStatsParams(startDttm, endDttm) {
	return {
		from: formatApiDateTime(startDttm),
		to: formatApiDateTime(endDttm),
	};
}

// 성능곡선 갱신(renewal) 조회 파라미터.
// 조합 목록 조회와 달리 목표 주파수(pumpHz)를 함께 싣는다. 값이 있는 조합만 붙여
// 주파수 미입력 조합에서는 지금까지처럼 주파수 조건 없이 회귀하게 둔다.
function buildCurveRenewalParams(startDttm, endDttm, pumpHz) {
	const params = buildOperationStatsParams(startDttm, endDttm);

	return pumpHz ? { ...params, pumpHz } : params;
}

function buildCurveExtractRequest(startDttm, endDttm, pointSeq, pumpHz) {
	return {
		from: formatApiDateTime(startDttm),
		to: formatApiDateTime(endDttm),
		points: pointSeq.map(point => ({
			flow: point.x,
			head: point.y,
		})),
		// 갱신과 같은 기준으로 실측 구간을 걸러야 지표(평균오차·전력원단위)가 서로 비교된다.
		...(pumpHz ? { pumpHz } : {}),
	};
}

function findNearestChartPoint(pointSeq, targetX) {
	if (!pointSeq?.length) return null;

	return pointSeq.reduce(
		(nearestPoint, point, index) => {
			const distance = Math.abs(point.x - targetX);
			const nearestDistance = Math.abs(nearestPoint.point.x - targetX);

			return distance < nearestDistance ? { point, index } : nearestPoint;
		},
		{ point: pointSeq[0], index: 0 }
	);
}

function createCurveChartDatasets(pointSeq = [], actualPointSeq = [], newPointSeq = [], clickedPointSeq = []) {
	const hasPointData = pointSeq.length > 0;
	const hasActualPointData = actualPointSeq.length > 0;
	const hasNewPointData = newPointSeq.length > 0;
	const hasClickedPointData = clickedPointSeq.length > 0;

	const datasets = [];

	if (hasActualPointData) {
		datasets.push({
			label: '실측 운전점',
			data: actualPointSeq,
			hidden: false,
			showLine: false,
			backgroundColor: '#2563eb',
			borderColor: '#2563eb',
			borderWidth: 1,
			pointRadius: 1,
			pointHoverRadius: 3,
		});
	}

	if (hasPointData) {
		datasets.push({
			label: '기존 성능곡선',
			data: pointSeq,
			hidden: false,
			showLine: true,
			borderColor: '#1d4ed8',
			backgroundColor: '#1d4ed8',
			borderWidth: 2,
			pointRadius: 0,
			pointHoverRadius: 3,
			tension: 0.25,
		});
	}

	if (hasNewPointData) {
		datasets.push({
			label: '신규 성능곡선',
			data: newPointSeq,
			hidden: false,
			showLine: true,
			borderColor: '#ef4444',
			backgroundColor: '#ef4444',
			borderDash: [6, 4],
			borderWidth: 2,
			pointRadius: 0,
			pointHoverRadius: 3,
			tension: 0.25,
		});
	}

	if (hasClickedPointData) {
		datasets.push({
			label: '신규 입력점',
			data: clickedPointSeq,
			hidden: false,
			showLine: false,
			pointRadius: 7,
			pointHoverRadius: 9,
			backgroundColor: '#f97316',
			borderColor: '#7c2d12',
			borderWidth: 1.5,
		});
	}

	return datasets;
}

function clampNumber(value, min, max) {
	return Math.min(max, Math.max(min, value));
}

function roundChartValue(value) {
	return Number(value.toFixed(2));
}

function resolveClickedChartPointFromContext(context) {
	const x = Number(context?.pointer?.xValue);
	const y = Number(context?.pointer?.yValue);
	const xScale = context?.chart?.scales?.x;
	const yScale = context?.chart?.scales?.y;
	const chartArea = context?.chart?.chartArea;
	const canvasX = context?.pointer?.canvasX;
	const canvasY = context?.pointer?.canvasY;

	if (!Number.isFinite(x) || !Number.isFinite(y) || !xScale || !yScale) return null;
	if (
		chartArea &&
		(canvasX < chartArea.left || canvasX > chartArea.right || canvasY < chartArea.top || canvasY > chartArea.bottom)
	) {
		return null;
	}

	return {
		x: roundChartValue(clampNumber(x, xScale.min, xScale.max)),
		y: roundChartValue(clampNumber(y, yScale.min, yScale.max)),
	};
}

function resolveDefaultOperationRowId(rows) {
	return rows[0]?.id ?? null;
}

function resolveDefaultMetricRowId(rows) {
	return rows[0]?.id ?? null;
}

const curveChartScales = {
	x: {
		min: 0,
		max: 1000,
		title: {
			display: true,
			text: '유량 Q (m³/h)',
			color: '#111827',
			font: { size: 12, weight: 800 },
		},
		grid: { color: 'rgba(148,163,184,0.26)' },
		ticks: { color: '#111827' },
	},
	y: {
		min: 0,
		max: 130,
		title: {
			display: true,
			text: '양정 H (m)',
			color: '#111827',
			font: { size: 12, weight: 800 },
		},
		grid: { color: 'rgba(148,163,184,0.26)' },
		ticks: { color: '#111827' },
	},
};

function resolveAxisMax(valueSeq, fallback, interval) {
	let maxValue = fallback;
	for (const value of valueSeq) {
		if (Number.isFinite(value) && value > maxValue) maxValue = value;
	}

	return Math.ceil(maxValue / interval) * interval;
}

function resolveDataAxisRange(valueSeq, fallbackRange) {
	let maxValue = -Infinity;
	let minValue = Infinity;
	for (const value of valueSeq) {
		if (!Number.isFinite(value)) continue;
		if (value > maxValue) maxValue = value;
		if (value < minValue) minValue = value;
	}
	if (!Number.isFinite(maxValue)) return fallbackRange;

	return { min: minValue * 0.5, max: maxValue * 1.5 };
}

function createCurveChartScales(pointSeq = [], actualPointSeq = [], newPointSeq = [], clickedPointSeq = [], flowRange = null) {
	const curvePointSeq = [...pointSeq, ...actualPointSeq, ...newPointSeq];
	const allPointSeq = [...curvePointSeq, ...clickedPointSeq];
	const xMin = flowRange?.minFlow ?? curveChartScales.x.min;
	const xMax =
		flowRange?.maxFlow ??
		resolveAxisMax(
			allPointSeq.map(point => point.x),
			curveChartScales.x.max,
			100
		);
	// 입력점을 추가해도 Y축은 유지한다. 조회된 곡선·실측 데이터 중 X축 표시 구간만 사용한다.
	const visiblePointSeq = curvePointSeq.filter(point => point.x >= xMin && point.x <= xMax);
	const yRange = resolveDataAxisRange(
		visiblePointSeq.map(point => point.y),
		{ min: curveChartScales.y.min, max: curveChartScales.y.max }
	);

	return {
		x: {
			...curveChartScales.x,
			display: allPointSeq.length > 0,
			min: xMin,
			max: xMax,
		},
		y: {
			...curveChartScales.y,
			display: allPointSeq.length > 0,
			min: yRange.min,
			max: yRange.max,
		},
	};
}

const curveChartLegend = {
	display: false,
	labels: {
		filter: legendItem => legendItem.text !== '사용자 입력곡선',
	},
};

function formatChartGuideValue(value, unit = '') {
	const numberValue = Number(value);
	if (!Number.isFinite(numberValue)) return '-';

	return `${numberValue.toLocaleString(undefined, { maximumFractionDigits: 2 })}${unit}`;
}

const curveChartCrosshairOptions = {
	color: 'rgba(14, 116, 144, 0.72)',
	width: 1,
	dash: [4, 4],
	labelBackgroundColor: 'rgba(15, 23, 42, 0.92)',
	labelColor: '#e0f2fe',
	xFormatter: value => `Q ${formatChartGuideValue(value, ' m³/h')}`,
	yFormatter: value => `H ${formatChartGuideValue(value, ' m')}`,
};

function SectionTitle({ children, action }) {
	return (
		<div className="flex h-8 items-center gap-3 bg-[linear-gradient(90deg,#0d6d87,#114f83_70%,rgba(17,79,131,0.18))] px-3 text-[14px] font-extrabold text-sky-50 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
			<span className="min-w-0 flex-1 truncate">{children}</span>
			{action ? <div className="shrink-0">{action}</div> : null}
		</div>
	);
}

function CurveChart({
	pointSeq = [],
	actualPointSeq = [],
	newPointSeq = [],
	clickedPointSeq = [],
	flowRange = null,
	isEditMode = false,
	isLoading = false,
	chartVersion = 0,
	onPointClick,
}) {
	const [clickPulse, setClickPulse] = useState(null);

	useEffect(() => {
		if (!clickPulse) return undefined;

		const timeoutId = window.setTimeout(() => setClickPulse(null), 400);
		return () => window.clearTimeout(timeoutId);
	}, [clickPulse]);

	const handleChartAreaClick = context => {
		if (!isEditMode && !pointSeq.length) return;

			const clickedPoint = resolveClickedChartPointFromContext(context);
		if (!clickedPoint) return;

		const nearestChartPoint = findNearestChartPoint(pointSeq, clickedPoint.x);
		if (!isEditMode) {
			if (!nearestChartPoint) return;

			onPointClick?.({
				mode: 'select',
				datasetLabel: '기존 성능곡선',
				x: nearestChartPoint.point.x,
				y: nearestChartPoint.point.y,
				pointNo: nearestChartPoint.index + 1,
			});
			return;
		}

		const canvasRect = context.chart.canvas.getBoundingClientRect();
		const containerRect = context.chart.canvas.parentElement?.parentElement?.getBoundingClientRect();
		if (containerRect) {
			setClickPulse(previousPulse => ({
				id: (previousPulse?.id ?? 0) + 1,
				left: canvasRect.left - containerRect.left + context.pointer.canvasX,
				top: canvasRect.top - containerRect.top + context.pointer.canvasY,
			}));
		}

		onPointClick?.({
			mode: 'edit',
			datasetLabel: '신규 입력점',
			x: clickedPoint.x,
			y: clickedPoint.y,
			pointNo: nearestChartPoint ? nearestChartPoint.index + 1 : clickedPointSeq.length + 1,
		});
	};

	const chartConfig = useMemo(
		() =>
			ChartWrapper.create('scatter', [], createCurveChartDatasets(pointSeq, actualPointSeq, newPointSeq, clickedPointSeq), {
				maintainAspectRatio: false,
				animation: false,
				parsing: false,
				interaction: {
					mode: 'nearest',
					intersect: false,
				},
				hover: {
					mode: 'nearest',
					intersect: false,
				},
				onClick: (_event, _elements, context) => {
					handleChartAreaClick(context);
				},
				scales: createCurveChartScales(pointSeq, actualPointSeq, newPointSeq, clickedPointSeq, flowRange),
			})
				.addCrosshair(curveChartCrosshairOptions)
				.setLegend(curveChartLegend)
				.customLegend(performCurveCustomLegendConfig)
				.setPlugin(performCurveLegendShapePlugin)
				.build('perform-curve-scatter'),
		[actualPointSeq, clickedPointSeq, flowRange, isEditMode, newPointSeq, onPointClick, pointSeq]
	);

	return (
		<div className="relative h-full">
			<PerformCurveCustomLegend />
			<CommonChart
				key={chartVersion}
				chartConfig={chartConfig}
				className="h-[calc(100%-28px)] bg-white px-2 pb-2"
				isLoading={isLoading}
				noData={{ text: '데이터가 없습니다.', color: '#64748b' }}
			/>
			{clickPulse && (
				<span
					key={clickPulse.id}
					className="perform-curve-click-pulse pointer-events-none absolute z-10 size-5 rounded-full border-2 border-orange-500 bg-orange-400/30"
					style={{ left: clickPulse.left, top: clickPulse.top }}
				/>
			)}
		</div>
	);
}

function PerformCurveManage() {
	const [operationTableRows, setOperationTableRows] = useState([]);
	const [selectedRowId, setSelectedRowId] = useState(null);
	const [selectedMetricRowId, setSelectedMetricRowId] = useState(resolveDefaultMetricRowId(metricRows));
	const [metricTableRows, setMetricTableRows] = useState(metricRows);
	const metricTableContainerRef = useRef(null);
	const [metricRowHeight, setMetricRowHeight] = useState(24);
	const [chartPointRows, setChartPointRows] = useState([]);
	const [actualChartPointRows, setActualChartPointRows] = useState([]);
	const [newChartPointRows, setNewChartPointRows] = useState([]);
	const [curveChartVersion, setCurveChartVersion] = useState(0);
	const [chartFlowRange, setChartFlowRange] = useState(null);
	const [clickedCurvePointRows, setClickedCurvePointRows] = useState([]);
	const [curvePreviewPayload, setCurvePreviewPayload] = useState(null);
	const [curveFlowStatus, setCurveFlowStatus] = useState('READY');
	const [isCurveEditMode, setIsCurveEditMode] = useState(false);
	const [isCurveDataLoaded, setIsCurveDataLoaded] = useState(false);
	const [isSearchLoading, setIsSearchLoading] = useState(false);
	const [isCurveLoading, setIsCurveLoading] = useState(false);
	const [isCurveSaving, setIsCurveSaving] = useState(false);
	const [isDateRangeValid, setIsDateRangeValid] = useState(true);
	const initialDateRange = useMemo(
		() => ({
			startDttm: dayjs().subtract(3, 'month').format(DATE_INPUT_FORMAT),
			endDttm: dayjs().format(DATE_INPUT_FORMAT),
		}),
		[]
	);
	const [startDttm, setStartDttm] = useState(initialDateRange.startDttm);
	const [endDttm, setEndDttm] = useState(initialDateRange.endDttm);
	const selectedOperationRow = useMemo(
		() => operationTableRows.find(row => row.id === selectedRowId) ?? null,
		[operationTableRows, selectedRowId]
	);
	const requestPerformanceCurve = useCallback(async (pumpGrp, combIdx, query = {}) => {
		const hasCombKey = [pumpGrp, combIdx].every(key => key !== undefined && key !== null && key !== '');
		if (!hasCombKey) {
			setChartPointRows([]);
			setActualChartPointRows([]);
			setNewChartPointRows([]);
			setChartFlowRange(null);
			setCurvePreviewPayload(null);
			return;
		}

		const includeActual = query.includeActual === true;

		setIsCurveLoading(true);
		try {
			const curveResponse = await performApi.getPmpCombinPerformanceCurve(pumpGrp, combIdx, {});
			const curvePayload = unwrapResponseData(curveResponse);
			setChartPointRows(normalizeCurvePointRows(curvePayload));
			setChartFlowRange(normalizeCurveFlowRange(curvePayload));

			if (includeActual) {
				const renewalResponse = await performApi.getPmpCombinPerformnaceCurveRenewal(pumpGrp, combIdx, {
					searchParams: buildCurveRenewalParams(query.startDttm, query.endDttm, query.operationRow?.pumpHz),
				});
				const renewalPayload = unwrapResponseData(renewalResponse);
				setActualChartPointRows(
					normalizeCurvePointRows(resolveCurvePointPayloadByKeys(renewalPayload, RENEWAL_ACTUAL_CURVE_KEYS))
				);
				setNewChartPointRows(
					normalizeCurvePointRows(resolveCurvePointPayloadByKeys(renewalPayload, RENEWAL_NEW_CURVE_KEYS))
				);

				if (query.operationRow) {
					const nextMetricRows = createMetricRowsFromOperationRow(query.operationRow, renewalPayload);
					setMetricTableRows(nextMetricRows);
					setSelectedMetricRowId(resolveDefaultMetricRowId(nextMetricRows));
				}
				setCurvePreviewPayload(renewalPayload);
			} else {
				setActualChartPointRows([]);
				setNewChartPointRows([]);
				setCurvePreviewPayload(null);
			}

			setClickedCurvePointRows([]);
			setCurveChartVersion(prevVersion => prevVersion + 1);
			setCurveFlowStatus('DATA_LOADED');
			setIsCurveDataLoaded(true);
		} catch {
			setChartPointRows([]);
			setActualChartPointRows([]);
			setNewChartPointRows([]);
			setChartFlowRange(null);
			setCurvePreviewPayload(null);
			showToast('error', '펌프 성능곡선 조회에 실패했습니다.');
		} finally {
			setIsCurveLoading(false);
		}
	}, []);
	const requestPerformanceCurveData = useCallback(async (query = {}) => {
		setIsSearchLoading(true);

		try {
			const response = await performApi.getPmpCombinOperatStats({
				skipErrorToast: true,
				showSpinner: false,
				searchParams: buildOperationStatsParams(query.startDttm, query.endDttm),
			});
			const nextOperationRows = normalizeOperationRows(unwrapResponseData(response));
			const defaultSelectedRowId = resolveDefaultOperationRowId(nextOperationRows);
			const defaultSelectedRow = nextOperationRows.find(row => row.id === defaultSelectedRowId) ?? null;

			setOperationTableRows(nextOperationRows);
			setSelectedRowId(defaultSelectedRowId);
			const nextMetricRows = createMetricRowsFromOperationRow(defaultSelectedRow);
			setMetricTableRows(nextMetricRows);
			setSelectedMetricRowId(resolveDefaultMetricRowId(nextMetricRows));
			setChartPointRows([]);
			setActualChartPointRows([]);
			setNewChartPointRows([]);
			setChartFlowRange(null);
			setClickedCurvePointRows([]);
			setCurvePreviewPayload(null);
			setCurveFlowStatus('READY');
			setIsCurveEditMode(false);
			setIsCurveDataLoaded(false);
		} catch {
			setOperationTableRows([]);
			setSelectedRowId(null);
			setChartPointRows([]);
			setActualChartPointRows([]);
			setNewChartPointRows([]);
			setChartFlowRange(null);
			setClickedCurvePointRows([]);
			setCurvePreviewPayload(null);
			setMetricTableRows(metricRows);
			setSelectedMetricRowId(resolveDefaultMetricRowId(metricRows));
			showToast('error', '펌프조합 운영 현황 조회에 실패했습니다.');
		} finally {
			setIsSearchLoading(false);
		}
	}, []);

	useEffect(() => {
		const timerId = window.setTimeout(() => {
			void requestPerformanceCurveData({
				startDttm: initialDateRange.startDttm,
				endDttm: initialDateRange.endDttm,
			});
		}, 0);

		return () => window.clearTimeout(timerId);
	}, [initialDateRange.endDttm, initialDateRange.startDttm, requestPerformanceCurveData]);

	useEffect(() => {
		const element = metricTableContainerRef.current;
		if (!element) return undefined;

		const updateRowHeight = () => {
			const rowCount = Math.max(metricTableRows.length, 1);
			const nextRowHeight = Math.max(24, Math.floor(element.clientHeight / rowCount));

			setMetricRowHeight(prevRowHeight => (prevRowHeight === nextRowHeight ? prevRowHeight : nextRowHeight));
		};

		updateRowHeight();

		if (typeof ResizeObserver === 'undefined') {
			window.addEventListener('resize', updateRowHeight);
			return () => window.removeEventListener('resize', updateRowHeight);
		}

		const resizeObserver = new ResizeObserver(updateRowHeight);
		resizeObserver.observe(element);

		return () => resizeObserver.disconnect();
	}, [metricTableRows.length]);

	const handleOperationRowClick = row => {
		const nextMetricRows = createMetricRowsFromOperationRow(row);

		setSelectedRowId(row.id);
		setMetricTableRows(nextMetricRows);
		setSelectedMetricRowId(resolveDefaultMetricRowId(nextMetricRows));
		setCurveFlowStatus('READY');
		setIsCurveEditMode(false);
		setChartPointRows([]);
		setChartFlowRange(null);
		setActualChartPointRows([]);
		setNewChartPointRows([]);
		setClickedCurvePointRows([]);
		setCurvePreviewPayload(null);
		setIsCurveDataLoaded(false);
		void requestPerformanceCurve(row.pumpGrp, row.combIdx);
	};
	const handleRefreshClick = () => {
		if (!selectedOperationRow) return;

		const nextMetricRows = createMetricRowsFromOperationRow(selectedOperationRow);

		setIsCurveEditMode(false);
		setMetricTableRows(nextMetricRows);
		setSelectedMetricRowId(resolveDefaultMetricRowId(nextMetricRows));
		setChartPointRows([]);
		setChartFlowRange(null);
		setActualChartPointRows([]);
		setNewChartPointRows([]);
		setClickedCurvePointRows([]);
		setCurvePreviewPayload(null);
		void requestPerformanceCurve(selectedOperationRow.pumpGrp, selectedOperationRow.combIdx, {
			startDttm,
			endDttm,
			includeActual: true,
			operationRow: selectedOperationRow,
		});
	};
	const handleEditClick = () => {
		if (!selectedOperationRow) return;

		setIsCurveDataLoaded(true);
		setIsCurveEditMode(!isCurveEditMode);
		setCurveFlowStatus(isCurveEditMode ? 'DATA_LOADED' : 'EDITING');
	};
	const handleExtractClick = async () => {
		if (!selectedOperationRow) return;
		if (clickedCurvePointRows.length === 0) {
			showToast('error', '차트에 입력점을 먼저 추가해주세요.');
			return;
		}

		setIsCurveLoading(true);
		try {
			const response = await performApi.addPmpCombinPerformnaceCurveExtract(
				selectedOperationRow.pumpGrp,
				selectedOperationRow.combIdx,
				buildCurveExtractRequest(startDttm, endDttm, clickedCurvePointRows, selectedOperationRow.pumpHz)
			);
			const extractPayload = unwrapResponseData(response);
			const nextMetricRows = createMetricRowsFromOperationRow(selectedOperationRow, extractPayload);

			setActualChartPointRows(
				normalizeCurvePointRows(resolveCurvePointPayloadByKeys(extractPayload, RENEWAL_ACTUAL_CURVE_KEYS))
			);
			setNewChartPointRows(
				normalizeCurvePointRows(resolveCurvePointPayloadByKeys(extractPayload, RENEWAL_NEW_CURVE_KEYS))
			);
			setCurvePreviewPayload(extractPayload);
			setIsCurveDataLoaded(true);
			setIsCurveEditMode(false);
			setMetricTableRows(nextMetricRows);
			setSelectedMetricRowId(resolveDefaultMetricRowId(nextMetricRows));
			setCurveChartVersion(prevVersion => prevVersion + 1);
			setCurveFlowStatus('EXTRACTED');
		} catch {
			showToast('error', '펌프 성능곡선 추출에 실패했습니다.');
		} finally {
			setIsCurveLoading(false);
		}
	};
	const handleSaveClick = async () => {
		if (!selectedOperationRow) return;

		const requestBody = createCurveSaveRequest(curvePreviewPayload);
		if (!requestBody) {
			showToast('error', '갱신 또는 추출된 성능곡선 정보가 없습니다.');
			return;
		}

		setIsCurveSaving(true);
		try {
			await performApi.savePmpCombinPerformanceCurve(selectedOperationRow.pumpGrp, selectedOperationRow.combIdx, requestBody, {
				skipErrorToast: true,
			});
			showToast('info', '성능곡선을 저장했습니다.');
			setIsCurveEditMode(false);
			setCurvePreviewPayload(null);
			setCurveFlowStatus('SAVED');
		} catch {
			showToast('error', '성능곡선 저장에 실패했습니다.');
		} finally {
			setIsCurveSaving(false);
		}
	};
	const handleCancelClick = () => {
		const nextMetricRows = createMetricRowsFromOperationRow(selectedOperationRow);

		setMetricTableRows(nextMetricRows);
		setSelectedMetricRowId(resolveDefaultMetricRowId(nextMetricRows));
		setClickedCurvePointRows([]);
		setCurvePreviewPayload(null);
		setIsCurveEditMode(false);
		setCurveFlowStatus('READY');
	};
	const handleSearchClick = () => {
		if (!isDateRangeValid) return;

		void requestPerformanceCurveData({
			startDttm,
			endDttm,
		});
	};
	const handleDateRangeValidationChange = useCallback(({ isValid }) => {
		setIsDateRangeValid(isValid);
	}, []);
	const handleChartPointClick = pointInfo => {
		if (pointInfo.mode === 'edit') {
			const nextPoint = { x: pointInfo.x, y: pointInfo.y };

			if (clickedCurvePointRows.length >= MAX_CURVE_INPUT_POINT_COUNT) {
				showToast('error', '신규 입력점은 5개만 찍을 수 있습니다.');
				return;
			}

			setClickedCurvePointRows(prevRows =>
				prevRows.length >= MAX_CURVE_INPUT_POINT_COUNT ? prevRows : [...prevRows, nextPoint].sort((a, b) => a.x - b.x)
			);
			setIsCurveDataLoaded(true);
			setCurveFlowStatus('EDITING');
			return;
		}

		setIsCurveDataLoaded(true);
		setCurveFlowStatus('DATA_LOADED');
	};
	const handleMetricCellChange = (row, key, value) => {
		setMetricTableRows(prevRows => prevRows.map(prevRow => (prevRow.id === row.id ? { ...prevRow, [key]: value } : prevRow)));
		setCurveFlowStatus('EDITING');
	};

	return (
		<div className="flex h-full min-h-0 flex-col bg-[radial-gradient(circle_at_top,rgba(34,87,183,0.24),rgba(8,22,52,0.12)_38%,rgba(4,10,25,0.98)_84%)] p-1 text-[13px] text-sky-50">
			<CommonCard className="flex h-full min-h-0 flex-1 flex-col overflow-hidden rounded-[4px] bg-[rgba(6,18,42,0.8)] p-2">
				<div className="mb-2 flex h-8 shrink-0 items-center justify-end gap-3">
					<CommonDateTimeRangePicker
						startValue={startDttm}
						endValue={endDttm}
						onStartChange={setStartDttm}
						onEndChange={setEndDttm}
						onValidationChange={handleDateRangeValidationChange}
						type="date"
						className="shrink-0"
					/>
					<CommonButton
						text="조회"
						size="sm"
						variant="secondary"
						isLoading={isSearchLoading}
						loadingText="조회중"
						disabled={!isDateRangeValid}
						onClick={handleSearchClick}
					/>
				</div>

				<div className="grid min-h-0 flex-1 grid-cols-[minmax(0,0.46fr)_minmax(0,0.54fr)] gap-3">
					<CommonCard className="flex h-full min-h-0 flex-col rounded-[4px] bg-slate-950/20 p-2">
						<SectionTitle>조합별 운영 현황 및 전력 원단위</SectionTitle>
						<div className="mt-2 min-h-0 flex-1 overflow-hidden rounded-[4px] border border-sky-200/20 bg-slate-950/30">
							<CommonTable
								colSeq={operationColSeq}
								rowSeq={operationTableRows}
								getRowKey={row => row.id}
								selectedRowKey={selectedRowId}
								onRowClick={handleOperationRowClick}
								loading={isSearchLoading}
								rowHeight={28}
								columnHeaderHeight={30}
								sx={{
									fontSize: 12,
									'& .MuiDataGrid-cell': {
										justifyContent: 'center',
										paddingLeft: '4px',
										paddingRight: '4px',
									},
									'& .MuiDataGrid-columnHeader': {
										paddingLeft: '4px',
										paddingRight: '4px',
									},
								}}
							/>
						</div>
					</CommonCard>

					<CommonCard className="flex h-full min-h-0 flex-col rounded-[4px] bg-slate-950/20 p-2">
						<SectionTitle
							action={
								<div className="flex items-center gap-1">
									<span className="mr-1 min-w-[62px] text-right text-[11px] font-semibold text-sky-100/70">
										{curveFlowStatusLabel[curveFlowStatus]}
									</span>
									<CommonButton
										text="갱신"
										size="xs"
										variant="secondary"
										isLoading={isCurveLoading}
										onClick={handleRefreshClick}
									/>
									<CommonButton
										text={isCurveEditMode ? '편집중' : '편집'}
										size="xs"
										onClick={handleEditClick}
									/>
									<CommonButton text="추출" size="xs" variant="outline" onClick={handleExtractClick} />
								</div>
							}
						>
							조합별 성능곡선 현황 및 갱신
						</SectionTitle>
						<div className="relative mt-2 min-h-0 flex-[1.55] cursor-crosshair overflow-hidden rounded-[4px] border border-sky-200/20 bg-white">
							<CurveChart
								pointSeq={chartPointRows}
								actualPointSeq={actualChartPointRows}
								newPointSeq={newChartPointRows}
								clickedPointSeq={clickedCurvePointRows}
								flowRange={chartFlowRange}
								isEditMode={isCurveEditMode}
								isLoading={isCurveLoading}
								chartVersion={curveChartVersion}
								onPointClick={handleChartPointClick}
							/>
						</div>
						<div className="mt-2 flex shrink-0 items-center justify-between gap-2">
							<span className="inline-flex h-6 items-center rounded-[2px] bg-[#163667] px-3 text-[13px] font-extrabold text-sky-50">
								성능곡선 정보
							</span>
							<div className="flex gap-1">
								{isCurveDataLoaded ? (
									<span className="mr-1 flex items-center text-[11px] font-semibold text-sky-100/60">
										{selectedOperationRow?.pumpSet ?? '-'}
									</span>
								) : null}
								<CommonButton
									text="저장"
									size="xs"
									isLoading={isCurveSaving}
									disabled={!curvePreviewPayload || isCurveLoading || isCurveSaving}
									onClick={handleSaveClick}
								/>
								<CommonButton text="취소" size="xs" variant="outline" onClick={handleCancelClick} />
							</div>
						</div>
						<div
							ref={metricTableContainerRef}
							className="mt-1 min-h-0 flex-1 overflow-hidden rounded-[4px] border border-sky-200/20 bg-slate-950/30"
						>
							<CommonTable
								colSeq={metricColSeq}
								rowSeq={metricTableRows}
								getRowKey={row => row.id}
								selectedRowKey={selectedMetricRowId}
								onRowClick={row => setSelectedMetricRowId(row.id)}
								onCellChange={handleMetricCellChange}
								loading={isSearchLoading || isCurveLoading}
								rowHeight={metricRowHeight}
								columnHeaderHeight={0}
								sx={{
									fontSize: 12,
									'& .MuiDataGrid-columnHeaders': {
										minHeight: '0 !important',
										maxHeight: '0 !important',
										height: '0 !important',
									},
									'& .MuiDataGrid-cell': {
										justifyContent: 'center',
										paddingLeft: '4px',
										paddingRight: '4px',
									},
									'& .MuiDataGrid-cell[data-field="beforeLabel"], & .MuiDataGrid-cell[data-field="afterLabel"]':
										{
											backgroundColor: 'rgba(20, 79, 139, 0.76)',
											color: '#dff6ff',
											fontWeight: 800,
										},
									'& .MuiDataGrid-cell[data-field="beforeValue"], & .MuiDataGrid-cell[data-field="afterValue"]':
										{
											backgroundColor: 'rgba(9, 43, 97, 0.72)',
											color: '#f8fbff',
											fontWeight: 700,
										},
									'& .MuiDataGrid-row[data-id="data"] .MuiDataGrid-cell[data-field="afterLabel"], & .MuiDataGrid-row[data-id="data"] .MuiDataGrid-cell[data-field="afterValue"]':
										{
											backgroundColor: 'transparent',
										},
								}}
							/>
						</div>
					</CommonCard>
				</div>
			</CommonCard>
		</div>
	);
}

export default PerformCurveManage;
