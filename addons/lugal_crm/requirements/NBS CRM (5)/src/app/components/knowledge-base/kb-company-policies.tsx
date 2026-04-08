import { useState } from "react";
import { motion } from "motion/react";
import { Pin, Eye, Clock, Search, Building2, Shield, Users, ChevronLeft } from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { companyPolicies, type Article } from "./kb-data";

export function KBCompanyPolicies() {
  const [search, setSearch] = useState("");
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);
  const [activeCategory, setActiveCategory] = useState("الكل");

  const categories = ["الكل", "عن الشركة", "سياسات"];

  const filtered = companyPolicies.filter((p) => {
    const matchSearch = p.title.includes(search) || p.excerpt.includes(search);
    const matchCategory = activeCategory === "الكل" || p.category === activeCategory;
    return matchSearch && matchCategory;
  });

  const getCategoryIcon = (cat: string) => {
    if (cat === "عن الشركة") return Building2;
    if (cat === "سياسات") return Shield;
    return Users;
  };

  if (selectedArticle) {
    return (
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="space-y-6"
      >
        <Button
          variant="ghost"
          onClick={() => setSelectedArticle(null)}
          className="gap-2 text-muted-foreground hover:text-primary"
        >
          <ChevronLeft className="w-4 h-4 rotate-180" />
          العودة للقائمة
        </Button>

        <Card className="border-primary/20">
          <CardContent className="p-8">
            <div className="flex items-center gap-3 mb-4">
              <Badge variant="secondary">{selectedArticle.category}</Badge>
              {selectedArticle.pinned && (
                <Badge className="bg-primary/10 text-primary border-primary/20">
                  <Pin className="w-3 h-3 me-1" />
                  مثبّت
                </Badge>
              )}
            </div>
            <h2 className="text-2xl text-foreground mb-4">{selectedArticle.title}</h2>
            <div className="flex items-center gap-4 text-sm text-muted-foreground mb-8 flex-wrap">
              <span className="flex items-center gap-1">
                <Users className="w-3.5 h-3.5" />
                {selectedArticle.author}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                {selectedArticle.readTime}
              </span>
              <span className="flex items-center gap-1">
                <Eye className="w-3.5 h-3.5" />
                {selectedArticle.views} مشاهدة
              </span>
              <span>{new Date(selectedArticle.date).toLocaleDateString("ar-SA")}</span>
            </div>
            <div className="prose prose-sm max-w-none">
              <p className="text-foreground/90 leading-relaxed text-base">
                {selectedArticle.excerpt}
              </p>
              <div className="mt-6 p-4 rounded-lg bg-secondary/30 border border-border/50">
                <p className="text-sm text-muted-foreground">
                  هذا محتوى تجريبي. في النسخة النهائية، سيتم عرض المحتوى الكامل للمقال هنا مع دعم التنسيق الغني
                  والصور والروابط التفاعلية.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="بحث في السياسات..."
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

      {/* Pinned Articles */}
      {filtered.some((a) => a.pinned) && (
        <div>
          <h4 className="text-sm text-muted-foreground mb-3 flex items-center gap-2">
            <Pin className="w-3.5 h-3.5 text-primary" />
            مقالات مثبّتة
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filtered
              .filter((a) => a.pinned)
              .map((article, i) => {
                const CatIcon = getCategoryIcon(article.category);
                return (
                  <motion.div
                    key={article.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                  >
                    <Card
                      className="border-primary/20 bg-primary/5 cursor-pointer hover:shadow-lg hover:border-primary/40 transition-all group"
                      onClick={() => setSelectedArticle(article)}
                    >
                      <CardContent className="p-5">
                        <div className="flex items-start gap-4">
                          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                            <CatIcon className="w-5 h-5 text-primary" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h4 className="text-foreground mb-1 group-hover:text-primary transition-colors">
                              {article.title}
                            </h4>
                            <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
                              {article.excerpt}
                            </p>
                            <div className="flex items-center gap-3 text-xs text-muted-foreground">
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {article.readTime}
                              </span>
                              <span className="flex items-center gap-1">
                                <Eye className="w-3 h-3" />
                                {article.views}
                              </span>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}
          </div>
        </div>
      )}

      {/* All Articles */}
      <div>
        <h4 className="text-sm text-muted-foreground mb-3">
          جميع المقالات ({filtered.length})
        </h4>
        <div className="space-y-3">
          {filtered.map((article, i) => {
            const CatIcon = getCategoryIcon(article.category);
            return (
              <motion.div
                key={article.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04 }}
              >
                <Card
                  className="cursor-pointer hover:shadow-md hover:border-primary/30 transition-all group border-border/50"
                  onClick={() => setSelectedArticle(article)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center gap-4">
                      <div className="w-9 h-9 rounded-lg bg-secondary/50 flex items-center justify-center shrink-0">
                        <CatIcon className="w-4.5 h-4.5 text-muted-foreground group-hover:text-primary transition-colors" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <h4 className="text-sm text-foreground truncate group-hover:text-primary transition-colors">
                            {article.title}
                          </h4>
                          {article.pinned && <Pin className="w-3 h-3 text-primary shrink-0" />}
                        </div>
                        <p className="text-xs text-muted-foreground truncate">
                          {article.author} · {article.readTime} · {new Date(article.date).toLocaleDateString("ar-SA")}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="text-[10px]">{article.category}</Badge>
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Eye className="w-3 h-3" />{article.views}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
