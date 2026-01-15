/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";

export class PosPerfumeOrderLineController extends ListController {
    setup() {
        super.setup();
        
        // Enable mouse click on all cells
        this.cellClickHandler = this._onCellClick.bind(this);
        
        // Enable mouse click on dropdown items
        this.dropdownItemClickHandler = this._onDropdownItemClick.bind(this);
    }
    
    /**
     * Handle cell click - make table cells clickable like Excel
     */
    _onCellClick(ev) {
        const cell = ev.target.closest('.o_data_cell');
        if (!cell || cell.classList.contains('o_list_record_remove')) {
            return;
        }
        
        // Get the field name from the cell
        const fieldName = cell.getAttribute('name');
        if (!fieldName) {
            return;
        }
        
        // Focus the input/select in the cell
        const input = cell.querySelector('input, select, textarea');
        if (input) {
            input.focus();
            
            // For select fields, open dropdown automatically
            if (input.tagName === 'SELECT') {
                input.click();
            }
            
            // For many2one fields, trigger autocomplete
            if (cell.querySelector('.o_field_many2one input')) {
                const many2oneInput = cell.querySelector('.o_field_many2one input');
                many2oneInput.focus();
                // Trigger dropdown by simulating click
                const dropdown = cell.querySelector('.o_field_many2one .dropdown-toggle');
                if (dropdown) {
                    dropdown.click();
                }
            }
        }
    }
    
    /**
     * Handle dropdown item click - ensure selection works
     */
    _onDropdownItemClick(ev) {
        const dropdownItem = ev.target.closest('.dropdown-item, .o-autocomplete--dropdown-item');
        if (!dropdownItem) {
            return;
        }
        
        // Let the click propagate normally to select the item
        // This ensures Odoo's default behavior works
        
        // After selection, focus back on the cell for keyboard navigation
        setTimeout(() => {
            const cell = ev.target.closest('.o_data_cell');
            if (cell) {
                const input = cell.querySelector('input, select, textarea');
                if (input) {
                    input.focus();
                }
            }
        }, 100);
    }
    
    /**
     * Enhanced keyboard navigation
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
        
        // Arrow key navigation - NO auto-dropdown
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(ev.key)) {
            ev.preventDefault();
            
            const cells = Array.from(row.querySelectorAll('.o_data_cell:not(.o_list_record_remove)'));
            const currentIndex = cells.indexOf(currentCell);
            
            let targetCell = null;
            
            if (ev.key === 'ArrowRight' && currentIndex < cells.length - 1) {
                targetCell = cells[currentIndex + 1];
            } else if (ev.key === 'ArrowLeft' && currentIndex > 0) {
                targetCell = cells[currentIndex - 1];
            } else if (ev.key === 'ArrowUp') {
                const prevRow = row.previousElementSibling;
                if (prevRow && prevRow.classList.contains('o_data_row')) {
                    const prevCells = Array.from(prevRow.querySelectorAll('.o_data_cell'));
                    targetCell = prevCells[currentIndex];
                }
            } else if (ev.key === 'ArrowDown') {
                const nextRow = row.nextElementSibling;
                if (nextRow && nextRow.classList.contains('o_data_row')) {
                    const nextCells = Array.from(nextRow.querySelectorAll('.o_data_cell'));
                    targetCell = nextCells[currentIndex];
                }
            }
            
            if (targetCell) {
                // Just focus the input - NO auto-dropdown
                const input = targetCell.querySelector('input, select, textarea');
                if (input) {
                    input.focus();
                    // Select text in input for easy editing
                    if (input.tagName === 'INPUT' && input.type === 'text') {
                        input.select();
                    }
                }
            }
            
            return;
        }
        
        // Arrow Up/Down in dropdown - navigate items
        if ((ev.key === 'ArrowUp' || ev.key === 'ArrowDown') && 
            (currentCell.querySelector('.dropdown-menu.show') || 
             currentCell.querySelector('.o-autocomplete--dropdown-menu.show'))) {
            // Let the dropdown handle navigation
            return super.onKeydown(ev);
        }
        
        // Enter key - Open dropdown OR select item OR move to next row
        if (ev.key === 'Enter') {
            const input = currentCell.querySelector('input, select, textarea');
            
            // Check if this is a many2one or selection field
            const isMany2one = currentCell.querySelector('.o_field_many2one');
            const isSelection = input && input.tagName === 'SELECT';
            
            if (isMany2one) {
                // Check if dropdown is already open
                const dropdownMenu = currentCell.querySelector('.o_input_dropdown .dropdown-menu, .o-autocomplete--dropdown-menu');
                const isDropdownOpen = dropdownMenu && dropdownMenu.classList.contains('show');
                
                if (isDropdownOpen) {
                    // Dropdown is open - select the highlighted item
                    const highlightedItem = dropdownMenu.querySelector('.dropdown-item.active, .dropdown-item:focus, .o-autocomplete--dropdown-item.ui-menu-item-wrapper.ui-state-active');
                    if (highlightedItem) {
                        ev.preventDefault();
                        highlightedItem.click();
                        return;
                    }
                } else {
                    // Dropdown is closed - open it
                    ev.preventDefault();
                    const dropdown = currentCell.querySelector('.o_input_dropdown, .dropdown-toggle');
                    if (dropdown) {
                        dropdown.click();
                    }
                    return;
                }
            } else if (isSelection) {
                // For select fields
                const isOpen = input.size > 1;
                
                if (isOpen) {
                    // Select is open - accept selection and move on
                    input.size = 1;
                    // Move to next row
                    ev.preventDefault();
                } else {
                    // Select is closed - open it
                    ev.preventDefault();
                    input.click();
                    input.size = Math.min(input.options.length, 10);
                    
                    // Close on blur
                    input.addEventListener('blur', () => {
                        input.size = 1;
                    }, { once: true });
                    
                    return;
                }
            }
            
            // For other fields OR after selection, move to next row (same column)
            const cells = Array.from(row.querySelectorAll('.o_data_cell:not(.o_list_record_remove)'));
            const currentIndex = cells.indexOf(currentCell);
            
            const nextRow = row.nextElementSibling;
            if (nextRow && nextRow.classList.contains('o_data_row')) {
                const nextCells = Array.from(nextRow.querySelectorAll('.o_data_cell'));
                const targetCell = nextCells[currentIndex];
                
                if (targetCell) {
                    const nextInput = targetCell.querySelector('input, select, textarea');
                    if (nextInput) {
                        nextInput.focus();
                        if (nextInput.tagName === 'INPUT' && nextInput.type === 'text') {
                            nextInput.select();
                        }
                    }
                }
            }
            
            return;
        }
        
        return super.onKeydown(ev);
    }
}

export const posPerfumeOrderLineListView = {
    ...listView,
    Controller: PosPerfumeOrderLineController,
};

registry.category("views").add("pos_perfume_order_line_list", posPerfumeOrderLineListView);

