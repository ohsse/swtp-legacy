<template>
  <div ref="mapContainer" class="map-container"></div>
</template>

<script>
// OpenLayers 모듈 Import
import "ol/ol.css";
import Map from "ol/Map";
import View from "ol/View";
import TileLayer from 'ol/layer/Tile';
import TileGrid from 'ol/tilegrid/TileGrid';
import XYZ from 'ol/source/XYZ';
import { get as getProjection } from 'ol/proj';
import { getTopLeft, getCenter } from 'ol/extent';
import proj4 from 'proj4';
import { register } from 'ol/proj/proj4';

// ★ 1. EPSG:5179 좌표계 정의 및 등록
proj4.defs("EPSG:5179", "+proj=tmerc +lat_0=38 +lon_0=127.5 +k=0.9996 +x_0=1000000 +y_0=2000000 +ellps=GRS80 +units=m +no_defs");
register(proj4);
const epsg5179 = getProjection('EPSG:5179');

export default {
  name: "MapTest",
  data() {
    return { map: null };
  },
  mounted() {
    // --- ★ 2. 공식 API에 명시된 정확한 지도 규칙을 사용 ---
    const resolutions = [2088.96, 1044.48, 522.24, 261.12, 130.56, 65.28, 32.64, 16.32, 8.16, 4.08, 2.04, 1.02, 0.51, 0.255];
    const mapBounds = [705680.0, 1349270.0, 1388291.0, 2581448.0];
    
    const customTileGrid = new TileGrid({
        extent: mapBounds,                       // ★ 정확한 지도 범위 적용
        origin: getTopLeft(mapBounds),           // ★ 정확한 원점 적용
        resolutions: resolutions,
    });

    // --- 3. 배경지도 레이어 생성 ---
    const backgroundLayer = new TileLayer({
        source: new XYZ({
            tileGrid: customTileGrid,
            tileUrlFunction: (tileCoord) => {
                const z = tileCoord[0];
                const x = tileCoord[1];
                const y = tileCoord[2]; // Y좌표는 양수이므로 변환 없이 사용

                // z+5 계산은 이전 GissApp.js를 따름 (0~13 -> L05~L18)
                const level = z + 5; 
                if (level < 10 || level > 15) return undefined;
                
                const zoomStr = "L" + String(level).padStart(2, '0');
                
                const url = `http://localhost:3001/tiles/${zoomStr}/${x}/${y}.png`;
                console.log("요청 URL:", url);
                return url;
            }
        })
    });
    
    // --- 4. View와 모든 것을 EPSG:5179로 통일 ---
    this.map = new Map({
      target: this.$refs.mapContainer,
      layers: [backgroundLayer],
      view: new View({ 
        projection: epsg5179,
        resolutions: resolutions,
        center: getCenter(mapBounds), // ★ 정확한 지도 범위의 중심으로 시작
        zoom: 2, // 초기 줌 레벨
      }),
    });
  },
};
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100vh;
}
</style>