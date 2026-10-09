/**
 * ═════════════════════════════════════════════════════════════
 * 📄 FILE     : performApi.js
 * 📁 PACKAGE  : Inp-simulator-
 * 👤 AUTHOR   : stz
 * 🕒 CREATED  : 26. 6. 29.
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 📝 DESCRIPTION
 *   - 성능 곡선 api
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 🔄 CHANGE LOG
 *   - DATE : 2026/06/29 | Author : stz | 최초 생성
 * ═════════════════════════════════════════════════════════════
 */
import apiRequest from '@/web/js/apis/apiRequest.js';

export const PERFORM_API_PREFIX = '/pump-combinations';
export const GET_PMP_COMBIN_OPERAT_STATS = `${PERFORM_API_PREFIX}/operation-stats`;

const performApi = {
	/** ■■■■■■■■■■■■■■■■   펌프조합 테이블 조회   ■■■■■■■■■■■■■■■■*/
	getPmpCombinOperatStats: async options => {
		return await apiRequest.get(GET_PMP_COMBIN_OPERAT_STATS, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   펌프 성능곡선   ■■■■■■■■■■■■■■■■*/
	getPmpCombinPerformanceCurve: async (pumpGrp, combIdx, options) => {
		const url = `${PERFORM_API_PREFIX}/${pumpGrp}/${combIdx}/performance-curve`;
		return await apiRequest.get(url, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   설측 성능곡선 조회   ■■■■■■■■■■■■■■■■*/
	getPmpCombinActualPerformanceCurve: async (pumpGrp, combIdx, options) => {
		const url = `${PERFORM_API_PREFIX}/${pumpGrp}/${combIdx}/actual-performance-curve`;
		return await apiRequest.get(url, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   펌프조합 성능곡선 갱신   ■■■■■■■■■■■■■■■■*/
	getPmpCombinPerformnaceCurveRenewal: async (pumpGrp, combIdx, options) => {
		const url = `${PERFORM_API_PREFIX}/${pumpGrp}/${combIdx}/performance-curve/renewal`;
		return await apiRequest.get(url, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   펌프조합 성능곡선 추출   ■■■■■■■■■■■■■■■■*/
	addPmpCombinPerformnaceCurveExtract: async (pumpGrp, combIdx, requestBody, options) => {
		const url = `${PERFORM_API_PREFIX}/${pumpGrp}/${combIdx}/performance-curve/extraction`;
		return await apiRequest.post(url, requestBody, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   펌프조합 성능곡선 저장   ■■■■■■■■■■■■■■■■*/
	savePmpCombinPerformanceCurve: async (pumpGrp, combIdx, requestBody, options) => {
		const url = `${PERFORM_API_PREFIX}/${pumpGrp}/${combIdx}/performance-curve`;
		return await apiRequest.put(url, requestBody, { ...options });
	},
};

export default performApi;
