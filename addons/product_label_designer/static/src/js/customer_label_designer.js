/** @odoo-module **/

// Customer Label Designer - Drag & Drop Visual Editor

class CustomerLabelDesigner {
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
        this.canvas.id = 'designer-canvas';
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
        const showName = this.templateData.show_name === true || this.templateData.show_name === 'true' || this.templateData.show_name === true;
        const showPhone = this.templateData.show_phone === true || this.templateData.show_phone === 'true' || this.templateData.show_phone === true;
        const showMobile = this.templateData.show_mobile === true || this.templateData.show_mobile === 'true' || this.templateData.show_mobile === true;
        const showInvoiceType = this.templateData.show_invoice_type === true || this.templateData.show_invoice_type === 'true' || this.templateData.show_invoice_type === true;
        // Force show_note to be checked more carefully
        const showNoteRaw = this.templateData.show_note;
        const showNote = showNoteRaw === true || showNoteRaw === 'true' || showNoteRaw === 'True' || String(showNoteRaw).toLowerCase() === 'true';
        const showLogo = this.templateData.show_logo === true || this.templateData.show_logo === 'true' || this.templateData.show_logo === true;
        
        console.log('Customer Template Data:', this.templateData);
        console.log('Show Name:', showName, 'Show Phone:', showPhone, 'Show Mobile:', showMobile, 'Show Invoice Type:', showInvoiceType, 'Show Note:', showNote);
        console.log('Show Logo:', showLogo, 'Has logo image:', !!this.templateData.logo_image);
        console.log('Show Note from templateData:', this.templateData.show_note, 'Type:', typeof this.templateData.show_note);
        console.log('Show Phone Label:', this.templateData.show_phone_label, 'Show Mobile Label:', this.templateData.show_mobile_label);
        console.log('Note X:', this.templateData.note_x, 'Note Y:', this.templateData.note_y);
        
        if (showName) {
            elements.push({
                id: 'customer-name',
                label: 'Customer Name',
                icon: '👤',
                x: this.templateData.name_x || 5.0,
                y: this.templateData.name_y || 5.0,
                width: this.templateData.name_width || 70.0,
                height: this.templateData.name_height || 10.0,
                content: 'اسم الزبون',
                style: {
                    fontSize: `${this.templateData.font_size_name || 14}pt`,
                    color: this.templateData.name_color || this.templateData.text_color || '#000000',
                    fontWeight: this.templateData.name_bold ? 'bold' : 'normal',
                    fontStyle: this.templateData.name_italic ? 'italic' : 'normal',
                    textAlign: this.templateData.name_align || 'right',
                    direction: this.templateData.name_direction || 'rtl',
                }
            });
        }
        
        if (showPhone) {
            // Check if label should be shown
            const showPhoneLabel = this.templateData.show_phone_label === true || this.templateData.show_phone_label === 'true';
            elements.push({
                id: 'phone',
                label: 'Phone',
                icon: '📞',
                x: this.templateData.phone_x || 5.0,
                y: this.templateData.phone_y || 20.0,
                width: this.templateData.phone_width || 70.0,
                height: this.templateData.phone_height || 8.0,
                content: showPhoneLabel ? 'هاتف: 123456789' : '123456789',
                style: {
                    fontSize: `${this.templateData.font_size_phone || 12}pt`,
                    color: this.templateData.phone_color || this.templateData.text_color || '#000000',
                    fontWeight: this.templateData.phone_bold ? 'bold' : 'normal',
                    fontStyle: this.templateData.phone_italic ? 'italic' : 'normal',
                    textAlign: this.templateData.phone_align || 'right',
                    direction: this.templateData.phone_direction || 'rtl',
                }
            });
        }
        
        if (showMobile) {
            // Check if label should be shown
            const showMobileLabel = this.templateData.show_mobile_label === true || this.templateData.show_mobile_label === 'true';
            elements.push({
                id: 'mobile',
                label: 'Mobile',
                icon: '📱',
                x: this.templateData.mobile_x || 5.0,
                y: this.templateData.mobile_y || 30.0,
                width: this.templateData.mobile_width || 70.0,
                height: this.templateData.mobile_height || 8.0,
                content: showMobileLabel ? 'موبايل: 987654321' : '987654321',
                style: {
                    fontSize: `${this.templateData.font_size_mobile || 12}pt`,
                    color: this.templateData.mobile_color || this.templateData.text_color || '#000000',
                    fontWeight: this.templateData.mobile_bold ? 'bold' : 'normal',
                    fontStyle: this.templateData.mobile_italic ? 'italic' : 'normal',
                    textAlign: this.templateData.mobile_align || 'right',
                    direction: this.templateData.mobile_direction || 'rtl',
                }
            });
        }
        
        if (showInvoiceType) {
            // Check if label should be shown
            const showInvoiceTypeLabel = this.templateData.show_invoice_type_label === true || this.templateData.show_invoice_type_label === 'true';
            elements.push({
                id: 'invoice-type',
                label: 'Invoice Type',
                icon: '📋',
                x: this.templateData.invoice_type_x || 5.0,
                y: this.templateData.invoice_type_y || 40.0,
                width: this.templateData.invoice_type_width || 70.0,
                height: this.templateData.invoice_type_height || 8.0,
                content: showInvoiceTypeLabel ? 'نوع الفاتورة: زبون محل' : 'زبون محل',
                style: {
                    fontSize: `${this.templateData.font_size_invoice_type || 10}pt`,
                    color: this.templateData.invoice_type_color || this.templateData.text_color || '#000000',
                    fontWeight: this.templateData.invoice_type_bold ? 'bold' : 'normal',
                    fontStyle: this.templateData.invoice_type_italic ? 'italic' : 'normal',
                    textAlign: this.templateData.invoice_type_align || 'right',
                    direction: this.templateData.invoice_type_direction || 'rtl',
                }
            });
        }
        
        // Always show notes if show_note is enabled (for visual designer)
        // The actual printing will check if note text exists
        // Force check show_note more carefully
        const showNoteValue = this.templateData.show_note;
        const showNoteFinal = showNoteValue === true || 
                             showNoteValue === 'true' || 
                             showNoteValue === 'True' || 
                             String(showNoteValue).toLowerCase() === 'true' ||
                             showNoteValue === 1;
        
        console.log('🔍 Notes Check - showNoteValue:', showNoteValue, 'type:', typeof showNoteValue, 'showNoteFinal:', showNoteFinal);
        
        if (showNoteFinal) {
            // Check if label should be shown
            const showNoteLabel = this.templateData.show_note_label === true || this.templateData.show_note_label === 'true';
            console.log('✅ Creating Notes element - showNoteFinal:', showNoteFinal, 'note_x:', this.templateData.note_x, 'note_y:', this.templateData.note_y);
            const noteElement = {
                id: 'note',
                label: 'Notes',
                icon: '📝',
                x: this.templateData.note_x || 5.0,
                y: this.templateData.note_y || 50.0,
                width: this.templateData.note_width || 70.0,
                height: this.templateData.note_height || 8.0,
                content: showNoteLabel ? 'ملاحظات: ملاحظة تجريبية' : 'ملاحظة تجريبية',
                style: {
                    fontSize: `${this.templateData.font_size_note || 10}pt`,
                    color: this.templateData.note_color || this.templateData.text_color || '#000000',
                    fontWeight: this.templateData.note_bold ? 'bold' : 'normal',
                    fontStyle: this.templateData.note_italic ? 'italic' : 'normal',
                    textAlign: this.templateData.note_align || 'right',
                    direction: this.templateData.note_direction || 'rtl',
                }
            };
            elements.push(noteElement);
            console.log('✅ Notes element added to elements array, total elements:', elements.length, 'note element:', noteElement);
        } else {
            console.error('❌ Notes NOT added - showNoteFinal is false');
            console.error('   showNoteValue:', showNoteValue, 'type:', typeof showNoteValue);
            console.error('   templateData.show_note:', this.templateData.show_note);
            console.error('   All templateData keys:', Object.keys(this.templateData));
        }
        
        if (showLogo && this.templateData.logo_image) {
            console.log('Adding Logo element');
            elements.push({
                id: 'logo',
                label: 'Logo',
                icon: '🏷️',
                x: this.templateData.logo_x || 50.0,
                y: this.templateData.logo_y || 5.0,
                isImage: true,
                width: this.templateData.logo_width || 20.0,
                height: this.templateData.logo_height || 15.0,
                src: `data:image/png;base64,${this.templateData.logo_image}`,
            });
        }
        
        console.log('Total customer elements to create:', elements.length);
        console.log('Elements list:', elements.map(e => e.id));
        elements.forEach(el => {
            console.log('Creating customer element:', el.id, el.label, 'at position:', el.x, el.y);
            this.createElement(el);
        });
        
        // Verify notes element was created - wait a bit for DOM to update
        setTimeout(() => {
            if (showNote) {
                const noteElement = this.canvas.querySelector('[data-id="note"]');
                if (noteElement) {
                    console.log('✅ Notes element found in canvas at:', noteElement.style.left, noteElement.style.top);
                } else {
                    console.error('❌ Notes element NOT found in canvas even though showNote is true');
                    console.error('Canvas elements:', Array.from(this.canvas.querySelectorAll('.draggable-element')).map(e => e.dataset.id));
                }
            } else {
                console.warn('⚠️ Notes not shown because showNote is false');
            }
        }, 100);
    }
    
    createElement(data) {
        const element = document.createElement('div');
        element.className = 'draggable-element';
        element.dataset.id = data.id;
        element.dataset.label = data.label;
        
        const x = data.x * this.mmToPixel;
        const y = data.y * this.mmToPixel;
        const width = (data.width || 70.0) * this.mmToPixel;
        const height = (data.height || 10.0) * this.mmToPixel;
        
        element.style.left = x + 'px';
        element.style.top = y + 'px';
        element.style.position = 'absolute';
        element.style.width = width + 'px';
        element.style.height = height + 'px';
        element.style.boxSizing = 'border-box';
        
        if (data.isImage) {
            const img = document.createElement('img');
            img.src = data.src;
            img.style.width = '100%';
            img.style.height = '100%';
            img.style.objectFit = 'contain';
            element.appendChild(img);
        } else {
            element.textContent = data.content;
            
            // Set direction first
            const direction = data.style.direction || 'rtl';
            element.setAttribute('dir', direction);
            element.style.direction = direction;
            
            // Set text-align
            const textAlign = data.style.textAlign || 'right';
            element.style.textAlign = textAlign;
            element.setAttribute('data-align', textAlign);
            
            // Apply other styles
            if (data.style.fontSize) element.style.fontSize = data.style.fontSize;
            if (data.style.color) element.style.color = data.style.color;
            if (data.style.fontWeight) element.style.fontWeight = data.style.fontWeight;
            if (data.style.fontStyle) element.style.fontStyle = data.style.fontStyle;
            
            element.style.overflow = 'hidden';
            element.style.wordWrap = 'break-word';
            element.style.whiteSpace = 'normal';
            
            // For center alignment, force LTR direction
            if (textAlign === 'center') {
                element.style.direction = 'ltr';
                element.setAttribute('dir', 'ltr');
            }
        }
        
        // Add resize handle for all elements
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
            
            this.rpc('/label_designer/customer/upload_image', {
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
        
        this.rpc('/label_designer/customer/remove_image', {
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
                x: this.templateData.logo_x || 50.0,
                y: this.templateData.logo_y || 5.0,
                isImage: true,
                width: this.templateData.logo_width || 20.0,
                height: this.templateData.logo_height || 15.0,
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
            const currentWidth = parseFloat(this.activeElement.style.width) || 0;
            const currentHeight = parseFloat(this.activeElement.style.height) || 0;
            
            const newWidth = Math.max(20, currentWidth + dx);
            const newHeight = Math.max(20, currentHeight + dy);
            
            this.activeElement.style.width = newWidth + 'px';
            this.activeElement.style.height = newHeight + 'px';
            
            // Update image if exists
            const img = this.activeElement.querySelector('img');
            if (img) {
                img.style.width = '100%';
                img.style.height = '100%';
            }
            
            this.startX = e.clientX;
            this.startY = e.clientY;
            
            this.updateSizeInputs();
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
            this.updateAlignmentControls();
            this.updateDirectionControls();
            this.updateTestTextControls();
        }
        
        // Highlight in sidebar
        document.querySelectorAll('.element-list-item').forEach(item => {
            item.classList.toggle('active', item.dataset.id === id);
        });
    }
    
    updateAlignmentControls() {
        const alignmentGroup = document.getElementById('text-alignment-group');
        if (!alignmentGroup || !this.activeElement) return;
        
        // Show alignment controls only for text elements (not images)
        const isImage = this.activeElement.querySelector('img') !== null;
        alignmentGroup.style.display = isImage ? 'none' : 'block';
        
        if (!isImage) {
            const currentAlign = this.activeElement.style.textAlign || 
                                window.getComputedStyle(this.activeElement).textAlign || 
                                'right';
            document.querySelectorAll('.align-btn').forEach(btn => {
                btn.classList.toggle('primary', btn.dataset.align === currentAlign);
            });
        }
    }
    
    updateDirectionControls() {
        const directionGroup = document.getElementById('text-direction-group');
        if (!directionGroup || !this.activeElement) return;
        
        // Show direction controls only for text elements (not images)
        const isImage = this.activeElement.querySelector('img') !== null;
        directionGroup.style.display = isImage ? 'none' : 'block';
        
        if (!isImage) {
            const currentDirection = this.activeElement.getAttribute('dir') || 
                                    this.activeElement.style.direction || 
                                    window.getComputedStyle(this.activeElement).direction || 
                                    'rtl';
            document.querySelectorAll('.direction-btn').forEach(btn => {
                btn.classList.toggle('primary', btn.dataset.direction === currentDirection);
            });
        }
    }
    
    changeDirection(direction) {
        if (!this.activeElement) return;
        
        const isImage = this.activeElement.querySelector('img') !== null;
        if (isImage) return;
        
        // If alignment is center, don't allow direction change (center requires LTR)
        const currentAlign = this.activeElement.style.textAlign || 
                            this.activeElement.getAttribute('data-align') || 
                            'right';
        if (currentAlign === 'center') {
            alert('Center alignment requires LTR direction. Please change alignment first.');
            return;
        }
        
        // Store original direction
        if (!this.activeElement.dataset.originalDirection) {
            this.activeElement.dataset.originalDirection = direction;
        }
        
        this.activeElement.style.direction = direction;
        this.activeElement.setAttribute('dir', direction);
        
        // Force reflow to apply changes
        this.activeElement.offsetHeight;
        
        // Update button states
        document.querySelectorAll('.direction-btn').forEach(btn => {
            btn.classList.toggle('primary', btn.dataset.direction === direction);
        });
        
        // Save direction to server
        this.saveDirection(direction);
    }
    
    saveDirection(direction) {
        if (!this.activeElement) return;
        
        const id = this.activeElement.dataset.id;
        const fieldMap = {
            'customer-name': 'name_direction',
            'phone': 'phone_direction',
            'mobile': 'mobile_direction',
            'invoice-type': 'invoice_type_direction',
            'note': 'note_direction',
        };
        
        if (fieldMap[id]) {
            const positions = {};
            positions[fieldMap[id]] = direction;
            
            this.rpc('/label_designer/customer/save_positions', {
                template_id: this.templateData.id,
                positions: positions
            }).then(result => {
                if (result.success) {
                    console.log('Direction saved successfully');
                }
            });
        }
    }
    
    updateTestTextControls() {
        const testTextGroup = document.getElementById('test-text-group');
        const testTextInput = document.getElementById('test-text-input');
        if (!testTextGroup || !testTextInput || !this.activeElement) return;
        
        // Show test text controls only for text elements (not images)
        const isImage = this.activeElement.querySelector('img') !== null;
        testTextGroup.style.display = isImage ? 'none' : 'block';
        
        if (!isImage) {
            // Store original text if not already stored
            if (!this.activeElement.dataset.originalText) {
                this.activeElement.dataset.originalText = this.activeElement.textContent;
            }
            testTextInput.value = this.activeElement.textContent;
        }
    }
    
    changeAlignment(align) {
        if (!this.activeElement) return;
        
        const isImage = this.activeElement.querySelector('img') !== null;
        if (isImage) return;
        
        // Apply alignment
        this.activeElement.style.textAlign = align;
        this.activeElement.setAttribute('data-align', align);
        
        // Get current direction (before changing it)
        let currentDirection = this.activeElement.getAttribute('dir') || 
                              this.activeElement.style.direction || 
                              'rtl';
        
        // When center is selected, use LTR direction to ensure proper centering
        if (align === 'center') {
            currentDirection = 'ltr';
            this.activeElement.style.direction = 'ltr';
            this.activeElement.setAttribute('dir', 'ltr');
            // Update direction button state
            document.querySelectorAll('.direction-btn').forEach(btn => {
                btn.classList.toggle('primary', btn.dataset.direction === 'ltr');
            });
            // Save direction
            this.saveDirection('ltr');
        } else {
            // For right/left, restore the original direction if it was changed for center
            // Otherwise keep current direction
            if (!this.activeElement.dataset.originalDirection) {
                this.activeElement.dataset.originalDirection = currentDirection;
            }
            const originalDirection = this.activeElement.dataset.originalDirection || 'rtl';
            this.activeElement.style.direction = originalDirection;
            this.activeElement.setAttribute('dir', originalDirection);
            // Update direction button state
            document.querySelectorAll('.direction-btn').forEach(btn => {
                btn.classList.toggle('primary', btn.dataset.direction === originalDirection);
            });
        }
        
        // Force reflow to apply changes
        this.activeElement.offsetHeight;
        
        // Update button states
        document.querySelectorAll('.align-btn').forEach(btn => {
            btn.classList.toggle('primary', btn.dataset.align === align);
        });
        
        // Save alignment to server
        this.saveAlignment(align);
    }
    
    saveAlignment(align) {
        if (!this.activeElement) return;
        
        const id = this.activeElement.dataset.id;
        const fieldMap = {
            'customer-name': 'name_align',
            'phone': 'phone_align',
            'mobile': 'mobile_align',
            'invoice-type': 'invoice_type_align',
            'note': 'note_align',
        };
        
        if (fieldMap[id]) {
            const positions = {};
            positions[fieldMap[id]] = align;
            
            this.rpc('/label_designer/customer/save_positions', {
                template_id: this.templateData.id,
                positions: positions
            }).then(result => {
                if (result.success) {
                    console.log('Alignment saved successfully');
                }
            });
        }
    }
    
    applyTestText() {
        const testTextInput = document.getElementById('test-text-input');
        if (!testTextInput || !this.activeElement) return;
        
        const isImage = this.activeElement.querySelector('img') !== null;
        if (isImage) return;
        
        const testText = testTextInput.value.trim();
        if (testText) {
            this.activeElement.textContent = testText;
            // Auto-adjust height based on content
            this.autoAdjustHeight();
        }
    }
    
    resetTestText() {
        if (!this.activeElement) return;
        
        const isImage = this.activeElement.querySelector('img') !== null;
        if (isImage) return;
        
        const originalText = this.activeElement.dataset.originalText;
        if (originalText) {
            this.activeElement.textContent = originalText;
            const testTextInput = document.getElementById('test-text-input');
            if (testTextInput) {
                testTextInput.value = originalText;
            }
            this.autoAdjustHeight();
        }
    }
    
    autoAdjustHeight() {
        if (!this.activeElement) return;
        
        const isImage = this.activeElement.querySelector('img') !== null;
        if (isImage) return;
        
        // Temporarily remove height constraint to measure
        const originalHeight = this.activeElement.style.height;
        this.activeElement.style.height = 'auto';
        
        const contentHeight = this.activeElement.scrollHeight;
        const minHeight = 8 * this.mmToPixel; // Minimum 8mm
        
        // Set height to content or minimum
        this.activeElement.style.height = Math.max(minHeight, contentHeight) + 'px';
        
        // Update size inputs
        this.updatePositionInputs();
        
        // Save new height
        this.savePositions();
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
        const width = (parseFloat(this.activeElement.style.width) || 0) / this.mmToPixel;
        const height = (parseFloat(this.activeElement.style.height) || 0) / this.mmToPixel;
        
        const xInput = document.querySelector('[name="position_x"]');
        const yInput = document.querySelector('[name="position_y"]');
        const widthInput = document.querySelector('[name="size_width"]');
        const heightInput = document.querySelector('[name="size_height"]');
        
        if (xInput) xInput.value = x.toFixed(1);
        if (yInput) yInput.value = y.toFixed(1);
        if (widthInput) widthInput.value = width.toFixed(1);
        if (heightInput) heightInput.value = height.toFixed(1);
        
        // Update sidebar list
        const listItem = document.querySelector(`.element-list-item[data-id="${this.activeElement.dataset.id}"]`);
        if (listItem) {
            const coordSpan = listItem.querySelector('.text-muted');
            if (coordSpan) {
                coordSpan.textContent = `${x.toFixed(1)}, ${y.toFixed(1)} mm (${width.toFixed(1)}×${height.toFixed(1)})`;
            }
        }
    }
    
    updateSizeInputs() {
        this.updatePositionInputs(); // Reuse same function
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
            const width = (parseFloat(el.style.width) || 0) / this.mmToPixel;
            const height = (parseFloat(el.style.height) || 0) / this.mmToPixel;
            
            // Customer label field mapping
            const fieldMap = {
                'customer-name': ['name_x', 'name_y', 'name_width', 'name_height'],
                'phone': ['phone_x', 'phone_y', 'phone_width', 'phone_height'],
                'mobile': ['mobile_x', 'mobile_y', 'mobile_width', 'mobile_height'],
                'invoice-type': ['invoice_type_x', 'invoice_type_y', 'invoice_type_width', 'invoice_type_height'],
                'note': ['note_x', 'note_y', 'note_width', 'note_height'],
                'logo': ['logo_x', 'logo_y', 'logo_width', 'logo_height'],
            };
            
            if (fieldMap[id]) {
                positions[fieldMap[id][0]] = x;
                positions[fieldMap[id][1]] = y;
                positions[fieldMap[id][2]] = width;
                positions[fieldMap[id][3]] = height;
            }
        });
        
        // Save to server
        this.rpc('/label_designer/customer/save_positions', {
            template_id: this.templateData.id,
            positions: positions
        }).then(result => {
            if (result.success) {
                console.log('Customer positions and sizes saved successfully');
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
        window.customerLabelDesigner = new CustomerLabelDesigner('label-designer', window.templateData);
    }
});

// Global functions for buttons
function savePositions() {
    if (window.customerLabelDesigner) {
        window.customerLabelDesigner.savePositions();
    }
}

function removeImage(imageType) {
    if (window.customerLabelDesigner) {
        window.customerLabelDesigner.removeImage(imageType);
    }
}

