import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Plus,
  PackagePlus,
  ImageIcon,
  CheckCircle2,
  Clock,
  XCircle,
  ShoppingBag,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Input } from "../ui/input";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "../ui/dialog";
import {
  itemRequests,
  requestStatusConfig,
  type Division,
} from "./sc-data";

export function SCRequests() {
  const [divisionFilter, setDivisionFilter] = useState<"all" | Division>("all");
  const [statusFilter, setStatusFilter] = useState<"all" | "pending" | "approved" | "ordered" | "rejected">("all");
  const [showCreate, setShowCreate] = useState(false);

  const filtered = itemRequests.filter((r) => {
    if (divisionFilter !== "all" && r.division !== divisionFilter) return false;
    if (statusFilter !== "all" && r.status !== statusFilter) return false;
    return true;
  });

  const statusIcon = (status: string) => {
    switch (status) {
      case "pending": return <Clock className="w-3.5 h-3.5 text-primary" />;
      case "approved": return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />;
      case "ordered": return <ShoppingBag className="w-3.5 h-3.5 text-blue-500" />;
      case "rejected": return <XCircle className="w-3.5 h-3.5 text-red-500" />;
      default: return null;
    }
  };

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          {/* Division Filter */}
          <div className="flex gap-1 p-0.5 rounded-md bg-secondary/40 border border-border/40">
            {([
              { key: "all" as const, label: "الكل" },
              { key: "europe" as const, label: "أوروبا" },
              { key: "china" as const, label: "الصين" },
            ]).map((d) => (
              <button
                key={d.key}
                onClick={() => setDivisionFilter(d.key)}
                className={`px-2.5 py-1 rounded text-[10px] transition-all ${
                  divisionFilter === d.key
                    ? "bg-card text-primary shadow-sm border border-primary/20"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {d.label}
              </button>
            ))}
          </div>
          {/* Status Filter */}
          <div className="flex gap-1">
            {([
              { key: "all" as const, label: "الكل" },
              { key: "pending" as const, label: "قيد الانتظار" },
              { key: "approved" as const, label: "موافق" },
              { key: "ordered" as const, label: "مطلوب" },
            ]).map((s) => (
              <Button
                key={s.key}
                variant={statusFilter === s.key ? "default" : "ghost"}
                size="sm"
                className="text-[10px] h-7"
                onClick={() => setStatusFilter(s.key)}
              >
                {s.label}
              </Button>
            ))}
          </div>
        </div>
        <Button size="sm" className="text-xs gap-1.5" onClick={() => setShowCreate(true)}>
          <Plus className="w-3.5 h-3.5" />
          طلب صنف جديد
        </Button>
      </div>

      {/* Request Cards */}
      <div className="grid grid-cols-2 gap-3">
        <AnimatePresence mode="popLayout">
          {filtered.map((req, i) => {
            const conf = requestStatusConfig[req.status];
            return (
              <motion.div
                key={req.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: i * 0.04 }}
                layout
              >
                <Card className="border-border/50 hover:border-primary/30 transition-all">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                        <PackagePlus className="w-4 h-4 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0 space-y-2">
                        <div className="flex items-center justify-between">
                          <p className="text-sm text-foreground">{req.itemName}</p>
                          <Badge className={`text-[9px] border-transparent ${conf.color}`}>{conf.label}</Badge>
                        </div>
                        <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                          <span>{req.size} {req.unit === "ml" ? "مل" : "كغ"}</span>
                          <span>الكمية: {req.quantity.toLocaleString("ar-SA")}</span>
                          <Badge variant="outline" className="text-[8px] h-4 px-1.5">
                            {req.category === "perfume" ? "عطور" : req.category === "glass" ? "زجاجيات" : req.category === "aluminium" ? "ألمنيوم" : "متنوع"}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between text-[10px]">
                          <span className="text-muted-foreground">
                            بواسطة: {req.requestedBy} • {req.requestedAt}
                          </span>
                          <Badge variant="outline" className="text-[8px] h-4">
                            {req.division === "europe" ? "أوروبا" : "الصين"}
                          </Badge>
                        </div>
                        {req.notes && (
                          <p className="text-[10px] text-muted-foreground p-2 rounded bg-muted/30">{req.notes}</p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* ── Create Request Dialog ── */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="!max-w-lg !p-0 !gap-0">
          <DialogTitle className="sr-only">طلب صنف جديد</DialogTitle>
          <DialogDescription className="sr-only">نموذج طلب صنف</DialogDescription>
          <div>
            <div className="p-5 border-b border-border/40 bg-gradient-to-l from-primary/5 to-transparent">
              <div className="flex items-center gap-2">
                <PackagePlus className="w-5 h-5 text-primary" />
                <h3 className="text-sm text-foreground">طلب صنف جديد</h3>
              </div>
            </div>
            <div className="p-5 space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs text-muted-foreground">اسم الصنف</label>
                <Input className="h-9 text-xs" placeholder="مثال: قارورة عطر بيضاوية" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs text-muted-foreground">الحجم</label>
                  <Input className="h-9 text-xs" placeholder="مثال: 100" type="number" />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs text-muted-foreground">الوحدة</label>
                  <select className="w-full h-9 rounded-md border border-input bg-input-background px-3 text-xs text-foreground">
                    <option value="ml">مل (ml)</option>
                    <option value="kg">كغ (kg)</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs text-muted-foreground">الكمية</label>
                  <Input className="h-9 text-xs" placeholder="مثال: 5000" type="number" />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs text-muted-foreground">التصنيف</label>
                  <select className="w-full h-9 rounded-md border border-input bg-input-background px-3 text-xs text-foreground">
                    <option value="perfume">عطور</option>
                    <option value="glass">زجاجيات</option>
                    <option value="aluminium">ألمنيوم</option>
                    <option value="mixed">متنوع</option>
                  </select>
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs text-muted-foreground">القسم</label>
                <select className="w-full h-9 rounded-md border border-input bg-input-background px-3 text-xs text-foreground">
                  <option value="europe">أوروبا</option>
                  <option value="china">الصين</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs text-muted-foreground">صورة (اختياري)</label>
                <div className="border-2 border-dashed border-border/50 rounded-lg p-6 text-center cursor-pointer hover:border-primary/30 transition-colors">
                  <ImageIcon className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                  <p className="text-[10px] text-muted-foreground">اسحب صورة أو اضغط للاختيار</p>
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs text-muted-foreground">ملاحظات</label>
                <textarea className="w-full h-16 rounded-md border border-input bg-input-background px-3 py-2 text-xs text-foreground resize-none" placeholder="ملاحظات إضافية..." />
              </div>
              <div className="flex justify-end gap-2 pt-2 border-t border-border/30">
                <Button variant="outline" size="sm" className="text-xs" onClick={() => setShowCreate(false)}>إلغاء</Button>
                <Button size="sm" className="text-xs gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  إرسال الطلب
                </Button>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}