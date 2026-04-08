import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Phone,
  PhoneOff,
  PhoneIncoming,
  PhoneOutgoing,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Pause,
  Play,
  Crown,
  Tag,
  MapPin,
  Mail,
  Calendar,
  Heart,
  CreditCard,
  Banknote,
  Receipt,
  FileText,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Clock,
  CheckCircle2,
  PhoneForwarded,
  ArrowUpCircle,
  Voicemail,
  Clipboard,
  ShoppingCart,
  RotateCcw,
  Send,
  Ticket,
  BookOpen,
  Bot,
  Star,
  Shield,
  TrendingUp,
  Eye,
  Wallet,
  DollarSign,
  CalendarClock,
  ClipboardCheck,
  MessageSquare,
  X,
  Save,
  Sparkles,
  Droplets,
  GlassWater,
  FlaskConical,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { Progress } from "../ui/progress";
import { Textarea } from "../ui/textarea";
import { Dialog, DialogContent, DialogTitle } from "../ui/dialog";
import { ScrollArea } from "../ui/scroll-area";
import {
  type CallCustomerProfile,
  type AISummary,
  type Invoice,
  type GuidedStep,
  guidedWorkflow,
} from "./cc-data";
import { InvoiceCreationDialog } from "../invoice-creation-dialog";

// ── Helpers ────────────────────────────────────────

function fmt(n: number) { return n.toLocaleString(); }
function fmtDur(sec: number) {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

const invStatusConf: Record<string, { label: string; color: string }> = {
  paid:    { label: "مدفوعة",   color: "bg-emerald-500/10 text-emerald-500" },
  partial: { label: "جزئي",     color: "bg-primary/10 text-primary" },
  unpaid:  { label: "غير مدفوعة", color: "bg-blue-500/10 text-blue-500" },
  overdue: { label: "متأخرة",   color: "bg-red-500/10 text-red-500" },
};

const payMethodConf: Record<string, string> = {
  cash: "نقدي",
  card: "بطاقة",
  bank: "حوالة",
  qi: "QI",
};

const outcomeOpts: { key: string; label: string; icon: typeof CheckCircle2; color: string }[] = [
  { key: "resolved",  label: "تم الحل",      icon: CheckCircle2,  color: "text-emerald-500" },
  { key: "callback",  label: "معاودة اتصال", icon: PhoneForwarded, color: "text-primary" },
  { key: "escalated", label: "تصعيد",        icon: ArrowUpCircle, color: "text-red-500" },
  { key: "voicemail", label: "بريد صوتي",    icon: Voicemail,     color: "text-purple-500" },
];

// ── Props ──────────────────────────────────────────

interface ActiveCallProps {
  open: boolean;
  onClose: () => void;
  customer: CallCustomerProfile;
  callType: "inbound" | "outbound";
  channel: string;
}

// ── Component ──────────────────────────────────────

export function CCActiveCall({ open, onClose, customer, callType, channel }: ActiveCallProps) {
  // ── State
  const [elapsed, setElapsed] = useState(0);
  const [muted, setMuted] = useState(false);
  const [volumeOn, setVolumeOn] = useState(true);
  const [onHold, setOnHold] = useState(false);
  const [callActive, setCallActive] = useState(true);
  const [notes, setNotes] = useState("");
  const [outcome, setOutcome] = useState<string | null>(null);
  const [guidedStep, setGuidedStep] = useState(0);
  const [showInvoice, setShowInvoice] = useState<Invoice | null>(null);
  const [showReorder, setShowReorder] = useState(false);
  const [showInvoiceCreate, setShowInvoiceCreate] = useState(false);
  const [financeOpen, setFinanceOpen] = useState(true);
  const [rightTab, setRightTab] = useState<"orders" | "script" | "frequent" | "ai">("script");
  const [wrapUpDone, setWrapUpDone] = useState<Set<string>>(new Set());
  const [saved, setSaved] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // AI summary (simulated)
  const aiSummary: AISummary = {
    agentName: "سارة الحربي",
    duration: fmtDur(elapsed),
    keyPoints: [
      "العميل استفسر عن مجموعة عطور الربيع الجديدة",
      "طلب معرفة أسعار عود ملكي بالحجم الكبير",
      "اهتمام بمجموعة هدايا لمناسبة خاصة",
      "ذُكرت ملاحظة عن تأخر توصيل الطلب السابق",
    ],
    situationStatus: outcome === "resolved" ? "resolved" : outcome === "escalated" ? "escalated" : "pending",
    qaScore: 92,
    issuesFound: ["تأخر توصيل مذكور — يجب المتابعة مع اللوجستيك"],
    invoiceMade: showReorder ? { id: "INV-2024-090", status: "مسودة" } : undefined,
    discountSuggestions: ["خصم 10% على مجموعة الربيع (عميل VIP بلاتيني)", "شحن مجاني للطلبات فوق 500 ر.س"],
  };

  // Timer
  useEffect(() => {
    if (open && callActive) {
      timerRef.current = setInterval(() => setElapsed((p) => p + 1), 1000);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [open, callActive]);

  // Reset on open
  useEffect(() => {
    if (open) {
      setElapsed(0);
      setCallActive(true);
      setMuted(false);
      setVolumeOn(true);
      setOnHold(false);
      setNotes("");
      setOutcome(null);
      setGuidedStep(0);
      setShowInvoice(null);
      setShowReorder(false);
      setShowInvoiceCreate(false);
      setWrapUpDone(new Set());
      setSaved(false);
    }
  }, [open]);

  const endCall = () => {
    setCallActive(false);
    if (timerRef.current) clearInterval(timerRef.current);
  };

  const handleWrapUp = (action: string) => {
    setWrapUpDone((p) => new Set([...p, action]));
  };

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => onClose(), 1200);
  };

  const canClose = !callActive && (wrapUpDone.size >= 2 || saved);

  // ── Render ───────────────────────────────────────

  return (
    <>
    <Dialog open={open} onOpenChange={(v) => { if (!v && canClose) onClose(); }}>
      <DialogContent
        className="!flex !flex-col !max-w-[98vw] sm:!max-w-[98vw] !w-[1400px] !h-[92vh] !p-0 !gap-0 overflow-hidden border-primary/20 bg-card rounded-2xl"
        onInteractOutside={(e) => e.preventDefault()}
        aria-describedby={undefined}
      >
        <DialogTitle className="sr-only">مكالمة نشطة — {customer.name}</DialogTitle>

          {/* ═══ TOP BAR: Call Controls ═══ */}
          <div className={`shrink-0 border-b px-5 py-3 flex items-center gap-4 ${
            callActive ? "bg-gradient-to-l from-emerald-500/10 via-transparent to-transparent border-emerald-500/20"
                       : "bg-gradient-to-l from-muted/30 via-transparent to-transparent border-border/50"
          }`}>
            {/* Call type indicator */}
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              callActive ? "bg-emerald-500/10" : "bg-muted"
            }`}>
              {callType === "inbound"
                ? <PhoneIncoming className={`w-5 h-5 ${callActive ? "text-emerald-500" : "text-muted-foreground"}`} />
                : <PhoneOutgoing className={`w-5 h-5 ${callActive ? "text-blue-500" : "text-muted-foreground"}`} />
              }
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="text-sm text-foreground truncate">{customer.name}</h3>
                {customer.vip && (
                  <Badge className="bg-primary/10 text-primary border-primary/20 text-[10px] gap-0.5">
                    <Crown className="w-2.5 h-2.5" /> VIP
                  </Badge>
                )}
                <Badge variant="outline" className="text-[10px]">
                  {callType === "inbound" ? "وارد" : "صادر"}
                </Badge>
                <Badge variant="outline" className="text-[10px]">{channel}</Badge>
              </div>
              <p className="text-xs text-muted-foreground font-mono" dir="ltr">{customer.phone}</p>
            </div>

            {/* Duration */}
            <div className="text-center px-4">
              <div className={`text-2xl font-mono tabular-nums ${
                callActive ? "text-emerald-500" : "text-muted-foreground"
              }`} dir="ltr">
                {fmtDur(elapsed)}
              </div>
              <p className="text-[10px] text-muted-foreground">
                {callActive ? "مكالمة نشطة" : "انتهت المكالمة"}
              </p>
            </div>

            {/* Call Controls */}
            {callActive ? (
              <div className="flex items-center gap-2">
                <Button
                  variant={muted ? "default" : "outline"}
                  size="icon"
                  className={`h-9 w-9 rounded-full ${muted ? "bg-red-500/80 hover:bg-red-500 text-white" : ""}`}
                  onClick={() => setMuted(!muted)}
                  title={muted ? "إلغاء الكتم" : "كتم الصوت"}
                >
                  {muted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </Button>
                <Button
                  variant={!volumeOn ? "default" : "outline"}
                  size="icon"
                  className={`h-9 w-9 rounded-full ${!volumeOn ? "bg-red-500/80 hover:bg-red-500 text-white" : ""}`}
                  onClick={() => setVolumeOn(!volumeOn)}
                >
                  {volumeOn ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
                </Button>
                <Button
                  variant={onHold ? "default" : "outline"}
                  size="icon"
                  className={`h-9 w-9 rounded-full ${onHold ? "bg-primary text-primary-foreground" : ""}`}
                  onClick={() => setOnHold(!onHold)}
                >
                  {onHold ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                </Button>
                <div className="w-px h-6 bg-border/50 mx-1" />
                <Button
                  onClick={endCall}
                  className="h-9 gap-2 bg-red-600 hover:bg-red-700 text-white rounded-full px-5"
                >
                  <PhoneOff className="w-4 h-4" />
                  إنهاء
                </Button>
              </div>
            ) : (
              <Badge className="bg-muted text-muted-foreground border-transparent">
                انتهت المكالمة — {fmtDur(elapsed)}
              </Badge>
            )}
          </div>

          {/* ═══ MAIN BODY ═══ */}
          <div className="flex-1 flex overflow-hidden min-h-0">
            {/* ──── LEFT PANEL: Customer & Finance ──── */}
            <div className="w-[340px] shrink-0 border-e border-border/50 flex flex-col bg-secondary/10">
              {/* Customer card — pinned at top */}
              <div className="shrink-0 p-4 pb-0 border-b border-border/30">
              <Card className="border-primary/20 mb-4">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3 mb-3">
                    <Avatar className="h-12 w-12 border-2 border-primary/30">
                      <AvatarFallback className="bg-primary/10 text-primary text-lg">{customer.avatar}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm text-foreground">{customer.name}</h4>
                      <p className="text-[10px] text-muted-foreground">{customer.id} · {customer.segment}</p>
                    </div>
                  </div>
                  <div className="space-y-1.5 text-xs text-muted-foreground">
                    <p className="flex items-center gap-2"><Mail className="w-3 h-3" /><span dir="ltr">{customer.email}</span></p>
                    <p className="flex items-center gap-2"><Phone className="w-3 h-3" /><span dir="ltr">{customer.phone}</span></p>
                    <p className="flex items-center gap-2"><MapPin className="w-3 h-3" />{customer.address}</p>
                    <p className="flex items-center gap-2"><Calendar className="w-3 h-3" />عميل منذ {new Date(customer.joinDate).toLocaleDateString("ar-SA")}</p>
                    {customer.favoriteFragrance && (
                      <p className="flex items-center gap-2"><Heart className="w-3 h-3 text-pink-500" />{customer.favoriteFragrance}</p>
                    )}
                  </div>
                  <div className="flex gap-1.5 mt-3 flex-wrap">
                    {customer.tags.map((t) => (
                      <Badge key={t} variant="outline" className="text-[9px] h-5">{t}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
              </div>

              {/* Scrollable content */}
              <ScrollArea className="flex-1 min-h-0" dir="rtl">
                <div className="p-4 space-y-4">

              {/* Financial summary */}
              <Card className="border-border/50">
                <CardHeader className="pb-2 p-3">
                  <button
                    className="flex items-center justify-between w-full"
                    onClick={() => setFinanceOpen(!financeOpen)}
                  >
                    <CardTitle className="text-xs flex items-center gap-1.5">
                      <Wallet className="w-3.5 h-3.5 text-primary" />
                      الملخص المالي
                    </CardTitle>
                    {financeOpen ? <ChevronUp className="w-3.5 h-3.5 text-muted-foreground" /> : <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />}
                  </button>
                </CardHeader>
                <AnimatePresence>
                  {financeOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                    >
                      <CardContent className="p-3 pt-0 space-y-3">
                        {/* Balance (clickable) */}
                        <div className="p-2.5 rounded-lg bg-red-500/5 border border-red-500/20 cursor-pointer hover:bg-red-500/10 transition-colors">
                          <div className="flex justify-between items-center">
                            <span className="text-[10px] text-muted-foreground">الرصيد المستحق (الذمم)</span>
                            <Eye className="w-3 h-3 text-muted-foreground" />
                          </div>
                          <p className="text-lg text-red-500">{fmt(customer.finance.currentBalance)} <span className="text-[10px]">ر.س</span></p>
                        </div>

                        {/* Credit Control */}
                        <div className="space-y-2">
                          <p className="text-[10px] text-muted-foreground flex items-center gap-1"><Shield className="w-3 h-3" />ضبط الائتمان</p>
                          <div className="grid grid-cols-3 gap-2 text-center">
                            <div className="p-1.5 rounded bg-secondary/50">
                              <p className="text-[9px] text-muted-foreground">الحد الائتماني</p>
                              <p className="text-xs text-foreground">{fmt(customer.finance.creditLimit)}</p>
                            </div>
                            <div className="p-1.5 rounded bg-secondary/50">
                              <p className="text-[9px] text-muted-foreground">المستخدم</p>
                              <p className="text-xs text-red-500">{fmt(customer.finance.usedCredit)}</p>
                            </div>
                            <div className="p-1.5 rounded bg-secondary/50">
                              <p className="text-[9px] text-muted-foreground">المتاح</p>
                              <p className="text-xs text-emerald-500">{fmt(customer.finance.availableCredit)}</p>
                            </div>
                          </div>
                        </div>

                        {/* Collection */}
                        <div className="space-y-1.5">
                          <p className="text-[10px] text-muted-foreground flex items-center gap-1"><TrendingUp className="w-3 h-3" />التحصيل</p>
                          <div className="flex justify-between text-xs">
                            <span className="text-muted-foreground">إجمالي المحصّل</span>
                            <span className="text-emerald-500">{fmt(customer.finance.totalCollected)}</span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-muted-foreground">المستحق</span>
                            <span className="text-red-500">{fmt(customer.finance.totalOutstanding)}</span>
                          </div>
                          <div className="flex justify-between text-xs items-center">
                            <span className="text-muted-foreground">نسبة التحصيل</span>
                            <span className="text-primary">{customer.finance.collectionRate}%</span>
                          </div>
                          <Progress value={customer.finance.collectionRate} className="h-1.5" />
                        </div>

                        {/* Debt Aging */}
                        <div className="space-y-1.5">
                          <p className="text-[10px] text-muted-foreground flex items-center gap-1"><CalendarClock className="w-3 h-3" />أعمار الديون</p>
                          {[
                            { label: "حالي", val: customer.finance.debtAging.current, color: "bg-blue-500" },
                            { label: "30 يوم", val: customer.finance.debtAging.days30, color: "bg-primary" },
                            { label: "60 يوم", val: customer.finance.debtAging.days60, color: "bg-primary/70" },
                            { label: "90 يوم", val: customer.finance.debtAging.days90, color: "bg-red-500/70" },
                            { label: "+120 يوم", val: customer.finance.debtAging.days120plus, color: "bg-red-500" },
                          ].map((ag) => {
                            const maxVal = Math.max(
                              customer.finance.debtAging.current,
                              customer.finance.debtAging.days30,
                              customer.finance.debtAging.days60,
                              customer.finance.debtAging.days90,
                              customer.finance.debtAging.days120plus,
                              1,
                            );
                            const pct = (ag.val / maxVal) * 100;
                            return (
                            <div key={ag.label} className="space-y-0.5">
                              <div className="flex items-center gap-2 text-[10px]">
                                <span className={`w-2 h-2 rounded-full ${ag.color} shrink-0`} />
                                <span className="flex-1 text-muted-foreground">{ag.label}</span>
                                <span className={`${ag.val > 0 ? "text-foreground" : "text-muted-foreground/50"}`}>
                                  {fmt(ag.val)} ر.س
                                </span>
                              </div>
                              <div className="h-1.5 w-full rounded-full bg-secondary/50 overflow-hidden ms-4" style={{ width: "calc(100% - 1rem)" }}>
                                <div
                                  className={`h-full rounded-full ${ag.color} transition-all duration-500`}
                                  style={{ width: `${pct}%` }}
                                />
                              </div>
                            </div>
                            );
                          })}
                        </div>

                        {/* Outstanding Invoices */}
                        <div className="space-y-1.5">
                          <p className="text-[10px] text-muted-foreground flex items-center gap-1"><Receipt className="w-3 h-3" />الفواتير المستحقة</p>
                          {customer.invoices.filter((i) => i.status !== "paid").map((inv) => {
                            const conf = invStatusConf[inv.status];
                            return (
                              <div
                                key={inv.id}
                                className="flex items-center gap-2 p-2 rounded-lg bg-secondary/30 border border-border/50 cursor-pointer hover:border-primary/30 transition-colors text-[10px]"
                                onClick={() => setShowInvoice(inv)}
                              >
                                <FileText className="w-3 h-3 text-muted-foreground shrink-0" />
                                <span className="flex-1 text-foreground truncate">{inv.id}</span>
                                <Badge className={`text-[8px] border-transparent ${conf.color}`}>{conf.label}</Badge>
                                <span className="text-muted-foreground">{fmt(inv.amount - inv.paid)}</span>
                              </div>
                            );
                          })}
                        </div>

                        {/* Payment History */}
                        <div className="space-y-1.5">
                          <p className="text-[10px] text-muted-foreground flex items-center gap-1"><CreditCard className="w-3 h-3" />سجل الدفعات</p>
                          {customer.payments.slice(0, 3).map((pay) => (
                            <div key={pay.id} className="flex items-center gap-2 text-[10px] p-1.5 rounded bg-secondary/30">
                              <Banknote className="w-3 h-3 text-emerald-500 shrink-0" />
                              <span className="flex-1 text-muted-foreground truncate">{pay.reference}</span>
                              <Badge variant="outline" className="text-[8px]">{payMethodConf[pay.method]}</Badge>
                              <span className="text-emerald-500">{fmt(pay.amount)}</span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </motion.div>
                  )}
                </AnimatePresence>
              </Card>

              {/* Quick Actions */}
              <Card className="border-border/50">
                <CardHeader className="p-3 pb-2">
                  <CardTitle className="text-xs flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-primary" />
                    إجراءات سريعة
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-3 pt-0 grid grid-cols-2 gap-2">
                  <Button variant="outline" size="sm" className="text-[10px] h-8 gap-1" onClick={() => setShowInvoiceCreate(true)}>
                    <Receipt className="w-3 h-3" />إنشاء فاتورة
                  </Button>
                  <Button variant="outline" size="sm" className="text-[10px] h-8 gap-1">
                    <Ticket className="w-3 h-3" />فتح تذكرة
                  </Button>
                  <Button variant="outline" size="sm" className="text-[10px] h-8 gap-1">
                    <Send className="w-3 h-3 text-emerald-500" />إرسال الكتالوج
                  </Button>
                  <Button variant="outline" size="sm" className="text-[10px] h-8 gap-1">
                    <Banknote className="w-3 h-3 text-emerald-500" />تسجيل دفعة
                  </Button>
                </CardContent>
              </Card>
                </div>
              </ScrollArea>
            </div>

            {/* ──── RIGHT PANEL: Call Content ──── */}
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Tab bar */}
              <div className="shrink-0 flex gap-1 px-4 pt-3 border-b border-border/50 bg-secondary/5">
                {[
                  { id: "script" as const, label: "سير العمل", icon: BookOpen },
                  { id: "orders" as const, label: "آخر طلب", icon: ShoppingCart },
                  { id: "frequent" as const, label: "الأكثر طلباً", icon: RotateCcw },
                  { id: "ai" as const, label: "تحليل AI", icon: Bot },
                ].map((tab) => {
                  const Icon = tab.icon;
                  const isActive = rightTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setRightTab(tab.id)}
                      className={`flex items-center gap-1.5 px-3 pb-2.5 pt-1.5 text-xs border-b-2 transition-colors ${
                        isActive
                          ? "border-primary text-primary"
                          : "border-transparent text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      {tab.label}
                    </button>
                  );
                })}
              </div>

              {/* Content area */}
              <ScrollArea className="flex-1 min-h-0" dir="rtl">
                <div className="p-4 space-y-4">
                {/* ── SCRIPT / GUIDED WORKFLOW ── */}
                {rightTab === "script" && (
                  <div className="space-y-3">
                    <h4 className="text-sm text-muted-foreground flex items-center gap-2">
                      <BookOpen className="w-4 h-4 text-primary" />
                      سير العمل الموجّه
                    </h4>
                    {guidedWorkflow.map((step, i) => {
                      const isCurrent = i === guidedStep;
                      const isDone = i < guidedStep;
                      return (
                        <motion.div
                          key={step.id}
                          initial={{ opacity: 0, y: 5 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.05 }}
                        >
                          <Card
                            className={`cursor-pointer transition-all ${
                              isCurrent
                                ? "border-primary/40 bg-primary/5 shadow-sm"
                                : isDone
                                ? "border-emerald-500/20 bg-emerald-500/5 opacity-70"
                                : "border-border/50 opacity-50"
                            }`}
                            onClick={() => setGuidedStep(i)}
                          >
                            <CardContent className="p-3">
                              <div className="flex items-start gap-3">
                                <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs ${
                                  isDone ? "bg-emerald-500 text-white" : isCurrent ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                                }`}>
                                  {isDone ? <CheckCircle2 className="w-4 h-4" /> : step.id}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <h5 className="text-sm text-foreground mb-0.5">{step.title}</h5>
                                  <p className="text-[10px] text-muted-foreground mb-2">{step.description}</p>
                                  {isCurrent && (
                                    <motion.div
                                      initial={{ opacity: 0 }}
                                      animate={{ opacity: 1 }}
                                    >
                                      <div className="p-2.5 rounded-lg bg-secondary/50 border border-border/50 mb-2">
                                        <p className="text-xs text-foreground/90 leading-relaxed">{step.script}</p>
                                      </div>
                                      {step.actions && (
                                        <div className="flex gap-1.5 flex-wrap">
                                          {step.actions.map((a) => (
                                            <Badge key={a} variant="outline" className="text-[9px] h-5 cursor-pointer hover:bg-primary/10 hover:text-primary">
                                              {a}
                                            </Badge>
                                          ))}
                                        </div>
                                      )}
                                    </motion.div>
                                  )}
                                </div>
                              </div>
                            </CardContent>
                          </Card>
                        </motion.div>
                      );
                    })}
                    <div className="flex gap-2 pt-2">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={guidedStep === 0}
                        onClick={() => setGuidedStep((p) => Math.max(0, p - 1))}
                        className="text-xs"
                      >
                        السابق
                      </Button>
                      <Button
                        size="sm"
                        disabled={guidedStep >= guidedWorkflow.length - 1}
                        onClick={() => setGuidedStep((p) => Math.min(guidedWorkflow.length - 1, p + 1))}
                        className="text-xs"
                      >
                        التالي
                      </Button>
                    </div>
                  </div>
                )}

                {/* ── LAST ORDER ── */}
                {rightTab === "orders" && (
                  <div className="space-y-4">
                    <h4 className="text-sm text-muted-foreground flex items-center gap-2">
                      <ShoppingCart className="w-4 h-4 text-primary" />
                      آخر طلب  {customer.lastOrder.id}
                    </h4>
                    <Card className="border-border/50">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <Badge className={`text-[10px] border-transparent ${
                              customer.lastOrder.status === "delivered" ? "bg-emerald-500/10 text-emerald-500" :
                              customer.lastOrder.status === "shipped" ? "bg-blue-500/10 text-blue-500" :
                              "bg-primary/10 text-primary"
                            }`}>
                              {customer.lastOrder.status === "delivered" ? "تم التسليم" : customer.lastOrder.status === "shipped" ? "قيد الشحن" : "قيد التجهيز"}
                            </Badge>
                            <span className="text-xs text-muted-foreground ms-2">
                              {new Date(customer.lastOrder.date).toLocaleDateString("ar-SA")}
                            </span>
                          </div>
                          <p className="text-lg text-primary">{fmt(customer.lastOrder.amount)} <span className="text-xs">ر.س</span></p>
                        </div>
                        {/* Items table */}
                        <div className="border border-border/50 rounded-lg overflow-hidden">
                          <table className="w-full text-xs">
                            <thead className="bg-muted/30">
                              <tr>
                                <th className="text-start p-2 text-muted-foreground">المنتج</th>
                                <th className="text-center p-2 text-muted-foreground">الكمية</th>
                                <th className="text-center p-2 text-muted-foreground">السعر</th>
                                <th className="text-center p-2 text-muted-foreground">الخصم</th>
                                <th className="text-end p-2 text-muted-foreground">الإجمالي</th>
                              </tr>
                            </thead>
                            <tbody>
                              {customer.lastOrder.items.map((item, idx) => (
                                <tr key={idx} className="border-t border-border/30">
                                  <td className="p-2 text-foreground">{item.name}</td>
                                  <td className="p-2 text-center">{item.qty}</td>
                                  <td className="p-2 text-center">{fmt(item.price)}</td>
                                  <td className="p-2 text-center">{item.discount > 0 ? `${item.discount}%` : ""}</td>
                                  <td className="p-2 text-end text-foreground">{fmt(item.qty * item.price * (1 - item.discount / 100))}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        <div className="flex gap-2 mt-3">
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-xs gap-1.5"
                            onClick={() => setShowInvoice(customer.invoices[0])}
                          >
                            <Eye className="w-3 h-3" />
                            عرض الفاتورة
                          </Button>
                          <Button
                            size="sm"
                            className="text-xs gap-1.5"
                            onClick={() => setShowReorder(true)}
                          >
                            <RotateCcw className="w-3 h-3" />
                            إعادة طلب
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )}

                {/* ── FREQUENTLY ORDERED ── */}
                {rightTab === "frequent" && (
                  <div className="space-y-3">
                    <h4 className="text-sm text-muted-foreground flex items-center gap-2">
                      <RotateCcw className="w-4 h-4 text-primary" />
                      ال��نتجات الأكثر طلباً
                    </h4>
                    <div className="grid grid-cols-2 gap-3">
                      {([
                        { key: "عطور", label: "عطور", icon: Droplets, color: "text-pink-500", bg: "bg-pink-500/10" },
                        { key: "زجاجيات", label: "زجاجيات", icon: GlassWater, color: "text-sky-500", bg: "bg-sky-500/10" },
                        { key: "كحول", label: "كحول", icon: FlaskConical, color: "text-emerald-500", bg: "bg-emerald-500/10" },
                      ] as const).map((cat) => {
                        const Icon = cat.icon;
                        const items = customer.frequentItems.filter((fi) => fi.category === cat.key);
                        if (items.length === 0) return null;
                        return (
                          <Card key={cat.key} className="border-border/50">
                            <CardContent className="p-0">
                              <div className={`flex items-center gap-2 px-3 py-2 border-b border-border/40 ${cat.bg} rounded-t-lg`}>
                                <Icon className={`w-3.5 h-3.5 ${cat.color}`} />
                                <span className="text-xs text-foreground">{cat.label}</span>
                                <span className="text-[9px] px-1.5 rounded-full bg-background/60 text-muted-foreground">{items.length}</span>
                              </div>
                              <div className="p-1.5 space-y-1">
                                {items.map((item, i) => (
                                  <motion.div
                                    key={item.id}
                                    initial={{ opacity: 0, y: 4 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: i * 0.04 }}
                                    className="flex items-center gap-2 p-2 rounded-md hover:bg-muted/40 transition-colors cursor-pointer group"
                                  >
                                    <div className="flex-1 min-w-0">
                                      <p className="text-xs text-foreground group-hover:text-primary transition-colors truncate">{item.name}</p>
                                      <div className="flex items-center gap-2 text-[9px] text-muted-foreground mt-0.5">
                                        <span>{item.timesOrdered}×</span>
                                        <span>متوسط {item.avgQty}</span>
                                      </div>
                                    </div>
                                    <div className="flex items-center gap-2 shrink-0">
                                      <div className="text-center">
                                        <p className={`text-[10px] ${item.stock <= 5 ? "text-red-500" : item.stock <= 10 ? "text-primary" : "text-emerald-500"}`}>{item.stock}</p>
                                        <p className="text-[8px] text-muted-foreground">مخزون</p>
                                      </div>
                                      <div className="w-px h-5 bg-border/40" />
                                      <div className="text-end">
                                        <p className="text-[10px] text-foreground">{fmt(item.lastPrice)}</p>
                                        <p className="text-[8px] text-muted-foreground">ر.س</p>
                                      </div>
                                    </div>
                                  </motion.div>
                                ))}
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* ── AI ANALYSIS ── */}
                {rightTab === "ai" && (
                  <div className="space-y-4">
                    <h4 className="text-sm text-muted-foreground flex items-center gap-2">
                      <Bot className="w-4 h-4 text-primary" />
                      التحليل الذكي (AI)
                      {callActive && <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />}
                    </h4>

                    {callActive ? (
                      <Card className="border-primary/20 bg-primary/5">
                        <CardContent className="p-4 text-center">
                          <Bot className="w-10 h-10 text-primary mx-auto mb-2 animate-pulse" />
                          <p className="text-sm text-foreground">التحليل الذكي يعمل...</p>
                          <p className="text-xs text-muted-foreground mt-1">سيظهر الملخص بعد انتهاء المكالمة</p>
                        </CardContent>
                      </Card>
                    ) : (
                      <>
                        {/* AI Summary */}
                        <Card className="border-primary/20">
                          <CardHeader className="p-3 pb-2">
                            <CardTitle className="text-xs flex items-center gap-1.5">
                              <Bot className="w-3.5 h-3.5 text-primary" />
                              ملخص AI — {aiSummary.agentName}
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="p-3 pt-0 space-y-3">
                            <div className="flex items-center gap-4 text-xs">
                              <span className="flex items-center gap-1 text-muted-foreground"><Clock className="w-3 h-3" />المدة: <strong className="text-foreground">{fmtDur(elapsed)}</strong></span>
                              <Badge className={`text-[10px] border-transparent ${
                                aiSummary.situationStatus === "resolved" ? "bg-emerald-500/10 text-emerald-500" :
                                aiSummary.situationStatus === "escalated" ? "bg-red-500/10 text-red-500" :
                                "bg-primary/10 text-primary"
                              }`}>
                                {aiSummary.situationStatus === "resolved" ? "تم الحل" : aiSummary.situationStatus === "escalated" ? "تم التصعيد" : "معلّق"}
                              </Badge>
                            </div>

                            {/* QA Score */}
                            <div>
                              <div className="flex justify-between text-xs mb-1">
                                <span className="text-muted-foreground flex items-center gap-1"><Shield className="w-3 h-3" />جودة المكالمة</span>
                                <span className={`${aiSummary.qaScore >= 90 ? "text-emerald-500" : aiSummary.qaScore >= 70 ? "text-primary" : "text-red-500"}`}>{aiSummary.qaScore}%</span>
                              </div>
                              <Progress value={aiSummary.qaScore} className="h-1.5" />
                            </div>

                            {/* Key Points */}
                            <div>
                              <p className="text-[10px] text-muted-foreground mb-1.5">النقاط الرئيسية</p>
                              <ul className="space-y-1">
                                {aiSummary.keyPoints.map((pt, i) => (
                                  <li key={i} className="flex items-start gap-2 text-xs text-foreground">
                                    <span className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
                                    {pt}
                                  </li>
                                ))}
                              </ul>
                            </div>

                            {/* Issues */}
                            {aiSummary.issuesFound.length > 0 && (
                              <div>
                                <p className="text-[10px] text-red-500 mb-1.5 flex items-center gap-1"><AlertTriangle className="w-3 h-3" />مشكلات مكتشفة</p>
                                {aiSummary.issuesFound.map((issue, i) => (
                                  <p key={i} className="text-xs text-foreground bg-red-500/5 p-2 rounded-lg border border-red-500/10">{issue}</p>
                                ))}
                              </div>
                            )}

                            {/* Invoice/Quotation */}
                            {aiSummary.invoiceMade && (
                              <div className="flex items-center gap-2 text-xs p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
                                <Receipt className="w-3.5 h-3.5 text-emerald-500" />
                                <span className="text-muted-foreground">فاتورة:</span>
                                <span className="text-foreground">{aiSummary.invoiceMade.id}</span>
                                <Badge className="text-[8px] bg-primary/10 text-primary border-transparent">{aiSummary.invoiceMade.status}</Badge>
                              </div>
                            )}

                            {/* Discount Suggestions */}
                            {aiSummary.discountSuggestions.length > 0 && (
                              <div>
                                <p className="text-[10px] text-muted-foreground mb-1.5 flex items-center gap-1"><DollarSign className="w-3 h-3" />اقتراحات خصم</p>
                                {aiSummary.discountSuggestions.map((d, i) => (
                                  <p key={i} className="text-xs text-foreground bg-primary/5 p-2 rounded-lg border border-primary/10 mb-1">{d}</p>
                                ))}
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      </>
                    )}
                  </div>
                )}

                {/* ── NOTES (always visible) ── */}
                <div className="space-y-2 pt-2 border-t border-border/50">
                  <h4 className="text-xs text-muted-foreground flex items-center gap-2">
                    <Clipboard className="w-3.5 h-3.5" />
                    ملاحظات المكالمة
                  </h4>
                  <Textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="اكتب ملاحظاتك هنا..."
                    className="min-h-[80px] bg-secondary/30 border-border/50 text-sm resize-none"
                  />
                </div>

                {/* ── OUTCOME ── */}
                <div className="space-y-2">
                  <h4 className="text-xs text-muted-foreground flex items-center gap-2">
                    <ClipboardCheck className="w-3.5 h-3.5" />
                    نتيجة المكالمة
                  </h4>
                  <div className="flex gap-2 flex-wrap">
                    {outcomeOpts.map((opt) => {
                      const Icon = opt.icon;
                      const isSelected = outcome === opt.key;
                      return (
                        <Button
                          key={opt.key}
                          variant={isSelected ? "default" : "outline"}
                          size="sm"
                          className={`text-xs gap-1.5 ${isSelected ? "" : opt.color}`}
                          onClick={() => setOutcome(opt.key)}
                        >
                          <Icon className="w-3.5 h-3.5" />
                          {opt.label}
                        </Button>
                      );
                    })}
                  </div>
                </div>
                </div>
              </ScrollArea>

              {/* ═══ BOTTOM: Wrap-Up Bar (mandatory after call ends) ═══ */}
              {!callActive && (
                <motion.div
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  className="shrink-0 border-t border-primary/30 bg-primary/5 px-4 py-3"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xs text-primary flex items-center gap-1.5">
                      <ClipboardCheck className="w-3.5 h-3.5" />
                      شريط إنهاء التفاعل (إلزامي)
                    </span>
                    <span className="text-[10px] text-muted-foreground">
                      {wrapUpDone.size}/{4} مكتمل
                    </span>
                    <Progress value={(wrapUpDone.size / 4) * 100} className="w-20 h-1.5" />
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    {[
                      { key: "task", label: "إنشاء مهمة", icon: ClipboardCheck },
                      { key: "ticket", label: "فتح تذكرة", icon: Ticket },
                      { key: "followup", label: "جدولة متابعة", icon: CalendarClock },
                      { key: "catalogue", label: "إرسال كتالوج", icon: Send },
                    ].map((action) => {
                      const Icon = action.icon;
                      const done = wrapUpDone.has(action.key);
                      return (
                        <Button
                          key={action.key}
                          variant={done ? "default" : "outline"}
                          size="sm"
                          className={`text-xs gap-1.5 ${done ? "bg-emerald-600 hover:bg-emerald-700 text-white" : ""}`}
                          onClick={() => handleWrapUp(action.key)}
                        >
                          {done ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Icon className="w-3.5 h-3.5" />}
                          {action.label}
                          {done && " ✓"}
                        </Button>
                      );
                    })}

                    <div className="flex-1" />

                    <Button
                      onClick={handleSave}
                      disabled={saved}
                      className={`gap-2 text-xs ${saved ? "bg-emerald-600 text-white" : ""}`}
                    >
                      {saved ? <CheckCircle2 className="w-4 h-4" /> : <Save className="w-4 h-4" />}
                      {saved ? "تم الحفظ" : "حفظ في السجل"}
                    </Button>
                  </div>
                </motion.div>
              )}
            </div>
          </div>

        {/* ═══ INVOICE DETAIL DIALOG ═══ */}
        <AnimatePresence>
          {showInvoice && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 z-50 bg-black/60 flex items-center justify-center p-8"
              onClick={() => setShowInvoice(null)}
            >
              <motion.div
                initial={{ scale: 0.95, y: 10 }}
                animate={{ scale: 1, y: 0 }}
                exit={{ scale: 0.95, y: 10 }}
                className="bg-card border border-border rounded-xl p-6 max-w-lg w-full max-h-[80vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-base text-foreground flex items-center gap-2">
                    <FileText className="w-4 h-4 text-primary" />
                    فاتورة {showInvoice.id}
                  </h3>
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setShowInvoice(null)}>
                    <X className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex justify-between text-xs text-muted-foreground mb-4">
                  <span>التاريخ: {new Date(showInvoice.date).toLocaleDateString("ar-SA")}</span>
                  <span>الاستحقاق: {new Date(showInvoice.dueDate).toLocaleDateString("ar-SA")}</span>
                </div>
                <div className="border border-border/50 rounded-lg overflow-hidden mb-4">
                  <table className="w-full text-xs">
                    <thead className="bg-muted/30">
                      <tr>
                        <th className="text-start p-2 text-muted-foreground">المنتج</th>
                        <th className="text-center p-2 text-muted-foreground">الكمية</th>
                        <th className="text-center p-2 text-muted-foreground">السعر</th>
                        <th className="text-end p-2 text-muted-foreground">الإجمالي</th>
                      </tr>
                    </thead>
                    <tbody>
                      {showInvoice.items.map((item, idx) => (
                        <tr key={idx} className="border-t border-border/30">
                          <td className="p-2 text-foreground">{item.name}</td>
                          <td className="p-2 text-center">{item.qty}</td>
                          <td className="p-2 text-center">{fmt(item.price)}</td>
                          <td className="p-2 text-end">{fmt(item.qty * item.price)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex justify-between text-sm border-t border-border/50 pt-3">
                  <div>
                    <span className="text-muted-foreground">المدفوع: </span>
                    <span className="text-emerald-500">{fmt(showInvoice.paid)} ر.س</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">المتبقي: </span>
                    <span className="text-red-500">{fmt(showInvoice.amount - showInvoice.paid)} ر.س</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">الإجمالي: </span>
                    <span className="text-foreground">{fmt(showInvoice.amount)} ر.س</span>
                  </div>
                </div>
                <div className="flex gap-2 mt-4">
                  <Button size="sm" className="text-xs gap-1.5"><Banknote className="w-3 h-3" />تسجيل دفعة</Button>
                  <Button size="sm" variant="outline" className="text-xs gap-1.5"><Send className="w-3 h-3" />إرسال للعميل</Button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ═══ REORDER / NEW INVOICE DIALOG ═══ */}
        <AnimatePresence>
          {showReorder && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 z-50 bg-black/60 flex items-center justify-center p-8"
              onClick={() => setShowReorder(false)}
            >
              <motion.div
                initial={{ scale: 0.95, y: 10 }}
                animate={{ scale: 1, y: 0 }}
                exit={{ scale: 0.95, y: 10 }}
                className="bg-card border border-border rounded-xl p-6 max-w-lg w-full max-h-[80vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-base text-foreground flex items-center gap-2">
                    <Receipt className="w-4 h-4 text-primary" />
                    فاتورة جديدة — {customer.name}
                  </h3>
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setShowReorder(false)}>
                    <X className="w-4 h-4" />
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mb-4">
                  تم نسخ عناصر الطلب السابق. عدّل حسب الحاجة ثم أصدر الفاتورة أو أرسلها لقسم الفوتر.
                </p>
                <div className="border border-border/50 rounded-lg overflow-hidden mb-4">
                  <table className="w-full text-xs">
                    <thead className="bg-muted/30">
                      <tr>
                        <th className="text-start p-2 text-muted-foreground">المنتج</th>
                        <th className="text-center p-2 text-muted-foreground">الكمية</th>
                        <th className="text-center p-2 text-muted-foreground">السعر</th>
                        <th className="text-end p-2 text-muted-foreground">الإجمالي</th>
                      </tr>
                    </thead>
                    <tbody>
                      {customer.lastOrder.items.map((item, idx) => (
                        <tr key={idx} className="border-t border-border/30">
                          <td className="p-2 text-foreground">{item.name}</td>
                          <td className="p-2 text-center">{item.qty}</td>
                          <td className="p-2 text-center">{fmt(item.price)}</td>
                          <td className="p-2 text-end">{fmt(item.qty * item.price)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="text-end text-sm mb-4">
                  <span className="text-muted-foreground">الإجمالي: </span>
                  <span className="text-primary text-lg">{fmt(customer.lastOrder.amount)} ر.س</span>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" className="text-xs gap-1.5">
                    <Receipt className="w-3 h-3" />
                    إصدار فاتورة
                  </Button>
                  <Button size="sm" variant="outline" className="text-xs gap-1.5">
                    <Send className="w-3 h-3" />
                    إرسال لقسم الفوترة
                  </Button>
                  <Button size="sm" variant="outline" className="text-xs gap-1.5" onClick={() => setShowReorder(false)}>
                    إلغاء
                  </Button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </DialogContent>
    </Dialog>

    {/* ── Invoice Creation Dialog ── */}
    <InvoiceCreationDialog
      open={showInvoiceCreate}
      onClose={() => setShowInvoiceCreate(false)}
      customerName={customer.name}
      customerId={customer.id}
      customerAddress={customer.address}
      customerPhone={customer.phone}
    />
    </>
  );
}