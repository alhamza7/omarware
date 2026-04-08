/** @odoo-module **/

import { registry } from "@web/core/registry";
import { CharField, charField } from "@web/views/fields/char/char_field";
import { useInputField } from "@web/views/fields/input_field_hook";
import { useState, useRef } from "@odoo/owl";

export class NoteWithSuggestionsField extends CharField {
    static template = "product_label_designer.NoteWithSuggestionsField";
    
    setup() {
        super.setup();
        this.input = useRef("input");
        this.suggestions = [
            { value: '1', label: 'زبون محل' },
            { value: '2', label: 'شركات توصيل' },
            { value: '3', label: 'نقليات' },
            { value: '4', label: 'ديلفري' },
            { value: '5', label: 'NBS' },
            { value: '6', label: 'شورجة' },
            { value: '7', label: 'NA' },
            { value: '8', label: 'مكاتب الشورجة' },
        ];
        this.state = useState({
            showSuggestions: false,
            filteredSuggestions: [...this.suggestions],
        });
        useInputField({
            getValue: () => this.props.record.data[this.props.name] || "",
            parse: (v) => v || "",
        });
    }
    
    onInput(ev) {
        const value = ev.target.value || '';
        this.filterSuggestions(value);
        // Update the record value
        this.props.record.update({ [this.props.name]: value });
    }
    
    onFocus(ev) {
        const value = ev.target.value || '';
        // Always show suggestions on focus, even if field is empty
        this.state.filteredSuggestions = value.length > 0 
            ? this.suggestions.filter(s => s.label.toLowerCase().includes(value.toLowerCase()))
            : [...this.suggestions];
        this.state.showSuggestions = true;
    }
    
    onBlur(ev) {
        // Delay hiding suggestions to allow clicking on them
        setTimeout(() => {
            this.state.showSuggestions = false;
        }, 200);
    }
    
    filterSuggestions(value) {
        if (value.length > 0) {
            this.state.filteredSuggestions = this.suggestions.filter(s => 
                s.label.toLowerCase().includes(value.toLowerCase())
            );
            this.state.showSuggestions = this.state.filteredSuggestions.length > 0;
        } else {
            // Show all suggestions when field is empty
            this.state.filteredSuggestions = [...this.suggestions];
            this.state.showSuggestions = true;
        }
    }
    
    selectSuggestion(suggestion) {
        this.props.record.update({ [this.props.name]: suggestion.label });
        this.state.showSuggestions = false;
    }
}

export const noteWithSuggestionsField = {
    ...charField,
    component: NoteWithSuggestionsField,
    displayName: "Note with Suggestions",
};

registry.category("fields").add("note_with_suggestions", noteWithSuggestionsField);

