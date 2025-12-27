/** @odoo-module **/

import { Component, useState, useRef, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class LugalChatComponent extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        
        this.state = useState({
            messages: [],
            inputText: "",
            isLoading: false,
            history: [],
            showHistory: false,
            stats: null,
        });
        
        this.chatContainerRef = useRef("chatContainer");
        
        onMounted(() => {
            this.loadHistory();
            this.loadStats();
        });
    }
    
    async loadHistory() {
        try {
            const result = await this.rpc("/lugal/api/chat/history", {
                limit: 20,
                offset: 0,
            });
            
            if (result.success) {
                this.state.history = result.conversations;
            }
        } catch (error) {
            console.error("Error loading history:", error);
        }
    }
    
    async loadStats() {
        try {
            const result = await this.rpc("/lugal/api/chat/stats", {
                days: 30,
            });
            
            if (result.success) {
                this.state.stats = result.stats;
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
            const result = await this.rpc("/lugal/api/ask", {
                question: question,
                context: null,
            });
            
            if (result.success) {
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
                    text: result.error || "Unknown error",
                    timestamp: new Date(),
                });
                
                this.notification.add("Error: " + result.error, {
                    type: "danger",
                });
            }
        } catch (error) {
            console.error("Error sending message:", error);
            this.state.messages.push({
                type: "error",
                text: "Failed to send message: " + error,
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
            await this.rpc("/lugal/api/rate", {
                conversation_id: message.conversation_id,
                rating: rating,
            });
            
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
}

LugalChatComponent.template = "lugal_ai.LugalChatTemplate";

registry.category("actions").add("lugal_chat", LugalChatComponent);

