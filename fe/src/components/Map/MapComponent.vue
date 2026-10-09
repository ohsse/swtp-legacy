<template>
  <div class="map-wrapper">
    <div ref="mapContainer" class="map-container"></div>
    <div v-if="timeText" class="time-display">
      {{ timeText }}
    </div>
    <button class="fullscreen-toggle-btn" @click="$emit('toggle-fullscreen')">
      <img v-if="!isFullscreen" src="@/assets/img/icon/icon-maximize.svg" alt="전체 화면" title="전체 화면" />
      <img v-else src="@/assets/img/icon/icon-minimize.svg" alt="일반 화면" title="일반 화면" />
    </button>
    <div v-if="isShowPin">
      <MapStatusPin v-for="poi in poiList" :key="poi.id" :status="poi.status" :style="poi.screenPosition"
        @mouseenter="handlePoiEnter(poi, $event)" @mouseleave="handlePoiLeave" />
    </div>


    <MapStatusLayer :visible="popupVisible" :style="{ top: popupPosition.y + 'px', left: popupPosition.x + 'px' }"
      :title="popupTitle" :flow="popupFlowData" :pressure="popupPressureData" :isSimulation="isSimulation" />
  </div>
</template>

<script>
import "ol/ol.css";
import Map from "ol/Map";
import View from "ol/View";
import TileLayer from 'ol/layer/Tile';
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import GeoJSON from "ol/format/GeoJSON";
import { Style, Stroke, Fill, Text, Icon } from "ol/style";
import circle from '@/assets/circle.png';
// import circle_gr from '@/assets/circle_gray.png'; // 일반 점 표시를 위해 import
import proj4 from 'proj4';
import { register } from 'ol/proj/proj4';
import TileImage from 'ol/source/TileImage';
import TileGrid from 'ol/tilegrid/TileGrid';
import { getTopLeft } from 'ol/extent';
import { fromLonLat } from 'ol/proj';
import MapStatusPin from "@/components/Map/MapStatusPin.vue";
import MapStatusLayer from "@/components/Map/MapStatusLayer.vue";
import { fetchFunc } from "@/util/fetchFunc";

proj4.defs("EPSG:5186", "+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m +no_defs");
proj4.defs("EPSG:5179", "+proj=tmerc +lat_0=38 +lon_0=127.5 +k=0.9996 +x_0=1000000 +y_0=2000000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs");
register(proj4);

export default {
  name: "MapComponent",
  components: { MapStatusPin, MapStatusLayer },
  vectorSource: null,
  activePoiId: null,
  props: {
    isFullscreen: {
      type: Boolean,
      default: false,
    },
    isShowPin:{
      type: Boolean,
      default: false,
    },
    isSimulation: {
      type: Boolean,
      default: false,
    },
    nodes: {
      type: Array,
      default: () => ([]),
    },
    timeText: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      map: null,
      popupVisible: false,
      popupPosition: { x: 0, y: 0 },
      popupTitle: '',
      popupFlowData: { measured: null, analyzed: null, error: null, state: "good" },
      popupPressureData: { measured: null, analyzed: null, error: null, state: "good" },
      poiList: [],
      // data 안에서 모든 변수를 안전하게 초기화합니다.
      poiIdSet: new Set(),
      poiInfoMap: new Map(),
      poiTextStyleCache: {},
      isMapReady: false,
      isNodesReady: false,
      isNetworkReady: false,
      isUnmounted: false,
    };
  },
  created() {
    // 관망은 지도가 뜬 뒤 API 로 받아 채운다(loadNetwork). 여기서는 빈 소스만 만들어
    // 레이어 구성이 지도 생성 시점에 끝나 있게 한다.
    this.vectorSource = new VectorSource();
  },
  mounted() {
    // 관망이 아직 비어 있어 범위를 모른다. extent/최소줌은 loadNetwork 에서 정한다.
    const backgroundLayer = new TileLayer({
      source: new TileImage({
        projection: 'EPSG:5179',
        tileGrid: new TileGrid({
          origin: getTopLeft([-200000.0, -28024123.62, 31824123.62, 4000000.0]),
          resolutions: [2088.96, 1044.48, 522.24, 261.12, 130.56, 65.28, 32.64, 16.32, 8.16, 4.08, 2.04, 1.02, 0.51],
          matrixIds: ["L05_1", "L06_1", "L07_1", "L08_1", "L09_1", "L10_1", "L11_1", "L12_1", "L13_1", "L14_1", "L15_1", "L16_1", "L17_1"],
        }),
        tileUrlFunction: (tileCoord) => {
          const z = tileCoord[0];
          const x = tileCoord[1];
          const y = tileCoord[2];
          if (z < 0) return undefined;
          const tileMatrix = "L" + this.fillZeroToZoomLevel(z + 5, 2) + "_1";
          // 상대경로로 요청한다. nginx(default.conf)의 location /newEMap/ 이
          // tile-server:25000 으로 프록시한다. 예전처럼 http://localhost:25000 을
          // 박아 두면 현장마다 프런트를 다시 말아야 하고 CORS 도 따라온다.
          const url = `/newEMap/${tileMatrix}/${x}/${y}.png`;
          return url;
        },
        crossOrigin: "anonymous",
      }),
    });
    const vectorLayer = new VectorLayer({
      source: this.vectorSource,
      style: (feature, resolution) => this.styleFunction(feature, resolution),
    });
    this.map = new Map({
      target: this.$refs.mapContainer,
      layers: [backgroundLayer, vectorLayer],
      // 관망이 도착하기 전의 임시 View. center/zoom 이 없으면 OpenLayers 가 해상도를
      // 못 정해 배경지도조차 그리지 않는다. 관망 로딩 중이거나 실패했을 때 빈 패널 대신
      // 전국 배경도가 보이도록 한반도 전체를 기본으로 둔다. 관망이 오면 loadNetwork 가
      // 관망 범위에 맞춘 View 로 갈아끼운다.
      view: new View({
        projection: 'EPSG:3857',
        maxZoom: 18,
        center: fromLonLat([127.5, 36.0]),
        zoom: 7,
      }),
    });

    this.map.on('postrender', this.updatePoiPositions);
    this.map.on('pointermove', this.handlePointerMove);

    this.isMapReady = true;
    this.loadNetwork();
  },
  beforeUnmount() {
    this.isUnmounted = true;
    if (this.map) {
      this.map.un('postrender', this.updatePoiPositions);
      this.map.un('pointermove', this.handlePointerMove);
    }
  },
  // [제거] nodes가 변경되지 않으므로 watch는 더 이상 필요 없습니다.
  watch: {
    isFullscreen() {
      this.$nextTick(() => {
        if (this.map) this.map.updateSize();
      });
    },
    nodes(newNodes) {
      // 데이터가 비어있지 않은 유효한 배열일 경우.
      // Array.isArray 로 막는 이유 — 부모가 API 응답을 그대로 넣는데 조회가 실패하면
      // 배열이 아닌 값이 올라온다. {} 는 length 가 undefined 라 예전 조건도 통과하지
      // 못했지만, 그때는 지도가 조용히 비어 원인을 찾기 어려웠다.
      if (Array.isArray(newNodes) && newNodes.length > 0) {
        // [핵심 수정] 2. '데이터 도착' 열쇠를 true로 변경하고, 게이트 함수를 호출합니다.
        this.isNodesReady = true;
        this.tryProcessData();
      }
    }
  },
  methods: {
    tryProcessData() {
      // 지도·노드·관망 세 열쇠가 모두 true일 때만 문을 엽니다.
      if (this.isMapReady && this.isNodesReady && this.isNetworkReady) {
        this.fetchPoiData();
      }
    },
    /**
     * 관망 형상을 epa API 에서 받아 지도에 채운다.
     *
     * 예전에는 번들에 박힌 combined_network.json 을 import 했는데, 그 파일은 고산 관망이라
     * 군산 스택에서는 표시지점 9건 중 1건만 절점 id 가 우연히 맞았고 그마저 39km 어긋난
     * 자리에 찍혔다. 관망은 현장마다 다르고 inpEditor 의 '적용'으로 런타임에 교체되므로,
     * 해석에 쓰는 INP 를 쥔 쪽(epa)이 내려주는 것이 맞다.
     */
    async loadNetwork() {
      const res = await fetchFunc(`${this.$pythonURL}/api/web/network`);
      // await 사이에 화면을 떠났을 수 있다. 그 뒤에 지도를 만지면 이미 지나간
      // beforeUnmount 의 정리를 되돌리는 꼴이 된다.
      if (this.isUnmounted) return;
      if (!res || res.error || !res.data) {
        // 실패하면 배경지도만 남는다. 예전 정적 파일을 폴백으로 두지 않는 이유는, 다른
        // 현장의 관망을 조용히 그리는 것이 빈 지도보다 나쁘기 때문이다.
        console.error('[MapComponent] 관망 형상을 불러오지 못했습니다:', res && res.message);
        return;
      }

      const geojson = res.data;
      const crs = geojson && geojson.crs && geojson.crs.properties
        ? geojson.crs.properties.name : null;
      // proj4 에 등록한 좌표계(파일 상단)가 아니면 좌표가 엉뚱한 곳에 찍힌다. 표준값으로
      // 떨어뜨리고 경고를 남긴다 — 5181 INP 는 좌표계를 늘릴 게 아니라 Y+100,000 으로
      // 5186 이관해서 써야 한다.
      const dataProjection = (crs === 'EPSG:5186' || crs === 'EPSG:5179') ? crs : 'EPSG:5186';
      if (crs && crs !== dataProjection) {
        console.warn(`[MapComponent] 등록되지 않은 좌표계 '${crs}' — EPSG:5186 으로 읽습니다.`);
      }

      this.vectorSource.addFeatures(new GeoJSON().readFeatures(geojson, {
        dataProjection,
        featureProjection: 'EPSG:3857',
      }));

      // View 의 extent(이동 제한)는 생성자 전용이라 나중에 못 바꾼다. 관망 범위를 알게 된
      // 지금 View 를 통째로 갈아끼운다. 화면 크기가 잡힌 뒤라야 최소줌 계산이 맞는다.
      this.$nextTick(() => {
        if (this.isUnmounted || !this.map) return;
        const bufferedExtent = this.getBufferedExtent(this.vectorSource.getExtent(), 0.1);
        if (bufferedExtent && bufferedExtent[0] !== Infinity) {
          const view = new View({
            projection: 'EPSG:3857',
            maxZoom: 18,
            extent: bufferedExtent,
          });
          this.map.setView(view);
          view.fit(bufferedExtent, { padding: [50, 50, 50, 50], duration: 1000, });
          // 크기를 명시한다. setView 직후에는 뷰포트 크기가 아직 뷰에 잡히지 않아
          // 인자를 비우면 최소줌이 엉뚱하게 계산될 수 있다.
          const resolution = view.getResolutionForExtent(bufferedExtent, this.map.getSize());
          const minZoomLevel = view.getZoomForResolution(resolution);
          view.setMinZoom(minZoomLevel);
        }
      });

      this.isNetworkReady = true;
      this.tryProcessData();
    },
    styleFunction(feature, resolution) {
      if (!this.poiIdSet) return;
      const properties = feature.getProperties();
      const featureType = properties.type; // e.g., 'junction' or 'pipe'
      const featureId = String(properties.id);

     
      if (featureType === 'junction' && this.poiIdSet.has(featureId)) {
        if (!this.poiTextStyleCache[featureId]) {
          const poiInfo = this.poiInfoMap.get(featureId);
          const displayName = poiInfo ? poiInfo.LOCATION_NM : featureId;
          this.poiTextStyleCache[featureId] = new Style({
            text: new Text({ text: `${displayName} 토출 압력`, offsetX: 85, font: 'bold 16px sans-serif', fill: new Fill({ color: '#fff' }), 
            backgroundFill: new Fill({ color: '#4A90E2' }), padding: [5, 8, 5, 8] }),
            zIndex: 10
          });
        }
        let scale;
        if (resolution > 50) scale = 0.1; else if (resolution > 10) scale = 0.15; else scale = 0.2;
        const iconStyle = new Style({ image: new Icon({ src: circle, scale: scale, anchor: [0.5, 0.5] }), zIndex: 9 });
        return [iconStyle, this.poiTextStyleCache[featureId]];
      }

      if (featureType === 'pipe') {
        const diameter = properties.diameter;
        let width;
        if (diameter > 1.0) { width = 3; } else if (diameter > 0.5) { width = 2; } else { width = 1.5; }
        return new Style({ stroke: new Stroke({ color: "#007BFF", width: width }) });
      }

      // if (featureType === 'junction') {
      //   let scale;
      //   if (resolution > 50) scale = 0.1; else if (resolution > 10) scale = 0.15; else scale = 0.2;
      //   return new Style({ image: new Icon({ src: circle_gr, scale: scale, anchor: [0.5, 0.5] }) });
      // }
    },
    fetchPoiData() {
      // nodes 는 prop 이고 부모가 API 응답을 그대로 넣는다. 조회 실패나 초기화 실수로
      // 배열이 아닌 값이 올 수 있으므로 여기서 한 번 막는다 — 아래 filter/forEach 가
      // "filter is not a function" 으로 죽으면 지도 전체가 그려지지 않는다.
      const nodes = Array.isArray(this.nodes) ? this.nodes : [];

      this.poiTextStyleCache = {};
      // nodes 는 모니터링 화면에서 5분마다 갱신되고(watch 가 재발화한다) 관망 feature 집합도
      // INP 교체로 바뀔 수 있다. 비우지 않으면 지난 회차의 절점이 남아 스타일과 팝업이
      // 유령 데이터를 문다.
      // clear() 대신 새로 만든다. 비우는 효과는 같으면서, 이 두 값이 어떤 이유로든
      // Map/Set 이 아니게 된 상태에서 "clear is not a function" 으로 멈추지 않는다.
      this.poiIdSet = new Set();
      this.poiInfoMap = new Map();

      nodes
      .filter(node => node.IS_DISPLAY == 1)
      .forEach(node => {
        const junctionId = String(node.JUNCTION_ID);
        this.poiIdSet.add(junctionId);
        this.poiInfoMap.set(junctionId, node);
      });
      this.poiList = nodes
      .filter(poiData => poiData.IS_DISPLAY == 1)
      .map(poiData => {
        const targetFeature = this.vectorSource.getFeatures().find(f => {
          const props = f.getProperties();

          return props.type === 'junction' && String(props.id) === String(poiData.JUNCTION_ID);
        });
        
        return targetFeature ? {
          id: poiData.JUNCTION_ID,
          status: poiData.status,
          geoCoordinates: targetFeature.getGeometry().getCoordinates(),
          screenPosition: { top: '-9999px', left: '-9999px' }
        } : null;
      }).filter(p => p !== null);


      if (this.vectorSource) this.vectorSource.changed();
    },
    updatePoiPositions() {
      if (!this.map || this.poiList.length === 0) return;
      this.poiList.forEach(poi => {
        const pixel = this.map.getPixelFromCoordinate(poi.geoCoordinates);
        if (pixel) {
          poi.screenPosition = { top: `${pixel[1]}px`, left: `${pixel[0]}px` };
        }
      });
    },
    handlePointerMove(event) {
      const feature = this.map.forEachFeatureAtPixel(
        event.pixel,
        (f) => f,
        { hitTolerance: 60 }
      );

      // type 을 함께 봐야 한다. 이 모델들은 절점 id 와 관로 id 가 대량으로 겹친다
      // (고산 311건, 군산 70건 — '10', '103' 같은 번호가 양쪽에 다 있다). 관망이
      // 직선이던 때와 달리 이제 관로가 실제 선형을 따르고 펌프·밸브도 그려지므로,
      // hitTolerance 60 안에서 같은 번호의 관로가 먼저 잡히면 절점 팝업이 엉뚱하게 떴다.
      // poiIdSet 은 String() 으로 채우므로(fetchPoiData) 조회도 String() 으로 맞춘다.
      const hitProps = feature ? feature.getProperties() : null;
      if (hitProps && hitProps.type === 'junction' && this.poiIdSet.has(String(hitProps.id))) {
        this.activePoiId = String(hitProps.id);
        // OpenLayers 이벤트 객체(event)를 그대로 전달
        this.showInfoPopup(feature, event);
      } else {
        if (this.activePoiId) {
          this.activePoiId = null;
          this.map.getTargetElement().style.cursor = '';
          this.popupVisible = false;
        }
      }
    },
    handlePoiEnter(poi, mouseEvent) {
      this.activePoiId = String(poi.id);
      // 절점 한정 + 문자열 비교. 이유는 handlePointerMove 주석 참고.
      const feature = this.vectorSource.getFeatures().find(f => {
        const props = f.getProperties();
        return props.type === 'junction' && String(props.id) === String(poi.id);
      });
      if (feature) this.showInfoPopup(feature, mouseEvent);
    },
    handlePoiLeave() {
      this.activePoiId = null;
      setTimeout(() => {
        if (!this.activePoiId) this.popupVisible = false;
      }, 100);
    },
    showInfoPopup(feature, event) {
      const properties = feature.getProperties();
      const featureId = String(properties.id);
      const poiInfo = this.poiInfoMap.get(featureId );
      if(!poiInfo) return;

      this.map.getTargetElement().style.cursor = 'pointer';
      
      this.popupTitle = poiInfo.LOCATION_NM || '정보';
      this.popupFlowData = {
        measured: poiInfo.flowMeasured,
        analyzed: poiInfo.flowAnalyzed,
        error: poiInfo.flowError, // 오차 값도 추가 (fmt 함수가 알아서 처리)
        state: poiInfo.flowStatus,
      };
      
      this.popupPressureData = {
        measured: poiInfo.pressureMeasured,
        analyzed: poiInfo.pressureAnalyzed,
        error: poiInfo.pressureError,
        state: poiInfo.pressureStatus,
      };      
      
      const POPUP_WIDTH = 260;
      const POPUP_HEIGHT = 180;
      const OFFSET = -300; // 마우스 커서와 팝업 사이의 간격 (px)

      const mapRect = this.map.getTargetElement().getBoundingClientRect();
      let mouseX, mouseY;

      // OpenLayers 이벤트와 DOM 이벤트를 구분하여 마우스 좌표 추출
      if (event.pixel) {
        mouseX = event.pixel[0];
        mouseY = event.pixel[1];
      } else {
        mouseX = event.clientX - mapRect.left;
        mouseY = event.clientY - mapRect.top;
      }

      let popupX, popupY;

      // Y 좌표 계산 (상하 위치)
      // 팝업이 지도 하단을 벗어나면 커서 위로, 아니면 아래로
      if ((mouseY + POPUP_HEIGHT + OFFSET) > mapRect.height) {
        popupY = mouseY - POPUP_HEIGHT - OFFSET;
      } else {
        popupY = mouseY + OFFSET - 200;
      }

      // X 좌표 계산 (좌우 위치)
      // 팝업이 지도 우측을 벗어나면 커서 왼쪽으로, 아니면 오른쪽으로
      if ((mouseX + POPUP_WIDTH + OFFSET) > mapRect.width) {
        popupX = mouseX - POPUP_WIDTH - OFFSET + 100;
      } else {
        popupX = mouseX + OFFSET - 100;
      }
      
      this.popupPosition.x = popupX;
      this.popupPosition.y = popupY;
      this.popupVisible = true;
    },
    getBufferedExtent(extent, buffer) {
      if (!extent || extent[0] === Infinity) return undefined;
      const width = extent[2] - extent[0];
      const height = extent[3] - extent[1];
      const bufferWidth = width * buffer;
      const bufferHeight = height * buffer;
      return [
        extent[0] - bufferWidth, extent[1] - bufferHeight,
        extent[2] + bufferWidth, extent[3] + bufferHeight,
      ];
    },
    fillZeroToZoomLevel(level, length) {
      return String(level).padStart(length, '0');
    },
  }
};
</script>

<style scoped>
.map-wrapper {
  position: relative;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.map-container {
  width: 100%;
  height: 100%;
  background-color: #f8f9fa;
}

.fullscreen-toggle-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
  /* OpenLayers 컨트롤 위에 표시되도록 z-index 설정 */
  background-color: rgba(255, 255, 255, 0.8);
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 5px;
  cursor: pointer;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fullscreen-toggle-btn:hover {
  background-color: white;
}

.time-display {
  position: absolute;
  top: 10px;
  /* 상단 여백 */
  left: 50%;
  transform: translateX(-50%);
  z-index: 999;
  /* 다른 요소들 위에 표시 (fullscreen 버튼보다는 낮게) */

  background-color: rgba(0, 0, 0, 0.6);
  /* 반투명 배경 */
  color: white;
  padding: 8px 12px;
  border-radius: 4px;

  font-size: 14px;
  font-weight: bold;
  white-space: nowrap;
  /* 텍스트가 줄바꿈되지 않도록 */

  /* 중요: 텍스트가 맵 조작을 방해하지 않도록 설정 */
  pointer-events: none;
}
</style>
