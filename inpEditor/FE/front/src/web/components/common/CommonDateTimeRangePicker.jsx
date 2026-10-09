import { TextField } from '@mui/material';
import { useEffect, useMemo } from 'react';
import { IoCalendarOutline } from 'react-icons/io5';

const DATE_TIME_VALUE_PATTERN = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?$/;
const DATE_VALUE_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/;
const DATE_PICKER_TYPE = {
	DATE: 'date',
	DATE_TIME: 'datetime-local',
};
const DATE_PICKER_DISPLAY_TYPE = {
	RANGE: 'range',
	SINGLE: 'single',
};

const dateTimeInputSx = {
	minWidth: 190,
	position: 'relative',
	'& .MuiInputLabel-root': {
		color: 'rgba(226, 242, 255, 0.82)',
		fontSize: 12,
		fontWeight: 700,
	},
	'& .MuiInputLabel-root.Mui-focused': {
		color: '#ffffff',
	},
	'& .MuiOutlinedInput-root': {
		height: 34,
		borderRadius: '6px',
		color: '#f8fbff',
		backgroundColor: 'rgba(5, 16, 40, 0.74)',
		'& fieldset': {
			borderColor: 'rgba(110,185,255,0.34)',
		},
		'&:hover fieldset': {
			borderColor: 'rgba(110,185,255,0.58)',
		},
		'&.Mui-focused fieldset': {
			borderColor: 'rgba(125,211,252,0.86)',
		},
	},
	'& .MuiInputBase-input': {
		fontSize: 12,
		fontWeight: 600,
		colorScheme: 'dark',
	},
	'& .MuiFormHelperText-root': {
		position: 'absolute',
		top: 34,
		left: 0,
		m: 0,
		fontSize: 10,
		fontWeight: 700,
		color: '#ff9ca3',
		whiteSpace: 'nowrap',
	},
};

function parseDateValue(value) {
	if (!value) return null;

	const dateMatch = String(value).match(DATE_VALUE_PATTERN);
	if (!dateMatch) return null;

	const [, yearText, monthText, dayText] = dateMatch;
	const year = Number(yearText);
	const month = Number(monthText);
	const day = Number(dayText);
	const date = new Date(year, month - 1, day, 0, 0, 0);
	const isValid = date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;

	return isValid ? date : null;
}

function parseDateTimeValue(value) {
	if (!value) return null;
	const match = String(value).match(DATE_TIME_VALUE_PATTERN);
	if (!match) return null;

	const [, yearText, monthText, dayText, hourText, minuteText, secondText = '0'] = match;
	const year = Number(yearText);
	const month = Number(monthText);
	const day = Number(dayText);
	const hour = Number(hourText);
	const minute = Number(minuteText);
	const second = Number(secondText);
	const date = new Date(year, month - 1, day, hour, minute, second);
	const isValid =
		date.getFullYear() === year &&
		date.getMonth() === month - 1 &&
		date.getDate() === day &&
		date.getHours() === hour &&
		date.getMinutes() === minute &&
		date.getSeconds() === second;

	return isValid ? date : null;
}

function parseLocalDateTime(value) {
	return parseDateValue(value) ?? parseDateTimeValue(value);
}

function parsePickerValue(value, type) {
	if (type === DATE_PICKER_TYPE.DATE) return parseDateValue(value);
	if (type === DATE_PICKER_TYPE.DATE_TIME) return parseDateTimeValue(value);
	return parseLocalDateTime(value);
}

function resolveRangeValidation({ startValue, endValue, required, minDateTime, maxDateTime, maxRangeDays, type }) {
	const errors = {
		start: '',
		end: '',
	};
	const startDate = parsePickerValue(startValue, type);
	const endDate = parsePickerValue(endValue, type);
	const minDate = parsePickerValue(minDateTime, type);
	const maxDate = parsePickerValue(maxDateTime, type);

	if (required && !startValue) {
		errors.start = '시작날짜를 입력해주세요.';
	} else if (startValue && !startDate) {
		errors.start = '시작날짜 형식이 올바르지 않습니다.';
	}

	if (required && !endValue) {
		errors.end = '끝날짜를 입력해주세요.';
	} else if (endValue && !endDate) {
		errors.end = '끝날짜 형식이 올바르지 않습니다.';
	}

	if (startDate && minDate && startDate < minDate) {
		errors.start = '시작날짜가 허용 범위보다 빠릅니다.';
	}
	if (startDate && maxDate && startDate > maxDate) {
		errors.start = '시작날짜가 허용 범위보다 늦습니다.';
	}
	if (endDate && minDate && endDate < minDate) {
		errors.end = '끝날짜가 허용 범위보다 빠릅니다.';
	}
	if (endDate && maxDate && endDate > maxDate) {
		errors.end = '끝날짜가 허용 범위보다 늦습니다.';
	}

	if (startDate && endDate && startDate > endDate) {
		errors.start = '시작날짜는 끝날짜보다 늦을 수 없습니다.';
		errors.end = '끝날짜는 시작날짜보다 빨라질 수 없습니다.';
	}

	if (startDate && endDate && maxRangeDays) {
		const rangeMs = endDate.getTime() - startDate.getTime();
		const maxRangeMs = Number(maxRangeDays) * 24 * 60 * 60 * 1000;
		if (rangeMs > maxRangeMs) {
			errors.end = `조회 기간은 최대 ${maxRangeDays}일까지 가능합니다.`;
		}
	}

	return {
		isValid: !errors.start && !errors.end,
		errors,
		startDate,
		endDate,
	};
}

function resolveSingleValidation({ value, required, minDateTime, maxDateTime, type }) {
	const errors = {
		value: '',
	};
	const date = parsePickerValue(value, type);
	const minDate = parsePickerValue(minDateTime, type);
	const maxDate = parsePickerValue(maxDateTime, type);

	if (required && !value) {
		errors.value = '날짜를 입력해주세요.';
	} else if (value && !date) {
		errors.value = '날짜 형식이 올바르지 않습니다.';
	}

	if (date && minDate && date < minDate) {
		errors.value = '날짜가 허용 범위보다 빠릅니다.';
	}
	if (date && maxDate && date > maxDate) {
		errors.value = '날짜가 허용 범위보다 늦습니다.';
	}

	return {
		isValid: !errors.value,
		errors,
		date,
	};
}

function CommonDateTimeRangePicker({
	label = '기간',
	datePickerType = DATE_PICKER_DISPLAY_TYPE.RANGE,
	value,
	onChange,
	startValue,
	endValue,
	onStartChange,
	onEndChange,
	singleLabel = '날짜',
	startLabel = '시작',
	endLabel = '종료',
	required = true,
	minDateTime,
	maxDateTime,
	maxRangeDays,
	onValidationChange,
	actionLabel,
	onActionClick,
	type = DATE_PICKER_TYPE.DATE_TIME,
	inputType,
	className = '',
}) {
	const pickerType = inputType ?? type;
	const isSinglePicker = datePickerType === DATE_PICKER_DISPLAY_TYPE.SINGLE;
	const rangeValidation = useMemo(
		() =>
			resolveRangeValidation({
				startValue,
				endValue,
				required,
				minDateTime,
				maxDateTime,
				maxRangeDays,
				type: pickerType,
			}),
		[endValue, maxDateTime, maxRangeDays, minDateTime, pickerType, required, startValue]
	);
	const singleValidation = useMemo(
		() =>
			resolveSingleValidation({
				value,
				required,
				minDateTime,
				maxDateTime,
				type: pickerType,
			}),
		[maxDateTime, minDateTime, pickerType, required, value]
	);
	const validation = isSinglePicker ? singleValidation : rangeValidation;

	useEffect(() => {
		if (isSinglePicker) {
			onValidationChange?.({
				isValid: validation.isValid,
				errors: validation.errors,
				date: validation.date,
			});
			return;
		}

		onValidationChange?.({
			isValid: validation.isValid,
			errors: validation.errors,
			startDate: validation.startDate,
			endDate: validation.endDate,
		});
	}, [
		isSinglePicker,
		onValidationChange,
		validation.date,
		validation.endDate,
		validation.errors,
		validation.isValid,
		validation.startDate,
	]);

	return (
		<div className={['flex min-w-0 items-center gap-2', className].filter(Boolean).join(' ')}>
			<div className="flex h-[34px] shrink-0 items-center gap-1.5 rounded-[4px] bg-[#0f3970] px-2 text-[12px] font-bold text-sky-50 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]">
				<IoCalendarOutline className="h-3.5 w-3.5 text-sky-100/85" />
				<span>{label}</span>
			</div>
			{isSinglePicker ? (
				<TextField
					type={pickerType}
					label={singleLabel}
					value={value}
					onChange={event => onChange?.(event.target.value)}
					size="small"
					sx={dateTimeInputSx}
					InputLabelProps={{ shrink: true }}
					inputProps={{ min: minDateTime, max: maxDateTime, required }}
					error={Boolean(validation.errors.value)}
					helperText={validation.errors.value}
				/>
			) : (
				<>
					<TextField
						type={pickerType}
						label={startLabel}
						value={startValue}
						onChange={event => onStartChange?.(event.target.value)}
						size="small"
						sx={dateTimeInputSx}
						InputLabelProps={{ shrink: true }}
						inputProps={{ min: minDateTime, max: maxDateTime, required }}
						error={Boolean(validation.errors.start)}
						helperText={validation.errors.start}
					/>
					<span className="text-xs font-semibold text-sky-100/60">~</span>
					<TextField
						type={pickerType}
						label={endLabel}
						value={endValue}
						onChange={event => onEndChange?.(event.target.value)}
						size="small"
						sx={dateTimeInputSx}
						InputLabelProps={{ shrink: true }}
						inputProps={{ min: minDateTime, max: maxDateTime, required }}
						error={Boolean(validation.errors.end)}
						helperText={validation.errors.end}
					/>
				</>
			)}
			{actionLabel ? (
				<button
					type="button"
					onClick={onActionClick}
					className="h-[34px] shrink-0 rounded-[4px] border border-sky-200/60 bg-[#1c5b9e] px-4 text-[12px] font-bold text-sky-50 transition hover:border-white/80 hover:bg-[#236bb8]"
				>
					{actionLabel}
				</button>
			) : null}
		</div>
	);
}

export default CommonDateTimeRangePicker;
export { parseLocalDateTime, resolveRangeValidation, resolveSingleValidation };
