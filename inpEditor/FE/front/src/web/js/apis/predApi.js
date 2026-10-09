/**
 * ═════════════════════════════════════════════════════════════
 * 📄 FILE     : predApi.js
 * 📁 PACKAGE  : Inp-simulator-
 * 👤 AUTHOR   : stz
 * 🕒 CREATED  : 26. 6. 26.
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 📝 DESCRIPTION
 *   - 성능 예측 API 관련 정의
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 🔄 CHANGE LOG
 *   - DATE : 2026/06/26 | Author : stz | 최초 생성
 * ═════════════════════════════════════════════════════════════
 */
import apiRequest from '@/web/js/apis/apiRequest.js';

export const PRED_API_PREFIX = '/tag-predictions';
export const GET_ACCURACY_SERIES = `${PRED_API_PREFIX}/accuracy/series`;
export const GET_ACCURACY_STATS = `${PRED_API_PREFIX}/accuracy/stats`;
export const predApi = {
	/** ■■■■■■■■■■■■■■■■   성능 예측 조회 (Chart)  ■■■■■■■■■■■■■■■■*/
	getAccuracySeries: async options => {
		return await apiRequest.get(GET_ACCURACY_SERIES, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   예측구간 정확도 통계   ■■■■■■■■■■■■■■■■*/
	getAccuracyStats: async options => {
		return await apiRequest.get(GET_ACCURACY_STATS, { ...options });
	},
};
