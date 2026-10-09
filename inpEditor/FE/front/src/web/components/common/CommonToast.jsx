import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const TYPE_MAP = {
	info: 'success',
	warn: 'warning',
	error: 'error',
};

const DEFAULT_TOAST_AUTO_CLOSE_MS = 3000;
const LEGACY_EXPIRED_TOKEN_MSG = 'accessToken이 만료되었습니다.';
const DEFAULT_EXPIRED_TOKEN_MSG = 'EXPIRED_TOKEN';

function resolveExpiredTokenMsg(i18n) {
	try {
		const translated = i18n?.t?.('errorCode.EXPIRED_TOKEN');
		if (typeof translated === 'string' && translated.trim().length > 0) {
			return translated.trim();
		}
	} catch {
		return DEFAULT_EXPIRED_TOKEN_MSG;
	}

	return DEFAULT_EXPIRED_TOKEN_MSG;
}

function isExpiredTokenToastMsg(msg, i18n) {
	const expiredTokenMsg = resolveExpiredTokenMsg(i18n);
	const normalizedMsg = String(msg ?? '').trim();

	return normalizedMsg.length > 0 && [expiredTokenMsg, LEGACY_EXPIRED_TOKEN_MSG].filter(Boolean).includes(normalizedMsg);
}

function showToast(type, msg, opts = {}, i18n) {
	const autoClose = opts.autoClose ?? (isExpiredTokenToastMsg(msg, i18n) ? false : DEFAULT_TOAST_AUTO_CLOSE_MS);
	return toast(msg, { type: TYPE_MAP[type], autoClose, ...opts });
}

function ConfirmToastContent({ message, confirmLabel = '확인', cancelLabel = '취소', onConfirm, onCancel }) {
	return (
		<div className="min-w-[280px] overflow-hidden rounded-[6px] border border-sky-200/20 bg-[linear-gradient(180deg,#122f5f,#0c2248)] text-white shadow-[0_18px_48px_rgba(2,9,34,0.42)]">
			<div className="flex items-start gap-3 px-4 pb-3 pt-4">
				<span className="mt-0.5 inline-flex size-7 shrink-0 items-center justify-center rounded-full border border-sky-200/30 bg-sky-300/12 text-[15px] font-semibold text-sky-100">
					?
				</span>
				<div className="min-w-0">
					<p className="text-[12px] font-semibold text-sky-100/72">확인 필요</p>
					<p className="mt-1 text-[14px] font-semibold leading-5 text-white">{message}</p>
				</div>
			</div>
			<div className="flex justify-end gap-2 border-t border-sky-200/12 bg-black/12 px-4 py-3">
				<button
					type="button"
					className="h-8 rounded-[3px] border border-sky-200/20 px-3.5 text-[12px] font-medium text-sky-50/78 transition hover:border-sky-100/40 hover:bg-white/8 hover:text-white"
					onClick={onCancel}
				>
					{cancelLabel}
				</button>
				<button
					type="button"
					className="h-8 rounded-[3px] border border-sky-200/60 bg-[linear-gradient(180deg,#3a78b8,#255a98)] px-4 text-[12px] font-semibold text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.18),0_8px_18px_rgba(6,28,70,0.32)] transition hover:border-sky-100 hover:bg-[linear-gradient(180deg,#458bd0,#2d68ac)]"
					onClick={onConfirm}
				>
					{confirmLabel}
				</button>
			</div>
		</div>
	);
}

function showConfirmToast(message, opts = {}) {
	const { confirmLabel, cancelLabel, ...toastOptions } = opts;

	return new Promise(resolve => {
		let toastId;
		const closeWith = result => {
			resolve(result);
			toast.dismiss(toastId);
		};

		toastId = toast(
			<ConfirmToastContent
				message={message}
				confirmLabel={confirmLabel}
				cancelLabel={cancelLabel}
				onConfirm={() => closeWith(true)}
				onCancel={() => closeWith(false)}
			/>,
			{
				autoClose: false,
				closeOnClick: false,
				draggable: false,
				type: 'default',
				className: '!w-auto !rounded-[6px] !bg-transparent !p-0 !shadow-none',
				bodyClassName: '!m-0 !p-0',
				closeButton: false,
				onClose: () => resolve(false),
				...toastOptions,
			}
		);
	});
}

function dismissToast(toastId) {
	toast.dismiss(toastId);
}

function CommonToast({
	position = 'top-right',
	closeOnClick = true,
	draggable = false,
	hideProgressBar,
	autoClose = DEFAULT_TOAST_AUTO_CLOSE_MS,
	isDisabled = false,
	dataTestId,
	ariaLabel,
}) {
	if (isDisabled) return null;

	const containerProps = {
		position,
		closeOnClick,
		draggable,
		hideProgressBar,
		autoClose,
	};

	return <ToastContainer {...containerProps} data-testid={dataTestId} aria-label={ariaLabel} />;
}

export { CommonToast, dismissToast, showConfirmToast, showToast };
export default CommonToast;
