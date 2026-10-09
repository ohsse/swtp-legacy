import { COMPARISON_TARGET_COLUMN_SEQ, SETTING_VALUE_COLUMN_SEQ, resolveApiErrorMessage } from '@/consts/index.js';
import CommonModal from '@/web/components/CommonModal.jsx';
import CommonButton from '@/web/components/common/CommonButton.jsx';
import CommonTable from '@/web/components/common/CommonTable.jsx';
import { showToast } from '@/web/components/common/CommonToast.jsx';
import { inpApi } from '@/web/js/apis/inpApi.js';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

function extractResponseData(response) {
	if (Array.isArray(response)) return response;
	if (Array.isArray(response?.data)) return response.data;
	return [];
}

async function resolveApiErrorCode(error) {
	try {
		const errorBody = await error?.response?.clone?.().json?.();
		return errorBody?.code ?? '';
	} catch {
		return '';
	}
}

function normalizeSettingRows(response, mode) {
	return extractResponseData(response).map((row, index) => ({
		...row,
		id: row.mappingId ?? row.comparisonTargetId ?? row.targetId ?? `setting-row-${mode}-${index}`,
		mappingId: row.mappingId ?? null,
		comparisonTargetId: row.comparisonTargetId ?? row.targetId ?? null,
		pointNm: row.pointNm ?? '',
		junctionId: row.junctionId ?? '',
		pipeId: row.pipeId ?? '',
		flowTagNo: row.flowTagNo ?? '',
		pressureTagNo: row.pressureTagNo ?? '',
		nodeId: row.nodeId ?? '',
		tagNo: row.tagNo ?? '',
		analYn: row.analYn ?? 'Y',
		dispYn: row.dispYn ?? 'Y',
		sortOrd: row.sortOrd ?? index + 1,
	}));
}

function createEmptySettingRow(nextIndex, mode) {
	return {
		id: `setting-row-new-${mode}-${Date.now()}`,
		mappingId: null,
		comparisonTargetId: null,
		pointNm: '',
		junctionId: '',
		pipeId: '',
		flowTagNo: '',
		pressureTagNo: '',
		nodeId: '',
		tagNo: '',
		analYn: 'Y',
		dispYn: 'Y',
		sortOrd: nextIndex,
	};
}

function normalizeOptionalMappingValue(value) {
	const trimmedValue = String(value ?? '').trim();
	return trimmedValue.length > 0 ? trimmedValue : null;
}

function buildInpMappingRequest(row, mode) {
	if (mode === 'comparisonTarget') {
		return {
			nodeId: normalizeOptionalMappingValue(row.nodeId),
			tagNo: normalizeOptionalMappingValue(row.tagNo),
			analYn: row.analYn || 'Y',
		};
	}

	const commonRequest = {
		junctionId: normalizeOptionalMappingValue(row.junctionId),
		flowTagNo: normalizeOptionalMappingValue(row.flowTagNo),
		pressureTagNo: normalizeOptionalMappingValue(row.pressureTagNo),
		pointNm: normalizeOptionalMappingValue(row.pointNm),
		sortOrd: Number(row.sortOrd) || 0,
		dispYn: row.dispYn || 'Y',
	};

	return {
		...commonRequest,
		pipeId: normalizeOptionalMappingValue(row.pipeId),
	};
}

function serializeInpMappingRequest(row, mode) {
	return JSON.stringify(buildInpMappingRequest(row, mode));
}

function buildOriginalRequestMap(rows, idKey, mode) {
	return rows.reduce((requestMap, row) => {
		const rowId = row[idKey];
		if (rowId) {
			requestMap[String(rowId)] = serializeInpMappingRequest(row, mode);
		}
		return requestMap;
	}, {});
}

function resolveChangedRows(rows, idKey, originalRequestMap, mode) {
	return rows.filter(row => {
		const rowId = row[idKey];
		if (!rowId) return true;

		return originalRequestMap[String(rowId)] !== serializeInpMappingRequest(row, mode);
	});
}

const DIALOG_CONFIG_BY_MODE = {
	settingValue: {
		title: '비교대상 설정',
		emptyMsg: '비교대상이 없습니다.',
		saveSuccessMsg: '비교대상을 저장했습니다.',
		saveFailMsg: '비교대상 저장에 실패했습니다.',
		requiredKeys: ['junctionId'],
		requiredMsg: '절점ID는 필수입니다.',
		columnSeq: SETTING_VALUE_COLUMN_SEQ,
		idKey: 'mappingId',
		loadFailMsg: '비교대상 목록 조회에 실패했습니다.',
		deleteTargetMsg: '비교대상을 삭제할 모델을 먼저 선택해주세요.',
		deleteSuccessMsg: '비교대상을 삭제했습니다.',
		deleteFailMsg: '비교대상 삭제에 실패했습니다.',
		saveTargetMsg: '비교대상을 저장할 모델을 먼저 선택해주세요.',
		api: {
			list: inpApi.getInpMappingList,
			add: inpApi.addInpMapping,
			modify: inpApi.modifyInpMapping,
			remove: inpApi.removeInpMapping,
		},
	},
	comparisonTarget: {
		title: '분석대상 설정',
		emptyMsg: '분석대상이 없습니다.',
		saveSuccessMsg: '분석대상을 저장했습니다.',
		saveFailMsg: '분석대상 저장에 실패했습니다.',
		requiredKeys: ['nodeId', 'tagNo'],
		requiredMsg: '노드아이디와 태그번호는 필수입니다.',
		columnSeq: COMPARISON_TARGET_COLUMN_SEQ,
		idKey: 'mappingId',
		loadFailMsg: '분석대상 목록 조회에 실패했습니다.',
		deleteTargetMsg: '분석대상을 삭제할 모델을 먼저 선택해주세요.',
		deleteSuccessMsg: '분석대상을 삭제했습니다.',
		deleteFailMsg: '분석대상 삭제에 실패했습니다.',
		saveTargetMsg: '분석대상을 저장할 모델을 먼저 선택해주세요.',
		api: {
			list: inpApi.getAnalsMappingList,
			add: inpApi.addAnalsMapping,
			modify: inpApi.modifyAnalsMapping,
			remove: inpApi.removeAnalsMapping,
		},
	},
};

function buildColumnSeq(mode) {
	const config = DIALOG_CONFIG_BY_MODE[mode] ?? DIALOG_CONFIG_BY_MODE.settingValue;

	return config.columnSeq.map(column => ({
		...column,
		editable: column.editable ?? true,
		headClassName:
			'border-b border-r border-[rgba(110,185,255,0.18)] bg-[rgba(14,42,82,0.9)] px-2 text-center text-[12px] font-semibold text-sky-50',
		cellClassName: 'border-b border-r border-[rgba(110,185,255,0.1)] px-1.5 text-sky-50',
	}));
}

const settingTableSx = {
	border: '1px solid rgba(110,185,255,0.3)',
	backgroundColor: 'rgba(5,16,37,0.44)',
	'& .MuiDataGrid-main': {
		backgroundColor: 'transparent',
	},
	'& .MuiDataGrid-columnHeaders, & .MuiDataGrid-topContainer': {
		backgroundColor: 'rgba(13,42,82,0.96)',
		borderBottom: '1px solid rgba(125,211,252,0.58)',
	},
	'& .MuiDataGrid-columnHeader': {
		minHeight: '40px !important',
		backgroundColor: 'rgba(13,42,82,0.96)',
	},
	'& .MuiDataGrid-filler, & .MuiDataGrid-contentFiller, & .MuiDataGrid-scrollbarFiller, & .MuiDataGrid-filler--borderBottom, & .MuiDataGrid-filler--horizontal':
		{
			backgroundColor: 'transparent !important',
			borderColor: 'transparent !important',
		},
	'& .MuiDataGrid-overlayWrapper': {
		minHeight: '132px',
		backgroundColor: 'rgba(5,16,37,0.34)',
	},
	'& .MuiDataGrid-overlayWrapperInner': {
		minHeight: '132px !important',
	},
	'& .MuiDataGrid-row': {
		backgroundColor: 'rgba(7,24,53,0.56)',
	},
};

function SettingValueDialog({ open, setOpen, selectedModelFile, mode = 'settingValue' }) {
	const dialogConfig = DIALOG_CONFIG_BY_MODE[mode] ?? DIALOG_CONFIG_BY_MODE.settingValue;
	const columnSeq = useMemo(() => buildColumnSeq(mode), [mode]);
	const inpFileId = selectedModelFile?.inpFileId;
	const [rowSeq, setRowSeq] = useState([]);
	const [selectedRowKey, setSelectedRowKey] = useState(null);
	const [isLoading, setIsLoading] = useState(false);
	const [isSaving, setIsSaving] = useState(false);
	const [isDeleting, setIsDeleting] = useState(false);
	const originalRequestMapRef = useRef({});

	const loadMappingRows = useCallback(async () => {
		if (!inpFileId) {
			setRowSeq([]);
			setSelectedRowKey(null);
			originalRequestMapRef.current = {};
			return;
		}

		setIsLoading(true);
		try {
			const response = await dialogConfig.api.list(inpFileId, { skipErrorToast: true });
			const nextRows = normalizeSettingRows(response, mode);
			setRowSeq(nextRows);
			originalRequestMapRef.current = buildOriginalRequestMap(nextRows, dialogConfig.idKey, mode);
			setSelectedRowKey(prev => (nextRows.some(row => row.id === prev) ? prev : null));
		} catch (error) {
			console.error(`Failed to load ${mode} rows.`, error);
			showToast('error', dialogConfig.loadFailMsg);
			setRowSeq([]);
			setSelectedRowKey(null);
			originalRequestMapRef.current = {};
		} finally {
			setIsLoading(false);
		}
	}, [dialogConfig, inpFileId, mode]);

	useEffect(() => {
		if (!open) return;

		const timerId = window.setTimeout(() => {
			loadMappingRows();
		}, 0);

		return () => {
			window.clearTimeout(timerId);
		};
	}, [loadMappingRows, open]);

	const handleAdd = () => {
		setRowSeq(prev => {
			const nextIndex = prev.length + 1;
			const nextRow = createEmptySettingRow(nextIndex, mode);
			setSelectedRowKey(nextRow.id);
			return [...prev, nextRow];
		});
	};

	const handleDelete = async () => {
		if (!selectedRowKey) return;

		const selectedRow = rowSeq.find(row => row.id === selectedRowKey);
		if (!selectedRow) return;

		const selectedRowId = selectedRow[dialogConfig.idKey];

		if (!selectedRowId) {
			setRowSeq(prev => prev.filter(row => row.id !== selectedRowKey));
			setSelectedRowKey(null);
			return;
		}

		if (!inpFileId) {
			showToast('error', dialogConfig.deleteTargetMsg);
			return;
		}

		setIsDeleting(true);
		try {
			await dialogConfig.api.remove(inpFileId, selectedRowId, { skipErrorToast: true });
			showToast('info', dialogConfig.deleteSuccessMsg);
			await loadMappingRows();
		} catch (error) {
			console.error(`Failed to delete ${mode} row.`, error);
			showToast('error', dialogConfig.deleteFailMsg);
		} finally {
			setIsDeleting(false);
		}
	};

	const handleCellChange = useCallback((row, key, value) => {
		setRowSeq(prev => prev.map(item => (item.id === row.id ? { ...item, [key]: value } : item)));
	}, []);
	const getSettingRowKey = useCallback(row => row.id, []);
	const handleRowClick = useCallback(row => setSelectedRowKey(row.id), []);
	const resolveRowClassName = useCallback(
		(_row, _rowKey, isSelected) => (isSelected ? 'bg-sky-500/18 hover:bg-sky-500/22' : 'bg-transparent'),
		[]
	);

	const handleSave = async () => {
		if (!inpFileId) {
			showToast('error', dialogConfig.saveTargetMsg);
			return;
		}

		const invalidRow = rowSeq.find(row =>
			dialogConfig.requiredKeys.some(requiredKey => !String(row[requiredKey] ?? '').trim())
		);
		if (invalidRow) {
			showToast('error', dialogConfig.requiredMsg);
			setSelectedRowKey(invalidRow.id);
			return;
		}

		setIsSaving(true);
		try {
			const changedRows = resolveChangedRows(rowSeq, dialogConfig.idKey, originalRequestMapRef.current, mode);

			if (changedRows.length === 0) {
				showToast('info', '저장할 변경사항이 없습니다.');
				return;
			}

			for (const row of changedRows) {
				const requestBody = buildInpMappingRequest(row, mode);
				const rowId = row[dialogConfig.idKey];

				if (rowId) {
					await dialogConfig.api.modify(inpFileId, rowId, requestBody, { skipErrorToast: true });
				} else {
					await dialogConfig.api.add(inpFileId, requestBody, { skipErrorToast: true });
				}
			}

			showToast('info', dialogConfig.saveSuccessMsg);
			await loadMappingRows();
		} catch (error) {
			console.error('Failed to save INP mappings.', error);
			const errorCode = await resolveApiErrorCode(error);
			showToast('error', resolveApiErrorMessage(errorCode, dialogConfig.saveFailMsg));
		} finally {
			setIsSaving(false);
		}
	};

	return (
		<CommonModal
			open={open}
			onOpenChange={setOpen}
			title={dialogConfig.title}
			preset="editor"
			actionLabel={null}
			showCancel={false}
			showFooter={false}
			closeOnBackdrop={true}
			contentClassName={mode === 'comparisonTarget' ? 'w-[min(92vw,520px)]' : 'w-[min(96vw,860px)]'}
			panelSx={{
				maxWidth: mode === 'comparisonTarget' ? '520px' : '860px',
			}}
		>
			<div className="flex min-h-[260px] flex-col gap-2">
				<div className="flex justify-end gap-1.5">
					<CommonButton
						text="삭제"
						variant="destructive"
						size="sm"
						className="h-8 min-w-[58px] !border-red-300/70 !bg-[linear-gradient(180deg,#d94555,#a82c3a)] px-3 text-[11px] !font-semibold !text-white shadow-[0_0_0_1px_rgba(255,255,255,0.06),0_8px_16px_rgba(127,29,29,0.18)] hover:!border-red-200 hover:!bg-[linear-gradient(180deg,#ef5262,#bf3344)] disabled:!border-red-200/55 disabled:!bg-[linear-gradient(180deg,rgba(153,27,27,0.88),rgba(127,29,29,0.78))] disabled:!text-red-50/90 disabled:!opacity-100"
						isLoading={isDeleting}
						preventDoubleClick={true}
						disabled={!selectedRowKey || isDeleting}
						onClick={handleDelete}
					/>
					<CommonButton
						text="저장"
						size="sm"
						className="h-8 min-w-[58px] px-3 text-[11px]"
						isLoading={isSaving}
						preventDoubleClick={true}
						disabled={isSaving}
						onClick={handleSave}
					/>
					<CommonButton
						text="추가"
						variant="outline"
						size="sm"
						className="h-8 min-w-[58px] px-3 text-[11px]"
						disabled={!inpFileId}
						onClick={handleAdd}
					/>
				</div>

				<div className="model-editor-setting-table h-[212px] overflow-hidden rounded-[14px] border border-[rgba(110,185,255,0.28)] bg-[linear-gradient(180deg,rgba(7,22,51,0.82),rgba(5,16,37,0.9))] p-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]">
					<CommonTable
						colSeq={columnSeq}
						rowSeq={rowSeq}
							getRowKey={getSettingRowKey}
						emptyMsg={dialogConfig.emptyMsg}
						loading={isLoading}
						columnHeaderHeight={40}
						selectedRowKey={selectedRowKey}
							onRowClick={handleRowClick}
							onCellChange={handleCellChange}
							rowClassName={resolveRowClassName}
						sx={settingTableSx}
					/>
				</div>
			</div>
		</CommonModal>
	);
}

export default SettingValueDialog;
