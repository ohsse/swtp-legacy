import dayjs from 'dayjs';
import { useEffect, useState } from 'react';
import SmartEmsTitleMenu from '@/web/components/SmartEmsTitleMenu.jsx';
import TitleBar from '@/web/components/TitleBar.jsx';

function SmartEmsCurrentTime() {
	const [currentTime, setCurrentTime] = useState(() => dayjs().format('YYYY.MM.DD HH:mm:ss'));

	useEffect(() => {
		const timerId = window.setInterval(() => {
			setCurrentTime(dayjs().format('YYYY.MM.DD HH:mm:ss'));
		}, 1000);

		return () => window.clearInterval(timerId);
	}, []);

	return (
		<div className="flex shrink-0 items-center whitespace-nowrap pt-1">
			<span
				className="text-[16px] leading-none text-[#c3eaff] [text-shadow:0_0_5px_rgba(101,183,255)]"
				style={{ fontFamily: 'KHNPHUotfR, sans-serif' }}
			>
				현재시각&nbsp;
			</span>
			<span
				className="text-[22px] leading-none text-[#c3eaff] [text-shadow:0_0_5px_rgba(101,183,255)]"
				style={{ fontFamily: 'LABDigital, monospace' }}
			>
				{currentTime}
			</span>
		</div>
	);
}

function SmartEmsPageHeader({ className = '' }) {
	return (
		<div className={['flex h-[44px] min-w-0 items-start justify-between gap-4', className].filter(Boolean).join(' ')}>
			<TitleBar
				title={<SmartEmsTitleMenu />}
				size="sm"
				className="h-[46px] w-[340px] max-w-[340px] shrink-0 px-3 pt-1 text-[22px]"
			/>
			<SmartEmsCurrentTime />
		</div>
	);
}

export default SmartEmsPageHeader;
export { SmartEmsCurrentTime };
