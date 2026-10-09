/**
 * ═════════════════════════════════════════════════════════════
 * 📄 FILE     : useLocalStorage.js
 * 📁 PACKAGE  : GLOBAL_SAAS-
 * 👤 AUTHOR   : stz
 * 🕒 CREATED  : 25. 05. 25.
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 📝 DESCRIPTION
 *   - 브라우저 로컬 스토리지의 변화를 감지하여 상태로 관리하는 커스텀 훅
 * ═════════════════════════════════════════════════════════════
 * ═════════════════════════════════════════════════════════════
 * 🔄 CHANGE LOG
 *   - DATE : 2025/05/25 | Author : stz | 최초 생성
 * ═════════════════════════════════════════════════════════════
 */
import { useState, useEffect } from 'react';

export const useLocalStorage = () => {
	const [storage, setStorage] = useState({});

	useEffect(() => {
		if (localStorage.length === 0) return;
		const updateStorage = () => {
			const storageObj = {};
			for (let i = 0; i < localStorage.length; i++) {
				const key = localStorage.key(i);
				const value = localStorage.getItem(key);
				if (key.includes('token')) {
					try {
						storageObj[key] = JSON.parse(value);
					} catch (e) {
						storageObj[key] = value;
					}
				} else {
					storageObj[key] = value;
				}
			}
			setStorage(storageObj);
		};

		updateStorage();

		const handleStorageChange = () => {
			if (localStorage.length === 0) return;
			updateStorage();
		};

		window.addEventListener('storage', handleStorageChange);

		return () => {
			window.removeEventListener('storage', handleStorageChange);
		};
	}, []);

	return storage;
};
