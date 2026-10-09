import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { CommonButton } from '@/web/components/common/CommonButton';
import CommonCard from '@/web/components/common/CommonCard';
import CommonChart from '@/web/components/common/CommonChart';
import CommonTable from '@/web/components/common/CommonTable';
import MapCanvas from '@/web/components/common/MapCanvas';
import CommonTabBtn from '@/web/components/common/CommonTabBtn';
import CommonDialog from '@/web/components/CommonDialog';
import SubTitleBar from '@/web/components/SubTitleBar';
import TitleBar from '@/web/components/TitleBar';
import { MoniterOrSimulation } from '@/consts';
import { getMap } from '@/web/js/utils/mapRegistry';

const summaryCardSeq = [
	{
		key: 'flow',
		title: '유량',
		itemSeq: [
			{ label: '적합', value: '4', rate: '2%' },
			{ label: '적정', value: '1', rate: '5%' },
			{ label: '미흡', value: '8', rate: '41%' },
		],
	},
	{
		key: 'pressure',
		title: '압력',
		itemSeq: [
			{ label: '적합', value: '1', rate: '5%' },
			{ label: '적정', value: '4', rate: '21%' },
			{ label: '미흡', value: '12', rate: '11%' },
		],
	},
];

const monitorDetailRowSeq = [
	{
		key: 'row-1',
		name: '추정송수관로',
		flowStatus: '미존',
		flowMeasure: '21,806',
		flowAnalyze: '20,709',
		flowErr: '5%',
		pressureStatus: '미존',
		pressureMeasure: '6.48',
		pressureAnalyze: '7.81',
		pressureErr: '20.6%',
	},
	{
		key: 'row-2',
		name: '고산분기',
		flowStatus: '격점',
		flowMeasure: '141',
		flowAnalyze: '141',
		flowErr: '0%',
		pressureStatus: '미존',
		pressureMeasure: '7.37',
		pressureAnalyze: '8.36',
		pressureErr: '13.4%',
	},
	{
		key: 'row-3',
		name: '군봉분기',
		flowStatus: '미존',
		flowMeasure: '2,416',
		flowAnalyze: '874',
		flowErr: '63.8%',
		pressureStatus: '미존',
		pressureMeasure: '8.16',
		pressureAnalyze: '9.82',
		pressureErr: '20.4%',
	},
	{
		key: 'row-4',
		name: '금구(화집)분기',
		flowStatus: '미존',
		flowMeasure: '522',
		flowAnalyze: '318',
		flowErr: '39.1%',
		pressureStatus: '미존',
		pressureMeasure: '8.99',
		pressureAnalyze: '10.20',
		pressureErr: '13.5%',
	},
	{
		key: 'row-5',
		name: '농수산분기',
		flowStatus: '미존',
		flowMeasure: '7,010',
		flowAnalyze: '5,671',
		flowErr: '19.1%',
		pressureStatus: '미존',
		pressureMeasure: '7.90',
		pressureAnalyze: '10.33',
		pressureErr: '43.3%',
	},
];

const monitorDetailColSeq = [
	{
		key: 'name',
		colNm: '구분',
		widthClassName: 'w-[19%]',
		headClassName: 'border border-[#27425f] bg-[#163667] px-2.5 py-1.5 font-semibold',
		cellClassName: 'border border-[#20344d] px-2.5 py-1.5 text-center',
	},
	{
		key: 'flowStatus',
		colNm: '상태',
		widthClassName: 'w-[8%]',
		headClassName: 'border border-[#27425f] bg-[#163667] px-2.5 py-1.5 font-semibold',
		cellClassName: 'border border-[#20344d] px-2.5 py-1.5 text-center',
	},
	{
		key: 'flowMeasure',
		colNm: '계측값',
		headClassName: 'border border-[#27425f] bg-[#1a417c] px-2.5 py-1.5 font-semibold',
		cellClassName: 'border border-[#20344d] px-2.5 py-1.5 text-right',
	},
	{
		key: 'flowAnalyze',
		colNm: '분석값',
		headClassName: 'border border-[#27425f] bg-[#1a417c] px-2.5 py-1.5 font-semibold',
		cellClassName: 'border border-[#20344d] px-2.5 py-1.5 text-right',
	},
	{
		key: 'flowErr',
		colNm: '오차율',
		headClassName: 'border border-[#27425f] bg-[#1a417c] px-2.5 py-1.5 font-semibold',
		cellClassName: 'border border-[#20344d] px-2.5 py-1.5 text-right',
	},
	{
		key: 'pressureStatus',
		colNm: '상태',
		widthClassName: 'w-[8%]',
		headClassName: 'border border-[#27425f] bg-[#163667] px-2.5 py-1.5 font-semibold',
		cellClassName: 'border border-[#20344d] px-2.5 py-1.5 text-center',
	},
	{
		key: 'pressureMeasure',
		colNm: '계측값',
		headClassName: 'border border-[#27425f] bg-[#1a417c] px-2.5 py-1.5 font-semibold',
		cellClassName: 'border border-[#20344d] px-2.5 py-1.5 text-right',
	},
	{
		key: 'pressureAnalyze',
		colNm: '분석값',
		headClassName: 'border border-[#27425f] bg-[#1a417c] px-2.5 py-1.5 font-semibold',
		cellClassName: 'border border-[#20344d] px-2.5 py-1.5 text-right',
	},
	{
		key: 'pressureErr',
		colNm: '오차율',
		headClassName: 'border border-[#27425f] bg-[#1a417c] px-2.5 py-1.5 font-semibold',
		cellClassName: 'border border-[#20344d] px-2.5 py-1.5 text-right',
	},
];

const monitorDetailHeadRowSeq = [
	[
		{
			key: 'name-group',
			colNm: '구분',
			rowSpan: 2,
			headClassName: 'w-[19%] border border-[#27425f] bg-[#163667] px-2.5 py-1.5 font-semibold',
		},
		{
			key: 'flow-status-group',
			colNm: '상태',
			rowSpan: 2,
			headClassName: 'w-[8%] border border-[#27425f] bg-[#163667] px-2.5 py-1.5 font-semibold',
		},
		{
			key: 'flow-group',
			colNm: '유량(㎥/h)',
			colSpan: 3,
			headClassName: 'border border-[#27425f] bg-[#163667] px-2.5 py-1.5 font-semibold',
		},
		{
			key: 'pressure-status-group',
			colNm: '상태',
			rowSpan: 2,
			headClassName: 'w-[8%] border border-[#27425f] bg-[#163667] px-2.5 py-1.5 font-semibold',
		},
		{
			key: 'pressure-group',
			colNm: '압력(kgf/㎠)',
			colSpan: 3,
			headClassName: 'border border-[#27425f] bg-[#163667] px-2.5 py-1.5 font-semibold',
		},
	],
	[
		{
			key: 'flow-measure-head',
			colNm: '계측값',
			headClassName: 'border border-[#27425f] bg-[#1a417c] px-2.5 py-1.5 font-semibold',
		},
		{
			key: 'flow-analyze-head',
			colNm: '분석값',
			headClassName: 'border border-[#27425f] bg-[#1a417c] px-2.5 py-1.5 font-semibold',
		},
		{
			key: 'flow-err-head',
			colNm: '오차율',
			headClassName: 'border border-[#27425f] bg-[#1a417c] px-2.5 py-1.5 font-semibold',
		},
		{
			key: 'pressure-measure-head',
			colNm: '계측값',
			headClassName: 'border border-[#27425f] bg-[#1a417c] px-2.5 py-1.5 font-semibold',
		},
		{
			key: 'pressure-analyze-head',
			colNm: '분석값',
			headClassName: 'border border-[#27425f] bg-[#1a417c] px-2.5 py-1.5 font-semibold',
		},
		{
			key: 'pressure-err-head',
			colNm: '오차율',
			headClassName: 'border border-[#27425f] bg-[#1a417c] px-2.5 py-1.5 font-semibold',
		},
	],
];

const simulationPumpComboSeq = [
	{ key: 'combo-1', order: 1, oldPumpSeq: [2, 4, 6, 7], newPumpSeq: [11], powerUnit: '0.19', totalCount: '4대' },
	{ key: 'combo-2', order: 2, oldPumpSeq: [3, 5, 6, 7], newPumpSeq: [11], powerUnit: '0.20', totalCount: '4대' },
	{ key: 'combo-3', order: 3, oldPumpSeq: [4, 5, 6], newPumpSeq: [8, 11], powerUnit: '0.21', totalCount: '4.5대' },
];

const simulationResultRowSeq = [
	{
		key: 'sim-1',
		division1: '통합송수펌프',
		flow1: '19,342',
		pressure1: '9.26',
		division2: '고산분기',
		flow2: '139',
		pressure2: '9.81',
	},
	{
		key: 'sim-2',
		division1: '군봉분기',
		flow1: '2,815',
		pressure1: '10.57',
		division2: '금구(화집)분기',
		flow2: '330',
		pressure2: '11.88',
	},
	{
		key: 'sim-3',
		division1: '농수산분기',
		flow1: '7,665',
		pressure1: '11.60',
		division2: '대야분기',
		flow2: '-',
		pressure2: '10.74',
	},
	{ key: 'sim-4', division1: '봉동분기', flow1: '0', pressure1: '12.25', division2: '상리분기', flow2: '-', pressure2: '9.35' },
	{
		key: 'sim-5',
		division1: '서천분기',
		flow1: '-',
		pressure1: '10.38',
		division2: '신지분기',
		flow2: '11,603',
		pressure2: '11.52',
	},
	{
		key: 'sim-6',
		division1: '오식도분기',
		flow1: '-',
		pressure1: '10.66',
		division2: '용봉분기',
		flow2: '834',
		pressure2: '10.97',
	},
	{
		key: 'sim-7',
		division1: '용진분기',
		flow1: '237',
		pressure1: '10.03',
		division2: '이서분기',
		flow2: '41',
		pressure2: '8.30',
	},
	{ key: 'sim-8', division1: '익산분기', flow1: '0', pressure1: '12.29', division2: '장항분기', flow2: '0', pressure2: '3.25' },
];

const initialReservoirDemandRowSeq = [
	[
		{ name: '효자', value: '1311' },
		{ name: '팔복', value: '1562.7' },
		{ name: '천마', value: '2815' },
	],
	[
		{ name: '인후', value: '2918' },
		{ name: '익산분기', value: '2676.95' },
		{ name: '이서', value: '152.8' },
	],
	[
		{ name: '용진', value: '100.125' },
		{ name: '왕궁관말', value: '833.7' },
		{ name: '완주산단', value: '1506.9' },
	],
	[
		{ name: '소양', value: '137.1' },
		{ name: '봉동', value: '0' },
		{ name: '대야', value: '2500' },
	],
	[
		{ name: '대성', value: '158.625' },
		{ name: '나운', value: '2108' },
		{ name: '김제', value: '828.0625' },
	],
	[
		{ name: '고산분기', value: '139' },
		{ name: '한산', value: '83' },
		{ name: '금암', value: '271' },
	],
	[
		{ name: '지곡', value: '621.2' },
		{ name: '중화산', value: '402.1729' },
		{ name: '서신', value: '287.2115' },
	],
	[
		{ name: '송천', value: '489.4776' },
		{ name: '서천', value: '0' },
		{ name: '대성', value: '158.625' },
	],
	[
		{ name: '왕궁관말', value: '833.7' },
		{ name: '군봉', value: '7000' },
		{ name: '백산', value: '38.8219' },
	],
];

function buildFlowChartConfig() {
	return {
		type: 'line',
		data: {
			labels: ['02:30', '03:40', '05:00', '06:15', '07:30', '09:10', '11:15', '13:20', '14:50'],
			datasets: [
				{
					label: '격점',
					data: [18800, 19620, 20100, 19810, 21200, 20420, 19320, 18670, 18210],
					borderColor: '#95df67',
					backgroundColor: 'rgba(149,223,103,0.18)',
					fill: false,
					tension: 0.32,
					pointRadius: 0,
					borderWidth: 2,
				},
				{
					label: '분석값',
					data: [14900, 13680, 12130, 13110, 15220, 17480, 18310, 18920, 19740],
					borderColor: '#5b84ff',
					backgroundColor: 'rgba(91,132,255,0.16)',
					fill: false,
					tension: 0.32,
					pointRadius: 0,
					borderWidth: 2,
				},
			],
		},
		options: {
			maintainAspectRatio: false,
			interaction: { mode: 'index', intersect: false },
			plugins: {
				legend: {
					display: true,
					position: 'top',
					align: 'start',
					labels: { color: '#d5eeff', boxWidth: 10, usePointStyle: true, pointStyle: 'circle', padding: 12 },
				},
				tooltip: {
					enabled: true,
					backgroundColor: 'rgba(8, 26, 61, 0.95)',
					titleColor: '#f8fbff',
					bodyColor: '#d5eeff',
					borderColor: 'rgba(125, 211, 252, 0.35)',
					borderWidth: 1,
				},
			},
			scales: {
				x: {
					grid: { color: 'rgba(145, 210, 255, 0.08)' },
					ticks: { color: '#a8cfff', font: { size: 10 } },
				},
				y: {
					min: 0,
					max: 24000,
					grid: { color: 'rgba(145, 210, 255, 0.08)' },
					ticks: { color: '#a8cfff', font: { size: 10 } },
					title: {
						display: true,
						text: '㎥/h',
						color: '#a8cfff',
						font: { size: 10, weight: '600' },
					},
				},
			},
		},
	};
}

function buildPressureChartConfig() {
	return {
		type: 'line',
		data: {
			labels: ['02:30', '03:40', '05:00', '06:15', '07:30', '09:10', '11:15', '13:20', '14:50'],
			datasets: [
				{
					label: '격점',
					data: [6.8, 7.1, 7.2, 7.25, 7.28, 7.26, 7.24, 7.21, 7.25],
					borderColor: '#7aa5ff',
					backgroundColor: 'rgba(122,165,255,0.16)',
					fill: false,
					tension: 0.28,
					pointRadius: 0,
					borderWidth: 2,
				},
				{
					label: '분석값',
					data: [7.05, 7.18, 7.21, 7.42, 7.48, 7.46, 7.44, 7.45, 7.49],
					borderColor: '#9be271',
					backgroundColor: 'rgba(155,226,113,0.18)',
					fill: false,
					tension: 0.28,
					pointRadius: 0,
					borderWidth: 2,
				},
			],
		},
		options: {
			maintainAspectRatio: false,
			interaction: { mode: 'index', intersect: false },
			plugins: {
				legend: {
					display: true,
					position: 'top',
					align: 'start',
					labels: { color: '#d5eeff', boxWidth: 10, usePointStyle: true, pointStyle: 'circle', padding: 12 },
				},
				tooltip: {
					enabled: true,
					backgroundColor: 'rgba(8, 26, 61, 0.95)',
					titleColor: '#f8fbff',
					bodyColor: '#d5eeff',
					borderColor: 'rgba(125, 211, 252, 0.35)',
					borderWidth: 1,
				},
			},
			scales: {
				x: {
					grid: { color: 'rgba(145, 210, 255, 0.08)' },
					ticks: { color: '#a8cfff', font: { size: 10 } },
				},
				y: {
					min: 0,
					max: 10,
					grid: { color: 'rgba(145, 210, 255, 0.08)' },
					ticks: { color: '#a8cfff', font: { size: 10 } },
					title: {
						display: true,
						text: 'kgf/㎠',
						color: '#a8cfff',
						font: { size: 10, weight: '600' },
					},
				},
			},
		},
	};
}

function formatNumber(value) {
	const numericValue = Number(String(value).replace(/,/g, ''));
	if (Number.isNaN(numericValue)) {
		return String(value);
	}

	return numericValue.toLocaleString('ko-KR');
}

function sumReservoirDemandRows(rowSeq) {
	return rowSeq.reduce(
		(total, row) =>
			total +
			row.reduce((rowTotal, cell) => {
				const numericValue = Number(String(cell.value).replace(/,/g, ''));
				return rowTotal + (Number.isNaN(numericValue) ? 0 : numericValue);
			}, 0),
		0
	);
}

function PumpChip({ value }) {
	return (
		<span className="inline-flex h-7 min-w-7 items-center justify-center rounded-full border border-sky-300/25 bg-[linear-gradient(180deg,#2d6fd1,#1a4f9e)] px-2 text-[12px] font-semibold text-white shadow-[0_0_16px_rgba(20,132,255,0.2)]">
			{value}
		</span>
	);
}

function PipNetAnals() {
	const navigate = useNavigate();
	const { mode = 'monitor' } = useParams();
	const flowChartConfig = useMemo(() => buildFlowChartConfig(), []);
	const pressureChartConfig = useMemo(() => buildPressureChartConfig(), []);
	const [simulationFlowInput, setSimulationFlowInput] = useState('23000');
	const [selectedPumpCombo, setSelectedPumpCombo] = useState(simulationPumpComboSeq[0].key);
	const [isDemandModalOpen, setIsDemandModalOpen] = useState(false);
	const [isMapExpanded, setIsMapExpanded] = useState(false);
	const [isModelEditModalOpen, setIsModelEditModalOpen] = useState(false);
	const [reservoirDemandRowSeq, setReservoirDemandRowSeq] = useState(initialReservoirDemandRowSeq);
	const [draftReservoirDemandRowSeq, setDraftReservoirDemandRowSeq] = useState(initialReservoirDemandRowSeq);
	const isMonitorMode = mode !== 'simulation';
	const activeMapId = isMonitorMode ? 'monitor-left-map' : 'simulation-left-map';
	const pageTitle = isMonitorMode ? '관망해석 모니터링' : '관망해석 시뮬레이션';
	const simulationFlowDisplay = formatNumber(simulationFlowInput || '0');

	const resizeActiveMap = () => {
		window.requestAnimationFrame(() => {
			window.requestAnimationFrame(() => {
				getMap(activeMapId)?.updateSize();
			});
		});
	};

	const openDemandModal = () => {
		setDraftReservoirDemandRowSeq(reservoirDemandRowSeq.map(row => row.map(cell => ({ ...cell }))));
		setIsDemandModalOpen(true);
	};

	const handleMapExpandToggle = () => {
		setIsMapExpanded(prevState => !prevState);
	};

	const handleDemandValueChange = (rowIndex, cellIndex, nextValue) => {
		setDraftReservoirDemandRowSeq(prevRowSeq =>
			prevRowSeq.map((row, currentRowIndex) =>
				currentRowIndex !== rowIndex
					? row
					: row.map((cell, currentCellIndex) =>
							currentCellIndex !== cellIndex
								? cell
								: {
										...cell,
										value: nextValue.replace(/[^0-9.]/g, ''),
									}
						)
			)
		);
	};

	const handleDemandSave = () => {
		setReservoirDemandRowSeq(draftReservoirDemandRowSeq.map(row => row.map(cell => ({ ...cell }))));
		setSimulationFlowInput(String(Math.round(sumReservoirDemandRows(draftReservoirDemandRowSeq))));
	};

	useEffect(() => {
		resizeActiveMap();
	}, [activeMapId, isMapExpanded]);

	const mapSection = (
		<CommonCard as="section" className="h-full min-h-0 min-w-0 p-2">
			<CommonCard className="relative h-full min-h-0 overflow-hidden rounded-[6px] bg-[linear-gradient(180deg,rgba(15,40,86,0.72),rgba(10,22,52,0.94))]">
				<MapCanvas mapId={activeMapId} className="absolute inset-0" />
				<div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,rgba(5,11,28,0.06),rgba(6,14,34,0.14)),radial-gradient(circle_at_30%_20%,rgba(108,168,255,0.08),transparent_30%)]" />
				<div className="absolute right-16 top-3 rounded-[2px] bg-black/55 px-3 py-1 text-[11px] font-medium tracking-normal text-white">
					{isMonitorMode ? '모니터링 시각 : 2025-11-05 14:30' : '시뮬레이션 시각 : 2025-11-04 17:12'}
				</div>
				<div className="absolute right-3 top-3 z-10 flex items-center gap-2">
					<button
						type="button"
						onClick={handleMapExpandToggle}
						className="flex h-8 w-8 items-center justify-center rounded-[4px] border border-[#243d5b] bg-[rgba(5,16,40,0.9)] text-[16px] leading-none text-sky-100 shadow-none transition hover:border-[#355a83] hover:text-white"
						aria-label={isMapExpanded ? '지도 페이지 전체화면 닫기' : '지도 페이지 전체화면'}
						title={isMapExpanded ? '지도 페이지 전체화면 닫기' : '지도 페이지 전체화면'}
					>
						{isMapExpanded ? '⤡' : '⤢'}
					</button>
				</div>
			</CommonCard>
		</CommonCard>
	);

	return (
		<div className="h-full min-h-0 overflow-hidden bg-[radial-gradient(circle_at_top,rgba(34,87,183,0.34),rgba(8,22,52,0.16)_36%,rgba(4,10,25,0.96)_82%)] px-1 pb-1 text-sky-50">
			<div className="flex h-full min-h-0 flex-col gap-2">
				<div className="grid items-start gap-3" style={{ gridTemplateColumns: '1.02fr 1.38fr' }}>
					<div className="flex min-w-0 items-start justify-between gap-3 pr-2">
						<TitleBar title={pageTitle} size="sm" className="max-w-[320px]" />
						{isMonitorMode ? (
							<CommonButton
								text="모형편집"
								size="sm"
								className="mt-3 h-8 border-[#243d5b] bg-[rgba(5,16,40,0.88)] px-3 text-[11px] text-sky-100 hover:border-[#355a83] hover:text-white"
								onClick={() => setIsModelEditModalOpen(true)}
							/>
						) : null}
					</div>
					<div className="flex items-center justify-end gap-2">
						{MoniterOrSimulation.map(label => {
							const nextMode = label === '모니터링' ? 'monitor' : 'simulation';
							return (
								<CommonTabBtn
									key={label}
									label={label}
									isActive={mode === nextMode}
									onClick={() => navigate(`/smartEMS/${nextMode}`)}
									className="ml-0 h-[24px] rounded-[14px] px-3 text-[11px]"
								/>
							);
						})}
					</div>
				</div>

				{isMapExpanded ? (
					<div className="min-h-0 flex-1">{mapSection}</div>
				) : (
					<div className="grid min-h-0 flex-1 gap-3" style={{ gridTemplateColumns: '1.02fr 1.38fr' }}>
						{mapSection}

						{isMonitorMode ? (
							<section className="grid min-h-0 min-w-0 grid-rows-[auto_minmax(0,1fr)] gap-2">
								<CommonCard className="p-2.5">
									<SubTitleBar title="관망해석 현황" className="mb-2" />
									<div className="grid grid-cols-2 gap-2.5">
										{summaryCardSeq.map(group => (
											<div key={group.key} className="flex flex-col gap-1.5">
												<div className="flex items-center justify-between">
													<span className="text-[13px] font-semibold text-sky-100">{group.title}</span>
													<span className="text-[10px] text-sky-200/65">오늘</span>
												</div>
												<div className="grid grid-cols-3 gap-2">
													{group.itemSeq.map(item => (
														<CommonCard
															key={`${group.key}-${item.label}`}
															className="rounded-[4px] bg-[linear-gradient(180deg,rgba(13,33,71,0.96),rgba(10,26,56,0.9))] px-3 py-1.5 shadow-none"
														>
															<div className="text-[10px] text-sky-200/74">{item.label}</div>
															<div className="mt-1 flex items-end justify-between gap-1">
																<span className="text-[22px] leading-none text-sky-50">
																	{item.value}
																</span>
																<span className="pb-[2px] text-[10px] text-sky-300/70">
																	({item.rate})
																</span>
															</div>
														</CommonCard>
													))}
												</div>
											</div>
										))}
									</div>
								</CommonCard>

								<div className="grid min-h-0 grid-rows-[minmax(0,1.08fr)_minmax(0,0.72fr)] gap-2">
									<CommonCard className="flex min-h-0 flex-col overflow-hidden p-2.5">
										<SubTitleBar title="해석 상세현황" className="mb-2" />
										<CommonCard className="min-h-0 flex-1 overflow-auto rounded-[6px] bg-[rgba(7,19,43,0.78)]">
											<CommonTable
												colSeq={monitorDetailColSeq}
												headRowSeq={monitorDetailHeadRowSeq}
												rowSeq={monitorDetailRowSeq}
												getRowKey={row => row.key}
												rowClassName="hover:bg-sky-500/6"
												ariaLabel="해석 상세현황"
											/>
										</CommonCard>
									</CommonCard>

									<div className="grid min-h-0 grid-cols-2 gap-2">
										<CommonCard className="min-h-0 p-2">
											<CommonChart chartConfig={flowChartConfig} variant="plain" className="h-full" />
										</CommonCard>
										<CommonCard className="min-h-0 p-2">
											<CommonChart chartConfig={pressureChartConfig} variant="plain" className="h-full" />
										</CommonCard>
									</div>
								</div>
							</section>
						) : (
							<section className="grid min-h-0 min-w-0 grid-rows-[auto_minmax(0,1fr)] gap-2">
								<CommonCard className="min-w-0 p-2.5">
									<SubTitleBar title="관망해석 설정" className="mb-2" />
									<div className="flex flex-wrap items-center justify-between gap-3">
										<div className="text-[16px] font-semibold text-sky-50">정수장 토출 유량 설정</div>
										<CommonButton
											text="배수지 수요량 설정"
											size="sm"
											className="h-[30px] px-3 text-[11px]"
											onClick={openDemandModal}
										/>
									</div>
									<CommonCard className="mt-2.5 flex items-stretch overflow-hidden rounded-[4px] bg-[rgba(8,22,52,0.88)]">
										<input
											value={simulationFlowInput}
											onChange={event => setSimulationFlowInput(event.target.value.replace(/[^\d]/g, ''))}
											className="h-[42px] min-w-0 flex-1 bg-transparent px-4 text-[24px] font-semibold text-sky-50 outline-none"
										/>
										<button
											type="button"
											className="w-[82px] shrink-0 border-l border-sky-300/24 bg-[linear-gradient(180deg,#1f77d7,#155cb0)] text-[15px] font-semibold text-white"
										>
											입력
										</button>
									</CommonCard>
									<div className="mt-2 flex items-end justify-end gap-[14px] whitespace-nowrap text-right">
										<span
											className="pt-1 text-[24px] leading-none text-[#c3eaff] [text-shadow:0_0_5px_rgba(101,183,255)]"
											style={{ fontFamily: 'KHNPHUotfR' }}
										>
											정수장 토출 유량
										</span>
										<div className="flex items-end gap-[7px]">
											<span
												className="text-[44px] leading-[0.9] text-[#e8faff] [text-shadow:0_0_7px_rgba(101,183,255)]"
												style={{ fontFamily: 'LABDigital' }}
											>
												{simulationFlowDisplay}
											</span>
											<span
												className="pb-[4px] text-[16px] leading-none text-[#c3eaff] [text-shadow:0_0_5px_rgba(101,183,255)]"
												style={{ fontFamily: 'KHNPHUotfR' }}
											>
												m³/h
											</span>
										</div>
									</div>
								</CommonCard>

								<div className="grid min-h-0 min-w-0 grid-rows-[minmax(0,0.88fr)_minmax(0,1.12fr)] gap-2">
									<CommonCard className="flex min-h-0 min-w-0 flex-col p-2.5">
										<div className="mb-2 flex items-center justify-between gap-3">
											<SubTitleBar title="펌프조합 선택" className="mb-0 flex-1" />
											<CommonButton
												text="조합 적용 및 실행"
												size="default"
												className="h-[30px] px-4 text-[12px]"
											/>
										</div>
										<CommonCard className="min-h-0 flex-1 overflow-auto rounded-[6px] bg-[rgba(7,19,43,0.72)]">
											<table className="w-full border-collapse text-[12px] text-sky-100">
												<thead>
													<tr>
														<th className="w-10 border border-sky-300/25 bg-[#11305f] px-2 py-2" />
														<th className="w-[90px] border border-sky-300/25 bg-[#11305f] px-3 py-2 font-semibold">
															순번
														</th>
														<th className="border border-sky-300/25 bg-[#11305f] px-3 py-2 font-semibold">
															구펌프
														</th>
														<th className="border border-sky-300/25 bg-[#11305f] px-3 py-2 font-semibold">
															신펌프
														</th>
														<th className="w-[140px] border border-sky-300/25 bg-[#11305f] px-3 py-2 font-semibold">
															전력원단위
														</th>
														<th className="w-[120px] border border-sky-300/25 bg-[#11305f] px-3 py-2 font-semibold">
															총 대수
														</th>
													</tr>
												</thead>
												<tbody>
													{simulationPumpComboSeq.map(combo => (
														<tr key={combo.key} className="hover:bg-sky-500/6">
															<td className="border border-sky-300/15 px-2 py-2 text-center">
																<input
																	type="radio"
																	name="pump-combo"
																	checked={selectedPumpCombo === combo.key}
																	onChange={() => setSelectedPumpCombo(combo.key)}
																	className="h-4 w-4 accent-sky-400"
																/>
															</td>
															<td className="border border-sky-300/15 px-3 py-2 text-center">
																{combo.order}
															</td>
															<td className="border border-sky-300/15 px-3 py-2">
																<div className="flex flex-wrap justify-center gap-2">
																	{combo.oldPumpSeq.map(pumpNo => (
																		<PumpChip
																			key={`${combo.key}-old-${pumpNo}`}
																			value={pumpNo}
																		/>
																	))}
																</div>
															</td>
															<td className="border border-sky-300/15 px-3 py-2">
																<div className="flex flex-wrap justify-center gap-2">
																	{combo.newPumpSeq.map(pumpNo => (
																		<PumpChip
																			key={`${combo.key}-new-${pumpNo}`}
																			value={pumpNo}
																		/>
																	))}
																</div>
															</td>
															<td className="border border-sky-300/15 px-3 py-2 text-center">
																{combo.powerUnit}
															</td>
															<td className="border border-sky-300/15 px-3 py-2 text-right">
																{combo.totalCount}
															</td>
														</tr>
													))}
												</tbody>
											</table>
										</CommonCard>
									</CommonCard>

									<CommonCard className="flex min-h-0 min-w-0 flex-col p-2.5">
										<div className="mb-2 flex items-center justify-between gap-3">
											<SubTitleBar title="관망해석 결과" className="mb-0 flex-1" />
											<CommonButton text="CSV 다운로드" size="sm" className="h-[32px] px-4 text-[12px]" />
										</div>
										<CommonCard className="min-h-0 flex-1 overflow-auto rounded-[6px] bg-[rgba(7,19,43,0.72)]">
											<table className="w-full border-collapse text-[13px] text-sky-100">
												<thead className="sticky top-0 z-10">
													<tr>
														<th className="border border-sky-300/25 bg-[#11305f] px-3 py-2 font-semibold">
															구분
														</th>
														<th className="border border-sky-300/25 bg-[#11305f] px-3 py-2 font-semibold">
															유량(m³/h)
														</th>
														<th className="border border-sky-300/25 bg-[#11305f] px-3 py-2 font-semibold">
															압력(kgf/cm²)
														</th>
														<th className="border border-sky-300/25 bg-[#11305f] px-3 py-2 font-semibold">
															구분
														</th>
														<th className="border border-sky-300/25 bg-[#11305f] px-3 py-2 font-semibold">
															유량(m³/h)
														</th>
														<th className="border border-sky-300/25 bg-[#11305f] px-3 py-2 font-semibold">
															압력(kgf/cm²)
														</th>
													</tr>
												</thead>
												<tbody>
													{simulationResultRowSeq.map(row => (
														<tr key={row.key} className="hover:bg-sky-500/6">
															<td className="border border-sky-300/15 px-3 py-2 text-center">
																{row.division1}
															</td>
															<td className="border border-sky-300/15 px-3 py-2 text-right">
																{row.flow1}
															</td>
															<td className="border border-sky-300/15 px-3 py-2 text-right">
																{row.pressure1}
															</td>
															<td className="border border-sky-300/15 px-3 py-2 text-center">
																{row.division2}
															</td>
															<td className="border border-sky-300/15 px-3 py-2 text-right">
																{row.flow2}
															</td>
															<td className="border border-sky-300/15 px-3 py-2 text-right">
																{row.pressure2}
															</td>
														</tr>
													))}
												</tbody>
											</table>
										</CommonCard>
									</CommonCard>
								</div>
							</section>
						)}
					</div>
				)}
			</div>

			<CommonDialog
				open={isModelEditModalOpen}
				setOpen={setIsModelEditModalOpen}
				option={{
					title: '모형편집',
					widthClassName: '!max-w-[720px]',
					contentClassName:
						'!rounded-none !border-[#3b5a87] !bg-[linear-gradient(180deg,#112b58_0%,#091730_100%)] !p-0 !text-sky-50 shadow-[0_18px_48px_rgba(0,0,0,0.42)]',
					backdropClassName: 'bg-slate-950/50',
					headerClassName: 'mb-0 border-b border-[#385589] px-4 pb-3 pt-3',
					bodyClassName: 'px-4 py-4',
					footerClassName: 'mt-0 border-t border-[#385589] px-4 py-3',
					titleClassName: 'text-[20px] font-bold text-white drop-shadow-[0_0_6px_rgba(116,196,255,0.28)]',
					closeClassName:
						'!h-[22px] !w-[22px] !rounded-none !bg-transparent !p-0 !text-[15px] !text-sky-100 hover:!bg-transparent hover:!text-white',
				}}
				buttons={[
					{
						key: 'close-model-edit',
						label: '닫기',
						closeOnClick: true,
						className: 'h-[30px] min-w-[56px] px-3 text-[12px]',
					},
				]}
			>
				<CommonCard className="rounded-[4px] bg-[rgba(8,18,36,0.9)] px-4 py-8 text-center text-[15px] text-sky-100/82">
					모형편집 화면은 이 위치에 연결됩니다.
				</CommonCard>
			</CommonDialog>

			<CommonDialog
				open={isDemandModalOpen}
				setOpen={setIsDemandModalOpen}
				option={{
					title: '배수지 수요량 설정',
					widthClassName: '!max-w-[1170px]',
					contentClassName:
						'!rounded-none !border-[#4c6ca6] !bg-[linear-gradient(180deg,#112b58_0%,#091730_100%)] !p-0 !text-sky-50 shadow-[0_18px_48px_rgba(0,0,0,0.42)]',
					backdropClassName: 'bg-slate-950/40',
					viewportClassName: 'items-start pt-[2px]',
					headerClassName: 'mb-[10px] border-b border-[#385589] px-[8px] pb-[7px] pt-[4px]',
					bodyClassName: 'px-[7px] pb-[8px]',
					footerClassName: 'mt-0 px-[8px] pb-[9px] pt-[8px]',
					titleClassName:
						'text-[18px] font-bold leading-none tracking-[-0.03em] text-white drop-shadow-[0_0_6px_rgba(116,196,255,0.28)]',
					closeClassName:
						'!mt-[1px] !h-[20px] !w-[20px] !rounded-none !bg-transparent !p-0 !text-[14px] !text-sky-100 hover:!bg-transparent hover:!text-white',
				}}
				buttons={[
					{
						key: 'save',
						label: '저장',
						onClick: handleDemandSave,
						closeOnClick: true,
						className: 'h-[29px] min-w-[48px] px-3 text-[12px]',
					},
					{
						key: 'cancel',
						label: '취소',
						closeOnClick: true,
						variant: 'outline',
						className: 'h-[29px] min-w-[48px] px-3 text-[12px]',
					},
				]}
			>
				<CommonCard className="overflow-hidden rounded-none bg-[rgba(10,20,42,0.82)]">
					<table className="w-full border-collapse text-[13px] text-sky-50">
						<thead>
							<tr>
								{['배수지', '수요량', '배수지', '수요량', '배수지', '수요량'].map((header, index) => (
									<th
										key={`${header}-${index}`}
										className="border border-[#45659c] bg-[#233b7b] px-3 py-[6px] text-center text-[13px] font-semibold"
									>
										{header}
									</th>
								))}
							</tr>
						</thead>
						<tbody>
							{draftReservoirDemandRowSeq.map((row, rowIndex) => (
								<tr key={`demand-row-${rowIndex}`}>
									{row.flatMap((cell, cellIndex) => [
										<td
											key={`${cell.name}-name`}
											className="border border-[#35517d] bg-[rgba(8,18,36,0.96)] px-3 py-[5px] text-center text-[13px] font-semibold text-white"
										>
											{cell.name}
										</td>,
										<td
											key={`${cell.name}-value`}
											className="border border-[#35517d] bg-[rgba(8,18,36,0.96)] px-[6px] py-[4px]"
										>
											<input
												value={cell.value}
												onChange={event =>
													handleDemandValueChange(rowIndex, cellIndex, event.target.value)
												}
												className="h-[30px] w-full rounded-[3px] border border-[#5c98d8] bg-[linear-gradient(180deg,#0e274f,#11284a)] px-[10px] text-left text-[13px] text-sky-50 outline-none shadow-[inset_0_0_0_1px_rgba(11,28,55,0.72)] focus:border-[#8bc8ff]"
											/>
										</td>,
									])}
								</tr>
							))}
						</tbody>
					</table>
				</CommonCard>
			</CommonDialog>
		</div>
	);
}

export default PipNetAnals;
