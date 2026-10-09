import { Dialog, DialogContent, DialogTitle, IconButton } from '@mui/material';

function cn(...classNames) {
	return classNames.filter(Boolean).join(' ');
}

function CommonDialog({
	visible = true,
	open = false,
	setOpen,
	title = '',
	children,
	className = '',
	contentClassName = '',
	width = 1100,
	maxWidth = false,
	onClose,
	showCloseButton = true,
	paperSx,
}) {
	if (!visible) {
		return null;
	}

	const handleClose = () => {
		onClose?.();
		setOpen?.(false);
	};

	return (
		<Dialog
			open={open}
			onClose={handleClose}
			maxWidth={maxWidth}
			slotProps={{
				paper: {
					className: cn('overflow-hidden rounded-none bg-white shadow-[0_18px_48px_rgba(15,23,42,0.24)]', className),
					sx: {
						width,
						maxWidth: width,
						...paperSx,
					},
				},
			}}
		>
			<DialogTitle className="flex min-h-[52px] items-center justify-between border-b border-[#e4e9f1] px-6 py-3">
				<span className="text-[16px] font-semibold tracking-[-0.02em] text-[#3d74c5]">{title}</span>
				{showCloseButton ? (
					<IconButton
						onClick={handleClose}
						size="small"
						sx={{
							color: '#c5cad3',
							padding: '2px',
							borderRadius: 0,
						}}
					>
						<span className="text-[20px] leading-none">×</span>
					</IconButton>
				) : null}
			</DialogTitle>
			<DialogContent className={cn('bg-white p-0', contentClassName)}>{children}</DialogContent>
		</Dialog>
	);
}

export default CommonDialog;
