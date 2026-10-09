import {
	INITIAL_STATUS_VALUE_SEQ_BY_OBJECT_TYPE,
	MODEL_EDITOR_RIGHT_TAB_ITEM_SEQ,
	MODEL_EDITOR_SELECT_MENU_PROPS,
	NESTED_PROPERTY_EDITOR_TITLE_BY_KEY,
	NESTED_PROPERTY_FIELD_SEQ_BY_KEY,
	NUMERIC_PROPERTY_KEY_SET,
	OBJECT_PROPERTY_LABEL_BY_KEY,
	OBJECT_TYPE_LABEL_BY_KEY,
	OBJ_TYPE_LAYER_NAME,
	OPTION_ENUM_VALUE_SEQ_BY_KEY,
	PROPERTY_ENUM_VALUE_SEQ_BY_KEY,
	PROPERTY_FIELD_KEYS_BY_OBJECT_TYPE,
	READ_ONLY_PROPERTY_KEY_SET,
	REQUIRED_PROPERTY_KEY_SEQ_BY_OBJECT_TYPE,
} from '@/consts/index.js';
import CommonModal from '@/web/components/CommonModal.jsx';
import CommonButton from '@/web/components/common/CommonButton.jsx';
import CommonInput from '@/web/components/common/CommonInput.jsx';
import CommonSelect from '@/web/components/common/CommonSelect.jsx';
import CommonTabs from '@/web/components/common/CommonTabs.jsx';
import TextareaAutosize from '@mui/material/TextareaAutosize';
import { useMemo, useState } from 'react';
import { IoTrashOutline } from 'react-icons/io5';

function buildPropertyFieldSeq(selectedFeature) {
	if (!selectedFeature) return [];
	const objectType = String(
		selectedFeature.objectType ??
			selectedFeature._rawProperties?.objectType ??
			OBJ_TYPE_LAYER_NAME[selectedFeature._layerName] ??
			''
	).toLowerCase();
	const schemaKeys = PROPERTY_FIELD_KEYS_BY_OBJECT_TYPE[objectType] ?? [];
	const fieldKeySet = new Set(schemaKeys);
	const extraKeys = Object.keys(selectedFeature).filter(
		key =>
			key !== 'rowKey' &&
			!key.startsWith('_') &&
			!(key === 'id' && selectedFeature.featureId != null) &&
			!fieldKeySet.has(key)
	);

	return [...schemaKeys, ...extraKeys]
		.filter(
			key =>
				schemaKeys.includes(key) ||
				key === 'featureId' ||
				key in selectedFeature ||
				key in (selectedFeature._rawProperties ?? {})
		)
		.map(key => ({
			key,
			label: OBJECT_PROPERTY_LABEL_BY_KEY[key] ?? key,
			value:
				key === 'featureId'
					? (selectedFeature.featureId ?? selectedFeature._featureId ?? selectedFeature.id ?? '')
					: (selectedFeature._rawProperties?.[key] ?? selectedFeature[key] ?? ''),
			isNested: Boolean(NESTED_PROPERTY_FIELD_SEQ_BY_KEY[key]),
		}));
}

function isBlankValue(value) {
	return value === null || value === undefined || String(value).trim() === '';
}

function hasWhitespaceValue(value) {
	return typeof value === 'string' && /\s/.test(value);
}

function isWhitespaceRestrictedKey(key) {
	return ['featureId', 'id'].includes(key);
}

function isNumberLikeValue(value) {
	if (isBlankValue(value)) return true;
	return Number.isFinite(Number(value));
}

function getSelectedObjectType(selectedFeature) {
	return String(
		selectedFeature?.objectType ??
			selectedFeature?._rawProperties?.objectType ??
			OBJ_TYPE_LAYER_NAME[selectedFeature?._layerName] ??
			''
	).toLowerCase();
}

function formatEnumErrorMessage(valueSeq) {
	return `허용값: ${valueSeq.join(', ')}`;
}

const ENUM_LABEL_BY_VALUE = {
	CONCEN: '농도',
	MASS: '질량주입',
	FLOWPACED: '유량비례',
	SETPOINT: '목표농도',
	YES: '예',
	NO: '아니오',
	FULL: '전체',
	MIXED: '완전혼합',
	'2COMP': '2구획 혼합',
	FIFO: '선입선출',
	LIFO: '후입선출',
	OPEN: '열림',
	CLOSED: '닫힘',
	CV: '체크밸브',
	PRV: '감압밸브',
	PSV: '압력유지밸브',
	PBV: '압력차단밸브',
	FCV: '유량제어밸브',
	TCV: '조절제어밸브',
	GPV: '범용밸브',
	'CFS': '세제곱피트/초',
	GPM: '갤런/분',
	MGD: '백만갤런/일',
	IMGD: '백만임페리얼갤런/일',
	AFD: '에이커피트/일',
	LPS: '리터/초',
	LPM: '리터/분',
	MLD: '백만리터/일',
	CMH: '세제곱미터/시간',
	CMD: '세제곱미터/일',
	'H-W': 'Hazen-Williams',
	'D-W': 'Darcy-Weisbach',
	'C-M': 'Chezy-Manning',
	STOP: '중지',
	CONTINUE: '계속',
	DDA: '수요기반',
	PDA: '압력기반',
	NONE: '없음',
	CHEMICAL: '화학물질',
	AGE: '수령',
	TRACE: '추적',
	AVERAGED: '평균',
	MINIMUM: '최소',
	MAXIMUM: '최대',
	RANGE: '범위',
	PUMP: '펌프',
	EFFICIENCY: '효율',
	VOLUME: '부피',
	HEADLOSS: '손실수두',
	0: '0차 반응',
	1: '1차 반응',
	2: '2차 반응',
};

function formatSelectOptionLabel(value) {
	const normalizedValue = String(value ?? '');
	const continueTrialMatch = normalizedValue.match(/^CONTINUE\s+(\d+)$/i);
	if (continueTrialMatch) {
		return `계속(${continueTrialMatch[1]}회 추가 반복) (${normalizedValue})`;
	}

	const label = ENUM_LABEL_BY_VALUE[normalizedValue];
	return label ? `${label} (${normalizedValue})` : normalizedValue;
}

function buildValueSelectOptions(valueSeq, { includeEmpty = true } = {}) {
	const optionSeq = valueSeq.map(value => ({
		value,
		label: formatSelectOptionLabel(value),
	}));

	return includeEmpty ? [{ value: '', label: '없음' }, ...optionSeq] : optionSeq;
}

function ensureCurrentSelectOption(optionSeq, value) {
	if (isBlankValue(value)) return optionSeq;
	const normalizedValue = String(value);
	if (optionSeq.some(option => String(option.value) === normalizedValue)) return optionSeq;
	return [...optionSeq, { value: normalizedValue, label: normalizedValue }];
}

function normalizeSelectValue(value) {
	return value === null || value === undefined ? '' : String(value);
}

function resolveSelectChangeValue(value) {
	return value === '' ? null : value;
}

function getObjectPropertyEnumValueSeq(key, selectedFeature) {
	if (key === 'initialStatus') {
		return INITIAL_STATUS_VALUE_SEQ_BY_OBJECT_TYPE[getSelectedObjectType(selectedFeature)] ?? [];
	}

	return PROPERTY_ENUM_VALUE_SEQ_BY_KEY[key] ?? [];
}

function validatePropertyValue(key, value, selectedFeature) {
	const objectType = getSelectedObjectType(selectedFeature);
	const requiredKeySeq = REQUIRED_PROPERTY_KEY_SEQ_BY_OBJECT_TYPE[objectType] ?? [];

	if (requiredKeySeq.includes(key) && isBlankValue(value)) {
		return '필수 입력값입니다.';
	}

	if (isWhitespaceRestrictedKey(key) && hasWhitespaceValue(value)) {
		return '공백은 입력할 수 없습니다.';
	}

	if (key === 'initialStatus') {
		const valueSeq = INITIAL_STATUS_VALUE_SEQ_BY_OBJECT_TYPE[objectType] ?? [];
		if (!isBlankValue(value) && valueSeq.length > 0 && !valueSeq.includes(String(value).toUpperCase())) {
			return formatEnumErrorMessage(valueSeq);
		}
	}

	if (key === 'setting' && objectType === 'valve') {
		const valveType = String(selectedFeature?.type ?? selectedFeature?._rawProperties?.type ?? '').toUpperCase();
		if (valveType !== 'GPV' && !isNumberLikeValue(value)) {
			return '숫자만 입력할 수 있습니다.';
		}
	}

	if (NUMERIC_PROPERTY_KEY_SET.has(key) && !isNumberLikeValue(value)) {
		return '숫자만 입력할 수 있습니다.';
	}

	if (key === 'mixingFraction' && !isBlankValue(value)) {
		const numberValue = Number(value);
		if (Number.isFinite(numberValue) && (numberValue < 0 || numberValue > 1)) {
			return '0부터 1 사이의 값을 입력하세요.';
		}
	}

	const enumValueSeq = PROPERTY_ENUM_VALUE_SEQ_BY_KEY[key];
	if (!isBlankValue(value) && enumValueSeq && !enumValueSeq.includes(String(value).toUpperCase())) {
		return formatEnumErrorMessage(enumValueSeq);
	}

	return '';
}

function validateNestedPropertyField(parentKey, key, value) {
	if (isWhitespaceRestrictedKey(key) && hasWhitespaceValue(value)) {
		return '공백은 입력할 수 없습니다.';
	}

	if (parentKey === 'sourceQuality' && key === 'sourceType') {
		return validatePropertyValue(key, value, null);
	}

	if (
		(parentKey === 'sourceQuality' && key === 'sourceQuality') ||
		(parentKey === 'demandCategories' && key === 'baseDemand')
	) {
		if (!isNumberLikeValue(value)) {
			return '숫자만 입력할 수 있습니다.';
		}
	}

	return '';
}

function buildNestedPropertyErrorMap(parentKey, draft, fieldSeq) {
	return Object.fromEntries(
		fieldSeq
			.map(item => [item.key, validateNestedPropertyField(parentKey, item.key, draft[item.key])])
			.filter(([, errorMessage]) => errorMessage)
	);
}

function createEmptyDemandCategory() {
	return {
		baseDemand: '',
		timePattern: '',
		category: '',
	};
}

function normalizeDemandCategoryRow(value) {
	return {
		baseDemand: value?.baseDemand ?? '',
		timePattern: value?.timePattern ?? '',
		category: value?.category ?? '',
	};
}

function isDemandCategoryRowEmpty(row) {
	return ['baseDemand', 'timePattern', 'category'].every(key => String(row?.[key] ?? '').trim() === '');
}

function normalizeDemandCategoryDraftSeq(value) {
	const parsedValue = parseNestedPropertyValue(value);
	if (Array.isArray(parsedValue)) return parsedValue.map(normalizeDemandCategoryRow);
	if (parsedValue && typeof parsedValue === 'object') return [normalizeDemandCategoryRow(parsedValue)];
	return [];
}

function trimTrailingEmptyDemandCategories(rowSeq) {
	const nextRowSeq = Array.isArray(rowSeq) ? rowSeq.map(normalizeDemandCategoryRow) : [];
	let lastFilledIndex = nextRowSeq.length - 1;

	while (lastFilledIndex >= 0 && isDemandCategoryRowEmpty(nextRowSeq[lastFilledIndex])) {
		lastFilledIndex -= 1;
	}

	return nextRowSeq.slice(0, lastFilledIndex + 1);
}

function getVisibleDemandCategoryDraftSeq(rowSeq) {
	const trimmedRowSeq = trimTrailingEmptyDemandCategories(rowSeq);
	return [...trimmedRowSeq, createEmptyDemandCategory()];
}

function resolveDemandCategoryValueForApply(rowSeq) {
	return trimTrailingEmptyDemandCategories(rowSeq)
		.filter(row => !isDemandCategoryRowEmpty(row))
		.map(row => ({
			baseDemand: row.baseDemand === '' ? null : row.baseDemand,
			timePattern: row.timePattern === '' ? null : row.timePattern,
			category: row.category === '' ? null : row.category,
		}));
}

function buildDemandCategoryErrorMap(rowSeq, fieldSeq) {
	return Object.fromEntries(
		(Array.isArray(rowSeq) ? rowSeq : []).flatMap((row, rowIndex) => {
			if (isDemandCategoryRowEmpty(row)) return [];

			return fieldSeq
				.map(field => [
					`${rowIndex}-${field.key}`,
					validateNestedPropertyField('demandCategories', field.key, row[field.key]),
				])
				.filter(([, errorMessage]) => errorMessage);
		})
	);
}

function parseNestedPropertyValue(value) {
	if (Array.isArray(value)) return value;
	if (value && typeof value === 'object') return value;
	if (typeof value !== 'string' || value.trim() === '') return null;

	try {
		return JSON.parse(value);
	} catch {
		return null;
	}
}

function createNestedPropertyDraft(propertyKey, value) {
	const parsedValue = parseNestedPropertyValue(value);
	const objectValue = Array.isArray(parsedValue) ? (parsedValue[0] ?? {}) : (parsedValue ?? {});

	if (propertyKey === 'sourceQuality') {
		return {
			sourceQuality: objectValue.sourceQuality ?? '',
			qualityPattern: objectValue.qualityPattern ?? '',
			sourceType: objectValue.sourceType ?? 'CONCEN',
		};
	}

	if (propertyKey === 'demandCategories') {
		return {
			baseDemand: objectValue.baseDemand ?? '',
			timePattern: objectValue.timePattern ?? '',
			category: objectValue.category ?? '',
		};
	}

	return { ...objectValue };
}

function hasNestedPropertyValidationError(propertyKey, value, fieldSeq) {
	if (propertyKey === 'demandCategories') {
		return Object.keys(buildDemandCategoryErrorMap(normalizeDemandCategoryDraftSeq(value), fieldSeq)).length > 0;
	}

	return Object.keys(buildNestedPropertyErrorMap(propertyKey, createNestedPropertyDraft(propertyKey, value), fieldSeq)).length > 0;
}

function resolveNestedPropertyValue(propertyKey, draft, currentValue) {
	const nextValue = Object.fromEntries(Object.entries(draft).map(([key, value]) => [key, value === '' ? null : value]));
	const parsedCurrentValue = parseNestedPropertyValue(currentValue);

	if (propertyKey === 'demandCategories' || Array.isArray(parsedCurrentValue)) {
		return [nextValue];
	}

	return nextValue;
}

function formatNestedPropertySummary(propertyKey, value) {
	const parsedValue = parseNestedPropertyValue(value);
	if (!parsedValue) return '';
	if (Array.isArray(parsedValue)) return parsedValue.length > 0 ? `${parsedValue.length}개 항목` : '';

	const fieldSeq = NESTED_PROPERTY_FIELD_SEQ_BY_KEY[propertyKey] ?? [];
	return fieldSeq
		.map(field => parsedValue[field.key])
		.filter(item => item !== null && item !== undefined && item !== '')
		.join(' / ');
}

function normalizePatternMultiplierSeq(value) {
	if (!Array.isArray(value)) return [];
	return value.map(item => String(item ?? ''));
}

function getVisiblePatternMultiplierSeq(value) {
	const multiplierSeq = normalizePatternMultiplierSeq(value);
	const lastFilledIndex = multiplierSeq.reduce((lastIndex, item, index) => (String(item).trim() ? index : lastIndex), -1);
	const visibleCount = Math.max(24, lastFilledIndex + 2);

	return Array.from({ length: visibleCount }, (_, index) => multiplierSeq[index] ?? '');
}

function normalizeCurvePointSeq(value) {
	if (!Array.isArray(value)) return [];
	return value.map(point => ({
		x: String(point?.x ?? ''),
		y: String(point?.y ?? ''),
	}));
}

function getVisibleCurvePointSeq(value) {
	const pointSeq = normalizeCurvePointSeq(value);
	return [...pointSeq, { x: '', y: '' }];
}

function formatReferenceOption(value) {
	return {
		value: String(value ?? ''),
		label: String(value ?? ''),
	};
}

function uniqueOptionSeq(valueSeq) {
	const seenValueSet = new Set();
	return valueSeq
		.map(value => String(value ?? '').trim())
		.filter(Boolean)
		.filter(value => {
			if (seenValueSet.has(value)) return false;
			seenValueSet.add(value);
			return true;
		})
		.map(formatReferenceOption);
}

function getFeatureIdFromGeoJson(feature) {
	return feature?.properties?.id ?? feature?.properties?.ID ?? feature?.properties?.name ?? feature?.id;
}

function getNodeReferenceOptions(networkDetail) {
	return uniqueOptionSeq(networkDetail?.layers?.nodeLayer?.features?.map(getFeatureIdFromGeoJson) ?? []);
}

function getPatternReferenceOptions(networkDetail) {
	return uniqueOptionSeq((networkDetail?.sections?.PATTERNS ?? []).map(pattern => pattern?.id));
}

function getCurveReferenceOptions(networkDetail, curveType) {
	const normalizedCurveType = String(curveType ?? '').toUpperCase();
	return uniqueOptionSeq(
		(networkDetail?.sections?.CURVES ?? [])
			.filter(curve => String(curve?.curveType ?? '').toUpperCase() === normalizedCurveType)
			.map(curve => curve?.id)
	);
}

function withEmptyOption(optionSeq) {
	return [{ value: '', label: '없음' }, ...optionSeq];
}

function getReferenceSelectOptions(key, selectedFeature, networkDetail) {
	if (!networkDetail) return [];

	if (
		[
			'demandPattern',
			'headPattern',
			'pattern',
			'pricePattern',
			'qualityPattern',
			'defaultPattern',
			'timePattern',
		].includes(key)
	) {
		return withEmptyOption(getPatternReferenceOptions(networkDetail));
	}

	if (['startNode', 'endNode', 'anchorNode', 'traceNode'].includes(key)) {
		return withEmptyOption(getNodeReferenceOptions(networkDetail));
	}

	if (key === 'volumeCurve') return withEmptyOption(getCurveReferenceOptions(networkDetail, 'VOLUME'));
	if (key === 'pumpCurve') return withEmptyOption(getCurveReferenceOptions(networkDetail, 'PUMP'));
	if (key === 'efficiencyCurve') return withEmptyOption(getCurveReferenceOptions(networkDetail, 'EFFICIENCY'));

	if (key === 'setting' && getSelectedObjectType(selectedFeature) === 'valve') {
		const valveType = String(selectedFeature?.type ?? selectedFeature?._rawProperties?.type ?? '').toUpperCase();
		if (valveType === 'GPV') return withEmptyOption(getCurveReferenceOptions(networkDetail, 'HEADLOSS'));
	}

	return [];
}

function getObjectPropertySelectOptions(key, selectedFeature, networkDetail, currentValue) {
	const enumValueSeq = getObjectPropertyEnumValueSeq(key, selectedFeature);
	if (enumValueSeq.length > 0) {
		return ensureCurrentSelectOption(buildValueSelectOptions(enumValueSeq), currentValue);
	}

	const referenceOptionSeq = getReferenceSelectOptions(key, selectedFeature, networkDetail);
	if (referenceOptionSeq.length === 0) return [];
	return ensureCurrentSelectOption(referenceOptionSeq, currentValue);
}

function getNestedFieldSelectOptions(field, selectedFeature, networkDetail, currentValue) {
	const explicitOptionSeq = field?.options ?? [];
	if (explicitOptionSeq.length > 0) {
		return ensureCurrentSelectOption(explicitOptionSeq, currentValue);
	}

	const referenceOptionSeq = getReferenceSelectOptions(field?.key, selectedFeature, networkDetail);
	if (referenceOptionSeq.length === 0) return [];
	return ensureCurrentSelectOption(referenceOptionSeq, currentValue);
}

const OPTION_GROUP_LABEL_BY_KEY = {
	hydraulics: '수리옵션',
	quality: '수질옵션',
	reactions: '반응',
	times: '시간',
	energy: '에너지',
};

const OPTION_FIELD_LABEL_BY_KEY = {
	flowUnits: '유량 단위',
	headlossFormula: '손실수두 공식',
	specificGravity: '비중',
	relativeViscosity: '상대 점도',
	maximumTrials: '최대 반복 횟수',
	accuracy: '정확도',
	checkFreq: '검사 주기',
	maxCheck: '최대 검사 횟수',
	ifUnbalanced: '미수렴 처리',
	demandMultiplier: '수요 배율',
	demandModel: '수요 모델',
	minimumPressure: '최소 압력',
	requiredPressure: '요구 압력',
	pressureExponent: '압력 지수',
	emitterExponent: '이미터 지수',
	parameter: '수질 해석 유형',
	relativeDiffusivity: '상대 확산도',
	qualityTolerance: '수질 허용오차',
	bulkReactionOrder: '벌크 반응 차수',
	tankReactionOrder: '탱크 반응 차수',
	wallReactionOrder: '벽면 반응 차수',
	globalBulkCoefficient: '전역 벌크 계수',
	globalWallCoefficient: '전역 관벽 계수',
	limitingConcentration: '제한 농도',
	wallCoefficientCorrelation: '관벽 계수 상관값',
	totalDuration: '총 지속 시간',
	hydraulicTimeStep: '수리 시간 간격',
	qualityTimeStep: '수질 시간 간격',
	patternTimeStep: '패턴 시간 간격',
	patternStartTime: '패턴 시작 시간',
	reportingTimeStep: '보고 시간 간격',
	reportStartTime: '보고 시작 시간',
	startingTimeOfDay: '시작 시각',
	ruleTimeStep: '규칙 시간 간격',
	statistic: '통계 처리',
	pumpEfficiency: '펌프 효율',
	energyPrice: '에너지 단가',
	demandCharge: '수요 요금',
	pumps: '펌프',
	id: '아이디',
	efficiencyCurve: '효율 곡선',
};

function getOptionGroupLabel(groupKey) {
	return OPTION_GROUP_LABEL_BY_KEY[groupKey] ?? groupKey;
}

function getOptionFieldLabel(fieldKey) {
	return OPTION_FIELD_LABEL_BY_KEY[fieldKey] ?? fieldKey;
}

function formatOptionFieldPathLabel(pathLabel) {
	if (!pathLabel) return '';

	const pumpMatch = pathLabel.match(/^pumps\[(\d+)\]\.(.+)$/);
	if (pumpMatch) {
		return `펌프 ${Number(pumpMatch[1]) + 1} ${getOptionFieldLabel(pumpMatch[2])}`;
	}

	return pathLabel
		.split('.')
		.map(pathItem => {
			const arrayMatch = pathItem.match(/^(.+)\[(\d+)]$/);
			if (arrayMatch) {
				return `${getOptionFieldLabel(arrayMatch[1])} ${Number(arrayMatch[2]) + 1}`;
			}
			return getOptionFieldLabel(pathItem);
		})
		.join(' / ');
}

function formatOptionModalFieldLabel(entryLabel, groupKey) {
	if (!groupKey) return formatOptionFieldPathLabel(entryLabel);
	if (entryLabel === groupKey) return getOptionGroupLabel(groupKey);
	if (entryLabel.startsWith(`${groupKey}.`)) return formatOptionFieldPathLabel(entryLabel.slice(groupKey.length + 1));
	if (entryLabel.startsWith(`${groupKey}[`)) return formatOptionFieldPathLabel(entryLabel.slice(groupKey.length));
	return formatOptionFieldPathLabel(entryLabel);
}

function getOptionEntryFieldKey(entry) {
	const pathSeq = entry?.pathSeq ?? [];
	const lastPath = pathSeq[pathSeq.length - 1];
	return typeof lastPath === 'string' ? lastPath : '';
}

function getOptionEntrySelectOptions(entry, networkDetail) {
	const fieldKey = getOptionEntryFieldKey(entry);
	const enumValueSeq = OPTION_ENUM_VALUE_SEQ_BY_KEY[fieldKey] ?? OPTION_ENUM_VALUE_SEQ_BY_KEY[fieldKey?.toLowerCase()] ?? [];
	if (enumValueSeq.length > 0) {
		return ensureCurrentSelectOption(buildValueSelectOptions(enumValueSeq), entry?.value);
	}

	if (fieldKey === 'traceNode') {
		return ensureCurrentSelectOption(withEmptyOption(getNodeReferenceOptions(networkDetail)), entry?.value);
	}

	if (['defaultPattern', 'pricePattern', 'qualityPattern'].includes(fieldKey)) {
		return ensureCurrentSelectOption(withEmptyOption(getPatternReferenceOptions(networkDetail)), entry?.value);
	}

	if (fieldKey === 'efficiencyCurve') {
		return ensureCurrentSelectOption(withEmptyOption(getCurveReferenceOptions(networkDetail, 'EFFICIENCY')), entry?.value);
	}

	return [];
}

function OptionGroupEditorDialog({ open, onOpenChange, group, networkDetail, onPropertyChange }) {
	const entrySeq = group?.entrySeq ?? [];

	return (
		<CommonModal
			open={open}
			onOpenChange={onOpenChange}
			title={getOptionGroupLabel(group?.key) || '옵션'}
			showFooter={false}
			contentClassName="w-[min(92vw,720px)]"
			headerClassName="px-4 py-3"
			bodyClassName="max-h-[70vh] overflow-y-auto px-4 py-4"
			titleClassName="text-[18px]"
			closeButtonClassName="h-7 w-7"
		>
			<div className="overflow-hidden border border-slate-700/70">
				{entrySeq.length === 0 ? (
					<div className="flex min-h-[120px] items-center justify-center px-3 py-4 text-[12px] text-slate-400">
						옵션 데이터가 없습니다.
					</div>
				) : null}
				{entrySeq.map(entry => (
					<div
						key={entry.label}
						className="grid grid-cols-[180px_minmax(0,1fr)] border-b border-slate-700/70 last:border-b-0"
					>
						<div className="flex min-w-0 items-center break-all bg-[#153b72] px-3 py-2 text-[12px] font-medium text-slate-100">
							{formatOptionModalFieldLabel(entry.label, group?.key)}
						</div>
						<div className="bg-slate-950/15 p-1.5">
							{getOptionEntrySelectOptions(entry, networkDetail).length > 0 ? (
								<CommonSelect
									value={normalizeSelectValue(entry.value)}
									options={getOptionEntrySelectOptions(entry, networkDetail)}
									onChange={value =>
										onPropertyChange?.('optionValue', {
											pathSeq: entry.pathSeq,
											value: resolveSelectChangeValue(value),
										})
									}
									className="model-editor-property-input w-full"
									menuProps={MODEL_EDITOR_SELECT_MENU_PROPS}
								/>
							) : (
								<CommonInput
									value={entry.value}
									onChange={value =>
										onPropertyChange?.('optionValue', {
											pathSeq: entry.pathSeq,
											value,
										})
									}
									className="model-editor-property-input w-full"
								/>
							)}
						</div>
					</div>
				))}
			</div>
		</CommonModal>
	);
}

function NestedPropertyEditorDialog({ open, onOpenChange, selectedFeature, networkDetail, field, onApply }) {
	const [draft, setDraft] = useState(() => createNestedPropertyDraft(field?.key, field?.value));
	const [demandCategoryDraftSeq, setDemandCategoryDraftSeq] = useState(() =>
		normalizeDemandCategoryDraftSeq(field?.value)
	);
	const objectType = String(
		selectedFeature?.objectType ??
			selectedFeature?._rawProperties?.objectType ??
			OBJ_TYPE_LAYER_NAME[selectedFeature?._layerName] ??
			''
	).toLowerCase();
	const fieldSeq = NESTED_PROPERTY_FIELD_SEQ_BY_KEY[field?.key] ?? [];
	const titleSubject = OBJECT_TYPE_LABEL_BY_KEY[objectType] ?? '객체';
	const titleTarget = NESTED_PROPERTY_EDITOR_TITLE_BY_KEY[field?.key] ?? field?.label ?? '속성';
	const errorMap = buildNestedPropertyErrorMap(field?.key, draft, fieldSeq);
	const isDemandCategoryEditor = field?.key === 'demandCategories';
	const visibleDemandCategoryDraftSeq = getVisibleDemandCategoryDraftSeq(demandCategoryDraftSeq);
	const demandCategoryErrorMap = buildDemandCategoryErrorMap(visibleDemandCategoryDraftSeq, fieldSeq);
	const hasValidationError = isDemandCategoryEditor
		? Object.keys(demandCategoryErrorMap).length > 0
		: Object.keys(errorMap).length > 0;

	const handleDraftChange = (key, value) => {
		setDraft(prev => ({
			...prev,
			[key]: value,
		}));
	};

	const handleDemandCategoryChange = (rowIndex, key, value) => {
		const nextRowSeq = getVisibleDemandCategoryDraftSeq(demandCategoryDraftSeq);
		nextRowSeq[rowIndex] = {
			...(nextRowSeq[rowIndex] ?? createEmptyDemandCategory()),
			[key]: value,
		};

		const nextDraftSeq = trimTrailingEmptyDemandCategories(nextRowSeq);
		setDemandCategoryDraftSeq(nextDraftSeq);
		onApply?.(resolveDemandCategoryValueForApply(nextDraftSeq));
	};

	const handleApply = () => {
		if (isDemandCategoryEditor) {
			onApply?.(resolveDemandCategoryValueForApply(demandCategoryDraftSeq));
			return;
		}

		onApply?.(resolveNestedPropertyValue(field?.key, draft, field?.value));
	};

	return (
		<CommonModal
			open={open}
			onOpenChange={onOpenChange}
			title={`${titleSubject}에 대한 ${titleTarget} 편집기 1`}
			actionLabel="Ok"
			showCancel={false}
			showFooter={!isDemandCategoryEditor}
			closeOnAction={true}
			actionDisabled={hasValidationError}
			onMove={handleApply}
			contentClassName={isDemandCategoryEditor ? 'w-[min(94vw,760px)]' : 'w-[min(92vw,420px)]'}
			headerClassName="px-4 py-3"
			bodyClassName="px-4 py-4"
			footerClassName="px-4 pb-4 pt-0"
			titleClassName="text-[16px]"
			closeButtonClassName="h-7 w-7"
		>
			{isDemandCategoryEditor ? (
				<div className="overflow-hidden border border-[rgba(110,185,255,0.28)]">
					<div className="grid grid-cols-[56px_repeat(3,minmax(0,1fr))] border-b border-[rgba(110,185,255,0.24)] bg-[#153b72]">
						<div className="border-r border-[rgba(110,185,255,0.22)] px-2.5 py-2 text-center text-[12px] font-semibold text-sky-50">
							번호
						</div>
						{fieldSeq.map(item => (
							<div
								key={item.key}
								className="border-r border-[rgba(110,185,255,0.22)] px-2.5 py-2 text-center text-[12px] font-semibold text-sky-50 last:border-r-0"
							>
								{item.label}
							</div>
						))}
					</div>
					<div className="max-h-[52vh] overflow-y-auto">
						{visibleDemandCategoryDraftSeq.map((row, rowIndex) => (
							<div
								key={rowIndex}
								className="grid grid-cols-[56px_repeat(3,minmax(0,1fr))] border-b border-[rgba(110,185,255,0.16)] last:border-b-0"
							>
								<div className="flex items-center justify-center border-r border-[rgba(110,185,255,0.16)] bg-slate-950/20 px-2 py-1.5 text-[12px] text-slate-300">
									{rowIndex + 1}
								</div>
								{fieldSeq.map(item => (
									<div
										key={item.key}
										className="border-r border-[rgba(110,185,255,0.16)] bg-slate-950/15 p-1.5 last:border-r-0"
									>
										{getNestedFieldSelectOptions(item, selectedFeature, networkDetail, row[item.key]).length > 0 ? (
											<CommonSelect
												value={normalizeSelectValue(row[item.key])}
												options={getNestedFieldSelectOptions(item, selectedFeature, networkDetail, row[item.key])}
												onChange={value =>
													handleDemandCategoryChange(rowIndex, item.key, resolveSelectChangeValue(value))
												}
												className="model-editor-property-input w-full"
												menuProps={MODEL_EDITOR_SELECT_MENU_PROPS}
												error={Boolean(demandCategoryErrorMap[`${rowIndex}-${item.key}`])}
												helperText={demandCategoryErrorMap[`${rowIndex}-${item.key}`] || undefined}
											/>
										) : (
											<CommonInput
												value={row[item.key] ?? ''}
												onChange={value => handleDemandCategoryChange(rowIndex, item.key, value)}
												className="model-editor-property-input w-full"
												error={Boolean(demandCategoryErrorMap[`${rowIndex}-${item.key}`])}
												helperText={demandCategoryErrorMap[`${rowIndex}-${item.key}`] || undefined}
											/>
										)}
									</div>
								))}
							</div>
						))}
					</div>
				</div>
			) : (
				<div className="overflow-hidden border border-[rgba(110,185,255,0.28)]">
					{fieldSeq.map(item => (
						<div
							key={item.key}
							className="grid grid-cols-[110px_minmax(0,1fr)] border-b border-[rgba(110,185,255,0.18)] last:border-b-0"
						>
							<div className="flex items-center bg-[#153b72] px-2.5 py-2 text-[12px] font-semibold text-sky-50">
								{item.label}
							</div>
							<div className="bg-slate-950/15 p-1.5">
								{getNestedFieldSelectOptions(item, selectedFeature, networkDetail, draft[item.key]).length > 0 ? (
									<CommonSelect
										value={normalizeSelectValue(draft[item.key])}
										options={getNestedFieldSelectOptions(item, selectedFeature, networkDetail, draft[item.key])}
										onChange={value => handleDraftChange(item.key, resolveSelectChangeValue(value))}
										className="model-editor-property-input w-full"
										menuProps={MODEL_EDITOR_SELECT_MENU_PROPS}
										error={Boolean(errorMap[item.key])}
										helperText={errorMap[item.key] || undefined}
									/>
								) : (
									<CommonInput
										value={draft[item.key] ?? ''}
										onChange={value => handleDraftChange(item.key, value)}
										className="model-editor-property-input w-full"
										error={Boolean(errorMap[item.key])}
										helperText={errorMap[item.key] || undefined}
									/>
								)}
							</div>
						</div>
					))}
				</div>
			)}
		</CommonModal>
	);
}

function NestedPropertyField({ selectedFeature, networkDetail, field, onPropertyChange }) {
	const [isOpen, setIsOpen] = useState(false);
	const summary = formatNestedPropertySummary(field.key, field.value);
	const nestedFieldSeq = NESTED_PROPERTY_FIELD_SEQ_BY_KEY[field.key] ?? [];
	const hasValidationError = hasNestedPropertyValidationError(field.key, field.value, nestedFieldSeq);

	return (
		<>
			<div
				className={['model-editor-object-field', hasValidationError ? 'model-editor-object-field--error' : ''].join(' ')}
			>
				<div className="model-editor-object-field__display" title={summary}>
					{summary}
				</div>
				<CommonButton
					size="icon-xs"
					variant="ghost"
					ariaLabel={`${field.label} 편집`}
					className="model-editor-object-field__button"
					onClick={() => setIsOpen(true)}
				>
					<span className="text-[15px] leading-none">☰</span>
				</CommonButton>
			</div>
			{isOpen ? (
				<NestedPropertyEditorDialog
					open={isOpen}
					onOpenChange={setIsOpen}
					selectedFeature={selectedFeature}
					networkDetail={networkDetail}
					field={field}
					onApply={value => onPropertyChange?.(field.key, value)}
				/>
			) : null}
		</>
	);
}

function FeaturePropertyPanel({ selectedFeature, networkDetail, onPropertyChange, validatePropertyChange }) {
	const [tab, setTab] = useState(MODEL_EDITOR_RIGHT_TAB_ITEM_SEQ[0].v);
	const [draftValueState, setDraftValueState] = useState({ selectedFeatureKey: '', valueByKey: {} });
	const [externalErrorState, setExternalErrorState] = useState({ selectedFeatureKey: '', errorByKey: {} });
	const [selectedOptionGroupState, setSelectedOptionGroupState] = useState({ selectedFeatureKey: '', groupKey: null });
	const resolvedPropertyFieldSeq = useMemo(() => buildPropertyFieldSeq(selectedFeature), [selectedFeature]);
	const selectedFeatureKey = selectedFeature?.rowKey ?? selectedFeature?._featureIndex ?? '';
	const draftValueByKey =
		draftValueState.selectedFeatureKey === selectedFeatureKey ? draftValueState.valueByKey : {};
	const externalErrorByKey =
		externalErrorState.selectedFeatureKey === selectedFeatureKey ? externalErrorState.errorByKey : {};
	const selectedOptionGroupKey =
		selectedOptionGroupState.selectedFeatureKey === selectedFeatureKey ? selectedOptionGroupState.groupKey : null;
	const isReadOnlyFeature = Boolean(selectedFeature?._isNonVisualSection);
	const isControlSection = selectedFeature?._sectionName === 'CONTROLS';
	const isPatternSection = selectedFeature?._sectionName === 'PATTERNS';
	const isOptionSection = selectedFeature?._sectionName === 'OPTIONS';
	const isCurveSection = selectedFeature?._sectionName === 'CURVES';
	const selectedOptionGroup = useMemo(
		() => (selectedFeature?.optionGroupSeq ?? []).find(group => group.key === selectedOptionGroupKey) ?? null,
		[selectedFeature?.optionGroupSeq, selectedOptionGroupKey]
	);
	const visiblePatternMultiplierSeq = useMemo(
		() => getVisiblePatternMultiplierSeq(selectedFeature?.multiplierSeq),
		[selectedFeature?.multiplierSeq]
	);
	const visibleCurvePointSeq = useMemo(() => getVisibleCurvePointSeq(selectedFeature?.xyDataSeq), [selectedFeature?.xyDataSeq]);

	const handlePropertyInputChange = (field, value) => {
		setDraftValueState(prev => ({
			selectedFeatureKey,
			valueByKey: {
				...(prev.selectedFeatureKey === selectedFeatureKey ? prev.valueByKey : {}),
				[field.key]: value,
			},
		}));

		const errorMessage = validatePropertyValue(field.key, value, selectedFeature);
		if (errorMessage) {
			setExternalErrorState(prev => ({
				selectedFeatureKey,
				errorByKey: {
					...(prev.selectedFeatureKey === selectedFeatureKey ? prev.errorByKey : {}),
					[field.key]: '',
				},
			}));
			return;
		}

		const externalErrorMessage = validatePropertyChange?.(field.key, value) ?? '';
		setExternalErrorState(prev => ({
			selectedFeatureKey,
			errorByKey: {
				...(prev.selectedFeatureKey === selectedFeatureKey ? prev.errorByKey : {}),
				[field.key]: externalErrorMessage,
			},
		}));
		if (externalErrorMessage) return;

		onPropertyChange?.(field.key, value);
	};

	return (
		<div className="flex h-full min-h-0 flex-col overflow-hidden bg-[linear-gradient(180deg,rgba(19,35,67,0.97),rgba(14,29,57,0.98))] text-slate-100">
			<CommonTabs
				className="flex min-h-0 flex-1 flex-col p-2.5"
				contentClassName="flex min-h-0 flex-1 flex-col"
				items={MODEL_EDITOR_RIGHT_TAB_ITEM_SEQ}
				value={tab}
				onChange={setTab}
			>
				{tab === 'modelInfo' ? (
					<div className="mt-2.5 min-h-0 flex-1 overflow-y-auto border border-[rgba(110,185,255,0.24)] bg-slate-950/20">
						{isControlSection ? (
							<div className="flex min-h-[320px] flex-col p-2.5">
								{selectedFeature?._controlType === 'rule' ? (
									<div className="flex flex-col gap-2">
										{(selectedFeature?.ruleSeq ?? []).length === 0 ? (
											<div className="flex min-h-[120px] items-center justify-center px-3 py-4 text-[12px] text-slate-400">
												규칙 제어 데이터가 없습니다.
											</div>
										) : null}
										{(selectedFeature?.ruleSeq ?? []).map(rule => (
											<div
												key={rule.index}
												className="overflow-hidden rounded border border-[rgba(110,185,255,0.32)] bg-slate-950/30"
											>
												<div className="flex items-center justify-between gap-2 border-b border-[rgba(110,185,255,0.24)] bg-[#153b72] px-3 py-1.5">
													<span className="min-w-0 truncate text-[12px] font-semibold text-sky-50">
														{rule.title || `RULE ${rule.id ?? ''}`}
													</span>
													<CommonButton
														text="삭제"
														size="xs"
														variant="destructive"
														Icon={IoTrashOutline}
														iconClassName="h-3.5 w-3.5"
														className="h-6 shrink-0 px-2"
														onClick={() =>
															onPropertyChange?.('deleteRule', {
																index: rule.index,
															})
														}
													/>
												</div>
												<TextareaAutosize
													minRows={8}
													value={rule.content ?? ''}
													onChange={event =>
														onPropertyChange?.('ruleContent', {
															index: rule.index,
															value: event.target.value,
														})
													}
													className="w-full resize-none bg-slate-950/40 p-3 font-mono text-[12px] leading-5 text-sky-50 outline-none"
												/>
											</div>
										))}
										<div className="flex justify-end">
											<CommonButton
												text="규칙 추가"
												size="sm"
												variant="outline"
												onClick={() => onPropertyChange?.('addRule')}
											/>
										</div>
									</div>
								) : (
									<div className="flex flex-col gap-2">
										{(selectedFeature?.simpleSeq ?? []).length === 0 ? (
											<div className="flex min-h-[120px] items-center justify-center px-3 py-4 text-[12px] text-slate-400">
												단순 제어 데이터가 없습니다.
											</div>
										) : null}
										{(selectedFeature?.simpleSeq ?? []).map((simpleContent, index) => (
											<div
												key={index}
												className="overflow-hidden rounded border border-[rgba(110,185,255,0.32)] bg-slate-950/30"
											>
												<div className="flex items-center justify-between gap-2 border-b border-[rgba(110,185,255,0.24)] bg-[#153b72] px-3 py-1.5">
													<span className="min-w-0 truncate text-[12px] font-semibold text-sky-50">
														단순 제어 {index + 1}
													</span>
													<CommonButton
														text="삭제"
														size="xs"
														variant="destructive"
														Icon={IoTrashOutline}
														iconClassName="h-3.5 w-3.5"
														className="h-6 shrink-0 px-2"
														onClick={() =>
															onPropertyChange?.('deleteSimpleControl', {
																index,
															})
														}
													/>
												</div>
												<TextareaAutosize
													minRows={3}
													value={simpleContent ?? ''}
													onChange={event =>
														onPropertyChange?.('simpleContent', {
															index,
															value: event.target.value,
														})
													}
													className="w-full resize-none bg-slate-950/40 p-3 font-mono text-[12px] leading-5 text-sky-50 outline-none"
												/>
											</div>
										))}
										<div className="flex justify-end">
											<CommonButton
												text="규칙 추가"
												size="sm"
												variant="outline"
												onClick={() => onPropertyChange?.('addSimpleControl')}
											/>
										</div>
									</div>
								)}
							</div>
						) : null}
						{isPatternSection ? (
							<div className="flex flex-col gap-3 p-2.5">
								<div className="grid grid-cols-[100px_minmax(0,1fr)] border border-slate-700/70">
									<div className="flex items-center bg-[#153b72] px-3 py-2 text-[12px] font-medium text-slate-100">
										패턴 아이디
									</div>
									<div className="bg-slate-950/15 p-1.5">
										<CommonInput
											value={selectedFeature?.id ?? ''}
											onChange={value => onPropertyChange?.('id', value)}
											className="model-editor-property-input w-full"
										/>
									</div>
									<div className="flex items-center border-t border-slate-700/70 bg-[#153b72] px-3 py-2 text-[12px] font-medium text-slate-100">
										패턴 설명
									</div>
									<div className="border-t border-slate-700/70 bg-slate-950/15 p-1.5">
										<CommonInput
											value={selectedFeature?.description ?? ''}
											onChange={value => onPropertyChange?.('description', value)}
											className="model-editor-property-input w-full"
										/>
									</div>
								</div>
								<div className="text-[12px] font-semibold text-sky-100">시간 구간</div>
								<div className="grid grid-cols-4 border-l border-t border-slate-700/70">
									{visiblePatternMultiplierSeq.map((periodValue, index) => (
										<div key={index} className="min-w-0 border-b border-r border-slate-700/70">
											<div className="bg-[#153b72] px-2 py-1 text-center text-[11px] font-medium text-slate-100">
												{index + 1}시
											</div>
											<div className="bg-slate-950/15 p-1">
												<CommonInput
													value={periodValue}
													onChange={value =>
														onPropertyChange?.('multiplier', {
															index,
															value,
														})
													}
													className="model-editor-property-input w-full"
												/>
											</div>
										</div>
									))}
								</div>
							</div>
						) : null}
						{isOptionSection ? (
							<div className="flex flex-col gap-1.5 p-2">
								{(selectedFeature?.optionGroupSeq ?? []).length === 0 ? (
									<div className="flex min-h-[120px] items-center justify-center px-3 py-4 text-[12px] text-slate-400">
										옵션 데이터가 없습니다.
									</div>
								) : null}
								{(selectedFeature?.optionGroupSeq ?? []).map(group => (
									<button
										key={group.key}
										type="button"
										className="flex h-9 w-full items-center justify-between gap-3 rounded border border-[rgba(110,185,255,0.24)] bg-slate-950/20 px-3 text-left transition-colors hover:border-sky-300/50 hover:bg-sky-950/30 focus-visible:outline focus-visible:outline-1 focus-visible:outline-sky-300"
										onClick={() =>
											setSelectedOptionGroupState({
												selectedFeatureKey,
												groupKey: group.key,
											})
										}
									>
										<span className="min-w-0 truncate text-[12px] font-medium text-sky-50">
											{getOptionGroupLabel(group.key)}
										</span>
										<span className="min-w-8 rounded bg-slate-800/80 px-2 py-0.5 text-center text-[11px] font-medium text-sky-100/80">
											{group.entryCount}
										</span>
									</button>
								))}
							</div>
						) : null}
						{isCurveSection ? (
							<div className="flex flex-col gap-3 p-2.5">
								<div className="grid grid-cols-[100px_minmax(0,1fr)] border border-slate-700/70">
									<div className="flex items-center bg-[#153b72] px-3 py-2 text-[12px] font-medium text-slate-100">
										커브 아이디
									</div>
									<div className="bg-slate-950/15 p-1.5">
										<CommonInput
											value={selectedFeature?.id ?? ''}
											onChange={value => onPropertyChange?.('id', value)}
											className="model-editor-property-input w-full"
										/>
									</div>
									<div className="flex items-center border-t border-slate-700/70 bg-[#153b72] px-3 py-2 text-[12px] font-medium text-slate-100">
										커브 유형
									</div>
									<div className="border-t border-slate-700/70 bg-slate-950/15 p-1.5">
										<CommonSelect
											value={normalizeSelectValue(selectedFeature?.curveType)}
											options={ensureCurrentSelectOption(
												buildValueSelectOptions(PROPERTY_ENUM_VALUE_SEQ_BY_KEY.curveType),
												selectedFeature?.curveType
											)}
											onChange={value => onPropertyChange?.('curveType', resolveSelectChangeValue(value))}
											className="model-editor-property-input w-full"
											menuProps={MODEL_EDITOR_SELECT_MENU_PROPS}
										/>
									</div>
									<div className="flex items-center border-t border-slate-700/70 bg-[#153b72] px-3 py-2 text-[12px] font-medium text-slate-100">
										커브 설명
									</div>
									<div className="border-t border-slate-700/70 bg-slate-950/15 p-1.5">
										<CommonInput
											value={selectedFeature?.description ?? ''}
											onChange={value => onPropertyChange?.('description', value)}
											className="model-editor-property-input w-full"
										/>
									</div>
								</div>
								<div className="grid grid-cols-[64px_minmax(0,1fr)_minmax(0,1fr)] border-l border-t border-slate-700/70">
									<div className="border-b border-r border-slate-700/70 bg-[#153b72] px-2 py-1 text-center text-[11px] font-medium text-slate-100">
										번호
									</div>
									<div className="border-b border-r border-slate-700/70 bg-[#153b72] px-2 py-1 text-center text-[11px] font-medium text-slate-100">
										유량
									</div>
									<div className="border-b border-r border-slate-700/70 bg-[#153b72] px-2 py-1 text-center text-[11px] font-medium text-slate-100">
										양정
									</div>
									{visibleCurvePointSeq.map((point, index) => (
										<div key={index} className="contents">
											<div className="flex items-center justify-center border-b border-r border-slate-700/70 bg-slate-950/15 px-2 py-1 text-[12px] text-slate-300">
												{index + 1}
											</div>
											<div className="border-b border-r border-slate-700/70 bg-slate-950/15 p-1">
												<CommonInput
													value={point.x}
													onChange={value =>
														onPropertyChange?.('curvePoint', {
															index,
															axis: 'x',
															value,
														})
													}
													className="model-editor-property-input w-full"
												/>
											</div>
											<div className="border-b border-r border-slate-700/70 bg-slate-950/15 p-1">
												<CommonInput
													value={point.y}
													onChange={value =>
														onPropertyChange?.('curvePoint', {
															index,
															axis: 'y',
															value,
														})
													}
													className="model-editor-property-input w-full"
												/>
											</div>
										</div>
									))}
								</div>
							</div>
						) : null}
						{!isControlSection &&
						!isPatternSection &&
						!isOptionSection &&
						!isCurveSection &&
						resolvedPropertyFieldSeq.length === 0 ? (
							<div className="flex min-h-[120px] items-center justify-center px-3 py-4 text-[12px] text-slate-400">
								모델 항목을 선택하면 상세 정보가 표시됩니다.
							</div>
						) : null}
						{!isControlSection &&
							!isPatternSection &&
							!isOptionSection &&
							!isCurveSection &&
							resolvedPropertyFieldSeq.map(field => {
								const fieldValue = Object.prototype.hasOwnProperty.call(draftValueByKey, field.key)
									? draftValueByKey[field.key]
									: field.value;
								const errorMessage =
									isReadOnlyFeature || field.isNested
										? ''
										: validatePropertyValue(field.key, fieldValue, selectedFeature) ||
											externalErrorByKey[field.key] ||
											'';

								return (
									<div
										key={field.key}
										className="grid grid-cols-[100px_minmax(0,1fr)] border-b border-slate-700/70 last:border-b-0"
									>
										<div className="flex items-center bg-[#153b72] px-3 py-2 text-[12px] font-medium text-slate-100">
											{field.label}
										</div>
										<div className="bg-slate-950/15 p-1.5">
											{field.isNested ? (
												<NestedPropertyField
													selectedFeature={selectedFeature}
													networkDetail={networkDetail}
													field={field}
													onPropertyChange={onPropertyChange}
												/>
											) : getObjectPropertySelectOptions(field.key, selectedFeature, networkDetail, fieldValue).length > 0 &&
												!isReadOnlyFeature &&
												!READ_ONLY_PROPERTY_KEY_SET.has(field.key) ? (
												<CommonSelect
													value={normalizeSelectValue(fieldValue)}
													options={getObjectPropertySelectOptions(field.key, selectedFeature, networkDetail, fieldValue)}
													onChange={value => handlePropertyInputChange(field, resolveSelectChangeValue(value))}
													className="model-editor-property-input w-full"
													menuProps={MODEL_EDITOR_SELECT_MENU_PROPS}
													error={Boolean(errorMessage)}
													helperText={errorMessage || undefined}
												/>
											) : (
												<CommonInput
													value={fieldValue}
													readOnly={isReadOnlyFeature || READ_ONLY_PROPERTY_KEY_SET.has(field.key)}
													onChange={value => handlePropertyInputChange(field, value)}
													className="model-editor-property-input w-full"
													error={Boolean(errorMessage)}
													helperText={errorMessage || undefined}
												/>
											)}
										</div>
									</div>
								);
							})}
					</div>
				) : null}
				{tab === 'tag' ? (
					<div className="mt-2.5 flex min-h-[180px] items-center justify-center text-sm text-slate-400">
						태그 컨텐츠
					</div>
				) : null}
			</CommonTabs>
			{isOptionSection ? (
				<OptionGroupEditorDialog
					open={Boolean(selectedOptionGroup)}
					onOpenChange={open => {
						if (!open) {
							setSelectedOptionGroupState({
								selectedFeatureKey,
								groupKey: null,
							});
						}
					}}
					group={selectedOptionGroup}
					networkDetail={networkDetail}
					onPropertyChange={onPropertyChange}
				/>
			) : null}
		</div>
	);
}

export default FeaturePropertyPanel;
