import { PROFILE } from '@/consts/const.js';

/**
 * ═════════════════════════════════════════════════════════════
 * 📄 FILE     : map.js
 * 📁 PACKAGE  : front-
 * 👤 AUTHOR   : stz
 * 🕒 CREATED  : 26. 6. 12.
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 📝 DESCRIPTION
 *   - 지도 관련 상수 정의
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 🔄 CHANGE LOG
 *   - DATE : 2026/06/12 | Author : stz | 최초 생성
 * ═════════════════════════════════════════════════════════════
 */
export const DEFAULT_BACKGROUND_MAP =
	PROFILE === 'dev' ? 'https://xdworld.vworld.kr/2d/Base/service/{z}/{x}/{y}.png' : '/newEMap/';
export const DEFAULT_CENTER = [126.97, 37.56];
export const DEFAULT_ZOOM = 12;
export const DEFAULT_PROJECTION = 'EPSG:5186';
export const DEFAULT_PROJECTION_DEF =
	'+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs +type=crs';
export const BACKGROUND_MAP_PROJECTION = 'EPSG:5179';
export const BACKGROUND_MAP_PROJECTION_DEF =
	'+proj=tmerc +lat_0=38 +lon_0=127.5 +k=0.9996 +x_0=1000000 +y_0=2000000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs +type=crs';
export const LAYER_ORDER = ['PIPES', 'PUMPS', 'VALVES', 'JUNCTIONS', 'RESERVOIRS', 'TANKS', 'LABELS'];
export const DEFAULT_MIN_ZOOM = 5;
export const DEFAULT_MAX_ZOOM = 25;

export const NODE_LAYER_NAMES = ['JUNCTIONS', 'RESERVOIRS', 'TANKS'];
export const LINK_LAYER_NAMES = ['PIPES', 'PUMPS', 'VALVES'];
export const DISPLAY_LAYER_ORDER = ['JUNCTIONS', 'RESERVOIRS', 'TANKS', 'PIPES', 'PUMPS', 'VALVES', 'LABELS'];
export const NON_VISUAL_MODEL_SECTION_ORDER = ['CONTROLS', 'PATTERNS', 'OPTIONS', 'CURVES'];
export const LAYER_LABEL_BY_NAME = {
	JUNCTIONS: '절점',
	RESERVOIRS: '저수지',
	TANKS: '탱크',
	PIPES: '관로',
	PUMPS: '펌프',
	VALVES: '밸브',
	LABELS: '라벨',
	CONTROLS: '제어',
	PATTERNS: '패턴',
	OPTIONS: '옵션',
	CURVES: '커브',
};
export const MODEL_TYPE_OPTION_SEQ = [
	{ k: '모델', v: 'MODEL' },
	...DISPLAY_LAYER_ORDER.map(layerName => ({
		k: LAYER_LABEL_BY_NAME[layerName],
		v: layerName,
	})),
];
export const LAYER_OPTION_SEQ = DISPLAY_LAYER_ORDER.map(layerName => ({
	value: layerName,
	label: LAYER_LABEL_BY_NAME[layerName],
})).concat(
	NON_VISUAL_MODEL_SECTION_ORDER.map(sectionName => ({
		value: sectionName,
		label: LAYER_LABEL_BY_NAME[sectionName],
	}))
);
export const OBJ_TYPE_LAYER_NAME = {
	JUNCTIONS: 'junction',
	RESERVOIRS: 'reservoir',
	TANKS: 'tank',
	PIPES: 'pipe',
	PUMPS: 'pump',
	VALVES: 'valve',
	LABELS: 'label',
};
