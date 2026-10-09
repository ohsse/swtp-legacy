import { MenuItem, TextField } from '@mui/material';

function resolveOptionValue(option, optionValueKey) {
	if (option && typeof option === 'object') {
		return option[optionValueKey];
	}
	return option;
}

function resolveOptionLabel(option, optionLabelKey) {
	if (option && typeof option === 'object') {
		return option[optionLabelKey];
	}
	return option;
}

function CommonSelect({
	value = '',
	onChange,
	options = [],
	className = '',
	label,
	placeholder,
	variant = 'outlined',
	size = 'small',
	disabled = false,
	sx,
	menuProps,
	SelectProps,
	optionLabelKey = 'label',
	optionValueKey = 'value',
	renderOption,
	slotProps,
	InputLabelProps,
	...props
}) {
	const resolvedSelectProps = {
		...SelectProps,
		MenuProps: {
			...(menuProps ?? {}),
			...(SelectProps?.MenuProps ?? {}),
		},
	};

	return (
		<TextField
			select
			value={value}
			onChange={event => onChange?.(event.target.value, event)}
			className={className}
			label={label}
			placeholder={placeholder}
			variant={variant}
			size={size}
			disabled={disabled}
			sx={sx}
			SelectProps={resolvedSelectProps}
			slotProps={slotProps}
			InputLabelProps={InputLabelProps}
			{...props}
		>
			{options.map(option => {
				const optionValue = resolveOptionValue(option, optionValueKey);
				const optionLabel = resolveOptionLabel(option, optionLabelKey);

				return (
					<MenuItem key={String(optionValue)} value={optionValue}>
						{renderOption ? renderOption(option) : optionLabel}
					</MenuItem>
				);
			})}
		</TextField>
	);
}

export { CommonSelect };
export default CommonSelect;
