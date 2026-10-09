import React from 'react';
import { Outlet } from 'react-router-dom';
import SmartEmsPageHeader from '@/web/components/SmartEmsPageHeader.jsx';

const Layout = ({ children }) => {
	return (
		<div className="relative h-screen overflow-hidden bg-[radial-gradient(circle_at_top_left,rgba(75,148,255,0.12),transparent_24%),radial-gradient(circle_at_right,rgba(62,194,255,0.12),transparent_22%),linear-gradient(180deg,#050d23,#08142f_45%,#071429)] p-[18px] text-sky-50">
			<div className="h-full min-h-0">
				<div className="relative grid h-full min-h-0 grid-cols-[minmax(0,1fr)] gap-[18px]">
					<div
						className="min-w-0 overflow-hidden rounded-[22px] bg-[linear-gradient(180deg,rgba(14,32,70,0.86),rgba(8,21,47,0.92))] shadow-[0_18px_40px_rgba(0,0,0,0.24)]"
						style={{ border: '1px solid #6eb9ff59' }}
					>
						<div className="relative flex h-full min-h-0 flex-col overflow-hidden px-4 pb-3 pt-4">
							<div className="shrink-0 pb-1">
								<SmartEmsPageHeader />
							</div>
							<div className="min-h-0 flex-1">{children ?? <Outlet />}</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
};

export default Layout;
