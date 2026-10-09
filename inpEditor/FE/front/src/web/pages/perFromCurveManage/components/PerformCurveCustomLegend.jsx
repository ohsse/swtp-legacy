const PERFORM_CURVE_LEGEND_CONTAINER_ID = 'perform-curve-legend';

const performCurveLegendClassName = [
	'flex h-7 items-center justify-center bg-white text-[12px] font-bold text-slate-950',
	'[&_.perform-curve-legend-list]:flex [&_.perform-curve-legend-list]:items-center [&_.perform-curve-legend-list]:gap-4',
	'[&_.perform-curve-legend-item]:flex [&_.perform-curve-legend-item]:cursor-pointer [&_.perform-curve-legend-item]:items-center [&_.perform-curve-legend-item]:gap-1.5',
	'[&_.perform-curve-legend-item]:select-none [&_.perform-curve-legend-item]:transition-opacity',
	'[&_.perform-curve-legend-item:hover]:opacity-80',
	'[&_.perform-curve-legend-text]:whitespace-nowrap [&_.perform-curve-legend-text]:!text-black',
	'[&_.perform-curve-legend-box]:shrink-0',
].join(' ');

const performCurveCustomLegendConfig = {
	containerID: PERFORM_CURVE_LEGEND_CONTAINER_ID,
	className: {
		list: 'perform-curve-legend-list',
		item: 'perform-curve-legend-item',
		box: 'perform-curve-legend-box',
		text: 'perform-curve-legend-text',
	},
	};
const performCurveLegendShapePlugin = {
	id: 'performCurveLegendShape',
	afterUpdate(chart) {
		const container = document.getElementById(PERFORM_CURVE_LEGEND_CONTAINER_ID);
		const itemSeq = container?.querySelectorAll?.('.perform-curve-legend-item') ?? [];
		const legendItemSeq = chart.options.plugins.legend.labels.generateLabels(chart);

		itemSeq.forEach((itemElement, index) => {
			const legendItem = legendItemSeq[index];
			const boxElement = itemElement.querySelector('.perform-curve-legend-box');
			const dataset = chart.data.datasets?.[legendItem?.datasetIndex] ?? {};
			if (!boxElement) return;

			const color = dataset.borderColor ?? legendItem?.strokeStyle ?? legendItem?.fillStyle ?? '#2563eb';
			boxElement.style.backgroundColor = 'transparent';
			boxElement.style.borderColor = color;
			boxElement.style.borderStyle = 'solid';
			boxElement.style.borderWidth = '0';

			if (dataset.showLine) {
				boxElement.style.width = '28px';
				boxElement.style.height = '0';
				boxElement.style.borderTopWidth = `${dataset.borderWidth ?? 2}px`;
				boxElement.style.borderTopStyle = Array.isArray(dataset.borderDash) && dataset.borderDash.length > 0 ? 'dashed' : 'solid';
				boxElement.style.borderRadius = '0';
				return;
			}

			boxElement.style.width = '10px';
			boxElement.style.height = '10px';
			boxElement.style.borderWidth = '1px';
			boxElement.style.borderRadius = '9999px';
			boxElement.style.backgroundColor = dataset.backgroundColor ?? legendItem?.fillStyle ?? color;
		});
	},
};

function PerformCurveCustomLegend() {
	return <div id={PERFORM_CURVE_LEGEND_CONTAINER_ID} className={performCurveLegendClassName} />;
}

export { performCurveCustomLegendConfig, performCurveLegendShapePlugin };
export default PerformCurveCustomLegend;
