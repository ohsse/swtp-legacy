import CommonCard from '@/web/components/common/CommonCard.jsx';
import CommonButton from '@/web/components/common/CommonButton.jsx';
import CommonDateTimeRangePicker from '@/web/components/common/CommonDateTimeRangePicker.jsx';
import CommonSelect from '@/web/components/common/CommonSelect.jsx';
import CommonTable from '@/web/components/common/CommonTable.jsx';
import CommonBadge from '@/web/components/common/CommonBadge.jsx';
import { showToast } from '@/web/components/common/CommonToast.jsx';
import { predApi } from '@/web/js/apis/predApi.js';
import PredictionTimeSeriesChart from '@/web/pages/predMonitor/components/PredictionTimeSeriesChart.jsx';
import dayjs from 'dayjs';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { IoContractOutline, IoExpandOutline, IoSearchOutline } from 'react-icons/io5';

const DATE_TIME_INPUT_FORMAT = 'YYYY-MM-DDTHH:mm';

const PREDICTION_TAG_OPTIONS = [
	{
		value: '701-367-FRI-4004,701-367-PRI-4019',
		label: '신 정수장',
		flowTagNo: '701-367-FRI-4004',
		pressureTagNo: '701-367-PRI-4019',
	},
	{
		value: '701-367-FRI-4001,701-367-PRI-4010',
		label: '구 정수장',
		flowTagNo: '701-367-FRI-4001',
		pressureTagNo: '701-367-PRI-4010',
	},
];

const TAG_SELECT_SX = {
	minWidth: 210,
	'& .MuiInputLabel-root': {
		color: 'rgba(226,242,255,0.84)',
		fontSize: 12,
		fontWeight: 700,
	},
	'& .MuiInputLabel-root.Mui-focused': {
		color: '#ffffff',
	},
	'& .MuiOutlinedInput-root': {
		height: 34,
		borderRadius: '6px',
		color: '#f8fbff',
		backgroundColor: 'rgba(5, 16, 40, 0.74)',
		'& fieldset': { borderColor: 'rgba(110,185,255,0.34)' },
		'&:hover fieldset': { borderColor: 'rgba(110,185,255,0.58)' },
		'&.Mui-focused fieldset': { borderColor: 'rgba(125,211,252,0.86)' },
	},
	'& .MuiSelect-select': {
		fontSize: 12,
		fontWeight: 700,
	},
	'& .MuiSvgIcon-root': {
		color: '#bae6fd',
	},
};

const ACCURACY_STATUS_CONFIG_BY_KEY = {
	EXCELLENT: {
		label: '우수',
		sx: {
			border: '1px solid rgba(74, 222, 128, 0.72)',
			background: 'linear-gradient(180deg, rgba(34,197,94,0.24), rgba(21,128,61,0.18))',
			color: '#86efac',
			boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.12), 0 0 12px rgba(34,197,94,0.12)',
		},
	},
	GOOD: {
		label: '양호',
		sx: {
			border: '1px solid rgba(45, 212, 191, 0.7)',
			background: 'linear-gradient(180deg, rgba(20,184,166,0.23), rgba(15,118,110,0.17))',
			color: '#99f6e4',
			boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.12), 0 0 12px rgba(20,184,166,0.1)',
		},
	},
	CAUTION: {
		label: '주의',
		sx: {
			border: '1px solid rgba(251, 191, 36, 0.76)',
			background: 'linear-gradient(180deg, rgba(245,158,11,0.25), rgba(180,83,9,0.18))',
			color: '#fde68a',
			boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.12), 0 0 12px rgba(245,158,11,0.12)',
		},
	},
	UNKNOWN: {
		label: '-',
		sx: {
			border: '1px solid rgba(148, 163, 184, 0.42)',
			background: 'rgba(15,23,42,0.48)',
			color: '#cbd5e1',
			boxShadow: 'none',
		},
	},
};

const ACCURACY_STATUS_KEY_BY_LABEL = {
	우수: 'EXCELLENT',
	양호: 'GOOD',
	주의: 'CAUTION',
};

function resolveAccuracyStatusConfig(status) {
	const rawStatus = String(status ?? '').trim();
	const normalizedStatus = rawStatus.toUpperCase();
	const statusKey = ACCURACY_STATUS_KEY_BY_LABEL[rawStatus] ?? normalizedStatus;

	return (
		ACCURACY_STATUS_CONFIG_BY_KEY[statusKey] ?? {
			label: rawStatus || '-',
			sx: ACCURACY_STATUS_CONFIG_BY_KEY.UNKNOWN.sx,
		}
	);
}

function AccuracyStatusBadge({ status }) {
	const config = resolveAccuracyStatusConfig(status);

	return (
		<CommonBadge
			size="sm"
			label={config.label}
			sx={{
				height: 22,
				minWidth: 44,
				borderRadius: '5px',
				fontSize: 11,
				fontWeight: 800,
				letterSpacing: 0,
				...config.sx,
			}}
		/>
	);
}

const DETAIL_TABLE_COL_SEQ = [
	{ key: 'durationLabel', colNm: '예측구간', flex: 0.95, minWidth: 104 },
	{ key: 'actual', colNm: '실측 평균', flex: 1, minWidth: 108 },
	{ key: 'predicted', colNm: '예측 평균', flex: 1, minWidth: 108 },
	{ key: 'errorRate', colNm: '오차율', flex: 0.85, minWidth: 90 },
	{ key: 'mae', colNm: 'MAE', flex: 0.8, minWidth: 88 },
	{ key: 'rmse', colNm: 'RMSE', flex: 0.8, minWidth: 88 },
	{ key: 'hitRate', colNm: '적중률', flex: 0.85, minWidth: 90 },
	{
		key: 'status',
		colNm: '상태',
		flex: 0.75,
		minWidth: 78,
		render: row => <AccuracyStatusBadge status={row.status} />,
	},
];

const EMPTY_CHART_DATA = {
	timeSeries: [],
};

const SERIES_META_KEYS = new Set(['tagNo', 'unit', 'name', 'label', 'pointNm']);

const POINT_TIME_KEYS = [
	'x',
	'time',
	'tm',
	'dttm',
	'predDttm',
	'datetime',
	'dateTime',
	'predTime',
	'predictTime',
	'predictionTime',
	'baseTime',
	'baseDttm',
];

const POINT_VALUE_KEYS = [
	'y',
	'value',
	'val',
	'predValue',
	'seriesValue',
	'anlsVal',
	'analysisValue',
	'actualVal',
	'actualValue',
	'measuredVal',
	'measuredValue',
	'predVal',
	'predValue',
	'predictionValue',
];

const STATS_DURATION_KEYS = [
	'duration',
	'durationCd',
	'durationCode',
	'interval',
	'intervalCd',
	'predInterval',
	'predIntervalCd',
	'predHorizon',
	'predHorizonCd',
	'horizon',
	'horizonCd',
	'period',
	'periodCd',
	'leadTime',
	'leadTimeCd',
];

const STATS_ACTUAL_KEYS = [
	'actualAvg',
	'actual',
	'actualValue',
	'actualVal',
	'measured',
	'measuredValue',
	'measuredVal',
	'obsValue',
];
const STATS_PREDICTED_KEYS = ['predAvg', 'predicted', 'predictedValue', 'predValue', 'predictionValue', 'forecastValue'];
const STATS_ERROR_RATE_KEYS = ['errorRate', 'errRate', 'errorPct', 'mape', 'MAPE', 'smape', 'sMAPE', 'SMAPE'];
const STATS_STATUS_KEYS = ['status', 'statusCd', 'statusGrade', 'grade', 'gradeCd', 'state', 'stateCd'];

function resolvePredictionTagOption(value) {
	return PREDICTION_TAG_OPTIONS.find(option => option.value === value) ?? PREDICTION_TAG_OPTIONS[0];
}

function getTodayDateTimeRange() {
	return {
		startDttm: dayjs().startOf('day').format(DATE_TIME_INPUT_FORMAT),
		endDttm: dayjs().endOf('day').format(DATE_TIME_INPUT_FORMAT),
	};
}

function formatApiDateTime(value) {
	if (!value) return undefined;
	return String(value).replace('T', ' ');
}

function formatTargetDateTime(value) {
	if (!value) return '';
	return dayjs(value).isValid() ? dayjs(value).format('YYYY-MM-DDTHH:mm') : String(value).replace(' ', 'T');
}

function readFirstValue(source, keys) {
	if (!source || typeof source !== 'object') return undefined;

	for (const key of keys) {
		if (source[key] !== undefined && source[key] !== null) return source[key];
	}

	return undefined;
}

function formatNumber(value, suffix = '') {
	if (value === undefined || value === null || value === '') return '-';
	const numericValue = Number(value);
	if (Number.isNaN(numericValue)) return String(value);

	return `${Number.isInteger(numericValue) ? numericValue : numericValue.toFixed(2)}${suffix}`;
}

function resolveDurationLabel(value) {
	if (!value) return '-';

	const normalizedValue = String(value).toUpperCase();
	const match = normalizedValue.match(/^([MH])(\d+)$/);
	if (!match) return String(value);

	const [, unit, amount] = match;
	return unit === 'M' ? `${Number(amount)}분` : `${Number(amount)}시간`;
}

function normalizeStatsPayload(responseData) {
	if (Array.isArray(responseData)) return responseData;
	if (Array.isArray(responseData?.data)) return responseData.data;
	if (Array.isArray(responseData?.result)) return responseData.result;
	if (Array.isArray(responseData?.list)) return responseData.list;
	if (Array.isArray(responseData?.items)) return responseData.items;
	if (Array.isArray(responseData?.rows)) return responseData.rows;

	return [];
}

function normalizeStatsRows(responseData) {
	return normalizeStatsPayload(responseData).map((row, index) => {
		const duration = readFirstValue(row, STATS_DURATION_KEYS);
		const actual = readFirstValue(row, STATS_ACTUAL_KEYS);
		const predicted = readFirstValue(row, STATS_PREDICTED_KEYS);
		const errorRate = readFirstValue(row, STATS_ERROR_RATE_KEYS);
		const status = readFirstValue(row, STATS_STATUS_KEYS);

		return {
			id: `${duration ?? 'duration'}-${index}`,
			durationLabel: resolveDurationLabel(duration),
			actual: formatNumber(actual),
			predicted: formatNumber(predicted),
			errorRate: formatNumber(errorRate, '%'),
			mae: formatNumber(row?.mae ?? row?.MAE),
			rmse: formatNumber(row?.rmse ?? row?.RMSE),
			hitRate: formatNumber(row?.hitRate ?? row?.hitRt ?? row?.accuracy ?? row?.accuracyRate, '%'),
			status: status ?? '-',
		};
	});
}

function toChartPoint(point, valueKeys = POINT_VALUE_KEYS) {
	if (!point || typeof point !== 'object') return null;

	const x = readFirstValue(point, POINT_TIME_KEYS);
	const y = readFirstValue(point, valueKeys);
	const numericValue = Number(y);

	if (!x || Number.isNaN(numericValue)) return null;

	return {
		x: typeof x === 'string' ? x.replace(' ', 'T') : x,
		y: numericValue,
	};
}

function normalizePointSeq(pointSeq, valueKeys) {
	if (!Array.isArray(pointSeq)) return [];

	return pointSeq.map(point => toChartPoint(point, valueKeys)).filter(Boolean);
}

function resolvePredictionSeriesLabel(key) {
	if (key === 'actual') return '실측';

	const match = String(key).match(/^([MH])(\d+)$/i);
	if (!match) return key;

	const [, unit, amount] = match;
	return unit.toUpperCase() === 'M' ? `예측 ${Number(amount)}분` : `예측 ${Number(amount)}시간`;
}

function resolvePredictionSeriesOrder(key) {
	if (key === 'actual') return 0;

	const match = String(key).match(/^([MH])(\d+)$/i);
	if (!match) return Number.MAX_SAFE_INTEGER;

	const [, unit, amount] = match;
	return unit.toUpperCase() === 'M' ? Number(amount) : Number(amount) * 60;
}

function normalizeTimeSeriesPayload(payload) {
	if (!payload || typeof payload !== 'object') return [];

	return Object.entries(payload)
		.filter(([key, value]) => !SERIES_META_KEYS.has(key) && Array.isArray(value))
		.map(([key, value]) => ({
			key,
			label: resolvePredictionSeriesLabel(key),
			data: normalizePointSeq(value),
			borderDash: key === 'actual' ? [] : [4, 3],
			pointRadius: 0,
			order: resolvePredictionSeriesOrder(key),
		}))
		.filter(series => series.data.length > 0)
		.sort((a, b) => a.order - b.order)
		.map(({ order, ...series }) => series);
}

function normalizeSeriesPayload(payload, fallback = EMPTY_CHART_DATA) {
	if (!payload) return fallback;

	const timeSeries = normalizeTimeSeriesPayload(payload);

	return timeSeries.length > 0 ? { timeSeries } : fallback;
}

function unwrapResponseData(response) {
	return response?.data ?? response?.result ?? response;
}

function resolveSeriesPair(responseData) {
	return {
		flow: responseData?.flow ?? responseData?.flowSeries ?? responseData?.flowAccuracySeries ?? responseData?.flowTimeSeries,
		pressure:
			responseData?.pressure ??
			responseData?.pressureSeries ??
			responseData?.pressureAccuracySeries ??
			responseData?.pressureTimeSeries,
	};
}

function hasChartValues(chartData) {
	return (chartData?.timeSeries ?? []).some(series =>
		(series.data ?? []).some(point => point?.y !== undefined && point?.y !== null)
	);
}

function SectionTitle({ children, action }) {
	return (
		<div className="flex h-8 items-center gap-3 bg-[linear-gradient(90deg,#0d6d87,#114f83_68%,rgba(17,79,131,0.16))] px-3 text-[14px] font-extrabold text-sky-50 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
			<span className="min-w-0 flex-1 truncate">{children}</span>
			{action ? <div className="shrink-0">{action}</div> : null}
		</div>
	);
}

function ChartDetailToggleButton({ isOpen, onClick }) {
	const Icon = isOpen ? IoContractOutline : IoExpandOutline;

	return (
		<button
			type="button"
			aria-label={isOpen ? '상세 테이블 닫기' : '상세 테이블 열기'}
			title={isOpen ? '상세 테이블 닫기' : '상세 테이블 열기'}
			onClick={event => {
				event.stopPropagation();
				onClick?.();
			}}
			className="inline-flex h-7 w-7 items-center justify-center rounded-[4px] border border-sky-100/75 bg-white text-slate-700 shadow-[0_1px_4px_rgba(0,0,0,0.24)] transition-colors hover:bg-sky-50 hover:text-sky-700"
		>
			<Icon className="h-3.5 w-3.5" />
		</button>
	);
}

function PredictionPanel({ type, title, unit, chartData, rows, yMin, yMax, showDetail, onChartClick, onToggleDetail }) {
	const canShowDetail = hasChartValues(chartData);

	return (
		<CommonCard className="flex min-h-0 flex-col overflow-hidden rounded-[4px] bg-[rgba(6,18,42,0.78)] p-2">
			<SectionTitle
				action={
					canShowDetail ? (
						<ChartDetailToggleButton isOpen={showDetail} onClick={() => onToggleDetail?.({ type })} />
					) : null
				}
			>
				{title}
			</SectionTitle>
			<div
				className={[
					'mt-2 rounded-[2px] border border-sky-200/20 bg-white p-2 transition-[height] duration-200 ease-out',
					canShowDetail ? 'cursor-pointer' : '',
					showDetail && canShowDetail ? 'h-[260px]' : 'min-h-[420px] flex-1',
				].join(' ')}
			>
				<PredictionTimeSeriesChart
					chartId={`pred-monitor-${type}`}
					type={type}
					title={title}
					unit={unit}
					series={chartData}
					yMin={yMin}
					yMax={yMax}
					onChartClick={canShowDetail ? onChartClick : undefined}
				/>
			</div>
			{showDetail && canShowDetail ? (
				<div className="mt-2 min-h-0 flex-1">
					<SectionTitle>{title.replace('비교', '비교상세 현황')}</SectionTitle>
					<div className="mt-2 h-[214px] overflow-hidden rounded-[4px] border border-sky-200/20 bg-slate-950/30">
						<CommonTable
							colSeq={DETAIL_TABLE_COL_SEQ}
							rowSeq={rows}
							getRowKey={row => row.id}
							rowHeight={34}
							columnHeaderHeight={36}
							emptyMsg="차트 포인트 선택 후 상세 현황이 표시됩니다."
							enableSorting={true}
							enableFiltering={true}
							enableColumnResize={true}
						/>
					</div>
				</div>
			) : null}
		</CommonCard>
	);
}

function PredMonitor() {
	const didInitialSearchRef = useRef(false);
	const initialDateRange = useMemo(() => getTodayDateTimeRange(), []);
	const [startDttm, setStartDttm] = useState(initialDateRange.startDttm);
	const [endDttm, setEndDttm] = useState(initialDateRange.endDttm);
	const [selectedTargetValue, setSelectedTargetValue] = useState(PREDICTION_TAG_OPTIONS[0].value);
	const [appliedFilters, setAppliedFilters] = useState({
		...initialDateRange,
		...PREDICTION_TAG_OPTIONS[0],
	});
	const [chartData, setChartData] = useState({
		flow: EMPTY_CHART_DATA,
		pressure: EMPTY_CHART_DATA,
	});
	const [detailRowsByType, setDetailRowsByType] = useState({
		flow: [],
		pressure: [],
	});
	const [visibleDetailTypeSeq, setVisibleDetailTypeSeq] = useState([]);
	const [isLoading, setIsLoading] = useState(false);
	const [isDateRangeValid, setIsDateRangeValid] = useState(true);

	const selectedTargetLabel = useMemo(() => resolvePredictionTagOption(appliedFilters.value).label, [appliedFilters.value]);

	const handleChartClick = useCallback(
		async chartClickInfo => {
			const target = formatTargetDateTime(chartClickInfo.targetLabel);
			const tagNo = chartClickInfo.type === 'flow' ? appliedFilters.flowTagNo : appliedFilters.pressureTagNo;

			if (!target || !tagNo) return;

			try {
				const response = await predApi.getAccuracyStats({
					skipErrorToast: true,
					searchParams: {
						tagNo,
						target,
						base: 'SMAPE',
					},
				});
				const rows = normalizeStatsRows(unwrapResponseData(response));

				setDetailRowsByType(prev => ({
					...prev,
					[chartClickInfo.type]: rows,
				}));
				setVisibleDetailTypeSeq(prev => (prev.includes(chartClickInfo.type) ? prev : [...prev, chartClickInfo.type]));
			} catch {
				showToast('error', '예측구간별 정확도 통계 조회에 실패했습니다.');
			}
		},
		[appliedFilters.flowTagNo, appliedFilters.pressureTagNo]
	);

	const handleDetailToggleClick = useCallback(chartClickInfo => {
		setVisibleDetailTypeSeq(prev =>
			prev.includes(chartClickInfo.type)
				? prev.filter(type => type !== chartClickInfo.type)
				: [...prev, chartClickInfo.type]
		);
	}, []);

	const handleSearchClick = useCallback(async () => {
		if (!isDateRangeValid) return;

		const selectedTarget = resolvePredictionTagOption(selectedTargetValue);

		setIsLoading(true);
		try {
			const response = await predApi.getAccuracySeries({
				skipErrorToast: true,
				searchParams: {
					from: formatApiDateTime(startDttm),
					to: formatApiDateTime(endDttm),
					flowTagNo: selectedTarget.flowTagNo,
					pressureTagNo: selectedTarget.pressureTagNo,
				},
			});
			const responseData = unwrapResponseData(response);
			const seriesPair = resolveSeriesPair(responseData);

			setChartData({
				flow: normalizeSeriesPayload(seriesPair.flow, EMPTY_CHART_DATA),
				pressure: normalizeSeriesPayload(seriesPair.pressure, EMPTY_CHART_DATA),
			});
			setDetailRowsByType({
				flow: [],
				pressure: [],
			});
			setVisibleDetailTypeSeq([]);
			setAppliedFilters({
				startDttm,
				endDttm,
				...selectedTarget,
				flowTagNo: seriesPair.flow?.tagNo ?? selectedTarget.flowTagNo,
				pressureTagNo: seriesPair.pressure?.tagNo ?? selectedTarget.pressureTagNo,
			});
		} catch {
			showToast('error', '예측 정확도 시계열 조회에 실패했습니다.');
		} finally {
			setIsLoading(false);
		}
	}, [endDttm, isDateRangeValid, selectedTargetValue, startDttm]);

	const handleDateRangeValidationChange = useCallback(({ isValid }) => {
		setIsDateRangeValid(isValid);
	}, []);

	useEffect(() => {
		if (didInitialSearchRef.current) return;

		didInitialSearchRef.current = true;
		handleSearchClick();
	}, [handleSearchClick]);

	return (
		<div className="flex h-full min-h-0 flex-col gap-3 bg-[radial-gradient(circle_at_top,rgba(34,87,183,0.32),rgba(8,22,52,0.16)_36%,rgba(4,10,25,0.98)_82%)] p-1 text-sky-50">
			<div className="flex shrink-0 flex-wrap items-center justify-end gap-2 px-3 py-2">
				<CommonDateTimeRangePicker
					startValue={startDttm}
					endValue={endDttm}
					onStartChange={setStartDttm}
					onEndChange={setEndDttm}
					onValidationChange={handleDateRangeValidationChange}
				/>
				<CommonSelect
					label="예측 태그"
					value={selectedTargetValue}
					options={PREDICTION_TAG_OPTIONS}
					onChange={setSelectedTargetValue}
					sx={TAG_SELECT_SX}
					InputLabelProps={{ shrink: true }}
					menuProps={{
						PaperProps: {
							sx: {
								border: '1px solid rgba(110,185,255,0.28)',
								background: 'linear-gradient(180deg, rgba(16,43,82,0.98), rgba(7,22,48,0.98))',
								color: '#e6f6ff',
							},
						},
					}}
				/>
				<CommonButton
					text="조회"
					size="lg"
					Icon={IoSearchOutline}
					iconClassName="h-4 w-4"
					onClick={handleSearchClick}
					className="h-[34px] min-w-[72px]"
					isLoading={isLoading}
					disabled={!isDateRangeValid}
					preventDoubleClick
				/>
			</div>

			<div className="grid min-h-0 flex-1 grid-cols-1 gap-3 xl:grid-cols-2">
				<PredictionPanel
					type="flow"
					title={`유량 예측 및 실측 비교 (${selectedTargetLabel} - ${appliedFilters.flowTagNo})`}
					unit="m³/h"
					chartData={chartData.flow}
					rows={detailRowsByType.flow}
					showDetail={visibleDetailTypeSeq.includes('flow')}
					onChartClick={handleChartClick}
					onToggleDetail={handleDetailToggleClick}
				/>
				<PredictionPanel
					type="pressure"
					title={`압력 예측 및 실측 비교 (${selectedTargetLabel} - ${appliedFilters.pressureTagNo})`}
					unit="kgf/cm²"
					chartData={chartData.pressure}
					rows={detailRowsByType.pressure}
					showDetail={visibleDetailTypeSeq.includes('pressure')}
					onChartClick={handleChartClick}
					onToggleDetail={handleDetailToggleClick}
				/>
			</div>
		</div>
	);
}

export default PredMonitor;
