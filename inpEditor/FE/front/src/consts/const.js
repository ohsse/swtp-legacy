import { setChartConfig } from 'stz-chart-maker';

/**
 * ═════════════════════════════════════════════════════════════
 * 📄 FILE     : const.js
 * 📁 PACKAGE  : front-consts
 * 👤 AUTHOR   : stz
 * 🕒 CREATED  : 26. 6. 12.
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 📝 DESCRIPTION
 *   - 전역 상수 정의 파일
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 🔄 CHANGE LOG
 *   - DATE : 2026/06/12 | Author : stz | 최초 생성
 * ═════════════════════════════════════════════════════════════
 */

export const PROFILE = import.meta.env.VITE_PROFILE ?? 'dev';
export const MoniterOrSimulation = ['모니터링', '시뮬레이션'];

export const globalChartColorSeq = ['#55fbff', '#fce652', '#58f4ff', '#5cafff', '#489cf2', '#5468ff', '#8fd8ff', '#79ffb3'];
export const ANALS_YN = { Y: '분석', N: '미분석' };
export const DISP_YN = { Y: '표출', N: '미표출' };

export const MODEL_EDITOR_MAP_ID = 'model-editor-map';
export const MODEL_EDITOR_RIPPLE_COLOR = 'rgba(145, 214, 255, 0.38)';
export const MODEL_EDITOR_ACTION_BUTTON_SEQ = [
	{ key: 'modelSelect', label: '모델 선택', variant: 'secondary' },
	{ key: 'save', label: '저장', variant: 'outline', requiresModelFile: true },
	{ key: 'apply', label: '적용', variant: 'outline', requiresModelFile: true },
	{ key: 'settingValue', label: '비교대상 설정', variant: 'outline', requiresModelFile: true },
	{ key: 'comparisonTarget', label: '분석대상 설정', variant: 'outline', requiresModelFile: true },
	{ key: 'optimizationExecution', label: '최적화 실행', variant: 'outline', requiresModelFile: true },
	{ key: 'optimizationManager', label: '최적화 이력', className: '!bg-none !bg-pink-500 !text-white', requiresModelFile: true },
];
export const MODEL_EDITOR_LEFT_TAB_ITEM_SEQ = [
	{ k: '모델', v: 'model' },
	{ k: '모델 레이어', v: 'modelLayer' },
];
export const MODEL_EDITOR_RIGHT_TAB_ITEM_SEQ = [{ k: '모델정보', v: 'modelInfo' }];
export const MODEL_EDITOR_LAYER_TREE_ITEMS = [
	{
		id: 'NODES',
		value: 'NODES',
		label: '노드',
		children: [
			{ id: 'JUNCTIONS', value: 'JUNCTIONS', label: '절점' },
			{ id: 'RESERVOIRS', value: 'RESERVOIRS', label: '저수지' },
			{ id: 'TANKS', value: 'TANKS', label: '탱크' },
		],
	},
	{
		id: 'LINKS',
		value: 'LINKS',
		label: '링크',
		children: [
			{ id: 'PIPES', value: 'PIPES', label: '관로' },
			{ id: 'PUMPS', value: 'PUMPS', label: '펌프' },
			{ id: 'VALVES', value: 'VALVES', label: '밸브' },
		],
	},
	{
		id: 'LABELS',
		value: 'LABELS',
		label: '라벨',
	},
];
export const MODEL_EDITOR_EDIT_ACTION_BUTTON_SEQ = [
	{ key: 'select', src: '/btn_edit_slt.png', alt: 'select' },
	{ key: 'add', src: '/btn_edit_add.png', alt: 'add' },
	{ key: 'delete', src: '/btn_edit_del.png', alt: 'delete' },
];
export const MODEL_EDITOR_BUTTON_PROPS = {
	disableRipple: false,
	rippleColor: MODEL_EDITOR_RIPPLE_COLOR,
};
export const MODEL_EDITOR_SELECT_MENU_PROPS = {
	transitionDuration: {
		enter: 240,
		exit: 160,
	},
};

export const MODEL_SELECT_FIELD_LABEL_BY_KEY = {
	inpFileId: 'INP 파일 ID',
	orgnlFileNm: '원본 파일명',
	storFileNm: '저장 파일명',
	fileXtns: '파일 확장자',
	fileSz: '파일 크기',
	currRevNo: '현재 리비전',
	currentRevNo: '현재 리비전',
	// 서버의 mntr_yn 플래그. 해석엔진(epa)에 적용된 모델 한 건만 Y 다.
	monitoringYn: '적용',
	workType: '작업 구분',
	rgstDttm: '등록일시',
};
export const MODEL_SELECT_FIELD_WIDTH_BY_KEY = {
	inpFileId: 'w-[220px]',
	orgnlFileNm: 'w-[200px]',
	storFileNm: 'w-[220px]',
	fileXtns: 'w-[120px]',
	fileSz: 'w-[120px]',
	currRevNo: 'w-[120px]',
	currentRevNo: 'w-[120px]',
	monitoringYn: 'w-[100px]',
	workType: 'w-[130px]',
	rgstDttm: 'w-[160px]',
};
export const MODEL_SELECT_DEFAULT_FIELD_ORDER = [
	'inpFileId',
	'orgnlFileNm',
	'storFileNm',
	'fileXtns',
	'fileSz',
	'currRevNo',
	'currentRevNo',
	'monitoringYn',
	'workType',
	'rgstDttm',
];
export const MODEL_SELECT_TABLE_CLASS_NAME = {
	headClassName: 'h-9 border border-[#d7dfeb] bg-[#edf2f8] px-3 text-[12px] font-semibold text-white',
	cellClassName: 'h-10 border border-[#d7dfeb] px-3 text-[12px] text-[#526783]',
};

export const SETTING_VALUE_COLUMN_SEQ = [
	{ key: 'pointNm', colNm: '지점명', flex: 1.2, minWidth: 110 },
	{ key: 'junctionId', colNm: '절점ID', flex: 1, minWidth: 96 },
	{ key: 'pipeId', colNm: '관로ID', flex: 1, minWidth: 96 },
	{ key: 'flowTagNo', colNm: '유량태그번호', flex: 1.35, minWidth: 126 },
	{ key: 'pressureTagNo', colNm: '압력태그번호', flex: 1.35, minWidth: 126 },
	{
		key: 'dispYn',
		colNm: '표출여부',
		flex: 0.9,
		minWidth: 104,
		type: 'comboBox',
		comboItems: Object.entries(DISP_YN).map(([value, label]) => ({ value, label })),
	},
	{ key: 'sortOrd', colNm: '정렬순서', flex: 0.9, minWidth: 88 },
];
export const COMPARISON_TARGET_COLUMN_SEQ = [
	{ key: 'nodeId', colNm: '노드아이디', flex: 1, minWidth: 150 },
	{ key: 'tagNo', colNm: '태그번호', flex: 1, minWidth: 150 },
	{
		key: 'analYn',
		colNm: '분석여부',
		flex: 0.8,
		minWidth: 120,
		type: 'comboBox',
		comboItems: Object.entries(ANALS_YN).map(([value, label]) => ({ value, label })),
	},
];
export const OPTIMIZATION_TABLE_CLASS_NAME = {
	headClassName:
		'border-b border-r border-[rgba(110,185,255,0.18)] bg-[rgba(14,42,82,0.9)] px-2 text-center text-[12px] font-semibold text-sky-50',
	cellClassName: 'border-b border-r border-[rgba(110,185,255,0.1)] px-2 text-sky-50',
};
export const OPTIMIZATION_HISTORY_COLUMN_SEQ = [
	{ key: 'startDttm', colNm: '실행일시', widthClassName: 'w-[132px]' },
	{ key: 'endDttm', colNm: '종료일시', widthClassName: 'w-[132px]' },
	{ key: 'fileRevNo', colNm: '파일 버전', widthClassName: 'w-[82px] text-center' },
	{ key: 'statusLabel', colNm: '상태', widthClassName: 'w-[82px] text-center' },
	{ key: 'progressText', colNm: '진행률', widthClassName: 'w-[82px] text-center' },
];
export const OPTIMIZATION_SETTING_COLUMN_SEQ = [
	{ key: 'nodeId', colNm: '노드아이디', flex: 1, minWidth: 150 },
	{ key: 'tagNo', colNm: '태그번호', flex: 1, minWidth: 150 },
	{ key: 'analYn', colNm: '분석여부', flex: 0.8, minWidth: 120 },
];
export const OPTIMIZATION_DETAIL_COLUMN_SEQ = [
	{ key: 'pointNm', colNm: '지점명', widthClassName: 'w-[110px]' },
	{ key: 'dataTypeNm', colNm: '항목', widthClassName: 'w-[86px]' },
	{ key: 'measureValue', colNm: '계측값', widthClassName: 'w-[90px]' },
	{ key: 'beforeValue', colNm: '최적화 전 분석값', widthClassName: 'w-[128px]' },
	{ key: 'afterValue', colNm: '최적화 후 분석값', widthClassName: 'w-[128px]' },
	{ key: 'beforeErrorRate', colNm: '전 오차율', widthClassName: 'w-[95px]' },
	{ key: 'afterErrorRate', colNm: '후 오차율', widthClassName: 'w-[95px]' },
	{ key: 'improvementRate', colNm: '개선율', widthClassName: 'w-[95px]' },
];
export const OPTIMIZATION_RUN_LOG_COLUMN_SEQ = [
	{ key: 'workerNm', colNm: '작업명', widthClassName: 'w-[150px]' },
	{ key: 'startDttm', colNm: '실행시작시간', widthClassName: 'w-[140px]' },
	{ key: 'endDttm', colNm: '실행종료시간', widthClassName: 'w-[140px]' },
	{ key: 'totalGenerCount', colNm: '총세대수', widthClassName: 'w-[90px] text-center' },
	{ key: 'implGenerCount', colNm: '진행세대수', widthClassName: 'w-[90px] text-center' },
	{ key: 'progress', colNm: '진행률', widthClassName: 'text-center' },
];

export const OBJECT_PROPERTY_LABEL_BY_KEY = {
	no: 'No',
	id: '아이디',
	featureId: '아이디',
	objectType: '객체 유형',
	layer: '레이어',
	x: 'X-좌표',
	y: 'Y-좌표',
	description: '설명',
	tag: '태그',
	elevation: '표고(고도)',
	baseDemand: '기준 수요량',
	demandPattern: '수요 패턴',
	demandCategories: '수요 카테고리',
	emitterCoefficient: '이미터 계수',
	initialQuality: '초기 수질',
	sourceQuality: '소스 수질',
	totalHead: '총 수두',
	headPattern: '수두 패턴',
	initialLevel: '초기 수위',
	minimumLevel: '최소 수위',
	maximumLevel: '최대 수위',
	diameter: '직경',
	minimumVolume: '최소 부피',
	volumeCurve: '부피 곡선',
	canOverflow: '월류 허용 여부',
	mixingModel: '혼합 모델',
	mixingFraction: '혼합 비율',
	reactionCoefficient: '반응 계수',
	startNode: '시작 노드',
	endNode: '끝 노드',
	length: '길이',
	roughness: '조도 계수',
	lossCoefficient: '미소손실 계수',
	initialStatus: '초기 상태',
	bulkCoefficient: '벌크 반응 계수',
	wallCoefficient: '벽면 반응 계수',
	pumpCurve: '펌프 곡선',
	power: '출력(정전력)',
	speed: '상대 속도',
	pattern: '속도 패턴',
	efficiencyCurve: '효율 곡선',
	energyPrice: '에너지 단가',
	pricePattern: '단가 패턴',
	type: '밸브 유형',
	setting: '설정값',
	fixedStatus: '고정 상태',
	text: '텍스트',
	anchorNode: '앵커 노드',
	sourceType: '소스 유형',
	qualityPattern: '수질 패턴',
	timePattern: '시간 패턴',
	category: '카테고리',
};
export const OBJECT_TYPE_LABEL_BY_KEY = {
	junction: '절점',
	reservoir: '저수지',
	tank: '탱크',
	pipe: '관로',
	pump: '펌프',
	valve: '밸브',
	label: '라벨',
};
export const PROPERTY_FIELD_KEYS_BY_OBJECT_TYPE = {
	junction: [
		'featureId',
		'objectType',
		'layer',
		'description',
		'tag',
		'elevation',
		'baseDemand',
		'demandPattern',
		'demandCategories',
		'emitterCoefficient',
		'initialQuality',
		'sourceQuality',
		'x',
		'y',
	],
	reservoir: [
		'featureId',
		'objectType',
		'layer',
		'description',
		'tag',
		'totalHead',
		'headPattern',
		'initialQuality',
		'sourceQuality',
		'x',
		'y',
	],
	tank: [
		'featureId',
		'objectType',
		'layer',
		'description',
		'tag',
		'elevation',
		'initialLevel',
		'minimumLevel',
		'maximumLevel',
		'diameter',
		'minimumVolume',
		'volumeCurve',
		'canOverflow',
		'mixingModel',
		'mixingFraction',
		'reactionCoefficient',
		'initialQuality',
		'sourceQuality',
		'x',
		'y',
	],
	pipe: [
		'featureId',
		'objectType',
		'layer',
		'startNode',
		'endNode',
		'description',
		'tag',
		'length',
		'diameter',
		'roughness',
		'lossCoefficient',
		'initialStatus',
		'bulkCoefficient',
		'wallCoefficient',
		'x',
		'y',
	],
	pump: [
		'featureId',
		'objectType',
		'layer',
		'startNode',
		'endNode',
		'description',
		'tag',
		'pumpCurve',
		'power',
		'speed',
		'pattern',
		'initialStatus',
		'efficiencyCurve',
		'energyPrice',
		'pricePattern',
		'x',
		'y',
	],
	valve: [
		'featureId',
		'objectType',
		'layer',
		'startNode',
		'endNode',
		'description',
		'tag',
		'diameter',
		'type',
		'setting',
		'lossCoefficient',
		'fixedStatus',
		'x',
		'y',
	],
	label: ['featureId', 'objectType', 'layer', 'text', 'anchorNode', 'x', 'y'],
};
export const READ_ONLY_PROPERTY_KEY_SET = new Set(['no', 'objectType', 'layer', 'x', 'y']);
export const NUMERIC_PROPERTY_KEY_SET = new Set([
	'elevation',
	'baseDemand',
	'emitterCoefficient',
	'initialQuality',
	'totalHead',
	'initialLevel',
	'minimumLevel',
	'maximumLevel',
	'diameter',
	'minimumVolume',
	'mixingFraction',
	'reactionCoefficient',
	'length',
	'roughness',
	'lossCoefficient',
	'bulkCoefficient',
	'wallCoefficient',
	'power',
	'speed',
	'energyPrice',
	'sourceQuality',
]);
export const PROPERTY_ENUM_VALUE_SEQ_BY_KEY = {
	canOverflow: ['YES', 'NO'],
	mixingModel: ['MIXED', '2COMP', 'FIFO', 'LIFO'],
	type: ['PRV', 'PSV', 'PBV', 'FCV', 'TCV', 'GPV'],
	fixedStatus: ['OPEN', 'CLOSED', 'NONE'],
	sourceType: ['CONCEN', 'MASS', 'FLOWPACED', 'SETPOINT'],
	curveType: ['PUMP', 'EFFICIENCY', 'VOLUME', 'HEADLOSS'],
};
export const OPTION_ENUM_VALUE_SEQ_BY_KEY = {
	flowUnits: ['CFS', 'GPM', 'MGD', 'IMGD', 'AFD', 'LPS', 'LPM', 'MLD', 'CMH', 'CMD'],
	headlossFormula: ['H-W', 'D-W', 'C-M'],
	ifUnbalanced: ['STOP', 'CONTINUE'],
	demandModel: ['DDA', 'PDA'],
	parameter: ['NONE', 'CHEMICAL', 'AGE', 'TRACE'],
	wallReactionOrder: ['0', '1'],
	bulkReactionOrder: ['0', '1', '2'],
	tankReactionOrder: ['0', '1', '2'],
	statistic: ['NONE', 'AVERAGED', 'MINIMUM', 'MAXIMUM', 'RANGE'],
	status: ['YES', 'NO', 'FULL'],
	summary: ['YES', 'NO'],
};
export const INITIAL_STATUS_VALUE_SEQ_BY_OBJECT_TYPE = {
	pipe: ['OPEN', 'CLOSED', 'CV'],
	pump: ['OPEN', 'CLOSED'],
};
export const REQUIRED_PROPERTY_KEY_SEQ_BY_OBJECT_TYPE = {
	junction: ['featureId'],
	reservoir: ['featureId'],
	tank: ['featureId'],
	pipe: ['featureId', 'startNode', 'endNode'],
	pump: ['featureId', 'startNode', 'endNode'],
	valve: ['featureId', 'startNode', 'endNode'],
	label: ['featureId', 'text'],
};
export const SOURCE_TYPE_OPTION_SEQ = [
	{ value: 'CONCEN', label: '농도 (CONCEN)' },
	{ value: 'MASS', label: '질량주입 (MASS)' },
	{ value: 'FLOWPACED', label: '유량비례 (FLOWPACED)' },
	{ value: 'SETPOINT', label: '목표농도 (SETPOINT)' },
];
export const NESTED_PROPERTY_FIELD_SEQ_BY_KEY = {
	sourceQuality: [
		{ key: 'sourceQuality', label: OBJECT_PROPERTY_LABEL_BY_KEY.sourceQuality },
		{ key: 'qualityPattern', label: OBJECT_PROPERTY_LABEL_BY_KEY.qualityPattern },
		{ key: 'sourceType', label: OBJECT_PROPERTY_LABEL_BY_KEY.sourceType, type: 'select', options: SOURCE_TYPE_OPTION_SEQ },
	],
	demandCategories: [
		{ key: 'baseDemand', label: OBJECT_PROPERTY_LABEL_BY_KEY.baseDemand },
		{ key: 'timePattern', label: OBJECT_PROPERTY_LABEL_BY_KEY.timePattern },
		{ key: 'category', label: OBJECT_PROPERTY_LABEL_BY_KEY.category },
	],
};
export const NESTED_PROPERTY_EDITOR_TITLE_BY_KEY = {
	sourceQuality: '소스',
	demandCategories: '수요 카테고리',
};
export const LAYER_TABLE_BASE_COL_CLASS_NAME = {
	headClassName: 'border-b border-r border-slate-700/70 bg-slate-900/55 text-center text-slate-300',
	cellClassName: 'border-b border-r border-slate-800/70 text-slate-100',
};

setChartConfig({
	errorLogging: true,
	silentMode: false,
	defaultColor: [...globalChartColorSeq],
	loading: false,
	zoom: {
		zoom: {
			drag: {
				enabled: true,
				modifierKey: 'shift',
			},
			pinch: {
				enabled: true,
			},
			mode: 'xy',
		},
		pan: {
			enabled: true,
			mode: 'xy',
			modifierKey: 'alt',
		},
		limits: {
			x: { min: 'original', max: 'original' },
			y: { min: 0, max: 130 },
		},
	},
	legend: {
		position: 'top',
		labels: {
			color: '#d5eeff',
			boxWidth: 12,
			padding: 14,
		},
	},
	tooltip: {
		enabled: true,
		backgroundColor: 'rgba(8, 26, 61, 0.95)',
		titleColor: '#f8fbff',
		bodyColor: '#d5eeff',
		borderColor: 'rgba(125, 211, 252, 0.35)',
		borderWidth: 1,
	},
});
