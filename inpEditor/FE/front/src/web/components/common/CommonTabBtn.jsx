function CommonTabBtn({
	label,
	onClick,
	disabled = false,
	title,
	isActive = false,
	type = 'button',
	className = '',
	...props
}) {
	return (
		<button
			type={type}
			onClick={onClick}
			disabled={disabled}
			title={title ?? 'AI 모드 변경'}
			className={[
				'ml-[5px] flex h-[26px] w-auto items-center rounded-[20px] border border-[#b4dffa] px-[10px] text-[13px] font-normal transition',
				isActive ? 'bg-[#b4dffa] text-black shadow-[0_0_5px_1px_rgba(180,223,250,0.6)]' : 'bg-[#4b668d] text-[#313131]',
				disabled ? 'cursor-not-allowed opacity-55' : 'cursor-pointer',
				className,
			]
				.filter(Boolean)
				.join(' ')}
			{...props}
		>
			{label}
		</button>
	);
}

export default CommonTabBtn;
