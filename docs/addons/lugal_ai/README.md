# 🧠 Lugal AI - Enterprise AI Control Layer for Odoo × Gemini

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/yourusername/lugal-ai)
[![License](https://img.shields.io/badge/license-LGPL--3-green.svg)](LICENSE)
[![Odoo](https://img.shields.io/badge/odoo-16.0%2B-875A7B.svg)](https://www.odoo.com/)

**Lugal AI** is an enterprise-grade AI integration module that brings Google Gemini's powerful language model directly into your Odoo environment with robust security, intelligent caching, and role-based permissions.

## ✨ Key Features

### 🔐 Enterprise Security
- **Role-Based Permissions**: Admin, Employee, and Customer roles with granular data access control
- **Data Scope Enforcement**: Users only see data they're authorized to access
- **Query Rate Limiting**: Prevent API abuse with configurable rate limits

### ⚡ Performance Optimization
- **Smart Caching**: Intelligent response caching reduces API costs by up to 80%
- **Question Indexing**: Pre-indexed common questions for instant answers
- **Token Optimization**: Minimizes token usage through efficient prompt engineering

### 💬 User Interfaces
- **Chat Interface**: Beautiful, intuitive chat UI for natural language queries
- **POS-Style Product Search**: Fast, modern product search with AI suggestions
- **Admin Dashboard**: Comprehensive analytics and system management

### 🌐 Bilingual Support
- Seamless Arabic/English support
- Automatic language detection
- Bilingual question patterns

### 📊 Analytics & Insights
- Conversation history tracking
- Performance metrics (response time, token usage)
- User feedback and ratings
- Cache hit rate analysis

## 📋 Requirements

- **Odoo**: 16.0 or higher
- **Python**: 3.8+
- **Google Gemini API Key**: [Get one here](https://makersuite.google.com/app/apikey)

## 🚀 Installation

### 1. Install Python Dependencies

```bash
cd addons/lugal_ai
pip install -r requirements.txt
```

Or directly:
```bash
pip install google-generativeai>=0.3.0
```

### 2. Install Odoo Module

```bash
# Copy to Odoo addons directory
cp -r lugal_ai /path/to/odoo/addons/

# Restart Odoo
sudo systemctl restart odoo

# Update apps list in Odoo
# Go to Apps → Update Apps List
```

### 3. Activate Module

1. Go to **Apps** in Odoo
2. Search for "Lugal AI"
3. Click **Install**

## ⚙️ Configuration

### 1. Get Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key

### 2. Configure Lugal AI

1. Go to **Lugal AI → Configuration → Settings**
2. Enter your Gemini API key
3. Choose your model (Gemini 2.0 Flash recommended for speed/cost balance)
4. Configure settings:
   - **Temperature**: 0.3 (recommended for business queries)
   - **Max Tokens**: 1000 for output
   - **Cache Duration**: 24 hours
5. Click **Test Connection** to verify
6. Save

### 3. Set Up Permissions (Optional)

Default permissions are configured automatically:
- **Admin**: Full access
- **Employee**: Own data + assigned customers
- **Customer**: Product info + own orders only

Customize at: **Lugal AI → Configuration → Permissions**

### 4. Add Question Patterns (Optional)

Pre-index common questions for faster responses:

Go to **Lugal AI → Configuration → Question Index**

Example patterns are included by default.

## 📖 Usage

### Chat Interface

1. Go to **Lugal AI → Chat**
2. Ask questions in natural language:
   - "ما هي أكثر المنتجات مبيعاً هذا الشهر؟"
   - "What are today's sales?"
   - "Is product ABC available?"
3. Get instant, accurate answers
4. Rate responses for continuous improvement

### Product Search

1. Go to **Lugal AI → Product Search**
2. Search products by:
   - Name or code
   - Natural language questions
   - Category, price range, availability
3. Click any product for detailed info
4. Get AI-powered product suggestions

### For Developers

#### Custom Queries

```python
# Call Lugal AI from Python code
self.env['lugal.conversation'].sudo()._ask_gemini_with_context(
    question="What are the top 5 customers?",
    context=json.dumps({"timeframe": "last_month"}),
    user=self.env.user,
)
```

#### API Endpoint

```javascript
// Call from JavaScript
await this.rpc("/lugal/api/ask", {
    question: "Your question here",
    context: { /* optional context */ },
});
```

## 🔧 SAP Integration

Lugal AI detects and integrates with the `sap_integration` module automatically.

If SAP module is installed, Lugal AI will:
- Include SAP data in responses
- Sync product information
- Provide SAP-specific insights

## 📊 System Prompt

The default system prompt enforces:
- ✅ Concise, business-focused answers
- ✅ Strict permission enforcement
- ✅ Token optimization
- ✅ No data leakage
- ✅ Professional tone

Customize at: **Lugal AI → Configuration → Settings → System Prompt**

## 🛠️ Architecture

```
┌─────────────────────────────────────────────────┐
│         User Interface (Owl Components)         │
│  - Chat Interface                               │
│  - Product Search                               │
│  - Admin Dashboard                              │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│      Odoo Backend (Python Controllers)          │
│  - Authentication & Role Management             │
│  - Permission Enforcement                       │
│  - Question Classification & Indexing           │
│  - Data Retrieval from Odoo Models              │
│  - Cache Management                             │
└─────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────┐
│        Google Gemini API Integration            │
│  - Structured Prompt Generation                 │
│  - Response Parsing                             │
│  - Token Usage Tracking                         │
└─────────────────────────────────────────────────┘
```

## 📈 Performance Tips

1. **Enable Caching**: Reduces costs and improves speed
2. **Use Question Index**: Pre-index frequently asked questions
3. **Choose Right Model**:
   - `gemini-2.0-flash-exp`: Fast, cheap (recommended)
   - `gemini-1.5-pro`: More powerful, slower
4. **Optimize Temperature**: Lower (0.2-0.4) for factual queries
5. **Set Rate Limits**: Prevent excessive API usage

## 🐛 Troubleshooting

### "No active configuration found"
→ Go to Settings and activate a configuration

### "API key invalid"
→ Verify your Gemini API key at [Google AI Studio](https://makersuite.google.com/)

### "Access denied"
→ Check user's role and permissions in Configuration → Permissions

### Slow responses
→ Enable caching and reduce max_output_tokens

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

This module is licensed under **LGPL-3**.

## 👨‍💻 Credits

Developed by **Capo Development**

Powered by **Google Gemini** and **Odoo**

## 📞 Support

For issues, questions, or feature requests:
- GitHub Issues: [yourusername/lugal-ai/issues](https://github.com/yourusername/lugal-ai/issues)
- Email: support@capo-dev.com

---

**Made with ❤️ for the Odoo community**

