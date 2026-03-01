import { useState } from "react";
import { motion } from "motion/react";
import {
  Phone,
  Mail,
  MapPin,
  Star,
  MessageCircle,
  ExternalLink,
  Globe,
  User,
  Search,
  Building2,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Input } from "../ui/input";
import { Avatar, AvatarFallback } from "../ui/avatar";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "../ui/dialog";
import { ScrollArea } from "../ui/scroll-area";
import {
  suppliers,
  purchaseOrders,
  currencyLabels,
  currencySymbols,
  type Supplier,
  type Division,
} from "./sc-data";

const fmt = (n: number) => new Intl.NumberFormat("ar-SA").format(n);

export function SCSuppliers() {
  const [divisionFilter, setDivisionFilter] = useState<"all" | Division>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);

  const filtered = suppliers.filter((s) => {
    if (divisionFilter !== "all" && s.division !== divisionFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return s.name.includes(searchQuery) || s.nameEn.toLowerCase().includes(q);
    }
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex gap-1 p-0.5 rounded-md bg-secondary/40 border border-border/40">
          {([
            { key: "all" as const, label: "الكل" },
            { key: "europe" as const, label: "أوروبا" },
            { key: "china" as const, label: "الصين" },
          ]).map((d) => (
            <button
              key={d.key}
              onClick={() => setDivisionFilter(d.key)}
              className={`px-3 py-1.5 rounded text-xs transition-all ${
                divisionFilter === d.key
                  ? "bg-card text-primary shadow-sm border border-primary/20"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {d.label}
            </button>
          ))}
        </div>
        <div className="relative">
          <Search className="absolute start-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
          <Input
            placeholder="بحث عن مورد..."
            className="h-8 text-xs ps-8 w-52"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Supplier Cards */}
      <div className="grid grid-cols-8 gap-2">
        {filtered.map((supplier, i) => {
          const supplierPOs = purchaseOrders.filter((po) => po.supplierId === supplier.id);
          return (
            <motion.div
              key={supplier.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Card
                className="border-border/50 hover:border-primary/30 transition-all cursor-pointer group"
                onClick={() => setSelectedSupplier(supplier)}
              >
                <CardContent className="p-3 space-y-2.5">
                  {/* Header */}
                  <div className="flex flex-col items-center text-center gap-1.5">
                    <Avatar className="w-10 h-10 border border-primary/20">
                      <AvatarFallback className="bg-primary/10 text-primary text-xs">{supplier.avatar}</AvatarFallback>
                    </Avatar>
                    <p className="text-xs text-foreground truncate w-full group-hover:text-primary transition-colors">{supplier.name}</p>
                  </div>

                  {/* Mini stats */}
                  <div className="flex items-center justify-around text-[10px] text-muted-foreground">
                    <span>{supplier.totalOrders} طلب</span>
                    <span className="text-primary flex items-center gap-0.5">
                      <Star className="w-2.5 h-2.5 fill-primary" />{supplier.rating}
                    </span>
                  </div>

                  {/* Country */}
                  <p className="text-[10px] text-muted-foreground text-center truncate">{supplier.country}</p>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* ── Supplier Detail Dialog ── */}
      <Dialog open={!!selectedSupplier} onOpenChange={(open) => { if (!open) setSelectedSupplier(null); }}>
        <DialogContent className="!max-w-2xl !p-0 !gap-0">
          <DialogTitle className="sr-only">بطاقة المورد</DialogTitle>
          <DialogDescription className="sr-only">تفاصيل المورد</DialogDescription>
          {selectedSupplier && (
            <div>
              {/* Header */}
              <div className="p-5 border-b border-border/40 bg-gradient-to-l from-primary/5 to-transparent">
                <div className="flex items-center gap-4">
                  <Avatar className="w-14 h-14 border-2 border-primary/30">
                    <AvatarFallback className="bg-primary/10 text-primary text-lg">{selectedSupplier.avatar}</AvatarFallback>
                  </Avatar>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-foreground">{selectedSupplier.name}</h3>
                      <Badge className={`text-[9px] border-transparent ${selectedSupplier.status === "active" ? "bg-emerald-500/15 text-emerald-500" : "bg-muted text-muted-foreground"}`}>
                        {selectedSupplier.status === "active" ? "نشط" : "غير نشط"}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5" style={{ direction: "ltr", unicodeBidi: "embed" }}>{selectedSupplier.nameEn}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="text-[9px]">{selectedSupplier.division === "europe" ? "أوروبا" : "الصين"}</Badge>
                      <Badge variant="outline" className="text-[9px]">{currencyLabels[selectedSupplier.currency]}</Badge>
                      <span className="text-xs text-primary flex items-center gap-0.5">
                        <Star className="w-3 h-3 fill-primary" />
                        {selectedSupplier.rating}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <ScrollArea className="max-h-[60vh]" dir="rtl">
                <div className="p-5 space-y-4">
                  {/* Contact Info */}
                  <Card className="border-border/50">
                    <CardContent className="p-4 space-y-3">
                      <h4 className="text-xs text-muted-foreground flex items-center gap-1.5">
                        <User className="w-3.5 h-3.5 text-primary" />
                        معلومات التواصل
                      </h4>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <p className="text-[10px] text-muted-foreground">المسؤول</p>
                          <p className="text-xs text-foreground">{selectedSupplier.contactPerson}</p>
                          <p className="text-[10px] text-muted-foreground">{selectedSupplier.contactRole}</p>
                        </div>
                        <div className="space-y-1">
                          <p className="text-[10px] text-muted-foreground">الممثل المعتمد</p>
                          <p className="text-xs text-foreground">{selectedSupplier.authorizedRep}</p>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 text-xs">
                          <Phone className="w-3.5 h-3.5 text-muted-foreground" />
                          <span style={{ direction: "ltr", unicodeBidi: "embed" }}>{selectedSupplier.phone}</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <Mail className="w-3.5 h-3.5 text-muted-foreground" />
                          <span style={{ direction: "ltr", unicodeBidi: "embed" }}>{selectedSupplier.email}</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <MapPin className="w-3.5 h-3.5 text-muted-foreground" />
                          <span>{selectedSupplier.address}</span>
                        </div>
                        {selectedSupplier.whatsapp && (
                          <div className="flex items-center gap-2 text-xs">
                            <MessageCircle className="w-3.5 h-3.5 text-emerald-500" />
                            <span className="text-emerald-500" style={{ direction: "ltr", unicodeBidi: "embed" }}>WhatsApp: {selectedSupplier.whatsapp}</span>
                          </div>
                        )}
                        {selectedSupplier.wechat && (
                          <div className="flex items-center gap-2 text-xs">
                            <MessageCircle className="w-3.5 h-3.5 text-emerald-500" />
                            <span className="text-emerald-500" style={{ direction: "ltr", unicodeBidi: "embed" }}>WeChat: {selectedSupplier.wechat}</span>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 rounded-lg bg-muted/30 text-center">
                      <p className="text-[10px] text-muted-foreground">إجمالي الطلبات</p>
                      <p className="text-lg text-foreground">{selectedSupplier.totalOrders}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-muted/30 text-center">
                      <p className="text-[10px] text-muted-foreground">إجمالي القيمة</p>
                      <p className="text-lg text-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                        {currencySymbols[selectedSupplier.currency]} {fmt(selectedSupplier.totalValue)}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-muted/30 text-center">
                      <p className="text-[10px] text-muted-foreground">أوامر نشطة</p>
                      <p className="text-lg text-foreground">
                        {purchaseOrders.filter((po) => po.supplierId === selectedSupplier.id && !["received", "cancelled"].includes(po.status)).length}
                      </p>
                    </div>
                  </div>

                  {/* Notes */}
                  {selectedSupplier.notes && (
                    <div className="p-3 rounded-lg bg-muted/30 text-xs text-muted-foreground">
                      <span className="text-foreground">ملاحظات: </span>
                      {selectedSupplier.notes}
                    </div>
                  )}

                  {/* Tags */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[10px] text-muted-foreground">التصنيفات:</span>
                    {selectedSupplier.tags.map((tag) => (
                      <Badge key={tag} variant="outline" className="text-[9px] h-5">{tag}</Badge>
                    ))}
                  </div>
                </div>
              </ScrollArea>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}