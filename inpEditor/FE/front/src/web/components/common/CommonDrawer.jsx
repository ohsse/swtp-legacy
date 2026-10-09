import { Box, Drawer } from '@mui/material';
import { isValidElement } from 'react';
import { IoClose } from 'react-icons/io5';
import CommonButton from '@/web/components/common/CommonButton.jsx';

function cn(...classNames) {
	return classNames.filter(Boolean).join(' ');
}

function resolveContent(content) {
	if (content == null) {
		return null;
	}

	if (isValidElement(content)) {
		return content;
	}

	if (typeof content === 'function') {
		const ContentComponent = content;
		return <ContentComponent />;
	}

	return content;
}

function CommonDrawer({
	open = false,
	setOpen,
	content = null,
	className = '',
	anchor = 'right',
	showCloseButton = true,
	closeButtonClassName = '',
	closeButtonAriaLabel = '닫기',
	bodyClassName = 'relative h-full w-full overflow-y-auto overflow-x-hidden',
	children,
	PaperProps,
	paperProps,
	ModalProps,
	...props
}) {
	const resolvedPaperProps = paperProps ?? PaperProps ?? {};
	const mergedPaperClassName = cn(resolvedPaperProps.className, className);

	const handleClose = () => {
		setOpen?.(false);
	};

	return (
		<Drawer
			anchor={anchor}
			open={open}
			onClose={handleClose}
			transitionDuration={{ enter: 320, exit: 220 }}
			SlideProps={{
				appear: true,
			}}
			{...props}
			ModalProps={ModalProps}
			slotProps={{
				paper: {
					...resolvedPaperProps,
					className: mergedPaperClassName,
				},
			}}
		>
			<Box className={bodyClassName}>
				{showCloseButton ? (
					<CommonButton
						ariaLabel={closeButtonAriaLabel}
						iconPosition="start"
						size="icon-sm"
						variant="ghost"
						className={cn(
							'absolute right-0 top-0 z-20 border-0 bg-transparent text-slate-300 shadow-none hover:bg-white/8 hover:text-white',
							closeButtonClassName
						)}
						onClick={handleClose}
					>
						<IoClose className="h-4 w-4" />
					</CommonButton>
				) : null}
				{resolveContent(content) ?? children}
			</Box>
		</Drawer>
	);
}

export default CommonDrawer;
