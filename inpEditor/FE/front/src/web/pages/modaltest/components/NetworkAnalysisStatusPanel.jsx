import { useMemo } from 'react';
import CommonCard from '@/web/components/common/CommonCard.jsx';
import CommonChart from '@/web/components/common/CommonChart.jsx';
import CommonTable from '@/web/components/common/CommonTable.jsx';
import { LAYER_TABLE_BASE_COL_CLASS_NAME } from '@/consts/index.js';

const defaultSummarySeq = [
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

const defaultDetailRowSeq = [
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
];

const tableClassName = {
	headClassName: `${LAYER_TABLE_BASE_COL_CLASS_NAME.headClassName} px-3 text-[12px] font-semibold`,
	cellClassName: `${LAYER_TABLE_BASE_COL_CLASS_NAME.cellClassName} px-3 text-[12px]`,
};

const defaultDetailColSeq = [
	{
		key: 'name',
		colNm: '구분',
		widthClassName: 'w-[16%]',
		minWidth: 190,
		cellClassName: `${tableClassName.cellClassName} text-left`,
	},
	{
		key: 'flowStatus',
		colNm: '유량 상태',
		widthClassName: 'w-[10%]',
		minWidth: 120,
		cellClassName: `${tableClassName.cellClassName} text-center`,
	},
	{
		key: 'flowMeasure',
		colNm: '유량 계측값',
		widthClassName: 'w-[11%]',
		minWidth: 128,
		cellClassName: `${tableClassName.cellClassName} text-right`,
	},
	{
		key: 'flowAnalyze',
		colNm: '유량 분석값',
		widthClassName: 'w-[11%]',
		minWidth: 128,
		cellClassName: `${tableClassName.cellClassName} text-right`,
	},
	{
		key: 'flowErr',
		colNm: '유량 오차율',
		widthClassName: 'w-[10%]',
		minWidth: 116,
		cellClassName: `${tableClassName.cellClassName} text-right`,
	},
	{
		key: 'pressureStatus',
		colNm: '압력 상태',
		widthClassName: 'w-[10%]',
		minWidth: 120,
		cellClassName: `${tableClassName.cellClassName} text-center`,
	},
	{
		key: 'pressureMeasure',
		colNm: '압력 계측값',
		widthClassName: 'w-[11%]',
		minWidth: 128,
		cellClassName: `${tableClassName.cellClassName} text-right`,
	},
	{
		key: 'pressureAnalyze',
		colNm: '압력 분석값',
		widthClassName: 'w-[11%]',
		minWidth: 128,
		cellClassName: `${tableClassName.cellClassName} text-right`,
	},
	{
		key: 'pressureErr',
		colNm: '압력 오차율',
		widthClassName: 'w-[10%]',
		minWidth: 116,
		cellClassName: `${tableClassName.cellClassName} text-right`,
	},
].map(column => ({
	...column,
	headClassName: column.headClassName ?? tableClassName.headClassName,
}));

const chartLabels = ['02:30', '03:40', '05:00', '06:15', '07:30', '09:10', '11:15', '13:20', '14:50'];

function buildLineChartConfig({ labels, unit, min, max, measuredData, analyzedData, measuredColor, analyzedColor }) {
	return {
		type: 'line',
		data: {
			labels,
			datasets: [
				{
					label: '격점',
					data: measuredData,
					borderColor: measuredColor,
					backgroundColor: `${measuredColor}24`,
					fill: false,
					tension: 0.3,
					pointRadius: 0,
					borderWidth: 2,
				},
				{
					label: '분석값',
					data: analyzedData,
					borderColor: analyzedColor,
					backgroundColor: `${analyzedColor}24`,
					fill: false,
					tension: 0.3,
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
					labels: {
						color: '#d5eeff',
						boxWidth: 9,
						usePointStyle: true,
						pointStyle: 'circle',
						padding: 10,
					},
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
					min,
					max,
					grid: { color: 'rgba(145, 210, 255, 0.08)' },
					ticks: { color: '#a8cfff', font: { size: 10 } },
					title: {
						display: true,
						text: unit,
						color: '#a8cfff',
						font: { size: 10, weight: '600' },
					},
				},
			},
		},
	};
}

function SectionTitle({ children }) {
	return (
		<div className="mb-3 flex h-9 items-center bg-[linear-gradient(90deg,rgba(45,105,161,0.18),rgba(69,139,199,0.72)_22%,rgba(28,65,108,0.64)_58%,rgba(10,25,54,0.08))] px-6 text-[19px] font-semibold text-white shadow-[inset_0_-1px_0_rgba(126,200,255,0.22)]">
			{children}
		</div>
	);
}

function SummaryGroup({ group }) {
	return (
		<div className="min-w-0">
			<div className="mb-2 flex items-center justify-between">
				<span className="text-[13px] font-semibold text-sky-100">{group.title}</span>
				<span className="text-[11px] text-sky-200/65">오늘</span>
			</div>
			<div className="grid grid-cols-3 gap-2">
				{group.itemSeq.map(item => (
					<CommonCard
						key={`${group.key}-${item.label}`}
						className="rounded-[6px] bg-[linear-gradient(180deg,rgba(14,35,76,0.96),rgba(9,25,55,0.92))] px-4 py-2"
					>
						<div className="text-[11px] text-sky-100/78">{item.label}</div>
						<div className="mt-1 flex items-end justify-between gap-2">
							<span className="text-[24px] leading-none text-white">{item.value}</span>
							<span className="pb-0.5 text-[11px] text-sky-300/78">({item.rate})</span>
						</div>
					</CommonCard>
				))}
			</div>
		</div>
	);
}

function NetworkAnalysisStatusPanel({
	summarySeq = defaultSummarySeq,
	detailRowSeq = defaultDetailRowSeq,
	detailColSeq = defaultDetailColSeq,
	detailHeadRowSeq,
	flowChartConfig,
	pressureChartConfig,
	className = '',
}) {
	const resolvedFlowChartConfig = useMemo(
		() =>
			flowChartConfig ??
			buildLineChartConfig({
				labels: chartLabels,
				unit: '㎥/h',
				min: 0,
				max: 24000,
				measuredData: [18800, 19620, 20100, 19810, 21200, 20420, 19320, 18670, 18210],
				analyzedData: [14900, 13680, 12130, 13110, 15220, 17480, 18310, 18920, 19740],
				measuredColor: '#95df67',
				analyzedColor: '#5b84ff',
			}),
		[flowChartConfig]
	);
	const resolvedPressureChartConfig = useMemo(
		() =>
			pressureChartConfig ??
			buildLineChartConfig({
				labels: chartLabels,
				unit: 'kgf/㎠',
				min: 0,
				max: 10,
				measuredData: [6.8, 7.1, 7.2, 7.25, 7.28, 7.26, 7.24, 7.21, 7.25],
				analyzedData: [7.05, 7.18, 7.21, 7.42, 7.48, 7.46, 7.44, 7.45, 7.49],
				measuredColor: '#7aa5ff',
				analyzedColor: '#9be271',
			}),
		[pressureChartConfig]
	);

	return (
		<div className={['grid h-full min-h-0 grid-rows-[auto_minmax(0,1fr)] gap-2 text-sky-50', className].join(' ')}>
			<CommonCard className="p-3">
				<SectionTitle>관망해석 현황</SectionTitle>
				<div className="grid grid-cols-2 gap-4">
					{summarySeq.map(group => (
						<SummaryGroup key={group.key} group={group} />
					))}
				</div>
			</CommonCard>

			<div className="grid min-h-0 grid-rows-[minmax(0,1.35fr)_minmax(160px,0.65fr)] gap-2">
				<CommonCard className="flex min-h-0 flex-col overflow-hidden p-3">
					<SectionTitle>해석 상세현황</SectionTitle>
					<CommonCard className="min-h-0 flex-1 overflow-hidden rounded-[6px] bg-[rgba(7,19,43,0.78)]">
						<CommonTable
							colSeq={detailColSeq}
							headRowSeq={detailHeadRowSeq}
							rowSeq={detailRowSeq}
							getRowKey={row => row.key}
							rowClassName="hover:bg-sky-500/6"
							headRowClassName="!border-slate-700/70"
							ariaLabel="해석 상세현황"
							enableFiltering
							enableSorting
							enableColumnResize
							rowHeight={36}
							columnHeaderHeight={36}
						/>
					</CommonCard>
				</CommonCard>

				<div className="grid min-h-0 grid-cols-2 gap-2">
					<CommonCard className="min-h-0 p-3">
						<CommonChart chartConfig={resolvedFlowChartConfig} variant="plain" className="h-full" />
					</CommonCard>
					<CommonCard className="min-h-0 p-3">
						<CommonChart chartConfig={resolvedPressureChartConfig} variant="plain" className="h-full" />
					</CommonCard>
				</div>
			</div>
		</div>
	);
}

export default NetworkAnalysisStatusPanel;
