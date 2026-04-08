import { useState } from "react";
import { motion } from "motion/react";
import {
  Search,
  Copy,
  CheckCircle2,
  FileText,
  Tag,
  BarChart3,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { scripts } from "./cc-data";

const categoryColors: Record<string, string> = {
  "عام": "bg-blue-500/10 text-blue-500",
  "VIP": "bg-primary/10 text-primary",
  "شكاوى": "bg-red-500/10 text-red-500",
  "طلبات": "bg-emerald-500/10 text-emerald-500",
  "مبيعات": "bg-pink-500/10 text-pink-500",
  "سياسات": "bg-purple-500/10 text-purple-500",
};

export function CCScripts() {
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("الكل");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const categories = ["الكل", ...Array.from(new Set(scripts.map((s) => s.category)))];

  const filtered = scripts.filter((s) => {
    const matchSearch =
      s.title.includes(search) ||
      s.content.includes(search) ||
      s.tags.some((t) => t.includes(search));
    const matchCategory = activeCategory === "الكل" || s.category === activeCategory;
    return matchSearch && matchCategory;
  });

  const handleCopy = (id: string, content: string) => {
    navigator.clipboard.writeText(content).catch(() => {});
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="border-border/50">
          <CardContent className="p-4 text-center">
            <p className="text-2xl text-foreground">{scripts.length}</p>
            <p className="text-xs text-muted-foreground">نص جاهز</p>
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
              {scripts.reduce((s, sc) => s + sc.usageCount, 0).toLocaleString()}
            </p>
            <p className="text-xs text-muted-foreground">مرة استخدام</p>
          </CardContent>
        </Card>
      </div>

      {/* Search & Filter */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="بحث في النصوص والردود..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pr-9 bg-secondary/30 border-border/50"
          />
        </div>
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
      </div>

      {/* Scripts List */}
      <div className="space-y-4">
        {filtered.map((script, i) => {
          const isCopied = copiedId === script.id;
          const catColor = categoryColors[script.category] || "bg-secondary text-foreground";

          return (
            <motion.div
              key={script.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
            >
              <Card className="border-border/50 hover:shadow-md hover:border-primary/30 transition-all group">
                <CardContent className="p-5">
                  {/* Header */}
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                        <FileText className="w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <h4 className="text-sm text-foreground group-hover:text-primary transition-colors">
                          {script.title}
                        </h4>
                        <div className="flex items-center gap-2 mt-0.5">
                          <Badge className={`text-[10px] border-transparent ${catColor}`}>
                            {script.category}
                          </Badge>
                          <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                            <BarChart3 className="w-2.5 h-2.5" />
                            {script.usageCount} استخدام
                          </span>
                        </div>
                      </div>
                    </div>
                    <Button
                      variant={isCopied ? "default" : "outline"}
                      size="sm"
                      className={`text-xs gap-1.5 shrink-0 ${
                        isCopied ? "bg-emerald-500 hover:bg-emerald-500 text-white" : ""
                      }`}
                      onClick={() => handleCopy(script.id, script.content)}
                    >
                      {isCopied ? (
                        <>
                          <CheckCircle2 className="w-3 h-3" />
                          تم النسخ
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          نسخ
                        </>
                      )}
                    </Button>
                  </div>

                  {/* Content */}
                  <div className="p-3 rounded-lg bg-secondary/30 border border-border/50 mb-3">
                    <p className="text-sm text-foreground/90 leading-relaxed whitespace-pre-wrap">
                      {script.content}
                    </p>
                  </div>

                  {/* Tags */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <Tag className="w-3 h-3 text-muted-foreground" />
                    {script.tags.map((tag) => (
                      <Badge
                        key={tag}
                        variant="outline"
                        className="text-[10px] h-5 cursor-pointer hover:bg-primary/10 hover:text-primary hover:border-primary/30 transition-colors"
                        onClick={() => setSearch(tag)}
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}

        {filtered.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>لا توجد نصوص تطابق البحث</p>
          </div>
        )}
      </div>
    </div>
  );
}
