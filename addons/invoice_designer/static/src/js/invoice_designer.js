/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const FABRIC_URL = "https://cdn.jsdelivr.net/npm/fabric@5.3.0/dist/fabric.min.js";
const MM_TO_PX = 3.78;

async function loadScriptOnce(src) {
    if (document.querySelector(`script[data-src="${src}"]`)) {
        return;
    }
    await new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = src;
        script.async = true;
        script.dataset.src = src;
        script.onload = () => resolve();
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

async function loadFabricWithFallback() {
    try {
        await loadScriptOnce(FABRIC_URL);
        return true;
    } catch (err) {
        console.warn("CDN fabric failed, trying local fallback", err);
        try {
            await loadScriptOnce("/invoice_designer/static/lib/fabric.min.js");
            return true;
        } catch (err2) {
            console.error("Fabric fallback failed", err2);
            return false;
        }
    }
}

function ensureGoogleFont(family, weights = "300;400;700;800") {
    const id = `gf-${family.replace(/\s+/g, "-")}`;
    if (!document.getElementById(id)) {
        const link = document.createElement("link");
        link.id = id;
        link.rel = "stylesheet";
        link.href = `https://fonts.googleapis.com/css2?family=${family.replace(/\s+/g, "+")}:wght@${weights}&display=swap`;
        document.head.appendChild(link);
    }
    if (document.fonts) {
        document.fonts.load(`16px "${family}"`);
    }
}

/**
 * Invoice Designer Canvas - Visual Designer Component
 * Simple but functional drag & drop designer
 */
export class InvoiceDesignerCanvas extends Component {
    static template = "invoice_designer.Canvas";
    static props = ["*"]; // Accept all props

    GRID_MM = 5; // grid size in mm (approx 5mm ~= 20px)

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this._boundMouseDown = this.onMouseDown.bind(this);
        this._boundMouseMove = this.onMouseMove.bind(this);
        this._boundMouseUp = this.onMouseUp.bind(this);
        this.elementObjects = new Map(); // elementId -> fabric object
        this.fabricReady = false;
        
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
            isResizing: false,
            resizeHandle: null,
            dragOffset: { x: 0, y: 0 },
            dragStart: { x: 0, y: 0 },
            unsavedChanges: false,
            canUndo: false,
            canRedo: false,
            history: [],
            historyIndex: -1,
            initialElement: null,
        });
        
        this.canvasRef = useRef("canvas");
        
        onMounted(() => {
            this.loadTemplate();
            this.setupEventListeners();
            this.ensureFabric(); // begin loading Fabric.js early
        });
        
        onWillUnmount(() => {
            this.removeEventListeners();
        });
    }
    
    async loadTemplate() {
        if (!this.templateId) {
            console.error("❌ Cannot load template: templateId is missing");
            this.notification.add("Error: Template ID is missing", { type: "danger" });
            return;
        }
        
        try {
            console.log("📥 Loading template ID:", this.templateId);
            
            const template = await this.orm.read(
                "invoice.template.designer",
                [this.templateId],
                ["name", "page_width", "page_height", "background_color", "show_grid", "element_ids"]
            );
            
            console.log("✅ Template loaded successfully:", template);
            
            if (template.length > 0) {
                this.state.template = template[0];
                this.state.showGrid = template[0].show_grid;
                console.log("📐 Template dimensions:", this.state.template.page_width, "x", this.state.template.page_height, "mm");
                
                this.setCanvasSize();
                console.log("✅ Canvas size set");
                
                await this.loadElements();
                console.log("✅ Elements loaded, count:", this.state.elements.length);
                
                await this.ensureFabric();
                console.log("🎨 Fabric ready status:", this.fabricReady);
                
                if (this.fabricReady) {
                    console.log("🎨 Building Fabric scene...");
                    this.buildFabricScene();
                } else {
                    console.log("🖌️ Using fallback canvas rendering...");
                    this.renderCanvas(); // fallback
                }
            } else {
                console.error("❌ Template not found");
                this.notification.add("Template not found", { type: "danger" });
            }
        } catch (error) {
            console.error("❌ Error loading template:", error);
            this.notification.add(`Error loading template: ${error.message}`, { type: "danger" });
        }
    }
    
    async loadElements() {
        try {
            console.log("📥 Loading elements for template:", this.templateId);
            const elements = await this.orm.searchRead(
                "invoice.template.element",
                [["template_id", "=", this.templateId]],
                [
                    // basic
                    "name", "element_type", "x", "y", "width", "height", "content",
                    "color", "background_color", "font_size", "z_index", "visible",
                    "font_family_name", "font_weight", "text_align", "shape_type",
                    "line_x2", "line_y2", "object_fit", "image_url", "image_data",
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
                    "show_table_footer", "table_footer_text", "table_max_rows_per_page",
                ]
            );
            console.log("✅ Elements loaded:", elements.length, "elements");
            if (elements.length > 0) {
                console.log("📋 First element sample:", elements[0]);
            } else {
                console.warn("⚠️ No elements found for this template");
            }
            this.state.elements = elements.sort((a, b) => a.z_index - b.z_index);
            this.addToHistory();
            if (this.fabricReady) {
                this.buildFabricScene();
            }
        } catch (error) {
            console.error("❌ Error loading elements:", error);
            this.notification.add("Error loading elements", { type: "danger" });
        }
    }
    
    setupEventListeners() {
        // Don't setup if Fabric is ready - Fabric handles its own events
        if (this.fabricReady && this.fabricCanvas) {
            console.log("⏩ Skipping native event listeners (Fabric handles events)");
            return;
        }
        if (!this.canvasRef.el) return;
        
        console.log("📌 Setting up native canvas event listeners");
        this.canvasRef.el.addEventListener('mousedown', this._boundMouseDown);
        this.canvasRef.el.addEventListener('mousemove', this._boundMouseMove);
        this.canvasRef.el.addEventListener('mouseup', this._boundMouseUp);
    }
    
    removeEventListeners() {
        if (!this.canvasRef.el) return;
        
        console.log("🗑️ Removing native canvas event listeners");
        this.canvasRef.el.removeEventListener('mousedown', this._boundMouseDown);
        this.canvasRef.el.removeEventListener('mousemove', this._boundMouseMove);
        this.canvasRef.el.removeEventListener('mouseup', this._boundMouseUp);
    }
    
    renderCanvas() {
        console.log("🎨 renderCanvas called, fabricCanvas exists:", !!this.fabricCanvas, "fabricReady:", this.fabricReady);
        if (this.fabricCanvas) {
            this.fabricCanvas.requestRenderAll();
            console.log("✅ Fabric canvas rendered");
            return;
        }
        if (!this.canvasRef.el) {
            console.error("❌ Canvas element not found");
            return;
        }
        console.log("🖌️ Using fallback canvas rendering");
        this.setCanvasSize();
        const ctx = this.canvasRef.el.getContext('2d');
        console.log("📐 Canvas dimensions:", this.canvasRef.el.width, "x", this.canvasRef.el.height);
        ctx.clearRect(0, 0, this.canvasRef.el.width, this.canvasRef.el.height);
        if (this.state.template) {
            ctx.fillStyle = this.state.template.background_color || '#FFFFFF';
            ctx.fillRect(0, 0, this.canvasRef.el.width, this.canvasRef.el.height);
            console.log("✅ Background drawn:", this.state.template.background_color || '#FFFFFF');
        }
        // Fallback rendering when Fabric is not ready
        if (!this.fabricReady) {
            if (this.state.showGrid) {
                this.drawGrid(ctx);
                console.log("✅ Grid drawn");
            }
            console.log("📦 Drawing", this.state.elements.length, "elements");
            this.state.elements.forEach((element, idx) => {
                if (element.visible !== false) {
                    console.log(`  → Element ${idx}:`, element.element_type, `at (${element.x}, ${element.y})`);
                    this.drawElement(ctx, element);
                }
            });
            if (this.state.selectedElement) {
                this.drawSelection(ctx, this.state.selectedElement);
                console.log("✅ Selection drawn");
            }
        }
        console.log("✅ renderCanvas complete");
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
        const fontSize = element.font_size || 12;
        
        // Background
        if (element.background_color && element.background_color !== 'transparent') {
            ctx.fillStyle = element.background_color;
            ctx.fillRect(x, y, width, height);
        }
        
        // Content rendering per element type
        ctx.save();
        ctx.fillStyle = element.color || '#000000';
        ctx.font = `${fontSize}px ${element.font_family_name || "Arial"}`;
        ctx.textBaseline = 'alphabetic'; // avoid invalid baseline values
        const allowedAlign = ['left', 'right', 'center', 'start', 'end'];
        ctx.textAlign = allowedAlign.includes(element.text_align) ? element.text_align : 'left';
        
        if (element.element_type === 'text') {
            ctx.fillText(element.content || 'نص', x + 6, y + fontSize + 6, width - 12);
        } else if (element.element_type === 'field') {
            ctx.fillText(element.content || `[${element.field_name || 'حقل'}]`, x + 6, y + fontSize + 6, width - 12);
        } else if (element.element_type === 'shape') {
            ctx.strokeStyle = element.color || '#000000';
            ctx.lineWidth = 1;
            if (element.shape_type === 'circle') {
                ctx.beginPath();
                ctx.arc(x + width / 2, y + height / 2, Math.min(width, height) / 2, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();
            } else if (element.shape_type === 'ellipse') {
                ctx.beginPath();
                ctx.ellipse(x + width / 2, y + height / 2, width / 2, height / 2, 0, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();
            } else if (element.shape_type === 'triangle') {
                ctx.beginPath();
                ctx.moveTo(x + width / 2, y);
                ctx.lineTo(x + width, y + height);
                ctx.lineTo(x, y + height);
                ctx.closePath();
                ctx.fill();
                ctx.stroke();
            } else {
                ctx.fillRect(x, y, width, height);
                ctx.strokeRect(x, y, width, height);
            }
        } else if (element.element_type === 'line') {
            ctx.strokeStyle = element.color || '#000000';
            ctx.lineWidth = element.border_width || 2;
            const x2 = (element.line_x2 || element.x + element.width) * scale;
            const y2 = (element.line_y2 || element.y) * scale;
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(x2, y2);
            ctx.stroke();
        } else if (element.element_type === 'table') {
            ctx.fillStyle = '#f7f7f7';
            ctx.fillRect(x, y, width, height);
            ctx.strokeStyle = '#b0b0b0';
            ctx.strokeRect(x, y, width, height);
            ctx.fillStyle = '#4a5568';
            ctx.fillRect(x, y, width, 24);
            ctx.fillStyle = '#ffffff';
            ctx.fillText('جدول المنتجات', x + 8, y + 18);
        } else if (element.element_type === 'barcode') {
            ctx.fillStyle = '#000000';
            for (let i = 0; i < width; i += 4) {
                if ((i / 4) % 2 === 0) {
                    ctx.fillRect(x + i, y, 2, height);
                }
            }
        } else if (element.element_type === 'qr') {
            ctx.fillStyle = '#000000';
            ctx.fillRect(x, y, width, height);
            ctx.clearRect(x + 4, y + 4, width - 8, height - 8);
            ctx.fillRect(x + width / 2 - 6, y + height / 2 - 6, 12, 12);
        } else if (element.element_type === 'image') {
            ctx.fillStyle = '#f0f0f0';
            ctx.strokeStyle = '#bbbbbb';
            ctx.fillRect(x, y, width, height);
            ctx.strokeRect(x, y, width, height);
            ctx.fillStyle = '#999999';
            ctx.fillText('صورة', x + width / 2, y + height / 2);
        } else if (element.element_type === 'gradient_box') {
            const gradient = ctx.createLinearGradient(x, y, x + width, y);
            gradient.addColorStop(0, '#667eea');
            gradient.addColorStop(1, '#764ba2');
            ctx.fillStyle = gradient;
            ctx.fillRect(x, y, width, height);
        }
        
        ctx.restore();
        
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
        const handleSize = 10;
        ctx.fillStyle = '#4A90E2';
        // Top-left
        ctx.fillRect(x - handleSize/2, y - handleSize/2, handleSize, handleSize);
        // Top-right
        ctx.fillRect(x + width - handleSize/2, y - handleSize/2, handleSize, handleSize);
        // Bottom-left
        ctx.fillRect(x - handleSize/2, y + height - handleSize/2, handleSize, handleSize);
        // Bottom-right
        ctx.fillRect(x + width - handleSize/2, y + height - handleSize/2, handleSize, handleSize);
    }
    
    onMouseDown(event) {
        if (this.fabricReady) return; // Fabric handles interactions
        const { x, y } = this._getCanvasCoordinates(event);
        
        // Find clicked element
        const clickedElement = this.findElementAt(x, y);
        
        // Check resize handles first on currently selected element
        if (this.state.selectedElement) {
            const handle = this._getResizeHandle(this.state.selectedElement, x, y);
            if (handle) {
                this.state.isResizing = true;
                this.state.resizeHandle = handle;
                this.state.dragStart = { x, y };
                this.state.initialElement = { ...this.state.selectedElement };
                return;
            }
        }
        
        if (clickedElement) {
            this.state.selectedElement = clickedElement;
            this.state.isDragging = true;
            this.state.dragStart = { x, y };
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
        if (this.fabricReady) return;
        if (!this.state.selectedElement) return;
        
        const { x, y } = this._getCanvasCoordinates(event);
        
        if (this.state.isResizing && this.state.initialElement) {
            const el = this.state.selectedElement;
            const init = this.state.initialElement;
            const dx = x - this.state.dragStart.x;
            const dy = y - this.state.dragStart.y;
            
            if (this.state.resizeHandle.includes('e')) {
                el.width = this._snap(Math.max(5, init.width + dx));
            }
            if (this.state.resizeHandle.includes('s')) {
                el.height = this._snap(Math.max(5, init.height + dy));
            }
            if (this.state.resizeHandle.includes('w')) {
                const newWidth = this._snap(Math.max(5, init.width - dx));
                const newX = this._snap(init.x + dx);
                if (newWidth >= 5) {
                    el.width = newWidth;
                    el.x = newX;
                }
            }
            if (this.state.resizeHandle.includes('n')) {
                const newHeight = this._snap(Math.max(5, init.height - dy));
                const newY = this._snap(init.y + dy);
                if (newHeight >= 5) {
                    el.height = newHeight;
                    el.y = newY;
                }
            }
            
            this.renderCanvas();
            return;
        }
        
        if (!this.state.isDragging) return;
        
        this.state.selectedElement.x = this._snap(x - this.state.dragOffset.x);
        this.state.selectedElement.y = this._snap(y - this.state.dragOffset.y);
        
        this.renderCanvas();
    }
    
    async onMouseUp() {
        if (this.fabricReady) return;
        if (this.state.selectedElement && (this.state.isDragging || this.state.isResizing)) {
            this.state.selectedElement.modified = true;
            this.state.unsavedChanges = true;
            this.addToHistory();
        }
        this.state.isDragging = false;
        this.state.isResizing = false;
        this.state.resizeHandle = null;
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
    
    async saveElement(element, extra = {}, persist = false) {
        Object.assign(element, extra);
        element.modified = true;
        this.state.unsavedChanges = true;
        this.refreshObjectFromElement(element);
        if (!persist) return;
        try {
            const payload = {
                x: element.x,
                y: element.y,
                width: element.width,
                height: element.height,
                z_index: element.z_index,
                visible: element.visible,
                rotation: element.rotation,
                content: element.content,
                font_size: element.font_size,
                font_family_name: element.font_family_name,
                font_weight: element.font_weight,
                text_align: element.text_align,
                color: element.color,
                background_color: element.background_color,
            };
            await this.orm.write("invoice.template.element", [element.id], payload);
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
        if (this.fabricReady) this.setZoom(this.state.zoom);
        this.renderCanvas();
    }
    
    zoomOut() {
        this.state.zoom = Math.max(this.state.zoom - 0.1, 0.5);
        if (this.fabricReady) this.setZoom(this.state.zoom);
        this.renderCanvas();
    }
    
    toggleGrid() {
        this.state.showGrid = !this.state.showGrid;
        this.updateGridBackground();
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
        if (this.fabricReady) this.setZoom(this.state.zoom);
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
        const obj = this.elementObjects.get(element.id);
        if (obj && this.fabricCanvas) {
            this.fabricCanvas.setActiveObject(obj);
            this.fabricCanvas.requestRenderAll();
        }
        this.renderCanvas();
    }
    
    toggleElementVisibility(element) {
        element.visible = element.visible !== false ? false : true;
        this.saveElement(element, { visible: element.visible });
        const obj = this.elementObjects.get(element.id);
        if (obj) {
            obj.set({ visible: element.visible !== false, opacity: element.visible === false ? 0 : 1, evented: element.visible !== false });
        }
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
        this.state.selectedElement.modified = true;
        this.state.unsavedChanges = true;
        this.refreshObjectFromElement(this.state.selectedElement);
        this.addToHistory();
    }
    
    alignCenter() {
        if (!this.state.selectedElement || !this.state.template) return;
        const centerX = (this.state.template.page_width - this.state.selectedElement.width) / 2;
        this.state.selectedElement.x = centerX;
        this.state.selectedElement.modified = true;
        this.state.unsavedChanges = true;
        this.refreshObjectFromElement(this.state.selectedElement);
        this.addToHistory();
    }
    
    alignRight() {
        if (!this.state.selectedElement || !this.state.template) return;
        this.state.selectedElement.x = this.state.template.page_width - this.state.selectedElement.width - 10;
        this.state.selectedElement.modified = true;
        this.state.unsavedChanges = true;
        this.refreshObjectFromElement(this.state.selectedElement);
        this.addToHistory();
    }
    
    // ================ LAYER OPERATIONS ================
    
    async bringToFront() {
        if (!this.state.selectedElement) return;
        const maxZ = Math.max(...this.state.elements.map(e => e.z_index || 1));
        this.state.selectedElement.z_index = maxZ + 1;
        await this.saveElement(this.state.selectedElement);
        this.state.elements = [...this.state.elements].sort((a, b) => a.z_index - b.z_index);
        this.buildFabricScene();
    }
    
    async sendToBack() {
        if (!this.state.selectedElement) return;
        const minZ = Math.min(...this.state.elements.map(e => e.z_index || 1));
        this.state.selectedElement.z_index = minZ - 1;
        await this.saveElement(this.state.selectedElement);
        this.state.elements = [...this.state.elements].sort((a, b) => a.z_index - b.z_index);
        this.buildFabricScene();
    }
    
    // ================ PROPERTY CHANGES ================
    
    onPropertyChange() {
        this.state.unsavedChanges = true;
        if (this.state.selectedElement) {
            this.state.selectedElement.modified = true;
            this.refreshObjectFromElement(this.state.selectedElement);
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
                this.buildFabricScene();
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

    // ================ FABRIC CANVAS ================

    async ensureFabric() {
        if (this.fabricReady) {
            console.log("✅ Fabric already ready");
            return;
        }
        console.log("📥 Attempting to load Fabric.js...");
        const ok = await loadFabricWithFallback();
        if (!ok || !window.fabric) {
            console.warn("⚠️ Fabric.js failed to load; falling back to classic canvas.");
            this.fabricReady = false;
            return;
        }
        console.log("✅ Fabric.js loaded successfully, version:", window.fabric.version);
        ensureGoogleFont("Almarai");
        console.log("✅ Google Font Almarai loaded");
        this.fabricReady = true;
        this.createFabricCanvas();
    }

    createFabricCanvas() {
        if (!this.canvasRef.el) {
            console.error("❌ Cannot create Fabric canvas: canvas element not found");
            return;
        }
        console.log("🎨 Creating Fabric canvas...");
        
        // Remove old event listeners FIRST to avoid conflicts
        this.removeEventListeners();
        
        // Ensure canvas is visible and interactive
        this.canvasRef.el.style.transform = "none";
        this.canvasRef.el.style.transformOrigin = "top left";
        this.canvasRef.el.style.display = "block";
        this.canvasRef.el.style.position = "relative";
        this.canvasRef.el.style.zIndex = "1";
        this.canvasRef.el.style.pointerEvents = "auto";
        
        this.setCanvasSize();
        this.fabricCanvas = new window.fabric.Canvas(this.canvasRef.el, {
            selection: true,
            preserveObjectStacking: true,
            stopContextMenu: true,
            interactive: true,
            enableRetinaScaling: true,
            allowTouchScrolling: false,
            fireRightClick: false,
            uniformScaling: false,
            centeredScaling: false,
            centeredRotation: true,
        });
        console.log("✅ Fabric canvas created");
        
        // Add alignment guidelines (snapping lines)
        this.fabricCanvas.on('object:moving', (e) => {
            this._showAlignmentGuides(e.target);
        });
        this.fabricCanvas.on('object:modified', () => {
            this._hideAlignmentGuides();
        });

        // Fabric event handlers
        this.fabricCanvas.on("selection:created", (e) => {
            console.log("🎯 Selection created:", e.selected);
            this.onFabricSelection(e);
        });
        this.fabricCanvas.on("selection:updated", (e) => {
            console.log("🎯 Selection updated:", e.selected);
            this.onFabricSelection(e);
        });
        this.fabricCanvas.on("selection:cleared", () => {
            console.log("🎯 Selection cleared");
            this.onFabricSelection(null);
        });
        this.fabricCanvas.on("object:moving", (e) => {
            console.log("🚚 Object moving");
            this.onFabricObjectChange(e);
        });
        this.fabricCanvas.on("object:scaling", (e) => {
            console.log("📏 Object scaling");
            this.onFabricObjectChange(e, true);
        });
        this.fabricCanvas.on("object:rotating", (e) => {
            console.log("🔄 Object rotating");
            this.onFabricObjectChange(e);
        });
        this.fabricCanvas.on("object:modified", (e) => {
            console.log("✏️ Object modified");
            this.onFabricObjectModified(e);
        });
        this.fabricCanvas.on("mouse:down", (e) => {
            console.log("🖱️ Mouse down, target:", e.target ? e.target.type : "canvas background", "pointer:", e.pointer);
            if (e.target) {
                console.log("   Object details:", {
                    type: e.target.type,
                    selectable: e.target.selectable,
                    evented: e.target.evented,
                    elementId: e.target.elementId,
                });
            }
        });
        this.fabricCanvas.on("mouse:move", (e) => {
            const obj = this.fabricCanvas.findTarget(e.e);
            if (obj) {
                console.log("🔍 Hovering over:", obj.type, obj.elementId);
            }
        });

        this.updateGridBackground();
        this.setZoom(this.state.zoom);
        
        // Force render
        this.fabricCanvas.requestRenderAll();
        
        // Log canvas state
        console.log("✅ Fabric canvas configured and ready");
        console.log("   Canvas element:", this.canvasRef.el);
        console.log("   Canvas dimensions:", this.fabricCanvas.width, "x", this.fabricCanvas.height);
        console.log("   Canvas interactive:", this.fabricCanvas.interactive);
        console.log("   Canvas selection:", this.fabricCanvas.selection);
        console.log("   Objects count:", this.fabricCanvas.getObjects().length);
        console.log("   First object (if any):", this.fabricCanvas.getObjects()[0]);
    }

    setCanvasSize() {
        if (!this.canvasRef.el || !this.state.template) {
            console.warn("⚠️ setCanvasSize: Missing canvas element or template");
            return;
        }
        const w = (this.state.template.page_width || 210) * MM_TO_PX;
        const h = (this.state.template.page_height || 297) * MM_TO_PX;
        console.log("📐 Setting canvas size:", w, "x", h, "px");
        this.canvasRef.el.width = w;
        this.canvasRef.el.height = h;
        if (this.fabricCanvas) {
            this.fabricCanvas.setWidth(w);
            this.fabricCanvas.setHeight(h);
            this.fabricCanvas.calcOffset();
            console.log("✅ Fabric canvas size updated");
        }
    }

    buildFabricScene() {
        if (!this.fabricCanvas) {
            console.error("❌ buildFabricScene: fabricCanvas not available");
            return;
        }
        console.log("🎨 Building Fabric scene with", this.state.elements.length, "elements");
        this._updatingFabric = true;
        this.fabricCanvas.clear();
        this.elementObjects.clear();

        this.updateGridBackground();
        // Set page background color
        if (this.state.template) {
            this.fabricCanvas.setBackgroundColor(
                this.state.template.background_color || "#ffffff",
                this.fabricCanvas.requestRenderAll.bind(this.fabricCanvas)
            );
            console.log("✅ Background color set:", this.state.template.background_color || "#ffffff");
        }

        this.state.elements.forEach((element, idx) => {
            const obj = this.createFabricObject(element);
            if (obj) {
                obj.elementId = element.id;
                obj.hasControls = true;
                obj.hasBorders = true;
                obj.lockScalingFlip = true;
                obj.transparentCorners = false;
                obj.cornerColor = "#4A90E2";
                obj.cornerStyle = "rect";
                obj.cornerSize = 10;
                obj.borderColor = "#4A90E2";
                obj.padding = 2;
                obj.selectable = true;  // Force selectable
                obj.evented = true;     // Force evented
                obj.hoverCursor = 'move';  // Show it's movable
                this.fabricCanvas.add(obj);
                this.elementObjects.set(element.id, obj);
                console.log(`  ✅ Added element ${idx}:`, element.element_type, element.name, 'selectable:', obj.selectable, 'evented:', obj.evented);
            } else {
                console.warn(`  ⚠️ Failed to create object for element ${idx}:`, element.element_type);
            }
        });

        this.fabricCanvas.requestRenderAll();
        this._updatingFabric = false;
        console.log("✅ Fabric scene built and rendered");
    }

    createFabricObject(element) {
        const left = this._mmToPx(element.x || 0);
        const top = this._mmToPx(element.y || 0);
        const width = this._mmToPx(element.width || 50);
        const height = this._mmToPx(element.height || 20);

        console.log(`Creating ${element.element_type}:`, {
            name: element.name,
            position: `(${left}, ${top})`,
            size: `${width} x ${height}`,
            color: element.color,
            bgColor: element.background_color
        });

        const common = {
            left,
            top,
            width,
            height,
            fill: element.background_color && element.background_color !== "transparent" ? element.background_color : "rgba(240,240,240,0.3)",
            stroke: element.color || "#333",
            strokeWidth: element.border_width || 1,
            angle: element.rotation || 0,
            selectable: true,
            hasRotatingPoint: true,
            objectCaching: false,
        };

        if (element.element_type === "text" || element.element_type === "field") {
            const textObj = new window.fabric.Textbox(element.content || (element.element_type === "field" ? `[${element.field_name || "حقل"}]` : "نص"), {
                ...common,
                fontSize: element.font_size || 14,
                fontFamily: element.font_family_name || "Almarai",
                fontWeight: element.font_weight || "400",
                textAlign: element.text_align || "left",
                fill: element.color || "#000000",
                stroke: "",
                strokeWidth: 0,
                backgroundColor: element.background_color && element.background_color !== "transparent" ? element.background_color : "transparent",
                editable: false,  // Prevent inline editing (confusing in designer)
                lockUniScaling: false,  // Allow free scaling
            });
            // Add double-click to edit text
            textObj.on('mousedblclick', () => {
                textObj.set({ editable: true });
                textObj.enterEditing();
                textObj.selectAll();
            });
            return textObj;
        }

        if (element.element_type === "shape") {
            const shapeFill = element.background_color || "#e0e0e0";
            if (element.shape_type === "circle" || element.shape_type === "ellipse") {
                return new window.fabric.Ellipse({
                    ...common,
                    fill: shapeFill,
                    rx: width / 2,
                    ry: height / 2,
                    originX: "left",
                    originY: "top",
                });
            }
            if (element.shape_type === "triangle") {
                return new window.fabric.Triangle({
                    ...common,
                    fill: shapeFill,
                });
            }
            return new window.fabric.Rect({
                ...common,
                fill: shapeFill,
                rx: element.border_radius || 0,
                ry: element.border_radius || 0,
            });
        }

        if (element.element_type === "line") {
            const x2 = this._mmToPx(element.line_x2 || (element.x || 0) + (element.width || 50));
            const y2 = this._mmToPx(element.line_y2 || (element.y || 0));
            return new window.fabric.Line([left, top, x2, y2], {
                stroke: element.color || "#333333",
                strokeWidth: element.border_width || 2,
                selectable: true,
                hasControls: false,
            });
        }

        if (element.element_type === "table") {
            const rect = new window.fabric.Rect({
                left,
                top,
                width,
                height,
                fill: "#f7f7f7",
                stroke: "#b0b0b0",
                strokeWidth: 1,
                rx: 2,
                ry: 2,
            });
            const text = new window.fabric.Text('جدول المنتجات', {
                left: 0,
                top: 0,
                fontSize: 12,
                fill: '#333',
                fontFamily: 'Almarai',
            });
            const tableGroup = new window.fabric.Group([rect, text], {
                left,
                top,
                selectable: true,
                evented: true,
                hasControls: true,
                hasBorders: true,
                lockScalingFlip: true,
                hoverCursor: 'move',
            });
            return tableGroup;
        }

        if (element.element_type === "barcode" || element.element_type === "qr") {
            const label = element.element_type === "barcode" ? "باركود" : "QR";
            const rect = new window.fabric.Rect({
                left: 0,
                top: 0,
                width,
                height,
                fill: "#ffffff",
                stroke: "#333333",
                strokeWidth: 1,
                rx: 2,
                ry: 2,
            });
            const text = new window.fabric.Text(`[${label}]`, {
                left: width / 2,
                top: height / 2,
                fontSize: 11,
                fill: '#666',
                fontFamily: 'Almarai',
                originX: 'center',
                originY: 'center',
            });
            return new window.fabric.Group([rect, text], {
                left,
                top,
                selectable: true,
                evented: true,
                hasControls: true,
                hasBorders: true,
                hoverCursor: 'move',
            });
        }

        if (element.element_type === "image") {
            const rect = new window.fabric.Rect({
                left: 0,
                top: 0,
                width,
                height,
                fill: "#f0f0f0",
                stroke: "#999",
            });
            
            const loadingText = new window.fabric.Text('[صورة]', {
                left: width / 2,
                top: height / 2,
                fontSize: 11,
                fill: '#999',
                fontFamily: 'Almarai',
                originX: 'center',
                originY: 'center',
            });
            const group = new window.fabric.Group([rect, loadingText], {
                left,
                top,
                selectable: true,
                evented: true,
                hasControls: true,
                hasBorders: true,
                hoverCursor: 'move',
            });
            
            if (element.image_data || element.image_url) {
                const src = element.image_data
                    ? `data:image/png;base64,${element.image_data}`
                    : element.image_url;
                window.fabric.Image.fromURL(src, (img) => {
                    if (img && this.fabricCanvas) {
                        img.set({
                            left,
                            top,
                            scaleX: width / (img.width || 100),
                            scaleY: height / (img.height || 100),
                            selectable: true,
                            hasControls: true,
                        });
                        img.elementId = element.id;
                        this.fabricCanvas.remove(group);
                        this.fabricCanvas.add(img);
                        this.elementObjects.set(element.id, img);
                        this.fabricCanvas.requestRenderAll();
                    }
                }, { crossOrigin: "anonymous" });
            }
            return group;
        }

        if (element.element_type === "gradient_box") {
            const gradient = new window.fabric.Gradient({
                type: "linear",
                gradientUnits: "percentage",
                coords: { x1: 0, y1: 0, x2: 1, y2: 0 },
                colorStops: [
                    { offset: 0, color: "#667eea" },
                    { offset: 1, color: "#764ba2" },
                ],
            });
            return new window.fabric.Rect({
                ...common,
                fill: gradient,
                stroke: "transparent",
            });
        }

        // Default fallback rectangle
        return new window.fabric.Rect({ ...common });
    }

    onFabricSelection(event) {
        if (this._updatingFabric) return;
        const obj = event && event.selected ? event.selected[0] : null;
        if (!obj || !obj.elementId) {
            this.state.selectedElement = null;
            this.fabricCanvas?.requestRenderAll();
            return;
        }
        const element = this.state.elements.find((el) => el.id === obj.elementId);
        if (element) {
            this.state.selectedElement = element;
        }
        this.fabricCanvas?.requestRenderAll();
    }

    onFabricObjectChange(event, isScaling = false) {
        if (this._updatingFabric) return;
        const obj = event.target;
        if (!obj || !obj.elementId) return;

        if (this.state.snapToGrid) {
            const grid = this.GRID_MM * MM_TO_PX;
            obj.set({
                left: Math.round(obj.left / grid) * grid,
                top: Math.round(obj.top / grid) * grid,
            });
            if (isScaling && obj.type !== "line") {
                obj.set({
                    width: Math.max(grid, Math.round(obj.width * obj.scaleX / grid) * grid),
                    height: Math.max(grid, Math.round(obj.height * obj.scaleY / grid) * grid),
                    scaleX: 1,
                    scaleY: 1,
                });
            }
        }

        this.updateElementFromObject(obj);
        this.fabricCanvas.requestRenderAll();
    }

    onFabricObjectModified(event) {
        if (this._updatingFabric) return;
        const obj = event.target;
        if (!obj || !obj.elementId) return;
        this.updateElementFromObject(obj);
        this.addToHistory();
    }

    updateElementFromObject(obj) {
        const element = this.state.elements.find((el) => el.id === obj.elementId);
        if (!element) return;

        if (obj.type === "line") {
            const [x1, y1, x2, y2] = obj.calcLinePoints ? obj.calcLinePoints() : [0, 0, obj.width, obj.height];
            element.x = this._pxToMm(obj.left + x1);
            element.y = this._pxToMm(obj.top + y1);
            element.line_x2 = this._pxToMm(obj.left + x2);
            element.line_y2 = this._pxToMm(obj.top + y2);
            element.width = this._pxToMm(Math.abs(x2 - x1));
            element.height = this._pxToMm(Math.abs(y2 - y1) || (element.height || 2));
        } else {
            element.x = this._pxToMm(obj.left);
            element.y = this._pxToMm(obj.top);
            element.width = this._pxToMm(obj.getScaledWidth ? obj.getScaledWidth() : obj.width);
            element.height = this._pxToMm(obj.getScaledHeight ? obj.getScaledHeight() : obj.height);
            element.rotation = obj.angle || 0;
        }

        element.modified = true;
        this.state.unsavedChanges = true;
        this.state.selectedElement = element;
    }

    refreshObjectFromElement(element) {
        const obj = this.elementObjects.get(element.id);
        if (!obj) return;
        this._updatingFabric = true;
        obj.set({
            left: this._mmToPx(element.x || 0),
            top: this._mmToPx(element.y || 0),
            angle: element.rotation || 0,
        });

        if (obj.type !== "line") {
            obj.set({
                width: this._mmToPx(element.width || 50),
                height: this._mmToPx(element.height || 20),
                scaleX: 1,
                scaleY: 1,
            });
        }

        if (obj.type === "textbox") {
            obj.set({
                text: element.content || "",
                fontSize: element.font_size || 14,
                fontFamily: element.font_family_name || "Almarai",
                fontWeight: element.font_weight || "400",
                textAlign: element.text_align || "left",
                fill: element.color || "#000",
                backgroundColor: element.background_color || "transparent",
            });
        }

        if (obj.type === "rect" || obj.type === "ellipse" || obj.type === "triangle") {
            obj.set({
                fill: element.background_color && element.background_color !== "transparent" ? element.background_color : "rgba(255,255,255,0)",
                stroke: element.color || "#000",
                strokeWidth: element.border_width || 0.5,
            });
        }

        this._updatingFabric = false;
        this.fabricCanvas.requestRenderAll();
    }

    updateGridBackground() {
        if (!this.fabricCanvas) return;
        if (!this.state.showGrid) {
            this.fabricCanvas.setBackgroundImage(null, this.fabricCanvas.requestRenderAll.bind(this.fabricCanvas));
            if (this.state.template) {
                this.fabricCanvas.setBackgroundColor(
                    this.state.template.background_color || "#ffffff",
                    this.fabricCanvas.requestRenderAll.bind(this.fabricCanvas)
                );
            }
            return;
        }
        const gridSize = this.GRID_MM * MM_TO_PX;
        const gridCanvas = document.createElement("canvas");
        gridCanvas.width = gridSize;
        gridCanvas.height = gridSize;
        const ctx = gridCanvas.getContext("2d");
        ctx.strokeStyle = "rgba(0,0,0,0.08)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(gridSize, 0);
        ctx.lineTo(gridSize, gridSize);
        ctx.moveTo(0, gridSize);
        ctx.lineTo(gridSize, gridSize);
        ctx.stroke();

        const pattern = new window.fabric.Pattern({
            source: gridCanvas,
            repeat: "repeat",
        });
        this.fabricCanvas.setBackgroundColor(pattern, this.fabricCanvas.requestRenderAll.bind(this.fabricCanvas));
    }

    setZoom(zoom) {
        if (!this.fabricCanvas) return;
        const vpt = this.fabricCanvas.viewportTransform;
        if (!vpt) return;
        const center = this.fabricCanvas.getCenter();
        this.fabricCanvas.zoomToPoint(new window.fabric.Point(center.left, center.top), zoom);
        this.fabricCanvas.requestRenderAll();
    }

    _mmToPx(mm) {
        return (mm || 0) * MM_TO_PX;
    }

    _pxToMm(px) {
        return (px || 0) / MM_TO_PX;
    }
    
    // ================ ALIGNMENT GUIDES ================
    
    _showAlignmentGuides(activeObject) {
        if (!this.fabricCanvas || !activeObject) return;
        
        const canvasObjects = this.fabricCanvas.getObjects().filter(obj => obj !== activeObject && obj.id !== 'vertical-guide' && obj.id !== 'horizontal-guide');
        const activeCenter = activeObject.getCenterPoint();
        const activeBounds = activeObject.getBoundingRect();
        
        const snapDistance = 5; // pixels
        let verticalLine = null;
        let horizontalLine = null;
        
        // Check alignment with other objects
        for (const obj of canvasObjects) {
            const objCenter = obj.getCenterPoint();
            const objBounds = obj.getBoundingRect();
            
            // Vertical center alignment
            if (Math.abs(activeCenter.x - objCenter.x) < snapDistance) {
                activeObject.set({ left: objCenter.x - activeObject.width / 2 });
                verticalLine = objCenter.x;
            }
            // Left edge alignment
            else if (Math.abs(activeBounds.left - objBounds.left) < snapDistance) {
                activeObject.set({ left: objBounds.left });
                verticalLine = objBounds.left;
            }
            // Right edge alignment
            else if (Math.abs(activeBounds.left + activeBounds.width - (objBounds.left + objBounds.width)) < snapDistance) {
                activeObject.set({ left: objBounds.left + objBounds.width - activeBounds.width });
                verticalLine = objBounds.left + objBounds.width;
            }
            
            // Horizontal center alignment
            if (Math.abs(activeCenter.y - objCenter.y) < snapDistance) {
                activeObject.set({ top: objCenter.y - activeObject.height / 2 });
                horizontalLine = objCenter.y;
            }
            // Top edge alignment
            else if (Math.abs(activeBounds.top - objBounds.top) < snapDistance) {
                activeObject.set({ top: objBounds.top });
                horizontalLine = objBounds.top;
            }
            // Bottom edge alignment
            else if (Math.abs(activeBounds.top + activeBounds.height - (objBounds.top + objBounds.height)) < snapDistance) {
                activeObject.set({ top: objBounds.top + objBounds.height - activeBounds.height });
                horizontalLine = objBounds.top + objBounds.height;
            }
        }
        
        // Draw guide lines
        this._hideAlignmentGuides();
        
        if (verticalLine !== null) {
            const line = new window.fabric.Line([verticalLine, 0, verticalLine, this.fabricCanvas.height], {
                stroke: '#4A90E2',
                strokeWidth: 1,
                strokeDashArray: [5, 5],
                selectable: false,
                evented: false,
                id: 'vertical-guide'
            });
            this.fabricCanvas.add(line);
            this.fabricCanvas.renderAll();
        }
        
        if (horizontalLine !== null) {
            const line = new window.fabric.Line([0, horizontalLine, this.fabricCanvas.width, horizontalLine], {
                stroke: '#4A90E2',
                strokeWidth: 1,
                strokeDashArray: [5, 5],
                selectable: false,
                evented: false,
                id: 'horizontal-guide'
            });
            this.fabricCanvas.add(line);
            this.fabricCanvas.renderAll();
        }
    }
    
    _hideAlignmentGuides() {
        if (!this.fabricCanvas) return;
        const objects = this.fabricCanvas.getObjects().filter(obj => 
            obj.id === 'vertical-guide' || obj.id === 'horizontal-guide'
        );
        objects.forEach(obj => this.fabricCanvas.remove(obj));
        this.fabricCanvas.renderAll();
    }

    _getCanvasCoordinates(event) {
        const rect = this.canvasRef.el.getBoundingClientRect();
        const scale = 3.78 * (this.state.zoom || 1);
        return {
            x: (event.clientX - rect.left) / scale,
            y: (event.clientY - rect.top) / scale,
        };
    }

    _snap(value) {
        if (!this.state.snapToGrid) {
            return value;
        }
        return Math.round(value / this.GRID_MM) * this.GRID_MM;
    }

    _getResizeHandle(element, x, y) {
        const tolerance = 3; // mm tolerance around corners
        const nearLeft = Math.abs(x - element.x) <= tolerance;
        const nearRight = Math.abs(x - (element.x + element.width)) <= tolerance;
        const nearTop = Math.abs(y - element.y) <= tolerance;
        const nearBottom = Math.abs(y - (element.y + element.height)) <= tolerance;

        if (nearTop && nearLeft) return 'nw';
        if (nearTop && nearRight) return 'ne';
        if (nearBottom && nearLeft) return 'sw';
        if (nearBottom && nearRight) return 'se';
        return null;
    }
}

registry.category("actions").add("invoice_designer_canvas", InvoiceDesignerCanvas);

