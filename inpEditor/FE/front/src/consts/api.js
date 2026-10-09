/**
 * ═════════════════════════════════════════════════════════════
 * 📄 FILE     : api.js
 * 📁 PACKAGE  : front-
 * 👤 AUTHOR   : stz
 * 🕒 CREATED  : 26. 6. 12.
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 📝 DESCRIPTION
 *   - API 관련 상수 정의
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 🔄 CHANGE LOG
 *   - DATE : 2026/06/12 | Author : stz | 최초 생성
 * ═════════════════════════════════════════════════════════════
 */
import { PROFILE } from '@/consts/const.js';

export const BASE_URL = '/api/';
export const API_TIMEOUT = 500000000; // API 요청 타임아웃 (ms)
export const RETRY_COUNT = 3; // API 요청 재시도 횟수
export const RETRY_DELAY = 1000; // API 요청 재시도 간격 (ms)
/** ■■■■■■■■■■■■■■■■   위대한 HTTP 제군들   ■■■■■■■■■■■■■■■■*/
export const HTTP_GET = 'GET';
export const HTTP_POST = 'POST';
export const HTTP_PUT = 'PUT';
export const HTTP_DELETE = 'DELETE';

export const HTTP_CODE_EMPTY_FILE = 'EMPTY_FILE';
export const HTTP_CODE_INVALID_FILE_EXTENSION = 'INVALID_FILE_EXTENSION';
export const HTTP_CODE_FILE_UPLOAD_ERROR = 'FILE_UPLOAD_ERROR';
export const HTTP_CODE_FILE_DOWNLOAD_ERROR = 'FILE_DOWNLOAD_ERROR';
export const HTTP_CODE_FILE_NOT_FOUND = 'FILE_NOT_FOUND';
export const HTTP_CODE_REVISION_NOT_FOUND = 'REVISION_NOT_FOUND';
export const HTTP_CODE_INVALID_APPLY_TARGET = 'INVALID_APPLY_TARGET';
export const HTTP_CODE_FILE_APPLY_ERROR = 'FILE_APPLY_ERROR';

export const API_ERROR_MESSAGE_MAP = {
	[HTTP_CODE_EMPTY_FILE]: '업로드된 파일이 비어 있습니다.',
	[HTTP_CODE_INVALID_FILE_EXTENSION]: 'INP 파일만 업로드할 수 있습니다.',
	[HTTP_CODE_FILE_UPLOAD_ERROR]: '파일 업로드에 실패했습니다.',
	[HTTP_CODE_FILE_DOWNLOAD_ERROR]: '파일 다운로드에 실패했습니다.',
	[HTTP_CODE_FILE_NOT_FOUND]: '파일을 찾을 수 없습니다. 다시 선택해주세요.',
	[HTTP_CODE_REVISION_NOT_FOUND]: '요청한 리비전을 찾을 수 없습니다.',
	[HTTP_CODE_INVALID_APPLY_TARGET]: '적용 가능한 모델 파일명이 아닙니다.',
	[HTTP_CODE_FILE_APPLY_ERROR]: '모델 적용 파일 갱신에 실패했습니다.',
};

export function resolveApiErrorMessage(code, fallbackMessage = '요청 처리 중 오류가 발생했습니다.') {
	return API_ERROR_MESSAGE_MAP[code] ?? fallbackMessage;
}
