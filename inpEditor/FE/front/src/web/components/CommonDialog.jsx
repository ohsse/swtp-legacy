import { Dialog, DialogActions, DialogContent, DialogTitle, IconButton } from '@mui/material'
import { CommonButton } from '@/web/components/common/CommonButton'

function resolveDialogOption(option = {}) {
	return {
		title: option.title ?? '',
		description: option.description ?? '',
		contentClassName: option.contentClassName ?? '',
		bodyClassName: option.bodyClassName ?? '',
		footerClassName: option.footerClassName ?? '',
		backdropClassName: option.backdropClassName ?? '',
		viewportClassName: option.viewportClassName ?? '',
		titleClassName: option.titleClassName ?? '',
		descriptionClassName: option.descriptionClassName ?? '',
		headerClassName: option.headerClassName ?? '',
		closeClassName: option.closeClassName ?? '',
		showCloseButton: option.showCloseButton !== false,
		showFooter: option.showFooter !== false,
		closeOnBackdrop: option.closeOnBackdrop !== false,
		closeLabel: option.closeLabel ?? '닫기',
		widthClassName: option.widthClassName ?? 'max-w-lg',
	}
}

function CommonDialog({
	open,
	setOpen,
	modalOpen,
	setModalOpen,
	children,
	option,
	buttons = [],
	trigger,
	dataTestId,
	ariaLabel,
}) {
	const resolvedOpen = typeof open === 'boolean' ? open : Boolean(modalOpen)
	const resolvedSetOpen = setOpen ?? setModalOpen
	const resolvedOption = resolveDialogOption(option)

	const handleOpenChange = nextOpen => {
		resolvedSetOpen?.(nextOpen)
	}

	const handleClose = () => {
		resolvedSetOpen?.(false)
	}

	const renderFooterButton = (button, index) => {
		const {
			key,
			label,
			text,
			onClick,
			closeOnClick = false,
			variant = 'default',
			disabled = false,
			...buttonProps
		} = button

		const buttonLabel = label ?? text ?? `button-${index + 1}`

		return (
			<CommonButton
				key={key ?? buttonLabel}
				text={buttonLabel}
				variant={variant}
				isDisabled={disabled}
				onClick={async event => {
					await Promise.resolve(onClick?.(event))
					if (closeOnClick) {
						handleClose()
					}
				}}
				{...buttonProps}
			/>
		)
	}

	return (
		<>
			{trigger ? <span onClick={() => handleOpenChange(true)}>{trigger}</span> : null}
			<Dialog
				open={resolvedOpen}
				onClose={(_, reason) => {
					if (!resolvedOption.closeOnBackdrop && reason === 'backdropClick') {
						return
					}
					handleOpenChange(false)
				}}
				fullWidth
				maxWidth={false}
				slotProps={{
					backdrop: {
						className: ['bg-slate-950/65 backdrop-blur-[2px]', resolvedOption.backdropClassName].filter(Boolean).join(' '),
					},
					paper: {
						className: [
							'w-full rounded-xl border border-slate-200 bg-white text-left shadow-2xl',
							resolvedOption.widthClassName,
							resolvedOption.contentClassName,
						]
							.filter(Boolean)
							.join(' '),
						'data-testid': dataTestId,
						'aria-label': ariaLabel,
					},
					container: {
						className: ['p-4', resolvedOption.viewportClassName].filter(Boolean).join(' '),
					},
				}}
			>
				{resolvedOption.title || resolvedOption.description ? (
					<div className={['flex items-start justify-between gap-4 px-6 pt-6', resolvedOption.headerClassName].filter(Boolean).join(' ')}>
						<div className="min-w-0 flex-1">
							{resolvedOption.title ? (
								<DialogTitle className={['p-0 text-lg font-semibold text-slate-950', resolvedOption.titleClassName].filter(Boolean).join(' ')}>
									{resolvedOption.title}
								</DialogTitle>
							) : null}
							{resolvedOption.description ? (
								<p className={['mt-1 text-sm text-slate-500', resolvedOption.descriptionClassName].filter(Boolean).join(' ')}>
									{resolvedOption.description}
								</p>
							) : null}
						</div>
						{resolvedOption.showCloseButton ? (
							<IconButton
								onClick={handleClose}
								aria-label={resolvedOption.closeLabel}
								className={['text-slate-400 transition hover:bg-slate-100 hover:text-slate-700', resolvedOption.closeClassName]
									.filter(Boolean)
									.join(' ')}
							>
								<span className="text-lg leading-none">×</span>
							</IconButton>
						) : null}
					</div>
				) : null}

				<DialogContent className={['px-6 pb-0 pt-4', resolvedOption.bodyClassName].filter(Boolean).join(' ')}>{children}</DialogContent>

				{resolvedOption.showFooter && buttons.length > 0 ? (
					<DialogActions className={['px-6 pb-6 pt-6', resolvedOption.footerClassName].filter(Boolean).join(' ')}>
						{buttons.map(renderFooterButton)}
					</DialogActions>
				) : null}
			</Dialog>
		</>
	)
}

export { CommonDialog }
export default CommonDialog
