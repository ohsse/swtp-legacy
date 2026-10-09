import {
	ANALS_YN,
	BASE_URL,
	HTTP_CODE_FILE_NOT_FOUND,
	INITIAL_STATUS_VALUE_SEQ_BY_OBJECT_TYPE,
	LAYER_ORDER,
	LAYER_OPTION_SEQ,
	LINK_LAYER_NAMES,
	MODEL_EDITOR_ACTION_BUTTON_SEQ,
	MODEL_EDITOR_BUTTON_PROPS,
	MODEL_EDITOR_EDIT_ACTION_BUTTON_SEQ,
	MODEL_EDITOR_MAP_ID,
	MODEL_EDITOR_RIPPLE_COLOR,
	MODEL_EDITOR_SELECT_MENU_PROPS,
	MODEL_TYPE_OPTION_SEQ,
	NODE_LAYER_NAMES,
	OBJECT_PROPERTY_LABEL_BY_KEY,
	OBJECT_TYPE_LABEL_BY_KEY,
	OBJ_TYPE_LAYER_NAME,
	OPTIMIZATION_DETAIL_COLUMN_SEQ,
	OPTIMIZATION_HISTORY_COLUMN_SEQ,
	OPTIMIZATION_RUN_LOG_COLUMN_SEQ,
	OPTIMIZATION_SETTING_COLUMN_SEQ,
	OPTIMIZATION_TABLE_CLASS_NAME,
	READ_ONLY_PROPERTY_KEY_SET,
	REQUIRED_PROPERTY_KEY_SEQ_BY_OBJECT_TYPE,
	resolveApiErrorMessage,
} from '@/consts/index.js';
import { dismissToast, showToast } from '@/web/components/common/CommonToast.jsx';
import CommonModal from '@/web/components/CommonModal.jsx';
import CommonDrawer from '@/web/components/common/CommonDrawer.jsx';
import { inpApi } from '@/web/js/apis/inpApi.js';
import { saveDownloadResponse } from '@/web/js/utils/commonUtil.js';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import CommonButton from '@/web/components/common/CommonButton.jsx';
import CommonCard from '@/web/components/common/CommonCard.jsx';
import CommonInput from '@/web/components/common/CommonInput.jsx';
import CommonSelect from '@/web/components/common/CommonSelect.jsx';
import CommonTable from '@/web/components/common/CommonTable.jsx';
import FeaturePropertyPanel from '@/web/pages/modelEditor/FeaturePropertyPanel.jsx';
import LayerFeatureTablePanel, { buildLayerTableRowFromFeature } from '@/web/pages/modelEditor/LayerFeatureTablePanel.jsx';
import MapCanvas from '@/web/components/common/MapCanvas.jsx';
import ModelSelectDialog from '@/web/pages/modelEditor/ModelSelectDialog.jsx';
import RevisionListPanel from '@/web/pages/modelEditor/RevisionListPanel.jsx';
import SettingValueDialog from '@/web/pages/modelEditor/SettingValueDialog.jsx';
import { getMap } from '@/web/js/utils/mapRegistry.js';
import { OlUtils as olUtils } from '@/web/js/utils/olUtils.js';
import GeoJSON from 'ol/format/GeoJSON.js';
import { IoPlayOutline, IoRefreshOutline } from 'react-icons/io5';
import { StzUtils } from 'stzutil-js/node';
import './ModelEditorPage.css';

function buildApiUrl(path, searchParams) {
	const normalizedBaseUrl = String(BASE_URL ?? '').replace(/\/+$/, '');
	const normalizedPath = String(path ?? '').replace(/^\/+/, '');
	const url = `${normalizedBaseUrl}/${normalizedPath}`;
	const queryString = new URLSearchParams(searchParams).toString();

	return queryString ? `${url}?${queryString}` : url;
}

async function fetchJson(url) {
	const response = await fetch(url);

	if (!response.ok) {
		throw new Error(`HTTP ${response.status}`);
	}

	return await response.json();
}

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

function normalizeInpFileName(fileName) {
	const trimmedFileName = String(fileName ?? '').trim();
	if (!trimmedFileName) return '';
	return /\.inp$/i.test(trimmedFileName) ? trimmedFileName : `${trimmedFileName}.inp`;
}

function createEmptyFeatureCollection() {
	return {
		type: 'FeatureCollection',
		features: [],
	};
}

function writeLayerNamesToFeatureCollection(map, layerNames, fallbackFeatureCollection) {
	const layers = layerNames.map(layerName => olUtils.getLayerByName(map, layerName)).filter(Boolean);
	if (layers.length === 0) return fallbackFeatureCollection ?? createEmptyFeatureCollection();

	const features = layers.flatMap(layer => layer.getSource?.()?.getFeatures?.() ?? []);
	const format = new GeoJSON();
	return format.writeFeaturesObject(features, {
		dataProjection: 'EPSG:5186',
		featureProjection: map?.getView?.()?.getProjection?.()?.getCode?.() ?? 'EPSG:3857',
	});
}

function buildNetworkSaveLayersFromMap(map, fallbackLayers = {}) {
	return {
		nodeLayer: writeLayerNamesToFeatureCollection(map, NODE_LAYER_NAMES, fallbackLayers.nodeLayer),
		linkLayer: writeLayerNamesToFeatureCollection(map, LINK_LAYER_NAMES, fallbackLayers.linkLayer),
		labelLayer: writeLayerNamesToFeatureCollection(map, ['LABELS'], fallbackLayers.labelLayer),
	};
}

function hasCurvePointValue(value) {
	return String(value ?? '').trim() !== '';
}

function sanitizeCurvePointSeqForSave(pointSeq) {
	if (!Array.isArray(pointSeq)) return [];

	return pointSeq
		.filter(point => hasCurvePointValue(point?.x) && hasCurvePointValue(point?.y))
		.map(point => ({
			x: normalizeCurvePointValue(point.x),
			y: normalizeCurvePointValue(point.y),
		}));
}

function sanitizeNetworkSectionsForSave(sections = {}) {
	if (!Array.isArray(sections?.CURVES)) return sections;

	return {
		...sections,
		CURVES: sections.CURVES.map(curve => ({
			...curve,
			xyData: sanitizeCurvePointSeqForSave(curve?.xyData),
		})),
	};
}

function resolveNetworkOptionsForSave(networkDetail) {
	return networkDetail?.sections?.OPTIONS ?? networkDetail?.options ?? {};
}

function buildNetworkSavePayload(networkDetail) {
	const map = getMap(MODEL_EDITOR_MAP_ID);
	const sections = sanitizeNetworkSectionsForSave(networkDetail?.sections ?? {});

	return {
		meta: networkDetail?.meta ?? null,
		layers: map ? buildNetworkSaveLayersFromMap(map, networkDetail?.layers ?? {}) : (networkDetail?.layers ?? {}),
		sections,
		options: resolveNetworkOptionsForSave({
			...networkDetail,
			sections,
		}),
	};
}

function updateNestedValueByPath(currentValue, pathSeq, nextValue) {
	if (!Array.isArray(pathSeq) || pathSeq.length === 0) return nextValue;

	const [currentPath, ...nextPathSeq] = pathSeq;
	if (Array.isArray(currentValue)) {
		const nextArray = [...currentValue];
		nextArray[currentPath] = updateNestedValueByPath(nextArray[currentPath], nextPathSeq, nextValue);
		return nextArray;
	}

	const nextObject = currentValue && typeof currentValue === 'object' ? { ...currentValue } : {};
	nextObject[currentPath] = updateNestedValueByPath(nextObject[currentPath], nextPathSeq, nextValue);
	return nextObject;
}

function isSamePathSeq(sourcePathSeq, targetPathSeq) {
	if (!Array.isArray(sourcePathSeq) || !Array.isArray(targetPathSeq)) return false;
	if (sourcePathSeq.length !== targetPathSeq.length) return false;
	return sourcePathSeq.every((pathItem, index) => pathItem === targetPathSeq[index]);
}

function parseControlRuleText(value, fallbackId = '') {
	const text = String(value ?? '');
	const lineSeq = text.split(/\r?\n/);
	const ruleHeaderMatch = lineSeq[0]?.trim().match(/^RULE\s+(.+)$/i);

	if (!ruleHeaderMatch) {
		return {
			id: fallbackId,
			content: text,
		};
	}

	return {
		id: ruleHeaderMatch[1].trim(),
		content: lineSeq.slice(1).join('\n'),
	};
}

function parseControlSimpleText(value) {
	return String(value ?? '')
		.split(/\r?\n/)
		.map(line => line.trim())
		.filter(Boolean);
}

function resolveNextControlRuleId(ruleSeq) {
	const maxId = (ruleSeq ?? []).reduce((currentMaxId, rule) => {
		const numericId = Number(rule?.id);
		return Number.isFinite(numericId) ? Math.max(currentMaxId, numericId) : currentMaxId;
	}, 0);

	return String(maxId + 1);
}

function reindexControlRuleSeq(ruleSeq) {
	return (Array.isArray(ruleSeq) ? ruleSeq : []).map((rule, index) => ({
		...(rule ?? {}),
		id: String(index + 1),
	}));
}

function buildControlRuleRowSeq(ruleSeq) {
	return (Array.isArray(ruleSeq) ? ruleSeq : []).map((rule, index) => ({
		index,
		id: String(rule?.id ?? index + 1),
		title: `RULE ${rule?.id ?? index + 1}`,
		content: String(rule?.content ?? ''),
	}));
}

function updatePatternMultiplierSeq(currentMultiplierSeq, index, value) {
	if (!Number.isInteger(index) || index < 0) return Array.isArray(currentMultiplierSeq) ? [...currentMultiplierSeq] : [];

	const nextMultiplierSeq = Array.isArray(currentMultiplierSeq) ? [...currentMultiplierSeq] : [];
	nextMultiplierSeq[index] = value ?? '';

	let lastValueIndex = nextMultiplierSeq.length - 1;
	while (lastValueIndex >= 0 && String(nextMultiplierSeq[lastValueIndex] ?? '').trim() === '') {
		lastValueIndex -= 1;
	}

	return nextMultiplierSeq.slice(0, lastValueIndex + 1);
}

function normalizeCurvePointValue(value) {
	const trimmedValue = String(value ?? '').trim();
	if (!trimmedValue) return '';

	const numberValue = Number(trimmedValue);
	return Number.isFinite(numberValue) ? numberValue : value;
}

function updateCurvePointSeq(currentPointSeq, index, axis, value) {
	if (!Number.isInteger(index) || index < 0 || !['x', 'y'].includes(axis)) {
		return Array.isArray(currentPointSeq) ? [...currentPointSeq] : [];
	}

	const nextPointSeq = Array.isArray(currentPointSeq) ? currentPointSeq.map(point => ({ ...(point ?? {}) })) : [];
	const currentPoint = nextPointSeq[index] ?? {};
	nextPointSeq[index] = {
		...currentPoint,
		[axis]: normalizeCurvePointValue(value),
	};

	let lastValueIndex = nextPointSeq.length - 1;
	while (
		lastValueIndex >= 0 &&
		String(nextPointSeq[lastValueIndex]?.x ?? '').trim() === '' &&
		String(nextPointSeq[lastValueIndex]?.y ?? '').trim() === ''
	) {
		lastValueIndex -= 1;
	}

	return nextPointSeq.slice(0, lastValueIndex + 1);
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

function pickValue(source, keys, fallback = '') {
	if (!source) return fallback;

	for (const key of keys) {
		const value = source[key];
		if (value !== null && value !== undefined && value !== '') return value;
	}

	return fallback;
}

function formatPercentValue(value) {
	if (value === null || value === undefined || value === '') return '';
	const numberValue = Number(value);
	if (!Number.isFinite(numberValue)) return String(value);
	return `${numberValue.toFixed(Number.isInteger(numberValue) ? 0 : 1)}%`;
}

function formatOptimizationNumber(value) {
	if (value === null || value === undefined || value === '') return '';
	const numberValue = Number(value);
	if (!Number.isFinite(numberValue)) return String(value);
	return Number.isInteger(numberValue) ? String(numberValue) : numberValue.toFixed(3);
}

function resolveOptimizationDataTypeLabel(dataType) {
	const dataTypeLabelByCode = {
		FLOW: '유량',
		PRESSURE: '압력',
	};

	return dataTypeLabelByCode[dataType] ?? dataType ?? '';
}

function resolveOptimizationStatusLabel(statusCd) {
	const statusLabelByCode = {
		READY: '대기',
		RUNNING: '실행중',
		COMPLETED: '완료',
		ERROR: '오류',
	};

	return statusLabelByCode[statusCd] ?? statusCd ?? '';
}

function normalizeOptimizationHistoryRows(response) {
	return extractOptimizationHistoryItems(response).map((row, index) => {
		const histId = pickValue(row, ['histId', 'optHistId', 'id', 'histSeq'], index + 1);
		const statusCd = pickValue(row, ['statusCd', 'progressStatusCd', 'sttsCd']);
		const progressRate = pickValue(row, ['progressRate', 'progressPct', 'progressPercent', 'rate']);

		return {
			...row,
			id: String(histId),
			histId,
			startDttm: formatDateTime(pickValue(row, ['startDttm', 'strtDttm', 'execStartDttm', 'runStartDttm', 'rgstDttm'])),
			endDttm: formatDateTime(pickValue(row, ['endDttm', 'finishDttm', 'execEndDttm', 'runEndDttm', 'mdfcnDttm'])),
			fileRevNo: pickValue(row, ['fileRevNo', 'inpFileRevNo', 'revNo', 'revisionNo', 'currRevNo']),
			statusLabel: resolveOptimizationStatusLabel(statusCd),
			progressText: formatPercentValue(progressRate),
		};
	});
}

function extractArrayByKeys(source, keys) {
	for (const key of keys) {
		const value = source?.[key];
		if (Array.isArray(value)) return value;
	}

	return [];
}

function extractOptimizationPayload(response) {
	return response?.data ?? response ?? {};
}

function extractOptimizationHistoryItems(response) {
	const payload = extractOptimizationPayload(response);
	if (Array.isArray(payload)) return payload;

	return extractArrayByKeys(payload, [
		'historyRows',
		'histRows',
		'optHistRows',
		'historyList',
		'histList',
		'optHistList',
		'optimizationHistoryList',
		'list',
		'rows',
		'content',
	]);
}

function normalizeOptimizationSettingRows(detail) {
	return extractArrayByKeys(detail, [
		'optionSnap',
		'settingInfo',
		'settings',
		'settingRows',
		'settingValueList',
		'optSettingList',
		'configRows',
	]).map((row, index) => ({
		...row,
		id: String(pickValue(row, ['mappingId', 'id', 'settingId', 'rowId'], index + 1)),
		nodeId: pickValue(row, ['nodeId', 'nodeNo', 'junctionId', 'juncId']),
		tagNo: pickValue(row, [
			'tagNo',
			'tagNumber',
			'flowTagNo',
			'flowTagNumber',
			'flowTagId',
			'flowTag',
			'pressureTagNo',
			'pressureTagNumber',
			'pressureTagId',
			'pressureTag',
		]),
		analYn: pickValue(row, ['analYn', 'analysisYn', 'analsYn', 'useYn'], 'Y'),
	}));
}

function normalizeOptimizationDetailRows(detail) {
	return extractArrayByKeys(detail, [
		'comparisons',
		'settingDetailInfo',
		'settingDetails',
		'settingDetailRows',
		'detailSettingInfo',
		'detailSettingRows',
		'compareRows',
		'comparisonRows',
		'resultRows',
		'detailRows',
		'mergedRows',
		'optResultList',
	]).map((row, index) => ({
		...row,
		id: String(pickValue(row, ['id', 'resultId', 'rowId'], index + 1)),
		pointNm: pickValue(row, ['pointNm', 'siteNm', 'siteName', 'nodeNm']),
		dataTypeNm: resolveOptimizationDataTypeLabel(pickValue(row, ['dataTypeNm', 'dataType', 'itemNm', 'itemName', 'typeNm'])),
		measureValue: formatOptimizationNumber(pickValue(row, ['measureValue', 'measuredValue', 'obsValue', 'meterValue'])),
		beforeValue: formatOptimizationNumber(
			pickValue(row, ['prevAnalValue', 'beforeValue', 'beforeAnalysisValue', 'beforeAnalsValue', 'prevAnalysisValue'])
		),
		afterValue: formatOptimizationNumber(
			pickValue(row, ['resultAnalValue', 'afterValue', 'afterAnalysisValue', 'afterAnalsValue', 'nextAnalysisValue'])
		),
		beforeErrorRate: formatPercentValue(
			pickValue(row, ['beforeErrorRate', 'beforeErrRate', 'prevErrorRate', 'beforeErrorPct'])
		),
		afterErrorRate: formatPercentValue(
			pickValue(row, ['resultErrorRate', 'afterErrorRate', 'afterErrRate', 'nextErrorRate', 'afterErrorPct'])
		),
		improvementRate: formatPercentValue(pickValue(row, ['improvementRate', 'improveRate', 'improvementPct'])),
	}));
}

function normalizeOptimizationRunLogRows(detail, historyRow) {
	const explicitRows = extractArrayByKeys(detail, ['runLogs', 'executionLogs', 'workerLogs', 'jobRows', 'taskRows']);
	if (explicitRows.length > 0) {
		return explicitRows.map((row, index) => ({
			...row,
			id: String(pickValue(row, ['id', 'logId', 'rowId'], index + 1)),
			workerNm: pickValue(row, ['workerNm', 'workerName', 'jobNm', 'taskNm']),
			startDttm: formatDateTime(pickValue(row, ['startDttm', 'strtDttm', 'execStartDttm', 'runStartDttm'])),
			collectStartDttm: formatDateTime(pickValue(row, ['collectStartDttm', 'clctStartDttm'])),
			collectEndDttm: formatDateTime(pickValue(row, ['collectEndDttm', 'clctEndDttm'])),
			targetCnt: pickValue(row, ['targetCnt', 'targetCount', 'totGenerCount']),
			collectCnt: pickValue(row, ['collectCnt', 'clctCnt', 'collectedCount', 'implGenerCount']),
			cycle: pickValue(row, ['cycle', 'collectCycle', 'clctCycle']),
			progress: formatPercentValue(pickValue(row, ['progress', 'progressRate', 'progressPct'])),
		}));
	}

	const mergedRow = {
		...(historyRow ?? {}),
		...(detail ?? {}),
	};
	if (StzUtils.isEmpty(mergedRow)) return [];

	const statusCd = pickValue(mergedRow, ['statusCd', 'progressStatusCd', 'sttsCd']);

	return [
		{
			...mergedRow,
			id: String(pickValue(mergedRow, ['histId', 'id', 'rowId'], 1)),
			workerNm: `최적화 ${resolveOptimizationStatusLabel(statusCd) || '실행'}`,
			startDttm: formatDateTime(pickValue(mergedRow, ['startDttm', 'strtDttm', 'execStartDttm', 'runStartDttm'])),
			collectStartDttm: formatDateTime(pickValue(mergedRow, ['collectStartDttm', 'clctStartDttm', 'strtDttm'])),
			collectEndDttm: formatDateTime(pickValue(mergedRow, ['collectEndDttm', 'clctEndDttm', 'endDttm'])),
			targetCnt: pickValue(mergedRow, ['targetCnt', 'targetCount', 'totGenerCount']),
			collectCnt: pickValue(mergedRow, ['collectCnt', 'clctCnt', 'collectedCount', 'implGenerCount']),
			cycle: pickValue(mergedRow, ['cycle', 'collectCycle', 'clctCycle']),
			progress: formatPercentValue(pickValue(mergedRow, ['progress', 'progressRate', 'progressPct'])),
		},
	];
}

function normalizeOptimizationRunningRows(response) {
	return extractOptimizationHistoryItems(response).map((row, index) => ({
		...row,
		id: String(pickValue(row, ['histId', 'optHistId', 'id', 'histSeq'], index + 1)),
		workerNm: '최적화',
		startDttm: formatDateTime(pickValue(row, ['startDttm', 'strtDttm', 'execStartDttm', 'runStartDttm', 'rgstDttm'])),
		endDttm: formatDateTime(pickValue(row, ['endDttm', 'finishDttm', 'execEndDttm', 'runEndDttm', 'mdfcnDttm'])),
		totalGenerCount: pickValue(row, [
			'totalGenerCount',
			'totalGenerCnt',
			'totGenerCount',
			'totGenerCnt',
			'totalGenerationCount',
			'targetCnt',
			'targetCount',
		]),
		implGenerCount: pickValue(row, [
			'implGenerCount',
			'implGenerCnt',
			'progressGenerCount',
			'progressGenerCnt',
			'currentGenerCount',
			'currentGenerCnt',
			'collectCnt',
			'collectedCount',
		]),
		progress: formatPercentValue(pickValue(row, ['progressRate', 'progressPct', 'progressPercent', 'progress', 'rate'])),
	}));
}

function getCurrentRevNo(file) {
	return file?.currentRevNo ?? file?.currRevNo ?? file?.revNo ?? file?.revisionNo ?? null;
}

function toBooleanFlag(value) {
	if (typeof value === 'boolean') return value;
	if (typeof value === 'string') return ['Y', 'YES', 'TRUE', '1'].includes(value.toUpperCase());
	return Boolean(value);
}

function buildRevisionRowSeq(revisionList, inpFileId = 'revision', currentRevNo = null) {
	return extractResponseData(revisionList)
		.map((revision, index) => {
			const revNo = revision.revNo ?? revision.revisionNo ?? revision.currRevNo ?? index;
			const workType = revision.workType ?? '';
			const downloadFileNm = revision.downloadFileNm ?? revision.fileNm ?? revision.storFileNm ?? `revision-${revNo}`;
			const fileSz = revision.fileSz ?? revision.fileSize;
			const rgstDttm = revision.rgstDttm ?? revision.regDttm ?? revision.createdAt;
			const explicitCurrent = revision.current ?? revision.currentYn ?? revision.currYn;
			const current =
				explicitCurrent !== null && explicitCurrent !== undefined
					? toBooleanFlag(explicitCurrent)
					: currentRevNo !== null && currentRevNo !== undefined && String(revNo) === String(currentRevNo);
			const rowSourceId = revision.inpFileId ?? inpFileId;

			return {
				...revision,
				id: `${rowSourceId}-${revNo}-${index}`,
				revNo,
				workType,
				downloadFileNm,
				fileSz,
				rgstDttm,
				current,
				checked: current,
				versionId: downloadFileNm,
				metaText: [`r${revNo}`, workType, formatFileSize(fileSz), formatDateTime(rgstDttm)].filter(Boolean).join(' · '),
			};
		})
		.sort((left, right) => {
			if (left.current !== right.current) return left.current ? -1 : 1;
			return Number(right.revNo) - Number(left.revNo);
		});
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

function formatAnalysisYn(value) {
	const normalizedValue = String(value ?? '').toUpperCase();
	if (ANALS_YN[normalizedValue]) return ANALS_YN[normalizedValue];
	return value ?? '';
}

function renderAnalysisYn(row) {
	const value = row.analYn ?? row.analysisYn ?? row.analsYn ?? row.useYn;
	const label = formatAnalysisYn(value);
	const isInactive = String(value ?? '').toUpperCase() === 'N' || label === ANALS_YN.N;

	return <span className={isInactive ? 'font-semibold text-red-300' : 'text-sky-50'}>{label}</span>;
}

const optimizationHistoryColSeq = OPTIMIZATION_HISTORY_COLUMN_SEQ.map(column => ({
	...column,
	...OPTIMIZATION_TABLE_CLASS_NAME,
}));

const optimizationSettingColSeq = OPTIMIZATION_SETTING_COLUMN_SEQ.map(column => ({
	...column,
	valueFormatter: column.key === 'analYn' ? formatAnalysisYn : column.valueFormatter,
	render: column.key === 'analYn' ? renderAnalysisYn : column.render,
	...OPTIMIZATION_TABLE_CLASS_NAME,
}));

const optimizationDetailColSeq = OPTIMIZATION_DETAIL_COLUMN_SEQ.map(column => ({
	...column,
	...OPTIMIZATION_TABLE_CLASS_NAME,
}));

const optimizationRunLogColSeq = OPTIMIZATION_RUN_LOG_COLUMN_SEQ.map(column => ({
	...column,
	...OPTIMIZATION_TABLE_CLASS_NAME,
}));

function SaveAsFileNameToast({ defaultFileName, onConfirm, onCancel }) {
	const [fileName, setFileName] = useState(defaultFileName);
	const normalizedFileName = normalizeInpFileName(fileName);
	const isConfirmDisabled = normalizedFileName.length === 0;

	return (
		<div className="flex w-[300px] flex-col gap-3 text-slate-900">
			<div className="space-y-1">
				<p className="text-[13px] font-semibold text-slate-950">다른 이름으로 저장</p>
				<p className="text-[12px] leading-5 text-slate-600">파일명이 변경되어 새 INP 파일로 저장합니다.</p>
			</div>
			<input
				value={fileName}
				onChange={event => setFileName(event.target.value)}
				className="h-9 rounded-[6px] border border-slate-300 bg-white px-2 text-[13px] text-slate-950 outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-200"
				placeholder="파일명을 입력하세요"
				autoFocus
			/>
			<div className="flex justify-end gap-2">
				<button
					type="button"
					className="h-8 rounded-[4px] border border-slate-300 px-3 text-[12px] font-medium text-slate-700 hover:bg-slate-100"
					onClick={onCancel}
				>
					취소
				</button>
				<button
					type="button"
					className="h-8 rounded-[4px] border border-sky-600 bg-sky-600 px-3 text-[12px] font-semibold text-white hover:bg-sky-700 disabled:cursor-not-allowed disabled:border-slate-300 disabled:bg-slate-200 disabled:text-slate-500"
					disabled={isConfirmDisabled}
					onClick={() => onConfirm(normalizedFileName)}
				>
					저장
				</button>
			</div>
		</div>
	);
}

function requestSaveAsFileName(defaultFileName) {
	return new Promise(resolve => {
		let toastId;
		const handleCancel = () => {
			dismissToast(toastId);
			resolve(null);
		};
		const handleConfirm = fileName => {
			dismissToast(toastId);
			resolve(fileName);
		};

		toastId = showToast(
			'warn',
			<SaveAsFileNameToast defaultFileName={defaultFileName} onConfirm={handleConfirm} onCancel={handleCancel} />,
			{
				autoClose: false,
				closeButton: false,
				closeOnClick: false,
				draggable: false,
				position: 'top-center',
			}
		);
	});
}

function formatTableCellValue(value) {
	if (value === null || value === undefined) return '';
	if (typeof value === 'object') return JSON.stringify(value);
	return value;
}

function resolveLayerFeatureId(properties, fallbackId = '') {
	return properties.id ?? properties.ID ?? properties.name ?? properties.label ?? properties.LABEL ?? fallbackId ?? '';
}

function isBlankValue(value) {
	return value === null || value === undefined || String(value).trim() === '';
}

function getFeatureObjectType(feature, layerName) {
	return String(feature?.get?.('objectType') ?? OBJ_TYPE_LAYER_NAME[layerName] ?? '').toLowerCase();
}

function getFeatureValidationValue(feature, key) {
	if (!feature) return '';
	if (key === 'featureId') {
		const { geometry, ...properties } = feature.getProperties?.() ?? {};
		return resolveLayerFeatureId(properties, feature.getId?.());
	}

	return feature.get?.(key);
}

function getFeatureId(feature) {
	return getFeatureValidationValue(feature, 'featureId');
}

function formatFeatureValidationName(feature, layerName, index) {
	const objectType = getFeatureObjectType(feature, layerName);
	const objectLabel = OBJECT_TYPE_LABEL_BY_KEY[objectType] ?? layerName;
	const featureId = getFeatureValidationValue(feature, 'featureId');
	const fallbackNo = String(index + 1).padStart(2, '0');
	return featureId ? `${objectLabel} "${featureId}"` : `${objectLabel} ${fallbackNo}`;
}

function getPointCoordinate(feature) {
	const geometry = feature?.getGeometry?.();
	return geometry?.getType?.() === 'Point' ? geometry.getCoordinates() : null;
}

function getLineEndCoordinates(feature) {
	const geometry = feature?.getGeometry?.();
	if (geometry?.getType?.() !== 'LineString') return null;

	const coordinates = geometry.getCoordinates();
	if (!Array.isArray(coordinates) || coordinates.length < 2) return null;

	return {
		startCoordinate: coordinates[0],
		endCoordinate: coordinates[coordinates.length - 1],
	};
}

function getCoordinateDistanceSq(a, b) {
	if (!Array.isArray(a) || !Array.isArray(b)) return Number.POSITIVE_INFINITY;
	const dx = Number(a[0]) - Number(b[0]);
	const dy = Number(a[1]) - Number(b[1]);
	if (!Number.isFinite(dx) || !Number.isFinite(dy)) return Number.POSITIVE_INFINITY;
	return dx * dx + dy * dy;
}

function getNodeFeatures(map) {
	if (!map) return [];

	return NODE_LAYER_NAMES.flatMap(layerName => {
		const layer = olUtils.getLayerByName(map, layerName);
		return layer?.getSource?.()?.getFeatures?.() ?? [];
	});
}

function getLinkFeatures(map) {
	if (!map) return [];

	return LINK_LAYER_NAMES.flatMap(layerName => {
		const layer = olUtils.getLayerByName(map, layerName);
		return layer?.getSource?.()?.getFeatures?.() ?? [];
	});
}

function getFeatureLayerName(map, feature) {
	const layer = olUtils.findFeatureLayer(map, feature, { layerNames: LAYER_ORDER });
	return layer?.get?.('name') ?? feature?.get?.('layer') ?? null;
}

function isSameFeatureId(a, b) {
	if (isBlankValue(a) || isBlankValue(b)) return false;
	return String(a).trim() === String(b).trim();
}

function isCoordinateMatched(a, b, tolerance = 0.001) {
	return getCoordinateDistanceSq(a, b) <= tolerance * tolerance;
}

function findNodeFeatureById(map, nodeId) {
	if (isBlankValue(nodeId)) return null;

	return getNodeFeatures(map).find(feature => isSameFeatureId(getFeatureId(feature), nodeId)) ?? null;
}

function findNodeFeatureAtCoordinate(map, coordinate, tolerance = 0.001) {
	if (!map || !coordinate) return null;

	return (
		getNodeFeatures(map).find(feature => {
			const pointCoordinate = getPointCoordinate(feature);
			return isCoordinateMatched(coordinate, pointCoordinate, tolerance);
		}) ?? null
	);
}

function findNodeIdAtCoordinate(map, coordinate, tolerance = 0.001) {
	if (!map || !coordinate) return '';

	let matchedNodeId = '';
	let matchedDistanceSq = tolerance * tolerance;

	getNodeFeatures(map).forEach(feature => {
		const pointCoordinate = getPointCoordinate(feature);
		const distanceSq = getCoordinateDistanceSq(coordinate, pointCoordinate);
		if (distanceSq > matchedDistanceSq) return;

		const nodeId = getFeatureId(feature);
		if (isBlankValue(nodeId)) return;

		matchedNodeId = String(nodeId).trim();
		matchedDistanceSq = distanceSq;
	});

	return matchedNodeId;
}

function setLineEndpointCoordinate(feature, endpointType, coordinate) {
	const geometry = feature?.getGeometry?.();
	if (geometry?.getType?.() !== 'LineString' || !Array.isArray(coordinate)) return false;

	const coordinates = geometry.getCoordinates();
	if (!Array.isArray(coordinates) || coordinates.length < 2) return false;

	const nextCoordinates = coordinates.map(item => [...item]);
	if (endpointType === 'start') {
		nextCoordinates[0] = [...coordinate];
	} else {
		nextCoordinates[nextCoordinates.length - 1] = [...coordinate];
	}

	geometry.setCoordinates(nextCoordinates);
	feature.changed();
	return true;
}

function moveNodeFeatureToCoordinate(feature, coordinate) {
	const geometry = feature?.getGeometry?.();
	if (geometry?.getType?.() !== 'Point' || !Array.isArray(coordinate)) return false;

	geometry.setCoordinates([...coordinate]);
	feature.changed();
	return true;
}

function resolveLinkEndpointNode(map, feature, endpointType, coordinate) {
	const currentNodeId = endpointType === 'start' ? feature?.get?.('startNode') : feature?.get?.('endNode');
	const snappedNodeFeature = findNodeFeatureAtCoordinate(map, coordinate);

	if (snappedNodeFeature) {
		return {
			nodeId: getFeatureId(snappedNodeFeature),
			nodeFeature: snappedNodeFeature,
			didMoveNode: false,
		};
	}

	const currentNodeFeature = findNodeFeatureById(map, currentNodeId);
	if (currentNodeFeature) {
		moveNodeFeatureToCoordinate(currentNodeFeature, coordinate);
		return {
			nodeId: currentNodeId,
			nodeFeature: currentNodeFeature,
			didMoveNode: true,
		};
	}

	return {
		nodeId: '',
		nodeFeature: null,
		didMoveNode: false,
	};
}

function syncLinkEndpointNodes(map, feature) {
	const endCoordinates = getLineEndCoordinates(feature);
	if (!endCoordinates) return;

	const startNodeResult = resolveLinkEndpointNode(map, feature, 'start', endCoordinates.startCoordinate);
	const endNodeResult = resolveLinkEndpointNode(map, feature, 'end', endCoordinates.endCoordinate);

	feature.setProperties({
		startNode: startNodeResult.nodeId,
		endNode: endNodeResult.nodeId,
	});
	feature.changed();

	[startNodeResult, endNodeResult].forEach(result => {
		if (!result.didMoveNode || !result.nodeFeature) return;
		syncLinksConnectedToNode(map, result.nodeFeature);
	});
}

function syncLinksConnectedToNode(map, nodeFeature) {
	const nodeId = getFeatureId(nodeFeature);
	const nodeCoordinate = getPointCoordinate(nodeFeature);
	if (isBlankValue(nodeId) || !nodeCoordinate) return [];

	const changedLinkFeatures = [];

	getLinkFeatures(map).forEach(linkFeature => {
		let isChanged = false;

		if (isSameFeatureId(linkFeature.get?.('startNode'), nodeId)) {
			isChanged = setLineEndpointCoordinate(linkFeature, 'start', nodeCoordinate) || isChanged;
		}

		if (isSameFeatureId(linkFeature.get?.('endNode'), nodeId)) {
			isChanged = setLineEndpointCoordinate(linkFeature, 'end', nodeCoordinate) || isChanged;
		}

		if (isChanged) {
			changedLinkFeatures.push(linkFeature);
		}
	});

	return changedLinkFeatures;
}

function applyLinkEndpointNodeIds(map, feature) {
	syncLinkEndpointNodes(map, feature);
}

function getSnapFeaturesForSelectedFeatures(map, selectedFeatures) {
	const selectedNodeIdSeq = selectedFeatures
		.filter(feature => NODE_LAYER_NAMES.includes(getFeatureLayerName(map, feature)))
		.map(feature => getFeatureId(feature))
		.filter(value => !isBlankValue(value));
	const hasSelectedLinkFeature = selectedFeatures.some(feature => LINK_LAYER_NAMES.includes(getFeatureLayerName(map, feature)));
	const snapFeatureSeq = [];

	if (hasSelectedLinkFeature) {
		snapFeatureSeq.push(...getNodeFeatures(map));
	}

	if (selectedNodeIdSeq.length > 0) {
		snapFeatureSeq.push(
			...getLinkFeatures(map).filter(feature => {
				return !selectedNodeIdSeq.some(
					nodeId =>
						isSameFeatureId(feature.get?.('startNode'), nodeId) || isSameFeatureId(feature.get?.('endNode'), nodeId)
				);
			})
		);
	}

	return snapFeatureSeq;
}

const MODEL_FEATURE_DRAW_ID_REQUIRED_LAYER_NAMES = [...NODE_LAYER_NAMES, ...LINK_LAYER_NAMES];

function findFirstMissingFeatureIdInfo(map, layerNames = MODEL_FEATURE_DRAW_ID_REQUIRED_LAYER_NAMES) {
	if (!map) return null;

	for (const layerName of layerNames) {
		const layer = olUtils.getLayerByName(map, layerName);
		const features = layer?.getSource?.()?.getFeatures?.() ?? [];
		const featureIndex = features.findIndex(feature => isBlankValue(getFeatureId(feature)));

		if (featureIndex < 0) continue;

		const feature = features[featureIndex];
		return {
			layerName,
			feature,
			featureName: formatFeatureValidationName(feature, layerName, featureIndex),
		};
	}

	return null;
}

function buildModelFeatureValidationResult(map) {
	if (!map) {
		return {
			isValid: false,
			message: '지도 정보를 찾을 수 없어 모델을 저장할 수 없습니다.',
		};
	}

	const issueSeq = [];

	LAYER_ORDER.forEach(layerName => {
		const layer = olUtils.getLayerByName(map, layerName);
		const features = layer?.getSource?.()?.getFeatures?.() ?? [];
		const featureIdOwnerMap = new Map();

		features.forEach((feature, index) => {
			const objectType = getFeatureObjectType(feature, layerName);
			const requiredKeySeq = REQUIRED_PROPERTY_KEY_SEQ_BY_OBJECT_TYPE[objectType] ?? [];
			const featureName = formatFeatureValidationName(feature, layerName, index);

			requiredKeySeq.forEach(key => {
				const value = getFeatureValidationValue(feature, key);
				if (!isBlankValue(value)) return;

				issueSeq.push(`${featureName}: ${OBJECT_PROPERTY_LABEL_BY_KEY[key] ?? key}은(는) 필수입니다.`);
			});

			const featureId = getFeatureValidationValue(feature, 'featureId');
			if (isBlankValue(featureId)) return;

			const normalizedId = String(featureId).trim();
			const duplicateOwner = featureIdOwnerMap.get(normalizedId);
			if (duplicateOwner) {
				issueSeq.push(
					`${duplicateOwner} / ${featureName}: 같은 레이어 안에서 아이디 "${normalizedId}"이(가) 중복됩니다.`
				);
				return;
			}

			featureIdOwnerMap.set(normalizedId, featureName);
		});
	});

	if (issueSeq.length === 0) {
		return {
			isValid: true,
			message: '',
		};
	}

	const previewIssueSeq = issueSeq.slice(0, 5);
	const remainingCount = issueSeq.length - previewIssueSeq.length;
	return {
		isValid: false,
		message: [
			'모델 저장 전 입력값을 확인해주세요.',
			...previewIssueSeq,
			...(remainingCount > 0 ? [`외 ${remainingCount}건`] : []),
		].join('\n'),
	};
}

function SidebarPanel({
	networkDetail,
	mapLayerVersion,
	layerType,
	onLayerTypeChange,
	selectedFeature,
	onSelectFeature,
	revisionRowSeq = [],
	onRevisionSave,
	onRevisionDownload,
	isRevisionSaving = false,
}) {
	return (
		<CommonCard className="flex h-full min-h-0 flex-col overflow-hidden rounded-[18px] bg-[linear-gradient(180deg,rgba(19,35,67,0.96),rgba(14,29,57,0.98))]">
			<div className="grid min-h-0 flex-1 grid-rows-[minmax(0,1fr)_minmax(0,0.92fr)] gap-3 p-1.5">
				<div className="min-h-0 overflow-hidden">
					<LayerFeatureTablePanel
						networkDetail={networkDetail}
						mapLayerVersion={mapLayerVersion}
						layerType={layerType}
						onLayerTypeChange={onLayerTypeChange}
						selectedFeature={selectedFeature}
						onSelectFeature={onSelectFeature}
					/>
				</div>
				<RevisionListPanel
					revisionRowSeq={revisionRowSeq}
					onRevisionSave={onRevisionSave}
					onRevisionDownload={onRevisionDownload}
					isRevisionSaving={isRevisionSaving}
				/>
			</div>
		</CommonCard>
	);
}

function TopToolbar({
	modelName,
	setModelName,
	onActionClick,
	hasSelectedModelFile,
	isSavingModel,
	isApplyingModel,
	isOptimizationExecuting,
}) {
	return (
		<div className="flex shrink-0 items-center justify-between gap-2 border-b border-slate-700/60 bg-slate-950/15 px-3 py-1.5">
			<div className="flex-1" />
			<div className="flex flex-wrap items-center justify-end gap-1.5">
				<CommonInput
					label="모델명"
					value={modelName}
					onChange={setModelName}
					className="model-editor-toolbar-input w-[180px]"
					disabled={!hasSelectedModelFile}
				/>
				{MODEL_EDITOR_ACTION_BUTTON_SEQ.filter(action => !action.requiresModelFile || hasSelectedModelFile).map(
					action => (
						<CommonButton
							key={action.key}
							text={action.label}
							variant={action.variant === 'run' ? 'default' : action.variant}
							{...MODEL_EDITOR_BUTTON_PROPS}
							className={
								action.variant === 'run'
									? 'h-8 bg-[linear-gradient(180deg,#25b38f,#159b78)] px-3 text-[11px] text-white hover:bg-[linear-gradient(180deg,#37c6a1,#21ac88)]'
									: action.className
										? action.className
										: 'h-8 px-3 text-[11px]'
							}
							size="sm"
							Icon={action.key === 'optimizationExecution' ? IoPlayOutline : undefined}
							iconClassName="h-3.5 w-3.5"
							isLoading={
								(action.key === 'save' && isSavingModel) ||
								(action.key === 'apply' && isApplyingModel) ||
								(action.key === 'optimizationExecution' && isOptimizationExecuting)
							}
							preventDoubleClick={
								action.key === 'save' || action.key === 'apply' || action.key === 'optimizationExecution'
							}
							disabled={
								(action.key === 'save' && isSavingModel) ||
								(action.key === 'apply' && isApplyingModel) ||
								(action.key === 'optimizationExecution' && isOptimizationExecuting)
							}
							onClick={() => onActionClick?.(action.key)}
						/>
					)
				)}
			</div>
		</div>
	);
}

function OptimizationManagerDialog({ open, setOpen, selectedModelFile }) {
	const inpFileId = selectedModelFile?.inpFileId;
	const [optimizationListPayload, setOptimizationListPayload] = useState(null);
	const [historyRows, setHistoryRows] = useState([]);
	const [runningRows, setRunningRows] = useState([]);
	const [selectedHistId, setSelectedHistId] = useState(null);
	const [histDetail, setHistDetail] = useState(null);
	const [isLoadingList, setIsLoadingList] = useState(false);
	const [isLoadingDetail, setIsLoadingDetail] = useState(false);
	const selectedHistoryRow = useMemo(
		() => historyRows.find(row => String(row.histId) === String(selectedHistId)) ?? null,
		[historyRows, selectedHistId]
	);
	const settingRows = useMemo(() => normalizeOptimizationSettingRows(histDetail), [histDetail]);
	const detailRows = useMemo(() => normalizeOptimizationDetailRows(histDetail), [histDetail]);

	const loadOptimizationList = useCallback(async () => {
		if (!inpFileId) {
			setOptimizationListPayload(null);
			setHistoryRows([]);
			setRunningRows([]);
			setSelectedHistId(null);
			setHistDetail(null);
			return;
		}

		setIsLoadingList(true);
		try {
			const [completedResponse, runningResponse] = await Promise.all([
				inpApi.getOptimizationList(inpFileId, {
					skipErrorToast: true,
					showSpinner: false,
					searchParams: {
						statusCd: 'COMPLETED',
					},
				}),
				inpApi.getOptimizationList(inpFileId, {
					skipErrorToast: true,
					showSpinner: false,
					searchParams: {
						statusCd: 'RUNNING',
					},
				}),
			]);
			setOptimizationListPayload(extractOptimizationPayload(completedResponse));
			const nextRows = normalizeOptimizationHistoryRows(completedResponse);
			setHistoryRows(nextRows);
			setRunningRows(normalizeOptimizationRunningRows(runningResponse));
			setSelectedHistId(prev => (nextRows.some(row => String(row.histId) === String(prev)) ? prev : nextRows[0]?.histId));
		} catch (error) {
			console.error('Failed to load optimization history.', error);
			showToast('error', '최적화 이력 조회에 실패했습니다.');
			setOptimizationListPayload(null);
			setHistoryRows([]);
			setRunningRows([]);
			setSelectedHistId(null);
			setHistDetail(null);
		} finally {
			setIsLoadingList(false);
		}
	}, [inpFileId]);

	useEffect(() => {
		if (!open) return;

		const timerId = window.setTimeout(() => {
			loadOptimizationList();
		}, 0);

		return () => {
			window.clearTimeout(timerId);
		};
	}, [loadOptimizationList, open]);

	const loadOptimizationRunningRows = useCallback(
		async ({ showErrorToast = true } = {}) => {
			if (!inpFileId) {
				return;
			}

			try {
				const response = await fetchJson(
					buildApiUrl('/opt', {
						inpFileId,
						statusCd: 'RUNNING',
					})
				);
				setRunningRows(normalizeOptimizationRunningRows(response));
			} catch (error) {
				console.error('Failed to load running optimization history.', error);
				if (showErrorToast) {
					showToast('error', '최적화 실행 로그 조회에 실패했습니다.');
				}
				setRunningRows([]);
			}
		},
		[inpFileId]
	);

	const loadOptimizationDetail = useCallback(
		async ({ showErrorToast = true, showLoading = true } = {}) => {
			if (!selectedHistId) {
				setHistDetail(null);
				return;
			}

			if (showLoading) {
				setIsLoadingDetail(true);
			}

			try {
				const response = await inpApi.getOptHist(selectedHistId, {
					skipErrorToast: true,
					showSpinner: false,
				});
				setHistDetail(extractOptimizationPayload(response));
			} catch (error) {
				console.error('Failed to load optimization detail.', error);
				if (showErrorToast) {
					showToast('error', '최적화 상세 조회에 실패했습니다.');
				}
				setHistDetail(null);
			} finally {
				if (showLoading) {
					setIsLoadingDetail(false);
				}
			}
		},
		[selectedHistId]
	);

	useEffect(() => {
		if (!open) return;
		if (!selectedHistId) return;

		const timeoutId = window.setTimeout(() => {
			loadOptimizationDetail();
		}, 0);

		return () => {
			window.clearTimeout(timeoutId);
		};
	}, [loadOptimizationDetail, open, selectedHistId]);

	useEffect(() => {
		if (!open) return;
		if (!inpFileId) return;

		const intervalId = window.setInterval(() => {
			loadOptimizationRunningRows({ showErrorToast: false });
		}, 10000);

		return () => {
			window.clearInterval(intervalId);
		};
	}, [inpFileId, loadOptimizationRunningRows, open]);

	return (
		<CommonModal
			open={open}
			onOpenChange={setOpen}
			title="최적화 이력"
			preset="editor"
			actionLabel={null}
			showCancel={false}
			showFooter={false}
			closeOnBackdrop={true}
			contentClassName="w-[min(98vw,1280px)]"
			panelSx={{
				maxWidth: '1280px',
			}}
		>
			<div className="flex h-[min(82vh,760px)] min-h-[560px] flex-col gap-3 overflow-hidden">
				<div className="grid min-h-0 flex-1 grid-cols-[285px_minmax(0,1fr)] gap-3">
					<CommonCard className="flex min-h-0 flex-col overflow-hidden rounded-[14px] border border-[rgba(110,185,255,0.18)] bg-[rgba(8,20,44,0.56)] p-3">
						<div className="mb-2 flex items-center justify-between gap-2">
							<div>
								<h3 className="text-[15px] font-semibold text-sky-50">최적화 이력</h3>
								<p className="mt-1 text-[11px] text-sky-100/55">
									{selectedModelFile?.orgnlFileNm ?? '선택된 모델 없음'}
								</p>
							</div>
							<CommonButton
								size="icon-xs"
								variant="ghost"
								Icon={IoRefreshOutline}
								iconClassName="h-3.5 w-3.5"
								className="border border-sky-200/20 bg-white/5 text-sky-50 hover:bg-white/10"
								isLoading={isLoadingList}
								preventDoubleClick={true}
								onClick={loadOptimizationList}
							/>
						</div>
						<div className="min-h-0 flex-1 overflow-hidden rounded-[10px] border border-[rgba(110,185,255,0.12)]">
							<CommonTable
								colSeq={optimizationHistoryColSeq}
								rowSeq={historyRows}
								getRowKey={row => row.id}
								emptyMsg="최적화 이력이 없습니다."
								loading={isLoadingList}
								enableSorting={true}
								enableColumnResize={true}
								selectedRowKey={selectedHistoryRow?.id ?? null}
								onRowClick={row => setSelectedHistId(row.histId)}
								rowHeight={46}
								rowClassName={(row, rowKey, isSel) =>
									isSel ? 'bg-sky-500/18 hover:bg-sky-500/22' : 'hover:bg-sky-500/10'
								}
							/>
						</div>
					</CommonCard>

					<div className="grid min-h-0 grid-rows-[minmax(0,0.78fr)_minmax(0,1.22fr)] gap-3 overflow-hidden">
						<CommonCard className="flex min-h-0 flex-col overflow-hidden rounded-[14px] border border-[rgba(110,185,255,0.18)] bg-[rgba(8,20,44,0.56)] p-3">
							<div className="mb-2 flex items-center justify-between">
								<h3 className="text-[15px] font-semibold text-sky-50">설정정보</h3>
								<span className="text-[11px] text-sky-100/55">
									{selectedHistoryRow?.statusLabel ? `상태 ${selectedHistoryRow.statusLabel}` : ''}
								</span>
							</div>
							<div className="min-h-0 flex-1 overflow-hidden rounded-[10px] border border-[rgba(110,185,255,0.12)]">
								<CommonTable
									colSeq={optimizationSettingColSeq}
									rowSeq={settingRows}
									getRowKey={row => row.id}
									emptyMsg="설정정보가 없습니다."
									loading={isLoadingDetail}
									enableColumnResize={true}
									rowHeight={38}
								/>
							</div>
						</CommonCard>

						<CommonCard className="flex min-h-0 flex-col overflow-hidden rounded-[14px] border border-[rgba(110,185,255,0.18)] bg-[rgba(8,20,44,0.56)] p-3">
							<div className="mb-2 flex items-center justify-between">
								<h3 className="text-[15px] font-semibold text-sky-50">최적화 결과</h3>
							</div>
							<div className="min-h-0 flex-1 overflow-hidden rounded-[10px] border border-[rgba(110,185,255,0.12)]">
								<CommonTable
									colSeq={optimizationDetailColSeq}
									rowSeq={detailRows}
									getRowKey={row => row.id}
									emptyMsg="상세 설정정보가 없습니다."
									loading={isLoadingDetail}
									enableColumnResize={true}
									rowHeight={38}
								/>
							</div>
						</CommonCard>
					</div>
				</div>

				<CommonCard className="h-[152px] shrink-0 overflow-hidden rounded-[14px] border border-[rgba(110,185,255,0.18)] bg-[rgba(8,20,44,0.56)] p-3">
					<div className="h-full overflow-hidden rounded-[10px] border border-[rgba(110,185,255,0.12)]">
						<CommonTable
							colSeq={optimizationRunLogColSeq}
							rowSeq={runningRows}
							getRowKey={row => row.id}
							emptyMsg="실행 로그가 없습니다."
							loading={isLoadingList}
							enableColumnResize={true}
							rowHeight={34}
							columnHeaderHeight={32}
							sx={{
								'& .MuiDataGrid-virtualScroller': {
									overflowY: 'auto !important',
								},
							}}
						/>
					</div>
				</CommonCard>
			</div>
		</CommonModal>
	);
}
function MapArea({
	selectedModel,
	setSelectedModel,
	isEditMode,
	setIsEditMode,
	onLayerChanged,
	onClearSelectedFeature,
	onFeatureAdded,
	onFeatureChanged,
}) {
	const clearEditInteractions = () => {
		const map = getMap(MODEL_EDITOR_MAP_ID);
		olUtils.removeDrawInteractions(map);
		olUtils.removeModifyInteraction(map);
		olUtils.removeSnapInteraction(map);
	};

	const handleModelTypeChange = nextModel => {
		setSelectedModel(nextModel);
		clearEditInteractions();
	};

	const handleEditModeClick = () => {
		setIsEditMode(prev => {
			const next = !prev;
			if (!next) {
				clearEditInteractions();
			}
			return next;
		});
	};

	const handleEditActionClick = actionKey => {
		const map = getMap(MODEL_EDITOR_MAP_ID);
		if (!map) return;

		if (actionKey === 'select') {
			olUtils.removeDrawInteractions(map);
			const select = map.get('__featureSelectInteraction');
			if (!select) return;
			const selectedFeatures = select.getFeatures?.()?.getArray?.() ?? [];
			const snapFeatures = getSnapFeaturesForSelectedFeatures(map, selectedFeatures);

			olUtils.setModify(map, select.getFeatures(), ({ features }) => {
				features.forEach(feature => {
					const layerName = getFeatureLayerName(map, feature);
					if (LINK_LAYER_NAMES.includes(layerName)) {
						syncLinkEndpointNodes(map, feature);
						onFeatureChanged?.(layerName, feature);
						return;
					}

					if (NODE_LAYER_NAMES.includes(layerName)) {
						syncLinksConnectedToNode(map, feature);
						onFeatureChanged?.(layerName, feature);
					}
				});
				onLayerChanged?.();
			});
			if (snapFeatures.length > 0) {
				olUtils.setSnap(map, snapFeatures);
			}
			return;
		}

		if (actionKey === 'add') {
			const shouldRequireFeatureId = MODEL_FEATURE_DRAW_ID_REQUIRED_LAYER_NAMES.includes(selectedModel);
			if (shouldRequireFeatureId) {
				const missingFeatureInfo = findFirstMissingFeatureIdInfo(map);
				if (missingFeatureInfo) {
					olUtils.removeDrawInteractions(map);
					showToast('error', `${missingFeatureInfo.featureName}의 아이디를 먼저 입력해주세요.`);
					onFeatureAdded?.(missingFeatureInfo.layerName, missingFeatureInfo.feature);
					onLayerChanged?.();
					return;
				}
			}

			olUtils.removeModifyInteraction(map);
			olUtils.setDraw(
				map,
				selectedModel,
				event => {
					const layerName = LAYER_ORDER.includes(selectedModel) ? selectedModel : null;

					if (layerName) {
						const isLinkLayer = LINK_LAYER_NAMES.includes(layerName);
						const isIdRequiredLayer = MODEL_FEATURE_DRAW_ID_REQUIRED_LAYER_NAMES.includes(layerName);
						if (isLinkLayer) {
							applyLinkEndpointNodeIds(map, event.feature);
						}

						event.feature.setProperties({
							id: event.feature.get('id') ?? '',
							layer: layerName,
							objectType: OBJ_TYPE_LAYER_NAME[layerName],
							...(isLinkLayer
								? {
										startNode: event.feature.get('startNode') ?? '',
										endNode: event.feature.get('endNode') ?? '',
									}
								: {}),
							...(layerName === 'LABELS' ? { text: '라벨' } : {}),
						});

						if (isIdRequiredLayer && isBlankValue(getFeatureId(event.feature))) {
							olUtils.removeDrawInteractions(map);
							showToast('error', '아이디를 입력해야 다음 객체를 추가할 수 있습니다.');
						}
					}

					requestAnimationFrame(() => {
						if (layerName) {
							onFeatureAdded?.(layerName, event.feature);
						}
						onLayerChanged?.();
					});
				},
				{ createLayerIfMissing: true }
			);

			if (LINK_LAYER_NAMES.includes(selectedModel)) {
				olUtils.setSnap(map, getNodeFeatures(map));
			} else if (NODE_LAYER_NAMES.includes(selectedModel)) {
				olUtils.setSnap(map, getLinkFeatures(map));
			}

			return;
		}

		if (actionKey === 'delete') {
			olUtils.removeDrawInteractions(map);
			olUtils.removeModifyInteraction(map);
			const select = map.get('__featureSelectInteraction');
			if (!select) return;

			const removed = olUtils.removeSelectedFeatures(map, select, {
				layerNames: LAYER_ORDER,
			});

			if (removed.length > 0) {
				olUtils.highlightFeatureEvent(null, map);
				onClearSelectedFeature?.();
				onLayerChanged?.();
			}
		}
	};

	return (
		<CommonCard className="relative h-full min-h-0 overflow-hidden rounded-[18px] bg-[linear-gradient(180deg,rgba(16,34,63,0.98),rgba(11,23,44,0.99))] p-0">
			<div className="absolute left-14 top-3 z-30 flex items-center gap-2">
				<div className="w-[96px] shrink-0">
					<CommonSelect
						value={selectedModel}
						onChange={handleModelTypeChange}
						options={MODEL_TYPE_OPTION_SEQ}
						optionLabelKey="k"
						optionValueKey="v"
						className="model-editor-select w-full"
						menuProps={MODEL_EDITOR_SELECT_MENU_PROPS}
					/>
				</div>
				<CommonButton
					text={isEditMode ? '편집종료' : '편집하기'}
					variant="outline"
					{...MODEL_EDITOR_BUTTON_PROPS}
					className="h-[34px] min-w-[74px] shrink-0 whitespace-nowrap px-3 text-[11px]"
					onClick={handleEditModeClick}
				/>
				{isEditMode ? (
					<div className="flex h-[34px] shrink-0 overflow-hidden rounded-[4px] border border-[#c7d2df] bg-[linear-gradient(180deg,#f8f9fb,#eef2f6)] shadow-[0_2px_8px_rgba(15,23,42,0.18)]">
						{MODEL_EDITOR_EDIT_ACTION_BUTTON_SEQ.map((item, index) => (
							<CommonButton
								key={item.key}
								onClick={() => handleEditActionClick(item.key)}
								{...MODEL_EDITOR_BUTTON_PROPS}
								className={[
									'h-[34px] w-9 rounded-none border-0 bg-transparent px-0 text-[#7d8da5] shadow-none transition hover:bg-[#ffffff] hover:text-[#365d90]',
									index > 0 ? 'border-l border-[#d8dde6]' : '',
								].join(' ')}
							>
								<img src={item.src} alt={item.alt} className="h-4 w-4 object-contain" />
							</CommonButton>
						))}
					</div>
				) : null}
			</div>
			<MapCanvas
				mapId={MODEL_EDITOR_MAP_ID}
				className="absolute inset-0"
				centerProjection="EPSG:4326"
				projectionCode="EPSG:3857"
				zoom={12}
				fullScreen={true}
			/>
		</CommonCard>
	);
}

function ModelEditorPageTemp() {
	const [sideBarOpen, setSideBarOpen] = useState(false);
	const [isModelSelectDialogOpen, setIsModelSelectDialogOpen] = useState(false); // 모델 선택 다이얼로그 오픈 여부
	const [isSettingValueDialogOpen, setIsSettingValueDialogOpen] = useState(false); // 설정값 불러오기 다이얼로그 오픈 여부
	const [isComparisonTargetDialogOpen, setIsComparisonTargetDialogOpen] = useState(false); // 비교대상 설정 다이얼로그 오픈 여부
	const [isOptimizationManagerOpen, setIsOptimizationManagerOpen] = useState(false); // 최적화 매니저 다이얼로그 오픈 여부
	const [modelName, setModelName] = useState('');
	const [selectedModelFile, setSelectedModelFile] = useState(null);
	const [networkDetail, setNetworkDetail] = useState(null);
	const [selectedModel, setSelectedModel] = useState(MODEL_TYPE_OPTION_SEQ[1].v);
	const [modelTableLayerType, setModelTableLayerType] = useState(LAYER_OPTION_SEQ[0].value);
	const [selectedFeature, setSelectedFeature] = useState(null);
	const [isEditMode, setIsEditMode] = useState(false);
	const [mapWorkspaceEl, setMapWorkspaceEl] = useState(null);
	const [mapLayerVersion, setMapLayerVersion] = useState(0);
	const [revisionRowSeq, setRevisionRowSeq] = useState([]);
	const [currentRevNo, setCurrentRevNo] = useState(null);
	const [isRevisionSaving, setIsRevisionSaving] = useState(false);
	const [isSavingModel, setIsSavingModel] = useState(false);
	const [isApplyingModel, setIsApplyingModel] = useState(false);
	const [isOptimizationExecuting, setIsOptimizationExecuting] = useState(false);
	useEffect(() => {
		let isMounted = true;

		const waitForMapInstance = isCancelled =>
			new Promise(resolve => {
				const tryResolve = () => {
					if (isCancelled()) return resolve(null);
					const map = getMap(MODEL_EDITOR_MAP_ID);
					if (map) {
						resolve(map);
						return;
					}
					window.requestAnimationFrame(tryResolve);
				};

				tryResolve();
			});

		(async () => {
			const map = await waitForMapInstance(() => !isMounted);
			if (!isMounted || !map) return;
		})();

		return () => {
			isMounted = false;
		};
	}, []);

	const loadRevisionRows = useCallback(
		async (inpFileId, nextCurrentRevNo = currentRevNo) => {
			if (!inpFileId) {
				setRevisionRowSeq([]);
				return [];
			}

			const revisionResponse = await inpApi.getInpFileRevisions(inpFileId);
			const nextRevisionRowSeq = buildRevisionRowSeq(revisionResponse, inpFileId, nextCurrentRevNo);
			setRevisionRowSeq(nextRevisionRowSeq);
			return nextRevisionRowSeq;
		},
		[currentRevNo]
	);

	const handleSaveModelFile = async () => {
		if (!selectedModelFile?.inpFileId || StzUtils.isEmpty(networkDetail)) {
			showToast('error', '저장할 모델을 먼저 선택해주세요.');
			return;
		}

		const originalFileName = normalizeInpFileName(selectedModelFile.orgnlFileNm);
		const currentFileName = normalizeInpFileName(modelName || originalFileName);

		if (!currentFileName) {
			showToast('error', '파일명을 입력해주세요.');
			return;
		}

		const isSaveAs = originalFileName !== currentFileName;
		const saveAsFileName = isSaveAs ? await requestSaveAsFileName(currentFileName) : null;
		if (isSaveAs && !saveAsFileName) return;

		const validationResult = buildModelFeatureValidationResult(getMap(MODEL_EDITOR_MAP_ID));
		if (!validationResult.isValid) {
			showToast('error', validationResult.message);
			return;
		}

		const savePayload = buildNetworkSavePayload(networkDetail);

		setIsSavingModel(true);
		try {
			const response = isSaveAs
				? await inpApi.saveNewInpFile(
						{
							...savePayload,
							fileName: saveAsFileName,
						},
						{ skipErrorToast: true }
					)
				: await inpApi.saveInpFile(selectedModelFile.inpFileId, savePayload, { skipErrorToast: true });
			const nextModelFile = response?.data;
			const nextInpFileId = nextModelFile?.inpFileId ?? selectedModelFile.inpFileId;
			const nextCurrentRevNo = getCurrentRevNo(nextModelFile) ?? currentRevNo;

			if (nextModelFile) {
				setSelectedModelFile(prev => ({
					...(prev ?? {}),
					...nextModelFile,
					currentRevNo: nextCurrentRevNo,
					currRevNo: nextCurrentRevNo,
				}));
				setModelName(nextModelFile.orgnlFileNm ?? saveAsFileName ?? currentFileName);
			} else if (isSaveAs) {
				setSelectedModelFile(prev => ({
					...(prev ?? {}),
					inpFileId: nextInpFileId,
					orgnlFileNm: saveAsFileName,
					currentRevNo: nextCurrentRevNo,
					currRevNo: nextCurrentRevNo,
				}));
				setModelName(saveAsFileName);
			}

			setCurrentRevNo(nextCurrentRevNo);
			setNetworkDetail(savePayload);
			await loadRevisionRows(nextInpFileId, nextCurrentRevNo);
			showToast('info', isSaveAs ? '새 파일로 저장했습니다.' : '모델을 저장했습니다.');
		} catch (error) {
			console.error('Failed to save INP network.', error);
			const errorCode = await resolveApiErrorCode(error);
			showToast('error', resolveApiErrorMessage(errorCode, '모델 저장에 실패했습니다.'));
		} finally {
			setIsSavingModel(false);
		}
	};

	const handleOptimizationExecution = async () => {
		const inpFileId = selectedModelFile?.inpFileId;
		if (!inpFileId) {
			showToast('error', '최적화를 실행할 모델을 먼저 선택해주세요.');
			return;
		}

		setIsOptimizationExecuting(true);
		try {
			await inpApi.getOptimizationExecution(inpFileId, { skipErrorToast: true });
			showToast('info', '최적화를 실행했습니다.');
		} catch (error) {
			console.error('Failed to execute optimization.', error);
			showToast('error', '최적화 실행에 실패했습니다.');
		} finally {
			setIsOptimizationExecuting(false);
		}
	};

	const handleApplyModelFile = async () => {
		const inpFileId = selectedModelFile?.inpFileId;
		if (!inpFileId) {
			showToast('error', '적용할 모델을 먼저 선택해주세요.');
			return;
		}

		setIsApplyingModel(true);
		try {
			await inpApi.applyInpFile(inpFileId, { skipErrorToast: true });
			showToast('info', '모델을 적용했습니다.');
		} catch (error) {
			console.error('Failed to apply INP file.', error);
			const errorCode = await resolveApiErrorCode(error);
			showToast('error', resolveApiErrorMessage(errorCode, '모델 적용에 실패했습니다.'));
		} finally {
			setIsApplyingModel(false);
		}
	};

	const handleToolbarActionClick = actionKey => {
		if (actionKey === 'modelSelect') {
			setIsModelSelectDialogOpen(true);
			return;
		}

		if (actionKey === 'save') {
			handleSaveModelFile();
			return;
		}

		if (actionKey === 'apply') {
			handleApplyModelFile();
			return;
		}

		if (actionKey === 'settingValue') {
			setIsSettingValueDialogOpen(true);
			return;
		}

		if (actionKey === 'comparisonTarget') {
			setIsComparisonTargetDialogOpen(true);
			return;
		}

		if (actionKey === 'optimizationExecution') {
			handleOptimizationExecution();
			return;
		}

		if (actionKey === 'optimizationManager') {
			setIsOptimizationManagerOpen(true);
		}
	};

	const handleModelSelectApply = async (file, detail) => {
		const nextCurrentRevNo = getCurrentRevNo(file);

		olUtils.highlightFeatureEvent(null, getMap(MODEL_EDITOR_MAP_ID));
		setSelectedModelFile(file);
		setCurrentRevNo(nextCurrentRevNo);
		setNetworkDetail(detail);
		setMapLayerVersion(prev => prev + 1);
		setSelectedFeature(null);
		setSideBarOpen(false);
		if (file?.orgnlFileNm) {
			setModelName(file.orgnlFileNm);
		}

		if (!file?.inpFileId) {
			setRevisionRowSeq([]);
			setCurrentRevNo(null);
			return;
		}

		try {
			await loadRevisionRows(file.inpFileId, nextCurrentRevNo);
		} catch (error) {
			console.error('Failed to load INP file revisions.', error);
			setRevisionRowSeq([]);
		}
	};

	const handleRevisionSave = async revisionRow => {
		const inpFileId = selectedModelFile?.inpFileId;
		const revNo = revisionRow?.revNo;

		if (!inpFileId || revNo === null || revNo === undefined) return;

		setIsRevisionSaving(true);
		try {
			const rollbackResponse = await inpApi.rollbackInpFileRevision(inpFileId, revNo, { skipErrorToast: true });
			const nextModelFile = rollbackResponse?.data;
			const nextCurrentRevNo = getCurrentRevNo(nextModelFile) ?? revNo;
			setCurrentRevNo(nextCurrentRevNo);
			if (nextModelFile) {
				setSelectedModelFile(prev => ({
					...(prev ?? {}),
					...nextModelFile,
					currentRevNo: nextCurrentRevNo,
					currRevNo: nextCurrentRevNo,
				}));
				if (nextModelFile.orgnlFileNm) {
					setModelName(nextModelFile.orgnlFileNm);
				}
			} else {
				setSelectedModelFile(prev => ({
					...(prev ?? {}),
					currentRevNo: nextCurrentRevNo,
					currRevNo: nextCurrentRevNo,
				}));
			}

			const { data: nextDetail } = await inpApi.getInpFileDetail(inpFileId, { skipErrorToast: true });
			if (!StzUtils.isEmpty(nextDetail)) {
				applyModelNetworkLayers(nextDetail);
				setNetworkDetail(nextDetail);
			}

			await loadRevisionRows(inpFileId, nextCurrentRevNo);
			olUtils.highlightFeatureEvent(null, getMap(MODEL_EDITOR_MAP_ID));
			setSelectedFeature(null);
			setSideBarOpen(false);
			setMapLayerVersion(prev => prev + 1);
			showToast('info', '선택한 리비전을 현재 버전으로 적용했습니다.');
		} catch (error) {
			console.error('Failed to rollback INP file revision.', error);
			showToast('error', '리비전 적용에 실패했습니다.');
		} finally {
			setIsRevisionSaving(false);
		}
	};

	const handleRevisionDownload = async revisionRow => {
		const inpFileId = selectedModelFile?.inpFileId;
		const revNo = revisionRow?.revNo;

		if (!inpFileId || revNo === null || revNo === undefined) return;

		try {
			const response = await inpApi.downloadSpecInpRevision(inpFileId, revNo, { skipErrorToast: true });
			await saveDownloadResponse(response, revisionRow?.downloadFileNm ?? `revision-${revNo}.inp`);
		} catch (error) {
			console.error('Failed to download INP file revision.', error);
			showToast('error', '리비전 파일 다운로드에 실패했습니다.');
		}
	};

	const handleFeatureSelect = row => {
		if (!row) {
			olUtils.highlightFeatureEvent(null, getMap(MODEL_EDITOR_MAP_ID));
			setSelectedFeature(null);
			setSideBarOpen(false);
			return;
		}

		const isSameRow = selectedFeature?.rowKey === row?.rowKey;
		if (isSameRow) {
			olUtils.highlightFeatureEvent(null, getMap(MODEL_EDITOR_MAP_ID));
			setSelectedFeature(null);
			setSideBarOpen(false);
			return;
		}

		if (row?._isNonVisualSection) {
			olUtils.highlightFeatureEvent(null, getMap(MODEL_EDITOR_MAP_ID));
			setSelectedFeature(row);
			setSideBarOpen(true);
			return;
		}

		olUtils.highlightFeatureEvent(row._featureId ?? row.featureId ?? row.id, getMap(MODEL_EDITOR_MAP_ID), {
			layerName: row._layerName,
			zoom: 17,
		});
		setSelectedFeature(row);
		setSideBarOpen(true);
	};

	const applyFeatureSelectFromMap = useCallback(row => {
		if (!row) {
			olUtils.highlightFeatureEvent(null, getMap(MODEL_EDITOR_MAP_ID));
			setSelectedFeature(null);
			setSideBarOpen(false);
			return;
		}

		olUtils.highlightFeatureEvent(row._featureId ?? row.featureId ?? row.id, getMap(MODEL_EDITOR_MAP_ID), {
			layerName: row._layerName,
			zoom: 17,
			fitToFeature: false,
		});
		setSelectedFeature(row);
		setSideBarOpen(true);
	}, []);

	const handleFeatureAdded = (layerName, feature) => {
		const row = buildLayerTableRowFromFeature(layerName, feature);
		if (!row) return;

		setModelTableLayerType(layerName);
		setSelectedFeature(row);
		setSideBarOpen(true);
	};

	const findMapFeatureByRow = row => {
		if (!row?._layerName) return null;
		const layer = olUtils.getLayerByName(getMap(MODEL_EDITOR_MAP_ID), row._layerName);
		const features = layer?.getSource?.()?.getFeatures?.() ?? [];
		if (Number.isInteger(row._featureIndex) && features[row._featureIndex]) {
			return features[row._featureIndex];
		}

		const featureId = row._featureId ?? row.featureId ?? '';
		return (
			features.find(feature =>
				[feature.get('id'), feature.get('ID'), feature.get('name'), feature.get('label'), feature.get('LABEL')]
					.filter(value => value !== null && value !== undefined)
					.some(value => String(value) === String(featureId))
			) ?? null
		);
	};

	const handleFeatureIdChange = (row, value) => {
		if (!row) return;
		const nextId = value ?? '';
		const feature = findMapFeatureByRow(row);
		if (!feature) return;

		feature.set('id', nextId);
		if (feature.get('ID') !== undefined) {
			feature.set('ID', nextId);
		}
		feature.changed();
		olUtils.getLayerByName(getMap(MODEL_EDITOR_MAP_ID), row._layerName)?.changed?.();
		getMap(MODEL_EDITOR_MAP_ID)?.render?.();

		const nextRow = {
			...row,
			id: nextId,
			_featureId: nextId,
			featureId: nextId,
			rowKey: row.rowKey,
			_rawProperties: {
				...(row._rawProperties ?? {}),
				id: nextId,
			},
		};

		setSelectedFeature(prev => {
			if (!prev) return prev;
			const isSameFeature = prev.rowKey === row.rowKey || prev._featureIndex === row._featureIndex;
			return isSameFeature ? nextRow : prev;
		});
		setMapLayerVersion(prev => prev + 1);
	};

	const validateSelectedFeaturePropertyChange = (key, value) => {
		if (key !== 'featureId' || !selectedFeature?._layerName || isBlankValue(value)) return '';

		const currentFeature = findMapFeatureByRow(selectedFeature);
		const layer = olUtils.getLayerByName(getMap(MODEL_EDITOR_MAP_ID), selectedFeature._layerName);
		const features = layer?.getSource?.()?.getFeatures?.() ?? [];
		const normalizedValue = String(value).trim();
		const hasDuplicate = features.some(feature => {
			if (feature === currentFeature) return false;
			return String(getFeatureId(feature)).trim() === normalizedValue;
		});

		return hasDuplicate ? '같은 레이어 안에서 아이디가 중복됩니다.' : '';
	};

	const handleNonVisualSectionPropertyChange = (key, value) => {
		if (
			selectedFeature?._sectionName === 'CONTROLS' &&
			[
				'content',
				'simpleContent',
				'addSimpleControl',
				'deleteSimpleControl',
				'ruleContent',
				'addRule',
				'deleteRule',
			].includes(key)
		) {
			const controlType = selectedFeature._controlType ?? 'simple';
			const nextContent = ['simpleContent', 'ruleContent'].includes(key) ? (value?.value ?? '') : (value ?? '');
			const controlIndex = Number.isInteger(value?.index) ? value.index : 0;

			setNetworkDetail(prev => {
				if (!prev) return prev;

				const currentControls = prev.sections?.CONTROLS;
				let nextControls;

				if (Array.isArray(currentControls)) {
					if (controlType === 'rule') {
						const nextRuleSeq = [];
						if (key === 'addRule') {
							nextRuleSeq.push({
								id: '1',
								content: '',
							});
						} else if (key === 'ruleContent') {
							nextRuleSeq[controlIndex] = parseControlRuleText(nextContent, String(controlIndex + 1));
						}

						nextControls = {
							simple: currentControls,
							rule: reindexControlRuleSeq(nextRuleSeq),
						};
					} else {
						if (key === 'addSimpleControl') {
							nextControls = [...currentControls, ''];
						} else if (key === 'deleteSimpleControl') {
							nextControls = currentControls.filter((_, index) => index !== controlIndex);
						} else if (key === 'simpleContent') {
							nextControls = [...currentControls];
							nextControls[controlIndex] = nextContent;
						} else {
							nextControls = parseControlSimpleText(nextContent);
						}
					}
				} else {
					const currentControlObject =
						currentControls && typeof currentControls === 'object' ? currentControls : { simple: [], rule: [] };
					if (controlType === 'rule') {
						const nextRuleSeq = Array.isArray(currentControlObject.rule) ? [...currentControlObject.rule] : [];
						if (key === 'addRule') {
							nextRuleSeq.push({
								id: resolveNextControlRuleId(nextRuleSeq),
								content: '',
							});
						} else if (key === 'deleteRule') {
							nextRuleSeq.splice(controlIndex, 1);
							nextControls = {
								...currentControlObject,
								rule: reindexControlRuleSeq(nextRuleSeq),
							};
							return {
								...prev,
								sections: {
									...(prev.sections ?? {}),
									CONTROLS: nextControls,
								},
							};
						} else {
							const currentRule = nextRuleSeq[controlIndex] ?? {};
							const parsedRule = parseControlRuleText(
								nextContent,
								currentRule.id ?? selectedFeature.controlId?.replace(/^RULE\s+/i, '')
							);

							nextRuleSeq[controlIndex] = {
								...currentRule,
								id: parsedRule.id,
								content: parsedRule.content,
							};
						}
						nextControls = {
							...currentControlObject,
							rule: nextRuleSeq,
						};
					} else {
						const nextSimpleSeq = Array.isArray(currentControlObject.simple) ? [...currentControlObject.simple] : [];
						if (key === 'addSimpleControl') {
							nextSimpleSeq.push('');
						} else if (key === 'deleteSimpleControl') {
							nextSimpleSeq.splice(controlIndex, 1);
						} else if (key === 'simpleContent') {
							nextSimpleSeq[controlIndex] = nextContent;
						}

						nextControls = {
							...currentControlObject,
							simple: ['simpleContent', 'addSimpleControl', 'deleteSimpleControl'].includes(key)
								? nextSimpleSeq
								: parseControlSimpleText(nextContent),
						};
					}
				}

				return {
					...prev,
					sections: {
						...(prev.sections ?? {}),
						CONTROLS: nextControls,
					},
				};
			});

			setSelectedFeature(prev => {
				if (!prev || prev.rowKey !== selectedFeature.rowKey) return prev;
				if (controlType === 'rule') {
					if (key === 'addRule') {
						const nextId = resolveNextControlRuleId(prev.ruleSeq);
						return {
							...prev,
							ruleSeq: [
								...(prev.ruleSeq ?? []),
								{
									index: (prev.ruleSeq ?? []).length,
									id: nextId,
									title: `RULE ${nextId}`,
									content: '',
								},
							],
						};
					}

					if (key === 'deleteRule') {
						const nextRuleSeq = reindexControlRuleSeq(
							(prev.ruleSeq ?? [])
								.filter(rule => rule.index !== controlIndex)
								.map(rule => ({
									id: rule.id,
									content: rule.content,
								}))
						);

						return {
							...prev,
							ruleSeq: buildControlRuleRowSeq(nextRuleSeq),
						};
					}

					return {
						...prev,
						ruleSeq: (prev.ruleSeq ?? []).map(rule => {
							if (rule.index !== controlIndex) return rule;
							const parsedRule = parseControlRuleText(nextContent, rule.id);
							return {
								...rule,
								id: parsedRule.id,
								title: `RULE ${parsedRule.id}`,
								content: parsedRule.content,
							};
						}),
					};
				}

				if (key === 'addSimpleControl') {
					const nextSimpleSeq = [...(prev.simpleSeq ?? []), ''];
					return {
						...prev,
						content: nextSimpleSeq.join('\n'),
						simpleSeq: nextSimpleSeq,
					};
				}

				if (key === 'deleteSimpleControl') {
					const nextSimpleSeq = (prev.simpleSeq ?? []).filter((_, index) => index !== controlIndex);
					return {
						...prev,
						content: nextSimpleSeq.join('\n'),
						simpleSeq: nextSimpleSeq,
					};
				}

				if (key === 'simpleContent') {
					const nextSimpleSeq = [...(prev.simpleSeq ?? [])];
					nextSimpleSeq[controlIndex] = nextContent;
					return {
						...prev,
						content: nextSimpleSeq.join('\n'),
						simpleSeq: nextSimpleSeq,
					};
				}

				return {
					...prev,
					content: nextContent,
					simpleSeq: parseControlSimpleText(nextContent),
				};
			});

			return true;
		}

		if (selectedFeature?._sectionName === 'PATTERNS') {
			const sectionIndex = Number.isInteger(selectedFeature._sectionIndex) ? selectedFeature._sectionIndex : 0;
			const nextPatternValue = value ?? '';

			if (!['id', 'description', 'multiplier'].includes(key)) return false;

			setNetworkDetail(prev => {
				if (!prev) return prev;

				const nextPatterns = Array.isArray(prev.sections?.PATTERNS) ? [...prev.sections.PATTERNS] : [];
				const currentPattern = nextPatterns[sectionIndex] ?? {};
				const nextPattern =
					key === 'multiplier'
						? {
								...currentPattern,
								multipliers: updatePatternMultiplierSeq(currentPattern.multipliers, value?.index, value?.value),
							}
						: {
								...currentPattern,
								[key]: nextPatternValue,
							};

				nextPatterns[sectionIndex] = nextPattern;

				return {
					...prev,
					sections: {
						...(prev.sections ?? {}),
						PATTERNS: nextPatterns,
					},
				};
			});

			setSelectedFeature(prev => {
				if (!prev || prev.rowKey !== selectedFeature.rowKey) return prev;

				if (key === 'multiplier') {
					return {
						...prev,
						multiplierSeq: updatePatternMultiplierSeq(prev.multiplierSeq, value?.index, value?.value),
					};
				}

				return {
					...prev,
					[key]: nextPatternValue,
					...(key === 'id' ? { rowKey: `PATTERNS-${sectionIndex}-${nextPatternValue}` } : {}),
				};
			});

			return true;
		}

		if (selectedFeature?._sectionName === 'CURVES') {
			const sectionIndex = Number.isInteger(selectedFeature._sectionIndex) ? selectedFeature._sectionIndex : 0;
			const nextCurveValue = value ?? '';

			if (!['id', 'description', 'curveType', 'curvePoint'].includes(key)) return false;

			setNetworkDetail(prev => {
				if (!prev) return prev;

				const nextCurves = Array.isArray(prev.sections?.CURVES) ? [...prev.sections.CURVES] : [];
				const currentCurve = nextCurves[sectionIndex] ?? {};
				const nextCurve =
					key === 'curvePoint'
						? {
								...currentCurve,
								xyData: updateCurvePointSeq(currentCurve.xyData, value?.index, value?.axis, value?.value),
							}
						: {
								...currentCurve,
								[key]: nextCurveValue,
							};

				nextCurves[sectionIndex] = nextCurve;

				return {
					...prev,
					sections: {
						...(prev.sections ?? {}),
						CURVES: nextCurves,
					},
				};
			});

			setSelectedFeature(prev => {
				if (!prev || prev.rowKey !== selectedFeature.rowKey) return prev;

				if (key === 'curvePoint') {
					return {
						...prev,
						xyDataSeq: updateCurvePointSeq(prev.xyDataSeq, value?.index, value?.axis, value?.value),
					};
				}

				return {
					...prev,
					[key]: nextCurveValue,
					...(key === 'id' ? { rowKey: `CURVES-${sectionIndex}-${nextCurveValue}` } : {}),
				};
			});

			return true;
		}

		if (selectedFeature?._sectionName === 'OPTIONS' && key === 'optionValue') {
			const pathSeq = value?.pathSeq;
			const nextOptionValue = value?.value ?? '';

			if (!Array.isArray(pathSeq)) return false;

			setNetworkDetail(prev => {
				if (!prev) return prev;

				const currentOptions = prev.sections?.OPTIONS ?? prev.options ?? {};
				const nextOptions = updateNestedValueByPath(currentOptions, pathSeq, nextOptionValue);
				const nextDetail = {
					...prev,
					sections: {
						...(prev.sections ?? {}),
						OPTIONS: nextOptions,
					},
				};

				if (prev.options) {
					nextDetail.options = nextOptions;
				}

				return nextDetail;
			});

			setSelectedFeature(prev => {
				if (!prev || prev.rowKey !== selectedFeature.rowKey) return prev;
				const updateEntryValue = entry =>
					isSamePathSeq(entry.pathSeq, pathSeq)
						? {
								...entry,
								value: nextOptionValue,
							}
						: entry;

				return {
					...prev,
					optionEntrySeq: (prev.optionEntrySeq ?? []).map(updateEntryValue),
					optionGroupSeq: (prev.optionGroupSeq ?? []).map(group => ({
						...group,
						entrySeq: (group.entrySeq ?? []).map(updateEntryValue),
					})),
				};
			});

			return true;
		}

		return false;
	};

	const handleSelectedFeaturePropertyChange = (key, value) => {
		if (key === 'featureId') {
			handleFeatureIdChange(selectedFeature, value);
			return;
		}

		if (!selectedFeature || READ_ONLY_PROPERTY_KEY_SET.has(key)) return;
		if (selectedFeature._isNonVisualSection) {
			handleNonVisualSectionPropertyChange(key, value);
			return;
		}

		const feature = findMapFeatureByRow(selectedFeature);
		if (feature) {
			feature.set(key, value);
			feature.changed();
			olUtils.getLayerByName(getMap(MODEL_EDITOR_MAP_ID), selectedFeature._layerName)?.changed?.();
			getMap(MODEL_EDITOR_MAP_ID)?.render?.();
		}

		setSelectedFeature(prev => {
			if (!prev) return prev;
			const isSameFeature = prev.rowKey === selectedFeature.rowKey || prev._featureIndex === selectedFeature._featureIndex;
			if (!isSameFeature) return prev;

			return {
				...prev,
				[key]: formatTableCellValue(value),
				_rawProperties: {
					...(prev._rawProperties ?? {}),
					[key]: value,
				},
			};
		});
		setMapLayerVersion(prev => prev + 1);
	};

	useEffect(() => {
		let isDisposed = false;
		let targetMap = null;

		const registerFeatureSelect = () => {
			if (isDisposed) return;

			const map = getMap(MODEL_EDITOR_MAP_ID);
			if (!map) {
				window.requestAnimationFrame(registerFeatureSelect);
				return;
			}

			targetMap = map;

			olUtils.setFeatureSelect(
				map,
				({ feature, layerName }) => {
					if (!feature) {
						applyFeatureSelectFromMap(null);
						return;
					}

					const resolvedLayerName = layerName ?? feature.get?.('layer');
					if (!LAYER_ORDER.includes(resolvedLayerName)) return;

					const row = buildLayerTableRowFromFeature(resolvedLayerName, feature);
					if (!row) return;

					setModelTableLayerType(resolvedLayerName);
					applyFeatureSelectFromMap(row);
				},
				{
					layerNames: LAYER_ORDER,
					hitTolerance: 8,
				}
			);
		};

		registerFeatureSelect();

		return () => {
			isDisposed = true;
			const map = targetMap ?? getMap(MODEL_EDITOR_MAP_ID);
			if (map) {
				olUtils.removeFeatureSelect(map);
			}
		};
	}, [applyFeatureSelectFromMap, mapLayerVersion]);

	return (
		<div className="flex h-full min-h-0 flex-col gap-0 bg-[linear-gradient(180deg,#122347,#0d1d39)]">
			<TopToolbar
				modelName={modelName}
				setModelName={setModelName}
				onActionClick={handleToolbarActionClick}
				hasSelectedModelFile={Boolean(selectedModelFile)}
				isSavingModel={isSavingModel}
				isApplyingModel={isApplyingModel}
				isOptimizationExecuting={isOptimizationExecuting}
			/>
			<div className="grid min-h-0 flex-1 grid-cols-[304px_minmax(0,1fr)] gap-2 px-2 py-2 pt-1">
				<SidebarPanel
					networkDetail={networkDetail}
					mapLayerVersion={mapLayerVersion}
					layerType={modelTableLayerType}
					onLayerTypeChange={setModelTableLayerType}
					selectedFeature={selectedFeature}
					onSelectFeature={handleFeatureSelect}
					revisionRowSeq={revisionRowSeq}
					onRevisionSave={handleRevisionSave}
					onRevisionDownload={handleRevisionDownload}
					isRevisionSaving={isRevisionSaving}
				/>
				<div ref={setMapWorkspaceEl} className="relative h-full min-h-0 overflow-hidden">
					<MapArea
						selectedModel={selectedModel}
						setSelectedModel={setSelectedModel}
						isEditMode={isEditMode}
						setIsEditMode={setIsEditMode}
						onLayerChanged={() => setMapLayerVersion(prev => prev + 1)}
						onClearSelectedFeature={() => setSelectedFeature(null)}
						onFeatureAdded={handleFeatureAdded}
						onFeatureChanged={handleFeatureAdded}
					/>
					<CommonDrawer
						visible={sideBarOpen}
						open={sideBarOpen}
						setOpen={setSideBarOpen}
						anchor="right"
						variant="persistent"
						ModalProps={{
							hideBackdrop: true,
							disablePortal: true,
							keepMounted: true,
							container: mapWorkspaceEl,
						}}
						sx={{
							position: 'absolute',
							top: 0,
							right: 0,
							bottom: 0,
							left: 'auto',
							width: 336,
							overflow: 'visible',
							pointerEvents: 'none',
							'& .MuiDrawer-paper': {
								pointerEvents: 'auto',
								overflow: 'hidden',
							},
						}}
						bodyClassName="relative flex h-full min-h-0 w-full flex-col overflow-hidden"
						className="overflow-hidden rounded-l-[18px] border-l border-t border-b border-[rgba(110,185,255,0.28)] bg-[linear-gradient(180deg,rgba(19,35,67,0.97),rgba(14,29,57,0.98))] shadow-[0_16px_48px_rgba(6,14,31,0.45)]"
						paperProps={{
							elevation: 0,
							sx: {
								position: 'absolute',
								top: 0,
								right: 0,
								left: 'auto',
								height: '100%',
								width: 336,
								maxWidth: '33%',
								minWidth: 320,
								backgroundImage: 'linear-gradient(180deg, rgba(19,35,67,0.97), rgba(14,29,57,0.98))',
								backgroundColor: 'rgba(14,29,57,0.98)',
								borderTop: '1px solid rgba(110, 185, 255, 0.24)',
								borderBottom: '1px solid rgba(110, 185, 255, 0.24)',
								borderLeft: '1px solid rgba(110, 185, 255, 0.24)',
								boxShadow: '0 16px 48px rgba(6, 14, 31, 0.45)',
								overflow: 'hidden',
							},
						}}
					>
						<div className="h-full min-h-0 overflow-hidden px-3 py-2">
							<FeaturePropertyPanel
								selectedFeature={selectedFeature}
								networkDetail={networkDetail}
								onPropertyChange={handleSelectedFeaturePropertyChange}
								validatePropertyChange={validateSelectedFeaturePropertyChange}
							/>
						</div>
					</CommonDrawer>
				</div>
			</div>
			<ModelSelectDialog
				open={isModelSelectDialogOpen}
				setOpen={setIsModelSelectDialogOpen}
				onApply={handleModelSelectApply}
			/>
			<SettingValueDialog
				open={isSettingValueDialogOpen}
				setOpen={setIsSettingValueDialogOpen}
				selectedModelFile={selectedModelFile}
			/>
			<SettingValueDialog
				open={isComparisonTargetDialogOpen}
				setOpen={setIsComparisonTargetDialogOpen}
				selectedModelFile={selectedModelFile}
				mode="comparisonTarget"
			/>
			<OptimizationManagerDialog
				open={isOptimizationManagerOpen}
				setOpen={setIsOptimizationManagerOpen}
				selectedModelFile={selectedModelFile}
			/>
		</div>
	);
}

export default ModelEditorPageTemp;
