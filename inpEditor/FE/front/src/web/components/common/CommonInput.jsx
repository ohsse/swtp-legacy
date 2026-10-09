import { TextField } from '@mui/material';

function CommonInput({
	value = '',
	onChange,
	className = '',
	label,
	placeholder,
	variant = 'outlined',
	size = 'small',
	type = 'text',
	readOnly = false,
	disabled = false,
	slotProps,
	InputLabelProps,
	inputProps,
	sx,
	...props
}) {
	const resolvedSlotProps = {
		...slotProps,
		input: {
			...(slotProps?.input ?? {}),
			...(readOnly ? { readOnly: true } : {}),
			...(inputProps ?? {}),
		},
	};

	return (
		<TextField
			value={value}
			onChange={event => onChange?.(event.target.value, event)}
			className={className}
			label={label}
			placeholder={placeholder}
			variant={variant}
			size={size}
			type={type}
			disabled={disabled}
			slotProps={resolvedSlotProps}
			InputLabelProps={InputLabelProps}
			sx={sx}
			{...props}
		/>
	);
}

export { CommonInput };
export default CommonInput;
