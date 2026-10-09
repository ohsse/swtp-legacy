import { Box, Modal } from '@mui/material';
import { CommonButton } from '@/web/components/common/CommonButton';
import { IoClose } from 'react-icons/io5';

function resolveSlotContent(content) {
	if (content == null) return null;
	if (typeof content === 'function') {
		const ContentComponent = content;
		return <ContentComponent />;
	}
	return content;
}

const modalPresetByKey = {
	editor: {
		overlayClassName: 'bg-[rgba(6,16,38,0.44)] backdrop-blur-[3px]',
		contentClassName:
			'rounded-[18px] border border-[rgba(110,185,255,0.22)] bg-[linear-gradient(180deg,rgba(14,28,58,0.98),rgba(10,21,46,0.98))] shadow-[0_28px_80px_rgba(2,9,34,0.58)]',
		headerClassName:
			'border-b border-[rgba(110,185,255,0.18)] bg-[linear-gradient(180deg,rgba(43,65,126,0.96),rgba(31,49,101,0.98))] px-6 py-4',
		bodyClassName: 'bg-transparent px-4 pb-4 pt-4',
		footerClassName: 'border-t border-[rgba(110,185,255,0.14)] bg-[rgba(7,17,37,0.42)] px-4 pb-4 pt-3',
		closeButtonClassName: 'rounded-[8px] text-[20px] text-sky-100/78 hover:bg-white/10 hover:text-white',
		titleClassName: 'text-[22px] font-semibold tracking-[-0.02em] text-white',
	},
};

export function CommonModal({
	open,
	onOpenChange,
	title,
	description,
	children,
	onMove,
	actionLabel = '이동',
	cancelLabel = '취소',
	showCancel = true,
	moveBtnProps,
	cancelBtnProps,
	extraActions,
	topRightAction,
	buttons,
	isDisabled = false,
	actionDisabled = false,
	actionLoading = false,
	closeOnAction = true,
	closeOnBackdrop = true,
	preset,
	contentClassName = '',
	overlayClassName = '',
	headerClassName = '',
	bodyClassName = '',
	footerClassName = '',
	closeButtonClassName = '',
	titleClassName = '',
	showFooter = true,
	panelSx,
	dataTestId,
	ariaLabel,
}) {
	const isPrimaryActionDisabled = isDisabled || actionDisabled || actionLoading;
	const presetConfig = modalPresetByKey[preset] ?? {};

	const requestClose = () => {
		if (actionLoading) return;
		onOpenChange(false);
	};

	const handleModalClose = (_, reason) => {
		if (actionLoading) return;
		if (!closeOnBackdrop && reason === 'backdropClick') return;
		requestClose();
	};

	const handleMove = async () => {
		if (isPrimaryActionDisabled) return;
		await Promise.resolve(onMove?.());
		if (closeOnAction) {
			onOpenChange(false);
		}
	};

	return (
		<Modal open={open} onClose={handleModalClose} disableEscapeKeyDown={actionLoading}>
			<Box
				className={[
					'flex min-h-screen items-center justify-center px-6 py-8',
					presetConfig.overlayClassName,
					overlayClassName,
				]
					.filter(Boolean)
					.join(' ')}
				sx={{
					bgcolor: 'rgba(4,19,57,0.72)',
				}}
				data-testid={dataTestId}
				aria-label={ariaLabel}
			>
				<Box
					className={[
						'relative w-[min(96vw,1180px)] overflow-hidden rounded-[4px] border border-sky-300/30 bg-[linear-gradient(180deg,rgba(11,24,55,0.96),rgba(9,20,49,0.96))] shadow-[0_18px_48px_rgba(2,9,34,0.62)]',
						presetConfig.contentClassName,
						contentClassName,
					]
						.filter(Boolean)
						.join(' ')}
					sx={panelSx}
				>
					<div
						className={[
							'relative border-b border-sky-300/24 bg-[linear-gradient(180deg,#2d3e82,#24356d)] px-5 py-4',
							presetConfig.headerClassName,
							headerClassName,
						]
							.filter(Boolean)
							.join(' ')}
					>
						<div className="flex items-start justify-between gap-4">
							<div className="min-w-0">
								<h2
									className={[
										'text-[24px] font-semibold text-sky-50',
										presetConfig.titleClassName,
										titleClassName,
									]
										.filter(Boolean)
										.join(' ')}
								>
									{title}
								</h2>
								{description ? <p className="mt-2 text-[13px] leading-6 text-sky-100/80">{description}</p> : null}
							</div>
							<div className="flex items-center gap-3">
								{topRightAction}
								<CommonButton
									size="icon-sm"
									variant="ghost"
									className={[
										'text-sky-100/72 hover:bg-transparent hover:text-white',
										presetConfig.closeButtonClassName,
										closeButtonClassName,
									]
										.filter(Boolean)
										.join(' ')}
									onClick={requestClose}
									ariaLabel="닫기"
									Icon={IoClose}
									iconClassName="size-5"
								/>
							</div>
						</div>
					</div>

					<div className={['px-3 py-4', presetConfig.bodyClassName, bodyClassName].filter(Boolean).join(' ')}>
						{children}
					</div>

					{showFooter ? (
						<div
							className={[
								'flex items-center justify-end gap-3 px-5 pb-5 pt-2',
								presetConfig.footerClassName,
								footerClassName,
							]
								.filter(Boolean)
								.join(' ')}
						>
							{extraActions}
							{resolveSlotContent(buttons) ??
								(actionLabel ? (
									<CommonButton
										text={actionLabel}
										size="default"
										isDisabled={isPrimaryActionDisabled}
										isLoading={actionLoading}
										onClick={handleMove}
										{...(moveBtnProps ?? {})}
									/>
								) : null)}
							{buttons == null && showCancel ? (
								<CommonButton
									text={cancelLabel}
									size="default"
									variant="outline"
									isDisabled={actionLoading}
									onClick={requestClose}
									{...(cancelBtnProps ?? {})}
								/>
							) : null}
						</div>
					) : null}
				</Box>
			</Box>
		</Modal>
	);
}

export default CommonModal;
