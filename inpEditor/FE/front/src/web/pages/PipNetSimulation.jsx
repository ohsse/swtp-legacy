import { useMemo, useState } from 'react';
import dayjs from 'dayjs';
import { CommonButton } from '@/web/components/common/CommonButton';
import CommonCard from '@/web/components/common/CommonCard';
import CommonTable from '@/web/components/common/CommonTable';
import CommonDateTimeRangePicker from '@/web/components/common/CommonDateTimeRangePicker.jsx';
import CommonDialog from '@/web/components/CommonDialog';
import SubTitleBar from '@/web/components/SubTitleBar';
import { simulApi } from '@/web/js/apis/simulApi.js';

const DATE_TIME_INPUT_FORMAT = 'YYYY-MM-DDTHH:mm';
const API_DATE_TIME_FORMAT = 'YYYY-MM-DD HH:mm';
const EMPTY_RESERVOIR_DEMAND_ROW_SEQ = [];

const EMPTY_SIMULATION_PUMP_COMBO_SEQ = [];
const EMPTY_SIMULATION_RESULT_ROW_SEQ = [];

const simulationResultColSeq = [
	{
		key: 'branch',
		colNm: '분기점',
		flex: 1.8,
		minWidth: 130,
		cellClassName: 'flex items-center justify-center',
	},
	{
		key: 'measuredFlow',
		colNm: '실측유량',
		flex: 1.3,
		minWidth: 105,
		cellClassName: 'flex items-center justify-end',
	},
	{
		key: 'analysisFlow',
		colNm: '해석유량',
		flex: 1.3,
		minWidth: 105,
		cellClassName: 'flex items-center justify-end',
	},
	{
		key: 'flowErrorRate',
		colNm: '유량오차율',
		flex: 1.4,
		minWidth: 115,
		cellClassName: 'flex items-center justify-end',
	},
	{
		key: 'measuredPressure',
		colNm: '실측압력',
		flex: 1.3,
		minWidth: 105,
		cellClassName: 'flex items-center justify-end',
	},
	{
		key: 'analysisPressure',
		colNm: '해석압력',
		flex: 1.3,
		minWidth: 105,
		cellClassName: 'flex items-center justify-end',
	},
	{
		key: 'pressureErrorRate',
		colNm: '압력오차율',
		flex: 1.6,
		minWidth: 120,
		cellClassName: 'flex items-center justify-end',
	},
];

function formatNumber(value) {
	if (value === undefined || value === null || value === '') {
		return '';
	}

	const numericValue = Number(String(value).replace(/,/g, ''));
	if (Number.isNaN(numericValue)) {
		return String(value);
	}

	return numericValue.toLocaleString('ko-KR');
}

function formatAnalysisDateTime(value) {
	const date = dayjs(value);
	return date.isValid() ? date.format(API_DATE_TIME_FORMAT) : String(value ?? '').replace('T', ' ');
}

function resolveSimulationData(payload) {
	return payload?.data ?? payload ?? {};
}

function resolveSimulationDataSeq(payload) {
	const data = payload?.data ?? payload ?? [];
	if (Array.isArray(data)) return data;
	if (Array.isArray(data?.data)) return data.data;
	if (Array.isArray(data?.result)) return data.result;
	if (Array.isArray(data?.list)) return data.list;
	return [];
}

function normalizePumpNoSeq(pumpComb) {
	if (Array.isArray(pumpComb)) return pumpComb.map(String).filter(Boolean);
	if (pumpComb === undefined || pumpComb === null) return [];

	return String(pumpComb)
		.split(',')
		.map(value => value.trim())
		.filter(Boolean);
}

function normalizePumpComboSeq(data) {
	const pumpNoSeq = normalizePumpNoSeq(data?.pumpComb ?? data?.pumpcomb ?? data?.pumpCombination);
	if (pumpNoSeq.length === 0) return EMPTY_SIMULATION_PUMP_COMBO_SEQ;

	return [
		{
			key: 'combo-1',
			order: 1,
			oldPumpSeq: pumpNoSeq,
			newPumpSeq: [],
			powerUnit: '',
			totalCount: `${pumpNoSeq.length}대`,
			pumpComb: pumpNoSeq.join(','),
		},
	];
}

function normalizeSimulationResultRows(resultSeq) {
	if (!Array.isArray(resultSeq) || resultSeq.length === 0) {
		return EMPTY_SIMULATION_RESULT_ROW_SEQ;
	}

	return resultSeq.map((item, index) => ({
		key: `analysis-${index}`,
		branch: String(item?.Name ?? item?.name ?? ''),
		measuredFlow: String(item?.actualFlow ?? item?.ActualFlow ?? ''),
		analysisFlow: String(item?.analFlow ?? item?.AnalFlow ?? ''),
		flowErrorRate: String(item?.flowErrorRate ?? item?.flowErrorEate ?? item?.FlowErrorRate ?? ''),
		measuredPressure: String(item?.actualPress ?? item?.ActualPress ?? ''),
		analysisPressure: String(item?.analPress ?? item?.AnalPress ?? ''),
		pressureErrorRate: String(item?.pressErrorRate ?? item?.pressureErrorRate ?? item?.PressErrorRate ?? ''),
	}));
}

function normalizeDemandRows(demands) {
	if (!Array.isArray(demands) || demands.length === 0) {
		return EMPTY_RESERVOIR_DEMAND_ROW_SEQ;
	}

	const cells = demands.map((item, index) => ({
		name: String(item?.Name ?? item?.name ?? item?.resName ?? ''),
		value: String(item?.Demand ?? item?.demand ?? item?.value ?? ''),
		key: `demand-${index}`,
	}));
	const rows = [];

	for (let index = 0; index < cells.length; index += 3) {
		rows.push(cells.slice(index, index + 3));
	}

	return rows;
}

function PumpChip({ value }) {
	return (
		<span className="inline-flex h-7 min-w-7 items-center justify-center rounded-full border border-sky-300/25 bg-[linear-gradient(180deg,#2d6fd1,#1a4f9e)] px-2 text-[12px] font-semibold text-white shadow-[0_0_16px_rgba(20,132,255,0.2)]">
			{value}
		</span>
	);
}

function PipNetSimulation() {
	const initialDateRange = useMemo(() => {
		const now = dayjs().format(DATE_TIME_INPUT_FORMAT);
		return {
			analysisDttm: now,
		};
	}, []);
	const [analysisDttm, setAnalysisDttm] = useState(initialDateRange.analysisDttm);
	const [simulationFlowInput, setSimulationFlowInput] = useState('');
	const [simulationPumpComboSeq, setSimulationPumpComboSeq] = useState(EMPTY_SIMULATION_PUMP_COMBO_SEQ);
	const [simulationResultRowSeq, setSimulationResultRowSeq] = useState(EMPTY_SIMULATION_RESULT_ROW_SEQ);
	const [selectedPumpCombo, setSelectedPumpCombo] = useState('');
	const [isDemandModalOpen, setIsDemandModalOpen] = useState(false);
	const [isModelEditModalOpen, setIsModelEditModalOpen] = useState(false);
	const [draftReservoirDemandRowSeq, setDraftReservoirDemandRowSeq] = useState(EMPTY_RESERVOIR_DEMAND_ROW_SEQ);
	const simulationFlowDisplay = formatNumber(simulationFlowInput);
	const simulationPumpComboColSeq = useMemo(
		() => [
			{
				key: 'order',
				colNm: '순번',
				flex: 2,
				minWidth: 80,
				cellClassName: 'flex items-center justify-center',
			},
			{
				key: 'oldPumpSeq',
				colNm: '펌프조합',
				flex: 8,
				minWidth: 160,
				cellClassName: 'flex items-center justify-center',
				render: row => (
					<div className="flex flex-wrap justify-center gap-2">
						{row.oldPumpSeq.map(pumpNo => (
							<PumpChip key={`${row.key}-old-${pumpNo}`} value={pumpNo} />
						))}
					</div>
				),
			},
		],
		[]
	);

	const openDemandModal = () => {
		setIsDemandModalOpen(true);
	};

	const handleAnalysisDateApply = async () => {
		try {
			const payload = await simulApi.searchDate(formatAnalysisDateTime(analysisDttm));
			const data = resolveSimulationData(payload);
			const nextPumpComboSeq = normalizePumpComboSeq(data);

			setSimulationFlowInput(String(data?.outFlow ?? data?.outflow ?? ''));
			setSimulationPumpComboSeq(nextPumpComboSeq);
			setSelectedPumpCombo(nextPumpComboSeq[0]?.key ?? '');
			setSimulationResultRowSeq(EMPTY_SIMULATION_RESULT_ROW_SEQ);
			setDraftReservoirDemandRowSeq(normalizeDemandRows(data?.Demands ?? data?.demands ?? data?.demandSeq));
		} catch (error) {
			console.error(error);
		}
	};

	const handleAnalysisRun = async () => {
		try {
			const selectedCombo = simulationPumpComboSeq.find(combo => combo.key === selectedPumpCombo);
			const payload = await simulApi.anals({
				analDateTime: formatAnalysisDateTime(analysisDttm),
				pumpComb: selectedCombo?.pumpComb,
			});

			setSimulationResultRowSeq(normalizeSimulationResultRows(resolveSimulationDataSeq(payload)));
		} catch (error) {
			console.error(error);
		}
	};

	return (
		<div className="h-full min-h-0 overflow-hidden bg-[radial-gradient(circle_at_top,rgba(34,87,183,0.34),rgba(8,22,52,0.16)_36%,rgba(4,10,25,0.96)_82%)] px-1 pb-1 text-sky-50">
			<div className="flex h-full min-h-0 flex-col gap-2">
				<div className="min-h-0 flex-1">
					<section className="grid h-full min-h-0 min-w-0 grid-rows-[auto_minmax(0,1fr)] gap-2">
						<CommonCard className="min-w-0 p-2.5">
							<div className="relative mb-2 min-h-[42px]">
								<SubTitleBar title="관망해석 설정" className="absolute inset-0 mb-0 w-full pr-[520px]" />
								<div className="relative z-10 flex h-[42px] items-center justify-end">
									<CommonDateTimeRangePicker
										datePickerType="single"
										label="해석일시"
										singleLabel="해석일시"
										value={analysisDttm}
										onChange={setAnalysisDttm}
										actionLabel="적용"
										onActionClick={handleAnalysisDateApply}
										className="justify-end"
									/>
								</div>
							</div>
							<CommonCard className="mt-2.5 flex items-stretch overflow-hidden rounded-[4px] bg-[rgba(8,22,52,0.88)]">
								<input
									value={simulationFlowInput}
									readOnly
									aria-label="정수장 토출 유량"
									className="h-[42px] min-w-0 flex-1 cursor-default bg-transparent px-4 text-[24px] font-semibold text-sky-50 outline-none"
								/>
							</CommonCard>
							<div className="mt-2 flex items-end justify-end gap-[16px] whitespace-nowrap text-right">
								<div className="flex items-end gap-[14px]">
									<span
										className="pt-1 text-[24px] leading-none text-[#c3eaff] [text-shadow:0_0_5px_rgba(101,183,255)]"
										style={{ fontFamily: 'KHNPHUotfR' }}
									>
										정수장 토출 유량
									</span>
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
								<CommonButton
									text="배수지 수요량 설정"
									size="sm"
									className="mb-[2px] h-[30px] px-3 text-[11px]"
									onClick={openDemandModal}
								/>
							</div>
						</CommonCard>

						<div className="grid h-full min-h-0 min-w-0 grid-rows-[minmax(0,0.9fr)_minmax(0,1.1fr)] gap-2">
							<CommonCard className="flex min-h-[clamp(14rem,32vh,26rem)] min-w-0 flex-col p-2.5">
								<div className="relative mb-2 min-h-[42px]">
									<SubTitleBar title="펌프조합 선택" className="absolute inset-0 mb-0 w-full pr-[140px]" />
									<div className="relative z-10 flex h-[42px] items-center justify-end">
										<CommonButton
											text="해석 실행"
											size="default"
											className="h-[30px] min-w-[104px] px-4 text-[12px]"
											onClick={handleAnalysisRun}
										/>
									</div>
								</div>
								<CommonCard className="min-h-0 flex-1 overflow-hidden rounded-[6px] bg-[rgba(7,19,43,0.72)]">
									<CommonTable
										colSeq={simulationPumpComboColSeq}
										rowSeq={simulationPumpComboSeq}
										getRowKey={row => row.key}
										selectedRowKey={selectedPumpCombo}
										onRowClick={row => setSelectedPumpCombo(row.key)}
										rowHeight={48}
										columnHeaderHeight={36}
										emptyMsg="펌프조합이 없습니다."
										ariaLabel="펌프조합 선택"
										sx={{
											'& .MuiDataGrid-columnHeader': {
												backgroundColor: '#11305f',
											},
										}}
									/>
								</CommonCard>
							</CommonCard>

							<CommonCard className="flex min-h-0 min-w-0 flex-col p-2.5">
								<div className="mb-2 flex items-center justify-between gap-3">
									<SubTitleBar title="관망해석 결과" className="mb-0 flex-1" />
									<CommonButton text="CSV 다운로드" size="sm" className="h-[32px] px-4 text-[12px]" />
								</div>
								<CommonCard className="min-h-0 flex-1 overflow-hidden rounded-[6px] bg-[rgba(7,19,43,0.72)]">
									<CommonTable
										colSeq={simulationResultColSeq}
										rowSeq={simulationResultRowSeq}
										getRowKey={row => row.key}
										rowClassName="hover:bg-sky-500/6"
										enableFiltering
										enableSorting
										enableColumnResize
										rowHeight={36}
										columnHeaderHeight={36}
										emptyMsg="관망해석 결과가 없습니다."
										ariaLabel="관망해석 결과"
									/>
								</CommonCard>
							</CommonCard>
						</div>
					</section>
				</div>
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
				buttons={[]}
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
											key={`demand-${rowIndex}-${cellIndex}-name`}
											className="border border-[#35517d] bg-[rgba(8,18,36,0.96)] px-3 py-[5px] text-center text-[13px] font-semibold text-white"
										>
											{cell.name}
										</td>,
										<td
											key={`demand-${rowIndex}-${cellIndex}-value`}
											className="border border-[#35517d] bg-[rgba(8,18,36,0.96)] px-[6px] py-[4px]"
										>
											<input
												type="text"
												value={cell.value}
												readOnly
												aria-label={`${cell.name} 수요량`}
												className="h-[30px] w-full cursor-default rounded-[3px] border border-[#3f6798] bg-[rgba(13,31,58,0.72)] px-[10px] text-left text-[13px] text-sky-50 outline-none shadow-[inset_0_0_0_1px_rgba(11,28,55,0.52)]"
											/>
										</td>,
									])}
									{row.length < 3 ? (
										<td
											colSpan={(3 - row.length) * 2}
											className="border border-[#35517d] bg-[rgba(8,18,36,0.96)]"
										/>
									) : null}
								</tr>
							))}
						</tbody>
					</table>
				</CommonCard>
			</CommonDialog>
		</div>
	);
}

export default PipNetSimulation;
