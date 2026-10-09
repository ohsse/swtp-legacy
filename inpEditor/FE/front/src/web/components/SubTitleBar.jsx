import React from 'react';

function SubTitleBar({ title, className = '' }) {
	return (
		<div
			className={[
				'flex h-[42px] items-center px-4 text-[19px] text-white',
				className,
			].join(' ')}
			style={{
				backgroundImage: 'url(/assets/small_title_bar.png)',
				backgroundRepeat: 'no-repeat',
				backgroundSize: '100% 100%',
			}}
		>
			<span style={{ textShadow: '0 0 2px #000' }}>{title}</span>
		</div>
	);
}

export default React.memo(SubTitleBar);
