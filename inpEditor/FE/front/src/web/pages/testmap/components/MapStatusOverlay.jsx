import Collapse from '@mui/material/Collapse';
import IconButton from '@mui/material/IconButton';
import { useState } from 'react';
import CommonCard from '@/web/components/common/CommonCard.jsx';
import CommonTable from '@/web/components/common/CommonTable.jsx';
import StatusBadge from '@/web/components/common/StatusBadge.jsx';

const overlayAnalysisTableSx = {
	fontSize: '11px',
	'& .MuiDataGrid-columnHeaders': {
		borderBottom: '1px solid rgba(186, 230, 253, 0.22)',
		backgroundColor: 'transparent',
	},
	'& .MuiDataGrid-columnHeader': {
		borderRight: 0,
		backgroundColor: 'transparent',
		padding: '0 4px',
	},
	'& .MuiDataGrid-columnHeaderTitle': {
		fontSize: '10px',
		fontWeight: 800,
		lineHeight: 1,
		color: 'rgba(224, 242, 254, 0.72)',
	},
	'& .MuiDataGrid-cell': {
		borderTop: 0,
		borderRight: 0,
		padding: '0 4px',
		color: '#e0f2fe',
	},
	'& .MuiDataGrid-row': {
		backgroundColor: 'transparent',
	},
	'& .MuiDataGrid-row:hover': {
		backgroundColor: 'transparent',
	},
	'& .MuiDataGrid-iconButtonContainer, & .MuiDataGrid-menuIcon, & .MuiDataGrid-columnSeparator': {
		display: 'none',
	},
	'& .MuiDataGrid-filler, & .MuiDataGrid-scrollbarFiller, & .MuiDataGrid-filler--borderBottom': {
		display: 'none',
	},
	'& .MuiDataGrid-overlayWrapper': {
		minHeight: 0,
	},
	'& .MuiDataGrid-virtualScroller': {
		overflow: 'hidden',
	},
};

function MetricValue({ value, unit, className = '' }) {
	return (
		<span
			className={['inline-flex min-w-0 items-baseline justify-end gap-1 whitespace-nowrap', className]
				.filter(Boolean)
				.join(' ')}
		>
			<strong className="tabular-nums">{value}</strong>
			{unit ? <span className="shrink-0 text-[8px] font-semibold text-slate-200/55">{unit}</span> : null}
		</span>
	);
}

function MapOverlayMetric({ label, observed, unit }) {
	return (
		<div className="grid h-[23px] grid-cols-[34px_1fr_8px] items-center gap-2 text-[12px] leading-none text-slate-100">
			<span className="min-w-0 font-semibold text-slate-100/90">{label}</span>
			<MetricValue
				value={observed}
				unit={unit}
				className="text-right text-[14px] font-extrabold text-white underline decoration-slate-100/80 decoration-1 underline-offset-2 [&>span]:text-[9px] [&>span]:text-slate-200/78"
			/>
			<span className="h-2 w-2 shrink-0 rounded-full bg-[#18c765] shadow-[0_0_0_2px_rgba(24,199,101,0.18)]" />
		</div>
	);
}

const defaultOverlayAnalysisColSeq = [
	{
		key: 'label',
		colNm: '항목',
		widthClassName: 'w-[44px]',
		disableColumnMenu: true,
		render: row => <span className="w-full font-bold text-sky-100/84">{row.label}</span>,
	},
	{
		key: 'observed',
		colNm: '계측값',
		widthClassName: 'w-[74px]',
		disableColumnMenu: true,
		render: row => (
			<MetricValue value={row.observed} unit={row.unit} className="w-full text-right font-semibold text-white" />
		),
	},
	{
		key: 'predicted',
		colNm: '예측값',
		widthClassName: 'w-[74px]',
		disableColumnMenu: true,
		render: row => (
			<MetricValue value={row.predicted} unit={row.unit} className="w-full text-right font-semibold text-sky-50/88" />
		),
	},
	{
		key: 'errorRate',
		colNm: '오차율',
		widthClassName: 'w-[46px]',
		disableColumnMenu: true,
		render: row => <span className="w-full text-right font-extrabold tabular-nums text-emerald-300">{row.errorRate}%</span>,
	},
];

function MapStatusOverlay({
	overlayRef,
	title = '관측점',
	collapsedTitle,
	status = 'NORMAL',
	metrics = [],
	extend = true,
	detailTitle = '유량/압력 분석',
	detailSubTitle = '실시간',
	colSeq = defaultOverlayAnalysisColSeq,
	tableSx = overlayAnalysisTableSx,
	className = '',
}) {
	const [isExpanded, setIsExpanded] = useState(false);
	const canExpand = Boolean(extend);
	const resolvedExpanded = canExpand && isExpanded;
	const resolvedTitle = resolvedExpanded ? title : (collapsedTitle ?? title);

	return (
		<div ref={overlayRef} className={['pointer-events-auto', className].filter(Boolean).join(' ')}>
			<CommonCard
				className={[
					'overflow-hidden rounded-[6px] bg-[linear-gradient(180deg,rgba(15,34,68,0.97),rgba(8,21,45,0.99))] p-0 shadow-[0_8px_18px_rgba(0,0,0,0.28)] backdrop-blur-sm',
					'transition-[width] duration-200 ease-out',
					resolvedExpanded ? 'w-[308px]' : 'w-[146px]',
				]
					.filter(Boolean)
					.join(' ')}
			>
				<div className="flex h-8 items-center gap-2 border-b border-sky-200/16 px-2.5">
					<strong className="min-w-0 flex-1 truncate text-[14px] font-extrabold text-white">{resolvedTitle}</strong>
					<StatusBadge
						status={status}
						size="sm"
						sx={{
							height: 19,
							minWidth: 56,
							fontSize: 10,
						}}
					/>
					{canExpand ? (
						<IconButton
							size="small"
							aria-label={resolvedExpanded ? '오버레이 접기' : '오버레이 펼치기'}
							onClick={() => setIsExpanded(prev => !prev)}
							sx={{
								width: 20,
								height: 20,
								p: 0,
								color: '#d7efff',
								border: '1px solid rgba(215,239,255,0.28)',
								backgroundColor: 'rgba(4, 15, 35, 0.36)',
								transform: resolvedExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
								transition: 'transform 180ms ease, background-color 180ms ease, border-color 180ms ease',
								'&:hover': {
									backgroundColor: 'rgba(42, 102, 172, 0.46)',
									borderColor: 'rgba(215,239,255,0.48)',
								},
							}}
						>
							<span className="text-[13px] leading-none">⌄</span>
						</IconButton>
					) : null}
				</div>
				<div className="px-2.5 py-1">
					{metrics.map(metric => (
						<MapOverlayMetric key={metric.key ?? metric.label} {...metric} />
					))}
				</div>
				{canExpand ? (
					<Collapse in={resolvedExpanded} timeout={180} unmountOnExit>
						<div className="border-t border-sky-200/14 px-2.5 py-2">
							<div className="mb-1.5 flex items-center justify-between gap-2">
								<span className="text-[11px] font-bold text-sky-100/86">{detailTitle}</span>
								<span className="text-[10px] font-semibold text-sky-100/52">{detailSubTitle}</span>
							</div>
							<div className="h-[78px] rounded-[6px] bg-slate-950/18">
								<CommonTable
									colSeq={colSeq}
									rowSeq={metrics}
									getRowKey={row => row.key ?? row.label}
									rowHeight={24}
									columnHeaderHeight={24}
									emptyMsg=""
									sx={tableSx}
								/>
							</div>
						</div>
					</Collapse>
				) : null}
			</CommonCard>
		</div>
	);
}

export { defaultOverlayAnalysisColSeq, overlayAnalysisTableSx };
export default MapStatusOverlay;
