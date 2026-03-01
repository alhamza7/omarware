import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Ship,
  Anchor,
  CheckCircle2,
  Clock,
  MapPin,
  FileText,
  MessageSquare,
  Bell,
  Truck,
  AlertTriangle,
  ExternalLink,
  Plus,
  Upload,
  User,
  Calendar,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "../ui/dialog";
import { ScrollArea } from "../ui/scroll-area";
import {
  containers,
  containerStatusConfig,
  purchaseOrders,
  poStatusConfig,
  currencySymbols,
  type Container,
} from "./sc-data";

type StatusFilter = "all" | Container["status"];

const fmt = (n: number) => new Intl.NumberFormat("ar-SA").format(n);

const statusTabs: { key: StatusFilter; label: string; icon: typeof Ship }[] = [
  { key: "all", label: "الكل", icon: Ship },
  { key: "active", label: "نشطة", icon: Ship },
  { key: "at-port", label: "في الميناء", icon: Anchor },
  { key: "arriving-soon", label: "تصل قريباً", icon: Clock },
  { key: "completed", label: "مكتملة", icon: CheckCircle2 },
];

export function SCContainers() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [selectedContainer, setSelectedContainer] = useState<Container | null>(null);
  const [dialogTab, setDialogTab] = useState<"info" | "pos" | "comments" | "attachments">("info");

  const filtered = containers.filter((c) => statusFilter === "all" || c.status === statusFilter);

  return (
    <div className="space-y-4">
      {/* Status Tabs */}
      <div className="flex gap-1.5 p-1 rounded-lg bg-secondary/40 border border-border/40">
        {statusTabs.map((tab) => {
          const Icon = tab.icon;
          const count = tab.key === "all" ? containers.length : containers.filter((c) => c.status === tab.key).length;
          const isActive = statusFilter === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setStatusFilter(tab.key)}
              className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-md text-xs transition-all ${
                isActive
                  ? "bg-card text-primary shadow-sm border border-primary/20"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
              <span className={`text-[9px] min-w-[16px] text-center px-1 rounded-full ${
                isActive ? "bg-primary/10 text-primary" : "bg-muted text-muted-foreground"
              }`}>{count}</span>
            </button>
          );
        })}
      </div>

      {/* Add Container Button */}
      <div className="flex justify-end">
        <Button size="sm" className="text-xs gap-1.5">
          <Plus className="w-3.5 h-3.5" />
          إضافة حاوية
        </Button>
      </div>

      {/* Container Cards */}
      <div className="grid grid-cols-2 gap-4">
        <AnimatePresence mode="popLayout">
          {filtered.map((container, i) => {
            const conf = containerStatusConfig[container.status];
            return (
              <motion.div
                key={container.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: i * 0.05 }}
                layout
              >
                <Card
                  className="border-border/50 hover:border-primary/30 transition-all cursor-pointer group"
                  onClick={() => { setSelectedContainer(container); setDialogTab("info"); }}
                >
                  <CardContent className="p-4 space-y-3">
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                          container.status === "active" ? "bg-blue-500/10" :
                          container.status === "at-port" ? "bg-primary/10" :
                          container.status === "arriving-soon" ? "bg-violet-500/10" :
                          "bg-emerald-500/10"
                        }`}>
                          <Ship className={`w-5 h-5 ${
                            container.status === "active" ? "text-blue-500" :
                            container.status === "at-port" ? "text-primary" :
                            container.status === "arriving-soon" ? "text-violet-500" :
                            "text-emerald-500"
                          }`} />
                        </div>
                        <div>
                          <p className="text-sm text-foreground group-hover:text-primary transition-colors">{container.name}</p>
                          <a
                            href={`https://www.searates.com/container/tracking/?number=${container.containerNumber}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[10px] text-primary hover:underline flex items-center gap-1"
                            onClick={(e) => e.stopPropagation()}
                            style={{ direction: "ltr", unicodeBidi: "embed" }}
                          >
                            {container.containerNumber}
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        </div>
                      </div>
                      <Badge className={`text-[9px] border-transparent ${conf.color}`}>{conf.label}</Badge>
                    </div>

                    {/* Info Grid */}
                    <div className="grid grid-cols-2 gap-2 text-[10px]">
                      <div className="flex items-center gap-1.5 text-muted-foreground">
                        <MapPin className="w-3 h-3 shrink-0" />
                        <span className="truncate">{container.departureLocation}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-muted-foreground">
                        <Calendar className="w-3 h-3 shrink-0" />
                        <span>الوصول: {container.expectedArrival}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <FileText className="w-3 h-3 shrink-0 text-muted-foreground" />
                        <span className={container.documentsDelivered ? "text-emerald-500" : "text-red-500"}>
                          {container.documentsDelivered ? "المستندات مُسلّمة" : "المستندات لم تُسلّم!"}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5 text-muted-foreground">
                        <User className="w-3 h-3 shrink-0" />
                        <span className="truncate">{container.clearanceCompanyName}</span>
                      </div>
                    </div>

                    {/* Tags */}
                    <div className="flex items-center gap-1 flex-wrap">
                      {container.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-[8px] h-4 px-1.5">{tag}</Badge>
                      ))}
                    </div>

                    {/* Location */}
                    <div className="p-2 rounded-md bg-muted/30 text-[10px] text-muted-foreground flex items-center gap-1.5">
                      <MapPin className="w-3 h-3 text-primary shrink-0" />
                      {container.currentLocation}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* ── Container Detail Dialog ── */}
      <Dialog open={!!selectedContainer} onOpenChange={(open) => { if (!open) setSelectedContainer(null); }}>
        <DialogContent className="!max-w-4xl !p-0 !gap-0 max-h-[90vh]">
          <DialogTitle className="sr-only">تفاصيل الحاوية</DialogTitle>
          <DialogDescription className="sr-only">عرض جميع تفاصيل الحاوية</DialogDescription>
          {selectedContainer && (
            <div className="flex flex-col max-h-[90vh]">
              {/* Dialog Header */}
              <div className="p-5 border-b border-border/40 bg-gradient-to-l from-primary/5 to-transparent shrink-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-xl bg-primary/10 flex items-center justify-center">
                      <Ship className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-foreground">{selectedContainer.name}</h3>
                        <Badge className={`text-[9px] border-transparent ${containerStatusConfig[selectedContainer.status].color}`}>
                          {containerStatusConfig[selectedContainer.status].label}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-3 mt-0.5">
                        <a
                          href={`https://www.searates.com/container/tracking/?number=${selectedContainer.containerNumber}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-primary hover:underline flex items-center gap-1"
                          style={{ direction: "ltr", unicodeBidi: "embed" }}
                        >
                          {selectedContainer.containerNumber}
                          <ExternalLink className="w-3 h-3" />
                        </a>
                        <span className="text-[10px] text-muted-foreground">{selectedContainer.type}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" className="text-[10px] h-7 gap-1">
                      <Truck className="w-3 h-3" />
                      تعيين سائق
                    </Button>
                    <Button variant="outline" size="sm" className="text-[10px] h-7 gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      إضافة غرامة
                    </Button>
                    <Button variant="outline" size="sm" className="text-[10px] h-7 gap-1">
                      <Upload className="w-3 h-3" />
                      رفع مستندات
                    </Button>
                    <Button variant="outline" size="sm" className="text-[10px] h-7 gap-1">
                      <Bell className="w-3 h-3" />
                      تذكير
                    </Button>
                  </div>
                </div>
              </div>

              {/* Dialog Tabs */}
              <div className="flex gap-1 px-5 pt-3 border-b border-border/40 shrink-0">
                {([
                  { key: "info" as const, label: "المعلومات", icon: FileText },
                  { key: "pos" as const, label: "أوامر الشراء", icon: FileText },
                  { key: "comments" as const, label: `التعليقات (${selectedContainer.comments.length})`, icon: MessageSquare },
                  { key: "attachments" as const, label: `المرفقات (${selectedContainer.attachments.length})`, icon: FileText },
                ]).map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setDialogTab(tab.key)}
                    className={`px-3 py-2 text-xs border-b-2 transition-all ${
                      dialogTab === tab.key
                        ? "border-primary text-primary"
                        : "border-transparent text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Dialog Content */}
              <ScrollArea className="flex-1" dir="rtl">
                <div className="p-5 space-y-4">
                  {dialogTab === "info" && (
                    <>
                      {/* Shipping Details */}
                      <div className="grid grid-cols-3 gap-3">
                        {([
                          { label: "موقع الانطلاق", value: selectedContainer.departureLocation, icon: MapPin },
                          { label: "تاريخ الانطلاق", value: selectedContainer.departureDate, icon: Calendar },
                          { label: "الوصول المتوقع", value: selectedContainer.expectedArrival, icon: Clock },
                          { label: "رقم البوليصة", value: selectedContainer.blNumber, icon: FileText, ltr: true },
                          { label: "رقم الفاتورة", value: selectedContainer.invoiceNumber, icon: FileText, ltr: true },
                          { label: "نوع الحاوية", value: selectedContainer.containerType === "perfume" ? "عطور" : selectedContainer.containerType === "glass" ? "زجاجيات" : selectedContainer.containerType === "alcohol" ? "كحول" : "مختلط", icon: FileText },
                        ] as const).map((field, idx) => {
                          const Icon = field.icon;
                          return (
                            <div key={idx} className="p-3 rounded-lg bg-muted/30 space-y-1">
                              <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                                <Icon className="w-3 h-3" />
                                {field.label}
                              </div>
                              <p className="text-xs text-foreground" style={field.ltr ? { direction: "ltr", unicodeBidi: "embed" } : undefined}>
                                {field.value}
                              </p>
                            </div>
                          );
                        })}
                      </div>

                      {/* Clearance Info */}
                      <Card className="border-border/50">
                        <CardContent className="p-4 space-y-3">
                          <h4 className="text-xs text-muted-foreground flex items-center gap-1.5">
                            <CheckCircle2 className="w-3.5 h-3.5 text-primary" />
                            معلومات التخليص
                          </h4>
                          <div className="grid grid-cols-2 gap-3">
                            <div className="space-y-1">
                              <p className="text-[10px] text-muted-foreground">المخلص المعني</p>
                              <p className="text-xs text-foreground">{selectedContainer.clearanceCompanyName}</p>
                            </div>
                            <div className="space-y-1">
                              <p className="text-[10px] text-muted-foreground">تسليم المستندات</p>
                              <p className={`text-xs ${selectedContainer.documentsDelivered ? "text-emerald-500" : "text-red-500"}`}>
                                {selectedContainer.documentsDelivered ? "تم التسليم ✓" : "لم يتم التسليم ✗"}
                              </p>
                            </div>
                            <div className="space-y-1">
                              <p className="text-[10px] text-muted-foreground">مدة التخليص</p>
                              <p className="text-xs text-foreground">{selectedContainer.clearanceDuration}</p>
                            </div>
                            <div className="space-y-1">
                              <p className="text-[10px] text-muted-foreground">مدة السماح</p>
                              <p className="text-xs text-foreground">{selectedContainer.gracePeriod}</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      {/* Driver */}
                      {selectedContainer.driver && (
                        <Card className="border-border/50">
                          <CardContent className="p-4">
                            <div className="flex items-center gap-3">
                              <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center">
                                <Truck className="w-4 h-4 text-primary" />
                              </div>
                              <div>
                                <p className="text-xs text-foreground">{selectedContainer.driver}</p>
                                <p className="text-[10px] text-muted-foreground">
                                  <span style={{ direction: "ltr", unicodeBidi: "embed" }}>{selectedContainer.driverPhone}</span>
                                </p>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      )}

                      {/* Current Location */}
                      <div className="p-3 rounded-lg bg-primary/5 border border-primary/20 flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-primary shrink-0" />
                        <div>
                          <p className="text-[10px] text-muted-foreground">الموقع الحالي</p>
                          <p className="text-xs text-foreground">{selectedContainer.currentLocation}</p>
                        </div>
                      </div>

                      {/* Penalties */}
                      {selectedContainer.penalties.length > 0 && (
                        <Card className="border-red-500/20">
                          <CardContent className="p-4 space-y-2">
                            <h4 className="text-xs text-red-500 flex items-center gap-1.5">
                              <AlertTriangle className="w-3.5 h-3.5" />
                              الغرامات
                            </h4>
                            {selectedContainer.penalties.map((p, idx) => (
                              <div key={idx} className="flex items-center justify-between p-2 rounded bg-red-500/5">
                                <div>
                                  <p className="text-xs text-foreground">{p.reason}</p>
                                  <p className="text-[10px] text-muted-foreground">{p.date}</p>
                                </div>
                                <span className="text-xs text-red-500">{fmt(p.amount)} $</span>
                              </div>
                            ))}
                          </CardContent>
                        </Card>
                      )}

                      {/* Tags */}
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[10px] text-muted-foreground">التصنيفات:</span>
                        {selectedContainer.tags.map((tag) => (
                          <Badge key={tag} variant="outline" className="text-[9px] h-5">{tag}</Badge>
                        ))}
                        <Button variant="ghost" size="sm" className="h-5 w-5 p-0">
                          <Plus className="w-3 h-3" />
                        </Button>
                      </div>
                    </>
                  )}

                  {dialogTab === "pos" && (
                    <div className="space-y-3">
                      {selectedContainer.purchaseOrderIds.length === 0 ? (
                        <div className="text-center py-8 text-xs text-muted-foreground">
                          لا توجد أوامر شراء مرتبطة بهذه الحاوية
                        </div>
                      ) : (
                        selectedContainer.purchaseOrderIds.map((poId) => {
                          const po = purchaseOrders.find((p) => p.id === poId);
                          if (!po) return null;
                          const conf = poStatusConfig[po.status];
                          return (
                            <Card key={po.id} className="border-border/50">
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between mb-3">
                                  <div className="flex items-center gap-2">
                                    <span className="text-sm text-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>{po.id}</span>
                                    <Badge className={`text-[9px] border-transparent ${conf.color}`}>{conf.label}</Badge>
                                  </div>
                                  <span className="text-xs text-primary" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                                    {currencySymbols[po.currency]} {fmt(po.totalAmount)}
                                  </span>
                                </div>
                                <div className="space-y-1">
                                  {po.items.map((item) => (
                                    <div key={item.id} className="flex items-center justify-between text-[10px] py-1 border-b border-border/20 last:border-0">
                                      <span className="text-foreground">{item.name}</span>
                                      <span className="text-muted-foreground">{fmt(item.qty)} وحدة</span>
                                    </div>
                                  ))}
                                </div>
                              </CardContent>
                            </Card>
                          );
                        })
                      )}
                    </div>
                  )}

                  {dialogTab === "comments" && (
                    <div className="space-y-3">
                      {selectedContainer.comments.map((comment) => (
                        <div key={comment.id} className="flex gap-3">
                          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0 text-[10px] text-primary">
                            {comment.user.slice(0, 2)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-foreground">{comment.user}</span>
                              <span className="text-[9px] text-muted-foreground">{comment.date}</span>
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">{comment.text}</p>
                          </div>
                        </div>
                      ))}
                      <div className="flex gap-2 mt-4">
                        <textarea
                          className="flex-1 h-16 rounded-md border border-input bg-input-background px-3 py-2 text-xs text-foreground resize-none"
                          placeholder="أضف تعليقاً..."
                        />
                        <Button size="sm" className="text-xs self-end">إرسال</Button>
                      </div>
                    </div>
                  )}

                  {dialogTab === "attachments" && (
                    <div className="space-y-3">
                      {selectedContainer.attachments.map((att) => (
                        <div key={att.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                          <div className="flex items-center gap-3">
                            <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center">
                              <FileText className="w-4 h-4 text-primary" />
                            </div>
                            <div>
                              <p className="text-xs text-foreground">{att.name}</p>
                              <p className="text-[10px] text-muted-foreground">{att.uploadedBy} • {att.uploadedAt} • {att.size}</p>
                            </div>
                          </div>
                          <Button variant="ghost" size="sm" className="h-7 text-[10px]">تحميل</Button>
                        </div>
                      ))}
                      <Button variant="outline" size="sm" className="text-xs gap-1.5 w-full">
                        <Upload className="w-3.5 h-3.5" />
                        رفع مرفق جديد
                      </Button>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}