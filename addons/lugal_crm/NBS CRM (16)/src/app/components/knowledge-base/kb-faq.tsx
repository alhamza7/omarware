import { useState } from "react";
import { motion } from "motion/react";
import { Search, ThumbsUp, Eye, HelpCircle } from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "../ui/accordion";
import { faqs } from "./kb-data";

const categoryColors: Record<string, string> = {
  "الموارد البشرية": "bg-blue-500/10 text-blue-500",
  "المزايا": "bg-emerald-500/10 text-emerald-500",
  "خدمة العملاء": "bg-purple-500/10 text-purple-500",
  "العمليات": "bg-primary/10 text-primary",
  "الأنظمة": "bg-cyan-500/10 text-cyan-500",
  "الجودة": "bg-pink-500/10 text-pink-500",
};

export function KBFAQ() {
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("الكل");
  const [helpfulMap, setHelpfulMap] = useState<Record<string, boolean>>({});

  const categories = ["الكل", ...Array.from(new Set(faqs.map((f) => f.category)))];

  const filtered = faqs.filter((f) => {
    const matchSearch =
      f.question.includes(search) || f.answer.includes(search);
    const matchCategory =
      activeCategory === "الكل" || f.category === activeCategory;
    return matchSearch && matchCategory;
  });

  const markHelpful = (id: string) => {
    setHelpfulMap((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="space-y-6">
      {/* Search */}
      <div className="relative max-w-lg">
        <Search className="absolute end-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="ابحث عن سؤال..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pe-9 bg-secondary/30 border-border/50 text-base h-11"
        />
      </div>

      {/* Categories */}
      <div className="flex gap-2 flex-wrap">
        {categories.map((cat) => (
          <Button
            key={cat}
            variant={activeCategory === cat ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveCategory(cat)}
            className="text-xs"
          >
            {cat}
          </Button>
        ))}
      </div>

      {/* FAQ Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="border-border/50">
          <CardContent className="p-4 text-center">
            <p className="text-2xl text-foreground">{faqs.length}</p>
            <p className="text-xs text-muted-foreground">سؤال متاح</p>
          </CardContent>
        </Card>
        <Card className="border-border/50">
          <CardContent className="p-4 text-center">
            <p className="text-2xl text-foreground">{categories.length - 1}</p>
            <p className="text-xs text-muted-foreground">تصنيف</p>
          </CardContent>
        </Card>
        <Card className="border-border/50">
          <CardContent className="p-4 text-center">
            <p className="text-2xl text-foreground">
              {faqs.reduce((sum, f) => sum + f.helpful, 0)}
            </p>
            <p className="text-xs text-muted-foreground">إعجاب</p>
          </CardContent>
        </Card>
      </div>

      {/* FAQ Accordion */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="border-border/50">
          <CardContent className="p-2">
            {filtered.length > 0 ? (
              <Accordion type="single" collapsible className="w-full">
                {filtered.map((faq, i) => (
                  <AccordionItem key={faq.id} value={faq.id} className="border-border/50">
                    <AccordionTrigger className="px-4 py-4 hover:no-underline group/trigger">
                      <div className="flex items-center gap-3 flex-1 text-start">
                        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 group-hover/trigger:bg-primary/20 transition-colors">
                          <HelpCircle className="w-4 h-4 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-foreground group-hover/trigger:text-primary transition-colors">
                            {faq.question}
                          </p>
                        </div>
                        <Badge
                          className={`text-[10px] shrink-0 border-transparent ms-2 ${
                            categoryColors[faq.category] || "bg-secondary text-foreground"
                          }`}
                        >
                          {faq.category}
                        </Badge>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="px-4 pb-4">
                      <div className="ps-11">
                        <p className="text-sm text-foreground/90 leading-relaxed mb-4">
                          {faq.answer}
                        </p>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <Eye className="w-3 h-3" />
                              {faq.views} مشاهدة
                            </span>
                            <span className="flex items-center gap-1">
                              <ThumbsUp className="w-3 h-3" />
                              {faq.helpful + (helpfulMap[faq.id] ? 1 : 0)} وجدها مفيدة
                            </span>
                          </div>
                          <Button
                            variant={helpfulMap[faq.id] ? "default" : "outline"}
                            size="sm"
                            className="text-xs h-7 gap-1.5"
                            onClick={() => markHelpful(faq.id)}
                          >
                            <ThumbsUp className={`w-3 h-3 ${helpfulMap[faq.id] ? "fill-current" : ""}`} />
                            {helpfulMap[faq.id] ? "شكراً!" : "مفيدة؟"}
                          </Button>
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <HelpCircle className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>لا توجد أسئلة تطابق البحث</p>
                <p className="text-xs mt-1">جرّب كلمات بحث مختلفة</p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}