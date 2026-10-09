import { useEffect, useMemo, useRef, useState } from 'react';
import 'ol/ol.css';
import Map from 'ol/Map';
import View from 'ol/View';
import TileLayer from 'ol/layer/Tile';
import { defaults as defaultControls } from 'ol/control/defaults';
import { defaults as defaultInteractions } from 'ol/interaction/defaults';
import { fromLonLat } from 'ol/proj';
import { unByKey } from 'ol/Observable';
import { BACKGROUND_MAP_PROJECTION, DEFAULT_BACKGROUND_MAP, DEFAULT_CENTER, DEFAULT_ZOOM, PROFILE } from '@/consts';
import { disposeMap, registerMap } from '@/web/js/utils/mapRegistry';
import { OlUtils as olUtils, OlUtils } from '@/web/js/utils/olUtils';
import { getTopLeft } from 'ol/extent';
import { TileImage, XYZ } from 'ol/source';
import { TileGrid } from 'ol/tilegrid';
const EMPTY_LAYER_SEQ = [];
const DEFAULT_COORDINATE_TEXT = 'Lon -, Lat -';
const DEFAULT_FEATURE_MIN_ZOOM = 10;
const MAP_STATUS_CHIP_CLASS_NAME = [
	'rounded-[4px] border border-white/45 bg-sky-950/42 px-3 py-1.5',
	'shadow-[0_8px_18px_rgba(0,0,0,0.28),inset_0_1px_0_rgba(255,255,255,0.28)] ring-1 ring-sky-900/25 backdrop-blur-md',
	"font-['LABDigital',monospace] text-[13px] font-semibold leading-none tracking-[0.015em] text-black",
	'[text-shadow:0_1px_1px_rgba(255,255,255,0.28)]',
	"[&>*]:font-['LABDigital',monospace] [&>*]:text-[13px] [&>*]:font-semibold [&>*]:leading-none [&>*]:tracking-[0.015em] [&>*]:text-black",
].join(' ');

const fillZeroToZoomLevel = (level, length) => {
	return String(level).padStart(length, '0');
};

function buildBaseLayer() {
	if (!DEFAULT_BACKGROUND_MAP) return null;
	OlUtils.ensureProjectionRegistered();

	if (PROFILE === 'dev') {
		return new TileLayer({
			source: new XYZ({
				url: DEFAULT_BACKGROUND_MAP,
				crossOrigin: 'anonymous',
			}),
		});
	}

	return new TileLayer({
		source: new TileImage({
			projection: BACKGROUND_MAP_PROJECTION,
			tileGrid: new TileGrid({
				origin: getTopLeft([-200000.0, -28024123.62, 31824123.62, 4000000.0]),
				resolutions: [2088.96, 1044.48, 522.24, 261.12, 130.56, 65.28, 32.64, 16.32, 8.16, 4.08, 2.04, 1.02, 0.51],
				matrixIds: [
					'L05_1',
					'L06_1',
					'L07_1',
					'L08_1',
					'L09_1',
					'L10_1',
					'L11_1',
					'L12_1',
					'L13_1',
					'L14_1',
					'L15_1',
					'L16_1',
					'L17_1',
				],
			}),
			tileUrlFunction: tileCoord => {
				const z = tileCoord[0];
				const x = tileCoord[1];
				const y = tileCoord[2];
				if (z < 0) return undefined;
				const tileMatrix = `L${fillZeroToZoomLevel(z + 5, 2)}_1`;
				return `${DEFAULT_BACKGROUND_MAP}${tileMatrix}/${x}/${y}.png`;
			},
			crossOrigin: 'anonymous',
		}),
	});
}

function resolveCenter(center, centerProjection, projectionCode) {
	const resolvedCenter = center ?? DEFAULT_CENTER;

	if (!Array.isArray(resolvedCenter) || resolvedCenter.length !== 2) {
		return fromLonLat(DEFAULT_CENTER);
	}

	if (!centerProjection || centerProjection === projectionCode) {
		return [...resolvedCenter];
	}

	if (centerProjection === 'EPSG:4326' && projectionCode === 'EPSG:3857') {
		return fromLonLat(resolvedCenter);
	}

	return OlUtils.transformCoordinate(resolvedCenter, centerProjection, projectionCode) ?? [...resolvedCenter];
}

function formatZoomLevel(zoomValue) {
	const zoomNumber = Number(zoomValue);
	if (!Number.isFinite(zoomNumber)) return '-';
	return zoomNumber.toFixed(2);
}

function MapCanvas({
	mapId,
	className = '',
	center = DEFAULT_CENTER,
	centerProjection = 'EPSG:4326',
	projectionCode,
	zoom = DEFAULT_ZOOM,
	layers,
	controls,
	interactions,
	fullScreen = false,
	fullScreenTarget,
	fullScreenClassName = '',
	showMapStatus = true,
	showOverviewMap = true,
	featureMinZoom = DEFAULT_FEATURE_MIN_ZOOM,
}) {
	const containerRef = useRef(null);
	const fullScreenTargetRef = useRef(null);
	const coordinateTargetRef = useRef(null);
	const overviewMapTargetRef = useRef(null);
	const overviewMapControlRef = useRef(null);
	const mapRef = useRef(null);
	const [zoomLevel, setZoomLevel] = useState(formatZoomLevel(zoom));
	const [isMapStatusOpen, setIsMapStatusOpen] = useState(true);
	const [isOverviewMapOpen, setIsOverviewMapOpen] = useState(true);
	const layerSeq = layers ?? EMPTY_LAYER_SEQ;
	const resolvedProjectionCode = projectionCode ?? OlUtils.defaultViewProjection;
	const resolvedLayers = useMemo(() => {
		const baseLayer = buildBaseLayer();
		return baseLayer ? [baseLayer, ...layerSeq] : [...layerSeq];
	}, [layerSeq]);

	useEffect(() => {
		if (!containerRef.current || !mapId) return;
		OlUtils.ensureProjectionRegistered();

		const mapInstance = new Map({
			target: containerRef.current,
			layers: resolvedLayers,
			view: new View({
				center: resolveCenter(center, centerProjection, 'EPSG:3857'),
				zoom,
				projection: 'EPSG:3857',
				minZoom: OlUtils.defaultMinZoom,
				maxZoom: OlUtils.defaultMaxZoom,
			}),
			controls: controls ?? defaultControls({ attribution: false }),
			interactions: interactions ?? defaultInteractions(),
		});

		mapRef.current = mapInstance;
		registerMap(mapId, mapInstance);

		const originalLayerMinZoomMap = new globalThis.Map();
		const applyFeatureMinZoom = layer => {
			if (!layer?.setMinZoom || !layer?.getMinZoom || featureMinZoom == null) return;

			const isManagedFeatureLayer = layerSeq.includes(layer) || Boolean(layer.get?.('name'));
			if (!isManagedFeatureLayer) return;

			if (!originalLayerMinZoomMap.has(layer)) {
				originalLayerMinZoomMap.set(layer, layer.getMinZoom());
			}

			const originalMinZoom = originalLayerMinZoomMap.get(layer);
			const resolvedMinZoom = Number.isFinite(originalMinZoom) ? Math.max(originalMinZoom, featureMinZoom) : featureMinZoom;
			layer.setMinZoom(resolvedMinZoom);
		};
		if (featureMinZoom != null) {
			mapInstance.getLayers?.()?.forEach?.(applyFeatureMinZoom);
		}
		const layerAddKey =
			featureMinZoom != null
				? mapInstance.getLayers?.()?.on?.('add', event => {
						applyFeatureMinZoom(event.element);
					})
				: null;

		const resizeObserver = new ResizeObserver(() => {
			mapInstance.updateSize();
		});

		const resolvedFullScreenTarget = fullScreenTarget ?? fullScreenTargetRef.current;
		let fullScreenControl = null;
		if (fullScreen && resolvedFullScreenTarget) {
			fullScreenControl = olUtils.setFullScreen(mapInstance, {
				target: resolvedFullScreenTarget,
				className: 'map-canvas-fullscreen',
			});
		}

		let overviewMapControl = null;
		if (showOverviewMap && overviewMapTargetRef.current) {
			const overviewBaseLayer = buildBaseLayer();
			overviewMapControl = olUtils.addOverviewMap(mapInstance, {
				target: overviewMapTargetRef.current,
				layers: overviewBaseLayer ? [overviewBaseLayer] : [],
				collapsed: false,
				collapsible: false,
				className: 'ol-overviewmap map-canvas-overview',
			});
			overviewMapControlRef.current = overviewMapControl;
			window.requestAnimationFrame(() => {
				overviewMapControl?.getOverviewMap?.()?.updateSize?.();
			});
		}

		const updateZoomStatus = () => {
			setZoomLevel(formatZoomLevel(mapInstance.getView?.()?.getZoom?.()));
		};
		let mousePositionControl = null;
		if (showMapStatus && coordinateTargetRef.current) {
			mousePositionControl = olUtils.addMousePositionControl(mapInstance, {
				target: coordinateTargetRef.current,
				projection: 'EPSG:4326',
				placeholder: DEFAULT_COORDINATE_TEXT,
				className: 'map-canvas-coordinate-control',
				coordinateFormat: coordinate => {
					if (!Array.isArray(coordinate)) return DEFAULT_COORDINATE_TEXT;
					const [lon, lat] = coordinate;
					if (!Number.isFinite(lon) || !Number.isFinite(lat)) return DEFAULT_COORDINATE_TEXT;
					return `Lon ${lon.toFixed(6)}, Lat ${lat.toFixed(6)}`;
				},
			});
		}
		const view = mapInstance.getView?.();
		const zoomChangeKey = view?.on?.('change:resolution', updateZoomStatus);
		updateZoomStatus();

		resizeObserver.observe(containerRef.current);
		window.requestAnimationFrame(() => {
			mapInstance.updateSize();
		});

		return () => {
			if (zoomChangeKey) unByKey(zoomChangeKey);
			if (layerAddKey) unByKey(layerAddKey);
			resizeObserver.disconnect();
			if (fullScreenControl) {
				olUtils.removeFullScreenControl(mapInstance);
			}
			if (mousePositionControl) {
				olUtils.removeControl(mapInstance, mousePositionControl);
			}
			if (overviewMapControl) {
				olUtils.removeControl(mapInstance, overviewMapControl);
				overviewMapControlRef.current = null;
			}
			originalLayerMinZoomMap.forEach((originalMinZoom, layer) => {
				layer?.setMinZoom?.(originalMinZoom);
			});
			if (mapRef.current) {
				disposeMap(mapId);
				mapRef.current = null;
			}
		};
	}, [
		center,
		centerProjection,
		controls,
		featureMinZoom,
		fullScreen,
		fullScreenTarget,
		interactions,
		layerSeq,
		mapId,
		resolvedLayers,
		resolvedProjectionCode,
		showMapStatus,
		showOverviewMap,
		zoom,
	]);

	useEffect(() => {
		if (!isOverviewMapOpen) return;

		window.requestAnimationFrame(() => {
			overviewMapControlRef.current?.getOverviewMap?.()?.updateSize?.();
		});
	}, [isOverviewMapOpen]);

	return (
		<div className={['relative h-full w-full', className].filter(Boolean).join(' ')}>
			<div ref={containerRef} className="absolute inset-0" />
			{fullScreen && !fullScreenTarget ? (
				<div
					ref={fullScreenTargetRef}
					className={[
						'pointer-events-auto absolute right-3 top-3 z-40 flex items-center justify-end',
						'[&_.map-canvas-fullscreen]:static [&_.map-canvas-fullscreen]:m-0',
						'[&_.map-canvas-fullscreen_button]:h-8 [&_.map-canvas-fullscreen_button]:w-8',
						fullScreenClassName,
					]
						.filter(Boolean)
						.join(' ')}
				/>
			) : null}
			{showMapStatus ? (
				<div className="pointer-events-none absolute bottom-4 left-4 z-40 flex max-w-[calc(100%-2rem)] items-end gap-1.5">
					<div className="flex flex-col items-start gap-1.5">
						<button
							type="button"
							aria-label={isMapStatusOpen ? '지도 상태 닫기' : '지도 상태 열기'}
							title={isMapStatusOpen ? '지도 상태 닫기' : '지도 상태 열기'}
							onClick={() => setIsMapStatusOpen(prev => !prev)}
							className={[
								'pointer-events-auto flex h-7 w-7 shrink-0 items-center justify-center rounded-[4px] border border-sky-100/55',
								'bg-slate-950/55 text-[13px] font-bold leading-none text-sky-50 shadow-[0_6px_14px_rgba(0,0,0,0.26)] backdrop-blur-md',
								'transition-colors hover:bg-sky-900/70',
							].join(' ')}
						>
							{isMapStatusOpen ? '−' : '▣'}
						</button>
						<div
							className={[
								MAP_STATUS_CHIP_CLASS_NAME,
								'transition-[transform,opacity] duration-200 ease-out',
								isMapStatusOpen
									? 'translate-x-0 opacity-100'
									: 'pointer-events-none -translate-x-[calc(100%+0.5rem)] opacity-0',
							].join(' ')}
						>
							<span>줌 {zoomLevel}</span>
						</div>
					</div>
					<div
						ref={coordinateTargetRef}
						className={[
							MAP_STATUS_CHIP_CLASS_NAME,
							'min-w-[272px] transition-[transform,opacity] duration-200 ease-out [&_.map-canvas-coordinate-control]:relative [&_.map-canvas-coordinate-control]:z-[1] [&_.map-canvas-coordinate-control]:whitespace-nowrap',
							isMapStatusOpen
								? 'translate-x-0 opacity-100'
								: 'pointer-events-none -translate-x-[calc(100%+0.5rem)] opacity-0',
						].join(' ')}
					/>
				</div>
			) : null}
			{showOverviewMap ? (
				<div className="pointer-events-auto absolute bottom-3 right-3 z-30 flex flex-col items-end gap-1.5">
					<button
						type="button"
						aria-label={isOverviewMapOpen ? '미니맵 닫기' : '미니맵 열기'}
						title={isOverviewMapOpen ? '미니맵 닫기' : '미니맵 열기'}
						onClick={() => setIsOverviewMapOpen(prev => !prev)}
						className={[
							'flex h-7 w-7 items-center justify-center rounded-[4px] border border-sky-100/55',
							'bg-slate-950/55 text-[13px] font-bold leading-none text-sky-50 shadow-[0_6px_14px_rgba(0,0,0,0.26)] backdrop-blur-md',
							'transition-colors hover:bg-sky-900/70',
						].join(' ')}
					>
						{isOverviewMapOpen ? '−' : '▣'}
					</button>
					<div
						ref={overviewMapTargetRef}
						className={[
							isOverviewMapOpen ? 'h-[132px] w-[184px] opacity-100' : 'pointer-events-none h-0 w-0 opacity-0',
							'overflow-hidden rounded-[6px] border border-sky-200/35 bg-slate-950/75',
							'shadow-[0_10px_24px_rgba(0,0,0,0.32)] backdrop-blur-sm transition-[width,height,opacity] duration-150 ease-out',
							'[&_.ol-overviewmap]:static [&_.ol-overviewmap]:m-0 [&_.ol-overviewmap]:h-full [&_.ol-overviewmap]:w-full',
							'[&_.ol-overviewmap-map]:h-full [&_.ol-overviewmap-map]:w-full [&_.ol-overviewmap-map]:border-0',
							'[&_.ol-overviewmap-box]:border-2 [&_.ol-overviewmap-box]:border-amber-300',
						].join(' ')}
					/>
				</div>
			) : null}
		</div>
	);
}

export default MapCanvas;
