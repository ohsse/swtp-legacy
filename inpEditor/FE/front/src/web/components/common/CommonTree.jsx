import { Box } from '@mui/material';
import { RichTreeView } from '@mui/x-tree-view/RichTreeView';

function toArray(value) {
	if (Array.isArray(value)) {
		return value;
	}

	if (!value) {
		return [];
	}

	return [value];
}

function normalizeTreeNode(node, index = 0, parentPath = 'node') {
	if (!node) {
		return null;
	}

	const rawId = node.id ?? node.key ?? node.value ?? `${parentPath}-${index}`;
	const children = toArray(node.children)
		.map((childNode, childIndex) => normalizeTreeNode(childNode, childIndex, String(rawId)))
		.filter(Boolean);

	return {
		id: String(rawId),
		value: node.value ?? rawId,
		label: node.label ?? node.name ?? node.title ?? String(rawId),
		children,
		disabled: Boolean(node.disabled),
	};
}

function normalizeTreeItems(items) {
	return toArray(items)
		.map((item, index) => normalizeTreeNode(item, index))
		.filter(Boolean);
}

function CommonTree({ items = [], type = 'default', className = '', options = {}, ...props }) {
	const {
		editable = false,
		itemChildrenIndentation = 18,
		itemChildrenIndentaion,
		selectedItems,
		defaultSelectedItems,
		defaultExpandedItems,
		onChange,
		onSelectedItemsChange,
		onItemSelectionToggle,
		onItemLabelChange,
		multiSelect,
		checkboxSelection,
		selectedColor = '#4fd1ff',
		selectedBgColor = 'rgba(79, 209, 255, 0.14)',
		radius = 4,
		outline = false,
		outlineColor = 'rgba(122, 138, 172, 0.55)',
		...treeOptions
	} = options;
	const normalizedItems = normalizeTreeItems(items);
	const itemValueById = new Map();
	const collectItemValues = treeItems => {
		treeItems.forEach(item => {
			itemValueById.set(item.id, item.value);
			collectItemValues(item.children ?? []);
		});
	};
	collectItemValues(normalizedItems);
	const useCheckboxSelection = checkboxSelection ?? type === 'checkbox';
	const useMultiSelect = multiSelect ?? useCheckboxSelection ?? type === 'multi';
	const resolvedIndentation = itemChildrenIndentaion ?? itemChildrenIndentation;
	const handleSelectedItemsChange = (event, itemIds) => {
		const selectedItemIds = toArray(itemIds);
		const selectedValues = selectedItemIds.map(itemId => itemValueById.get(itemId) ?? itemId);
		onSelectedItemsChange?.(event, itemIds, selectedValues);
	};
	const handleItemSelectionToggle = (event, itemId, isSelected) => {
		const value = itemValueById.get(itemId) ?? itemId;
		onItemSelectionToggle?.(event, itemId, isSelected, value);
		onChange?.(value, isSelected, itemId, event);
	};

	return (
		<Box
			className={className}
			sx={{
				border: '1px solid rgba(110, 185, 255, 0.18)',
				background: 'linear-gradient(180deg, rgba(13, 28, 54, 0.88), rgba(10, 22, 44, 0.94))',
				padding: '6px 8px',
				overflow: 'auto',
				'& .MuiTreeItem-content': {
					position: 'relative',
					minHeight: '28px',
					paddingY: '1px',
					paddingX: '4px',
					borderRadius: `${radius}px`,
				},
				'& .MuiTreeItem-content:hover': {
					backgroundColor: 'rgba(110, 185, 255, 0.08)',
				},
				'& .MuiTreeItem-content.Mui-selected': {
					backgroundColor: selectedBgColor,
				},
				'& .MuiTreeItem-label': {
					fontSize: '14px',
					color: '#d7e7ff',
					lineHeight: 1.2,
				},
				'& .MuiTreeItem-content.Mui-selected .MuiTreeItem-label': {
					color: selectedColor,
				},
				'& .MuiCheckbox-root': {
					padding: '2px',
					color: 'rgba(143, 216, 255, 0.9)',
				},
				'& .MuiCheckbox-root.Mui-checked': {
					color: '#55b8ff',
				},
				'& .MuiSvgIcon-root': {
					fontSize: '18px',
					color: 'rgba(198, 225, 255, 0.92)',
				},
				'& .MuiTreeItem-groupTransition': outline
					? {
							marginLeft: '10px',
							paddingLeft: '14px',
							borderLeft: `1px solid ${outlineColor}`,
						}
					: {},
				'& .MuiTreeItem-groupTransition .MuiTreeItem-content::before': outline
					? {
							content: '""',
							position: 'absolute',
							left: '-14px',
							top: '50%',
							width: '10px',
							borderTop: `1px solid ${outlineColor}`,
							transform: 'translateY(-50%)',
						}
					: {},
			}}
		>
			<RichTreeView
				items={normalizedItems}
				checkboxSelection={useCheckboxSelection}
				multiSelect={useMultiSelect}
				defaultExpandedItems={defaultExpandedItems}
				selectedItems={selectedItems}
				defaultSelectedItems={defaultSelectedItems}
				onSelectedItemsChange={handleSelectedItemsChange}
				onItemSelectionToggle={handleItemSelectionToggle}
				isItemEditable={editable}
				onItemLabelChange={onItemLabelChange}
				itemChildrenIndentation={resolvedIndentation}
				expansionTrigger="iconContainer"
				{...treeOptions}
				{...props}
			/>
		</Box>
	);
}

export { CommonTree, normalizeTreeItems };
export default CommonTree;
