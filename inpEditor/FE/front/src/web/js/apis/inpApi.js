/**
 * ═════════════════════════════════════════════════════════════
 * 📄 FILE     : inpApi.js
 * 📁 PACKAGE  : Inp-simulator-
 * 👤 AUTHOR   : stz
 * 🕒 CREATED  : 26. 6. 19.
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 📝 DESCRIPTION
 *   -
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 🔄 CHANGE LOG
 *   - DATE : 2026/06/19 | Author : stz | 최초 생성
 * ═════════════════════════════════════════════════════════════
 */
import apiRequest from '@/web/js/apis/apiRequest.js';
const INP_API_PREFIX = '/inp-files';
export const GET_INP_FILE = `${INP_API_PREFIX}`;
export const MULTI_DOWNLOAD_INP_FILE = `${INP_API_PREFIX}/download-zip`;
export const SAVE_NEW_INP_FILE = `${INP_API_PREFIX}/network/save-as`;
export const OPTIMIZATION_PREFIX = `/opt`;

export const inpApi = {
	/** ■■■■■■■■■■■■■■■■   조회   ■■■■■■■■■■■■■■■■*/
	getInpFile: async options => {
		return await apiRequest.get(GET_INP_FILE, { showSpinner: false, ...options });
	},
	/** ■■■■■■■■■■■■■■■■   업로드   ■■■■■■■■■■■■■■■■*/
	uploadInpFile: async (file, options) => {
		const formData = new FormData();
		formData.append('file', file);
		formData.append(
			'info',
			new Blob([JSON.stringify({ orgnlFileNm: file?.name ?? '' })], {
				type: 'application/json',
			})
		);

		return await apiRequest.post(INP_API_PREFIX, formData, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   상세 조회   ■■■■■■■■■■■■■■■■*/
	getInpFileDetail: async (inpFileId, options) => {
		const url = `/inp-files/${inpFileId}/network`;
		return await apiRequest.get(url, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■ 다중   다운로드   ■■■■■■■■■■■■■■■■*/
	multiDownloadInpFile: async (inpFileIds, options) => {
		return await apiRequest.post(MULTI_DOWNLOAD_INP_FILE, { inpFileIds }, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■ 단일  다운로드   ■■■■■■■■■■■■■■■■*/
	downloadInpFile: async (inpFileId, options) => {
		const url = `/inp-files/${inpFileId}/download`;
		return await apiRequest.get(url, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   리비전 조회   ■■■■■■■■■■■■■■■■*/
	getInpFileRevisions: async (inpFileId, options) => {
		const url = `/inp-files/${inpFileId}/revisions`;
		return await apiRequest.get(url, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   특정 리비전 다운로드   ■■■■■■■■■■■■■■■■*/
	downloadSpecInpRevision: async (inpFileId, revNo, options) => {
		const url = `/inp-files/${inpFileId}/revisions/${revNo}/download`;
		return await apiRequest.get(url, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   리비전 최신버전 롤백   ■■■■■■■■■■■■■■■■*/
	rollbackInpFileRevision: async (inpFileId, revNo, options) => {
		const url = `/inp-files/${inpFileId}/revisions/${revNo}/rollback`;
		return await apiRequest.put(url, undefined, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   새 inp file 추가   ■■■■■■■■■■■■■■■■*/
	saveNewInpFile: async (inpFileData, options) => {
		return await apiRequest.post(SAVE_NEW_INP_FILE, inpFileData, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   inp file 수정   ■■■■■■■■■■■■■■■■*/
	saveInpFile: async (inpFileId, inpFileData, options) => {
		const url = `/inp-files/${inpFileId}/network`;
		return await apiRequest.put(url, inpFileData, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   inp file 적용   ■■■■■■■■■■■■■■■■*/
	applyInpFile: async (inpFileId, options) => {
		const url = `/inp-files/${inpFileId}/apply`;
		return await apiRequest.put(url, undefined, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   inp file 삭제   ■■■■■■■■■■■■■■■■*/
	removeInpFile: async (inpFileId, options) => {
		const url = `/inp-files/${inpFileId}`;
		return await apiRequest.delete(url, undefined, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   최적화 이력 목록 조회   ■■■■■■■■■■■■■■■■*/
	getOptimizationList: async (inpFileId, options) => {
		return await apiRequest.get(`${OPTIMIZATION_PREFIX}`, {
			...options,
			searchParams: {
				...(options?.searchParams ?? {}),
				...(inpFileId ? { inpFileId } : {}),
			},
		});
	},
	/** ■■■■■■■■■■■■■■■■   최적화 실행   ■■■■■■■■■■■■■■■■*/
	getOptimizationExecution: async (inpFileId, options) => {
		return await apiRequest.get(`${OPTIMIZATION_PREFIX}/${inpFileId}`, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   최적화 이력 상세 조회   ■■■■■■■■■■■■■■■■*/
	getOptHist: async (histId, options) => {
		const url = `/opt/hist/${histId}`;
		return await apiRequest.get(url, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   매핑 단건 조회   ■■■■■■■■■■■■■■■■*/
	getInpMapping: async (inpFileId, mappingId, options) => {
		const url = `${INP_API_PREFIX}/${inpFileId}/mappings/${mappingId}`;
		return await apiRequest.get(url, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   매핑 목록 조회   ■■■■■■■■■■■■■■■■*/
	getInpMappingList: async (inpFileId, options) => {
		const url = `${INP_API_PREFIX}/${inpFileId}/mappings`;
		return await apiRequest.get(url, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   매핑 등록   ■■■■■■■■■■■■■■■■*/
	addInpMapping: async (inpFileId, mappingData, options) => {
		const url = `${INP_API_PREFIX}/${inpFileId}/mappings`;
		return await apiRequest.post(url, mappingData, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   매핑 수정   ■■■■■■■■■■■■■■■■*/
	modifyInpMapping: async (inpFileId, mappingId, mappingData, options) => {
		const url = `${INP_API_PREFIX}/${inpFileId}/mappings/${mappingId}`;
		return await apiRequest.put(url, mappingData, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   매핑 삭제   ■■■■■■■■■■■■■■■■*/
	removeInpMapping: async (inpFileId, mappingId, options) => {
		const url = `${INP_API_PREFIX}/${inpFileId}/mappings/${mappingId}`;
		return await apiRequest.delete(url, undefined, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   비교대상 분석 매핑 조회  ■■■■■■■■■■■■■■■■*/
	getAnalsMappingList: async (inpFileId, options) => {
		const url = `${INP_API_PREFIX}/${inpFileId}/anal-mappings`;
		return await apiRequest.get(url, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   비교대상 분석 매핑 등록   ■■■■■■■■■■■■■■■■*/
	addAnalsMapping: async (inpFileId, mappingData, options) => {
		const url = `${INP_API_PREFIX}/${inpFileId}/anal-mappings`;
		return await apiRequest.post(url, mappingData, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   비교대상 분석 매핑 수정   ■■■■■■■■■■■■■■■■*/
	modifyAnalsMapping: async (inpFileId, mappingId, mappingData, options) => {
		const url = `${INP_API_PREFIX}/${inpFileId}/anal-mappings/${mappingId}`;
		return await apiRequest.put(url, mappingData, { ...options });
	},
	/** ■■■■■■■■■■■■■■■■   비교대상 분석 매핑 삭제   ■■■■■■■■■■■■■■■■*/
	removeAnalsMapping: async (inpFileId, mappingId, options) => {
		const url = `${INP_API_PREFIX}/${inpFileId}/anal-mappings/${mappingId}`;
		return await apiRequest.delete(url, undefined, { ...options });
	},
	getTagCortPending: async options => {
		const url = `/tag-corrections/pending`;
		return await apiRequest.get(url, { ...options });
	},
	addTagCortNotify: async (notiBody, options) => {
		const url = `/tag-corrections/notify`;
		return await apiRequest.post(url, notiBody, { ...options });
	},
};
