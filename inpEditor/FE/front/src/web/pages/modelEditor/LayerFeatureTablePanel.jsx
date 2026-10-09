import {
	LAYER_OPTION_SEQ,
	LAYER_ORDER,
	LAYER_TABLE_BASE_COL_CLASS_NAME,
	MODEL_EDITOR_LAYER_TREE_ITEMS,
	MODEL_EDITOR_LEFT_TAB_ITEM_SEQ,
	MODEL_EDITOR_MAP_ID,
	MODEL_EDITOR_SELECT_MENU_PROPS,
	NON_VISUAL_MODEL_SECTION_ORDER,
	OBJECT_PROPERTY_LABEL_BY_KEY,
} from '@/consts/index.js';
import CommonButton from '@/web/components/common/CommonButton.jsx';
import CommonCard from '@/web/components/common/CommonCard.jsx';
import CommonSelect from '@/web/components/common/CommonSelect.jsx';
import CommonTable from '@/web/components/common/CommonTable.jsx';
import CommonTabs from '@/web/components/common/CommonTabs.jsx';
import CommonTree from '@/web/components/common/CommonTree.jsx';
import { getMap } from '@/web/js/utils/mapRegistry.js';
import { OlUtils as olUtils } from '@/web/js/utils/olUtils.js';
import { useCallback, useEffect, useMemo, useState } from 'react';

function formatTableCellValue(value) {
	if (value === null || value === undefined) return '';
	if (typeof value === 'object') return JSON.stringify(value);
	return value;
}

function formatTableTextValue(value) {
	return String(formatTableCellValue(value));
}

function resolveLayerFeatureId(properties, fallbackId = '') {
	return properties.id ?? properties.ID ?? properties.name ?? properties.label ?? properties.LABEL ?? fallbackId ?? '';
}

function buildLayerTableRow(layerType, properties, coordinates, index, fallbackId = '') {
	const [x, y] = Array.isArray(coordinates) && typeof coordinates[0] === 'number' ? coordinates : ['', ''];
	const featureId = resolveLayerFeatureId(properties, fallbackId);

	return {
		...Object.fromEntries(Object.entries(properties).map(([key, value]) => [key, formatTableCellValue(value)])),
		no: String(index + 1).padStart(2, '0'),
		rowKey: `${layerType}-${index}`,
		_layerName: layerType,
		_featureId: featureId,
		_featureIndex: index,
		_rawProperties: properties,
		featureId,
		x,
		y,
	};
}

function getOlFeatureCoordinate(feature) {
	const geometry = feature?.getGeometry?.();
	if (!geometry) return null;
	if (geometry.getType?.() === 'Point') return geometry.getCoordinates?.() ?? null;
	return olUtils.getGeometryCenterCoordinate(feature);
}

function buildLayerTableRowsFromMap(layerType) {
	const layer = olUtils.getLayerByName(getMap(MODEL_EDITOR_MAP_ID), layerType);
	const features = layer?.getSource?.()?.getFeatures?.() ?? [];

	return features.map((feature, index) => {
		const { geometry, ...properties } = feature.getProperties?.() ?? {};
		return buildLayerTableRow(layerType, properties, getOlFeatureCoordinate(feature), index, feature.getId?.());
	});
}

function buildLayerTableRows(networkDetail, layerType, mapLayerVersion = 0) {
	if (NON_VISUAL_MODEL_SECTION_ORDER.includes(layerType)) {
		return buildNonVisualTableRows(networkDetail, layerType);
	}

	const shouldReadMapLayer = mapLayerVersion >= 0;
	const mapRows = shouldReadMapLayer ? buildLayerTableRowsFromMap(layerType) : [];
	if (mapRows.length > 0) return mapRows;

	const layerMap = olUtils.normalizeLayerDataMap(networkDetail?.layers ?? networkDetail);
	const features = layerMap[layerType]?.features ?? [];

	return features.map((feature, index) =>
		buildLayerTableRow(layerType, feature?.properties ?? {}, feature?.geometry?.coordinates, index)
	);
}

function buildLayerTableRowFromFeature(layerType, feature) {
	if (!layerType || !feature) return null;

	const layer = olUtils.getLayerByName(getMap(MODEL_EDITOR_MAP_ID), layerType);
	const features = layer?.getSource?.()?.getFeatures?.() ?? [];
	const featureIndex = features.indexOf(feature);
	const { geometry, ...properties } = feature.getProperties?.() ?? {};

	return buildLayerTableRow(
		layerType,
		properties,
		getOlFeatureCoordinate(feature),
		featureIndex >= 0 ? featureIndex : features.length,
		feature.getId?.()
	);
}

function buildControlRows(networkDetail) {
	const controls = networkDetail?.sections?.CONTROLS;
	const simpleSeq = Array.isArray(controls)
		? controls.map(formatTableTextValue)
		: Array.isArray(controls?.simple)
			? controls.simple.map(formatTableTextValue)
			: [];
	const ruleSeq = Array.isArray(controls?.rule)
		? controls.rule.map((rule, index) => ({
				index,
				id: formatTableTextValue(rule?.id),
				title: `RULE ${formatTableTextValue(rule?.id)}`,
				content: formatTableTextValue(rule?.content),
			}))
		: [];

	return [
		{
			no: '01',
			rowKey: 'CONTROLS-simple',
			_sectionName: 'CONTROLS',
			_sectionIndex: 0,
			_controlType: 'simple',
			_isNonVisualSection: true,
			sectionLabel: '단순 제어',
			content: simpleSeq.join('\n'),
			simpleSeq,
		},
		{
			no: '02',
			rowKey: 'CONTROLS-rule',
			_sectionName: 'CONTROLS',
			_sectionIndex: 0,
			_controlType: 'rule',
			_isNonVisualSection: true,
			sectionLabel: '규칙 제어',
			ruleSeq,
		},
	];
}

function buildPatternRows(networkDetail) {
	const patternSeq = networkDetail?.sections?.PATTERNS;
	if (!Array.isArray(patternSeq)) return [];

	return patternSeq.map((pattern, index) => ({
		...Object.fromEntries(Object.entries(pattern ?? {}).map(([key, value]) => [key, formatTableCellValue(value)])),
		no: String(index + 1).padStart(2, '0'),
		rowKey: `PATTERNS-${index}-${pattern?.id ?? ''}`,
		_sectionName: 'PATTERNS',
		_sectionIndex: index,
		_isNonVisualSection: true,
		id: formatTableTextValue(pattern?.id),
		description: formatTableTextValue(pattern?.description),
		multiplierSeq: Array.isArray(pattern?.multipliers) ? pattern.multipliers.map(formatTableTextValue) : [],
		multipliers: Array.isArray(pattern?.multipliers)
			? `${pattern.multipliers.length}개`
			: formatTableTextValue(pattern?.multipliers),
	}));
}

function buildCurveRows(networkDetail) {
	const curveSeq = networkDetail?.sections?.CURVES;
	if (!Array.isArray(curveSeq)) return [];

	return curveSeq
		.flatMap((curve, index) => {
			if (String(curve?.curveType ?? '').toUpperCase() !== 'PUMP') return [];

			return [
				{
					...Object.fromEntries(Object.entries(curve ?? {}).map(([key, value]) => [key, formatTableCellValue(value)])),
					rowKey: `CURVES-${index}-${curve?.id ?? ''}`,
					_sectionName: 'CURVES',
					_sectionIndex: index,
					_isNonVisualSection: true,
					id: formatTableTextValue(curve?.id),
					curveType: formatTableTextValue(curve?.curveType),
					description: formatTableTextValue(curve?.description),
					xyDataSeq: Array.isArray(curve?.xyData)
						? curve.xyData.map(point => ({
								x: formatTableTextValue(point?.x),
								y: formatTableTextValue(point?.y),
							}))
						: [],
					xyData: Array.isArray(curve?.xyData) ? `${curve.xyData.length}개` : formatTableTextValue(curve?.xyData),
				},
			];
		})
		.map((row, index) => ({
			...row,
			no: String(index + 1).padStart(2, '0'),
		}));
}

function getOptionSection(networkDetail) {
	return networkDetail?.sections?.OPTIONS ?? networkDetail?.options;
}

function formatOptionEntryPath(pathSeq) {
	return pathSeq
		.map((pathItem, index) => {
			if (typeof pathItem === 'number') return `[${pathItem}]`;
			return index === 0 ? pathItem : `.${pathItem}`;
		})
		.join('');
}

function buildOptionEntryRows(value, pathSeq = []) {
	if (Array.isArray(value)) {
		return value.flatMap((item, index) => buildOptionEntryRows(item, [...pathSeq, index]));
	}

	if (value && typeof value === 'object') {
		return Object.entries(value).flatMap(([key, item]) => buildOptionEntryRows(item, [...pathSeq, key]));
	}

	return [
		{
			pathSeq,
			label: formatOptionEntryPath(pathSeq),
			value: formatTableTextValue(value),
		},
	];
}

function buildOptionRows(networkDetail) {
	const options = getOptionSection(networkDetail);
	if (!options || typeof options !== 'object') return [];
	const optionEntrySeq = buildOptionEntryRows(options);
	const optionGroupSeq = Object.entries(options).map(([key, value]) => ({
		key,
		entryCount: buildOptionEntryRows(value).length,
		entrySeq: buildOptionEntryRows(value, [key]),
	}));

	return [
		{
			no: '01',
			rowKey: 'OPTIONS-root',
			_sectionName: 'OPTIONS',
			_sectionIndex: 0,
			_isNonVisualSection: true,
			sectionLabel: '옵션',
			entryCount: optionEntrySeq.length,
			optionEntrySeq,
			optionGroupSeq,
		},
	];
}

function buildNonVisualTableRows(networkDetail, layerType) {
	switch (layerType) {
		case 'CONTROLS':
			return buildControlRows(networkDetail);
		case 'PATTERNS':
			return buildPatternRows(networkDetail);
		case 'OPTIONS':
			return buildOptionRows(networkDetail);
		case 'CURVES':
			return buildCurveRows(networkDetail);
		default:
			return [];
	}
}

function buildEmptyNonVisualSelectionRow(layerType) {
	const baseRow = {
		no: '',
		rowKey: `${layerType}-empty`,
		_sectionName: layerType,
		_sectionIndex: 0,
		_isNonVisualSection: true,
	};

	switch (layerType) {
		case 'CONTROLS':
			return {
				...baseRow,
				_controlType: 'simple',
				sectionLabel: '단순 제어',
				content: '',
				simpleSeq: [],
				ruleSeq: [],
			};
		case 'PATTERNS':
			return {
				...baseRow,
				id: '',
				description: '',
				multiplierSeq: [],
				multipliers: '',
			};
		case 'OPTIONS':
			return {
				...baseRow,
				category: '',
				sectionLabel: '옵션',
				entryCount: '',
				optionEntrySeq: [],
				optionGroupSeq: [],
			};
		case 'CURVES':
			return {
				...baseRow,
				id: '',
				curveType: '',
				description: '',
				xyDataSeq: [],
			};
		default:
			return baseRow;
	}
}

function createTableColumn(key, label, widthClassName) {
	return {
		key,
		colNm: label,
		widthClassName,
		editable: false,
		headClassName: LAYER_TABLE_BASE_COL_CLASS_NAME.headClassName,
		cellClassName:
			key === 'no'
				? 'border-b border-r border-slate-800/70 text-center text-slate-400'
				: LAYER_TABLE_BASE_COL_CLASS_NAME.cellClassName,
	};
}

function buildLayerTableColumns(layerType) {
	if (layerType === 'CONTROLS') {
		return [createTableColumn('no', '번호', 'w-16 text-center'), createTableColumn('sectionLabel', '구분', 'w-[180px]')];
	}

	if (layerType === 'PATTERNS') {
		return [
			createTableColumn('no', '번호', 'w-16 text-center'),
			createTableColumn('id', '아이디', 'w-[160px]'),
			createTableColumn('description', '설명', 'w-[220px]'),
			createTableColumn('multipliers', '배율', 'w-[260px]'),
		];
	}

	if (layerType === 'OPTIONS') {
		return [
			createTableColumn('no', '번호', 'w-16 text-center'),
			createTableColumn('sectionLabel', '구분', 'w-[180px]'),
			createTableColumn('entryCount', '항목수', 'w-[90px]'),
		];
	}

	if (layerType === 'CURVES') {
		return [
			createTableColumn('no', '번호', 'w-16 text-center'),
			createTableColumn('id', '아이디', 'w-[160px]'),
			createTableColumn('curveType', '유형', 'w-[130px]'),
			createTableColumn('description', '설명', 'w-[220px]'),
		];
	}

	return [
		createTableColumn('no', OBJECT_PROPERTY_LABEL_BY_KEY.no, 'w-16 text-center'),
		createTableColumn('featureId', OBJECT_PROPERTY_LABEL_BY_KEY.featureId, 'w-[180px]'),
	];
}

function resolveVisibleModelLayerNames(selectedItems) {
	return new Set((selectedItems ?? []).filter(item => LAYER_ORDER.includes(item)));
}

const MODEL_LAYER_TABLE_PAGE_SIZE = 100;

function LayerFeatureTablePanel({
	networkDetail,
	mapLayerVersion,
	layerType,
	onLayerTypeChange,
	selectedFeature,
	onSelectFeature,
	extraTabItems = [],
	renderExtraTab,
	onTabChange,
}) {
	const [tab, setTab] = useState(MODEL_EDITOR_LEFT_TAB_ITEM_SEQ[0].v);
	const [selectedModelLayerSeq, setSelectedModelLayerSeq] = useState([
		'NODES',
		'JUNCTIONS',
		'RESERVOIRS',
		'TANKS',
		'LINKS',
		'PIPES',
		'PUMPS',
		'VALVES',
		'LABELS',
	]);
	const [paginationModel, setPaginationModel] = useState({
		page: 0,
		pageSize: MODEL_LAYER_TABLE_PAGE_SIZE,
	});
	const rowSeq = useMemo(
		() => buildLayerTableRows(networkDetail, layerType, mapLayerVersion),
		[networkDetail, layerType, mapLayerVersion]
	);
	const colSeq = useMemo(() => buildLayerTableColumns(layerType), [layerType]);
	const isExtraTabSelected = extraTabItems.some(item => item.v === tab);
	const pageCount = Math.max(1, Math.ceil(rowSeq.length / MODEL_LAYER_TABLE_PAGE_SIZE));
	const visibleStartRowNo =
		rowSeq.length === 0 ? 0 : paginationModel.page * MODEL_LAYER_TABLE_PAGE_SIZE + 1;
	const visibleEndRowNo = Math.min(rowSeq.length, (paginationModel.page + 1) * MODEL_LAYER_TABLE_PAGE_SIZE);
	const canMovePreviousPage = paginationModel.page > 0;
	const canMoveNextPage = paginationModel.page < pageCount - 1;
	const handleModelLayerSelectionChange = useCallback((values, itemIds, valuesArr) => {
		const nextSelectedItems = valuesArr ?? itemIds;
		setSelectedModelLayerSeq(nextSelectedItems);
	}, []);
	const handleTabChange = useCallback(
		nextTab => {
			setTab(nextTab);
			onTabChange?.(nextTab);
		},
		[onTabChange]
	);
	const handlePaginationModelChange = useCallback(nextPaginationModel => {
		setPaginationModel({
			page: nextPaginationModel.page,
			pageSize: MODEL_LAYER_TABLE_PAGE_SIZE,
		});
	}, []);
	const moveModelLayerPage = useCallback(
		pageOffset => {
			setPaginationModel(prev => ({
				page: Math.min(Math.max(prev.page + pageOffset, 0), pageCount - 1),
				pageSize: MODEL_LAYER_TABLE_PAGE_SIZE,
			}));
		},
		[pageCount]
	);

	useEffect(() => {
		setPaginationModel({
			page: 0,
			pageSize: MODEL_LAYER_TABLE_PAGE_SIZE,
		});
	}, [layerType, mapLayerVersion, networkDetail]);

	useEffect(() => {
		if (!NON_VISUAL_MODEL_SECTION_ORDER.includes(layerType)) return;
		if (selectedFeature?._sectionName === layerType) return;
		const firstRow = rowSeq[0] ?? buildEmptyNonVisualSelectionRow(layerType);
		if (selectedFeature?.rowKey === firstRow.rowKey) return;

		onSelectFeature?.(firstRow);
	}, [layerType, onSelectFeature, rowSeq, selectedFeature?._sectionName, selectedFeature?.rowKey]);

	useEffect(() => {
		if (isExtraTabSelected) return;

		const map = getMap(MODEL_EDITOR_MAP_ID);
		if (!map) return;

		const visibleLayerNameSet = resolveVisibleModelLayerNames(selectedModelLayerSeq);
		LAYER_ORDER.forEach(layerName => {
			olUtils.setVisibleLayer(map, layerName, visibleLayerNameSet.has(layerName));
		});
	}, [isExtraTabSelected, mapLayerVersion, networkDetail, selectedModelLayerSeq]);

	return (
		<CommonTabs
			className="flex h-full min-h-0 flex-col"
			contentClassName="min-h-0 flex-1"
			items={[...MODEL_EDITOR_LEFT_TAB_ITEM_SEQ, ...extraTabItems]}
			value={tab}
			onChange={handleTabChange}
		>
			{tab === 'model' ? (
				<div className="mt-2 flex h-full min-h-0 flex-col overflow-hidden">
					<div className="shrink-0">
						<CommonSelect
							value={layerType}
							onChange={nextLayerType => {
								onLayerTypeChange?.(nextLayerType);
								onSelectFeature?.(null);
							}}
							options={LAYER_OPTION_SEQ}
							optionLabelKey="label"
							optionValueKey="value"
							className="model-editor-select"
							menuProps={MODEL_EDITOR_SELECT_MENU_PROPS}
						/>
					</div>
					<div className="mt-2 flex shrink-0 items-center justify-between gap-2 text-[11px] text-sky-100/70">
						<span className="min-w-0 truncate">
							{visibleStartRowNo}-{visibleEndRowNo} / {rowSeq.length}
						</span>
						<div className="flex shrink-0 items-center gap-1">
							<CommonButton
								text="이전"
								size="xs"
								variant="outline"
								disabled={!canMovePreviousPage}
								onClick={() => moveModelLayerPage(-1)}
							/>
							<span className="min-w-[52px] text-center">
								{paginationModel.page + 1} / {pageCount}
							</span>
							<CommonButton
								text="다음"
								size="xs"
								variant="outline"
								disabled={!canMoveNextPage}
								onClick={() => moveModelLayerPage(1)}
							/>
						</div>
					</div>
					<CommonCard className="mt-2 min-h-0 flex-1 overflow-hidden rounded-none bg-transparent p-0 shadow-none">
						<CommonTable
							colSeq={colSeq}
							rowSeq={rowSeq}
							getRowKey={row => row.rowKey}
							emptyMsg="모델을 선택하면 데이터가 표시됩니다."
							enableSorting={true}
							enableFiltering={true}
							disableHeaderSortClick={true}
							hideFooter={true}
							initialPaginationModel={{ page: 0, pageSize: 100 }}
							pageSizeOptions={[100]}
							paginationModel={paginationModel}
							onPaginationModelChange={handlePaginationModelChange}
							onRowClick={row => {
								onSelectFeature?.(row);
							}}
							selectedRowKey={selectedFeature?.rowKey ?? null}
							rowClassName="hover:bg-slate-900/30"
							sx={{
								'& .MuiDataGrid-virtualScroller': {
									overflowY: 'auto',
								},
							}}
						/>
					</CommonCard>
				</div>
			) : null}
			{tab === 'modelLayer' ? (
				<div className="mt-2 flex min-h-0 flex-1 flex-col">
					<CommonTree
						type="checkbox"
						className="min-h-0 flex-1"
						items={MODEL_EDITOR_LAYER_TREE_ITEMS}
							options={{
								radius: 0,
								outline: true,
								outlineColor: 'rgba(110, 185, 255, 0.24)',
								itemChildrenIndentation: 22,
								defaultExpandedItems: ['NODES', 'LINKS'],
								selectedItems: selectedModelLayerSeq,
								onSelectedItemsChange: handleModelLayerSelectionChange,
							}}
						/>
				</div>
			) : null}
			{isExtraTabSelected ? renderExtraTab?.(tab) : null}
		</CommonTabs>
	);
}

export { buildLayerTableRowFromFeature };
export default LayerFeatureTablePanel;
