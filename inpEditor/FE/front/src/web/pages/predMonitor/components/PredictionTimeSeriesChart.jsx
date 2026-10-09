import CommonChart from '@/web/components/common/CommonChart.jsx';
import { ChartWrapper, noDataPlugin } from 'stz-chart-maker';
import { useMemo } from 'react';

const LINE_COLOR_BY_KEY = {
	actual: '#2563eb',
	M5: '#16a34a',
	M10: '#ea580c',
	M30: '#7c3aed',
	H1: '#0891b2',
	H3: '#db2777',
	H6: '#475569',
};

const FALLBACK_LINE_COLORS = ['#16a34a', '#ea580c', '#7c3aed', '#0891b2', '#db2777', '#475569'];

const NO_DATA_CONFIG = {
	text: '조회된 데이터가 없습니다.',
	color: '#111827',
};

function withNoDataConfig(chartConfig) {
	const plugins = chartConfig.plugins ?? [];
	const hasNoDataPlugin = plugins.some(plugin => plugin?.id === noDataPlugin.id);

	return {
		...chartConfig,
		options: {
			...(chartConfig.options ?? {}),
			_noDataText: NO_DATA_CONFIG.text,
			_noData: NO_DATA_CONFIG,
		},
		plugins: hasNoDataPlugin ? plugins : [noDataPlugin, ...plugins],
	};
}

function resolveTimeLabels(timeSeries = []) {
	const labels = new Set();

	timeSeries.forEach(series => {
		(series.data ?? []).forEach(point => {
			if (point?.x) labels.add(point.x);
		});
	});

	return [...labels].sort((a, b) => new Date(a).getTime() - new Date(b).getTime());
}

function buildDataset({ key, label, data, borderDash = [], pointRadius = 0 }, labels, index) {
	const color =
		LINE_COLOR_BY_KEY[key] ??
		LINE_COLOR_BY_KEY[String(key).toUpperCase()] ??
		FALLBACK_LINE_COLORS[index % FALLBACK_LINE_COLORS.length] ??
		'#d4ecff';
	const isActual = String(key).toLowerCase() === 'actual';
	const pointByX = new Map((data ?? []).map(point => [point.x, point.y]));

	return {
		label,
		data: labels.map(x => pointByX.get(x) ?? null),
		borderColor: color,
		backgroundColor: color,
		borderWidth: isActual ? 4 : 2.8,
		borderDash,
		spanGaps: true,
		pointRadius,
		pointHoverRadius: 5,
		tension: 0.28,
		fill: false,
	};
}

function toTimeMs(value) {
	if (value === undefined || value === null || value === '') return Number.NaN;
	if (value instanceof Date) return value.getTime();
	if (typeof value === 'number') return value;

	return new Date(String(value)).getTime();
}

function resolveClosestLabelByXValue(xValue, labels) {
	const xTime = toTimeMs(xValue);
	if (Number.isNaN(xTime)) return '';

	return labels.reduce((closestLabel, label) => {
		if (!closestLabel) return label;

		const currentDiff = Math.abs(toTimeMs(label) - xTime);
		const closestDiff = Math.abs(toTimeMs(closestLabel) - xTime);

		return currentDiff < closestDiff ? label : closestLabel;
	}, '');
}

function resolveClickedLabel(event, elements, chart, labels) {
	const activeElements =
		elements?.length > 0 ? elements : (chart?.getElementsAtEventForMode?.(event, 'index', { intersect: false }, true) ?? []);
	const dataIndex = activeElements[0]?.index;

	if (dataIndex === undefined || dataIndex === null) {
		return {
			activeElements,
			dataIndex: null,
			label: resolveClosestLabelByXValue(chart?.scales?.x?.getValueForPixel?.(event?.x), labels),
		};
	}

	return {
		activeElements,
		dataIndex,
		label: labels[dataIndex] ?? '',
	};
}

function PredictionTimeSeriesChart({ chartId, type, title, unit, series, yMin, yMax, onChartClick }) {
	const chartConfig = useMemo(() => {
		const timeSeries = series.timeSeries ?? [];
		const labels = resolveTimeLabels(timeSeries);
		const datasets = timeSeries.map((line, index) => buildDataset(line, labels, index));
		const yScaleRange = {
			...(Number.isFinite(yMin) ? { min: yMin } : {}),
			...(Number.isFinite(yMax) ? { max: yMax } : {}),
		};

		const nextChartConfig = ChartWrapper.create('line', labels, datasets, {
			maintainAspectRatio: false,
			animation: false,
			_noDataText: NO_DATA_CONFIG.text,
			_noData: NO_DATA_CONFIG,
			interaction: {
				mode: 'index',
				intersect: false,
			},
			plugins: {
				legend: {
					position: 'top',
					align: 'center',
					labels: {
						color: '#111827',
						boxWidth: 10,
						boxHeight: 2,
						usePointStyle: false,
						padding: 12,
						font: {
							size: 11,
							weight: '700',
						},
					},
				},
				tooltip: {
					callbacks: {
						label: context => {
							const value = context.parsed?.y;
							return `${context.dataset.label}: ${Number(value).toFixed(2)} ${unit}`;
						},
					},
				},
			},
			scales: {
				y: {
					...yScaleRange,
					title: {
						display: true,
						text: unit,
						color: '#111827',
					},
					grid: {
						color: 'rgba(148, 163, 184, 0.16)',
					},
					ticks: {
						color: '#111827',
					},
				},
			},
		})
			.setTimeScale('x', {
				unit: 'hour',
				displayFormats: {
					hour: 'HH:mm',
				},
				tooltipFormat: 'yyyy-MM-dd HH:mm',
				grid: {
					color: 'rgba(148, 163, 184, 0.18)',
				},
				ticks: {
					color: '#111827',
					maxRotation: 0,
					autoSkipPadding: 18,
				},
			})
			.setPlugin(noDataPlugin)
			.setLegend({ position: 'top' })
			.build(chartId);

		nextChartConfig.options.onClick = (event, elements, chart) => {
			const clicked = resolveClickedLabel(event, elements, chart, labels);

			onChartClick?.({
				chartId,
				type,
				title,
				event,
				elements: clicked.activeElements,
				chart,
				dataIndex: clicked.dataIndex,
				targetLabel: clicked.label,
			});
		};

		return withNoDataConfig(nextChartConfig);
	}, [chartId, onChartClick, series, title, type, unit, yMax, yMin]);

	return <CommonChart chartConfig={chartConfig} className="h-full w-full" />;
}

export default PredictionTimeSeriesChart;
