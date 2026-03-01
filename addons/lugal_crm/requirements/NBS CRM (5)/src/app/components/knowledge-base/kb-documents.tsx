import { useState } from "react";
import { motion } from "motion/react";
import {
  Search,
  Download,
  FileText,
  FileSpreadsheet,
  Presentation,
  File,
  Clock,
  FolderOpen,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { documents, type Document } from "./kb-data";

const fileTypeConfig: Record<Document["type"], { icon: typeof FileText; color: string; bg: string }> = {
  pdf: { icon: FileText, color: "text-red-500", bg: "bg-red-500/10" },
  doc: { icon: File, color: "text-blue-500", bg: "bg-blue-500/10" },
  xlsx: { icon: FileSpreadsheet, color: "text-emerald-500", bg: "bg-emerald-500/10" },
  pptx: { icon: Presentation, color: "text-primary", bg: "bg-primary/10" },
};

export function KBDocuments() {
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("الكل");

  const categories = ["الكل", ...Array.from(new Set(documents.map((d) => d.category)))];

  const filtered = documents.filter((d) => {
    const matchSearch = d.title.includes(search);
    const matchCategory = activeCategory === "الكل" || d.category === activeCategory;
    return matchSearch && matchCategory;
  });

  return (
    <div className="space-y-6">
      {/* Search & Filter */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="بحث في المستندات..."
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

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "PDF", count: documents.filter((d) => d.type === "pdf").length, ...fileTypeConfig.pdf },
          { label: "Word", count: documents.filter((d) => d.type === "doc").length, ...fileTypeConfig.doc },
          { label: "Excel", count: documents.filter((d) => d.type === "xlsx").length, ...fileTypeConfig.xlsx },
          { label: "PowerPoint", count: documents.filter((d) => d.type === "pptx").length, ...fileTypeConfig.pptx },
        ].map((stat, i) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Card className="border-border/50">
                <CardContent className="p-3 flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg ${stat.bg} flex items-center justify-center shrink-0`}>
                    <Icon className={`w-4 h-4 ${stat.color}`} />
                  </div>
                  <div>
                    <p className="text-lg text-foreground">{stat.count}</p>
                    <p className="text-[10px] text-muted-foreground">{stat.label}</p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* Documents List */}
      <div className="space-y-3">
        {filtered.map((doc, i) => {
          const config = fileTypeConfig[doc.type];
          const Icon = config.icon;

          return (
            <motion.div
              key={doc.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
            >
              <Card className="border-border/50 hover:shadow-md hover:border-primary/30 transition-all group">
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    {/* File Icon */}
                    <div className={`w-10 h-10 rounded-xl ${config.bg} flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform`}>
                      <Icon className={`w-5 h-5 ${config.color}`} />
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm text-foreground truncate group-hover:text-primary transition-colors">
                        {doc.title}
                      </h4>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
                        <Badge variant="outline" className="text-[10px] h-5">
                          {doc.category}
                        </Badge>
                        <span>{doc.size}</span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(doc.updatedAt).toLocaleDateString("ar-SA")}
                        </span>
                      </div>
                    </div>

                    {/* Download Info & Button */}
                    <div className="flex items-center gap-3 shrink-0">
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Download className="w-3 h-3" />
                        {doc.downloads}
                      </span>
                      <Badge className={`text-[10px] uppercase ${config.bg} ${config.color} border-transparent`}>
                        .{doc.type}
                      </Badge>
                      <Button
                        variant="outline"
                        size="icon"
                        className="h-8 w-8 hover:bg-primary/10 hover:text-primary hover:border-primary/30"
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}

        {filtered.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            <FolderOpen className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>لا توجد مستندات تطابق البحث</p>
          </div>
        )}
      </div>
    </div>
  );
}
