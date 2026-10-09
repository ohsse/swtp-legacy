import CommonChart from '@/web/components/common/CommonChart.jsx';
import { ChartWrapper } from 'stz-chart-maker';
import { useMemo } from 'react';

const DEFAULT_COLOR_SEQ = [
	{ borderColor: 'rgba(125, 211, 252, 0.8)', backgroundColor: 'rgba(56, 189, 248, 0.68)' },
	{ borderColor: 'rgba(251, 146, 60, 0.88)', backgroundColor: 'rgba(251, 146, 60, 0.72)' },
	{ borderColor: 'rgba(52, 211, 153, 0.82)', backgroundColor: 'rgba(52, 211, 153, 0.66)' },
	{ borderColor: 'rgba(167, 139, 250, 0.82)', backgroundColor: 'rgba(167, 139, 250, 0.66)' },
];
const DEFAULT_AXIS_PADDING = { x: 0.08, y: 0.12 };

function toFiniteNumber(value) {
	const numberValue = typeof value === 'number' ? value : Number(value);
	return Number.isFinite(numberValue) ? numberValue : undefined;
}

function normalizeScatterData({ data, xKey, yKey, groupKey, labelKey }) {
	const dataSeq = Array.isArray(data) ? data : [];
	const groupedDataMap = new Map();

	dataSeq.forEach((row, index) => {
		if (!row || typeof row !== 'object') return;

		const x = toFiniteNumber(row[xKey]);
		const y = toFiniteNumber(row[yKey]);
		if (typeof x === 'undefined' || typeof y === 'undefined') return;

		const groupValue = groupKey ? row[groupKey] : undefined;
		const groupName = groupValue || '데이터';
		const point = {
			...row,
			x,
			y,
			_label: row[labelKey] ?? row.name ?? row.id ?? `P-${index + 1}`,
		};

		if (!groupedDataMap.has(groupName)) {
			groupedDataMap.set(groupName, []);
		}

		groupedDataMap.get(groupName).push(point);
	});

	const datasetSeq = Array.from(groupedDataMap.entries()).map(([label, points], index) => {
		const color = DEFAULT_COLOR_SEQ[index % DEFAULT_COLOR_SEQ.length];
		return {
			label,
			data: points,
			borderColor: color.borderColor,
			backgroundColor: color.backgroundColor,
		};
	});

	return datasetSeq.length > 0
		? datasetSeq
		: [
				{
					label: '데이터',
					data: [],
					borderColor: DEFAULT_COLOR_SEQ[0].borderColor,
					backgroundColor: DEFAULT_COLOR_SEQ[0].backgroundColor,
				},
			];
}

function CommonScatterChart({
	data = [],
	chartId = 'common-scatter-chart',
	className,
	xKey = 'x',
	yKey = 'y',
	groupKey = 'group',
	labelKey = 'pointNm',
	title = 'Scatter Chart',
	xAxisTitle = 'X',
	yAxisTitle = 'Y',
	pointRadius = 5,
	pointHoverRadius = 8,
	showTrendLine = true,
	showCrosshair = true,
	axisPadding = DEFAULT_AXIS_PADDING,
	onPointClick,
}) {
	const chartConfig = useMemo(() => {
		const datasets = normalizeScatterData({
			data,
			xKey,
			yKey,
			groupKey,
			labelKey,
		});

		const chart = ChartWrapper.create('scatter', [], datasets, {
			maintainAspectRatio: false,
			onClick: (event, elements, context) => {
				onPointClick?.({
					event,
					elements,
					context,
					point: context.primary?.raw,
					primary: context.primary,
				});
			},
			interaction: {
				mode: 'nearest',
				intersect: false,
			},
			plugins: {
				legend: {
					position: 'top',
					labels: {
						color: '#d7efff',
						boxWidth: 10,
						usePointStyle: true,
					},
				},
				tooltip: {
					callbacks: {
						label: context => {
							const raw = context.raw ?? {};
							return `${raw._label ?? context.dataset.label}: ${xAxisTitle} ${raw.x} / ${yAxisTitle} ${raw.y}`;
						},
					},
				},
			},
			scales: {
				x: {
					title: {
						display: true,
						text: xAxisTitle,
						color: '#bfdbfe',
					},
					grid: {
						color: 'rgba(148, 163, 184, 0.14)',
					},
					ticks: {
						color: '#c7ddff',
					},
				},
				y: {
					title: {
						display: true,
						text: yAxisTitle,
						color: '#bfdbfe',
					},
					grid: {
						color: 'rgba(148, 163, 184, 0.14)',
					},
					ticks: {
						color: '#c7ddff',
					},
				},
			},
		})
			.setAllPointRadius(pointRadius)
			.setAllPointHoverRadius(pointHoverRadius)
			.setPointStyleByValue(point => ({
				pointBorderColor: point.datasetIndex === 0 ? '#d7efff' : '#fff7ed',
				pointBorderWidth: 1,
			}))
			.setAxisRangeFromData(axisPadding)
			.setTitle({
				display: Boolean(title),
				text: title,
				color: '#f8fafc',
				font: {
					size: 16,
					weight: '700',
				},
			});

		if (showTrendLine) {
			chart.addTrendLine({
				borderColor: 'rgba(52, 211, 153, 0.86)',
				borderWidth: 2,
				borderDash: [6, 4],
			});
		}

		if (showCrosshair) {
			chart.addCrosshair({
				color: 'rgba(125, 211, 252, 0.55)',
				xFormatter: value => `${Number(value).toFixed(1)}`,
				yFormatter: value => `${Number(value).toFixed(1)}`,
			});
		}

		return chart.build(chartId);
	}, [
		axisPadding,
		chartId,
		data,
		groupKey,
		labelKey,
		onPointClick,
		pointHoverRadius,
		pointRadius,
		showCrosshair,
		showTrendLine,
		title,
		xAxisTitle,
		xKey,
		yAxisTitle,
		yKey,
	]);

	return <CommonChart chartConfig={chartConfig} className={className} />;
}

export default CommonScatterChart;
