/**
 *packageName    : inp-simulator-
 * fileName       : simulApi.js
 * author         : 'stz'
 * date           : 26. 7. 7.
 * description    :
 * ===========================================================
 * DATE              AUTHOR             NOTE
 * -----------------------------------------------------------
 * 26. 7. 7.          'stz'       최초 생성
 */
import apiRequest from '@/web/js/apis/apiRequest.js';

export const SIMUL_API_PREFIX = '/simulations';

function encodePathParam(value) {
	return encodeURIComponent(String(value ?? ''));
}

export const simulApi = {
	searchDate: async (analDateTime, options) => {
		const url = `${SIMUL_API_PREFIX}/${encodePathParam(analDateTime)}/analysis`;
		return await apiRequest.get(url, { ...options });
	},
	anals: async ({ analDateTime, pumpComb } = {}, options) => {
		const url = `${SIMUL_API_PREFIX}/${encodePathParam(analDateTime)}/analysis-result`;
		return await apiRequest.get(url, {
			...options,
			searchParams: {
				...(options?.searchParams ?? {}),
				...(pumpComb ? { pumpComb } : {}),
			},
		});
	},
};
