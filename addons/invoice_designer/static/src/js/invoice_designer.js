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
        this.router = useService("router");
        
        // Get templateId from multiple sources
        let templateId = null;
        
        // 1. Try from URL hash parameters (most reliable)
        const hash = window.location.hash;
        if (hash) {
            const match = hash.match(/template_id=(\d+)/);
            if (match) {
                templateId = parseInt(match[1]);
                console.log("Template ID from URL:", templateId);
            }
        }
        
        // 2. Try from router current hash
        if (!templateId && this.router && this.router.current && this.router.current.hash) {
            const hashObj = this.router.current.hash;
            templateId = hashObj.template_id || hashObj.templateId;
            console.log("Template ID from router:", templateId);
        }
        
        // 3. Try from props (fallback)
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
            console.log("Template ID from props:", templateId);
        }
        
        console.log("Final Template ID:", templateId);
        console.log("Props received:", this.props);
        
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
            isDragging: false,
            dragOffset: { x: 0, y: 0 },
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
                ["name", "element_type", "x", "y", "width", "height", "content", 
                 "color", "background_color", "font_size", "z_index"]
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
            this.drawElement(ctx, element);
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
}

registry.category("actions").add("invoice_designer_canvas", InvoiceDesignerCanvas);

