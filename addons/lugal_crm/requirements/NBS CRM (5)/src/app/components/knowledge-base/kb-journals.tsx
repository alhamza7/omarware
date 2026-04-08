import { useState } from "react";
import { motion } from "motion/react";
import { Eye, Clock, Search, BookOpen, ChevronLeft, User } from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { journals, type Article } from "./kb-data";

const categoryColors: Record<string, string> = {
  "صناعة العطور": "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  "تحليلات السوق": "bg-blue-500/10 text-blue-500 border-blue-500/20",
  "تجربة العميل": "bg-purple-500/10 text-purple-500 border-purple-500/20",
  "تسويق": "bg-pink-500/10 text-pink-500 border-pink-500/20",
};

export function KBJournals() {
  const [search, setSearch] = useState("");
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null);

  const filtered = journals.filter(
    (j) => j.title.includes(search) || j.excerpt.includes(search) || j.category.includes(search)
  );

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
          العودة للمجلات
        </Button>

        <Card className="border-border/50 overflow-hidden">
          {/* Article Header Banner */}
          <div className="h-32 bg-gradient-to-l from-emerald-500/20 via-primary/10 to-transparent flex items-end p-6">
            <Badge className={categoryColors[selectedArticle.category] || "bg-secondary text-foreground"}>
              {selectedArticle.category}
            </Badge>
          </div>
          <CardContent className="p-8 -mt-2">
            <h2 className="text-2xl text-foreground mb-4">{selectedArticle.title}</h2>
            <div className="flex items-center gap-4 text-sm text-muted-foreground mb-8 flex-wrap">
              <span className="flex items-center gap-1.5">
                <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center">
                  <User className="w-3 h-3 text-primary" />
                </div>
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
            <p className="text-foreground/90 leading-relaxed text-base mb-6">
              {selectedArticle.excerpt}
            </p>
            <div className="p-4 rounded-lg bg-secondary/30 border border-border/50">
              <p className="text-sm text-muted-foreground">
                محتوى تجريبي — سيتم ربط المحتوى الكامل من قاعدة البيانات لاحقاً مع دعم للصور والوسائط المتعددة.
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="بحث في المجلات..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pr-9 bg-secondary/30 border-border/50"
        />
      </div>

      {/* Featured Article */}
      {filtered.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}>
          <Card
            className="cursor-pointer group hover:shadow-xl transition-all duration-300 overflow-hidden border-emerald-500/20"
            onClick={() => setSelectedArticle(filtered[0])}
          >
            <div className="grid md:grid-cols-3">
              <div className="md:col-span-1 bg-gradient-to-bl from-emerald-500/20 via-primary/10 to-secondary/50 flex items-center justify-center p-8">
                <BookOpen className="w-16 h-16 text-emerald-500/40 group-hover:text-emerald-500/60 transition-colors group-hover:scale-110 transition-transform duration-500" />
              </div>
              <CardContent className="md:col-span-2 p-6">
                <Badge className={categoryColors[filtered[0].category] || ""}>
                  {filtered[0].category}
                </Badge>
                <h3 className="text-xl text-foreground mt-3 mb-2 group-hover:text-primary transition-colors">
                  {filtered[0].title}
                </h3>
                <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                  {filtered[0].excerpt}
                </p>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span>{filtered[0].author}</span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {filtered[0].readTime}
                  </span>
                  <span className="flex items-center gap-1">
                    <Eye className="w-3 h-3" />
                    {filtered[0].views}
                  </span>
                </div>
              </CardContent>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Articles Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.slice(1).map((article, i) => (
          <motion.div
            key={article.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <Card
              className="cursor-pointer group hover:shadow-md hover:border-primary/30 transition-all h-full border-border/50"
              onClick={() => setSelectedArticle(article)}
            >
              <CardContent className="p-5">
                <Badge className={`text-[10px] mb-3 ${categoryColors[article.category] || ""}`}>
                  {article.category}
                </Badge>
                <h4 className="text-foreground mb-2 group-hover:text-primary transition-colors">
                  {article.title}
                </h4>
                <p className="text-xs text-muted-foreground line-clamp-2 mb-4">
                  {article.excerpt}
                </p>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{article.author}</span>
                  <div className="flex items-center gap-3">
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
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
