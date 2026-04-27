# فحص إعدادات القالب "1"

## ✅ **تأكد من إعدادات A4:**

### افتح القالب:
```
المخزون → Product Labels → Label Templates → افتح "1"
```

### تبويب "A4 Layout":
```
تأكد من:
- Labels per Row: 2        ← يجب أن يكون 2
- Labels per Column: 4     ← يجب أن يكون 4
- Margin: 2mm

إذا كانت مختلفة، عدّلها واحفظ
```

---

## 🔍 **التحقق السريع:**

في Python shell:

```python
# افتح Python shell
./odoo-bin shell -c odoo.conf -d your_database

# ثم شغّل:
template = env['product.label.template'].browse(1)
print(f"Name: {template.name}")
print(f"Labels per Row: {template.labels_per_row}")
print(f"Labels per Column: {template.labels_per_column}")
print(f"Total per page: {template.labels_per_row * template.labels_per_column}")
```

---

## ✅ **الإعدادات الصحيحة:**

```
Name: 1 (أو أي اسم)
Width: 80mm
Height: 60mm
Labels per Row: 2
Labels per Column: 4
Margin: 2mm
→ Total: 8 labels per A4 page
```

---

## 🚀 **الحل:**

إذا كانت الإعدادات خاطئة:

```
1. Label Templates → افتح "1"
2. تبويب "A4 Layout"
3. عدّل:
   - Labels per Row: 2
   - Labels per Column: 4
   - Margin: 2
4. Save
5. جرّب الطباعة مرة أخرى
```

---

**تحقق من القالب الآن!**

