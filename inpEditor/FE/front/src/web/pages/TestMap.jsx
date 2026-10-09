/**
 * ═════════════════════════════════════════════════════════════
 * 📄 FILE     : TestMap.jsx
 * 📁 PACKAGE  : Inp-simulator-
 * 👤 AUTHOR   : stz
 * 🕒 CREATED  : 26. 6. 22.
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 📝 DESCRIPTION
 *   -
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 🔄 CHANGE LOG
 *   - DATE : 2026/06/22 | Author : stz | 최초 생성
 * ═════════════════════════════════════════════════════════════
 */
import MapCanvas from '@/web/components/common/MapCanvas.jsx';
import MapStatusOverlay from '@/web/pages/testmap/components/MapStatusOverlay.jsx';
import { getMap } from '@/web/js/utils/mapRegistry';
import { OlUtils as olUtils } from '@/web/js/utils/olUtils';
import React, { useEffect, useMemo, useRef } from 'react';

export const MAP_ID = 'TEST_MAP';
const SEOUL_CITY_HALL_COORDINATE = [126.9784147, 37.5666805];
const TEST_DRAG_BOX_LAYER_NAME = 'JUNCTIONS';
const TEST_DRAG_BOX_INTERACTION_KEY = '__testMapDragBoxInteraction';
const TEST_DRAG_BOX_SELECT_INTERACTION_KEY = '__testMapDragBoxSelectInteraction';

const testDragBoxFeatureCollection = {
	type: 'FeatureCollection',
	features: [
		{
			type: 'Feature',
			properties: {
				id: '서울시청-01',
				ID: '서울시청-01',
				layer: TEST_DRAG_BOX_LAYER_NAME,
				objectType: 'junction',
			},
			geometry: {
				type: 'Point',
				coordinates: [126.9784147, 37.5666805],
			},
		},
		{
			type: 'Feature',
			properties: {
				id: '덕수궁-02',
				ID: '덕수궁-02',
				layer: TEST_DRAG_BOX_LAYER_NAME,
				objectType: 'junction',
			},
			geometry: {
				type: 'Point',
				coordinates: [126.9751, 37.5658],
			},
		},
		{
			type: 'Feature',
			properties: {
				id: '광화문-03',
				ID: '광화문-03',
				layer: TEST_DRAG_BOX_LAYER_NAME,
				objectType: 'junction',
			},
			geometry: {
				type: 'Point',
				coordinates: [126.9769, 37.5716],
			},
		},
		{
			type: 'Feature',
			properties: {
				id: '선택제외-04',
				ID: '선택제외-04',
				layer: TEST_DRAG_BOX_LAYER_NAME,
				objectType: 'junction',
				COLOR_BIO: '#CC6767',
			},
			geometry: {
				type: 'Point',
				coordinates: [126.982, 37.5682],
			},
		},
	],
};

const overlayAnalysisMetricSeq = [
	{
		key: 'flow',
		label: '유량',
		unit: 'm³/h',
		observedMin: 20,
		observedMax: 60,
		fractionDigits: 1,
	},
	{
		key: 'pressure',
		label: '압력',
		unit: 'kgf/cm²',
		observedMin: 1,
		observedMax: 4,
		fractionDigits: 1,
	},
];

function getRandomValue(min, max, fractionDigits = 1) {
	return (Math.random() * (max - min) + min).toFixed(fractionDigits);
}

function getAnalysisMetric(metric) {
	const observed = Number(getRandomValue(metric.observedMin, metric.observedMax, metric.fractionDigits));
	const predicted = Number((observed * (1 + (Math.random() * 0.16 - 0.08))).toFixed(metric.fractionDigits));
	const errorRate = observed === 0 ? 0 : Math.abs(((predicted - observed) / observed) * 100);

	return {
		...metric,
		observed: observed.toFixed(metric.fractionDigits),
		predicted: predicted.toFixed(metric.fractionDigits),
		errorRate: errorRate.toFixed(1),
	};
}

function TestMap() {
	const overlayRef = useRef(null);
	const overlayMetrics = useMemo(() => overlayAnalysisMetricSeq.map(metric => getAnalysisMetric(metric)), []);

	useEffect(() => {
		let animationFrameId = null;
		let overlay = null;

		const attachOverlay = () => {
			const map = getMap(MAP_ID);
			if (!map || !overlayRef.current) {
				animationFrameId = window.requestAnimationFrame(attachOverlay);
				return;
			}

			overlay = olUtils.addOverlay(
				map,
				{
					element: overlayRef.current,
					positioning: 'bottom-center',
					offset: [0, -12],
					stopEvent: true,
				},
				olUtils.fromLonLat(SEOUL_CITY_HALL_COORDINATE, olUtils.getMapProjectionCode(map))
			);
		};

		attachOverlay();

		return () => {
			if (animationFrameId) window.cancelAnimationFrame(animationFrameId);
			olUtils.removeOverlay(getMap(MAP_ID), overlay);
		};
	}, []);

	useEffect(() => {
		let animationFrameId = null;
		let targetMap = null;

		const attachDragBox = () => {
			const map = getMap(MAP_ID);
			if (!map) {
				animationFrameId = window.requestAnimationFrame(attachDragBox);
				return;
			}

			targetMap = map;
			olUtils.setLayerOnMap(map, testDragBoxFeatureCollection, TEST_DRAG_BOX_LAYER_NAME, {
				dataProjection: 'EPSG:4326',
				featureProjection: olUtils.getMapProjectionCode(map),
				visibleNodeTagYn: true,
			});
			olUtils.setDragBox(
				map,
				({ features }) => {
					console.log(
						'[TestMap] dragBox selected features:',
						features.map(feature => feature.get('id') ?? feature.get('ID'))
					);
				},
				{
					interactionKey: TEST_DRAG_BOX_INTERACTION_KEY,
					selectInteractionKey: TEST_DRAG_BOX_SELECT_INTERACTION_KEY,
					condition: () => true,
					layerNames: [TEST_DRAG_BOX_LAYER_NAME],
					selectColor: {
						fillColor: 'rgba(56, 189, 248, 0.36)',
						strokeColor: 'rgba(14, 165, 233, 0.96)',
					},
				}
			);
		};

		attachDragBox();

		return () => {
			if (animationFrameId) window.cancelAnimationFrame(animationFrameId);

			const map = targetMap ?? getMap(MAP_ID);
			if (!map) return;

			olUtils.removeInteraction(map, map.get(TEST_DRAG_BOX_INTERACTION_KEY));
			olUtils.removeInteraction(map, map.get(TEST_DRAG_BOX_SELECT_INTERACTION_KEY));
			map.set(TEST_DRAG_BOX_INTERACTION_KEY, null);
			map.set(TEST_DRAG_BOX_SELECT_INTERACTION_KEY, null);
			olUtils.removeLayerByName(map, TEST_DRAG_BOX_LAYER_NAME);
		};
	}, []);

	return (
		<div className="relative h-full min-h-screen w-full overflow-hidden bg-slate-950">
			<MapCanvas
				mapId={MAP_ID}
				center={SEOUL_CITY_HALL_COORDINATE}
				centerProjection="EPSG:4326"
				projectionCode="EPSG:3857"
				zoom={16}
			/>
			<MapStatusOverlay
				overlayRef={overlayRef}
				title="서울시청 관측점"
				collapsedTitle="세울"
				status="NORMAL"
				metrics={overlayMetrics}
				extend={true}
			/>
		</div>
	);
}

export default TestMap;
