import { DataGrid, useGridApiRef } from '@mui/x-data-grid';
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import {
	buildGroupedHeaderMeta,
	createInitialState,
	createRowSelectionModel,
	extractWidthMeta,
	getBoolVal,
	getNumberVal,
	isNegativeComboOption,
	normalizeSelectedRowKey,
	resolveCellOption,
	resolveComboOptionLabel,
	resolveComboOptionValue,
	resolveHeaderLabel,
	stripWidthClassName,
	toNumberOrRaw,
	toStringVal,
} from '@/web/js/utils/commonUtil.js';
import CommonSelect from './CommonSelect.jsx';

function renderDefaultComboText(value, label, isSelected = false) {
	const isNegative = isNegativeComboOption(value, label);
	const color = isNegative ? '#f87171' : isSelected ? '#ffffff' : '#111827';

	return (
		<span
			style={{
				color,
				WebkitTextFillColor: color,
				fontWeight: isNegative ? 700 : 500,
			}}
		>
			{toStringVal(label ?? value)}
		</span>
	);
}

function NoRowsOverlay({ message }) {
	return <div className="flex h-full items-center justify-center text-sm text-sky-100/70">{message}</div>;
}

function LoadingOverlay({ message }) {
	return <div className="flex h-full items-center justify-center text-sm text-sky-100/70">{message}</div>;
}

function HeaderLabel({ label }) {
	return (
		<div className="flex w-full min-w-0 items-center justify-center">
			<span className="min-w-0 truncate text-white">{label}</span>
		</div>
	);
}

const pendingCaretByCell = new Map();

function restoreCaretAfterGridRender(cellKey, caret) {
	window.requestAnimationFrame(() => {
		window.requestAnimationFrame(() => {
			const input = Array.from(document.querySelectorAll('input[data-common-table-cell-key]')).find(
				candidate => candidate.dataset.commonTableCellKey === cellKey
			);
			if (!input) return;

			input.focus({ preventScroll: true });
			input.setSelectionRange(caret.start, caret.end);
		});
	});
}

function EditableCellInput({ cellKey, value, inputType, placeholder, disabled, className, onClick, onChange }) {
	const inputRef = useRef(null);

	useLayoutEffect(() => {
		const pendingCaret = pendingCaretByCell.get(cellKey);
		if (!pendingCaret || !inputRef.current) return;

		pendingCaretByCell.delete(cellKey);
		inputRef.current.focus({ preventScroll: true });
		inputRef.current.setSelectionRange(pendingCaret.start, pendingCaret.end);
	});

	const handleChange = event => {
		if (event.target.selectionStart != null && event.target.selectionEnd != null) {
			const caret = {
				start: event.target.selectionStart,
				end: event.target.selectionEnd,
			};
			pendingCaretByCell.set(cellKey, caret);
			restoreCaretAfterGridRender(cellKey, caret);
		}
		onChange(event);
	};
	const handleKeyDown = event => {
		if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) {
			event.stopPropagation();
		}
	};

	return (
		<input
			ref={inputRef}
			data-common-table-cell-key={cellKey}
			type={inputType}
			value={value}
			placeholder={placeholder}
			disabled={disabled}
			className={className}
			onClick={onClick}
			onChange={handleChange}
			onKeyDown={handleKeyDown}
		/>
	);
}

function CommonTable({
	type = 'default',
	colSeq,
	headRowSeq,
	rowSeq,
	getRowKey,
	caption,
	emptyMsg = '조회된 데이터가 없습니다.',
	headRowClassName,
	rowClassName,
	selectedRowKey = null,
	onRowClick,
	onCellChange,
	treeOpt,
	loading = false,
	loadingMsg = '조회 중입니다.',
	isRowDisabled,
	stickyHeader = false,
	isDisabled = false,
	enableSorting = false,
	enableFiltering = false,
	enableColumnResize = false,
	disableHeaderSortClick = false,
	hideFooter = true,
	initialSortModel,
	initialFilterModel,
	initialPaginationModel,
	pageSizeOptions,
	paginationModel,
	sortModel: sortModelProp,
	filterModel: filterModelProp,
	onPaginationModelChange,
	onSortModelChange,
	onFilterModelChange,
	ignoreDiacritics = false,
	rowHeight = 40,
	columnHeaderHeight = 38,
	autoRowHeight = false,
	dataTestId,
	ariaLabel,
	sx,
}) {
	const groupedHeaderMeta = useMemo(() => buildGroupedHeaderMeta(colSeq, headRowSeq), [colSeq, headRowSeq]);
	const resolvedSelectedRowKey = useMemo(() => normalizeSelectedRowKey(selectedRowKey), [selectedRowKey]);
	const rowSelectionModel = useMemo(() => createRowSelectionModel(resolvedSelectedRowKey), [resolvedSelectedRowKey]);
	const apiRef = useGridApiRef();
	const [innerSortModel, setInnerSortModel] = useState(() => initialSortModel ?? []);
	const [innerFilterModel, setInnerFilterModel] = useState(() => initialFilterModel ?? { items: [] });
	const blockNextHeaderSortRef = useRef(false);
	const lastScrolledRowKeyRef = useRef(null);
	const controlledSortModel = sortModelProp ?? innerSortModel;
	const controlledFilterModel = filterModelProp ?? innerFilterModel;
	const initialState = useMemo(() => {
		const baseState = createInitialState(initialSortModel, initialFilterModel);
		if (!initialPaginationModel) return baseState;

		return {
			...(baseState ?? {}),
			pagination: {
				paginationModel: initialPaginationModel,
			},
		};
	}, [initialFilterModel, initialPaginationModel, initialSortModel]);

	const rows = useMemo(
		() =>
			(rowSeq ?? []).map(row => ({
				...row,
				id: getRowKey ? getRowKey(row) : row.id,
			})),
		[getRowKey, rowSeq]
	);

	const columns = useMemo(
		() =>
			(colSeq ?? []).map((col, colIndex) => {
				const widthMeta = {
					...extractWidthMeta(col.widthClassName),
					...(col.width ? { width: col.width } : {}),
					...(col.flex ? { flex: col.flex } : {}),
					...(col.minWidth ? { minWidth: col.minWidth } : {}),
				};
				const headerClassName = stripWidthClassName(col.headClassName);
				const cellClassName = stripWidthClassName(col.cellClassName);
				const resolvedHeaderLabel = groupedHeaderMeta?.headerLabelByField?.[col.key] ?? col.colNm;
				const resolvedFilterable = col.filterable ?? enableFiltering;

				return {
					field: col.key,
					headerName: resolveHeaderLabel(resolvedHeaderLabel),
					sortable: col.sortable ?? enableSorting,
					filterable: resolvedFilterable,
					resizable: col.resizable ?? enableColumnResize,
					editable: false,
					disableColumnMenu: col.disableColumnMenu ?? !(enableFiltering || enableSorting),
					sortingOrder: col.sortingOrder,
					sortComparator: col.sortComparator,
					getSortComparator: col.getSortComparator,
					valueFormatter: col.valueFormatter ? (value, row) => col.valueFormatter(value, row) : undefined,
					headerClassName,
					cellClassName,
					...widthMeta,
					renderHeader: () =>
						typeof resolvedHeaderLabel === 'string' || typeof resolvedHeaderLabel === 'number' ? (
							<HeaderLabel label={resolvedHeaderLabel} />
						) : (
							resolvedHeaderLabel
						),
					renderCell: params => {
						const row = params.row;
						const rowKey = row.id;
						const disabledByRow = isDisabled || Boolean(isRowDisabled?.(row));
						const value = row[col.key];
						const displayValue =
							params.formattedValue !== undefined
								? params.formattedValue
								: (col.valueFormatter?.(value, row) ?? value);
						const resolvedEditable =
							typeof col.editable === 'function' ? col.editable(row, col.key, value) : col.editable;

						if (col.render) {
							return col.render(row);
						}

						if (resolvedEditable && onCellChange) {
							const inputValue = toStringVal(value);
							const inputType = col.inputType ?? 'text';
							const handleEditableControlClick = event => {
								event.stopPropagation();
								if (disabledByRow) return;
								onRowClick?.(row);
							};
							const rowType =
								resolveCellOption(row, col, col.key, 'rowType', undefined) ??
								resolveCellOption(row, col, col.key, 'type', 'input');
							const comboItem =
								resolveCellOption(row, col, col.key, 'comboItem', undefined) ??
								resolveCellOption(row, col, col.key, 'comboItems', []);

							if (rowType === 'comboBox') {
								const selectedOption = comboItem.find(
									option =>
										String(resolveComboOptionValue(option, col.comboValueKey ?? 'value')) === String(value)
								);
								const selectedLabel =
									resolveComboOptionLabel(selectedOption, col.comboLabelKey ?? 'label') ?? value;
								const defaultComboTextColor = isNegativeComboOption(value, selectedLabel) ? '#f87171' : '#f8fafc';
								const comboTextColor = col.getComboTextColor?.(value, row) ?? defaultComboTextColor;
								const comboFontWeight =
									col.getComboFontWeight?.(value, row) ??
									(isNegativeComboOption(value, selectedLabel) ? 700 : 500);
								const comboLabelKey = col.comboLabelKey ?? 'label';
								const comboValueKey = col.comboValueKey ?? 'value';

								return (
									<CommonSelect
										value={inputValue}
										options={comboItem}
										optionLabelKey={comboLabelKey}
										optionValueKey={comboValueKey}
										renderOption={
											col.renderComboOption ??
											(option => {
												const optionValue = resolveComboOptionValue(option, comboValueKey);
												const optionLabel = resolveComboOptionLabel(option, comboLabelKey);
												return renderDefaultComboText(optionValue, optionLabel, false);
											})
										}
										SelectProps={{
											renderValue: selectedValue => {
												if (col.renderComboValue) {
													return col.renderComboValue(selectedValue, row, comboItem);
												}

												const selectedOption = comboItem.find(
													option =>
														String(resolveComboOptionValue(option, comboValueKey)) ===
														String(selectedValue)
												);
												const selectedLabel =
													resolveComboOptionLabel(selectedOption, comboLabelKey) ?? selectedValue;
												return renderDefaultComboText(selectedValue, selectedLabel, true);
											},
										}}
										disabled={disabledByRow}
										className="w-full"
										size="small"
										onClick={handleEditableControlClick}
										onChange={nextValue => onCellChange(row, col.key, nextValue)}
										sx={{
											'& .MuiOutlinedInput-root': {
												height: 32,
												borderRadius: '6px',
												color: comboTextColor,
												backgroundColor: 'rgba(15, 23, 42, 0.7)',
												'& fieldset': {
													borderColor: 'rgba(125, 211, 252, 0.22)',
												},
												'&:hover fieldset': {
													borderColor: 'rgba(125, 211, 252, 0.42)',
												},
												'&.Mui-focused fieldset': {
													borderColor: 'rgba(125, 211, 252, 0.66)',
												},
											},
											'& .MuiOutlinedInput-root.Mui-disabled': {
												color: `${comboTextColor} !important`,
												WebkitTextFillColor: `${comboTextColor} !important`,
											},
											'& .MuiSelect-select': {
												display: 'flex',
												alignItems: 'center',
												paddingTop: '6px',
												paddingBottom: '6px',
												fontSize: '12px',
												color: comboTextColor,
												WebkitTextFillColor: comboTextColor,
												fontWeight: comboFontWeight,
											},
											'& .MuiSelect-select span': {
												color: `${comboTextColor} !important`,
												WebkitTextFillColor: `${comboTextColor} !important`,
												fontWeight: `${comboFontWeight} !important`,
											},
											'& .MuiSelect-select.Mui-disabled': {
												color: `${comboTextColor} !important`,
												WebkitTextFillColor: `${comboTextColor} !important`,
											},
											'& .MuiOutlinedInput-root.Mui-disabled .MuiSelect-select': {
												color: `${comboTextColor} !important`,
												WebkitTextFillColor: `${comboTextColor} !important`,
											},
											'& .MuiOutlinedInput-root.Mui-disabled .MuiSelect-select span': {
												color: `${comboTextColor} !important`,
												WebkitTextFillColor: `${comboTextColor} !important`,
												fontWeight: `${comboFontWeight} !important`,
											},
											'& .MuiSvgIcon-root': {
												color: '#bae6fd',
											},
											'& .MuiSvgIcon-root.Mui-disabled': {
												color: '#bae6fd',
											},
										}}
									/>
								);
							}

							if (type === 'tree' && colIndex === 0) {
								const depthKey = treeOpt?.depthKey ?? 'depth';
								const hasChildrenKey = treeOpt?.hasChildrenKey ?? 'hasChildren';
								const indentSize = treeOpt?.indentSize ?? 18;
								const depth = getNumberVal(row[depthKey], 1);
								const hasChildren = getBoolVal(row[hasChildrenKey]);
								const expandedRowKeys = treeOpt?.expandedRowKeys;
								const isExpanded = expandedRowKeys ? expandedRowKeys.has(rowKey) : false;

								return (
									<div
										className="flex w-full items-center gap-2"
										style={{ paddingLeft: `${Math.max(0, depth - 1) * indentSize}px` }}
									>
										{hasChildren ? (
											<button
												type="button"
												className="w-[14px] text-[10px] text-sky-100/80"
												disabled={disabledByRow}
												onClick={event => {
													event.stopPropagation();
													if (disabledByRow) return;
													treeOpt?.onToggleExpand?.(rowKey);
												}}
											>
												{isExpanded ? '▼' : '▶'}
											</button>
										) : (
											<span className="w-[14px] text-center text-sky-100/50">•</span>
										)}
											<EditableCellInput
												cellKey={`${rowKey}:${col.key}`}
												inputType={inputType}
												value={inputValue}
												placeholder={col.placeholder}
												disabled={disabledByRow}
												className="h-8 w-full rounded border border-sky-200/20 bg-slate-900/70 px-2 text-sky-50 outline-none focus:border-sky-300/50"
											onClick={handleEditableControlClick}
											onChange={event => onCellChange(row, col.key, event.target.value)}
										/>
									</div>
								);
							}

								return (
									<EditableCellInput
										cellKey={`${rowKey}:${col.key}`}
										inputType={inputType}
									value={inputValue}
									placeholder={col.placeholder}
									disabled={disabledByRow}
									className="h-8 w-full rounded border border-sky-200/20 bg-slate-900/70 px-2 text-sky-50 outline-none focus:border-sky-300/50"
									onClick={handleEditableControlClick}
									onChange={event =>
										onCellChange(
											row,
											col.key,
											inputType === 'number'
												? toStringVal(toNumberOrRaw(event.target.value))
												: event.target.value
										)
									}
								/>
							);
						}

						return <span>{toStringVal(displayValue)}</span>;
					},
				};
			}),
		[
			colSeq,
			enableColumnResize,
			enableFiltering,
			enableSorting,
			groupedHeaderMeta,
			isDisabled,
			isRowDisabled,
			onCellChange,
			onRowClick,
			treeOpt,
			type,
		]
	);

	const gridTemplateColumns = useMemo(
		() =>
			columns
				.map(column => {
					if (column.width) return `${column.width}px`;
					if (column.flex) return `minmax(${column.minWidth ?? 110}px, ${column.flex}fr)`;
					return `minmax(${column.minWidth ?? 110}px, 1fr)`;
				})
				.join(' '),
		[columns]
	);

	const resolvedRowClassName = params => {
		const row = params.row;
		const rowKey = row.id;
		const isSel = resolvedSelectedRowKey === rowKey;
		const disabledByRow = isDisabled || Boolean(isRowDisabled?.(row));
		const customRowClassName = typeof rowClassName === 'function' ? rowClassName(row, rowKey, isSel) : rowClassName;

		return [isSel ? 'Mui-selected' : '', disabledByRow ? 'pointer-events-none opacity-55' : '', customRowClassName]
			.filter(Boolean)
			.join(' ');
	};

	useEffect(() => {
		if (resolvedSelectedRowKey == null) {
			lastScrolledRowKeyRef.current = null;
			return;
		}
		if (lastScrolledRowKeyRef.current === resolvedSelectedRowKey) return;

		const rowIndex = rows.findIndex(row => row.id === resolvedSelectedRowKey);
		if (rowIndex < 0) return;

		lastScrolledRowKeyRef.current = resolvedSelectedRowKey;
		apiRef.current?.scrollToIndexes?.({ rowIndex });
	}, [apiRef, resolvedSelectedRowKey, rows]);

	const handleSortModelChange = nextModel => {
		if (disableHeaderSortClick && blockNextHeaderSortRef.current) {
			blockNextHeaderSortRef.current = false;
			return;
		}

		if (sortModelProp == null) {
			setInnerSortModel(nextModel);
		}
		onSortModelChange?.(nextModel);
	};

	const handleFilterModelChange = nextModel => {
		if (filterModelProp == null) {
			setInnerFilterModel(nextModel);
		}
		onFilterModelChange?.(nextModel);
	};

	const handleColumnHeaderClick = (params, event) => {
		if (!disableHeaderSortClick || !params.colDef?.sortable) return;

		const interactiveHeaderButton = event.target?.closest?.(
			'.MuiDataGrid-menuIconButton, .MuiDataGrid-iconButtonContainer, .MuiDataGrid-sortButton'
		);
		if (interactiveHeaderButton) return;

		blockNextHeaderSortRef.current = true;
	};

	return (
		<div className="flex h-full min-h-0 flex-col">
			{caption ? <div className="py-2 text-left text-sm text-sky-100/70">{caption}</div> : null}
			{groupedHeaderMeta ? (
				<div
					className={['grid overflow-hidden border-b border-[#27425f] text-sm text-sky-50', headRowClassName]
						.filter(Boolean)
						.join(' ')}
					style={{ gridTemplateColumns }}
				>
					{groupedHeaderMeta.topCells.map(cell => (
						<div key={cell.key} className={cell.className} style={{ gridColumn: `span ${cell.span}` }}>
							{cell.label}
						</div>
					))}
				</div>
			) : null}
			<div className="min-h-0 flex-1">
				<DataGrid
					apiRef={apiRef}
					rows={rows}
					columns={columns}
					initialState={initialState}
					loading={loading}
					disableColumnSelector
					disableDensitySelector
					disableRowSelectionOnClick
					disableColumnSorting={!enableSorting}
					disableColumnFilter={!enableFiltering}
					hideFooter={hideFooter}
					pageSizeOptions={pageSizeOptions}
					paginationModel={paginationModel}
					onPaginationModelChange={onPaginationModelChange}
					rowHeight={autoRowHeight ? undefined : rowHeight}
					getRowHeight={autoRowHeight ? () => 'auto' : undefined}
					columnHeaderHeight={columnHeaderHeight}
					sortModel={controlledSortModel}
					filterModel={controlledFilterModel}
					onSortModelChange={handleSortModelChange}
					onFilterModelChange={handleFilterModelChange}
					onColumnHeaderClick={handleColumnHeaderClick}
					ignoreDiacritics={ignoreDiacritics}
					getRowClassName={resolvedRowClassName}
					rowSelectionModel={rowSelectionModel}
					onRowClick={params => {
						const row = params.row;
						if (isDisabled || isRowDisabled?.(row)) return;
						onRowClick?.(row);
					}}
					slots={{
						noRowsOverlay: () => <NoRowsOverlay message={emptyMsg} />,
						loadingOverlay: () => <LoadingOverlay message={loadingMsg} />,
					}}
					slotProps={{
						basePopper: {
							sx: {
								zIndex: 1600,
								'&.MuiDataGrid-panel, & .MuiDataGrid-paper, & .MuiPaper-root': {
									borderRadius: '12px',
									border: '1px solid rgba(110, 185, 255, 0.24)',
									background: 'linear-gradient(180deg, rgba(18,35,71,0.98), rgba(12,24,49,0.98))',
									boxShadow: '0 18px 42px rgba(2, 9, 34, 0.46)',
									color: '#e0f2fe',
									backdropFilter: 'blur(12px)',
								},
								'& .MuiDataGrid-panel': {
									maxWidth: 'calc(100vw - 32px)',
								},
								'& .MuiDataGrid-paper, & .MuiDataGrid-panelWrapper, & .MuiDataGrid-panelContent': {
									background: 'linear-gradient(180deg, rgba(18,35,71,0.98), rgba(12,24,49,0.98))',
									color: '#e0f2fe',
									maxWidth: 'calc(100vw - 32px)',
									overflowX: 'auto',
								},
								'& .MuiDataGrid-menuList': {
									padding: '6px',
								},
								'& .MuiMenuItem-root, & .MuiDataGrid-menuList .MuiButtonBase-root': {
									minHeight: '34px',
									borderRadius: '8px',
									padding: '8px 10px',
									fontSize: '13px',
									color: '#e0f2fe',
								},
								'& .MuiMenuItem-root:hover, & .MuiDataGrid-menuList .MuiButtonBase-root:hover': {
									backgroundColor: 'rgba(110, 185, 255, 0.14)',
								},
								'& .MuiMenuItem-root.Mui-focusVisible, & .MuiDataGrid-menuList .MuiButtonBase-root.Mui-focusVisible':
									{
										backgroundColor: 'rgba(110, 185, 255, 0.18)',
									},
								'& .MuiDivider-root': {
									margin: '6px 0',
									borderColor: 'rgba(110, 185, 255, 0.16)',
								},
								'& .MuiListItemIcon-root, & .MuiSvgIcon-root': {
									minWidth: '30px',
									color: '#8fd4ff',
								},
								'& .MuiDataGrid-filterForm': {
									display: 'grid',
									gridTemplateColumns: '32px 150px 150px minmax(220px, 1fr)',
									gap: '12px',
									width: '680px',
									maxWidth: 'calc(100vw - 56px)',
									padding: '16px',
									alignItems: 'start',
								},
								'& .MuiDataGrid-filterFormDeleteIcon': {
									display: 'flex',
									alignItems: 'center',
									justifyContent: 'center',
									margin: 0,
									paddingTop: '2px',
									width: '32px',
								},
								'& .MuiDataGrid-filterForm > .MuiFormControl-root:has(.MuiDataGrid-filterFormLogicOperatorInput)':
									{
										display: 'none',
									},
								'& .MuiDataGrid-filterForm > .MuiFormControl-root:has(.MuiDataGrid-filterFormColumnInput)': {
									gridColumn: '2',
									margin: 0,
									minWidth: 0,
									width: '100%',
								},
								'& .MuiDataGrid-filterForm > .MuiFormControl-root:has(.MuiDataGrid-filterFormOperatorInput)': {
									gridColumn: '3',
									margin: 0,
									minWidth: 0,
									width: '100%',
								},
								'& .MuiDataGrid-filterFormValueInput': {
									gridColumn: '4',
									margin: 0,
									minWidth: 0,
									width: '100%',
								},
								'& .MuiDataGrid-filterFormColumnInput, & .MuiDataGrid-filterFormOperatorInput': {
									width: '100%',
								},
								'& .MuiDataGrid-filterForm .MuiFormControl-root': {
									minWidth: 0,
									width: '100%',
								},
								'& .MuiDataGrid-filterForm .MuiInputBase-root, & .MuiDataGrid-filterForm .MuiOutlinedInput-root':
									{
										height: '38px',
										minHeight: '38px',
									},
								'& .MuiDataGrid-filterForm .MuiInputBase-input, & .MuiDataGrid-filterForm .MuiSelect-select': {
									boxSizing: 'border-box',
									display: 'flex',
									alignItems: 'center',
									height: '38px',
									minHeight: '38px',
									paddingTop: '8px',
									paddingBottom: '8px',
								},
								'& .MuiInputLabel-root, & .MuiFormLabel-root, & .MuiFormControl-root .MuiInputLabel-root': {
									color: 'rgba(224, 242, 254, 0.78)',
								},
								'& .MuiInputLabel-root.Mui-focused, & .MuiFormLabel-root.Mui-focused, & .MuiFormControl-root .MuiInputLabel-root.Mui-focused':
									{
										color: '#d9f2ff',
									},
								'& .MuiInputBase-root, & .MuiOutlinedInput-root': {
									borderRadius: '10px',
									color: '#f8fafc',
									backgroundColor: 'rgba(255,255,255,0.04)',
									'& fieldset': {
										borderColor: 'rgba(110, 185, 255, 0.22)',
									},
									'&:hover fieldset': {
										borderColor: 'rgba(110, 185, 255, 0.4)',
									},
									'&.Mui-focused fieldset': {
										borderColor: 'rgba(110, 185, 255, 0.62)',
									},
								},
								'& .MuiInputBase-input::placeholder': {
									color: 'rgba(224, 242, 254, 0.34)',
									opacity: 1,
								},
								'& .MuiInputBase-input, & .MuiSelect-select': {
									color: '#f8fafc',
								},
								'& .MuiSelect-icon': {
									color: '#8fd4ff',
								},
								'& .MuiDataGrid-filterFormDeleteIcon button': {
									color: '#8fd4ff',
								},
								'& .MuiDataGrid-filterFormDeleteIcon button:hover': {
									backgroundColor: 'rgba(110, 185, 255, 0.12)',
								},
								'@media (max-width: 560px)': {
									'& .MuiDataGrid-filterForm': {
										gridTemplateColumns: '32px minmax(0, 1fr)',
										width: 'calc(100vw - 56px)',
									},
									'& .MuiDataGrid-filterFormColumnInput, & .MuiDataGrid-filterFormOperatorInput, & .MuiDataGrid-filterFormValueInput':
										{
											gridColumn: '2',
										},
								},
							},
						},
					}}
					sx={[
						{
							border: 0,
							color: '#e0f2fe',
							fontSize: '0.875rem',
							backgroundColor: 'transparent',
							'& .MuiDataGrid-main': {
								border: 0,
							},
							'& .MuiDataGrid-columnHeaders': {
								borderBottom: groupedHeaderMeta ? '1px solid #27425f' : '1px solid rgba(110, 185, 255, 0.24)',
								backgroundColor: '#163667',
							},
							'& .MuiDataGrid-columnHeader': {
								outline: 'none',
								borderRight: '1px solid rgba(39, 66, 95, 0.92)',
								backgroundColor: groupedHeaderMeta ? '#1a417c' : 'rgba(15, 41, 82, 0.85)',
							},
							'& .MuiDataGrid-columnHeader, & .MuiDataGrid-columnHeaderTitle, & .MuiDataGrid-iconButtonContainer, & .MuiDataGrid-menuIconButton, & .MuiDataGrid-sortIcon, & .MuiDataGrid-menuIcon svg':
								{
									color: '#ffffff',
								},
							'& .MuiDataGrid-columnHeaderTitleContainer': {
								justifyContent: 'center',
								padding: 0,
							},
							'& .MuiDataGrid-iconButtonContainer': {
								visibility: 'visible',
								width: 'auto',
							},
							'& .MuiDataGrid-menuIcon': {
								visibility: 'visible',
								width: 'auto',
								marginLeft: '2px',
							},
							'& .MuiDataGrid-menuIconButton': {
								opacity: 1,
								backgroundColor: 'transparent',
							},
							'& .MuiDataGrid-columnSeparator': {
								visibility: enableColumnResize ? 'visible' : 'hidden',
								color: 'rgba(159, 210, 255, 0.46)',
							},
							'& .MuiDataGrid-columnSeparator:hover': {
								color: 'rgba(199, 232, 255, 0.84)',
							},
							'& .MuiDataGrid-columnHeader .MuiIconButton-root, & .MuiDataGrid-columnHeader .MuiButtonBase-root': {
								color: '#ffffff',
								backgroundColor: 'transparent',
							},
							'& .MuiDataGrid-columnHeader .MuiIconButton-root:hover, & .MuiDataGrid-columnHeader .MuiButtonBase-root:hover, & .MuiDataGrid-columnHeader .MuiIconButton-root.Mui-focusVisible, & .MuiDataGrid-columnHeader .MuiButtonBase-root.Mui-focusVisible':
								{
									backgroundColor: 'rgba(110, 185, 255, 0.12)',
								},
							'& .MuiDataGrid-columnHeader .MuiTouchRipple-root': {
								display: 'none',
							},
							'& .MuiDataGrid-columnHeaderTitle': {
								fontWeight: 600,
								whiteSpace: 'normal',
								lineHeight: 1.2,
							},
							'& .MuiDataGrid-cell': {
								display: 'flex',
								alignItems: 'center',
								borderTop: '1px solid rgba(39, 66, 95, 0.72)',
								borderRight: '1px solid rgba(32, 52, 77, 0.92)',
								outline: 'none',
							},
							'& .MuiDataGrid-cellContent': {
								overflow: 'hidden',
								textOverflow: 'ellipsis',
							},
							'& .MuiDataGrid-topContainer, & .MuiDataGrid-columnHeaders .MuiDataGrid-filler, & .MuiDataGrid-columnHeaders .MuiDataGrid-scrollbarFiller, & .MuiDataGrid-columnHeader--emptyGroup':
								{
									backgroundColor: 'rgba(15, 41, 82, 0.85)',
								},
							'& .MuiDataGrid-filler, & .MuiDataGrid-contentFiller, & .MuiDataGrid-scrollbarFiller, & .MuiDataGrid-filler--borderBottom, & .MuiDataGrid-filler--horizontal':
								{
									backgroundColor: 'rgba(15, 41, 82, 0.85)',
									borderColor: 'rgba(39, 66, 95, 0.92)',
								},
							...(autoRowHeight
								? {
										'& .MuiDataGrid-cell': {
											alignItems: 'flex-start',
											paddingTop: '8px',
											paddingBottom: '8px',
										},
										'& .MuiDataGrid-cellContent': {
											whiteSpace: 'normal',
											lineHeight: 1.45,
											textOverflow: 'clip',
										},
									}
								: {}),
							'& .MuiDataGrid-row': {
								backgroundColor: 'transparent',
							},
							'& .MuiDataGrid-row:hover': {
								backgroundColor: 'rgba(14, 165, 233, 0.09)',
							},
							'& .MuiDataGrid-row.Mui-selected': {
								backgroundColor: 'rgba(8, 47, 91, 0.42)',
								boxShadow: 'inset 0 0 0 1px rgba(56, 189, 248, 0.96)',
								'& .MuiDataGrid-cell': {
									backgroundColor: 'rgba(8, 47, 91, 0.28)',
									color: '#f8fafc',
									borderTopColor: 'transparent',
									borderBottomColor: 'transparent',
									borderRightColor: 'rgba(32, 52, 77, 0.92)',
								},
								'& .MuiDataGrid-cell:first-of-type': {
									borderLeftColor: 'transparent',
								},
								'& .MuiDataGrid-cell:last-of-type': {
									borderRightColor: 'transparent',
								},
							},
							'& .MuiDataGrid-row.Mui-selected:hover': {
								backgroundColor: 'rgba(8, 47, 91, 0.48)',
								boxShadow: 'inset 0 0 0 1px rgba(56, 189, 248, 0.96)',
							},
							'& .MuiDataGrid-virtualScroller': {
								overflowX: 'auto',
							},
							'& .MuiDataGrid-footerContainer': {
								display: 'none',
							},
							'& .MuiDataGrid-overlayWrapper': {
								minHeight: '120px',
							},
							...(stickyHeader
								? {
										'& .MuiDataGrid-columnHeaders': {
											position: 'sticky',
											top: 0,
											zIndex: 2,
										},
									}
								: {}),
						},
						...(Array.isArray(sx) ? sx : sx ? [sx] : []),
					]}
					data-testid={dataTestId}
					aria-label={ariaLabel}
				/>
			</div>
		</div>
	);
}

export default CommonTable;
