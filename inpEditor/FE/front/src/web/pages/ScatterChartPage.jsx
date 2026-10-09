import CommonCard from '@/web/components/common/CommonCard.jsx';
import CommonScatterChart from '@/web/components/common/CommonScatterChart.jsx';

const scatterData = [];

function ScatterChartPage() {
	const handlePointClick = ({ point, primary, context }) => {
		console.log('%c:::::::::::::::::::: point', 'color:#0bb; font-weight:700;', point);
		console.log('%c:::::::::::::::::::: primary', 'color:#0bb; font-weight:700;', primary);
		console.log('%c:::::::::::::::::::: context', 'color:#0bb; font-weight:700;', context);
	};

	return (
		<div className="flex h-full min-h-0 flex-col gap-4 overflow-hidden">
			<div className="flex items-center justify-between gap-3 border-b border-sky-200/16 px-1 pb-3">
				<div>
					<h1 className="text-[22px] font-bold text-white">Scatter Chart</h1>
					<p className="mt-1 text-[12px] text-sky-100/62">
						API 응답 데이터를 data prop으로 받아 렌더링하는 scatter 차트
					</p>
				</div>
			</div>

			<CommonCard className="min-h-0 flex-1 p-4">
				<div className="mb-3 grid grid-cols-3 gap-3">
					<div className="rounded-[6px] border border-sky-200/18 bg-slate-950/24 px-4 py-3">
						<div className="text-[12px] font-semibold text-sky-100/60">차트 타입</div>
						<div className="mt-1 text-[18px] font-bold text-white">scatter</div>
					</div>
					<div className="rounded-[6px] border border-sky-200/18 bg-slate-950/24 px-4 py-3">
						<div className="text-[12px] font-semibold text-sky-100/60">데이터 소스</div>
						<div className="mt-1 text-[18px] font-bold text-white">API</div>
					</div>
					<div className="rounded-[6px] border border-sky-200/18 bg-slate-950/24 px-4 py-3">
						<div className="text-[12px] font-semibold text-sky-100/60">수신 건수</div>
						<div className="mt-1 text-[18px] font-bold text-white">{scatterData.length}</div>
					</div>
				</div>
				<CommonScatterChart
					chartId="api-scatter-chart"
					data={scatterData}
					xKey="x"
					yKey="y"
					groupKey="group"
					labelKey="pointNm"
					title="API Scatter Chart"
					xAxisTitle="유량(m³/h)"
					yAxisTitle="압력(kgf/cm²)"
					onPointClick={handlePointClick}
					className="h-[calc(100%-88px)] min-h-[360px] rounded-[8px] border border-sky-200/18 bg-slate-950/24 p-3"
				/>
			</CommonCard>
		</div>
	);
}

export default ScatterChartPage;
