const mapRegistry = new Map();

export function registerMap(mapId, mapInstance) {
	if (!mapId || !mapInstance) return;

	const existingMap = mapRegistry.get(mapId);
	if (existingMap && existingMap !== mapInstance) {
		existingMap.setTarget(null);
	}

	mapRegistry.set(mapId, mapInstance);
}

export function getMap(mapId) {
	if (!mapId) return null;
	return mapRegistry.get(mapId) ?? null;
}

export function hasMap(mapId) {
	return getMap(mapId) !== null;
}

export function disposeMap(mapId) {
	const mapInstance = getMap(mapId);
	if (!mapInstance) return;

	mapInstance.setTarget(null);
	mapRegistry.delete(mapId);
}

export function clearMapRegistry() {
	mapRegistry.forEach(mapInstance => {
		mapInstance.setTarget(null);
	});
	mapRegistry.clear();
}
