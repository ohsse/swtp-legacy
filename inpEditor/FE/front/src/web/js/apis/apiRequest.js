/**
 * ═════════════════════════════════════════════════════════════
 * 📄 FILE     : apiRequest.js
 * 📁 PACKAGE  : front-
 * 👤 AUTHOR   : stz
 * 🕒 CREATED  : 26. 6. 13.
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 📝 DESCRIPTION
 *   - customKy 기반 공통 API 요청 래퍼
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 🔄 CHANGE LOG
 *   - DATE : 2026/06/13 | Author : stz | 최초 생성
 * ═════════════════════════════════════════════════════════════
 */
import { BASE_URL, HTTP_DELETE, HTTP_GET, HTTP_POST, HTTP_PUT } from '@/consts/index.js';
import { customKy } from './customKy.js';

const INTERNAL_SKIP_SPINNER_HEADER = 'x-stz-skip-spinner';
const INTERNAL_SKIP_ERROR_TOAST_HEADER = 'x-stz-skip-error-toast';

function isAbsoluteUrl(url) {
	return /^https?:\/\//i.test(url);
}

function buildRequestUrl(url) {
	if (isAbsoluteUrl(url)) {
		return url;
	}

	const normalizedBaseUrl = String(BASE_URL ?? '').replace(/\/+$/, '');
	const normalizedPath = String(url ?? '').replace(/^\/+/, '');

	return `${normalizedBaseUrl}/${normalizedPath}`;
}

function hasRequestBody(method) {
	return [HTTP_POST, HTTP_PUT, HTTP_DELETE].includes(method);
}

function isFormData(value) {
	return typeof FormData !== 'undefined' && value instanceof FormData;
}

function isBlob(value) {
	return typeof Blob !== 'undefined' && value instanceof Blob;
}

function setInternalRequestHeader(requestOptions, headerName, enabled) {
	if (!enabled) return;

	const headers = new Headers(requestOptions.headers ?? undefined);
	headers.set(headerName, 'true');
	requestOptions.headers = headers;
}

function buildRequestOptions(method, requestBody, options = {}) {
	const requestOptions = { ...options };

	if (requestOptions.showLoading !== undefined) {
		const skipSpinner = requestOptions.showLoading === false;
		requestOptions.context = {
			...(requestOptions.context ?? {}),
			skipSpinner,
		};
		setInternalRequestHeader(requestOptions, INTERNAL_SKIP_SPINNER_HEADER, skipSpinner);
		delete requestOptions.showLoading;
	}

	if (requestOptions.showSpinner !== undefined) {
		const skipSpinner = requestOptions.showSpinner === false;
		requestOptions.context = {
			...(requestOptions.context ?? {}),
			skipSpinner,
		};
		setInternalRequestHeader(requestOptions, INTERNAL_SKIP_SPINNER_HEADER, skipSpinner);
		delete requestOptions.showSpinner;
	}

	if (requestOptions.skipSpinner !== undefined) {
		const skipSpinner = requestOptions.skipSpinner === true;
		requestOptions.context = {
			...(requestOptions.context ?? {}),
			skipSpinner,
		};
		setInternalRequestHeader(requestOptions, INTERNAL_SKIP_SPINNER_HEADER, skipSpinner);
		delete requestOptions.skipSpinner;
	}

	if (requestOptions.showErrorToast !== undefined) {
		const skipErrorToast = requestOptions.showErrorToast === false;
		requestOptions.context = {
			...(requestOptions.context ?? {}),
			skipErrorToast,
		};
		setInternalRequestHeader(requestOptions, INTERNAL_SKIP_ERROR_TOAST_HEADER, skipErrorToast);
		delete requestOptions.showErrorToast;
	}

	if (requestOptions.skipErrorToast !== undefined) {
		const skipErrorToast = requestOptions.skipErrorToast === true;
		requestOptions.context = {
			...(requestOptions.context ?? {}),
			skipErrorToast,
		};
		setInternalRequestHeader(requestOptions, INTERNAL_SKIP_ERROR_TOAST_HEADER, skipErrorToast);
		delete requestOptions.skipErrorToast;
	}

	if (!hasRequestBody(method) || requestBody === undefined || requestBody === null) {
		return requestOptions;
	}

	if (
		isFormData(requestBody) ||
		isBlob(requestBody) ||
		typeof requestBody === 'string' ||
		requestBody instanceof ArrayBuffer ||
		ArrayBuffer.isView(requestBody) ||
		requestBody instanceof URLSearchParams
	) {
		requestOptions.body = requestBody;
		return requestOptions;
	}

	requestOptions.json = requestBody;
	return requestOptions;
}

async function parseResponse(response) {
	const contentType = response.headers.get('content-type') ?? '';

	if (contentType.includes('application/json')) {
		return await response.json();
	}

	if (contentType.startsWith('text/')) {
		return await response.text();
	}

	return response;
}

async function request(method, url, requestBody, options = {}) {
	const requestUrl = buildRequestUrl(url);
	const response = await customKy(requestUrl, {
		method,
		...buildRequestOptions(method, requestBody, options),
	});

	return await parseResponse(response);
}

export const ApiRequest = {
	request,
	get(url, options = {}) {
		return request(HTTP_GET, url, undefined, options);
	},
	post(url, requestBody, options = {}) {
		return request(HTTP_POST, url, requestBody, options);
	},
	put(url, requestBody, options = {}) {
		return request(HTTP_PUT, url, requestBody, options);
	},
	delete(url, requestBody, options = {}) {
		return request(HTTP_DELETE, url, requestBody, options);
	},
};

export default ApiRequest;
