import React from 'react';

function cn(...classNames) {
	return classNames.filter(Boolean).join(' ');
}

const defaultCardStyle = {
	border: '1px solid #6eb9ff59',
};

function CommonCard({ as: Tag = 'div', className = '', style, children, ...props }) {
	return (
		<Tag
			className={cn(
				'rounded-[8px] bg-[linear-gradient(180deg,rgba(10,27,59,0.92),rgba(8,20,44,0.94))] shadow-none',
				className
			)}
			style={{ ...defaultCardStyle, ...style }}
			{...props}
		>
			{children}
		</Tag>
	);
}

export { defaultCardStyle };
export default React.memo(CommonCard);
