import {
	BACKGROUND_MAP_PROJECTION,
	BACKGROUND_MAP_PROJECTION_DEF,
	DEFAULT_CENTER,
	DEFAULT_MAX_ZOOM,
	DEFAULT_MIN_ZOOM,
	DEFAULT_PROJECTION,
	DEFAULT_PROJECTION_DEF,
	DEFAULT_ZOOM,
	LAYER_ORDER,
} from '@/consts/index.js';
import GeoJSON from 'ol/format/GeoJSON.js';
import { Collection, Overlay } from 'ol';
import { FullScreen, MousePosition, OverviewMap } from 'ol/control.js';
import { defaults as defaultControls } from 'ol/control/defaults';
import { defaults as defaultInteractions } from 'ol/interaction/defaults';
import { DblClickDragZoom, DragBox, DragZoom, Draw, Modify, Select, Snap } from 'ol/interaction.js';
import Point from 'ol/geom/Point.js';
import { fromCircle } from 'ol/geom/Polygon.js';
import VectorLayer from 'ol/layer/Vector.js';
import { transform, transformExtent } from 'ol/proj';
import { register } from 'ol/proj/proj4';
import VectorSource from 'ol/source/Vector.js';
import { Circle, Fill, Icon, RegularShape, Stroke, Style, Text } from 'ol/style.js';
import proj4 from 'proj4';
import { click as mapClick, platformModifierKeyOnly } from 'ol/events/condition.js';
import { StzUtils } from 'stzutil-js/node';

/**
 * ═════════════════════════════════════════════════════════════
 * 📄 FILE     : olUtils.js
 * 📁 PACKAGE  : front-web.js.utils
 * 👤 AUTHOR   : stz
 * 🕒 CREATED  : 26. 6. 16.
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 📝 DESCRIPTION
 *   -
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 🔄 CHANGE LOG
 *   - DATE : 2026/06/16 | Author : stz | 최초 생성
 * ═════════════════════════════════════════════════════════════
 */
export class OlUtils {
	static defaultZoom = DEFAULT_ZOOM;
	static defaultMinZoom = DEFAULT_MIN_ZOOM;
	static defaultMaxZoom = DEFAULT_MAX_ZOOM;
	static defaultCenter = DEFAULT_CENTER;
	static defaultDataProjection = DEFAULT_PROJECTION;
	static defaultProjectionDef = DEFAULT_PROJECTION_DEF;
	static backgroundMapProjection = BACKGROUND_MAP_PROJECTION;
	static backgroundMapProjectionDef = BACKGROUND_MAP_PROJECTION_DEF;
	static defaultViewProjection = DEFAULT_PROJECTION;
	static longitudeLatitudeProjection = 'EPSG:4326';
	static webMercatorProjection = 'EPSG:3857';
	static isProjectionRegistered = false;
	static layerOrder = LAYER_ORDER;
	static defaultLayerStyleOptions = {
		nodeZoom: 13,
		labelZoom: 11,
		labelFontSize: 12,
		nodeSize: 6,
		linkSize: 2,
		visibleNodeTagYn: false,
		fitPadding: [40, 40, 40, 40],
		fitMaxZoom: 16,
		colorMap: {
			PIPES: '#55fbff',
			PUMPS: '#95df67',
			VALVES: '#fce652',
			JUNCTIONS: '#7aa5ff',
			RESERVOIRS: '#67d6ff',
			TANKS: '#9df5b3',
			LABELS: '#d9f3ff',
		},
	};
	static nodeIconSrcByLayerName = {
		JUNCTIONS: '/JUNCTIONS.svg',
		RESERVOIRS: '/RESERVOIRS.svg',
		TANKS: '/TANKS.svg',
	};
	static nodeIconSizeByLayerName = {
		JUNCTIONS: [10, 11],
		RESERVOIRS: [10, 10],
		TANKS: [32, 32],
	};
	static drawTypeByLayerName = {
		JUNCTIONS: 'Point',
		RESERVOIRS: 'Point',
		TANKS: 'Point',
		PIPES: 'LineString',
		PUMPS: 'LineString',
		VALVES: 'LineString',
		LABELS: 'Point',
	};

	static validDrawTypes = ['Point', 'LineString', 'Polygon', 'Circle'];
	static defaultDrawInteractionKey = '__modelEditorDrawInteraction';
	static defaultDrawInteractionFlagKey = '__isModelEditorDrawInteraction';
	static defaultFullScreenControlKey = '__fullScreenControl';
	static defaultModifyInteractionKey = '__featureModifyInteraction';
	static defaultSelectInteractionKey = '__featureSelectInteraction';
	static defaultSnapInteractionKey = '__featureSnapInteraction';
	static defaultDragBoxInteractionKey = '__featureDragBoxInteraction';

	/**
	 * @description OpenLayers 기본 사용자 좌표계 등록
	 * @returns {string}
	 */
	static ensureProjectionRegistered() {
		if (!this.isProjectionRegistered) {
			proj4.defs(this.defaultDataProjection, this.defaultProjectionDef);
			proj4.defs(this.backgroundMapProjection, this.backgroundMapProjectionDef);
			register(proj4);
			this.isProjectionRegistered = true;
		}
		return this.defaultDataProjection;
	}

	/**
	 * @description 지도 View 좌표계 코드 반환
	 * @param map
	 * @returns {string}
	 */
	static getMapProjectionCode(map) {
		return map?.getView?.()?.getProjection?.()?.getCode?.() ?? this.defaultViewProjection;
	}

	/**
	 * @description 좌표 변환
	 * @param coordinate
	 * @param sourceProjection
	 * @param targetProjection
	 * @returns {number[]|null}
	 */
	static transformCoordinate(
		coordinate,
		sourceProjection = this.defaultDataProjection,
		targetProjection = this.defaultViewProjection
	) {
		if (!Array.isArray(coordinate) || coordinate.length !== 2) return null;
		if (!sourceProjection || !targetProjection) return [...coordinate];
		if (sourceProjection === targetProjection) return [...coordinate];

		this.ensureProjectionRegistered();
		return transform(coordinate, sourceProjection, targetProjection);
	}

	/**
	 * @description 경위도 좌표를 지도 좌표계로 변환
	 * @param coordinate
	 * @param targetProjection
	 * @returns {number[]|null}
	 */
	static fromLonLat(coordinate, targetProjection = this.webMercatorProjection) {
		return this.transformCoordinate(coordinate, this.longitudeLatitudeProjection, targetProjection);
	}

	/**
	 * @description extent 변환
	 * @param extent
	 * @param sourceProjection
	 * @param targetProjection
	 * @returns {number[]|null}
	 */
	static transformExtent(extent, sourceProjection = this.defaultDataProjection, targetProjection = this.defaultViewProjection) {
		if (!Array.isArray(extent) || extent.length !== 4) return null;
		if (!sourceProjection || !targetProjection) return [...extent];
		if (sourceProjection === targetProjection) return [...extent];

		this.ensureProjectionRegistered();
		return transformExtent(extent, sourceProjection, targetProjection);
	}

	/**
	 * @description 데이터 좌표를 현재 지도 좌표계로 변환
	 * @param map
	 * @param coordinate
	 * @param sourceProjection
	 * @returns {number[]|null}
	 */
	static toMapCoordinate(map, coordinate, sourceProjection = this.defaultDataProjection) {
		return this.transformCoordinate(coordinate, sourceProjection, this.getMapProjectionCode(map));
	}

	/**
	 * @description 현재 지도 좌표를 데이터 좌표계로 변환
	 * @param map
	 * @param coordinate
	 * @param targetProjection
	 * @returns {number[]|null}
	 */
	static toDataCoordinate(map, coordinate, targetProjection = this.defaultDataProjection) {
		return this.transformCoordinate(coordinate, this.getMapProjectionCode(map), targetProjection);
	}

	/**
	 * @description 데이터 extent를 현재 지도 좌표계로 변환
	 * @param map
	 * @param extent
	 * @param sourceProjection
	 * @returns {number[]|null}
	 */
	static toMapExtent(map, extent, sourceProjection = this.defaultDataProjection) {
		return this.transformExtent(extent, sourceProjection, this.getMapProjectionCode(map));
	}

	/**
	 * @description 지도에 오버레이 추가
	 * @param map
	 * @param options
	 * @param position
	 * @returns {Overlay|null}
	 */
	static addOverlay(map, options = {}, position) {
		const { element, positioning = 'bottom-center', stopEvent = false, offset, autoPan } = options;
		if (!map || !element) return null;
		const overlay = new Overlay({
			element,
			positioning,
			stopEvent,
			offset,
			autoPan,
		});
		if (position) this.setOverlayPosition(overlay, position);
		map.addOverlay(overlay);
		return overlay;
	}

	/**
	 * @description 오버레이 위치 설정
	 * @param overlay
	 * @param position
	 * @return void
	 */
	static setOverlayPosition(overlay, position) {
		if (!overlay) return;
		overlay.setPosition(position);
	}

	/**
	 * @description 지도에서 오버레이 제거
	 * @param map
	 * @param overlay
	 * @return void
	 */
	static removeOverlay(map, overlay) {
		if (!map || !overlay) return;
		map.removeOverlay(overlay);
	}

	/**
	 * @description 지도 줌 레벨 설정
	 * @param map
	 * @param zoom
	 * @return void
	 */
	static setZoom(map, zoom) {
		if (!map) return;
		if (zoom == null) zoom = this.defaultZoom;
		if (zoom < 0) zoom = 0;
		map.getView().setZoom(zoom);
	}

	/**
	 * @description 지도 중심 좌표 및 줌 레벨 설정
	 * @param map
	 * @param center
	 * @param zoom
	 * @return void
	 */
	static setCenterAndZoom(map, center, zoom) {
		if (!map) return;
		this.setCenter(map, center);
		this.setZoom(map, zoom);
	}

	/**
	 * @description 지도 중심 좌표 설정
	 * @param map
	 * @param center
	 * @return void
	 */
	static setCenter(map, center) {
		if (!map) return;
		if (!center || center.length !== 2) center = this.defaultCenter;
		map.getView().setCenter(center);
	}

	/**
	 * @description 지도에 기본 컨트롤 추가
	 * @param map
	 * @return void
	 */
	static setDefaultControls(map) {
		if (!map) return;
		map.getControls().extend(defaultControls().getArray());
	}

	/**
	 * @description 지도에 기본 인터랙션 추가
	 * @param map
	 */
	static setDefaultInteractions(map) {
		if (!map) return;
		map.getInteractions().extend(defaultInteractions().getArray());
	}

	/**
	 * @description 지도에서 인터랙션 제거
	 * @param map
	 * @param interaction
	 * @return void
	 */
	static removeInteraction(map, interaction) {
		if (!map || !interaction) return;
		map.removeInteraction(interaction);
	}

	/**
	 * @description 지도에 컨트롤 추가
	 * @param map
	 * @param control
	 * @return void
	 */
	static addControl(map, control) {
		if (!map || !control) return;
		map.addControl(control);
	}

	/**
	 * @description 지도에서 컨트롤 제거
	 * @param map
	 * @param control
	 */
	static removeControl(map, control) {
		if (!map || !control) return;
		map.removeControl(control);
	}

	static removeFullScreenControl(map, options = {}) {
		if (!map) return null;

		const { controlKey = this.defaultFullScreenControlKey } = options;
		const control = map.get?.(controlKey);
		if (!control) return null;

		this.removeControl(map, control);
		map.set(controlKey, null);
		return control;
	}

	/**
	 * @description 지도에 마우스 위치 컨트롤 추가
	 * @param map
	 * @param options
	 * @returns {*}
	 */
	static addMousePositionControl(map, options = {}) {
		if (!map) return;
		const { projection = 'EPSG:4326', coordinateFormat, className = 'ol-mouse-position', target = null, placeholder, wrapX } = options;
		const control = new MousePosition({
			projection,
			coordinateFormat,
			className,
			target,
			placeholder,
			wrapX,
		});
		this.addControl(map, control);
		return control;
	}

	static addOverviewMap(map, options = {}) {
		if (!map) return null;

		const { className, layers, collapseLabel, label, collapsed = false, collapsible = false, target = null } = options;

		const control = new OverviewMap({
			className,
			layers,
			collapseLabel,
			label,
			collapsed,
			collapsible,
			target,
		});

		this.addControl(map, control);
		return control;
	}

	static addInteraction(map, interaction) {
		if (!map || !interaction) return;
		map.addInteraction(interaction);
	}

	static addFullScreenControl(map, options = {}) {
		if (!map) return null;

		const { className = '', label, tipLabel, target, controlKey = this.defaultFullScreenControlKey } = options;

		this.removeFullScreenControl(map, { controlKey });
		if (target && className) {
			target.querySelectorAll?.(`.${className}`).forEach(element => element.remove());
		}

		const control = new FullScreen({
			className,
			label,
			tipLabel,
			target,
		});

		this.addControl(map, control);
		map.set(controlKey, control);
		return control;
	}

	static addDragZoomInteraction(map, options = {}) {
		if (!map) return null;

		const { className, condition, duration, out = false } = options;

		const interaction = new DragZoom({
			className,
			condition,
			duration,
			out,
		});

		map.addInteraction(interaction);
		return interaction;
	}

	static onMapLoadStart(map, callback) {
		if (!map || !callback) return;
		map.on('loadstart', callback);
	}

	static onMapLoadEnd(map, callback) {
		if (!map || !callback) return;
		map.on('loadend', callback);
	}

	static getLayerByName(map, layerName) {
		if (!map || !layerName) return null;
		return (
			map
				.getLayers()
				.getArray()
				.find(layer => layer?.get?.('name') === layerName) ?? null
		);
	}

	static createEmptyLayer(map, layerName, options = {}) {
		if (!map || !layerName) return null;
		return this.setLayerOnMap(
			map,
			{
				type: 'FeatureCollection',
				features: [],
			},
			layerName,
			options
		);
	}

	static getOrCreateLayerByName(map, layerName, options = {}) {
		const layer = this.getLayerByName(map, layerName);
		if (layer || !options.createLayerIfMissing) return layer;
		return this.createEmptyLayer(map, layerName, options);
	}

	static removeLayerByName(map, layerName) {
		if (!map || !layerName) return;
		const layer = this.getLayerByName(map, layerName);
		if (!layer) return;
		map.removeLayer(layer);
	}

	static addLayer(map, layer) {
		if (!map || !layer) return null;
		map.addLayer(layer);
		return layer;
	}

	static addLayers(map, data, options = {}) {
		if (!map || !data) return {};

		const layerDataMap = this.normalizeLayerDataMap(data);
		const layerOrder = options.layerOrder ?? this.layerOrder;
		const layerMap = {};

		layerOrder.forEach(layerName => {
			if (!layerDataMap[layerName]) return;
			layerMap[layerName] = this.setLayerOnMap(map, layerDataMap[layerName], layerName, options);
		});

		const fitLayerName = options.fitLayerName ?? 'JUNCTIONS';
		const fitLayer = layerMap[fitLayerName];

		if (fitLayer && options.fitToExtent !== false) {
			const extent = fitLayer.getSource()?.getExtent?.();
			if (extent && extent.every(Number.isFinite)) {
				map.getView().fit(extent, {
					padding: options.fitPadding ?? this.defaultLayerStyleOptions.fitPadding,
					maxZoom: options.fitMaxZoom ?? this.defaultLayerStyleOptions.fitMaxZoom,
					duration: options.fitDuration ?? 350,
				});
			}
		}

		return layerMap;
	}

	static setLayerOnMap(map, layerData, layerName, options = {}) {
		if (!map || !layerName) return null;
		this.ensureProjectionRegistered();

		const vectorStyle =
			options.vectorStyleResolver?.(layerName, map, options) ??
			options.vectorStyle ??
			this.getVectorStyle(layerName, map, options);

		const vectorLayer = new VectorLayer({
			source: new VectorSource(),
			style: vectorStyle,
		});

		vectorLayer.set('name', layerName);
		vectorLayer.set('__styleOptions', {
			...this.defaultLayerStyleOptions,
			...options,
		});
		vectorLayer.set('__baseStyle', vectorStyle);
		vectorLayer.setZIndex(['JUNCTIONS', 'RESERVOIRS', 'TANKS', 'LABELS'].includes(layerName) ? 5 : 4);

		const geoJson = this.normalizeGeoJson(layerData);
		if (this.isGeoJsonLike(geoJson)) {
			const format = new GeoJSON();
			const featureProjection = options.featureProjection ?? map.getView()?.getProjection?.()?.getCode?.() ?? 'EPSG:3857';
			const dataProjection = options.dataProjection ?? this.defaultDataProjection;
			const features = format.readFeatures(geoJson, {
				featureProjection,
				dataProjection,
			});
			vectorLayer.getSource().addFeatures(features);
		}

		this.removeLayerByName(map, layerName);
		this.addLayer(map, vectorLayer);
		return vectorLayer;
	}

	static getVectorStyle(layerName, map, options = {}) {
		const resolvedOptions = {
			...this.defaultLayerStyleOptions,
			...options,
		};

		if (['JUNCTIONS', 'RESERVOIRS', 'TANKS'].includes(layerName)) {
			return feature => {
				const id = feature.get('ID') ?? feature.get('id') ?? '';
				const color = this.resolveLayerColor(layerName, feature, resolvedOptions);
				const shouldShowText = (map.getView()?.getZoom?.() ?? 0) > resolvedOptions.nodeZoom;
				const nodeText = shouldShowText ? String(id) : '';
				const nodeSize = Number(resolvedOptions.nodeSize ?? 6);
				const styleList = [
					new Style({
						image: this.createNodeImageStyle(layerName, color, nodeSize),
						text: nodeText
							? new Text({
									font: '10px Verdana',
									text: nodeText,
									fill: new Fill({ color: '#0b1325' }),
									stroke: new Stroke({ color: '#e9f6ff', width: 2 }),
									offsetX: 16,
									offsetY: 16,
								})
							: undefined,
					}),
				];

				if (this.isVisibleNodeTag(feature, resolvedOptions)) {
					styleList.push(
						new Style({
							image: new Circle({
								radius: nodeSize + 6,
								stroke: new Stroke({ color: '#55d66b', width: 2 }),
							}),
						})
					);
				}

				return styleList;
			};
		}

		if (layerName === 'LABELS') {
			return feature =>
				new Style({
					text: new Text({
						text:
							(map.getView()?.getZoom?.() ?? 0) > resolvedOptions.labelZoom
								? String(feature.get('LABEL') ?? feature.get('label') ?? feature.get('text') ?? '')
								: '',
						font: `${resolvedOptions.labelFontSize}px Verdana`,
						fill: new Fill({ color: resolvedOptions.colorMap?.LABELS ?? '#d9f3ff' }),
						stroke: new Stroke({ color: 'rgba(4, 12, 25, 0.55)', width: 3 }),
					}),
				});
		}

		if (['PUMPS', 'VALVES'].includes(layerName)) {
			return feature => {
				const color = this.resolveLayerColor(layerName, feature, resolvedOptions);
				const linkSize = Number(resolvedOptions.linkSize ?? 2);
				const id = feature.get('ID') ?? feature.get('id') ?? '';
				const shouldShowText = (map.getView()?.getZoom?.() ?? 0) > resolvedOptions.nodeZoom;
				const lineText = shouldShowText ? String(id) : '';
				const styleList = [
					new Style({
						stroke: new Stroke({
							color,
							width: linkSize,
							lineDash: [6, 4],
						}),
						text: lineText
							? new Text({
									font: '10px Verdana',
									text: lineText,
									fill: new Fill({ color: '#0b1325' }),
									stroke: new Stroke({ color: '#eef8ff', width: 2 }),
									offsetX: 14,
									offsetY: 14,
								})
							: undefined,
					}),
				];

				const centerCoordinate = this.getGeometryCenterCoordinate(feature);
				if (centerCoordinate) {
					styleList.push(
						new Style({
							geometry: new Point(centerCoordinate),
							image: new RegularShape({
								points: layerName === 'VALVES' ? 4 : 3,
								radius: Number(resolvedOptions.nodeSize ?? 6) + 1,
								fill: new Fill({ color }),
								stroke: new Stroke({ color: '#edf7ff', width: 1.5 }),
								angle: layerName === 'VALVES' ? Math.PI / 4 : 0,
							}),
						})
					);
				}

				return styleList;
			};
		}

		return feature => {
			const color = this.resolveLayerColor(layerName, feature, resolvedOptions);
			const linkSize = Number(resolvedOptions.linkSize ?? 2);
			const id = feature.get('ID') ?? feature.get('id') ?? '';
			const shouldShowText = (map.getView()?.getZoom?.() ?? 0) > resolvedOptions.nodeZoom;
			const lineText = shouldShowText ? String(id) : '';

			return new Style({
				stroke: new Stroke({
					color,
					width: linkSize,
				}),
				text: lineText
					? new Text({
							font: '10px Verdana',
							text: lineText,
							fill: new Fill({ color: '#0b1325' }),
							stroke: new Stroke({ color: '#eef8ff', width: 2 }),
							offsetX: 14,
							offsetY: 14,
						})
					: undefined,
			});
		};
	}

	static normalizeLayerDataMap(data) {
		if (!data) return {};

		const payload = data.content ?? data.layers ?? data;
		const nodeLayer = payload.nodeLayer ?? {};
		const linkLayer = payload.linkLayer ?? {};
		const labelLayer = payload.labelLayer ?? {};
		const directLayerMap = Object.fromEntries(
			Object.entries(payload).filter(([key, value]) => this.layerOrder.includes(key) && this.isGeoJsonLike(value))
		);
		const backendLayerMap = this.normalizeBackendLayerMap({ nodeLayer, linkLayer, labelLayer });

		return {
			...directLayerMap,
			...linkLayer,
			...nodeLayer,
			...backendLayerMap,
		};
	}

	static normalizeBackendLayerMap({ nodeLayer, linkLayer, labelLayer }) {
		const layerMap = {};

		this.appendBackendFeatureCollection(layerMap, nodeLayer);
		this.appendBackendFeatureCollection(layerMap, linkLayer);
		this.appendBackendFeatureCollection(layerMap, labelLayer, 'LABELS');

		return layerMap;
	}

	static appendBackendFeatureCollection(layerMap, featureCollection, fallbackLayerName) {
		const geoJson = this.normalizeGeoJson(featureCollection);
		if (!geoJson || geoJson.type !== 'FeatureCollection' || !Array.isArray(geoJson.features)) return;

		geoJson.features.forEach(feature => {
			const layerName = fallbackLayerName ?? this.resolveBackendLayerName(feature?.properties);
			if (!layerName || !this.layerOrder.includes(layerName)) return;

			if (!layerMap[layerName]) {
				layerMap[layerName] = {
					type: 'FeatureCollection',
					features: [],
				};
			}

			layerMap[layerName].features.push(feature);
		});
	}

	static resolveBackendLayerName(properties = {}) {
		const objectType = String(properties.objectType ?? '').toLowerCase();
		const layer = String(properties.layer ?? '').toLowerCase();
		const layerKey = objectType || layer;

		const layerNameByBackendKey = {
			junction: 'JUNCTIONS',
			junctions: 'JUNCTIONS',
			reservoir: 'RESERVOIRS',
			reservoirs: 'RESERVOIRS',
			tank: 'TANKS',
			tanks: 'TANKS',
			pipe: 'PIPES',
			pipes: 'PIPES',
			pump: 'PUMPS',
			pumps: 'PUMPS',
			valve: 'VALVES',
			valves: 'VALVES',
			label: 'LABELS',
			labels: 'LABELS',
		};

		return layerNameByBackendKey[layerKey] ?? null;
	}

	static normalizeGeoJson(layerData) {
		if (!layerData) return null;
		if (typeof layerData === 'string') {
			try {
				return JSON.parse(layerData);
			} catch (error) {
				console.error('Failed to parse GeoJSON layer data', error);
				return null;
			}
		}
		return layerData;
	}

	static isGeoJsonLike(layerData) {
		const normalized = this.normalizeGeoJson(layerData);
		return (
			!!normalized && !Array.isArray(normalized) && typeof normalized === 'object' && typeof normalized.type === 'string'
		);
	}

	static resolveLayerColor(layerName, feature, options = {}) {
		return feature?.get?.('COLOR') ?? options.colorMap?.[layerName] ?? '#7aa5ff';
	}

	static createNodeImageStyle(layerName, color, nodeSize) {
		const iconSrc = this.nodeIconSrcByLayerName[layerName];
		if (iconSrc) {
			return new Icon({
				src: iconSrc,
				anchor: [0.5, 0.5],
				anchorXUnits: 'fraction',
				anchorYUnits: 'fraction',
				scale: Math.max(0.6, nodeSize / 8),
			});
		}

		if (layerName === 'RESERVOIRS') {
			return new RegularShape({
				points: 4,
				radius: nodeSize + 1,
				angle: Math.PI / 4,
				fill: new Fill({ color }),
				stroke: new Stroke({ color: '#eef8ff', width: 1.5 }),
			});
		}

		if (layerName === 'TANKS') {
			return new RegularShape({
				points: 3,
				radius: nodeSize + 2,
				rotation: Math.PI,
				fill: new Fill({ color }),
				stroke: new Stroke({ color: '#eef8ff', width: 1.5 }),
			});
		}

		return new Circle({
			radius: nodeSize,
			fill: new Fill({ color }),
			stroke: new Stroke({ color: '#eef8ff', width: 1.5 }),
		});
	}

	static getNodeHighlightRadius(layerName, nodeSize) {
		const iconSize = this.nodeIconSizeByLayerName[layerName];
		if (!iconSize) return nodeSize;

		const scale = Math.max(0.6, nodeSize / 8);
		return (Math.max(...iconSize) * scale) / 2;
	}

	static getDrawStyle(layerName, drawType, options = {}) {
		const resolvedOptions = {
			...this.defaultLayerStyleOptions,
			...options,
		};
		const color = resolvedOptions.colorMap?.[layerName] ?? '#ffcc33';
		const nodeSize = Number(resolvedOptions.nodeSize ?? this.defaultLayerStyleOptions.nodeSize);
		const linkSize = Number(resolvedOptions.linkSize ?? this.defaultLayerStyleOptions.linkSize);

		if (drawType === 'Point') {
			return new Style({
				image: this.createNodeImageStyle(layerName, color, nodeSize),
			});
		}

		return new Style({
			fill: new Fill({
				color: 'rgba(255, 255, 255, 0.2)',
			}),
			stroke: new Stroke({
				color,
				width: Math.max(2, linkSize),
			}),
			image: new Circle({
				radius: nodeSize,
				fill: new Fill({ color }),
			}),
		});
	}

	static isVisibleNodeTag(feature, options = {}) {
		const visibleNodeTagYn = options.visibleNodeTagYn;
		const nodeTagYn = feature?.get?.('NODE_TAG_YN');
		return (visibleNodeTagYn === true || visibleNodeTagYn === 'Y') && (nodeTagYn === true || nodeTagYn === 'Y');
	}

	static getGeometryCenterCoordinate(feature) {
		const geometry = feature?.getGeometry?.();
		if (!geometry) return null;

		if (geometry.getType() === 'LineString') {
			return geometry.getCoordinateAt(0.5);
		}

		if (geometry.getType() === 'MultiLineString') {
			const firstLine = geometry.getLineString?.(0);
			return firstLine?.getCoordinateAt?.(0.5) ?? null;
		}

		return null;
	}

	static getCoordinateDistanceSq(a, b) {
		if (!Array.isArray(a) || !Array.isArray(b)) return Number.POSITIVE_INFINITY;
		const dx = a[0] - b[0];
		const dy = a[1] - b[1];
		return dx * dx + dy * dy;
	}

	static buildCirclePolygonCoordinates(centerCoordinate, edgeCoordinate, segmentCount = 96) {
		if (!Array.isArray(centerCoordinate) || !Array.isArray(edgeCoordinate)) return null;

		const radius = Math.sqrt(this.getCoordinateDistanceSq(centerCoordinate, edgeCoordinate));
		if (!Number.isFinite(radius) || radius <= 0) return null;

		const ring = Array.from({ length: segmentCount }, (_, index) => {
			const angle = (index / segmentCount) * Math.PI * 2;
			return [
				centerCoordinate[0] + Math.cos(angle) * radius,
				centerCoordinate[1] + Math.sin(angle) * radius,
			];
		});
		ring.push([...ring[0]]);

		return [ring];
	}

	static buildBoxPolygonCoordinates(startCoordinate, endCoordinate) {
		if (!Array.isArray(startCoordinate) || !Array.isArray(endCoordinate)) return null;
		if (this.getCoordinateDistanceSq(startCoordinate, endCoordinate) <= 0) return null;

		const [startX, startY] = startCoordinate;
		const [endX, endY] = endCoordinate;

		return [[
			[startX, startY],
			[endX, startY],
			[endX, endY],
			[startX, endY],
			[startX, startY],
		]];
	}

	static toPolygonGeometry(geometry, options = {}) {
		if (!geometry) return null;

		const geometryType = geometry.getType?.();
		if (geometryType === 'Polygon') return geometry;
		if (geometryType === 'Circle') return fromCircle(geometry, options.segmentCount ?? 96);
		return null;
	}

	static isExtentIntersecting(a, b) {
		if (!a || !b) return false;
		return a[0] <= b[2] && a[2] >= b[0] && a[1] <= b[3] && a[3] >= b[1];
	}

	static getLineCoordinateSeq(geometry) {
		const coordinates = geometry?.getCoordinates?.();
		if (!Array.isArray(coordinates)) return [];
		if (typeof coordinates[0]?.[0] === 'number') return [coordinates];
		if (Array.isArray(coordinates[0]) && typeof coordinates[0]?.[0]?.[0] === 'number') return coordinates;
		return [];
	}

	static getPolygonRingCoordinateSeq(geometry) {
		const coordinates = geometry?.getCoordinates?.();
		return Array.isArray(coordinates?.[0]) ? coordinates[0] : [];
	}

	static getSegmentOrientation(a, b, c) {
		return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
	}

	static isCoordinateOnSegment(a, b, c) {
		const minX = Math.min(a[0], b[0]);
		const maxX = Math.max(a[0], b[0]);
		const minY = Math.min(a[1], b[1]);
		const maxY = Math.max(a[1], b[1]);
		return (
			Math.abs(this.getSegmentOrientation(a, b, c)) < 1e-9 &&
			c[0] >= minX &&
			c[0] <= maxX &&
			c[1] >= minY &&
			c[1] <= maxY
		);
	}

	static doSegmentsIntersect(a, b, c, d) {
		const abC = this.getSegmentOrientation(a, b, c);
		const abD = this.getSegmentOrientation(a, b, d);
		const cdA = this.getSegmentOrientation(c, d, a);
		const cdB = this.getSegmentOrientation(c, d, b);

		if (abC * abD < 0 && cdA * cdB < 0) return true;
		return (
			this.isCoordinateOnSegment(a, b, c) ||
			this.isCoordinateOnSegment(a, b, d) ||
			this.isCoordinateOnSegment(c, d, a) ||
			this.isCoordinateOnSegment(c, d, b)
		);
	}

	static doesLineIntersectPolygon(lineCoordinateSeq, polygonGeometry, polygonRingCoordinateSeq) {
		if (lineCoordinateSeq.some(coordinate => polygonGeometry.intersectsCoordinate?.(coordinate))) return true;

		return lineCoordinateSeq.slice(0, -1).some((lineStart, index) => {
			const lineEnd = lineCoordinateSeq[index + 1];
			return polygonRingCoordinateSeq.slice(0, -1).some((polygonStart, ringIndex) => {
				const polygonEnd = polygonRingCoordinateSeq[ringIndex + 1];
				return this.doSegmentsIntersect(lineStart, lineEnd, polygonStart, polygonEnd);
			});
		});
	}

	static isGeometryIntersectingPolygon(targetGeometry, polygonGeometry, options = {}) {
		const areaGeometry = this.toPolygonGeometry(polygonGeometry, options);
		if (!targetGeometry || !areaGeometry) return false;

		const targetExtent = targetGeometry.getExtent?.();
		const areaExtent = areaGeometry.getExtent?.();
		if (!this.isExtentIntersecting(targetExtent, areaExtent)) return false;

		const polygonRingCoordinateSeq = this.getPolygonRingCoordinateSeq(areaGeometry);
		if (polygonRingCoordinateSeq.length < 4) return false;

		return this.getLineCoordinateSeq(targetGeometry).some(lineCoordinateSeq =>
			this.doesLineIntersectPolygon(lineCoordinateSeq, areaGeometry, polygonRingCoordinateSeq)
		);
	}

	static findFeaturesIntersectingGeometry(features = [], geometry, options = {}) {
		if (!Array.isArray(features) || !geometry) return [];

		return features.filter(feature => this.isGeometryIntersectingPolygon(feature?.getGeometry?.(), geometry, options));
	}

	/**
	 * @description 지도에서 특정 레이어의 모든 피처 가져오기
	 * @param map
	 * @param layer
	 * @returns {Array<import("../Feature.js").default<import("../geom.js").Geometry, {[p: string]: any}>>|*[]}
	 */
	static getFeatures(map, layer) {
		if (!map || !layer) return [];
		return layer.getSource().getFeatures() || [];
	}

	/**
	 * @description 지도에서 특정 레이어의 피처 ID로 피처 가져오기
	 * @param map
	 * @param layer
	 * @param featureId
	 * @returns {T|null}
	 */
	static getFeatureById(map, layer, featureId) {
		const features = this.getFeatures(map, layer);
		return features.find(feature => feature.getId() === featureId) || null;
	}

	static getFeatureByName(map, layer, featureName) {
		const features = this.getFeatures(map, layer);
		const targetName = String(featureName);
		return (
			features.find(feature =>
				[feature.get('name'), feature.get('id'), feature.get('ID'), feature.get('label'), feature.get('LABEL')]
					.filter(value => value !== null && value !== undefined)
					.some(value => String(value) === targetName)
			) || null
		);
	}

	static highlightFeatureEvent(featureName, map, options = {}) {
		if (!map) return null;

		const previousSelect = map.get('__highlightFeatureSelectInteraction');
		if (previousSelect) {
			map.removeInteraction(previousSelect);
			map.set('__highlightFeatureSelectInteraction', null);
		}

		if (!featureName) return null;

		const layer = this.getLayerByName(map, options.layerName ?? 'JUNCTIONS');
		const feature = this.getFeatureByName(map, layer, featureName);
		if (!feature) return null;
		const resolvedOptions = {
			...this.defaultLayerStyleOptions,
			...(layer?.get?.('__styleOptions') ?? {}),
			...options,
		};
		const highlightFillColor = resolvedOptions.fillColor ?? 'rgba(255, 255, 0, 0.35)';
		const highlightStrokeColor = resolvedOptions.strokeColor ?? 'rgba(255, 255, 0, 0.95)';

		const selectedStyle = selectedFeature => {
			const baseStyle = layer?.get?.('__baseStyle');
			const baseStyleSeq =
				typeof baseStyle === 'function' ? baseStyle(selectedFeature) : (selectedFeature.getStyle?.() ?? baseStyle);
			const geometryType = selectedFeature.getGeometry?.()?.getType?.();
			const isPoint = geometryType === 'Point' || geometryType === 'MultiPoint';
			const sizeMultiplier = Number(resolvedOptions.highlightSizeMultiplier ?? 1.8);
			const strokeWidth = Number(
				resolvedOptions.strokeWidth ??
					(isPoint ? 2 : (resolvedOptions.linkSize ?? this.defaultLayerStyleOptions.linkSize))
			);
			const nodeSize = Number(resolvedOptions.nodeSize ?? this.defaultLayerStyleOptions.nodeSize);
			const baseNodeRadius = Number(
				resolvedOptions.radius ?? this.getNodeHighlightRadius(resolvedOptions.layerName ?? options.layerName, nodeSize)
			);
			const highlightRadius = baseNodeRadius * sizeMultiplier;
			const highlightLineWidth = strokeWidth * sizeMultiplier;

			const highlightStyle = new Style({
				image: isPoint
					? new Circle({
							radius: highlightRadius,
							fill: new Fill({
								color: highlightFillColor,
							}),
							stroke: new Stroke({
								color: highlightStrokeColor,
								width: Math.max(2, highlightLineWidth),
							}),
						})
					: undefined,
				fill: new Fill({
					color: highlightFillColor,
				}),
				stroke: new Stroke({
					color: highlightStrokeColor,
					width: Math.max(2, highlightLineWidth),
				}),
			});
			const normalizedBaseStyleSeq = Array.isArray(baseStyleSeq) ? baseStyleSeq : [baseStyleSeq].filter(Boolean);
			return [highlightStyle, ...normalizedBaseStyleSeq];
		};

		const selectClick = new Select({
			condition: mapClick,
			layers: layer ? [layer] : undefined,
			style: selectedStyle,
		});
		selectClick.getFeatures().push(feature);
		map.addInteraction(selectClick);
		map.set('__highlightFeatureSelectInteraction', selectClick);

		const geometry = feature.getGeometry?.();
		const view = map.getView?.();
		if (geometry && view && options.fitToFeature !== false) {
			const zoom = Math.max(view.getZoom?.() ?? 0, options.zoom ?? 17);
			if (geometry.getType?.() === 'Point') {
				this.setCenterAndZoom(map, geometry.getCoordinates(), zoom);
			} else {
				const center = this.getGeometryCenterCoordinate(feature);
				if (center) {
					this.setCenterAndZoom(map, center, zoom);
				}
			}
		}

		return selectClick;
	}

	static resolveDrawInteractionOptions(options = {}) {
		return {
			drawInteractionKey: options.drawInteractionKey ?? this.defaultDrawInteractionKey,
			drawInteractionFlagKey: options.drawInteractionFlagKey ?? this.defaultDrawInteractionFlagKey,
		};
	}

	static removeDrawInteractions(map, options = {}) {
		if (!map) return;

		const { drawInteractionKey, drawInteractionFlagKey } = this.resolveDrawInteractionOptions(options);
		const storedDraw = map.get(drawInteractionKey);
		if (storedDraw) {
			this.removeInteraction(map, storedDraw);
		}

		map.getInteractions()
			.getArray()
			.filter(interaction => interaction instanceof Draw || interaction?.get?.(drawInteractionFlagKey))
			.forEach(interaction => this.removeInteraction(map, interaction));

		map.set(drawInteractionKey, null);
	}

	static setDraw(map, layerNameOrType, callBack, options = {}) {
		if (!map || !layerNameOrType) return null;

		const { drawInteractionKey, drawInteractionFlagKey } = this.resolveDrawInteractionOptions(options);
		this.removeDrawInteractions(map, options);

		const layerName = this.layerOrder.includes(layerNameOrType) ? layerNameOrType : null;
		const drawType = this.drawTypeByLayerName[layerNameOrType] ?? layerNameOrType;
		if (!this.validDrawTypes.includes(drawType)) return null;

		const layer = layerName ? this.getOrCreateLayerByName(map, layerName, options) : null;
		if (layerName && !layer) return null;

		const source = layer?.getSource?.() ?? new VectorSource();
		const drawStyle = this.getDrawStyle(layerName, drawType, {
			...(layer?.get?.('__styleOptions') ?? {}),
			...options,
		});
		const draw = new Draw({
			source,
			type: drawType,
			style: drawStyle,
		});
		draw.set(drawInteractionFlagKey, true);
		draw.set('layerName', layerName);
		draw.set('drawType', drawType);

		this.addInteraction(map, draw);
		map.set(drawInteractionKey, draw);
		if (typeof callBack === 'function') draw.on('drawend', event => callBack(event));
		return draw;
	}

	static setSnap(map, features = [], options = {}) {
		if (!map || StzUtils.isEmpty(features)) return null;

		const { interactionKey = this.defaultSnapInteractionKey, pixelTolerance = 15 } = options;
		this.removeSnapInteraction(map, { interactionKey });

		const snapCollection = new Collection(features);

		const snap = new Snap({
			features: snapCollection,
			pixelTolerance,
		});

		this.addInteraction(map, snap);
		map.set(interactionKey, snap);
		return snap;
	}

	static removeSnapInteraction(map, options = {}) {
		if (!map) return null;

		const { interactionKey = this.defaultSnapInteractionKey } = options;
		const snap = map.get(interactionKey);
		if (!snap) return null;

		map.removeInteraction(snap);
		map.set(interactionKey, null);
		return snap;
	}

	/**
	 * @description 지도에 전체화면 컨트롤 추가
	 * @param map
	 * @param options
	 * @returns {null}
	 */
	static setFullScreen(map, options = {}) {
		if (!map) return null;
		return this.addFullScreenControl(map, options);
	}

	/**
	 * @description 지도 View 애니메이션 추가
	 * @param map
	 * @param options
	 * @returns {void}
	 */
	static addViewAnimation(map, options = {}) {
		if (!map) return;
		const view = map.getView?.();
		if (!view) return;

		const { center, zoom, rotation, duration = 1000 } = options;
		view.animate({
			center,
			zoom,
			rotation,
			duration,
		});
	}

	static addEventListener(map, eventType, callback) {
		if (!map || !eventType || typeof callback !== 'function') return;
		map.on(eventType, callback);
	}

	static findFeatureLayer(map, feature, options = {}) {
		if (!map || !feature) return null;

		const { layerNames = [] } = options;
		const layers = map.getLayers?.()?.getArray?.() ?? [];

		return (
			layers.find(layer => {
				const layerName = layer.get?.('name');
				if (layerNames.length > 0 && !layerNames.includes(layerName)) return false;

				const source = layer.getSource?.();
				const features = source?.getFeatures?.() ?? [];

				return features.includes(feature);
			}) ?? null
		);
	}

	static setFeatureSelect(map, callback, options = {}) {
		if (!map) return null;

		const {
			layerNames = [],
			hitTolerance = 8,
			multi = false,
			condition = mapClick,
			interactionKey = '__featureSelectInteraction',
		} = options;

		const previousSelect = map.get(interactionKey);
		if (previousSelect) {
			map.removeInteraction(previousSelect);
			map.set(interactionKey, null);
		}

		const targetLayers =
			layerNames.length > 0 ? layerNames.map(layerName => this.getLayerByName(map, layerName)).filter(Boolean) : null;

		const select = new Select({
			condition,
			hitTolerance,
			multi,
			layers: targetLayers ?? undefined,
		});

		select.on('select', event => {
			const feature = event.selected?.[0] ?? null;
			const layer = feature ? this.findFeatureLayer(map, feature, { layerNames }) : null;

			if (typeof callback === 'function') {
				callback({
					feature,
					layer,
					layerName: layer?.get?.('name') ?? feature?.get?.('layer') ?? null,
					selected: event.selected ?? [],
					deselected: event.deselected ?? [],
					event,
					select,
				});
			}
		});

		this.addInteraction(map, select);
		map.set(interactionKey, select);

		return select;
	}

	static removeFeatureSelect(map, options = {}) {
		if (!map) return null;

		const { interactionKey = '__featureSelectInteraction' } = options;
		const select = map.get(interactionKey);

		if (!select) return null;

		map.removeInteraction(select);
		map.set(interactionKey, null);

		return select;
	}

	/**
	 * @description 지도에서 특정 레이어의 가시성 설정
	 * @param map
	 * @param layerName
	 * @param visible
	 */
	static setVisibleLayer(map, layerName, visible) {
		if (!map || !layerName) return;
		const layer = this.getLayerByName(map, layerName);
		if (!layer) return;
		layer.setVisible(!!visible);
	}

	static removeModifyInteraction(map, options = {}) {
		if (!map) return null;

		const { interactionKey = '__featureModifyInteraction' } = options;
		const modify = map.get(interactionKey);

		if (!modify) return null;

		map.removeInteraction(modify);
		map.set(interactionKey, null);

		return modify;
	}

	static setModify(map, featuresOrSource, callback, options = {}) {
		if (!map || !featuresOrSource) return null;

		const { interactionKey = this.defaultModifyInteractionKey, pixelTolerance = 10 } = options;

		this.removeModifyInteraction(map, options);

		const modifyOptions = {
			pixelTolerance,
		};

		if (featuresOrSource instanceof Collection) {
			modifyOptions.features = featuresOrSource;
		} else if (featuresOrSource?.getFeatures) {
			modifyOptions.source = featuresOrSource;
		} else if (Array.isArray(featuresOrSource)) {
			modifyOptions.features = new Collection(featuresOrSource);
		} else {
			return null;
		}

		const modify = new Modify(modifyOptions);

		modify.on('modifyend', event => {
			if (typeof callback === 'function') {
				callback({
					features: event.features?.getArray?.() ?? [],
					event,
					modify,
				});
			}
		});

		this.addInteraction(map, modify);
		map.set(interactionKey, modify);

		return modify;
	}

	static removeFeature(map, feature, options = {}) {
		if (!map || !feature) return false;

		const { layerNames = [] } = options;
		const layer = this.findFeatureLayer(map, feature, { layerNames });
		const source = layer?.getSource?.();

		if (!source) return false;

		source.removeFeature(feature);
		return true;
	}

	static removeSelectedFeatures(map, selectInteraction, options = {}) {
		if (!map || !selectInteraction) return [];

		const selectedFeatures = selectInteraction.getFeatures?.();
		const features = selectedFeatures?.getArray?.() ?? [];
		const removed = [];

		features.forEach(feature => {
			if (this.removeFeature(map, feature, options)) {
				removed.push(feature);
			}
		});

		selectedFeatures?.clear?.();

		return removed;
	}

	/**
	 * @description 지도에서 특정 레이어의 줌 범위 설정
	 * @param map
	 * @param layerName
	 * @param options
	 * @returns {*|null}
	 */
	static setLayerZoomRange(map, layerName, options = {}) {
		const layer = this.getLayerByName(map, layerName);
		if (!layer) return null;

		const { minZoom, maxZoom, minResolution, maxResolution } = options;

		if (minZoom != null) layer.setMinZoom(minZoom);
		if (maxZoom != null) layer.setMaxZoom(maxZoom);
		if (minResolution != null) layer.setMinResolution(minResolution);
		if (maxResolution != null) layer.setMaxResolution(maxResolution);

		return layer;
	}

	/**
	 * @description 지도에서 드래그 박스 선택 기능 설정
	 * @param map
	 * @param callback
	 * @param options
	 * @returns {{select: *, dragBox: *}|null}
	 */
	static setDragBox(map, callback, options = {}) {
		if (!map) return null;

		const {
			interactionKey = this.defaultDragBoxInteractionKey,
			selectInteractionKey = '__dragBoxSelectInteraction',
			condition = platformModifierKeyOnly,
			selectColor = {},
			layerNames = [],
		} = options;

		const prevDragBox = map.get(interactionKey);
		if (prevDragBox) this.removeInteraction(map, prevDragBox);

		const prevSelect = map.get(selectInteractionKey);
		if (prevSelect) this.removeInteraction(map, prevSelect);

		const selectedStyle = new Style({
			image: new Circle({
				radius: 8,
				fill: new Fill({
					color: selectColor.fillColor ?? 'rgba(255,255,255,0.6)',
				}),
				stroke: new Stroke({
					color: selectColor.strokeColor ?? 'rgba(0,0,255,0.8)',
					width: 2,
				}),
			}),
			fill: new Fill({
				color: selectColor.fillColor ?? 'rgba(255,255,255,0.6)',
			}),
			stroke: new Stroke({
				color: selectColor.strokeColor ?? 'rgba(0,0,255,0.8)',
				width: 2,
			}),
		});

		const select = new Select({
			filter: feature => feature.get('COLOR_BIO') !== '#CC6767',
			style: selectedStyle,
		});

		const dragBox = new DragBox({ condition });

		this.addInteraction(map, select);
		this.addInteraction(map, dragBox);

		map.set(selectInteractionKey, select);
		map.set(interactionKey, dragBox);

		dragBox.on('boxstart', () => {
			select.getFeatures().clear();
		});

		dragBox.on('boxend', () => {
			const extent = dragBox.getGeometry().getExtent();
			const selectedFeatures = select.getFeatures();

			const layers =
				layerNames.length > 0
					? layerNames.map(layerName => this.getLayerByName(map, layerName)).filter(Boolean)
					: map.getLayers().getArray();

			layers.forEach(layer => {
				const source = layer.getSource?.();
				if (!source?.forEachFeatureIntersectingExtent) return;

				source.forEachFeatureIntersectingExtent(extent, feature => {
					if (feature.get('COLOR_BIO') === '#CC6767') return;
					selectedFeatures.push(feature);
				});
			});

			callback?.({
				features: selectedFeatures.getArray(),
				select,
				dragBox,
				extent,
			});
		});

		return { select, dragBox };
	}
}
