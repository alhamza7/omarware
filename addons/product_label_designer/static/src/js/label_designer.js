/** @odoo-module **/

// Label Designer - Drag & Drop Visual Editor

class LabelDesigner {
    constructor(containerId, templateData) {
        this.container = document.getElementById(containerId);
        this.templateData = templateData;
        this.canvas = null;
        this.activeElement = null;
        this.isDragging = false;
        this.isResizing = false;
        this.startX = 0;
        this.startY = 0;
        this.mmToPixel = 3.7795275591; // 1mm = ~3.78px at 96 DPI
        
        this.init();
    }
    
    init() {
        this.createCanvas();
        this.createElements();
        this.setupEventListeners();
        this.setupImageUploads();
        this.loadPositions();
    }
    
    createCanvas() {
        const width = this.templateData.label_width * this.mmToPixel;
        const height = this.templateData.label_height * this.mmToPixel;
        
        this.canvas = document.createElement('div');
        this.canvas.className = 'designer-canvas';
        this.canvas.style.width = width + 'px';
        this.canvas.style.height = height + 'px';
        this.canvas.style.backgroundColor = this.templateData.bg_color || '#FFFFFF';
        
        // Add background image if exists
        if (this.templateData.background_image) {
            this.canvas.style.backgroundImage = `url(data:image/png;base64,${this.templateData.background_image})`;
            this.canvas.style.backgroundSize = 'cover';
            this.canvas.style.backgroundPosition = 'center';
        }
        
        // Add grid overlay
        const grid = document.createElement('div');
        grid.className = 'grid-overlay';
        this.canvas.appendChild(grid);
        
        const canvasArea = document.querySelector('.designer-canvas-area');
        if (canvasArea) {
            canvasArea.appendChild(this.canvas);
        }
    }
    
    createElements() {
        const elements = [];
        
        // Convert string booleans to actual booleans
        const showName = this.templateData.show_name === true || this.templateData.show_name === 'true';
        const showForeignName = this.templateData.show_foreign_name === true || this.templateData.show_foreign_name === 'true';
        const showCode = this.templateData.show_code === true || this.templateData.show_code === 'true';
        const showPrice = this.templateData.show_price === true || this.templateData.show_price === 'true';
        const showBarcode = this.templateData.show_barcode === true || this.templateData.show_barcode === 'true';
        const showQR = this.templateData.show_qr === true || this.templateData.show_qr === 'true';
        const showLogo = this.templateData.show_logo === true || this.templateData.show_logo === 'true';
        
        console.log('Template Data:', this.templateData);
        console.log('Show QR:', showQR, '(original:', this.templateData.show_qr, ')');
        console.log('Show Logo:', showLogo, 'Has logo image:', !!this.templateData.logo_image);
        
        if (showName) {
            elements.push({
                id: 'product-name',
                label: 'Product Name',
                icon: '📝',
                x: this.templateData.name_x,
                y: this.templateData.name_y,
                content: 'عطر الورد',
                style: {
                    fontSize: `${this.templateData.font_size_name}pt`,
                    color: this.templateData.text_color,
                    fontWeight: 'bold',
                }
            });
        }
        
        if (showForeignName) {
            elements.push({
                id: 'foreign-name',
                label: 'Foreign Name',
                icon: '🌐',
                x: this.templateData.foreign_name_x,
                y: this.templateData.foreign_name_y,
                content: 'Rose Perfume',
                style: {
                    fontSize: `${this.templateData.font_size_name - 2}pt`,
                    color: this.templateData.text_color,
                }
            });
        }
        
        if (showCode) {
            elements.push({
                id: 'product-code',
                label: 'Product Code',
                icon: '#️⃣',
                x: this.templateData.code_x,
                y: this.templateData.code_y,
                content: 'S-001',
                style: {
                    fontSize: `${this.templateData.font_size_code}pt`,
                    color: this.templateData.text_color,
                    fontWeight: 'bold',
                }
            });
        }
        
        if (showPrice) {
            elements.push({
                id: 'product-price',
                label: 'Price',
                icon: '💰',
                x: this.templateData.price_x,
                y: this.templateData.price_y,
                content: '99.99 ريال',
                style: {
                    fontSize: `${this.templateData.font_size_price}pt`,
                    color: this.templateData.price_color,
                    fontWeight: '900',
                }
            });
        }
        
        if (showBarcode) {
            elements.push({
                id: 'barcode',
                label: 'Barcode',
                icon: '📊',
                x: this.templateData.barcode_x,
                y: this.templateData.barcode_y,
                content: '||||| ||||| |||||',
                style: {
                    fontSize: '14pt',
                    fontFamily: 'monospace',
                }
            });
        }
        
        if (showQR) {
            console.log('Adding QR Code element at:', this.templateData.qr_x, this.templateData.qr_y);
            elements.push({
                id: 'qr-code',
                label: 'QR Code',
                icon: '📱',
                x: this.templateData.qr_x || 60.0,
                y: this.templateData.qr_y || 45.0,
                content: '▀▀▀\n▀▀▀\n▀▀▀',
                isQR: true,
                size: this.templateData.qr_size || 15.0,
                style: {
                    fontSize: '10pt',
                    fontFamily: 'monospace',
                    textAlign: 'center',
                    lineHeight: '0.9',
                    border: '2px solid #333',
                    whiteSpace: 'pre',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: 'transparent',
                }
            });
        }
        
        if (showLogo && this.templateData.logo_image) {
            console.log('Adding Logo element');
            elements.push({
                id: 'logo',
                label: 'Logo',
                icon: '🏷️',
                x: this.templateData.logo_x || 5.0,
                y: this.templateData.logo_y || 5.0,
                isImage: true,
                width: this.templateData.logo_width || 20.0,
                height: this.templateData.logo_height || 15.0,
                src: `data:image/png;base64,${this.templateData.logo_image}`,
            });
        }
        
        console.log('Total elements to create:', elements.length);
        elements.forEach(el => {
            console.log('Creating element:', el.id, el.label);
            this.createElement(el);
        });
    }
    
    createElement(data) {
        const element = document.createElement('div');
        element.className = 'draggable-element';
        element.dataset.id = data.id;
        element.dataset.label = data.label;
        
        const x = data.x * this.mmToPixel;
        const y = data.y * this.mmToPixel;
        
        element.style.left = x + 'px';
        element.style.top = y + 'px';
        
        if (data.isImage) {
            const img = document.createElement('img');
            img.src = data.src;
            img.style.width = (data.width * this.mmToPixel) + 'px';
            img.style.height = (data.height * this.mmToPixel) + 'px';
            img.style.objectFit = 'contain';
            element.appendChild(img);
        } else if (data.isQR) {
            const size = (data.size * this.mmToPixel) + 'px';
            element.style.width = size;
            element.style.height = size;
            element.textContent = data.content;
            Object.assign(element.style, data.style);
        } else {
            element.textContent = data.content;
            Object.assign(element.style, data.style);
        }
        
        // Add resize handle
        const resizeHandle = document.createElement('div');
        resizeHandle.className = 'resize-handle';
        element.appendChild(resizeHandle);
        
        this.canvas.appendChild(element);
        
        // Add to sidebar list
        this.addToElementList(data);
    }
    
    addToElementList(data) {
        const list = document.querySelector('.element-list');
        if (!list) return;
        
        const item = document.createElement('li');
        item.className = 'element-list-item';
        item.dataset.id = data.id;
        
        item.innerHTML = `
            <span>
                <span class="element-icon">${data.icon}</span>
                ${data.label}
            </span>
            <span class="text-muted">${data.x.toFixed(1)}, ${data.y.toFixed(1)} mm</span>
        `;
        
        item.addEventListener('click', () => {
            this.selectElement(data.id);
        });
        
        list.appendChild(item);
    }
    
    setupEventListeners() {
        this.canvas.addEventListener('mousedown', this.onMouseDown.bind(this));
        document.addEventListener('mousemove', this.onMouseMove.bind(this));
        document.addEventListener('mouseup', this.onMouseUp.bind(this));
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (!this.activeElement) return;
            
            const step = e.shiftKey ? 10 : 1; // 10mm if shift, 1mm otherwise
            const px = step * this.mmToPixel;
            
            switch(e.key) {
                case 'ArrowLeft':
                    this.moveElement(-px, 0);
                    e.preventDefault();
                    break;
                case 'ArrowRight':
                    this.moveElement(px, 0);
                    e.preventDefault();
                    break;
                case 'ArrowUp':
                    this.moveElement(0, -px);
                    e.preventDefault();
                    break;
                case 'ArrowDown':
                    this.moveElement(0, px);
                    e.preventDefault();
                    break;
            }
        });
    }
    
    setupImageUploads() {
        // Background upload
        const backgroundInput = document.getElementById('background-upload');
        if (backgroundInput) {
            backgroundInput.addEventListener('change', (e) => {
                this.handleImageUpload(e, 'background');
            });
        }
        
        // Logo upload
        const logoInput = document.getElementById('logo-upload');
        if (logoInput) {
            logoInput.addEventListener('change', (e) => {
                this.handleImageUpload(e, 'logo');
            });
        }
    }
    
    handleImageUpload(event, imageType) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Check file size (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
            alert('File size too large. Maximum 5MB.');
            return;
        }
        
        // Check file type
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file.');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = (e) => {
            const base64 = e.target.result.split(',')[1]; // Remove data:image/... prefix
            
            this.rpc('/label_designer/upload_image', {
                template_id: this.templateData.id,
                image_type: imageType,
                image_data: base64
            }).then(result => {
                if (result.success) {
                    // Update preview
                    this.updateImagePreview(imageType, e.target.result);
                    
                    // Update canvas background/logo
                    if (imageType === 'background') {
                        this.canvas.style.backgroundImage = `url(${e.target.result})`;
                        this.canvas.style.backgroundSize = 'cover';
                        this.canvas.style.backgroundPosition = 'center';
                        this.templateData.background_image = base64;
                    } else if (imageType === 'logo') {
                        this.templateData.logo_image = base64;
                        // Recreate logo element
                        this.recreateLogoElement();
                    }
                    
                    console.log(`${imageType} uploaded successfully`);
                    alert(`${imageType === 'background' ? 'Background' : 'Logo'} uploaded successfully!`);
                } else {
                    alert('Failed to upload image: ' + (result.error || 'Unknown error'));
                }
            });
        };
        
        reader.readAsDataURL(file);
        
        // Clear input so same file can be uploaded again
        event.target.value = '';
    }
    
    updateImagePreview(imageType, dataUrl) {
        const previewId = imageType === 'background' ? 'background-preview' : 'logo-preview';
        const preview = document.getElementById(previewId);
        
        if (preview) {
            preview.innerHTML = `<img src="${dataUrl}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 5px;" alt="${imageType}"/>`;
        }
    }
    
    removeImage(imageType) {
        if (!confirm(`Remove ${imageType}?`)) return;
        
        this.rpc('/label_designer/remove_image', {
            template_id: this.templateData.id,
            image_type: imageType
        }).then(result => {
            if (result.success) {
                const previewId = imageType === 'background' ? 'background-preview' : 'logo-preview';
                const preview = document.getElementById(previewId);
                
                if (preview) {
                    preview.innerHTML = `<div style="padding: 20px; background: #f5f5f5; border: 1px dashed #ccc; border-radius: 4px; text-align: center; color: #999;">No ${imageType}</div>`;
                }
                
                if (imageType === 'background') {
                    this.canvas.style.backgroundImage = 'none';
                    this.templateData.background_image = null;
                } else if (imageType === 'logo') {
                    this.templateData.logo_image = null;
                    // Remove logo element
                    const logoElement = this.canvas.querySelector('[data-id="logo"]');
                    if (logoElement) {
                        logoElement.remove();
                    }
                }
                
                alert(`${imageType === 'background' ? 'Background' : 'Logo'} removed successfully!`);
            }
        });
    }
    
    recreateLogoElement() {
        // Remove old logo if exists
        const oldLogo = this.canvas.querySelector('[data-id="logo"]');
        if (oldLogo) {
            oldLogo.remove();
        }
        
        // Remove from element list
        const oldListItem = document.querySelector('.element-list-item[data-id="logo"]');
        if (oldListItem) {
            oldListItem.remove();
        }
        
        // Create new logo with updated image
        const showLogo = this.templateData.show_logo === true || this.templateData.show_logo === 'true';
        if (showLogo && this.templateData.logo_image) {
            this.createElement({
                id: 'logo',
                label: 'Logo',
                icon: '🏷️',
                x: this.templateData.logo_x,
                y: this.templateData.logo_y,
                isImage: true,
                width: this.templateData.logo_width,
                height: this.templateData.logo_height,
                src: `data:image/png;base64,${this.templateData.logo_image}`,
            });
        }
    }
    
    onMouseDown(e) {
        if (e.target.classList.contains('grid-overlay')) return;
        
        const element = e.target.closest('.draggable-element');
        if (!element) {
            this.deselectAll();
            return;
        }
        
        this.activeElement = element;
        this.selectElement(element.dataset.id);
        
        if (e.target.classList.contains('resize-handle')) {
            this.isResizing = true;
        } else {
            this.isDragging = true;
        }
        
        this.startX = e.clientX;
        this.startY = e.clientY;
        
        e.preventDefault();
    }
    
    onMouseMove(e) {
        if (!this.activeElement) return;
        
        const dx = e.clientX - this.startX;
        const dy = e.clientY - this.startY;
        
        if (this.isDragging) {
            const currentLeft = parseFloat(this.activeElement.style.left) || 0;
            const currentTop = parseFloat(this.activeElement.style.top) || 0;
            
            this.activeElement.style.left = (currentLeft + dx) + 'px';
            this.activeElement.style.top = (currentTop + dy) + 'px';
            
            this.startX = e.clientX;
            this.startY = e.clientY;
            
            this.updatePositionInputs();
        }
        
        if (this.isResizing) {
            const img = this.activeElement.querySelector('img');
            if (img) {
                const currentWidth = parseFloat(img.style.width) || 0;
                const currentHeight = parseFloat(img.style.height) || 0;
                
                img.style.width = Math.max(20, currentWidth + dx) + 'px';
                img.style.height = Math.max(20, currentHeight + dy) + 'px';
                
                this.startX = e.clientX;
                this.startY = e.clientY;
            }
        }
    }
    
    onMouseUp() {
        if (this.isDragging || this.isResizing) {
            this.savePositions();
        }
        
        this.isDragging = false;
        this.isResizing = false;
    }
    
    selectElement(id) {
        this.deselectAll();
        
        const element = this.canvas.querySelector(`[data-id="${id}"]`);
        if (element) {
            element.classList.add('active');
            this.activeElement = element;
            this.updatePositionInputs();
        }
        
        // Highlight in sidebar
        document.querySelectorAll('.element-list-item').forEach(item => {
            item.classList.toggle('active', item.dataset.id === id);
        });
    }
    
    deselectAll() {
        this.canvas.querySelectorAll('.draggable-element').forEach(el => {
            el.classList.remove('active');
        });
        
        document.querySelectorAll('.element-list-item').forEach(item => {
            item.classList.remove('active');
        });
        
        this.activeElement = null;
    }
    
    moveElement(dx, dy) {
        if (!this.activeElement) return;
        
        const currentLeft = parseFloat(this.activeElement.style.left) || 0;
        const currentTop = parseFloat(this.activeElement.style.top) || 0;
        
        this.activeElement.style.left = (currentLeft + dx) + 'px';
        this.activeElement.style.top = (currentTop + dy) + 'px';
        
        this.updatePositionInputs();
        this.savePositions();
    }
    
    updatePositionInputs() {
        if (!this.activeElement) return;
        
        const x = (parseFloat(this.activeElement.style.left) || 0) / this.mmToPixel;
        const y = (parseFloat(this.activeElement.style.top) || 0) / this.mmToPixel;
        
        const xInput = document.querySelector('[name="position_x"]');
        const yInput = document.querySelector('[name="position_y"]');
        
        if (xInput) xInput.value = x.toFixed(1);
        if (yInput) yInput.value = y.toFixed(1);
        
        // Update sidebar list
        const listItem = document.querySelector(`.element-list-item[data-id="${this.activeElement.dataset.id}"]`);
        if (listItem) {
            const coordSpan = listItem.querySelector('.text-muted');
            if (coordSpan) {
                coordSpan.textContent = `${x.toFixed(1)}, ${y.toFixed(1)} mm`;
            }
        }
    }
    
    loadPositions() {
        // Positions are already set during createElement
    }
    
    savePositions() {
        const positions = {};
        
        this.canvas.querySelectorAll('.draggable-element').forEach(el => {
            const id = el.dataset.id;
            const x = (parseFloat(el.style.left) || 0) / this.mmToPixel;
            const y = (parseFloat(el.style.top) || 0) / this.mmToPixel;
            
            const fieldMap = {
                'product-name': ['name_x', 'name_y'],
                'foreign-name': ['foreign_name_x', 'foreign_name_y'],
                'product-code': ['code_x', 'code_y'],
                'product-price': ['price_x', 'price_y'],
                'barcode': ['barcode_x', 'barcode_y'],
                'qr-code': ['qr_x', 'qr_y'],
                'logo': ['logo_x', 'logo_y'],
            };
            
            if (fieldMap[id]) {
                positions[fieldMap[id][0]] = x;
                positions[fieldMap[id][1]] = y;
                
                // Handle logo size
                if (id === 'logo') {
                    const img = el.querySelector('img');
                    if (img) {
                        positions['logo_width'] = parseFloat(img.style.width) / this.mmToPixel;
                        positions['logo_height'] = parseFloat(img.style.height) / this.mmToPixel;
                    }
                }
                
                // Handle QR size
                if (id === 'qr-code') {
                    const size = parseFloat(el.style.width) / this.mmToPixel;
                    positions['qr_size'] = size;
                }
            }
        });
        
        // Save to server
        this.rpc('/label_designer/save_positions', {
            template_id: this.templateData.id,
            positions: positions
        }).then(result => {
            if (result.success) {
                console.log('Positions saved successfully');
            }
        });
    }
    
    rpc(route, params) {
        return fetch(route, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: params,
                id: new Date().getTime(),
            }),
        }).then(response => response.json())
          .then(data => data.result || {});
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const designerContainer = document.getElementById('label-designer');
    if (designerContainer && window.templateData) {
        window.labelDesigner = new LabelDesigner('label-designer', window.templateData);
    }
});

