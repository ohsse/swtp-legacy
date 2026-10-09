import CommonButton from '@/web/components/common/CommonButton.jsx';
import CommonCard from '@/web/components/common/CommonCard.jsx';
import CommonTable from '@/web/components/common/CommonTable.jsx';
import { useMemo, useState } from 'react';
import { IoDownloadOutline } from 'react-icons/io5';

function RevisionListPanel({ revisionRowSeq = [], onRevisionSave, onRevisionDownload, isRevisionSaving = false }) {
	const revisionSelectionKey = useMemo(
		() => revisionRowSeq.map(row => `${row.id}:${row.checked ? 1 : 0}`).join('|'),
		[revisionRowSeq]
	);
	const [versionSelection, setVersionSelection] = useState(() => ({
		key: revisionSelectionKey,
		selectedId: revisionRowSeq.find(row => row.checked)?.id ?? null,
	}));

	if (versionSelection.key !== revisionSelectionKey) {
		setVersionSelection({
			key: revisionSelectionKey,
			selectedId: revisionRowSeq.find(row => row.checked)?.id ?? null,
		});
	}

	const resolvedVersionRowSeq = useMemo(
		() =>
			revisionRowSeq.map(row => ({
				...row,
				checked: row.id === versionSelection.selectedId,
			})),
		[revisionRowSeq, versionSelection.selectedId]
	);
	const selectedRevisionRow = useMemo(
		() => resolvedVersionRowSeq.find(row => row.id === versionSelection.selectedId) ?? null,
		[resolvedVersionRowSeq, versionSelection.selectedId]
	);
	const versionColSeq = useMemo(
		() => [
			{
				key: 'checked',
				colNm: '',
				widthClassName: 'w-[34px] text-center',
				headClassName: 'revision-check-header border-0 bg-transparent text-center text-transparent',
				cellClassName: 'border-b border-r border-slate-800/70 justify-center text-center',
				render: row => (
					<input
						type="checkbox"
						checked={row.checked}
						className="h-3.5 w-3.5 accent-sky-400"
						onChange={() => {
							setVersionSelection(prev => ({
								...prev,
								selectedId: prev.selectedId === row.id ? null : row.id,
							}));
						}}
						onClick={event => event.stopPropagation()}
					/>
				),
			},
			{
				key: 'versionId',
				colNm: '버전 아이디',
				headClassName: 'border-b border-slate-700/70 bg-slate-900/55 text-slate-300',
				cellClassName: 'border-b border-slate-800/70 text-slate-100',
				render: row => (
					<div className="min-w-0 py-1">
						<span className="block whitespace-normal break-words leading-5 text-slate-100">{row.versionId}</span>
						{row.metaText ? (
							<span className="mt-0.5 block whitespace-normal break-words text-[11px] leading-4 text-slate-400">
								{row.metaText}
							</span>
						) : null}
					</div>
				),
			},
			{
				key: 'download',
				colNm: '',
				widthClassName: 'w-[48px] text-center',
				headClassName: 'border-b border-l border-slate-700/70 bg-slate-900/55 text-center text-slate-300',
				cellClassName: 'border-b border-l border-slate-800/70 justify-center text-center',
				render: row => (
					<CommonButton
						size="icon-xs"
						variant="outline"
						ariaLabel={`${row.versionId} 다운로드`}
						className="h-7 w-7"
						onClick={event => {
							event.stopPropagation();
							onRevisionDownload?.(row);
						}}
					>
						<IoDownloadOutline className="h-4 w-4" />
					</CommonButton>
				),
			},
		],
		[onRevisionDownload]
	);

	return (
		<CommonCard className="flex min-h-0 flex-col overflow-hidden rounded-[14px] border border-[rgba(110,185,255,0.2)] bg-[rgba(9,20,44,0.38)] p-0">
			<div className="flex h-9 shrink-0 items-center justify-end border-b border-[rgba(110,185,255,0.18)] px-2">
				<CommonButton
					text="저장"
					size="xs"
					variant="outline"
					className="min-w-[54px]"
					isLoading={isRevisionSaving}
					preventDoubleClick={true}
					disabled={!selectedRevisionRow || isRevisionSaving}
					onClick={() => onRevisionSave?.(selectedRevisionRow)}
				/>
			</div>
			<div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden">
				<CommonTable
					colSeq={versionColSeq}
					rowSeq={resolvedVersionRowSeq}
					getRowKey={row => row.id}
					emptyMsg="리비전 이력이 없습니다."
					autoRowHeight={true}
					enableColumnResize={true}
					selectedRowKey={selectedRevisionRow?.id ?? null}
					sx={{
						'& .revision-check-header': {
							backgroundColor: 'transparent !important',
							borderBottom: '0 !important',
							borderRight: '0 !important',
							color: 'transparent !important',
						},
					}}
					onRowClick={row => {
						setVersionSelection(prev => ({
							...prev,
							selectedId: row.id,
						}));
					}}
					rowClassName="hover:bg-slate-900/20"
				/>
			</div>
		</CommonCard>
	);
}

export default RevisionListPanel;
