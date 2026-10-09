import { Button } from '@mui/material';
import { useState } from 'react';
import { showConfirmToast } from '@/web/components/common/CommonToast.jsx';

function cn(...classNames) {
	return classNames.filter(Boolean).join(' ');
}

function DefaultLoadingIcon({ className = '' }) {
	return (
		<svg
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth="2"
			strokeLinecap="round"
			strokeLinejoin="round"
			className={className}
			aria-hidden="true"
		>
			<path d="M21 12a9 9 0 1 1-6.219-8.56" />
		</svg>
	);
}

function resolveSurfaceClassName(variant) {
	if (variant === 'outline') {
		return cn(
			'rounded-[3px] border-[#4d6f9c] bg-[linear-gradient(180deg,#182f5a,#102649)] text-white',
			'shadow-[inset_0_1px_0_rgba(255,255,255,0.05)] hover:border-[#79a9e0] hover:bg-[linear-gradient(180deg,#244677,#17355f)] hover:text-white',
			'focus-visible:border-[#9fd2ff] focus-visible:ring-[rgba(159,210,255,0.18)] disabled:border-[#314766] disabled:bg-[linear-gradient(180deg,#142442,#0d1d38)] disabled:text-[rgba(255,255,255,0.45)]'
		);
	}
	if (variant === 'ghost') {
		return 'rounded-[3px] border-transparent bg-transparent text-white hover:border-[#34557d] hover:bg-[rgba(20,44,88,0.48)] hover:text-white';
	}
	if (variant === 'secondary') {
		return cn(
			'rounded-[3px] border-[#7397c7] bg-[linear-gradient(180deg,#21406f,#17325c)] text-white',
			'shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] hover:border-[#9dc7ff] hover:bg-[linear-gradient(180deg,#2b538a,#1d4273)]'
		);
	}
	if (variant === 'destructive') {
		return cn(
			'rounded-[3px] border-[#ff8d96] bg-[linear-gradient(180deg,#d63f4d,#9f2431)] text-white',
			'shadow-[inset_0_1px_0_rgba(255,255,255,0.14),0_8px_16px_rgba(159,36,49,0.22)]',
			'hover:border-[#ffb1b8] hover:bg-[linear-gradient(180deg,#ec5260,#b92d3b)] focus-visible:border-[#ffc7cc] focus-visible:ring-[rgba(255,141,150,0.24)]',
			'disabled:border-[#88444c] disabled:bg-[linear-gradient(180deg,#5a2730,#411c24)] disabled:text-[rgba(255,255,255,0.58)] disabled:shadow-none'
		);
	}
	if (variant === 'link') {
		return 'rounded-[3px] border-transparent bg-transparent px-1 text-white hover:text-white';
	}
	return cn(
		'rounded-[3px] border-[#9fd2ff] bg-[linear-gradient(180deg,#305f9a,#214b7f)] text-white',
		'shadow-[inset_0_0_8px_rgba(148,220,255,0.45)] hover:border-[#c7e8ff] hover:bg-[linear-gradient(180deg,#3a6ba8,#2a568d)]',
		'focus-visible:border-[#c7e8ff] focus-visible:ring-[rgba(159,210,255,0.2)] disabled:border-[#4c6286] disabled:bg-[linear-gradient(180deg,#203b60,#172c49)] disabled:text-[rgba(255,255,255,0.45)]'
	);
}

function resolveSizeClassName(size) {
	if (size === 'xs') return 'h-6 rounded-[3px] px-2 text-[11px]';
	if (size === 'sm') return 'h-7 rounded-[3px] px-3 text-[11px] font-medium';
	if (size === 'lg') return 'h-8 rounded-[3px] px-4 text-[12px] font-medium';
	if (size === 'icon') return 'size-8 rounded-[3px]';
	if (size === 'icon-xs') return 'size-6 rounded-[3px]';
	if (size === 'icon-sm') return 'size-7 rounded-[3px]';
	if (size === 'icon-lg') return 'size-9 rounded-[3px]';
	return 'h-8 rounded-[3px] px-3.5 text-[12px] font-medium';
}

const CONFIRM_RULES = [
	{ keyword: '저장', message: '저장하시겠습니까?' },
	{ keyword: '실행', message: '실행 하시겠습니까?' },
	{ keyword: '삭제', message: '삭제하시겠습니까?' },
];

function resolveButtonName(text, children) {
	if (typeof children === 'string' || typeof children === 'number') {
		return String(children);
	}
	return String(text ?? '');
}

function resolveConfirmMessage(buttonName) {
	const normalizedButtonName = String(buttonName ?? '').trim();
	if (!normalizedButtonName) return null;

	return CONFIRM_RULES.find(rule => normalizedButtonName.includes(rule.keyword))?.message ?? null;
}

function resolveButtonVariant(buttonName, variant) {
	const normalizedButtonName = String(buttonName ?? '').trim();
	if (normalizedButtonName.includes('삭제')) return 'destructive';
	if (normalizedButtonName.includes('저장')) return 'default';
	return variant ?? 'default';
}

function CommonButton({
	text = '',
	className = '',
	variant,
	size = 'default',
	disableRipple = true,
	rippleColor = 'rgba(159, 210, 255, 0.34)',
	Icon = null,
	iconClassName = '',
	iconPosition = 'start',
	isDisabled = false,
	isLoading = false,
	loadingText,
	LoadingIcon = DefaultLoadingIcon,
	preventDoubleClick = false,
	dataTestId,
	ariaLabel,
	children,
	onClick,
	disabled,
	type = 'button',
	sx: sxProp,
	...props
}) {
	const [isSubmitting, setIsSubmitting] = useState(false);
	const content = children ?? text;
	const buttonName = resolveButtonName(text, children);
	const resolvedVariant = resolveButtonVariant(buttonName, variant);
	const surfaceClassName = resolveSurfaceClassName(resolvedVariant);
	const sizeClassName = resolveSizeClassName(size);
	const isBusy = isLoading || (preventDoubleClick && isSubmitting);
	const resolvedDisabled = Boolean(disabled || isDisabled || isBusy);
	const resolvedContent = isBusy && loadingText ? loadingText : content;
	const confirmMessage = resolveConfirmMessage(buttonName);
	const resolvedSx = [
		{
			minWidth: 0,
			textTransform: 'none',
			lineHeight: 1,
			'& .MuiTouchRipple-child': {
				backgroundColor: rippleColor,
			},
		},
		...(Array.isArray(sxProp) ? sxProp : sxProp ? [sxProp] : []),
	];

	const handleClick = async (...args) => {
		if (!onClick || resolvedDisabled) return;
		if (confirmMessage) {
			const confirmed = await showConfirmToast(confirmMessage);
			if (!confirmed) return;
		}
		if (!preventDoubleClick) {
			onClick(...args);
			return;
		}

		setIsSubmitting(true);
		try {
			await Promise.resolve(onClick(...args));
		} finally {
			setIsSubmitting(false);
		}
	};

	return (
		<Button
			type={type}
			variant="text"
			className={cn(
				'inline-flex items-center justify-center gap-2 border outline-none',
				'transition-[background-color,border-color,color,box-shadow,transform,opacity] duration-200 ease-out',
				'focus-visible:ring-2 active:translate-y-px active:scale-[0.985]',
				'disabled:translate-y-0 disabled:scale-100 motion-reduce:transition-none',
				surfaceClassName,
				sizeClassName,
				className,
				isBusy ? 'cursor-wait' : ''
			)}
			disableElevation
			disableRipple={disableRipple}
			disabled={resolvedDisabled}
			onClick={handleClick}
			data-testid={dataTestId}
			aria-label={ariaLabel}
			sx={resolvedSx}
			{...props}
		>
			{isBusy ? <LoadingIcon className={cn('size-4 animate-spin', iconClassName)} /> : null}
			{!isBusy && Icon && iconPosition === 'start' ? <Icon className={iconClassName} /> : null}
			{resolvedContent}
			{!isBusy && Icon && iconPosition === 'end' ? <Icon className={iconClassName} /> : null}
		</Button>
	);
}

export { CommonButton, DefaultLoadingIcon, resolveButtonVariant, resolveConfirmMessage, resolveSizeClassName, resolveSurfaceClassName };
export default CommonButton;
