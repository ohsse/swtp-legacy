import Chip from '@mui/material/Chip';
import React from 'react';

const toneSxMap = {
	success: {
		background: 'linear-gradient(180deg, #18c765, #0fb153)',
		color: '#ffffff',
		boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.22)',
	},
	warning: {
		background: 'linear-gradient(180deg, #f1b442, #d89317)',
		color: '#ffffff',
		boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.22)',
	},
	error: {
		background: 'linear-gradient(180deg, #ee5462, #c92f41)',
		color: '#ffffff',
		boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.2)',
	},
	info: {
		background: 'linear-gradient(180deg, #3a82dd, #2668be)',
		color: '#ffffff',
		boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.18)',
	},
	neutral: {
		background: 'linear-gradient(180deg, #6a7d94, #516378)',
		color: '#ffffff',
		boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.16)',
	},
};

const sizeSxMap = {
	sm: {
		height: 20,
		minWidth: 54,
		fontSize: 11,
		px: 1.5,
	},
	md: {
		height: 22,
		minWidth: 74,
		fontSize: 12,
		px: 2,
	},
	lg: {
		height: 26,
		minWidth: 88,
		fontSize: 13,
		px: 2.5,
	},
};

function CommonBadge({ children, label, tone = 'neutral', size = 'md', className = '', sx, ...props }) {
	const resolvedSx = [
		{
			borderRadius: '999px',
			fontWeight: 700,
			lineHeight: 1,
			whiteSpace: 'nowrap',
			'& .MuiChip-label': {
				px: 0,
				overflow: 'visible',
			},
			...(toneSxMap[tone] ?? toneSxMap.neutral),
			...(sizeSxMap[size] ?? sizeSxMap.md),
		},
		...(Array.isArray(sx) ? sx : sx ? [sx] : []),
	];

	return <Chip label={label ?? children} className={className} sx={resolvedSx} {...props} />;
}

export { CommonBadge, toneSxMap };
export default React.memo(CommonBadge);
