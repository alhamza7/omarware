/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * Invoice Designer Canvas - Visual Designer Component
 * Simple but functional drag & drop designer
 */
export class InvoiceDesignerCanvas extends Component {
    static template = "invoice_designer.Canvas";
    static props = ["*"]; // Accept all props

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        // Get templateId from URL hash (most reliable in Odoo 19)
        let templateId = null;
        
        // Parse URL hash: #action=invoice_designer_canvas&template_id=5
        const hash = window.location.hash;
        console.log("Current URL hash:", hash);
        
        if (hash) {
            const match = hash.match(/template_id=(\d+)/);
            if (match) {
                templateId = parseInt(match[1]);
                console.log("✅ Template ID found in URL:", templateId);
            } else {
                console.log("❌ No template_id in URL hash");
            }
        }
        
        // Fallback: try from props (unlikely to work but worth trying)
        if (!templateId) {
            if (this.props.action && this.props.action.params) {
                templateId = this.props.action.params.templateId || this.props.action.params.template_id;
            }
            if (!templateId && this.props.action && this.props.action.context) {
                templateId = this.props.action.context.default_template_id;
            }
            if (!templateId) {
                templateId = this.props.templateId || this.props.template_id;
            }
            if (templateId) {
                console.log("✅ Template ID found in props:", templateId);
            }
        }
        
        console.log("Final Template ID:", templateId);
        
        if (!templateId) {
            this.notification.add(
                "Template ID is missing. Please open designer from a template record.", 
                { type: "danger", sticky: true }
            );
        }
        
        this.templateId = templateId;
        
        this.state = useState({
            template: null,
            elements: [],
            selectedElement: null,
            zoom: 1.0,
            showGrid: true,
            snapToGrid: false,
            isDragging: false,
            dragOffset: { x: 0, y: 0 },
            unsavedChanges: false,
            canUndo: false,
            canRedo: false,
            history: [],
            historyIndex: -1,
        });
        
        this.canvasRef = useRef("canvas");
        
        onMounted(() => {
            this.loadTemplate();
            this.setupEventListeners();
        });
        
        onWillUnmount(() => {
            this.removeEventListeners();
        });
    }
    
    async loadTemplate() {
        if (!this.templateId) {
            console.error("Cannot load template: templateId is missing");
            this.notification.add("Error: Template ID is missing", { type: "danger" });
            return;
        }
        
        try {
            console.log("Loading template ID:", this.templateId);
            
            const template = await this.orm.read(
                "invoice.template.designer",
                [this.templateId],
                ["name", "page_width", "page_height", "background_color", "show_grid", "element_ids"]
            );
            
            console.log("Template loaded:", template);
            
            if (template.length > 0) {
                this.state.template = template[0];
                this.state.showGrid = template[0].show_grid;
                await this.loadElements();
                this.renderCanvas();
            } else {
                this.notification.add("Template not found", { type: "danger" });
            }
        } catch (error) {
            console.error("Error loading template:", error);
            this.notification.add(`Error loading template: ${error.message}`, { type: "danger" });
        }
    }
    
    async loadElements() {
        if (!this.state.template.element_ids) return;
        
        try {
            const elements = await this.orm.read(
                "invoice.template.element",
                this.state.template.element_ids,
                [
                    // basic
                    "name", "element_type", "x", "y", "width", "height", "content",
                    "color", "background_color", "font_size", "z_index", "visible",
                    // table core
                    "show_column_product", "show_column_description", "show_column_qty", "show_column_uom",
                    "show_column_price", "show_column_discount", "show_column_tax", "show_column_subtotal",
                    "column_width_product", "column_width_description", "column_width_qty", "column_width_uom",
                    "column_width_price", "column_width_discount", "column_width_tax", "column_width_subtotal",
                    "column_order_product", "column_order_description", "column_order_qty", "column_order_uom",
                    "column_order_price", "column_order_discount", "column_order_tax", "column_order_subtotal",
                    "column_align_product", "column_align_description", "column_align_qty", "column_align_uom",
                    "column_align_price", "column_align_discount", "column_align_tax", "column_align_subtotal",
                    "header_product", "header_description", "header_qty", "header_uom",
                    "header_price", "header_discount", "header_tax", "header_subtotal",
                    "table_direction", "table_font_family", "table_custom_font",
                    "table_header_bg", "table_header_color", "table_header_font_size", "table_header_font_weight",
                    "table_row_bg", "table_row_alternate_bg", "table_row_color", "table_row_font_size",
                    "table_border_color", "table_border_width", "table_cell_padding",
                    "show_table_footer", "table_footer_text",
                ]
            );
            this.state.elements = elements.sort((a, b) => a.z_index - b.z_index);
            this.renderCanvas();
        } catch (error) {
            this.notification.add("Error loading elements", { type: "danger" });
        }
    }
    
    setupEventListeners() {
        if (!this.canvasRef.el) return;
        
        this.canvasRef.el.addEventListener('mousedown', this.onMouseDown.bind(this));
        this.canvasRef.el.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.canvasRef.el.addEventListener('mouseup', this.onMouseUp.bind(this));
    }
    
    removeEventListeners() {
        if (!this.canvasRef.el) return;
        
        this.canvasRef.el.removeEventListener('mousedown', this.onMouseDown.bind(this));
        this.canvasRef.el.removeEventListener('mousemove', this.onMouseMove.bind(this));
        this.canvasRef.el.removeEventListener('mouseup', this.onMouseUp.bind(this));
    }
    
    renderCanvas() {
        if (!this.canvasRef.el) return;
        
        const canvas = this.canvasRef.el;
        const ctx = canvas.getContext('2d');
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Background
        if (this.state.template) {
            ctx.fillStyle = this.state.template.background_color || '#FFFFFF';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
        }
        
        // Grid
        if (this.state.showGrid) {
            this.drawGrid(ctx);
        }
        
        // Elements
        this.state.elements.forEach(element => {
            if (element.visible !== false) {
                this.drawElement(ctx, element);
            }
        });
        
        // Selection
        if (this.state.selectedElement) {
            this.drawSelection(ctx, this.state.selectedElement);
        }
    }
    
    drawGrid(ctx) {
        const gridSize = 20;
        ctx.strokeStyle = '#E0E0E0';
        ctx.lineWidth = 0.5;
        
        for (let x = 0; x < ctx.canvas.width; x += gridSize) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, ctx.canvas.height);
            ctx.stroke();
        }
        
        for (let y = 0; y < ctx.canvas.height; y += gridSize) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(ctx.canvas.width, y);
            ctx.stroke();
        }
    }
    
    drawElement(ctx, element) {
        const scale = 3.78; // mm to pixels
        const x = element.x * scale;
        const y = element.y * scale;
        const width = element.width * scale;
        const height = element.height * scale;
        
        // Background
        if (element.background_color && element.background_color !== 'transparent') {
            ctx.fillStyle = element.background_color;
            ctx.fillRect(x, y, width, height);
        }
        
        // Content
        if (element.element_type === 'text' && element.content) {
            ctx.fillStyle = element.color || '#000000';
            ctx.font = `${element.font_size || 12}px Arial`;
            ctx.fillText(element.content, x + 5, y + 20);
        }
        
        // Border (for visualization)
        ctx.strokeStyle = '#CCCCCC';
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y, width, height);
    }
    
    drawSelection(ctx, element) {
        const scale = 3.78;
        const x = element.x * scale;
        const y = element.y * scale;
        const width = element.width * scale;
        const height = element.height * scale;
        
        ctx.strokeStyle = '#4A90E2';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.strokeRect(x, y, width, height);
        ctx.setLineDash([]);
        
        // Resize handles
        const handleSize = 8;
        ctx.fillStyle = '#4A90E2';
        ctx.fillRect(x - handleSize/2, y - handleSize/2, handleSize, handleSize);
        ctx.fillRect(x + width - handleSize/2, y - handleSize/2, handleSize, handleSize);
        ctx.fillRect(x - handleSize/2, y + height - handleSize/2, handleSize, handleSize);
        ctx.fillRect(x + width - handleSize/2, y + height - handleSize/2, handleSize, handleSize);
    }
    
    onMouseDown(event) {
        const rect = this.canvasRef.el.getBoundingClientRect();
        const x = (event.clientX - rect.left) / 3.78;
        const y = (event.clientY - rect.top) / 3.78;
        
        // Find clicked element
        const clickedElement = this.findElementAt(x, y);
        
        if (clickedElement) {
            this.state.selectedElement = clickedElement;
            this.state.isDragging = true;
            this.state.dragOffset = {
                x: x - clickedElement.x,
                y: y - clickedElement.y
            };
            this.renderCanvas();
        } else {
            this.state.selectedElement = null;
            this.renderCanvas();
        }
    }
    
    onMouseMove(event) {
        if (!this.state.isDragging || !this.state.selectedElement) return;
        
        const rect = this.canvasRef.el.getBoundingClientRect();
        const x = (event.clientX - rect.left) / 3.78;
        const y = (event.clientY - rect.top) / 3.78;
        
        this.state.selectedElement.x = x - this.state.dragOffset.x;
        this.state.selectedElement.y = y - this.state.dragOffset.y;
        
        this.renderCanvas();
    }
    
    async onMouseUp() {
        if (this.state.isDragging && this.state.selectedElement) {
            // Save position
            await this.saveElement(this.state.selectedElement);
        }
        this.state.isDragging = false;
    }
    
    findElementAt(x, y) {
        for (let i = this.state.elements.length - 1; i >= 0; i--) {
            const element = this.state.elements[i];
            if (x >= element.x && x <= element.x + element.width &&
                y >= element.y && y <= element.y + element.height) {
                return element;
            }
        }
        return null;
    }
    
    async saveElement(element) {
        try {
            await this.orm.write(
                "invoice.template.element",
                [element.id],
                { x: element.x, y: element.y }
            );
            this.notification.add("Element updated", { type: "success" });
        } catch (error) {
            this.notification.add("Error saving element", { type: "danger" });
        }
    }
    
    async addTextElement() {
        if (!this.templateId) {
            this.notification.add("Cannot add element: Template ID is missing", { type: "danger" });
            return;
        }
        
        try {
            const newElement = await this.orm.create(
                "invoice.template.element",
                [{
                    template_id: this.templateId,
                    name: "New Text",
                    element_type: "text",
                    content: "Sample Text",
                    x: 20,
                    y: 20,
                    width: 100,
                    height: 30,
                    font_size: 14,
                    color: "#000000",
                }]
            );
            
            console.log("Element created:", newElement);
            await this.loadElements();
            this.notification.add("Text element added", { type: "success" });
        } catch (error) {
            console.error("Error adding element:", error);
            this.notification.add(`Error adding element: ${error.message}`, { type: "danger" });
        }
    }
    
    zoomIn() {
        this.state.zoom = Math.min(this.state.zoom + 0.1, 2.0);
        this.renderCanvas();
    }
    
    zoomOut() {
        this.state.zoom = Math.max(this.state.zoom - 0.1, 0.5);
        this.renderCanvas();
    }
    
    toggleGrid() {
        this.state.showGrid = !this.state.showGrid;
        this.renderCanvas();
    }
    
    toggleSnap() {
        this.state.snapToGrid = !this.state.snapToGrid;
        this.notification.add(
            this.state.snapToGrid ? "Snap to grid enabled" : "Snap to grid disabled",
            { type: "info" }
        );
    }
    
    zoomReset() {
        this.state.zoom = 1.0;
        this.renderCanvas();
    }
    
    // ================ ADD ELEMENTS ================
    
    async addFieldElement() {
        await this.createElement({
            name: "حقل ديناميكي",
            element_type: "field",
            field_name: "partner_id.name",
            content: "[اسم العميل]",
            x: 20,
            y: 50,
            width: 100,
            height: 20,
            font_size: 12,
            color: "#000000",
        });
    }
    
    async addImageElement() {
        await this.createElement({
            name: "صورة",
            element_type: "image",
            x: 150,
            y: 20,
            width: 50,
            height: 50,
            object_fit: "contain",
        });
    }
    
    async addTableElement() {
        await this.createElement({
            name: "جدول المنتجات",
            element_type: "table",
            x: 20,
            y: 100,
            width: 170,
            height: 100,
            border_width: 1,
            border_style: "solid",
            color: "#000000",
        });
    }
    
    async addShapeElement() {
        await this.createElement({
            name: "شكل",
            element_type: "shape",
            shape_type: "rectangle",
            x: 20,
            y: 80,
            width: 50,
            height: 30,
            background_color: "#e0e0e0",
            border_width: 1,
            border_style: "solid",
            color: "#000000",
        });
    }
    
    async addLineElement() {
        await this.createElement({
            name: "خط",
            element_type: "line",
            x: 20,
            y: 70,
            width: 170,
            height: 2,
            color: "#000000",
            border_width: 1,
        });
    }
    
    async addBarcodeElement() {
        await this.createElement({
            name: "باركود",
            element_type: "barcode",
            field_name: "name",
            x: 20,
            y: 220,
            width: 60,
            height: 20,
        });
    }
    
    async addQRElement() {
        await this.createElement({
            name: "QR Code",
            element_type: "qr",
            field_name: "name",
            x: 100,
            y: 220,
            width: 30,
            height: 30,
        });
    }
    
    async addIconElement() {
        await this.createElement({
            name: "أيقونة",
            element_type: "icon",
            content: "fa-star",
            x: 150,
            y: 80,
            width: 20,
            height: 20,
            color: "#FFD700",
            font_size: 20,
        });
    }
    
    async addGradientElement() {
        await this.createElement({
            name: "تدرج لوني",
            element_type: "gradient_box",
            x: 20,
            y: 260,
            width: 170,
            height: 20,
            background_color: "linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
        });
    }
    
    async createElement(elementData) {
        if (!this.templateId) {
            this.notification.add("Cannot add element: Template ID is missing", { type: "danger" });
            return;
        }
        
        try {
            const newElement = await this.orm.create(
                "invoice.template.element",
                [{
                    template_id: this.templateId,
                    ...elementData
                }]
            );
            
            console.log("Element created:", newElement);
            await this.loadElements();
            this.state.unsavedChanges = true;
            this.notification.add(`تم إضافة ${elementData.name}`, { type: "success" });
        } catch (error) {
            console.error("Error adding element:", error);
            this.notification.add(`خطأ في إضافة العنصر: ${error.message}`, { type: "danger" });
        }
    }
    
    // ================ ELEMENT OPERATIONS ================
    
    selectElement(element) {
        this.state.selectedElement = element;
        this.renderCanvas();
    }
    
    toggleElementVisibility(element) {
        element.visible = element.visible !== false ? false : true;
        this.saveElement(element);
        this.renderCanvas();
    }
    
    async deleteElement() {
        if (!this.state.selectedElement) return;
        
        if (confirm(`هل تريد حذف ${this.state.selectedElement.name}؟`)) {
            try {
                await this.orm.unlink("invoice.template.element", [this.state.selectedElement.id]);
                this.state.selectedElement = null;
                await this.loadElements();
                this.notification.add("تم حذف العنصر", { type: "success" });
            } catch (error) {
                this.notification.add("خطأ في حذف العنصر", { type: "danger" });
            }
        }
    }
    
    // ================ ALIGNMENT ================
    
    alignLeft() {
        if (!this.state.selectedElement) return;
        this.state.selectedElement.x = 10;
        this.saveElement(this.state.selectedElement);
        this.renderCanvas();
    }
    
    alignCenter() {
        if (!this.state.selectedElement || !this.state.template) return;
        const centerX = (this.state.template.page_width - this.state.selectedElement.width) / 2;
        this.state.selectedElement.x = centerX;
        this.saveElement(this.state.selectedElement);
        this.renderCanvas();
    }
    
    alignRight() {
        if (!this.state.selectedElement || !this.state.template) return;
        this.state.selectedElement.x = this.state.template.page_width - this.state.selectedElement.width - 10;
        this.saveElement(this.state.selectedElement);
        this.renderCanvas();
    }
    
    // ================ LAYER OPERATIONS ================
    
    async bringToFront() {
        if (!this.state.selectedElement) return;
        const maxZ = Math.max(...this.state.elements.map(e => e.z_index || 1));
        this.state.selectedElement.z_index = maxZ + 1;
        await this.saveElement(this.state.selectedElement);
        await this.loadElements();
        this.renderCanvas();
    }
    
    async sendToBack() {
        if (!this.state.selectedElement) return;
        const minZ = Math.min(...this.state.elements.map(e => e.z_index || 1));
        this.state.selectedElement.z_index = minZ - 1;
        await this.saveElement(this.state.selectedElement);
        await this.loadElements();
        this.renderCanvas();
    }
    
    // ================ PROPERTY CHANGES ================
    
    onPropertyChange() {
        this.state.unsavedChanges = true;
        if (this.state.selectedElement) {
            this.state.selectedElement.modified = true;
        }
        this.renderCanvas();
    }
    
    onElementTypeChange() {
        this.onPropertyChange();
    }
    
    setTextAlign(align) {
        if (!this.state.selectedElement) return;
        this.state.selectedElement.text_align = align;
        this.onPropertyChange();
    }
    
    async onImageUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = async (e) => {
            if (this.state.selectedElement) {
                this.state.selectedElement.image_data = e.target.result.split(',')[1];
                this.state.selectedElement.image_filename = file.name;
                await this.saveElement(this.state.selectedElement);
                this.renderCanvas();
                this.notification.add("تم رفع الصورة", { type: "success" });
            }
        };
        reader.readAsDataURL(file);
    }
    
    // ================ CANVAS EVENTS ================
    
    onCanvasMouseDown(event) {
        this.onMouseDown(event);
    }
    
    onCanvasMouseMove(event) {
        this.onMouseMove(event);
    }
    
    onCanvasMouseUp(event) {
        this.onMouseUp(event);
    }
    
    // ================ SAVE & PREVIEW ================
    
    async saveTemplate() {
        try {
            // Save all modified elements
            for (const element of this.state.elements) {
                if (element.modified) {
                    const payload = { ...element };
                    delete payload.modified; // not a DB field
                    // strip any computed-only keys
                    delete payload.id;
                    delete payload.__last_update;
                    delete payload.display_name;
                    await this.orm.write(
                        "invoice.template.element",
                        [element.id],
                        payload
                    );
                }
            }
            
            this.state.unsavedChanges = false;
            this.notification.add("تم حفظ القالب بنجاح", { type: "success" });
        } catch (error) {
            this.notification.add("خطأ في حفظ القالب", { type: "danger" });
        }
    }
    
    async previewTemplate() {
        if (!this.templateId) return;
        
        try {
            const action = await this.orm.call(
                "invoice.template.designer",
                "action_preview_pdf",
                [[this.templateId]]
            );
            
            // Open preview in new window
            window.open(action.url, '_blank');
        } catch (error) {
            this.notification.add("خطأ في المعاينة", { type: "danger" });
        }
    }
    
    async exportPDF() {
        this.notification.add("جاري تصدير PDF...", { type: "info" });
        await this.previewTemplate();
    }
    
    // ================ UNDO/REDO ================
    
    undo() {
        if (this.state.historyIndex > 0) {
            this.state.historyIndex--;
            this.state.elements = JSON.parse(JSON.stringify(this.state.history[this.state.historyIndex]));
            this.state.canUndo = this.state.historyIndex > 0;
            this.state.canRedo = this.state.historyIndex < this.state.history.length - 1;
            this.renderCanvas();
        }
    }
    
    redo() {
        if (this.state.historyIndex < this.state.history.length - 1) {
            this.state.historyIndex++;
            this.state.elements = JSON.parse(JSON.stringify(this.state.history[this.state.historyIndex]));
            this.state.canUndo = this.state.historyIndex > 0;
            this.state.canRedo = this.state.historyIndex < this.state.history.length - 1;
            this.renderCanvas();
        }
    }
    
    addToHistory() {
        // Remove any forward history
        this.state.history = this.state.history.slice(0, this.state.historyIndex + 1);
        
        // Add current state
        this.state.history.push(JSON.parse(JSON.stringify(this.state.elements)));
        this.state.historyIndex = this.state.history.length - 1;
        
        // Limit history to 50 states
        if (this.state.history.length > 50) {
            this.state.history.shift();
            this.state.historyIndex--;
        }
        
        this.state.canUndo = this.state.historyIndex > 0;
        this.state.canRedo = false;
    }
}

registry.category("actions").add("invoice_designer_canvas", InvoiceDesignerCanvas);

