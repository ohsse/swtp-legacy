/**
 * ═════════════════════════════════════════════════════════════
 * 📄 FILE     : customKy.js
 * 📁 PACKAGE  : front-
 * 👤 AUTHOR   : stz
 * 🕒 CREATED  : 26. 6. 12.
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 📝 DESCRIPTION
 *   -
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 🔄 CHANGE LOG
 *   - DATE : 2026/06/12 | Author : stz | 최초 생성
 * ═════════════════════════════════════════════════════════════
 */
import { API_TIMEOUT, resolveApiErrorMessage } from '@/consts/index.js';
import ky from 'ky';
import { offSpinner, onSpinner } from '@/web/components/common/Spinner.jsx';
import { showToast } from '@/web/components/common/CommonToast.jsx';

const INTERNAL_SKIP_SPINNER_HEADER = 'x-stz-skip-spinner';
const INTERNAL_SKIP_ERROR_TOAST_HEADER = 'x-stz-skip-error-toast';
const skipSpinnerRequestSet = new WeakSet();
const skipErrorToastRequestSet = new WeakSet();

function hasInternalHeader(request, headerName) {
	return request?.headers?.get?.(headerName) === 'true';
}

function markInternalOptions(request, options) {
	if (hasInternalHeader(request, INTERNAL_SKIP_SPINNER_HEADER)) {
		skipSpinnerRequestSet.add(request);
		request.headers.delete(INTERNAL_SKIP_SPINNER_HEADER);
		options.context = {
			...(options.context ?? {}),
			skipSpinner: true,
		};
	}

	if (hasInternalHeader(request, INTERNAL_SKIP_ERROR_TOAST_HEADER)) {
		skipErrorToastRequestSet.add(request);
		request.headers.delete(INTERNAL_SKIP_ERROR_TOAST_HEADER);
		options.context = {
			...(options.context ?? {}),
			skipErrorToast: true,
		};
	}
}

function shouldHandleSpinner(request, options) {
	return options?.context?.skipSpinner !== true && !skipSpinnerRequestSet.has(request);
}

function shouldHandleErrorToast(error) {
	return error?.options?.context?.skipErrorToast !== true && !skipErrorToastRequestSet.has(error?.request);
}

async function resolveErrorMsg(error) {
	if (error?.response?.clone) {
		try {
			const body = await error.response.clone().json();
			if (typeof body?.code === 'string' && body.code.trim()) {
				return resolveApiErrorMessage(body.code, body.message ?? body.code);
			}
			if (typeof body?.message === 'string' && body.message.trim()) {
				return body.message;
			}
		} catch {
			// Ignore body parsing failures and fallback to generic messages.
		}
	}

	if (typeof error?.message === 'string' && error.message.trim()) {
		return error.message;
	}

	return '요청 처리 중 오류가 발생했습니다.';
}

export const customKy = ky.create({
	timeout: API_TIMEOUT,
	retry: {
		limit: 0,
	},
	hooks: {
		beforeRequest: [
			(request, options) => {
				markInternalOptions(request, options);

				if (shouldHandleSpinner(request, options)) {
					onSpinner();
				}
			},
		],
		afterResponse: [
			async (request, options, response) => {
				if (shouldHandleSpinner(request, options)) {
					offSpinner();
				}

				return response;
			},
		],
		beforeError: [
			async error => {
				if (shouldHandleSpinner(error?.request, error?.options)) {
					offSpinner();
				}

				if (shouldHandleErrorToast(error)) {
					showToast('error', await resolveErrorMsg(error));
				}
				return error;
			},
		],
	},
});
