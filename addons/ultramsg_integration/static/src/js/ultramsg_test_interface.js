/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { _t } from "@web/core/l10n/translation";

patch(FormController.prototype, {
    setup() {
        super.setup();
    },
    
    onMounted() {
        super.onMounted(...arguments);
        if (this.model.root.resModel === 'ultramsg.config') {
            setTimeout(() => this.setupTestInterface(), 1000);
        }
    },

    setupTestInterface() {
        console.log('[ULTRAMSG] Setting up test interface...');
        
        const messageTypeSelect = document.getElementById('test_message_type');
        const documentFields = document.getElementById('test_document_fields');
        
        if (messageTypeSelect && documentFields) {
            messageTypeSelect.addEventListener('change', function() {
                if (this.value === 'document' || this.value === 'image') {
                    documentFields.style.display = 'block';
                } else {
                    documentFields.style.display = 'none';
                }
            });
        }
        
        const sendButton = document.getElementById('test_send_button');
        if (sendButton) {
            if (!sendButton.hasAttribute('data-listener-added')) {
                console.log('[ULTRAMSG] Adding click listener to button');
                sendButton.setAttribute('data-listener-added', 'true');
                const self = this;
                sendButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('[ULTRAMSG] Button clicked!');
                    self.sendTestMessage();
                });
            } else {
                console.log('[ULTRAMSG] Button already has listener');
            }
        } else {
            console.log('[ULTRAMSG] Button not found!');
        }
    },

    showResult(type, title, message, details) {
        const resultDiv = document.getElementById('test_result');
        const resultTitle = document.getElementById('test_result_title');
        const resultMessage = document.getElementById('test_result_message');
        const resultDetails = document.getElementById('test_result_details');
        
        if (!resultDiv) return;
        
        resultDiv.style.display = 'block';
        
        if (type === 'success') {
            resultDiv.style.backgroundColor = '#d4edda';
            resultDiv.style.border = '1px solid #c3e6cb';
            resultDiv.style.color = '#155724';
        } else {
            resultDiv.style.backgroundColor = '#f8d7da';
            resultDiv.style.border = '1px solid #f5c6cb';
            resultDiv.style.color = '#721c24';
        }
        
        if (resultTitle) resultTitle.textContent = title;
        if (resultMessage) resultMessage.textContent = message;
        if (resultDetails) {
            if (details) {
                resultDetails.innerHTML = `<strong>التفاصيل:</strong><pre style="white-space: pre-wrap; font-size: 11px; max-height: 200px; overflow: auto; background: rgba(0,0,0,0.1); padding: 10px; border-radius: 3px;">${details}</pre>`;
            } else {
                resultDetails.innerHTML = '';
            }
        }
    },

    async sendTestMessage() {
        console.log('[ULTRAMSG] sendTestMessage called');
        
        const phone = document.getElementById('test_phone')?.value?.trim();
        const messageType = document.getElementById('test_message_type')?.value;
        const messageBody = document.getElementById('test_message_body')?.value?.trim();
        const documentUrl = document.getElementById('test_document_url')?.value?.trim();
        const documentName = document.getElementById('test_document_name')?.value?.trim();
        
        console.log('[ULTRAMSG] Input values:', { phone, messageType, messageBody, documentUrl, documentName });
        
        const sendButton = document.getElementById('test_send_button');
        
        // Clear previous result
        const resultDiv = document.getElementById('test_result');
        if (resultDiv) resultDiv.style.display = 'none';
        
        // Validation
        if (!phone) {
            this.showResult('error', '✗ خطأ في الإدخال', 'يرجى إدخال رقم الهاتف', '');
            return;
        }
        
        if (messageType === 'text' && !messageBody) {
            this.showResult('error', '✗ خطأ في الإدخال', 'يرجى إدخال نص الرسالة', '');
            return;
        }
        
        if ((messageType === 'document' || messageType === 'image') && !documentUrl) {
            this.showResult('error', '✗ خطأ في الإدخال', 'يرجى إدخال رابط المستند/الصورة', '');
            return;
        }
        
        // Disable button and show loading
        const originalButtonText = sendButton.innerHTML;
        sendButton.disabled = true;
        sendButton.innerHTML = '<i class="fa fa-spinner fa-spin"/> جاري الإرسال...';
        
        this.showResult('info', '⏳ جاري الإرسال...', 'يرجى الانتظار...', '');
        
        try {
            let recordId = null;
            
            // Try to get from model first (most reliable)
            const record = this.model.root;
            if (record && record.resId) {
                recordId = record.resId;
            }
            
            // Fallback: Try to get from URL hash (most common in Odoo)
            if (!recordId) {
                const hashMatch = window.location.hash.match(/id=(\d+)/);
                if (hashMatch) recordId = hashMatch[1];
            }
            
            // Try from URL params
            if (!recordId) {
                const urlParams = new URLSearchParams(window.location.search);
                recordId = urlParams.get('id');
            }
            
            // Try from form inputs
            if (!recordId) {
                const idInputs = document.querySelectorAll('input[name="id"]');
                for (const input of idInputs) {
                    if (input.value && input.value !== '0' && input.value !== '') {
                        recordId = input.value;
                        break;
                    }
                }
            }
            
            // Try from form data attributes
            if (!recordId) {
                const form = document.querySelector('form.o_form_view');
                if (form) {
                    recordId = form.getAttribute('data-res-id') || form.getAttribute('data-id');
                }
            }
            
            console.log('[ULTRAMSG] Record:', record);
            console.log('[ULTRAMSG] Record ID:', recordId);
            console.log('[ULTRAMSG] URL:', window.location.href);
            
            if (!recordId || recordId === '0' || recordId === '') {
                throw new Error('لا يمكن العثور على معرف السجل. يرجى حفظ الإعدادات أولاً. (URL: ' + window.location.href + ')');
            }
            
            console.log('[ULTRAMSG] Calling API with record ID:', recordId);
            
            // Try with record ID first
            let result;
            try {
                result = await this.env.services.orm.call(
                    'ultramsg.config',
                    'action_test_send_message',
                    [parseInt(recordId)],
                    {
                        phone: phone,
                        message_type: messageType,
                        message_body: messageBody || '',
                        document_url: documentUrl || '',
                        document_name: documentName || '',
                    }
                );
            } catch (idError) {
                console.log('[ULTRAMSG] Failed with record ID, trying without ID:', idError);
                // Fallback: Call method without record ID
                result = await this.env.services.orm.call(
                    'ultramsg.config',
                    'action_test_send_message_direct',
                    [],
                    {
                        phone: phone,
                        message_type: messageType,
                        message_body: messageBody || '',
                        document_url: documentUrl || '',
                        document_name: documentName || '',
                    }
                );
            }
            
            console.log('[ULTRAMSG] API Result:', result);
            
            if (result && result.success) {
                let details = '';
                if (result.message_id) {
                    details = `<strong>معرف الرسالة:</strong> ${result.message_id}<br/>`;
                    details += `<a href="/web#id=${result.message_id}&model=ultramsg.message&view_type=form" target="_blank" style="color: #155724; text-decoration: underline;">عرض تفاصيل الرسالة</a>`;
                }
                this.showResult('success', '✓ تم الإرسال بنجاح', result.message || 'تم إرسال الرسالة بنجاح', details);
                
                this.displayNotification({
                    title: _t('نجاح'),
                    message: result.message || _t('تم إرسال الرسالة بنجاح'),
                    type: 'success',
                });
            } else {
                let details = '';
                if (result && result.response) {
                    details = JSON.stringify(result.response, null, 2);
                } else if (result && result.message) {
                    details = result.message;
                }
                this.showResult('error', '✗ فشل الإرسال', (result && result.message) || 'فشل إرسال الرسالة', details);
                
                this.displayNotification({
                    title: _t('خطأ'),
                    message: (result && result.message) || _t('فشل إرسال الرسالة'),
                    type: 'danger',
                    sticky: true,
                });
            }
        } catch (error) {
            let errorDetails = '';
            if (error.message) {
                errorDetails = error.message;
            } else if (error.toString) {
                errorDetails = error.toString();
            } else {
                errorDetails = 'خطأ غير معروف';
            }
            
            this.showResult('error', '✗ حدث خطأ', `حدث خطأ أثناء محاولة الإرسال: ${errorDetails}`, errorDetails);
            
            this.displayNotification({
                title: _t('خطأ'),
                message: `حدث خطأ: ${error.message || error}`,
                type: 'danger',
                sticky: true,
            });
        } finally {
            if (sendButton) {
                sendButton.disabled = false;
                sendButton.innerHTML = originalButtonText;
            }
        }
    },
});

// Fallback: Direct event listener if patch doesn't work
(function() {
    function setupFallback() {
        const sendButton = document.getElementById('test_send_button');
        if (sendButton && !sendButton.hasAttribute('data-fallback-listener')) {
            sendButton.setAttribute('data-fallback-listener', 'true');
            
            sendButton.addEventListener('click', async function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const phone = document.getElementById('test_phone')?.value?.trim();
                const messageType = document.getElementById('test_message_type')?.value;
                const messageBody = document.getElementById('test_message_body')?.value?.trim();
                const documentUrl = document.getElementById('test_document_url')?.value?.trim();
                const documentName = document.getElementById('test_document_name')?.value?.trim();
                
                const resultDiv = document.getElementById('test_result');
                const resultTitle = document.getElementById('test_result_title');
                const resultMessage = document.getElementById('test_result_message');
                const resultDetails = document.getElementById('test_result_details');
                
                function showResult(type, title, msg, details) {
                    if (!resultDiv) return;
                    resultDiv.style.display = 'block';
                    
                    if (type === 'success') {
                        resultDiv.style.backgroundColor = '#d4edda';
                        resultDiv.style.border = '1px solid #c3e6cb';
                        resultDiv.style.color = '#155724';
                    } else {
                        resultDiv.style.backgroundColor = '#f8d7da';
                        resultDiv.style.border = '1px solid #f5c6cb';
                        resultDiv.style.color = '#721c24';
                    }
                    
                    if (resultTitle) resultTitle.textContent = title;
                    if (resultMessage) resultMessage.textContent = msg;
                    if (resultDetails) {
                        if (details) {
                            resultDetails.innerHTML = `<strong>التفاصيل:</strong><pre style="white-space: pre-wrap; font-size: 11px; max-height: 200px; overflow: auto; background: rgba(0,0,0,0.1); padding: 10px; border-radius: 3px;">${details}</pre>`;
                        } else {
                            resultDetails.innerHTML = '';
                        }
                    }
                }
                
                // Validation
                if (!phone) {
                    showResult('error', '✗ خطأ في الإدخال', 'يرجى إدخال رقم الهاتف', '');
                    return;
                }
                
                if (messageType === 'text' && !messageBody) {
                    showResult('error', '✗ خطأ في الإدخال', 'يرجى إدخال نص الرسالة', '');
                    return;
                }
                
                if ((messageType === 'document' || messageType === 'image') && !documentUrl) {
                    showResult('error', '✗ خطأ في الإدخال', 'يرجى إدخال رابط المستند/الصورة', '');
                    return;
                }
                
                sendButton.disabled = true;
                const originalText = sendButton.innerHTML;
                sendButton.innerHTML = '<i class="fa fa-spinner fa-spin"/> جاري الإرسال...';
                
                showResult('info', '⏳ جاري الإرسال...', 'يرجى الانتظار...', '');
                
                try {
                    // Get record ID from multiple sources
                    let recordId = null;
                    
                    // Try from URL hash (most common in Odoo)
                    const hashMatch = window.location.hash.match(/id=(\d+)/);
                    if (hashMatch) recordId = hashMatch[1];
                    
                    // Try from URL params
                    if (!recordId) {
                        const urlParams = new URLSearchParams(window.location.search);
                        recordId = urlParams.get('id');
                    }
                    
                    // Try from form - look for hidden input with name="id"
                    if (!recordId) {
                        const idInputs = document.querySelectorAll('input[name="id"]');
                        for (const input of idInputs) {
                            if (input.value && input.value !== '0' && input.value !== '') {
                                recordId = input.value;
                                break;
                            }
                        }
                    }
                    
                    // Try from form - look for any input with id containing "id"
                    if (!recordId) {
                        const allInputs = document.querySelectorAll('input[type="hidden"]');
                        for (const input of allInputs) {
                            if (input.name && input.name.includes('id') && input.value && input.value !== '0') {
                                recordId = input.value;
                                break;
                            }
                        }
                    }
                    
                    // Try from form data attributes
                    if (!recordId) {
                        const form = document.querySelector('form.o_form_view');
                        if (form) {
                            // Try data-res-id
                            recordId = form.getAttribute('data-res-id');
                            // Try data-id
                            if (!recordId) recordId = form.getAttribute('data-id');
                        }
                    }
                    
                    // Try from Odoo's window object
                    if (!recordId && window.odoo) {
                        try {
                            // Try to access Odoo's services
                            const services = window.odoo.__DEBUG__?.services;
                            if (services) {
                                const action = services.action?.currentController?.props?.resId;
                                if (action) recordId = action;
                            }
                        } catch (e) {
                            // Ignore errors
                        }
                    }
                    
                    // Last resort: try to get from active record
                    if (!recordId) {
                        // Look for any element with data-res-id
                        const elementWithId = document.querySelector('[data-res-id]');
                        if (elementWithId) {
                            recordId = elementWithId.getAttribute('data-res-id');
                        }
                    }
                    
                    console.log('[ULTRAMSG Fallback] Found record ID:', recordId);
                    
                    // Prepare RPC call - use direct method if no ID
                    const useDirectMethod = !recordId || recordId === '0' || recordId === '';
                    const method = useDirectMethod ? 'action_test_send_message_direct' : 'action_test_send_message';
                    const args = useDirectMethod ? [] : [[parseInt(recordId)]];
                    
                    console.log('[ULTRAMSG Fallback] Using method:', method, 'with args:', args);
                    
                    // Call RPC
                    const response = await fetch('/web/dataset/call_kw', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            jsonrpc: '2.0',
                            method: 'call',
                            params: {
                                model: 'ultramsg.config',
                                method: method,
                                args: args,
                                kwargs: {
                                    phone: phone,
                                    message_type: messageType,
                                    message_body: messageBody || '',
                                    document_url: documentUrl || '',
                                    document_name: documentName || '',
                                },
                            },
                            id: Math.floor(Math.random() * 1000000),
                        }),
                    });
                    
                    const data = await response.json();
                    
                    console.log('[ULTRAMSG Fallback] Full response:', data);
                    
                    if (data.error) {
                        const errorMsg = data.error.data?.message || data.error.message || JSON.stringify(data.error);
                        console.error('[ULTRAMSG Fallback] Error from server:', data.error);
                        throw new Error(errorMsg);
                    }
                    
                    const result = data.result;
                    console.log('[ULTRAMSG Fallback] Result:', result);
                    
                    if (result && result.success) {
                        let details = '';
                        if (result.message_id) {
                            details = `<strong>معرف الرسالة:</strong> ${result.message_id}<br/>`;
                            details += `<a href="/web#id=${result.message_id}&model=ultramsg.message&view_type=form" target="_blank" style="color: #155724; text-decoration: underline;">عرض تفاصيل الرسالة</a>`;
                        }
                        showResult('success', '✓ تم الإرسال بنجاح', result.message || 'تم إرسال الرسالة بنجاح', details);
                    } else {
                        let details = '';
                        if (result && result.response) {
                            details = JSON.stringify(result.response, null, 2);
                        } else if (result && result.message) {
                            details = result.message;
                        }
                        showResult('error', '✗ فشل الإرسال', (result && result.message) || 'فشل إرسال الرسالة', details);
                    }
                } catch (error) {
                    let errorDetails = error.message || error.toString() || 'خطأ غير معروف';
                    showResult('error', '✗ حدث خطأ', `حدث خطأ أثناء محاولة الإرسال: ${errorDetails}`, errorDetails);
                } finally {
                    sendButton.disabled = false;
                    sendButton.innerHTML = originalText;
                }
            });
        }
        
        // Setup message type change
        const messageTypeSelect = document.getElementById('test_message_type');
        const documentFields = document.getElementById('test_document_fields');
        
        if (messageTypeSelect && documentFields) {
            messageTypeSelect.addEventListener('change', function() {
                if (this.value === 'document' || this.value === 'image') {
                    documentFields.style.display = 'block';
                } else {
                    documentFields.style.display = 'none';
                }
            });
        }
    }
    
    // Setup after DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(setupFallback, 1000);
        });
    } else {
        setTimeout(setupFallback, 1000);
    }
    
    // Retry setup
    setTimeout(setupFallback, 3000);
    setTimeout(setupFallback, 5000);
})();
