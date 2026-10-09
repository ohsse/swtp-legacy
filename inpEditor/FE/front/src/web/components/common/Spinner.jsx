import { MagnifyingGlass } from 'react-loader-spinner';
import { byPromise } from '../../js/utils/commonUtil.js';

const SHOW_TIME = 0.1;
const HIDE_TIME = 0.1;

export function Spinner() {
	return (
		<>
			<div
				id="common_spinner"
				style={{
					width: '100%',
					height: '100%',
					top: '0px',
					position: 'fixed',
					zIndex: '9999',
					opacity: '0.5',
					background: 'black',
					visibility: 'hidden',
					transition: `opacity ${SHOW_TIME + HIDE_TIME}s, visibility ${SHOW_TIME}s`,
				}}
			>
				<div
					style={{ display: 'inline-block', position: 'absolute', top: 'calc(50% - 3.5px)', left: 'calc(50% - 3.5px)' }}
				>
					{/*<RotatingLines strokeColor="grey" strokeWidth="5" animationDuration="0.75" width="96" visible={true} />*/}
					<MagnifyingGlass
						visible={true}
						height="80"
						width="80"
						ariaLabel="magnifying-glass-loading"
						wrapperStyle={{}}
						wrapperClass="magnifying-glass-wrapper"
						glassColor="#c0efff"
						color="#e15b64"
					/>
				</div>
			</div>
		</>
	);
}

let active = 0;

export const withSpinner = async fnc => {
	const spinner = document.getElementById('common_spinner');
	byPromise([
		async () => {
			// console.log('@@@ spinner open');
			spinner.style.visibility = 'visible';
		},
		async () => await fnc(),
		async () => {
			// console.log('@@@ spinner close');
			spinner.style.visibility = 'hidden';
		},
	]);
};

export const onSpinner = callback => {
	const spinner = document.getElementById('common_spinner');
	if (!spinner) {
		if (callback) callback();
		return;
	}
	spinner.style.opacity = '0.5';
	spinner.style.visibility = 'visible';

	active++;

	if (callback) callback();
};

export const offSpinner = (delayTime = 200) => {
	//console.trace();
	active = Math.max(0, active - 1);
	if (active > 0) return;
	const spinner = document.getElementById('common_spinner');
	setTimeout(() => {
		if (active <= 0 && spinner) {
			spinner.style.opacity = '0';
			spinner.style.visibility = 'hidden';
		}
	}, delayTime);

	// setTimeout(() => {
	// 	const spinner = document.getElementById('common_spinner');
	// 	spinner.style.opacity = '0';
	// 	setTimeout(() => {
	// 		spinner.style.visibility = 'hidden';
	// 	}, SHOW_TIME * 1000); // this must be greater than the transition time
	// }, delayTime);
};
