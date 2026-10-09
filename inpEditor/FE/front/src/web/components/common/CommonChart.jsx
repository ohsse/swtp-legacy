import 'chartjs-adapter-date-fns';
import { Chart as ChartJS, registerables } from 'chart.js';
import { Chart } from 'react-chartjs-2';
import zoomPlugin from 'chartjs-plugin-zoom';
import { forwardRef } from 'react';
import { loadingPlugin, noDataPlugin } from 'stz-chart-maker';
ChartJS.register(...registerables, zoomPlugin);

function mergeRuntimePluginSeq(chartConfig, isLoading, noData) {
	const runtimePluginSeq = [...(chartConfig.plugins ?? [])];
	const hasPlugin = pluginId => runtimePluginSeq.some(plugin => plugin?.id === pluginId);

	if (isLoading && !hasPlugin(loadingPlugin.id)) {
		runtimePluginSeq.push(loadingPlugin);
	}

	if (typeof noData?.text === 'string' && !hasPlugin(noDataPlugin.id)) {
		runtimePluginSeq.push(noDataPlugin);
	}

	return runtimePluginSeq;
}

const chartVariantClassNameMap = {
	plain: '',
	panel: 'rounded-[8px] border border-sky-200/20 bg-slate-950/45 p-3',
};

function cn(...classNames) {
	return classNames.filter(Boolean).join(' ');
}

function CommonChart({ chartConfig, className, style, variant = 'plain', isLoading, noData, onClick }, ref) {
	const mergedChartConfig =
		isLoading === undefined && noData === undefined
			? chartConfig
			: {
					...chartConfig,
					plugins: mergeRuntimePluginSeq(chartConfig, isLoading, noData),
					options: {
						...(chartConfig.options ?? {}),
						...(isLoading === undefined ? {} : { _loading: isLoading }),
						...(noData === undefined ? {} : { _noData: noData, _noDataText: noData?.text }),
					},
				};

	return (
		<div className={cn('relative min-h-0', chartVariantClassNameMap[variant], className)} style={style} onClick={onClick}>
			<Chart ref={ref} {...mergedChartConfig} />
		</div>
	);
}

export default forwardRef(CommonChart);
