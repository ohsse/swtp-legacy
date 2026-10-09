import { Spinner } from '@/web/components/common/Spinner.jsx';
import CommonToast, { showConfirmToast } from '@/web/components/common/CommonToast.jsx';
import { BASE_URL, DEFAULT_BACKGROUND_MAP } from '@/consts/index.js';
import { StzUtils } from 'stzutil-js/browser';
import Layout from '@/web/pages/Layout.jsx';
import PerformCurveManage from '@/web/pages/perFromCurveManage/PerformCurveManage.jsx';
import PredMonitor from '@/web/pages/predMonitor/PredMonitor.jsx';
import TestMap from '@/web/pages/TestMap.jsx';
import { useEffect, useState, useRef } from 'react';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import PipNetAnals from '@/web/pages/PipNetAnals.jsx';
import PipNetSimulation from '@/web/pages/PipNetSimulation.jsx';
import ModelEditorPageTemp from '@/web/pages/ModelEditorPageTemp.jsx';
import ModelEditorPage from '@/web/pages/ModelEditorPage.jsx';
import ModalTestPage from '@/web/pages/ModalTestPage.jsx';
import ScatterChartPage from '@/web/pages/ScatterChartPage.jsx';

function registerStzUtilsGlobal() {
	window.stz = () => StzUtils.stz();
	window.stzUtil = StzUtils;
	window.StzUtils = StzUtils;
}

registerStzUtilsGlobal();

function buildApiUrl(path) {
	const normalizedBaseUrl = String(BASE_URL ?? '').replace(/\/+$/, '');
	const normalizedPath = String(path ?? '').replace(/^\/+/, '');

	return `${normalizedBaseUrl}/${normalizedPath}`;
}

function resolveArrayPayload(payload) {
	if (Array.isArray(payload)) return payload;
	if (Array.isArray(payload?.data)) return payload.data;
	if (Array.isArray(payload?.result)) return payload.result;
	if (Array.isArray(payload?.list)) return payload.list;
	if (Array.isArray(payload?.items)) return payload.items;
	if (Array.isArray(payload?.rows)) return payload.rows;
	if (payload && typeof payload === 'object') return [payload];

	return [];
}

function createTagCorrectionNotifyBody(pendingSeq) {
	const keys = pendingSeq
		.map(item => ({
			measTs: item?.measTs ?? item?.measTS ?? item?.meansTS,
			tagNo: item?.tagNo,
		}))
		.filter(key => key.measTs !== undefined && key.measTs !== null && key.tagNo !== undefined && key.tagNo !== null);

	return keys.length > 0 ? { keys } : null;
}

function resolveTagCorrectionMessage(payload) {
	if (typeof payload?.message === 'string' && payload.message.trim()) {
		return payload.message.trim();
	}

	const pendingSeq = resolveArrayPayload(payload);
	const messageSeq = pendingSeq
		.map(item => item?.message)
		.filter(message => typeof message === 'string' && message.trim())
		.map(message => message.trim());

	if (messageSeq.length > 0) {
		return messageSeq.join('\n');
	}

	return '이상값이 발생했습니다.';
}

function RouteHistoryTracker({ linkRef, setCurrent }) {
	const location = useLocation();

	useEffect(() => {
		const item = {
			nodeId: location.pathname,
			node: location.pathname,
		};

		linkRef.current.add(item);
		setCurrent(item);

		console.log('history size:', linkRef.current.getSize);
		console.log('current:', linkRef.current);
	}, [location.pathname, linkRef, setCurrent]);

	return null;
}

function App() {
	const [, setResult] = useState(null);
	const linkRef = useRef(StzUtils.addLinkedList());
	const [current, setCurrent] = useState(undefined);
	useEffect(() => {
		let isRequesting = false;

		const toggleFullScreen = () => {
			if (!document.fullscreenElement) {
				document.documentElement.requestFullscreen?.();
			} else {
				document.exitFullscreen?.();
			}
		};

		const handleKeyDown = event => {
			if (event.ctrlKey && event.key === 'Enter') {
				event.preventDefault();
				toggleFullScreen();
			}
		};

		document.addEventListener('keydown', handleKeyDown);

		const loadPendingTagCorrections = async () => {
			if (isRequesting) return;
			isRequesting = true;

			try {
				const pendingResponse = await fetch(buildApiUrl('/tag-corrections/pending'));
				if (!pendingResponse.ok) return;

				const pendingPayload = await pendingResponse.json();
				const pendingSeq = resolveArrayPayload(pendingPayload);
				setResult(pendingSeq);

				const notifyBody = createTagCorrectionNotifyBody(pendingSeq);
				if (!notifyBody) return;

				const confirmed = await showConfirmToast(resolveTagCorrectionMessage(pendingPayload), {
					type: 'error',
					confirmLabel: '확인',
					cancelLabel: '취소',
				});
				if (!confirmed) return;

				await fetch(buildApiUrl('/tag-corrections/notify'), {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
					},
					body: JSON.stringify(notifyBody),
				});
			} catch (e) {
				console.error(e);
			} finally {
				isRequesting = false;
			}
		};

		// void loadPendingTagCorrections();
		// const intervalId = setInterval(loadPendingTagCorrections, 5000);
		//
		// return () => {
		// 	clearInterval(intervalId);
		// 	document.removeEventListener('keydown', handleKeyDown);
		// };
	}, []);

	return (
		<>
			<Spinner />
			<CommonToast />
			<BrowserRouter>
				<RouteHistoryTracker linkRef={linkRef} setCurrent={setCurrent} />
				<Routes>
					<Route element={<Layout />}>
						<Route path="/" element={<Navigate to="/smartEMS/model-editor" replace />} />
						{/*<Route path="/smartEMS/modelEiditor-temp" element={<ModelEditorPageTemp />} />*/}
						<Route path="/smartEMS/model-editor" element={<ModelEditorPage />} />
						<Route path={'/smartEMS/predMonitor'} element={<PredMonitor />} />
						<Route path={'/smartEMS/perfromCurveManage'} element={<PerformCurveManage />} />
						<Route path="/smartEMS/simulation" element={<PipNetSimulation />} />
						<Route path="/smartEMS/:mode" element={<PipNetAnals />} />
						<Route path="/modaltest/test" element={<ModalTestPage />} />
						<Route path="/chart/scatter" element={<ScatterChartPage />} />
						<Route path={'/test/test-map'} element={<TestMap />} />
						<Route path="*" element={<Navigate to="/smartEMS/model-editor" replace />} />
					</Route>
				</Routes>
			</BrowserRouter>
		</>
	);
}

export default App;
