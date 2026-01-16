/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { onMounted } from "@odoo/owl";

export class PosPerfumeOrderLineController extends ListController {
    setup() {
        super.setup();
        
        onMounted(() => {
            this._setupEventListeners();
        });
    }
    
    /**
     * Setup event listeners for mouse clicks
     */
    _setupEventListeners() {
        const tbody = this.root.el?.querySelector('.o_list_table tbody');
        if (!tbody) return;
        
        // Cell click handler - enable mouse click on cells
        tbody.addEventListener('click', this._onCellClick.bind(this));
        
        // Dropdown item click handler - enable mouse selection from dropdowns
        tbody.addEventListener('click', this._onDropdownItemClick.bind(this), true);
    }
    
    /**
     * Handle cell click - Focus input without opening dropdown
     */
    _onCellClick(ev) {
        const cell = ev.target.closest('.o_data_cell');
        if (!cell || cell.classList.contains('o_list_record_remove')) {
            return;
        }
        
        // Don't trigger if clicking on a dropdown item
        if (ev.target.closest('.dropdown-item, .o-autocomplete--dropdown-item')) {
            return;
        }
        
        // Try to find any input in the cell (including readonly fields)
        let input = cell.querySelector('input:not([type="checkbox"]):not([type="radio"])');
        
        // Check for monetary/float/integer widgets
        if (!input) {
            input = cell.querySelector('.o_field_monetary input, .o_field_float input, .o_field_integer input, .o_field_percentage input');
        }
        
        // Check for many2one
        if (!input) {
            input = cell.querySelector('.o_field_many2one input');
        }
        
        // Check for textarea
        if (!input) {
            input = cell.querySelector('textarea');
        }
        
        if (input) {
            input.focus();
            if ((input.type === 'text' || input.type === 'number') && !input.readOnly) {
                input.select();
            }
        } else {
            // For readonly cells without input, make cell focusable
            if (cell.tabIndex === -1) {
                cell.tabIndex = 0;
            }
            cell.focus();
        }
    }
    
    /**
     * Handle dropdown item click - Ensure mouse selection works
     */
    _onDropdownItemClick(ev) {
        const dropdownItem = ev.target.closest('.dropdown-item, .o-autocomplete--dropdown-item, .ui-menu-item');
        if (!dropdownItem) {
            return;
        }
        
        // Let the click propagate to select the item
        // After selection, move focus for continued keyboard navigation
        setTimeout(() => {
            const activeCell = document.activeElement?.closest('.o_data_cell');
            if (activeCell) {
                const row = activeCell.closest('.o_data_row');
                if (row) {
                    const cells = Array.from(row.querySelectorAll('.o_data_cell:not(.o_list_record_remove)'));
                    const currentIndex = cells.indexOf(activeCell);
                    
                    // Move to next cell or next row
                    if (currentIndex < cells.length - 1) {
                        const nextCell = cells[currentIndex + 1];
                        const nextInput = nextCell.querySelector('input, textarea');
                        if (nextInput) {
                            nextInput.focus();
                            if (nextInput.type === 'text' || nextInput.type === 'number') {
                                nextInput.select();
                            }
                        }
                    }
                }
            }
        }, 150);
    }
    
    /**
     * Enhanced keyboard navigation - Complete rewrite
     */
    onKeydown(ev) {
        const currentCell = ev.target.closest('.o_data_cell');
        if (!currentCell) {
            return super.onKeydown(ev);
        }
        
        const row = currentCell.closest('.o_data_row');
        if (!row) {
            return super.onKeydown(ev);
        }
        
        // Get ALL visible cells (excluding hidden columns)
        const allCells = Array.from(row.querySelectorAll('.o_data_cell:not(.o_list_record_remove):not(.o_list_button)'));
        const cells = allCells.filter(cell => {
            // Exclude hidden cells (display: none or column_invisible)
            const isVisible = cell.offsetParent !== null;
            return isVisible;
        });
        const currentIndex = cells.indexOf(currentCell);
        
        // Check if a dropdown is currently open
        const isDropdownOpen = currentCell.querySelector('.dropdown-menu.show, .o-autocomplete--dropdown-menu.show, .ui-autocomplete.ui-menu[style*="display: block"]');
        
        // Arrow Up/Down inside open dropdown - Let dropdown handle it
        if (isDropdownOpen && (ev.key === 'ArrowUp' || ev.key === 'ArrowDown')) {
            return; // Let Odoo handle dropdown navigation
        }
        
        // Arrow key navigation - Move between ALL cells (including readonly)
        if (ev.key === 'ArrowRight') {
            ev.preventDefault();
            ev.stopPropagation();
            
            if (currentIndex < cells.length - 1) {
                const targetCell = cells[currentIndex + 1];
                this._focusCell(targetCell);
            }
            return;
        }
        
        if (ev.key === 'ArrowLeft') {
            ev.preventDefault();
            ev.stopPropagation();
            
            if (currentIndex > 0) {
                const targetCell = cells[currentIndex - 1];
                this._focusCell(targetCell);
            }
            return;
        }
        
        if (ev.key === 'ArrowUp') {
            ev.preventDefault();
            ev.stopPropagation();
            
            const prevRow = row.previousElementSibling;
            if (prevRow && prevRow.classList.contains('o_data_row')) {
                const allPrevCells = Array.from(prevRow.querySelectorAll('.o_data_cell:not(.o_list_record_remove):not(.o_list_button)'));
                const prevCells = allPrevCells.filter(cell => cell.offsetParent !== null);
                const targetCell = prevCells[currentIndex];
                if (targetCell) {
                    this._focusCell(targetCell);
                }
            }
            return;
        }
        
        if (ev.key === 'ArrowDown') {
            ev.preventDefault();
            ev.stopPropagation();
            
            const nextRow = row.nextElementSibling;
            if (nextRow && nextRow.classList.contains('o_data_row')) {
                const allNextCells = Array.from(nextRow.querySelectorAll('.o_data_cell:not(.o_list_record_remove):not(.o_list_button)'));
                const nextCells = allNextCells.filter(cell => cell.offsetParent !== null);
                const targetCell = nextCells[currentIndex];
                if (targetCell) {
                    this._focusCell(targetCell);
                }
            }
            return;
        }
        
        // Enter key - Open dropdown OR select item OR move to next row
        if (ev.key === 'Enter') {
            const input = currentCell.querySelector('input, textarea');
            const isMany2one = currentCell.querySelector('.o_field_many2one');
            const isSelection = input && input.tagName === 'SELECT';
            
            if (isMany2one) {
                if (isDropdownOpen) {
                    // Dropdown is open - let Enter select the highlighted item
                    return; // Let Odoo handle selection
                } else {
                    // Dropdown is closed - open it
                    ev.preventDefault();
                    ev.stopPropagation();
                    
                    const many2oneInput = currentCell.querySelector('.o_field_many2one input');
                    if (many2oneInput) {
                        many2oneInput.focus();
                        // Trigger dropdown
                        const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
                        many2oneInput.dispatchEvent(clickEvent);
                    }
                    return;
                }
            } else if (isSelection) {
                // For select fields - open/close
                const isOpen = input.size > 1;
                
                if (isOpen) {
                    input.size = 1;
                } else {
                    ev.preventDefault();
                    input.click();
                    input.size = Math.min(input.options.length, 10);
                    input.addEventListener('blur', () => { input.size = 1; }, { once: true });
                    return;
                }
            }
            
            // For other fields OR after selection, move to next row (same column)
            ev.preventDefault();
            const nextRow = row.nextElementSibling;
            if (nextRow && nextRow.classList.contains('o_data_row')) {
                const allNextCells = Array.from(nextRow.querySelectorAll('.o_data_cell:not(.o_list_record_remove):not(.o_list_button)'));
                const nextCells = allNextCells.filter(cell => cell.offsetParent !== null);
                const targetCell = nextCells[currentIndex];
                if (targetCell) {
                    this._focusCell(targetCell);
                }
            }
            return;
        }
        
        // Tab key - Move to next cell (including readonly)
        if (ev.key === 'Tab' && !ev.shiftKey) {
            ev.preventDefault();
            
            if (currentIndex < cells.length - 1) {
                const targetCell = cells[currentIndex + 1];
                this._focusCell(targetCell);
            } else {
                // Move to first cell of next row
                const nextRow = row.nextElementSibling;
                if (nextRow && nextRow.classList.contains('o_data_row')) {
                    const allNextCells = Array.from(nextRow.querySelectorAll('.o_data_cell:not(.o_list_record_remove):not(.o_list_button)'));
                    const nextCells = allNextCells.filter(cell => cell.offsetParent !== null);
                    if (nextCells[0]) {
                        this._focusCell(nextCells[0]);
                    }
                }
            }
            return;
        }
        
        // Shift+Tab - Move to previous cell (including readonly)
        if (ev.key === 'Tab' && ev.shiftKey) {
            ev.preventDefault();
            
            if (currentIndex > 0) {
                const targetCell = cells[currentIndex - 1];
                this._focusCell(targetCell);
            } else {
                // Move to last cell of previous row
                const prevRow = row.previousElementSibling;
                if (prevRow && prevRow.classList.contains('o_data_row')) {
                    const allPrevCells = Array.from(prevRow.querySelectorAll('.o_data_cell:not(.o_list_record_remove):not(.o_list_button)'));
                    const prevCells = allPrevCells.filter(cell => cell.offsetParent !== null);
                    if (prevCells.length > 0) {
                        this._focusCell(prevCells[prevCells.length - 1]);
                    }
                }
            }
            return;
        }
        
        return super.onKeydown(ev);
    }
    
    /**
     * Helper: Focus a cell's input
     */
    _focusCell(cell) {
        // Try to find ANY input, including readonly cells and monetary/float widgets
        let input = cell.querySelector('input:not([type="checkbox"]):not([type="radio"])');
        
        // If no direct input, check for monetary/float/integer field inputs
        if (!input) {
            input = cell.querySelector('.o_field_monetary input, .o_field_float input, .o_field_integer input');
        }
        
        // If still no input, check for many2one
        if (!input) {
            input = cell.querySelector('.o_field_many2one input');
        }
        
        // If still no input, try textarea
        if (!input) {
            input = cell.querySelector('textarea');
        }
        
        // If still no input (readonly cell), try to make the cell focusable
        if (!input) {
            // For readonly cells, we can at least focus the cell itself
            if (cell.tabIndex === -1) {
                cell.tabIndex = 0;
            }
            cell.focus();
            return;
        }
        
        // Focus the input
        input.focus();
        
        // Select text if it's a text/number input
        if ((input.type === 'text' || input.type === 'number') && !input.readOnly) {
            input.select();
        }
    }
}

export const posPerfumeOrderLineListView = {
    ...listView,
    Controller: PosPerfumeOrderLineController,
};

registry.category("views").add("pos_perfume_order_line_list", posPerfumeOrderLineListView);

