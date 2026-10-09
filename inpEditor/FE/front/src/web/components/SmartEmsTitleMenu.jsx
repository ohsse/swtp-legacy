import { Menu, MenuItem } from '@mui/material';
import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const SMART_EMS_MENU_ITEMS = [
	{ label: '관망최적화', url: '/smartEMS/model-editor' },
	/*{ label: '관망해석 시뮬레이션', url: '/smartEMS/simulation' },
	{ label: '예측모니터링', url: '/smartEMS/predMonitor' },*/
	{ label: '성능곡선관리', url: '/smartEMS/perfromCurveManage' },
];

function SmartEmsTitleMenu() {
	const navigate = useNavigate();
	const location = useLocation();
	const [anchorEl, setAnchorEl] = useState(null);
	const isOpen = Boolean(anchorEl);
	const selectedItem =
		SMART_EMS_MENU_ITEMS.find(item => location.pathname === item.url) ??
		SMART_EMS_MENU_ITEMS.find(item => location.pathname.startsWith(item.url)) ??
		SMART_EMS_MENU_ITEMS[0];

	const handleMenuOpen = event => {
		setAnchorEl(event.currentTarget);
	};

	const handleMenuClose = () => {
		setAnchorEl(null);
	};

	const handleMenuClick = item => {
		handleMenuClose();
		if (item.url === location.pathname) return;
		navigate(item.url);
	};

	return (
		<>
			<button
				type="button"
				className="inline-flex min-w-max cursor-pointer items-center gap-1.5 whitespace-nowrap border-0 bg-transparent p-0 text-left font-[inherit] font-bold leading-[1.15] text-[#d4ecff] outline-none transition hover:text-white focus-visible:text-white"
				style={{
					fontFamily: 'KHNPHUotfR, sans-serif',
					textShadow: isOpen ? '0 0 18px rgba(10,196,255,0.95)' : '0 0 20px #0ac4ff',
				}}
				aria-haspopup="menu"
				aria-expanded={isOpen ? 'true' : undefined}
				onClick={handleMenuOpen}
			>
				<span>{selectedItem.label}</span>
				<span
					className={[
						'mt-0.5 inline-flex h-3.5 w-3.5 items-center justify-center text-[13px] leading-none text-[#d4ecff]/80 transition-transform',
						isOpen ? 'rotate-180' : '',
					].join(' ')}
				>
					▾
				</span>
			</button>
			<Menu
				anchorEl={anchorEl}
				open={isOpen}
				onClose={handleMenuClose}
				anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
				transformOrigin={{ vertical: 'top', horizontal: 'left' }}
				slotProps={{
					paper: {
						sx: {
							mt: 0.5,
							minWidth: 240,
							borderRadius: '8px',
							border: '1px solid rgba(110, 185, 255, 0.34)',
							background: 'linear-gradient(180deg, rgba(16, 43, 82, 0.98), rgba(7, 22, 48, 0.98))',
							boxShadow: '0 16px 36px rgba(2, 8, 23, 0.42), inset 0 1px 0 rgba(255,255,255,0.06)',
							overflow: 'hidden',
						},
					},
					list: {
						sx: { py: 0.5 },
					},
				}}
			>
				{SMART_EMS_MENU_ITEMS.map(item => {
					const isSelected = selectedItem.url === item.url;
					return (
						<MenuItem
							key={item.url}
							selected={isSelected}
							onClick={() => handleMenuClick(item)}
							sx={{
								minHeight: 38,
								px: 1.5,
								fontFamily: 'KHNPHUotfR, sans-serif',
								fontSize: 16,
								fontWeight: 700,
								color: '#d4ecff',
								textShadow: '0 0 14px rgba(10,196,255,0.76)',
								transition: 'background-color 160ms ease, color 160ms ease, text-shadow 160ms ease',
								'&.Mui-selected': {
									color: '#ffffff',
									backgroundColor: 'rgba(56, 189, 248, 0.2)',
									textShadow: '0 0 18px rgba(56,189,248,0.95)',
								},
								'&.Mui-selected:hover, &:hover': {
									color: '#ffffff',
									backgroundColor: 'rgba(56, 189, 248, 0.28)',
								},
							}}
						>
							{item.label}
						</MenuItem>
					);
				})}
			</Menu>
		</>
	);
}

export default SmartEmsTitleMenu;
