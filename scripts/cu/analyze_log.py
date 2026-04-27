#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحليل ملف LOG لمعرفة ما يحدث
"""

with open("odoo.log", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()
    
    # آخر 200 سطر
    recent = lines[-200:]
    
    print("=" * 80)
    print("🔍 آخر عمليات UoM Pricing")
    print("=" * 80 + "\n")
    
    for line in recent:
        if any(x in line for x in ["✅ Found matching", "💰 Final price", "⏭️ Skipping", "🎯 Using FIXED"]):
            print(line.strip())
    
    print("\n" + "=" * 80)
    print("📊 التحليل")
    print("=" * 80 + "\n")
    
    print("إذا لم تظهر رسائل logging:")
    print("   → Module لم يُستدعى!")
    print("   → أو logging لم يُفعّل\n")
    
    print("الحل: إضافة logging أقوى وإعادة الاختبار")

