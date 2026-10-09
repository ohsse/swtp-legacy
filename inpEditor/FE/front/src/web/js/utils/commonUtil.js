/**
 * ═════════════════════════════════════════════════════════════
 * 📄 FILE     : commonUtil.js
 * 📁 PACKAGE  : front-
 * 👤 AUTHOR   : stz
 * 🕒 CREATED  : 26. 6. 12.
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 📝 DESCRIPTION
 *   -
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 🔄 CHANGE LOG
 *   - DATE : 2026/06/12 | Author : stz | 최초 생성
 * ═════════════════════════════════════════════════════════════
 */

export const byPromise = function (actions) {
	return actions.reduce((promise, action) => {
		return promise.then(async () => {
			if (typeof action === 'function') {
				return await action();
			} else {
				return await action;
			}
		});
	}, Promise.resolve());
};

export function parseContentDispositionFileName(contentDisposition) {
	if (!contentDisposition) return '';

	const encodedMatch = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
	if (encodedMatch?.[1]) {
		try {
			return decodeURIComponent(encodedMatch[1].replace(/"/g, '').trim());
		} catch {
			return encodedMatch[1].replace(/"/g, '').trim();
		}
	}

	const fileNameMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
	return fileNameMatch?.[1]?.trim() ?? '';
}

export async function saveDownloadResponse(response, fallbackFileName) {
	const blob = response instanceof Response ? await response.blob() : response;
	if (!(blob instanceof Blob)) {
		throw new Error('Invalid download response.');
	}

	const responseFileName =
		response instanceof Response ? parseContentDispositionFileName(response.headers.get('content-disposition')) : '';
	const fileName = responseFileName || fallbackFileName || 'download';
	const objectUrl = URL.createObjectURL(blob);
	const anchor = document.createElement('a');

	anchor.href = objectUrl;
	anchor.download = fileName;
	anchor.style.display = 'none';
	document.body.appendChild(anchor);
	anchor.click();
	anchor.remove();
	URL.revokeObjectURL(objectUrl);
}

export function toStringVal(value) {
	if (value === null || value === undefined) return '';
	return String(value);
}

export function toNumberOrRaw(value) {
	const parsed = Number(value);
	return Number.isNaN(parsed) ? value : parsed;
}

export function getNumberVal(value, fallback) {
	if (typeof value === 'number') return value;
	if (typeof value === 'string') {
		const parsed = Number(value);
		if (!Number.isNaN(parsed)) return parsed;
	}
	return fallback;
}

export function getBoolVal(value) {
	if (typeof value === 'boolean') return value;
	if (typeof value === 'string') return value.toLowerCase() === 'true';
	if (typeof value === 'number') return value > 0;
	return false;
}

export function resolveCellOption(row, column, key, optionName, fallback) {
	return row?.cellOptions?.[key]?.[optionName] ?? row?.[`${key}${optionName}`] ?? column?.[optionName] ?? fallback;
}

export function resolveComboOptionValue(option, optionValueKey) {
	if (option && typeof option === 'object') {
		return option[optionValueKey];
	}
	return option;
}

export function resolveComboOptionLabel(option, optionLabelKey) {
	if (option && typeof option === 'object') {
		return option[optionLabelKey];
	}
	return option;
}

export function isNegativeComboOption(value, label) {
	const normalizedValue = String(value ?? '')
		.trim()
		.toUpperCase();
	const normalizedLabel = String(label ?? '').trim();
	return normalizedValue === 'N' || normalizedLabel === '미분석' || normalizedLabel === '미표출';
}

export function extractWidthMeta(widthClassName = '') {
	const percentMatch = widthClassName.match(/w-\[(\d+(?:\.\d+)?)%\]/);
	if (percentMatch) {
		return {
			flex: Number(percentMatch[1]),
			minWidth: Math.max(90, Math.round(Number(percentMatch[1]) * 6)),
		};
	}

	const pixelMatch = widthClassName.match(/w-\[(\d+(?:\.\d+)?)px\]/);
	if (pixelMatch) {
		return { width: Number(pixelMatch[1]) };
	}

	const spacingMatch = widthClassName.match(/w-(\d+(?:\.\d+)?)$/);
	if (spacingMatch) {
		return { width: Number(spacingMatch[1]) * 4 };
	}

	return { flex: 1, minWidth: 110 };
}

export function stripWidthClassName(className = '') {
	return className
		.split(/\s+/)
		.filter(token => token && !/^w-(\[.*\]|\d+(\.\d+)?)$/.test(token))
		.join(' ');
}

export function resolveHeaderLabel(label) {
	if (typeof label === 'string' || typeof label === 'number') {
		return label;
	}
	return '';
}

export function buildGroupedHeaderMeta(colSeq, headRowSeq) {
	if (!Array.isArray(headRowSeq) || headRowSeq.length < 2) return null;

	const topRow = headRowSeq[0] ?? [];
	const bottomRow = headRowSeq[headRowSeq.length - 1] ?? [];
	const headerLabelByField = {};
	const topCells = [];
	let colIndex = 0;
	let bottomIndex = 0;

	topRow.forEach(cell => {
		const span = cell.colSpan ?? 1;
		const isRowSpan = (cell.rowSpan ?? 1) > 1;

		topCells.push({
			key: cell.key ?? `group-${colIndex}`,
			label: cell.colNm,
			className: cell.headClassName,
			span,
			isRowSpan,
		});

		if (isRowSpan) {
			const col = colSeq[colIndex];
			if (col) {
				headerLabelByField[col.key] = '';
			}
			colIndex += 1;
			return;
		}

		for (let i = 0; i < span; i += 1) {
			const col = colSeq[colIndex + i];
			if (!col) continue;
			headerLabelByField[col.key] = bottomRow[bottomIndex + i]?.colNm ?? col.colNm;
		}

		colIndex += span;
		bottomIndex += span;
	});

	return { topCells, headerLabelByField };
}

export function normalizeSelectedRowKey(selectedRowKey) {
	if (selectedRowKey == null) return null;
	if (Array.isArray(selectedRowKey)) return selectedRowKey[0] ?? null;
	if (selectedRowKey instanceof Set) return selectedRowKey.values().next().value ?? null;
	return selectedRowKey;
}

export function createRowSelectionModel(selectedRowKey) {
	return {
		type: 'include',
		ids: selectedRowKey == null ? new Set() : new Set([selectedRowKey]),
	};
}

export function createInitialState(initialSortModel, initialFilterModel) {
	const nextState = {};

	if (Array.isArray(initialSortModel) && initialSortModel.length > 0) {
		nextState.sorting = {
			sortModel: initialSortModel,
		};
	}

	if (initialFilterModel && Array.isArray(initialFilterModel.items)) {
		nextState.filter = {
			filterModel: initialFilterModel,
		};
	}

	return Object.keys(nextState).length > 0 ? nextState : undefined;
}
