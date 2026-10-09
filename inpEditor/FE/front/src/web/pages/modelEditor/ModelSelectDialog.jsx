import {
	HTTP_CODE_FILE_NOT_FOUND,
	LINK_LAYER_NAMES,
	MODEL_EDITOR_MAP_ID,
	MODEL_EDITOR_RIPPLE_COLOR,
	MODEL_SELECT_DEFAULT_FIELD_ORDER,
	MODEL_SELECT_FIELD_LABEL_BY_KEY,
	MODEL_SELECT_FIELD_WIDTH_BY_KEY,
	MODEL_SELECT_TABLE_CLASS_NAME,
	NODE_LAYER_NAMES,
	resolveApiErrorMessage,
} from '@/consts/index.js';
import CommonModal from '@/web/components/CommonModal.jsx';
import CommonButton from '@/web/components/common/CommonButton.jsx';
import CommonTable from '@/web/components/common/CommonTable.jsx';
import { dismissToast, showToast } from '@/web/components/common/CommonToast.jsx';
import { inpApi } from '@/web/js/apis/inpApi.js';
import { saveDownloadResponse } from '@/web/js/utils/commonUtil.js';
import { getMap } from '@/web/js/utils/mapRegistry.js';
import { OlUtils as olUtils } from '@/web/js/utils/olUtils.js';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { IoCloseOutline, IoCloudUploadOutline, IoDownloadOutline, IoTrashOutline } from 'react-icons/io5';
import { StzUtils } from 'stzutil-js/node';

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

async function isFileNotFoundApiError(error) {
	if (error?.response?.status === 404) return true;

	const errorCode = await resolveApiErrorCode(error);
	return errorCode === HTTP_CODE_FILE_NOT_FOUND;
}

function formatDateTime(value) {
	if (!value) return '';
	return String(value).replace('T', ' ').slice(0, 19);
}

function formatFileSize(value) {
	const size = Number(value);
	if (!Number.isFinite(size)) return '';
	if (size < 1024) return `${size} B`;
	if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
	return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function getModelSelectFieldLabel(key) {
	return MODEL_SELECT_FIELD_LABEL_BY_KEY[key] ?? key;
}

function formatModelSelectValue(key, value) {
	if (key === 'fileSz') return formatFileSize(value);
	if (key === 'rgstDttm') return formatDateTime(value);
	// 서버의 mntr_yn 플래그. 해석엔진(epa)에 적용된 모델 한 건만 Y 이므로 그 행에만 표시한다.
	if (key === 'monitoringYn') return value === 'Y' ? '적용중' : '';
	if (value === null || value === undefined) return '';
	return value;
}

function buildModelSelectFieldKeys(fileList) {
	const keySet = new Set();

	extractResponseData(fileList).forEach(file => {
		Object.keys(file ?? {}).forEach(key => keySet.add(key));
	});

	return [
		...MODEL_SELECT_DEFAULT_FIELD_ORDER.filter(key => keySet.has(key)),
		...[...keySet].filter(key => !MODEL_SELECT_DEFAULT_FIELD_ORDER.includes(key)),
	];
}

function buildModelSelectRowSeq(fileList) {
	return extractResponseData(fileList).map((file, index) => ({
		...file,
		id: file.inpFileId ?? file.id ?? `inp-file-${index}`,
		...Object.fromEntries(Object.entries(file ?? {}).map(([key, value]) => [key, formatModelSelectValue(key, value)])),
	}));
}

function applyModelNetworkLayers(result) {
	if (StzUtils.isEmpty(result)) return;

	const map = getMap(MODEL_EDITOR_MAP_ID);
	if (!map) return;

	olUtils.addLayers(map, result.layers, {
		dataProjection: 'EPSG:5186',
		featureProjection: map.getView()?.getProjection?.()?.getCode?.() ?? 'EPSG:3857',
		fitLayerName: 'JUNCTIONS',
		fitMaxZoom: 16,
		labelZoom: 0,
		nodeZoom: 0,
		labelFontSize: 13,
		nodeSize: 8,
		linkSize: 3,
		colorMap: {
			PIPES: '#5a6b87',
			PUMPS: '#16a34a',
			VALVES: '#f59e0b',
			JUNCTIONS: '#1e293b',
			RESERVOIRS: '#38bdf8',
			TANKS: '#06b6d4',
			LABELS: '#334155',
		},
	});
}

function ModelSelectCheckBox({ checked, disabled = false, ariaLabel, onChange }) {
	return (
		<input
			type="checkbox"
			checked={checked}
			disabled={disabled}
			aria-label={ariaLabel}
			className="h-3.5 w-3.5 accent-sky-400 disabled:opacity-40"
			onChange={onChange}
			onClick={event => event.stopPropagation()}
		/>
	);
}

function buildModelSelectColSeq(
	fieldKeys,
	{ hasRows, rowCount, selectedDownloadRowKeys, onToggleAllDownloadRows, onToggleDownloadRow, onDownloadRow }
) {
	const isAllChecked = hasRows && rowCount > 0 && selectedDownloadRowKeys.size === rowCount;

	return [
		{
			key: '__downloadSelect',
			colNm: (
				<div className="flex items-center justify-center">
					<ModelSelectCheckBox
						checked={isAllChecked}
						disabled={!hasRows}
						ariaLabel="전체 선택"
						onChange={onToggleAllDownloadRows}
					/>
				</div>
			),
			widthClassName: 'w-[48px] text-center',
			headClassName: 'h-9 border border-[#d7dfeb] bg-[#edf2f8] px-1 text-center text-[12px] font-semibold text-white',
			cellClassName: 'h-10 border border-[#d7dfeb] px-1 text-center text-[12px] text-[#526783]',
			sortable: false,
			filterable: false,
			disableColumnMenu: true,
			resizable: false,
			render: row => (
				<ModelSelectCheckBox
					checked={selectedDownloadRowKeys.has(row.id)}
					ariaLabel={`${row.orgnlFileNm ?? row.inpFileId ?? '파일'} 선택`}
					onChange={() => onToggleDownloadRow(row.id)}
				/>
			),
		},
		...fieldKeys.map(key => ({
			key,
			colNm: getModelSelectFieldLabel(key),
			widthClassName: MODEL_SELECT_FIELD_WIDTH_BY_KEY[key] ?? 'w-[140px]',
			headClassName: MODEL_SELECT_TABLE_CLASS_NAME.headClassName,
			cellClassName: MODEL_SELECT_TABLE_CLASS_NAME.cellClassName,
		})),
		{
			key: '__downloadAction',
			colNm: '다운로드',
			widthClassName: 'w-[116px] text-center',
			headClassName: 'h-9 border border-[#d7dfeb] bg-[#edf2f8] px-2 text-center text-[12px] font-semibold text-white',
			cellClassName: 'h-10 border border-[#d7dfeb] px-2 text-center text-[12px] text-[#526783]',
			sortable: false,
			filterable: false,
			disableColumnMenu: true,
			resizable: false,
			render: row => (
				<div className="flex h-full w-full items-center justify-center">
					<CommonButton
						size="icon-sm"
						variant="ghost"
						Icon={IoDownloadOutline}
						iconClassName="h-4 w-4"
						disableRipple={false}
						rippleColor={MODEL_EDITOR_RIPPLE_COLOR}
						className="h-7 w-11 rounded-[6px] border border-[rgba(159,210,255,0.32)] bg-[rgba(42,92,150,0.36)] text-sky-50 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] hover:border-[rgba(199,232,255,0.55)] hover:bg-[rgba(54,116,184,0.48)]"
						ariaLabel={`${row.orgnlFileNm ?? row.inpFileId ?? '파일'} 다운로드`}
						onClick={event => {
							event.stopPropagation();
							onDownloadRow(row);
						}}
					/>
				</div>
			),
		},
	];
}

function ModelSelectDialog({ open, setOpen, onApply }) {
	const fileInputRef = useRef(null);
	const [fileList, setFileList] = useState([]);
	const [pendingSelectedRowKey, setPendingSelectedRowKey] = useState(null);
	const [selectedDownloadRowKeys, setSelectedDownloadRowKeys] = useState(() => new Set());
	const [isMultiDownloading, setIsMultiDownloading] = useState(false);
	const [isDeletingFiles, setIsDeletingFiles] = useState(false);
	const [isUploadingFile, setIsUploadingFile] = useState(false);
	const [selectedUploadFile, setSelectedUploadFile] = useState(null);
	const modelSelectFieldKeys = useMemo(() => buildModelSelectFieldKeys(fileList), [fileList]);
	const modelSelectRowSeq = useMemo(() => buildModelSelectRowSeq(fileList), [fileList]);
	const pendingSelectedRow = useMemo(
		() => modelSelectRowSeq.find(row => row.id === pendingSelectedRowKey) ?? null,
		[modelSelectRowSeq, pendingSelectedRowKey]
	);
	const hasDownloadRows = modelSelectRowSeq.length > 0;
	const selectedDownloadRows = useMemo(
		() => modelSelectRowSeq.filter(row => selectedDownloadRowKeys.has(row.id)),
		[modelSelectRowSeq, selectedDownloadRowKeys]
	);
	const applyTargetRow = pendingSelectedRow ?? selectedDownloadRows[0] ?? null;

	const handleOpenChange = nextOpen => {
		if (!nextOpen) {
			setSelectedUploadFile(null);
		}
		setOpen(nextOpen);
	};

	const loadFileList = useCallback(async () => {
		const response = await inpApi.getInpFile({});
		const nextFileList = extractResponseData(response);
		const nextRowKeys = new Set(nextFileList.map((file, index) => file.inpFileId ?? file.id ?? `inp-file-${index}`));

		setFileList(nextFileList);
		setSelectedDownloadRowKeys(new Set());
		setPendingSelectedRowKey(prev => (prev && nextRowKeys.has(prev) ? prev : null));

		return nextFileList;
	}, []);

	const handleToggleDownloadRow = useCallback(rowKey => {
		setSelectedDownloadRowKeys(prev => {
			const next = new Set(prev);

			if (next.has(rowKey)) {
				next.delete(rowKey);
			} else {
				next.add(rowKey);
			}

			return next;
		});
	}, []);

	const handleToggleAllDownloadRows = useCallback(() => {
		setSelectedDownloadRowKeys(prev => {
			if (prev.size === modelSelectRowSeq.length) {
				return new Set();
			}

			return new Set(modelSelectRowSeq.map(row => row.id));
		});
	}, [modelSelectRowSeq]);

	const handleDownloadRow = useCallback(async row => {
		if (!row?.inpFileId) return;

		try {
			const response = await inpApi.downloadInpFile(row.inpFileId, { skipErrorToast: true });
			await saveDownloadResponse(response, row.orgnlFileNm ?? `${row.inpFileId}.inp`);
		} catch (error) {
			console.error('Failed to download INP file.', error);
			showToast('error', '파일 다운로드에 실패했습니다.');
		}
	}, []);

	const handleMultiDownload = async () => {
		const targetRows = selectedDownloadRows.length > 0 ? selectedDownloadRows : modelSelectRowSeq;

		if (targetRows.length === 0) {
			showToast('error', '다운로드할 파일이 없습니다.');
			return;
		}

		setIsMultiDownloading(true);
		try {
			const response = await inpApi.multiDownloadInpFile(
				targetRows.map(row => row.inpFileId),
				{ skipErrorToast: true }
			);
			await saveDownloadResponse(response, 'inp-files.zip');
		} catch (error) {
			console.error('Failed to download INP files.', error);
			showToast('error', '전체 다운로드에 실패했습니다.');
		} finally {
			setIsMultiDownloading(false);
		}
	};

	const handleDeleteSelectedRows = async () => {
		const targetRows = selectedDownloadRows.filter(row => row?.inpFileId);

		if (targetRows.length === 0) {
			showToast('error', '삭제할 파일을 선택해주세요.');
			return;
		}

		setIsDeletingFiles(true);
		try {
			await Promise.all(targetRows.map(row => inpApi.removeInpFile(row.inpFileId, { skipErrorToast: true })));
			showToast('info', '선택한 파일을 삭제했습니다.');
			await loadFileList();
		} catch (error) {
			console.error('Failed to delete INP files.', error);
			showToast('error', '파일 삭제에 실패했습니다.');
		} finally {
			setIsDeletingFiles(false);
		}
	};

	const handleUploadFileChange = event => {
		const file = event.target.files?.[0];
		event.target.value = '';

		if (!file) return;
		if (!file.name.toLowerCase().endsWith('.inp')) {
			showToast('error', 'INP 파일만 업로드할 수 있습니다.');
			return;
		}
		if (file.size <= 0) {
			showToast('error', '업로드된 파일이 비어 있습니다.');
			return;
		}

		setSelectedUploadFile(file);
	};

	const handleUploadSelectedFile = async () => {
		if (!selectedUploadFile) {
			showToast('error', '업로드할 파일을 선택해주세요.');
			return;
		}

		setIsUploadingFile(true);
		try {
			const response = await inpApi.uploadInpFile(selectedUploadFile, { skipErrorToast: true });
			const uploadedFile = response?.data;
			const uploadedRowKey = uploadedFile?.inpFileId ?? uploadedFile?.id ?? null;

			showToast('info', '파일을 업로드했습니다.');
			setSelectedUploadFile(null);
			await loadFileList();
			if (uploadedRowKey) {
				setPendingSelectedRowKey(uploadedRowKey);
			}
		} catch (error) {
			const errorCode = await resolveApiErrorCode(error);
			showToast('error', resolveApiErrorMessage(errorCode, '파일 업로드에 실패했습니다.'));
		} finally {
			setIsUploadingFile(false);
		}
	};

	const modelSelectColSeq = useMemo(
		() =>
			buildModelSelectColSeq(modelSelectFieldKeys, {
				hasRows: hasDownloadRows,
				rowCount: modelSelectRowSeq.length,
				selectedDownloadRowKeys,
				onToggleAllDownloadRows: handleToggleAllDownloadRows,
				onToggleDownloadRow: handleToggleDownloadRow,
				onDownloadRow: handleDownloadRow,
			}),
		[
			handleDownloadRow,
			handleToggleAllDownloadRows,
			handleToggleDownloadRow,
			hasDownloadRows,
			modelSelectFieldKeys,
			modelSelectRowSeq.length,
			selectedDownloadRowKeys,
		]
	);

	useEffect(() => {
		if (!open) return;

		const timerId = window.setTimeout(() => {
			loadFileList().catch(error => {
				console.error('Failed to load INP file list.', error);
				showToast('error', '파일 목록 조회에 실패했습니다.');
			});
		}, 0);

		return () => {
			window.clearTimeout(timerId);
		};
	}, [loadFileList, open]);

	const handleApply = async () => {
		if (!applyTargetRow) return;

		let response;
		try {
			response = await inpApi.getInpFileDetail(applyTargetRow.inpFileId, { skipErrorToast: true });
		} catch (error) {
			const isFileNotFound = await isFileNotFoundApiError(error);

			showToast(
				'error',
				isFileNotFound ? resolveApiErrorMessage(HTTP_CODE_FILE_NOT_FOUND) : '모델 정보를 불러오지 못했습니다.'
			);
			return;
		}

		const { code, data: result } = response;
		if (code === HTTP_CODE_FILE_NOT_FOUND) {
			showToast('error', resolveApiErrorMessage(code));
			return;
		}
		if (!StzUtils.isEmpty(result)) {
			applyModelNetworkLayers(result);
			await Promise.resolve(onApply?.(applyTargetRow, result));
		}
		handleOpenChange(false);
	};

	return (
		<CommonModal
			open={open}
			onOpenChange={handleOpenChange}
			title="모델 선택"
			preset="editor"
			actionLabel={null}
			showCancel={false}
			showFooter={true}
			closeOnBackdrop={true}
			panelSx={{
				maxWidth: '1180px',
			}}
			buttons={
				<div className="flex items-center gap-2">
					<CommonButton
						text="닫기"
						variant="outline"
						size="sm"
						onClick={() => handleOpenChange(false)}
						className="min-w-[84px]"
					/>
					<CommonButton
						text="적용"
						size="sm"
						className="min-w-[84px]"
						disabled={!applyTargetRow}
						onClick={handleApply}
					/>
				</div>
			}
		>
			<div className="mb-3 flex items-center justify-end gap-2">
				<input ref={fileInputRef} type="file" className="hidden" accept=".inp" onChange={handleUploadFileChange} />
				<CommonButton
					text="삭제"
					variant="destructive"
					size="sm"
					Icon={IoTrashOutline}
					iconClassName="h-3.5 w-3.5"
					className="h-8 min-w-[62px] px-3 text-[11px]"
					isLoading={isDeletingFiles}
					preventDoubleClick={true}
					disabled={selectedDownloadRows.length === 0 || isDeletingFiles}
					onClick={handleDeleteSelectedRows}
				/>
				<CommonButton
					text="전체 다운로드"
					variant="outline"
					size="sm"
					Icon={IoDownloadOutline}
					iconClassName="h-3.5 w-3.5"
					className="h-8 px-3 text-[11px]"
					isLoading={isMultiDownloading}
					preventDoubleClick={true}
					disabled={modelSelectRowSeq.length === 0 || isMultiDownloading}
					onClick={handleMultiDownload}
				/>
				<CommonButton
					text="파일 업로드"
					variant="outline"
					size="sm"
					Icon={IoCloudUploadOutline}
					iconClassName="h-3.5 w-3.5"
					className="h-8 px-3 text-[11px]"
					disabled={isUploadingFile}
					onClick={() => fileInputRef.current?.click()}
				/>
				{selectedUploadFile ? (
					<div className="flex h-8 min-w-0 items-center overflow-hidden rounded-[3px] border border-sky-300/24 bg-[linear-gradient(180deg,rgba(23,48,86,0.92),rgba(13,31,61,0.92))] shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
						<div className="flex min-w-0 items-center gap-1.5 px-2.5">
							<IoCloudUploadOutline className="h-3.5 w-3.5 shrink-0 text-sky-200/80" />
							<span className="max-w-[210px] truncate text-[11px] font-medium text-sky-50">
								{selectedUploadFile.name}
							</span>
						</div>
						<CommonButton
							text="업로드"
							size="xs"
							className="h-full min-w-[60px] rounded-none border-y-0 border-r-0 px-2 text-[11px]"
							isLoading={isUploadingFile}
							preventDoubleClick={true}
							disabled={isUploadingFile}
							onClick={handleUploadSelectedFile}
						/>
						<CommonButton
							size="icon-xs"
							variant="ghost"
							className="h-full w-7 rounded-none border-y-0 border-r-0 px-0 text-sky-100/72 hover:text-white"
							Icon={IoCloseOutline}
							iconClassName="h-4 w-4"
							ariaLabel="선택 파일 해제"
							disabled={isUploadingFile}
							onClick={() => setSelectedUploadFile(null)}
						/>
					</div>
				) : null}
			</div>
			<div className="overflow-hidden rounded-[14px] border border-[rgba(110,185,255,0.16)] bg-[linear-gradient(180deg,rgba(10,26,56,0.72),rgba(8,19,42,0.76))] p-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
				<CommonTable
					colSeq={modelSelectColSeq}
					rowSeq={modelSelectRowSeq}
					getRowKey={row => row.id}
					emptyMsg=""
					enableSorting={true}
					enableFiltering={true}
					enableColumnResize={true}
					disableHeaderSortClick={true}
					selectedRowKey={pendingSelectedRowKey}
					onRowClick={row => setPendingSelectedRowKey(row.id)}
				/>
			</div>
		</CommonModal>
	);
}

export default ModelSelectDialog;
