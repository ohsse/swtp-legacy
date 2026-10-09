import { Box, Tab, Tabs } from '@mui/material';

function CommonTabs({ items = [], value, onChange, children, className = '', contentClassName = '' }) {
	return (
		<Box className={className}>
			<Tabs
				value={value}
				onChange={(_, nextValue) => onChange?.(nextValue)}
				variant="scrollable"
				scrollButtons={false}
				sx={{
					minHeight: 44,
					borderBottom: '1px solid rgba(100, 116, 139, 0.28)',
					'& .MuiTabs-flexContainer': { gap: '12px' },
					'& .MuiTabs-indicator': {
						height: '2px',
						borderRadius: '999px',
						backgroundColor: '#7dd3fc',
					},
				}}
			>
				{items.map(item => (
					<Tab
						key={item.v}
						value={item.v}
						label={item.k}
						disableRipple
						sx={{
							minHeight: 44,
							minWidth: 'fit-content',
							paddingX: '8px',
							paddingY: '10px',
							color: 'rgba(226,232,240,0.68)',
							textTransform: 'none',
							fontSize: '0.9rem',
							fontWeight: 600,
							letterSpacing: '0.01em',
							'&.Mui-selected': {
								color: '#d9f2ff',
							},
						}}
					/>
				))}
			</Tabs>
			<Box className={contentClassName}>{children}</Box>
		</Box>
	);
}

export { CommonTabs };
export default CommonTabs;
