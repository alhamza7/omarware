/** @odoo-module **/

import { Component, useState, useRef, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class LugalChatComponent extends Component {
    setup() {
        // Get services from the environment
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        
        this.state = useState({
            messages: [],
            inputText: "",
            isLoading: false,
            history: [],
            showHistory: false,
            stats: {
                total_questions: 0,
                avg_response_time: 0,
                cached_percentage: 0,
                today_questions: 0
            },
        });
        
        this.chatContainerRef = useRef("chatContainer");
        
        onMounted(() => {
            this.loadHistory();
            this.loadStats();
        });
    }
    
    async loadHistory() {
        try {
            const result = await this.orm.call(
                "lugal.conversation",
                "search_read",
                [],
                {
                    fields: ["id", "question", "answer", "create_date", "user_id", "category", "was_cached"],
                    limit: 20,
                    order: "create_date DESC"
                }
            );
            
            this.state.history = result.map(conv => ({
                ...conv,
                user_name: conv.user_id ? conv.user_id[1] : 'Unknown'
            }));
        } catch (error) {
            console.error("Error loading history:", error);
        }
    }
    
    async loadStats() {
        try {
            const result = await this.orm.call(
                "lugal.conversation",
                "get_stats",
                [],
                { days: 30 }
            );
            
            if (result) {
                this.state.stats = result;
            }
        } catch (error) {
            console.error("Error loading stats:", error);
        }
    }
    
    async sendMessage() {
        const question = this.state.inputText.trim();
        
        if (!question) return;
        
        // Add user message to UI
        this.state.messages.push({
            type: "user",
            text: question,
            timestamp: new Date(),
        });
        
        this.state.inputText = "";
        this.state.isLoading = true;
        
        // Scroll to bottom
        setTimeout(() => this.scrollToBottom(), 100);
        
        try {
            // Call the Gemini API through Odoo backend
            const result = await this.orm.call(
                "lugal.conversation",
                "ask_question",
                [],
                {
                    question: question,
                    context: {}
                }
            );
            
            if (result && result.success) {
                // Add AI response to UI
                this.state.messages.push({
                    type: "ai",
                    text: result.answer,
                    timestamp: new Date(),
                    category: result.category,
                    was_cached: result.was_cached,
                    response_time: result.response_time_ms,
                    conversation_id: result.conversation_id,
                });
                
                // Show cache indicator
                if (result.was_cached) {
                    this.notification.add("⚡ Response from cache", {
                        type: "info",
                    });
                }
            } else {
                this.state.messages.push({
                    type: "error",
                    text: result?.error || "Failed to get response",
                    timestamp: new Date(),
                });
                
                this.notification.add("Error: " + (result?.error || "Unknown error"), {
                    type: "danger",
                });
            }
        } catch (error) {
            console.error("Error sending message:", error);
            this.state.messages.push({
                type: "error",
                text: "Failed to send message: " + error.message,
                timestamp: new Date(),
            });
            
            this.notification.add("Failed to send message", {
                type: "danger",
            });
        } finally {
            this.state.isLoading = false;
            setTimeout(() => this.scrollToBottom(), 100);
            
            // Reload history and stats
            this.loadHistory();
            this.loadStats();
        }
    }
    
    scrollToBottom() {
        if (this.chatContainerRef.el) {
            this.chatContainerRef.el.scrollTop = this.chatContainerRef.el.scrollHeight;
        }
    }
    
    onInputKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }
    
    toggleHistory() {
        this.state.showHistory = !this.state.showHistory;
    }
    
    loadHistoryItem(conversation) {
        // Add both question and answer to current chat
        this.state.messages.push({
            type: "user",
            text: conversation.question,
            timestamp: new Date(conversation.create_date),
        });
        
        this.state.messages.push({
            type: "ai",
            text: conversation.answer,
            timestamp: new Date(conversation.create_date),
            category: conversation.category,
            was_cached: conversation.was_cached,
        });
        
        this.state.showHistory = false;
        setTimeout(() => this.scrollToBottom(), 100);
    }
    
    async rateMessage(message, rating) {
        if (!message.conversation_id) return;
        
        try {
            await this.orm.call(
                "lugal.conversation",
                "rate_conversation",
                [message.conversation_id],
                { rating: rating }
            );
            
            message.rating = rating;
            this.notification.add("Thank you for your feedback!", {
                type: "success",
            });
        } catch (error) {
            console.error("Error rating message:", error);
        }
    }
    
    clearChat() {
        this.state.messages = [];
    }
    
    formatMessage(text) {
        if (!text) return '';
        
        // Convert markdown-style formatting to HTML
        let formatted = text;
        
        // Escape HTML first to prevent XSS
        const escapeHtml = (str) => {
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        };
        
        formatted = escapeHtml(formatted);
        
        // Convert line breaks to <br>
        formatted = formatted.replace(/\n/g, '<br>');
        
        // Convert bullets (* item) to proper list
        formatted = formatted.replace(/\* (.+?)(<br>|$)/g, '<div class="bullet-item">• $1</div>');
        
        // Convert numbered lists (1. item)
        formatted = formatted.replace(/(\d+)\. (.+?)(<br>)/g, '<div class="numbered-item"><strong>$1.</strong> $2</div><br>');
        
        // Make dividers
        formatted = formatted.replace(/={3,}/g, '<hr class="my-2" style="border-color: #ddd;">');
        
        // Highlight product codes (ADF00XXX, EXP00XXX, etc.)
        formatted = formatted.replace(/\b([A-Z]{2,}\d{5,})\b/g, '<code class="product-code badge bg-secondary">$1</code>');
        
        // Make emojis stand out
        formatted = formatted.replace(/([\u{1F300}-\u{1F9FF}])/gu, '<span class="emoji" style="font-size: 1.2em;">$1</span>');
        
        // Format sections with icons (🏷️, 💰, 📊, etc.)
        formatted = formatted.replace(/(🏷️|💰|📊|🏭|🏪|📦|💼|📄|👥|🔢) (.+?):/g, '<div class="section-header"><strong>$1 $2:</strong></div>');
        
        return formatted;
    }
}

LugalChatComponent.template = "lugal_ai.LugalChatTemplate";

// Register as a client action
registry.category("actions").add("lugal_chat", LugalChatComponent);
