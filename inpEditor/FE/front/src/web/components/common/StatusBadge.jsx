import React from 'react';
import CommonBadge from '@/web/components/common/CommonBadge.jsx';

const statusConfigByKey = {
	NORMAL: { label: '정상', tone: 'success' },
	OK: { label: '정상', tone: 'success' },
	SUCCESS: { label: '정상', tone: 'success' },
	GOOD: { label: '정상', tone: 'success' },
	WARNING: { label: '주의', tone: 'warning' },
	CAUTION: { label: '주의', tone: 'warning' },
	WARN: { label: '주의', tone: 'warning' },
	ERROR: { label: '오류', tone: 'error' },
	FAIL: { label: '오류', tone: 'error' },
	FAILED: { label: '오류', tone: 'error' },
	DANGER: { label: '경고', tone: 'error' },
	RUNNING: { label: '진행', tone: 'info' },
	READY: { label: '대기', tone: 'neutral' },
	WAIT: { label: '대기', tone: 'neutral' },
	UNKNOWN: { label: '미확인', tone: 'neutral' },
	정상: { label: '정상', tone: 'success' },
	주의: { label: '주의', tone: 'warning' },
	경고: { label: '경고', tone: 'error' },
	오류: { label: '오류', tone: 'error' },
	진행: { label: '진행', tone: 'info' },
	대기: { label: '대기', tone: 'neutral' },
};

function normalizeStatusKey(status) {
	if (status === null || status === undefined || status === '') return 'UNKNOWN';
	return String(status).trim().toUpperCase();
}

function StatusBadge({ status = 'NORMAL', label, className = '', size = 'md', ...props }) {
	const normalizedKey = normalizeStatusKey(status);
	const config = statusConfigByKey[normalizedKey] ?? statusConfigByKey[String(status).trim()] ?? statusConfigByKey.UNKNOWN;

	return <CommonBadge tone={config.tone} size={size} label={label ?? config.label} className={className} {...props} />;
}

export { StatusBadge, statusConfigByKey };
export default React.memo(StatusBadge);
