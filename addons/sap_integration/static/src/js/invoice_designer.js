/** @odoo-module **/

import { Component, useState, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * Invoice Visual Designer
 * Canvas-based drag & drop designer for invoice templates
 */
class InvoiceDesigner extends Component {
    static template = "sap_integration.InvoiceDesigner";
    
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        
        this.canvasRef = useRef("canvas");
        
        this.state = useState({
            template: null,
            selectedElement: null,
            elements: [],
            scale: 1.0,
            showGrid: true,
            snapToGrid: true,
            gridSize: 5,
            mode: 'select', // select, text, field, image, shape, table
        });
        
        onMounted(() => {
            this.loadTemplate();
            this.initCanvas();
        });
    }
    
    async loadTemplate() {
        const templateId = this.props.action.params.template_id;
        if (!templateId) return;
        
        const [template] = await this.orm.read(
            "invoice.template.designer",
            [templateId],
            ["name", "canvas_width", "canvas_height", "background_color", 
             "background_image", "show_grid", "grid_size", "snap_to_grid"]
        );
        
        this.state.template = template;
        this.state.showGrid = template.show_grid;
        this.state.gridSize = template.grid_size;
        this.state.snapToGrid = template.snap_to_grid;
        
        // Load elements
        const elements = await this.orm.searchRead(
            "invoice.template.element",
            [["template_id", "=", templateId]],
            ["element_type", "x", "y", "width", "height", "static_text", 
             "field_name", "font_size", "color", "sequence"]
        );
        
        this.state.elements = elements;
        this.renderCanvas();
    }
    
    initCanvas() {
        const canvas = this.canvasRef.el;
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Set canvas size (A4 @ 96 DPI = 794 x 1123 px)
        canvas.width = 794;
        canvas.height = 1123;
        
        // Mouse events
        canvas.addEventListener('mousedown', this.onCanvasMouseDown.bind(this));
        canvas.addEventListener('mousemove', this.onCanvasMouseMove.bind(this));
        canvas.addEventListener('mouseup', this.onCanvasMouseUp.bind(this));
        
        this.ctx = ctx;
    }
    
    renderCanvas() {
        if (!this.ctx) return;
        
        const ctx = this.ctx;
        const canvas = this.canvasRef.el;
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Background
        ctx.fillStyle = this.state.template?.background_color || '#FFFFFF';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Grid
        if (this.state.showGrid) {
            this.drawGrid();
        }
        
        // Elements
        for (const element of this.state.elements) {
            this.drawElement(element);
        }
        
        // Selection box
        if (this.state.selectedElement) {
            this.drawSelectionBox(this.state.selectedElement);
        }
    }
    
    drawGrid() {
        const ctx = this.ctx;
        const canvas = this.canvasRef.el;
        const gridSize = this.mmToPx(this.state.gridSize);
        
        ctx.strokeStyle = '#E0E0E0';
        ctx.lineWidth = 0.5;
        
        // Vertical lines
        for (let x = 0; x < canvas.width; x += gridSize) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        }
        
        // Horizontal lines
        for (let y = 0; y < canvas.height; y += gridSize) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(canvas.width, y);
            ctx.stroke();
        }
    }
    
    drawElement(element) {
        const ctx = this.ctx;
        const x = this.mmToPx(element.x);
        const y = this.mmToPx(element.y);
        const width = this.mmToPx(element.width);
        const height = this.mmToPx(element.height);
        
        ctx.save();
        
        switch (element.element_type) {
            case 'text':
            case 'field':
                this.drawTextElement(element, x, y, width, height);
                break;
            case 'shape':
                this.drawShapeElement(element, x, y, width, height);
                break;
            case 'line':
                this.drawLineElement(element, x, y, width, height);
                break;
            case 'image':
                this.drawImageElement(element, x, y, width, height);
                break;
            case 'table':
                this.drawTableElement(element, x, y, width, height);
                break;
        }
        
        ctx.restore();
    }
    
    drawTextElement(element, x, y, width, height) {
        const ctx = this.ctx;
        
        // Background
        ctx.fillStyle = element.background_color || 'transparent';
        if (ctx.fillStyle !== 'transparent') {
            ctx.fillRect(x, y, width, height);
        }
        
        // Border
        if (element.border_width > 0) {
            ctx.strokeStyle = element.border_color || '#000000';
            ctx.lineWidth = element.border_width;
            ctx.strokeRect(x, y, width, height);
        }
        
        // Text
        ctx.fillStyle = element.color || '#000000';
        ctx.font = `${element.font_size}pt ${element.font_family || 'Arial'}`;
        ctx.textBaseline = 'top';
        
        const text = element.element_type === 'text' 
            ? (element.static_text || '') 
            : `[${element.field_name || 'Field'}]`;
        
        ctx.fillText(text, x + 5, y + 5, width - 10);
    }
    
    drawShapeElement(element, x, y, width, height) {
        const ctx = this.ctx;
        
        ctx.fillStyle = element.background_color || '#CCCCCC';
        ctx.fillRect(x, y, width, height);
        
        if (element.border_width > 0) {
            ctx.strokeStyle = element.border_color || '#000000';
            ctx.lineWidth = element.border_width;
            ctx.strokeRect(x, y, width, height);
        }
    }
    
    drawLineElement(element, x, y, width, height) {
        const ctx = this.ctx;
        
        ctx.strokeStyle = element.border_color || '#000000';
        ctx.lineWidth = element.border_width || 1;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + width, y);
        ctx.stroke();
    }
    
    drawImageElement(element, x, y, width, height) {
        const ctx = this.ctx;
        
        // Draw placeholder
        ctx.fillStyle = '#F0F0F0';
        ctx.fillRect(x, y, width, height);
        ctx.strokeStyle = '#CCCCCC';
        ctx.strokeRect(x, y, width, height);
        
        // Draw icon
        ctx.fillStyle = '#999999';
        ctx.font = '24px FontAwesome';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('🖼', x + width/2, y + height/2);
    }
    
    drawTableElement(element, x, y, width, height) {
        const ctx = this.ctx;
        
        ctx.fillStyle = '#F9F9F9';
        ctx.fillRect(x, y, width, height);
        ctx.strokeStyle = '#DDDDDD';
        ctx.strokeRect(x, y, width, height);
        
        // Draw header row
        ctx.fillStyle = '#4A90E2';
        ctx.fillRect(x, y, width, 20);
        
        ctx.strokeStyle = '#FFFFFF';
        ctx.fillText('[Table]', x + 5, y + 5);
    }
    
    drawSelectionBox(element) {
        const ctx = this.ctx;
        const x = this.mmToPx(element.x);
        const y = this.mmToPx(element.y);
        const width = this.mmToPx(element.width);
        const height = this.mmToPx(element.height);
        
        // Blue selection box
        ctx.strokeStyle = '#4A90E2';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.strokeRect(x - 2, y - 2, width + 4, height + 4);
        ctx.setLineDash([]);
        
        // Resize handles
        const handleSize = 6;
        ctx.fillStyle = '#FFFFFF';
        ctx.strokeStyle = '#4A90E2';
        ctx.lineWidth = 1;
        
        const handles = [
            [x, y], // top-left
            [x + width/2, y], // top-center
            [x + width, y], // top-right
            [x, y + height/2], // middle-left
            [x + width, y + height/2], // middle-right
            [x, y + height], // bottom-left
            [x + width/2, y + height], // bottom-center
            [x + width, y + height], // bottom-right
        ];
        
        for (const [hx, hy] of handles) {
            ctx.fillRect(hx - handleSize/2, hy - handleSize/2, handleSize, handleSize);
            ctx.strokeRect(hx - handleSize/2, hy - handleSize/2, handleSize, handleSize);
        }
    }
    
    // ========== Mouse Events ==========
    
    onCanvasMouseDown(e) {
        const rect = this.canvasRef.el.getBoundingClientRect();
        const x = (e.clientX - rect.left) / this.state.scale;
        const y = (e.clientY - rect.top) / this.state.scale;
        
        // Find clicked element
        const clickedElement = this.findElementAt(x, y);
        
        if (clickedElement) {
            this.state.selectedElement = clickedElement;
            this.dragStart = { x, y };
            this.dragElement = clickedElement;
        } else {
            this.state.selectedElement = null;
        }
        
        this.renderCanvas();
    }
    
    onCanvasMouseMove(e) {
        if (!this.dragElement) return;
        
        const rect = this.canvasRef.el.getBoundingClientRect();
        const x = (e.clientX - rect.left) / this.state.scale;
        const y = (e.clientY - rect.top) / this.state.scale;
        
        const dx = x - this.dragStart.x;
        const dy = y - this.dragStart.y;
        
        let newX = this.pxToMm(this.mmToPx(this.dragElement.x) + dx);
        let newY = this.pxToMm(this.mmToPx(this.dragElement.y) + dy);
        
        // Snap to grid
        if (this.state.snapToGrid) {
            newX = Math.round(newX / this.state.gridSize) * this.state.gridSize;
            newY = Math.round(newY / this.state.gridSize) * this.state.gridSize;
        }
        
        this.dragElement.x = newX;
        this.dragElement.y = newY;
        
        this.dragStart = { x, y };
        this.renderCanvas();
    }
    
    onCanvasMouseUp(e) {
        if (this.dragElement) {
            // Save to server
            this.saveElement(this.dragElement);
        }
        this.dragElement = null;
    }
    
    findElementAt(x, y) {
        // Check from top to bottom (reverse order)
        for (let i = this.state.elements.length - 1; i >= 0; i--) {
            const elem = this.state.elements[i];
            const ex = this.mmToPx(elem.x);
            const ey = this.mmToPx(elem.y);
            const ew = this.mmToPx(elem.width);
            const eh = this.mmToPx(elem.height);
            
            if (x >= ex && x <= ex + ew && y >= ey && y <= ey + eh) {
                return elem;
            }
        }
        return null;
    }
    
    // ========== Actions ==========
    
    async addElement(type) {
        if (!this.state.template) return;
        
        const newElement = {
            template_id: this.state.template.id,
            element_type: type,
            x: 10,
            y: 10,
            width: type === 'table' ? 180 : 50,
            height: type === 'table' ? 100 : 10,
            sequence: this.state.elements.length,
            font_size: 12,
            color: '#000000',
        };
        
        if (type === 'text') {
            newElement.static_text = 'New Text';
        } else if (type === 'field') {
            newElement.field_name = 'partner_id.name';
        }
        
        const id = await this.orm.create("invoice.template.element", [newElement]);
        newElement.id = id;
        
        this.state.elements.push(newElement);
        this.state.selectedElement = newElement;
        this.renderCanvas();
        
        this.notification.add("Element added!", { type: "success" });
    }
    
    async saveElement(element) {
        await this.orm.write("invoice.template.element", [element.id], {
            x: element.x,
            y: element.y,
            width: element.width,
            height: element.height,
        });
    }
    
    async deleteElement() {
        if (!this.state.selectedElement) return;
        
        await this.orm.unlink("invoice.template.element", [this.state.selectedElement.id]);
        
        this.state.elements = this.state.elements.filter(
            e => e.id !== this.state.selectedElement.id
        );
        this.state.selectedElement = null;
        this.renderCanvas();
        
        this.notification.add("Element deleted!", { type: "success" });
    }
    
    async saveTemplate() {
        this.notification.add("Template saved!", { type: "success" });
    }
    
    async preview() {
        if (!this.state.template) return;
        
        await this.orm.call(
            "invoice.template.designer",
            "action_preview",
            [this.state.template.id]
        );
    }
    
    closeDesigner() {
        this.action.doAction({
            type: "ir.actions.act_window_close",
        });
    }
    
    // ========== Utilities ==========
    
    mmToPx(mm) {
        // A4 @ 96 DPI: 210mm = 794px
        return (mm / 210) * 794;
    }
    
    pxToMm(px) {
        return (px / 794) * 210;
    }
    
    zoomIn() {
        this.state.scale = Math.min(this.state.scale + 0.1, 2.0);
    }
    
    zoomOut() {
        this.state.scale = Math.max(this.state.scale - 0.1, 0.5);
    }
    
    toggleGrid() {
        this.state.showGrid = !this.state.showGrid;
        this.renderCanvas();
    }
}

InvoiceDesigner.template = "sap_integration.InvoiceDesigner";

registry.category("actions").add("invoice_designer", InvoiceDesigner);

export default InvoiceDesigner;

