import React from 'react';
function resolveSizeClassName(size) {
	if (size === 'sm') return 'h-[56px] w-[280px] px-4 pt-2 text-[24px]';
	if (size === 'lg') return 'h-[80px] w-[360px] px-5 pt-2 text-[31px]';
	return 'h-[72px] w-[320px] px-4 pt-2 text-[28px]';
}

export function TitleBar({ title, className = '', subtitle, rightSlot, size = 'md', isDisabled = false, dataTestId, ariaLabel }) {
	return (
		<div
			data-testid={dataTestId}
			aria-label={ariaLabel}
			className={[
				'relative flex items-start font-semibold text-[#d4ecff]',
				resolveSizeClassName(size),
				isDisabled ? 'opacity-55' : '',
				className,
			].join(' ')}
			style={{
				backgroundImage: 'url(/assets/big_title_bar.png)',
				backgroundRepeat: 'no-repeat',
				backgroundSize: '100% 100%',
				fontFamily: 'KHNPHUotfR, sans-serif',
				textShadow: '0 0 20px #0ac4ff',
			}}
		>
			<div className="flex h-full min-w-0 w-full items-start justify-between gap-3">
				<div className="min-w-0">
					<div className="truncate">{title}</div>
					{subtitle ? <div className="truncate text-[11px] font-normal text-sky-100/80">{subtitle}</div> : null}
				</div>
				{rightSlot ? <div className="shrink-0">{rightSlot}</div> : null}
			</div>
		</div>
	);
}

export default React.memo(TitleBar);
