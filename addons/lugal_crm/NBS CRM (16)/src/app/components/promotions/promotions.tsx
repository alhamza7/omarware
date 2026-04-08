import { useState, useMemo } from "react";
import { motion } from "motion/react";
import {
  Megaphone, Search, Plus, Send, Users, MapPin, Crown, Tag,
  Calendar, FileText, Link, Check, Clock, Eye, BarChart3,
  Filter, ChevronDown, Sparkles, Image, Mail, MessageCircle,
} from "lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from "../ui/tooltip";

// ── Data ────────────────────────────────────────────────

type CampaignStatus = "draft" | "pending_approval" | "approved" | "sent" | "scheduled";
type TargetGroup = "all" | "vip" | "city" | "segment" | "custom";

interface Campaign {
  id: string;
  name: string;
  description: string;
  status: CampaignStatus;
  targetGroup: TargetGroup;
  targetDetails: string;
  targetCount: number;
  channel: string;
  template: string;
  hasAttachment: boolean;
  attachmentType?: "pdf" | "image" | "link";
  createdBy: string;
  createdAt: string;
  scheduledAt?: string;
  sentAt?: string;
  approvedBy?: string;
  stats?: { sent: number; delivered: number; opened: number; clicked: number };
}

interface CustomerGroup {
  id: string;
  name: string;
  criteria: string;
  count: number;
  icon: typeof Users;
}

const customerGroups: CustomerGroup[] = [
  { id: "grp-all", name: "جميع العملاء", criteria: "الكل", count: 1247, icon: Users },
  { id: "grp-vip", name: "عملاء VIP", criteria: "VIP = نعم", count: 89, icon: Crown },
  { id: "grp-riyadh", name: "الرياض", criteria: "المدينة = الرياض", count: 456, icon: MapPin },
  { id: "grp-jeddah", name: "جدة", criteria: "المدينة = جدة", count: 312, icon: MapPin },
  { id: "grp-dammam", name: "الدمام والخبر", criteria: "المدينة = الدمام أو الخبر", count: 198, icon: MapPin },
  { id: "grp-dormant", name: "عملاء خاملون", criteria: "آخر طلب > 90 يوم", count: 167, icon: Clock },
  { id: "grp-new", name: "عملاء جدد", criteria: "تاريخ التسجيل < 30 يوم", count: 45, icon: Sparkles },
  { id: "grp-highvalue", name: "عملاء بقيمة عالية", criteria: "إجمالي المشتريات > 10,000 ر.س", count: 134, icon: BarChart3 },
];

const mockCampaigns: Campaign[] = [
  {
    id: "cmp-01", name: "عرض الربيع الخاص", description: "خصم 20% على جميع العطور الجديدة لعملاء VIP",
    status: "sent", targetGroup: "vip", targetDetails: "عملاء VIP", targetCount: 89,
    channel: "whatsapp", template: "🌸 عرض خاص لعملائنا المميزين!\nخصم 20% على الإصدارات الجديدة\nالعرض ساري حتى نهاية الشهر",
    hasAttachment: true, attachmentType: "pdf",
    createdBy: "فهد الراشد", createdAt: "2026-02-20T10:00:00", sentAt: "2026-02-20T12:00:00",
    approvedBy: "أحمد العلي",
    stats: { sent: 89, delivered: 87, opened: 72, clicked: 45 },
  },
  {
    id: "cmp-02", name: "وصول مجموعة الصيف", description: "إعلان وصول مجموعة عطور الصيف الجديدة",
    status: "approved", targetGroup: "all", targetDetails: "جميع العملاء", targetCount: 1247,
    channel: "whatsapp", template: "☀️ وصلت مجموعة الصيف الجديدة!\nاكتشف أحدث العطور المنعشة\nزورونا في أقرب فرع",
    hasAttachment: true, attachmentType: "image",
    createdBy: "منى الشهري", createdAt: "2026-02-22T09:00:00",
    approvedBy: "فهد الراشد",
  },
  {
    id: "cmp-03", name: "حملة إعادة التنشيط", description: "عرض خاص لإعادة تنشيط العملاء الخاملين",
    status: "pending_approval", targetGroup: "custom", targetDetails: "عملاء خاملون (>90 يوم)", targetCount: 167,
    channel: "sms", template: "نفتقدك في نور النبراس! 🌟\nخصم 15% على طلبك القادم\nاستخدم الكود: WELCOME15",
    hasAttachment: false,
    createdBy: "عبدالله الحربي", createdAt: "2026-02-23T08:00:00",
  },
  {
    id: "cmp-04", name: "تخفيضات نهاية الموسم", description: "تخفيضات تصل إلى 30% على منتجات مختارة",
    status: "draft", targetGroup: "city", targetDetails: "الرياض + جدة", targetCount: 768,
    channel: "email", template: "🏷️ تخفيضات نهاية الموسم\nوصلت إلى 30%!\nلا تفوّت الفرصة",
    hasAttachment: true, attachmentType: "link",
    createdBy: "سعود المالكي", createdAt: "2026-02-23T10:00:00",
  },
  {
    id: "cmp-05", name: "دعوة لمعرض العطور", description: "دعوة حصرية لمعرض العطور السنوي",
    status: "scheduled", targetGroup: "vip", targetDetails: "عملاء VIP", targetCount: 89,
    channel: "whatsapp", template: "✨ دعوة خاصة!\nأنت مدعو لمعرض نور النبراس السنوي\nالتاريخ: 15 مارس 2026\nالمكان: فندق الريتز كارلتون — الرياض",
    hasAttachment: true, attachmentType: "pdf",
    createdBy: "فهد الراشد", createdAt: "2026-02-21T11:00:00", scheduledAt: "2026-03-01T10:00:00",
    approvedBy: "أحمد العلي",
  },
];

const statusLabels: Record<CampaignStatus, string> = {
  draft: "مسودة",
  pending_approval: "في انتظار الموافقة",
  approved: "معتمد",
  sent: "تم الإرسال",
  scheduled: "مجدول",
};

const statusColors: Record<CampaignStatus, string> = {
  draft: "bg-muted/30 text-muted-foreground",
  pending_approval: "bg-primary/15 text-primary",
  approved: "bg-emerald-500/15 text-emerald-500",
  sent: "bg-blue-500/15 text-blue-400",
  scheduled: "bg-violet-500/15 text-violet-400",
};

// ── Main ────────────────────────────────────────────────

export function Promotions() {
  const [activeTab, setActiveTab] = useState<"campaigns" | "groups" | "calling">("campaigns");
  const [statusFilter, setStatusFilter] = useState<CampaignStatus | "all">("all");
  const [selectedGroups, setSelectedGroups] = useState<Set<string>>(new Set());

  const filteredCampaigns = useMemo(() => {
    if (statusFilter === "all") return mockCampaigns;
    return mockCampaigns.filter((c) => c.status === statusFilter);
  }, [statusFilter]);

  const toggleGroup = (id: string) => {
    setSelectedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectedCount = useMemo(() => {
    return customerGroups
      .filter((g) => selectedGroups.has(g.id))
      .reduce((sum, g) => sum + g.count, 0);
  }, [selectedGroups]);

  return (
    <TooltipProvider delayDuration={200}>
      <div className="space-y-4">

        {/* ── Header Stats ── */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {[
            { label: "إجمالي الحملات", value: mockCampaigns.length, color: "text-foreground" },
            { label: "تم الإرسال", value: mockCampaigns.filter((c) => c.status === "sent").length, color: "text-blue-400" },
            { label: "في الانتظار", value: mockCampaigns.filter((c) => c.status === "pending_approval").length, color: "text-primary" },
            { label: "مجدولة", value: mockCampaigns.filter((c) => c.status === "scheduled").length, color: "text-violet-400" },
            { label: "مسودات", value: mockCampaigns.filter((c) => c.status === "draft").length, color: "text-muted-foreground" },
          ].map((s) => (
            <div key={s.label} className="p-3 rounded-xl border border-border/30 bg-card/30 text-center">
              <p className={`text-2xl ${s.color}`}>{s.value}</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
          <div className="flex items-center justify-between">
            <TabsList className="bg-muted/20">
              <TabsTrigger value="campaigns" className="text-xs gap-1.5">
                <Megaphone className="w-3.5 h-3.5" />
                الحملات
              </TabsTrigger>
              <TabsTrigger value="groups" className="text-xs gap-1.5">
                <Users className="w-3.5 h-3.5" />
                المجموعات
              </TabsTrigger>
            </TabsList>

            <Button size="sm" className="h-8 text-xs gap-1.5">
              <Plus className="w-3.5 h-3.5" />
              حملة جديدة
            </Button>
          </div>

          {/* ── Campaigns ── */}
          <TabsContent value="campaigns" className="mt-4 space-y-3">
            {/* Status filters */}
            <div className="flex gap-1.5 mb-3">
              {(["all", "draft", "pending_approval", "approved", "scheduled", "sent"] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`px-2.5 py-1 rounded-lg text-[10px] border transition-all ${
                    statusFilter === st
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border/30 text-muted-foreground hover:border-primary/30"
                  }`}
                >
                  {st === "all" ? "الكل" : statusLabels[st]}
                </button>
              ))}
            </div>

            {filteredCampaigns.map((campaign) => (
              <CampaignCard key={campaign.id} campaign={campaign} />
            ))}

            {filteredCampaigns.length === 0 && (
              <div className="text-center py-12">
                <Megaphone className="w-8 h-8 mx-auto mb-2 text-muted-foreground/30" />
                <p className="text-xs text-muted-foreground">لا توجد حملات</p>
              </div>
            )}
          </TabsContent>

          {/* ── Customer Groups ── */}
          <TabsContent value="groups" className="mt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
              {customerGroups.map((group) => {
                const isSelected = selectedGroups.has(group.id);
                const Icon = group.icon;
                return (
                  <motion.button
                    key={group.id}
                    onClick={() => toggleGroup(group.id)}
                    className={`text-start p-4 rounded-xl border transition-all ${
                      isSelected
                        ? "border-primary bg-primary/5 dark:bg-primary/10 shadow-sm shadow-primary/10"
                        : "border-border/30 bg-card/30 hover:border-primary/30"
                    }`}
                    whileTap={{ scale: 0.98 }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                          isSelected ? "bg-primary/15 text-primary" : "bg-muted/30 text-muted-foreground"
                        }`}>
                          <Icon className="w-4 h-4" />
                        </div>
                        <div>
                          <p className="text-xs text-foreground">{group.name}</p>
                          <p className="text-[9px] text-muted-foreground">{group.criteria}</p>
                        </div>
                      </div>
                      {isSelected && <Check className="w-4 h-4 text-primary shrink-0" />}
                    </div>
                    <div className="mt-3 flex items-center justify-between">
                      <span className="text-lg text-foreground">{group.count.toLocaleString()}</span>
                      <span className="text-[9px] text-muted-foreground">عميل</span>
                    </div>
                  </motion.button>
                );
              })}
            </div>

            {selectedGroups.size > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 p-4 rounded-xl border border-primary/20 bg-primary/5 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <Users className="w-5 h-5 text-primary" />
                  <div>
                    <p className="text-sm text-foreground">
                      {selectedGroups.size} مجموعة محددة — {selectedCount.toLocaleString()} عميل
                    </p>
                    <p className="text-[10px] text-muted-foreground">
                      يمكنك إرسال حملة ترويجية لهذه المجموعات
                    </p>
                  </div>
                </div>
                <Button size="sm" className="gap-1.5 text-xs">
                  <Send className="w-3.5 h-3.5" />
                  إنشاء حملة
                </Button>
              </motion.div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </TooltipProvider>
  );
}

// ── Campaign Card ───────────────────────────────────────

function CampaignCard({ campaign }: { campaign: Campaign }) {
  return (
    <div className="p-4 rounded-xl border border-border/30 bg-card/30 space-y-3">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="text-sm text-foreground">{campaign.name}</h4>
            <Badge className={`${statusColors[campaign.status]} text-[8px] h-4`}>
              {statusLabels[campaign.status]}
            </Badge>
            {campaign.hasAttachment && (
              <Tooltip>
                <TooltipTrigger>
                  {campaign.attachmentType === "pdf" && <FileText className="w-3.5 h-3.5 text-red-400" />}
                  {campaign.attachmentType === "image" && <Image className="w-3.5 h-3.5 text-blue-400" />}
                  {campaign.attachmentType === "link" && <Link className="w-3.5 h-3.5 text-violet-400" />}
                </TooltipTrigger>
                <TooltipContent className="text-xs">مرفق: {campaign.attachmentType}</TooltipContent>
              </Tooltip>
            )}
          </div>
          <p className="text-[10px] text-muted-foreground mt-0.5">{campaign.description}</p>
        </div>

        {campaign.status === "pending_approval" && (
          <div className="flex gap-1 shrink-0">
            <Button size="sm" className="h-7 text-[10px] gap-1">
              <Check className="w-3 h-3" /> اعتماد
            </Button>
          </div>
        )}
        {campaign.status === "approved" && (
          <Button size="sm" className="h-7 text-[10px] gap-1 shrink-0">
            <Send className="w-3 h-3" /> إرسال الآن
          </Button>
        )}
      </div>

      {/* Target & Channel */}
      <div className="flex items-center gap-4 text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <Users className="w-3 h-3" /> {campaign.targetDetails} ({campaign.targetCount})
        </span>
        <span className="flex items-center gap-1">
          <MessageCircle className="w-3 h-3" /> {campaign.channel}
        </span>
        <span className="flex items-center gap-1">
          <Calendar className="w-3 h-3" /> {new Date(campaign.createdAt).toLocaleDateString("ar-SA")}
        </span>
        <span>أنشأها: {campaign.createdBy}</span>
        {campaign.approvedBy && <span>اعتمدها: {campaign.approvedBy}</span>}
      </div>

      {/* Stats (for sent campaigns) */}
      {campaign.stats && (
        <div className="grid grid-cols-4 gap-3 pt-2 border-t border-border/20">
          {[
            { label: "مُرسل", value: campaign.stats.sent, color: "text-blue-400" },
            { label: "وصل", value: campaign.stats.delivered, color: "text-emerald-400" },
            { label: "مقروء", value: campaign.stats.opened, color: "text-primary" },
            { label: "نقر", value: campaign.stats.clicked, color: "text-violet-400" },
          ].map((s) => (
            <div key={s.label} className="text-center">
              <p className={`text-sm ${s.color}`}>{s.value}</p>
              <p className="text-[8px] text-muted-foreground">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Template preview */}
      <div className="p-3 rounded-lg bg-muted/10 border border-border/20">
        <p className="text-[9px] text-muted-foreground mb-1">معاينة القالب</p>
        <p className="text-[10px] text-foreground/80 whitespace-pre-line line-clamp-3">
          {campaign.template}
        </p>
      </div>
    </div>
  );
}
