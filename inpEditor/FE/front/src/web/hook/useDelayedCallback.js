/**
 * ═════════════════════════════════════════════════════════════
 * 📄 FILE     : useDelayedCallback.js
 * 📁 PACKAGE  : GLOBAL_SAAS-
 * 👤 AUTHOR   : stz
 * 🕒 CREATED  : 25. 12. 2.
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 📝 DESCRIPTION
 *   -
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 🔄 CHANGE LOG
 *   - DATE : 2025/12/02 | Author : stz | 최초 생성
 * ═════════════════════════════════════════════════════════════
 */
import { useRef, useCallback, useEffect } from 'react';

export function useDelayedCallback(callBack, delay = 300) {
	const fnRef = useRef(callBack);
	const timerRef = useRef(null);

	useEffect(() => {
		fnRef.current = callBack;
	}, [callBack]);

	const execute = useCallback(
		(...args) => {
			if (timerRef.current) {
				clearTimeout(timerRef.current);
			}

			timerRef.current = setTimeout(() => {
				fnRef.current(...args);
			}, delay);
		},
		[delay]
	);

	const cancel = useCallback(() => {
		if (timerRef.current) {
			clearTimeout(timerRef.current);
			timerRef.current = null;
		}
	}, []);

	return [execute, cancel];
}
