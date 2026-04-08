import { useState, useMemo, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Search, Phone, Paperclip, FileText, BookOpen,
  Clock, AlertTriangle, User, UserPlus, X, Check,
  Shield, Eye, Lock, ArrowLeftRight, Star, Bot,
  Mic, MoreHorizontal, Send, MessageCircle,
  PhoneMissed, PhoneCall, PhoneForwarded, CheckCircle2, RotateCcw,
} from "lucide-react";
import {
  AllChannelsIcon,
  WhatsAppIcon,
  TelegramIcon,
  TikTokIcon,
  InstagramIcon,
  SnapchatIcon,
  SmsIcon,
  XIcon,
} from "./channel-icons";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";
import { Avatar, AvatarFallback } from "../ui/avatar";
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from "../ui/tooltip";
import {
  type ChannelType,
  channelConfigs,
  mockConversations,
  mockMessages,
  mockAgents,
  mockEscalations,
  mockCallingList,
  ocTemplates,
  mockOCMissedCalls,
  type OCConversation,
  type OCMessage,
  type MissedCallAgentStatus,
  type TransferRequest,
} from "./oc-data";

// ── Channel icon resolver (brand SVGs) ──────────────────

type IconComponent = React.FC<{ className?: string; style?: React.CSSProperties }>;

const channelIcons: Record<ChannelType, IconComponent> = {
  whatsapp: WhatsAppIcon,
  whatsapp2: WhatsAppIcon,
  telegram: TelegramIcon,
  tiktok: TikTokIcon,
  instagram: InstagramIcon,
  snapchat: SnapchatIcon,
  sms: SmsIcon,
  x: XIcon,
};

function getChannelColor(ch: ChannelType): string {
  return channelConfigs.find((c) => c.id === ch)?.color ?? "#888";
}

// ── Time formatting ─────────────────────────────────────

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "الآن";
  if (mins < 60) return `${mins} د`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} س`;
  return `${Math.floor(hrs / 24)} ي`;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("ar-SA", { hour: "2-digit", minute: "2-digit" });
}

// ── Main Component ──────────────────────────────────────

export function OmniChannel() {
  const [activeChannel, setActiveChannel] = useState<ChannelType | "all">("all");
  const [activeConvId, setActiveConvId] = useState<string | null>("conv-001");
  const [searchQuery, setSearchQuery] = useState("");
  const [filterUnregistered, setFilterUnregistered] = useState(false);
  const [messageInput, setMessageInput] = useState("");
  const [sidePanel, setSidePanel] = useState<"none" | "escalation" | "calling" | "templates" | "missed" | "transfers">("none");
  const [showTransferMenu, setShowTransferMenu] = useState(false);
  const [transferReason, setTransferReason] = useState("");
  const [noteInput, setNoteInput] = useState("");
  const [addedNotes, setAddedNotes] = useState<OCMessage[]>([]);
  const [transferRequests, setTransferRequests] = useState<TransferRequest[]>([
    // Mock: an incoming pending transfer from emp-03 to current user (emp-01)
    {
      id: "tr-mock-01",
      conversationId: "conv-005",
      customerName: "user_tiktok_392",
      channel: "tiktok",
      fromAgentId: "emp-03",
      fromAgentName: "عبدالله الحربي",
      toAgentId: "emp-01",
      toAgentName: "سعود المالكي",
      reason: "العميل يسأل عن أسعار — أحتاج دعم المبيعات",
      status: "pending",
      createdAt: new Date().toISOString(),
    },
    // Mock: historical approved transfer
    {
      id: "tr-mock-02",
      conversationId: "conv-003",
      customerName: "فاطمة عبدالله السالم",
      channel: "whatsapp",
      fromAgentId: "emp-01",
      fromAgentName: "سعود المالكي",
      toAgentId: "emp-02",
      toAgentName: "منى الشهري",
      reason: "العميلة تريد متابعة شحن — منى أقرب للمستودع",
      status: "approved",
      createdAt: "2026-02-25T08:30:00",
      respondedAt: "2026-02-25T08:32:00",
    },
    // Mock: historical rejected transfer
    {
      id: "tr-mock-03",
      conversationId: "conv-004",
      customerName: "سارة علي الحربي",
      channel: "instagram",
      fromAgentId: "emp-02",
      fromAgentName: "منى الشهري",
      toAgentId: "emp-03",
      toAgentName: "عبدالله الحربي",
      reason: "العميلة تسأل عن حساب إنستقرام",
      rejectionReason: "عندي 3 محادثات نشطة حالياً ولا أستطيع استقبال المزيد",
      status: "rejected",
      createdAt: "2026-02-25T09:00:00",
      respondedAt: "2026-02-25T09:05:00",
    },
  ]);
  const [transferSentToast, setTransferSentToast] = useState<string | null>(null);
  const [rejectingTransferId, setRejectingTransferId] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const transferRef = useRef<HTMLDivElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Current logged-in agent (simulated)
  const currentAgentId = "emp-01";
  const currentAgentName = mockAgents.find((a) => a.id === currentAgentId)?.name ?? "";

  // Incoming pending transfers for current agent
  const incomingTransfers = transferRequests.filter(
    (tr) => tr.toAgentId === currentAgentId && tr.status === "pending"
  );

  // Outgoing pending transfers for current agent
  const outgoingTransfers = transferRequests.filter(
    (tr) => tr.fromAgentId === currentAgentId && tr.status === "pending"
  );

  // Check if there's a pending transfer for the active conversation
  const activeConvPendingTransfer = activeConvId
    ? transferRequests.find(
        (tr) => tr.conversationId === activeConvId && tr.status === "pending"
      )
    : null;

  const handleTransferRequest = (targetAgent: typeof mockAgents[0]) => {
    if (!activeConv) return;
    const newRequest: TransferRequest = {
      id: `tr-${Date.now()}`,
      conversationId: activeConv.id,
      customerName: activeConv.customerName,
      channel: activeConv.channel,
      fromAgentId: currentAgentId,
      fromAgentName: currentAgentName,
      toAgentId: targetAgent.id,
      toAgentName: targetAgent.name,
      reason: transferReason.trim(),
      status: "pending",
      createdAt: new Date().toISOString(),
    };
    setTransferRequests((prev) => [...prev, newRequest]);
    setShowTransferMenu(false);
    setTransferReason("");
    setTransferSentToast(targetAgent.name);
    setTimeout(() => setTransferSentToast(null), 3000);
  };

  const handleTransferResponse = (requestId: string, action: "approved" | "rejected", rejectReason?: string) => {
    setTransferRequests((prev) =>
      prev.map((tr) =>
        tr.id === requestId
          ? {
              ...tr,
              status: action,
              respondedAt: new Date().toISOString(),
              ...(action === "rejected" && rejectReason ? { rejectionReason: rejectReason } : {}),
            }
          : tr
      )
    );
    setRejectingTransferId(null);
    setRejectionReason("");
  };

  const startRejectTransfer = (requestId: string) => {
    setRejectingTransferId(requestId);
    setRejectionReason("");
  };

  const confirmRejectTransfer = () => {
    if (!rejectingTransferId || !rejectionReason.trim()) return;
    handleTransferResponse(rejectingTransferId, "rejected", rejectionReason.trim());
  };

  const handleCancelTransfer = (requestId: string) => {
    setTransferRequests((prev) =>
      prev.map((tr) =>
        tr.id === requestId
          ? { ...tr, status: "cancelled", respondedAt: new Date().toISOString() }
          : tr
      )
    );
  };

  const handleAddNote = () => {
    if (!noteInput.trim() || !activeConvId) return;
    const newNote: OCMessage = {
      id: `note-${Date.now()}`,
      conversationId: activeConvId,
      sender: "agent",
      senderName: currentAgentName,
      type: "internal_note",
      content: noteInput.trim(),
      timestamp: new Date().toISOString(),
      read: true,
      isInternalNote: true,
    };
    setAddedNotes((prev) => [...prev, newNote]);
    setNoteInput("");
  };

  // Filter conversations
  const filteredConvs = useMemo(() => {
    let convs = [...mockConversations];
    if (activeChannel !== "all") {
      convs = convs.filter((c) => c.channel === activeChannel);
    }
    if (filterUnregistered) {
      convs = convs.filter((c) => c.isUnregistered);
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      convs = convs.filter(
        (c) =>
          c.customerName.toLowerCase().includes(q) ||
          c.lastMessage.includes(searchQuery) ||
          (c.customerPhone && c.customerPhone.includes(searchQuery)),
      );
    }
    return convs.sort((a, b) => {
      const statusOrder = { open: 0, waiting: 1, responded: 2, closed: 3 };
      const diff = statusOrder[a.status] - statusOrder[b.status];
      if (diff !== 0) return diff;
      return new Date(b.lastMessageTime).getTime() - new Date(a.lastMessageTime).getTime();
    });
  }, [activeChannel, searchQuery, filterUnregistered]);

  const activeConv = activeConvId
    ? mockConversations.find((c) => c.id === activeConvId) ?? null
    : null;
  const activeMessages = activeConvId ? [...(mockMessages[activeConvId] ?? []), ...addedNotes.filter((n) => n.conversationId === activeConvId)] : [];

  // Channel stats
  const channelStats = useMemo(() => {
    const stats: Record<string, { total: number; unread: number }> = {
      all: { total: mockConversations.length, unread: mockConversations.filter((c) => c.unreadCount > 0).length },
    };
    for (const ch of channelConfigs) {
      const chConvs = mockConversations.filter((c) => c.channel === ch.id);
      stats[ch.id] = { total: chConvs.length, unread: chConvs.filter((c) => c.unreadCount > 0).length };
    }
    return stats;
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeMessages.length, activeConvId]);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (transferRef.current && !transferRef.current.contains(e.target as Node)) {
        setShowTransferMenu(false);
      }
    };
    if (showTransferMenu) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [showTransferMenu]);

  const totalEscalations = mockEscalations.length;

  return (
    <TooltipProvider delayDuration={200}>
      {/* ── Incoming Transfer Requests Banner ── */}
      <AnimatePresence>
        {incomingTransfers.map((tr) => {
          const ChIcon = channelIcons[tr.channel];
          const linkedConv = mockConversations.find((c) => c.id === tr.conversationId);
          const lastMsg = linkedConv?.lastMessage;
          return (
            <motion.div
              key={tr.id}
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20, height: 0 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
              className="mb-3 rounded-xl border border-primary/30 bg-primary/[0.06] shadow-[0_4px_20px_rgba(0,0,0,0.2),_inset_0_1px_0_rgba(255,255,255,0.04)] overflow-hidden"
              dir="rtl"
            >
              <div className="px-4 py-3 flex items-center gap-3">
                <div className="shrink-0 w-9 h-9 rounded-full bg-primary/15 flex items-center justify-center ring-2 ring-primary/20">
                  <ArrowLeftRight className="w-4 h-4 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-foreground">طلب نقل محادثة من <span className="text-primary">{tr.fromAgentName}</span></span>
                    <Badge className="bg-primary/10 text-primary text-[7px] h-4">بانتظار الموافقة</Badge>
                  </div>
                  <div className="flex items-center gap-2 mt-1 text-[9px] text-muted-foreground">
                    <ChIcon className="w-3 h-3" style={{ color: getChannelColor(tr.channel) }} />
                    <span>{channelConfigs.find((c) => c.id === tr.channel)?.label}</span>
                    <span className="opacity-40">|</span>
                    <span>{tr.customerName}</span>
                    <span className="opacity-40">|</span>
                    <Clock className="w-2.5 h-2.5" />
                    <span>{timeAgo(tr.createdAt)}</span>
                  </div>
                  {tr.reason && (
                    <p className="text-[10px] text-muted-foreground/80 mt-1 border-s-2 border-primary/20 ps-2">{tr.reason}</p>
                  )}
                  {lastMsg && (
                    <div className="flex items-start gap-1.5 mt-1.5 px-2.5 py-1.5 rounded-lg bg-muted/15 border border-border/20">
                      <MessageCircle className="w-3 h-3 text-muted-foreground/60 shrink-0 mt-0.5" />
                      <div className="min-w-0">
                        <span className="text-[8px] text-muted-foreground/50 block mb-0.5">آخر رسالة</span>
                        <p className="text-[10px] text-foreground/80 truncate">{lastMsg}</p>
                      </div>
                    </div>
                  )}
                </div>
                <div className="shrink-0 flex items-center gap-2">
                  <Button
                    size="sm"
                    className="h-8 text-[10px] gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white"
                    onClick={() => handleTransferResponse(tr.id, "approved")}
                  >
                    <Check className="w-3.5 h-3.5" />
                    قبول
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-8 text-[10px] gap-1.5 text-red-400 border-red-500/30 hover:bg-red-500/10"
                    onClick={() => startRejectTransfer(tr.id)}
                  >
                    <X className="w-3.5 h-3.5" />
                    رفض
                  </Button>
                </div>
              </div>

              {/* Rejection reason form (inline expand) */}
              <AnimatePresence>
                {rejectingTransferId === tr.id && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="px-4 pb-3 pt-1 border-t border-red-500/20 bg-red-500/[0.03]" dir="rtl">
                      <label className="text-[9px] text-red-400 mb-1.5 block">سبب الرفض (مطلوب) — سيظهر للمشرف وللمرسل</label>
                      <div className="flex items-end gap-2">
                        <Input
                          placeholder="اكتب سبب الرفض..."
                          className="flex-1 h-8 text-[10px] border-red-500/20 focus:border-red-500/40"
                          value={rejectionReason}
                          onChange={(e) => setRejectionReason(e.target.value)}
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === "Enter" && rejectionReason.trim()) {
                              confirmRejectTransfer();
                            }
                          }}
                        />
                        <Button
                          size="sm"
                          className="h-8 text-[10px] gap-1 bg-red-600 hover:bg-red-700 text-white"
                          disabled={!rejectionReason.trim()}
                          onClick={confirmRejectTransfer}
                        >
                          <X className="w-3 h-3" />
                          تأكيد الرفض
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-8 text-[10px] text-muted-foreground"
                          onClick={() => { setRejectingTransferId(null); setRejectionReason(""); }}
                        >
                          إلغاء
                        </Button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          );
        })}
      </AnimatePresence>

      {/* ── Transfer Sent Toast ── */}
      <AnimatePresence>
        {transferSentToast && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-6 start-1/2 -translate-x-1/2 z-[100] flex items-center gap-2 bg-card border border-primary/30 rounded-xl px-4 py-2.5 shadow-2xl shadow-black/30"
            dir="rtl"
          >
            <CheckCircle2 className="w-4 h-4 text-primary" />
            <span className="text-xs text-foreground">تم إرسال طلب النقل إلى <span className="text-primary">{transferSentToast}</span> — بانتظار الموافقة</span>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex h-[calc(100vh-220px)] gap-0 rounded-xl border border-border/40 overflow-hidden bg-card/20">

        {/* ═══ Left: Channel Tabs + Conversation List ═══ */}
        <div className="w-80 shrink-0 border-e border-border/30 flex flex-col bg-card/30">

          {/* Channel selector cards */}
          <div className="shrink-0 p-3 border-b border-border/20">
            <div className="flex items-center gap-2 mb-2.5">
              <MessageCircle className="w-4 h-4 text-primary" />
              <span className="text-xs text-foreground">القنوات</span>
              <div className="ms-auto flex items-center gap-1.5">
                <button
                  onClick={() => setSidePanel(sidePanel === "transfers" ? "none" : "transfers")}
                  className={`relative flex items-center gap-1 text-[9px] px-2 py-0.5 rounded-full transition-colors cursor-pointer ${
                    sidePanel === "transfers"
                      ? "text-primary bg-primary/15"
                      : "text-muted-foreground bg-muted/20 hover:text-primary hover:bg-primary/10"
                  }`}
                >
                  <ArrowLeftRight className="w-3 h-3" />
                  نقل
                  {transferRequests.filter((t) => t.status === "pending").length > 0 && (
                    <span className="w-3.5 h-3.5 rounded-full bg-primary text-white text-[7px] flex items-center justify-center">
                      {transferRequests.filter((t) => t.status === "pending").length}
                    </span>
                  )}
                </button>
                {totalEscalations > 0 && (
                  <button
                    onClick={() => setSidePanel(sidePanel === "escalation" ? "none" : "escalation")}
                    className="flex items-center gap-1 text-[9px] text-red-500 bg-red-500/10 px-2 py-0.5 rounded-full"
                  >
                    <AlertTriangle className="w-3 h-3" />
                    {totalEscalations} تصعيد
                  </button>
                )}
              </div>
            </div>

            <div className="grid grid-cols-5 gap-1.5">
              {/* All channels */}
              <button
                onClick={() => setActiveChannel("all")}
                className={`relative flex flex-col items-center gap-1 px-1 py-2 rounded-lg border text-[9px] transition-all cursor-pointer ${
                  activeChannel === "all"
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border/30 text-muted-foreground hover:border-primary/30"
                }`}
              >
                <AllChannelsIcon className="w-4 h-4" />
                <span className="truncate w-full text-center">الكل</span>
                {channelStats.all.unread > 0 && (
                  <span className="absolute -top-1 -end-1 w-4 h-4 rounded-full bg-red-500 text-white text-[7px] flex items-center justify-center ring-2 ring-card shadow-sm">
                    {channelStats.all.unread}
                  </span>
                )}
              </button>

              {channelConfigs.filter((c) => c.enabled).map((ch) => {
                const Icon = channelIcons[ch.id];
                const stat = channelStats[ch.id];
                return (
                  <button
                    key={ch.id}
                    onClick={() => setActiveChannel(ch.id)}
                    className={`relative flex flex-col items-center gap-1 px-1 py-2 rounded-lg border text-[9px] transition-all cursor-pointer ${
                      activeChannel === ch.id
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border/30 text-muted-foreground hover:border-primary/30"
                    }`}
                  >
                    <Icon className="w-4 h-4" style={{ color: ch.color }} />
                    <span className="truncate w-full text-center">{ch.label}</span>
                    {stat && stat.unread > 0 && (
                      <span className="absolute -top-1 -end-1 w-4 h-4 rounded-full bg-red-500 text-white text-[7px] flex items-center justify-center ring-2 ring-card shadow-sm">
                        {stat.unread}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Search + Filters */}
          <div className="shrink-0 p-3 border-b border-border/20">
            <div className="relative mb-2">
              <Search className="absolute start-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <Input
                placeholder="بحث بالاسم أو الرقم..."
                className="h-8 text-xs ps-8"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setFilterUnregistered(!filterUnregistered)}
                className={`flex items-center gap-1 text-[9px] px-2 py-1 rounded-md border transition-all cursor-pointer ${
                  filterUnregistered
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border/30 text-muted-foreground hover:border-primary/30"
                }`}
              >
                <UserPlus className="w-3 h-3" />
                غير مسجل
              </button>
              <button
                onClick={() => setSidePanel(sidePanel === "calling" ? "none" : "calling")}
                className="flex items-center gap-1 text-[9px] px-2 py-1 rounded-md border border-border/30 text-muted-foreground hover:border-primary/30 transition-all cursor-pointer"
              >
                <Phone className="w-3 h-3" />
                قائمة الاتصال
              </button>
              <button
                onClick={() => setSidePanel(sidePanel === "missed" ? "none" : "missed")}
                className="relative flex items-center gap-1 text-[9px] px-2 py-1 rounded-md border border-border/30 text-muted-foreground hover:border-red-500/30 transition-all cursor-pointer"
              >
                <PhoneMissed className="w-3 h-3 text-red-400" />
                فائتة
                {mockOCMissedCalls.filter((c) => c.status === "pending").length > 0 && (
                  <span className="w-3.5 h-3.5 rounded-full bg-red-500 text-white text-[7px] flex items-center justify-center">
                    {mockOCMissedCalls.filter((c) => c.status === "pending").length}
                  </span>
                )}
              </button>
              <button
                onClick={() => setSidePanel(sidePanel === "templates" ? "none" : "templates")}
                className="flex items-center gap-1 text-[9px] px-2 py-1 rounded-md border border-border/30 text-muted-foreground hover:border-primary/30 transition-all ms-auto cursor-pointer"
              >
                <FileText className="w-3 h-3" />
                قوالب
              </button>
            </div>
          </div>

          {/* Conversation list */}
          <ScrollArea dir="rtl" className="flex-1 min-h-0 bg-card/40">
            <div className="p-2.5 space-y-2">
              {filteredConvs.map((conv) => (
                <ConversationCard
                  key={conv.id}
                  conv={conv}
                  isActive={activeConvId === conv.id}
                  onClick={() => setActiveConvId(conv.id)}
                />
              ))}
              {filteredConvs.length === 0 && (
                <div className="text-center py-8 text-xs text-muted-foreground">
                  لا توجد محادثات
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Stats bar */}
          <div className="shrink-0 p-3 border-t border-border/20 bg-muted/10">
            <div className="flex items-center justify-between text-[9px] text-muted-foreground">
              <span>{filteredConvs.length} محادثة</span>
              <span>{filteredConvs.filter((c) => c.status === "open").length} مفتوحة</span>
              <span>{filteredConvs.filter((c) => c.isEscalated).length} مصعّدة</span>
            </div>
          </div>
        </div>

        {/* ═══ Center: Chat Area ═══ */}
        <div className="flex-1 flex flex-col min-w-0">
          {activeConv ? (
            <>
              {/* Chat header */}
              <div className="shrink-0 px-5 py-3 border-b border-border/30 bg-card/40">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Avatar className="h-9 w-9">
                      <AvatarFallback
                        className="text-[10px]"
                        style={{ backgroundColor: getChannelColor(activeConv.channel) + "20", color: getChannelColor(activeConv.channel) }}
                      >
                        {activeConv.customerName.slice(0, 2)}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-foreground">{activeConv.customerName}</span>
                        {activeConv.isVip && (
                          <Star className="w-3.5 h-3.5 text-primary fill-primary" />
                        )}
                        {activeConv.isUnregistered && (
                          <Badge className="bg-red-500/10 text-red-400 text-[7px] h-4 border-red-500/20">
                            غير مسجل
                          </Badge>
                        )}
                        {activeConv.aiHandled && (
                          <Badge className="bg-violet-500/10 text-violet-400 text-[7px] h-4 border-violet-500/20">
                            <Bot className="w-2.5 h-2.5 me-0.5" /> AI
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-[9px] text-muted-foreground">
                        {(() => {
                          const Icon = channelIcons[activeConv.channel];
                          return <Icon className="w-3 h-3" style={{ color: getChannelColor(activeConv.channel) }} />;
                        })()}
                        <span>{channelConfigs.find((c) => c.id === activeConv.channel)?.label}</span>
                        {activeConv.assignedAgentName && (
                          <>
                            <span>•</span>
                            <span>مُعيّن: {activeConv.assignedAgentName}</span>
                          </>
                        )}
                        {activeConv.activeWriter && (
                          <>
                            <span>•</span>
                            <span className="text-primary flex items-center gap-0.5">
                              <Lock className="w-2.5 h-2.5" />
                              {mockAgents.find((a) => a.id === activeConv.activeWriter)?.name} يكتب...
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5">
                    {activeConv.isUnregistered && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button variant="outline" size="sm" className="h-7 text-[10px] gap-1">
                            <UserPlus className="w-3 h-3" />
                            تسجيل كعميل محتمل
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent className="text-xs">تسجيل كـ Lead مع وسم القناة</TooltipContent>
                      </Tooltip>
                    )}
                    {activeConv.customerId && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-primary">
                            <User className="w-3.5 h-3.5" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent className="text-xs">عرض بطاقة العميل</TooltipContent>
                      </Tooltip>
                    )}
                    <div className="relative" ref={transferRef}>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className={`h-7 w-7 relative ${showTransferMenu ? "text-primary bg-primary/10" : "text-muted-foreground hover:text-primary"}`}
                            onClick={() => setShowTransferMenu(!showTransferMenu)}
                          >
                            <ArrowLeftRight className="w-3.5 h-3.5" />
                            {activeConvPendingTransfer && (
                              <span className="absolute -top-0.5 -end-0.5 w-2.5 h-2.5 rounded-full bg-primary animate-pulse" />
                            )}
                          </Button>
                        </TooltipTrigger>
                        {!showTransferMenu && (
                          <TooltipContent className="text-xs">نقل المحادثة</TooltipContent>
                        )}
                      </Tooltip>

                      {/* Transfer dropdown */}
                      <AnimatePresence>
                        {showTransferMenu && (
                          <motion.div
                            initial={{ opacity: 0, y: -8, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: -8, scale: 0.95 }}
                            transition={{ duration: 0.15, ease: "easeOut" }}
                            className="absolute top-full end-0 mt-2 w-72 bg-card border border-border/50 rounded-xl z-50 shadow-2xl shadow-black/20 overflow-hidden"
                            dir="rtl"
                          >
                            <div className="px-4 py-3 border-b border-border/30 bg-muted/10">
                              <div className="flex items-center gap-2">
                                <ArrowLeftRight className="w-4 h-4 text-primary" />
                                <span className="text-xs text-foreground">نقل المحادثة إلى</span>
                              </div>
                              {activeConvPendingTransfer && (
                                <div className="mt-2 flex items-center gap-2 text-[9px] text-primary bg-primary/5 border border-primary/20 rounded-lg px-2 py-1.5">
                                  <Clock className="w-3 h-3" />
                                  <span>طلب نقل معلّق إلى {activeConvPendingTransfer.toAgentName}</span>
                                  <button
                                    className="ms-auto text-red-400 hover:text-red-300 transition-colors cursor-pointer"
                                    onClick={(e) => { e.stopPropagation(); handleCancelTransfer(activeConvPendingTransfer.id); }}
                                  >
                                    <X className="w-3 h-3" />
                                  </button>
                                </div>
                              )}
                            </div>
                            <div className="px-3 py-2 border-b border-border/20">
                              <Input
                                placeholder="سبب النقل (مطلوب)..."
                                className={`h-7 text-[10px] ${!transferReason.trim() ? "border-red-500/30 focus:border-red-500/50" : ""}`}
                                value={transferReason}
                                onChange={(e) => setTransferReason(e.target.value)}
                                autoFocus
                              />
                              {!transferReason.trim() && (
                                <p className="text-[8px] text-red-400 mt-1">يجب كتابة سبب النقل قبل اختيار الموظف</p>
                              )}
                            </div>
                            <div className="p-2 space-y-1 max-h-64 overflow-y-auto">
                              {mockAgents
                                .filter((a) => a.id !== activeConv?.assignedAgent)
                                .map((agent) => {
                                  const isBusy = agent.activeConversations >= agent.maxCapacity;
                                  const noReason = !transferReason.trim();
                                  const isDisabled = isBusy || noReason;
                                  const presenceColor =
                                    agent.presence === "available" ? "bg-emerald-500" :
                                    agent.presence === "busy" ? "bg-red-500" :
                                    agent.presence === "away" ? "bg-yellow-500" : "bg-gray-400";
                                  return (
                                    <button
                                      key={agent.id}
                                      className={`w-full text-start flex items-center gap-3 p-2.5 rounded-lg border transition-all ${
                                        isDisabled
                                          ? "border-border/20 opacity-50 cursor-not-allowed"
                                          : "border-border/30 hover:border-primary/30 hover:bg-primary/5 cursor-pointer"
                                      }`}
                                      disabled={isDisabled}
                                      onClick={() => handleTransferRequest(agent)}
                                    >
                                      <div className="relative shrink-0">
                                        <Avatar className="h-8 w-8">
                                          <AvatarFallback className="text-[9px] bg-primary/10 text-primary">
                                            {agent.name.slice(0, 2)}
                                          </AvatarFallback>
                                        </Avatar>
                                        <span className={`absolute bottom-0 end-0 w-2.5 h-2.5 rounded-full ${presenceColor} border-2 border-card`} />
                                      </div>
                                      <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between">
                                          <span className="text-[11px] text-foreground truncate">{agent.name}</span>
                                          <Badge className="bg-muted/30 text-muted-foreground text-[7px] h-4 shrink-0">
                                            {agent.role === "supervisor" ? "مشرف" : "وكيل"}
                                          </Badge>
                                        </div>
                                        <div className="flex items-center gap-2 mt-0.5">
                                          <span className="text-[9px] text-muted-foreground">
                                            {agent.activeConversations}/{agent.maxCapacity} محادثة
                                          </span>
                                          <span className="text-[8px] text-muted-foreground/60">
                                            {agent.presence === "available" ? "متاح" :
                                             agent.presence === "busy" ? "مشغول" :
                                             agent.presence === "away" ? "بعيد" : "غير متصل"}
                                          </span>
                                        </div>
                                      </div>
                                    </button>
                                  );
                                })}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-primary">
                          <Phone className="w-3.5 h-3.5" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent className="text-xs">اتصال</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-primary">
                          <MoreHorizontal className="w-3.5 h-3.5" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent className="text-xs">المزيد</TooltipContent>
                    </Tooltip>
                  </div>
                </div>

                {/* Visual block warning */}
                {activeConv.activeWriter && activeConv.activeWriter !== "emp-01" && (
                  <div className="mt-2 flex items-center gap-2 text-[10px] text-red-400 bg-red-500/5 border border-red-500/20 rounded-lg px-3 py-1.5">
                    <Lock className="w-3 h-3" />
                    <span>المحادثة مقفلة — {mockAgents.find((a) => a.id === activeConv.activeWriter)?.name} يكتب الآن</span>
                    <Button variant="ghost" size="sm" className="h-5 text-[9px] ms-auto text-red-400 hover:text-red-300">
                      <Shield className="w-3 h-3 me-1" />
                      تجاوز (مشرف)
                    </Button>
                  </div>
                )}
              </div>

              {/* Outgoing transfer pending banner */}
              {activeConvPendingTransfer && activeConvPendingTransfer.fromAgentId === currentAgentId && (
                <div className="shrink-0 px-5 py-2">
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-2 text-[10px] text-primary bg-primary/5 border border-primary/20 rounded-lg px-3 py-2"
                    dir="rtl"
                  >
                    <ArrowLeftRight className="w-3.5 h-3.5 shrink-0" />
                    <span>
                      طلب نقل معلّق إلى <span className="text-foreground">{activeConvPendingTransfer.toAgentName}</span>
                      {activeConvPendingTransfer.reason && (
                        <span className="text-muted-foreground"> — {activeConvPendingTransfer.reason}</span>
                      )}
                    </span>
                    <span className="text-[8px] text-muted-foreground ms-1">{timeAgo(activeConvPendingTransfer.createdAt)}</span>
                    <button
                      className="ms-auto text-[9px] text-red-400 hover:text-red-300 flex items-center gap-0.5 cursor-pointer transition-colors"
                      onClick={() => handleCancelTransfer(activeConvPendingTransfer.id)}
                    >
                      <X className="w-3 h-3" />
                      إلغاء
                    </button>
                  </motion.div>
                </div>
              )}

              {/* Incoming transfer pending banner (receiver view) */}
              {activeConvPendingTransfer && activeConvPendingTransfer.toAgentId === currentAgentId && (
                <div className="shrink-0 px-5 py-2">
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-lg border border-emerald-500/20 overflow-hidden"
                    dir="rtl"
                  >
                    <div className="flex items-center gap-2 text-[10px] text-emerald-400 bg-emerald-500/5 px-3 py-2">
                      <ArrowLeftRight className="w-3.5 h-3.5 shrink-0" />
                      <span className="flex-1">
                        <span className="text-foreground">{activeConvPendingTransfer.fromAgentName}</span> يريد نقل هذه المحادثة إليك
                        {activeConvPendingTransfer.reason && (
                          <span className="text-muted-foreground"> — {activeConvPendingTransfer.reason}</span>
                        )}
                      </span>
                      <div className="shrink-0 flex items-center gap-1.5">
                        <button
                          className="text-[9px] text-emerald-400 hover:text-emerald-300 flex items-center gap-0.5 cursor-pointer bg-emerald-500/10 px-2 py-1 rounded-md transition-colors"
                          onClick={() => handleTransferResponse(activeConvPendingTransfer.id, "approved")}
                        >
                          <Check className="w-3 h-3" />
                          قبول
                        </button>
                        <button
                          className="text-[9px] text-red-400 hover:text-red-300 flex items-center gap-0.5 cursor-pointer bg-red-500/10 px-2 py-1 rounded-md transition-colors"
                          onClick={() => startRejectTransfer(activeConvPendingTransfer.id)}
                        >
                          <X className="w-3 h-3" />
                          رفض
                        </button>
                      </div>
                    </div>
                    {/* Inline rejection reason */}
                    <AnimatePresence>
                      {rejectingTransferId === activeConvPendingTransfer.id && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <div className="px-3 pb-2 pt-1.5 border-t border-red-500/15 bg-red-500/[0.03]">
                            <label className="text-[8px] text-red-400 mb-1 block">سبب الرفض (مطلوب)</label>
                            <div className="flex items-center gap-1.5">
                              <Input
                                placeholder="اكتب سبب الرفض..."
                                className="flex-1 h-7 text-[10px] border-red-500/20 focus:border-red-500/40"
                                value={rejectionReason}
                                onChange={(e) => setRejectionReason(e.target.value)}
                                autoFocus
                                onKeyDown={(e) => {
                                  if (e.key === "Enter" && rejectionReason.trim()) confirmRejectTransfer();
                                }}
                              />
                              <button
                                className="text-[9px] text-white bg-red-600 hover:bg-red-700 px-2 py-1 rounded-md transition-colors disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed"
                                disabled={!rejectionReason.trim()}
                                onClick={confirmRejectTransfer}
                              >
                                تأكيد
                              </button>
                              <button
                                className="text-[9px] text-muted-foreground hover:text-foreground px-1 py-1 cursor-pointer transition-colors"
                                onClick={() => { setRejectingTransferId(null); setRejectionReason(""); }}
                              >
                                إلغاء
                              </button>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                </div>
              )}

              {/* Messages area */}
              <ScrollArea dir="rtl" className="flex-1 min-h-0">
                <div className="p-5 space-y-3">
                  {activeMessages.map((msg) => (
                    <MessageBubble key={msg.id} msg={msg} />
                  ))}
                  <div ref={chatEndRef} />
                </div>
              </ScrollArea>

              {/* Message input */}
              <div className="shrink-0 px-5 py-3 border-t border-border/30 bg-card/30">
                <div className="flex items-end gap-2">
                  <div className="flex gap-1 shrink-0 pb-1">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-primary">
                          <Paperclip className="w-4 h-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent className="text-xs">إرفاق ملف</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-primary">
                          <BookOpen className="w-4 h-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent className="text-xs">إرسال الكتالوج</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-primary">
                          <FileText className="w-4 h-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent className="text-xs">إرسال فاتورة</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-primary">
                          <Mic className="w-4 h-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent className="text-xs">رسالة صوتية</TooltipContent>
                    </Tooltip>
                  </div>
                  <div className="flex-1 relative">
                    <Input
                      placeholder="اكتب رسالة..."
                      className="pe-10 text-xs"
                      value={messageInput}
                      onChange={(e) => setMessageInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          setMessageInput("");
                        }
                      }}
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      className="absolute end-1 top-1/2 -translate-y-1/2 h-7 w-7 text-primary hover:bg-primary/10"
                      onClick={() => setMessageInput("")}
                    >
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">
              <div className="text-center">
                <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-20" />
                <p>اختر محادثة للبدء</p>
              </div>
            </div>
          )}
        </div>

        {/* ═══ Right: Side panels ═══ */}
        <AnimatePresence>
          {sidePanel !== "none" && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 300, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
              className="shrink-0 border-s border-border/30 bg-card/40 overflow-hidden"
            >
              <div className="w-[300px] h-full flex flex-col">
                {/* Panel header */}
                <div className="shrink-0 p-3 border-b border-border/20 flex items-center justify-between">
                  <span className="text-xs text-foreground">
                    {sidePanel === "escalation" && "التصعيدات"}
                    {sidePanel === "calling" && "قائمة الاتصال"}
                    {sidePanel === "templates" && "القوالب"}
                    {sidePanel === "missed" && "المكالمات الفائتة"}
                    {sidePanel === "transfers" && "سجل نقل المحادثات"}
                  </span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 text-muted-foreground"
                    onClick={() => setSidePanel("none")}
                  >
                    <X className="w-3.5 h-3.5" />
                  </Button>
                </div>

                <ScrollArea dir="rtl" className="flex-1 min-h-0">
                  <div className="p-3 space-y-2">
                    {sidePanel === "escalation" && (
                      <>
                        {mockEscalations.map((esc) => (
                          <div key={esc.id} className="p-3 rounded-xl border border-red-500/20 bg-card shadow-[0_2px_8px_rgba(0,0,0,0.2),_inset_0_1px_0_rgba(255,255,255,0.03)] space-y-1.5">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-foreground">{esc.customerName}</span>
                              <Badge className="bg-red-500/15 text-red-500 text-[8px] h-4">{esc.priority === "urgent" ? "عاجل" : "عالي"}</Badge>
                            </div>
                            <p className="text-[10px] text-muted-foreground">{esc.reason}</p>
                            <div className="flex items-center gap-2 text-[9px] text-red-400">
                              <Clock className="w-3 h-3" />
                              <span>منذ {esc.waitingMinutes} دقيقة</span>
                            </div>
                            <Button size="sm" className="w-full h-7 text-[10px] mt-1">
                              تولي المحادثة
                            </Button>
                          </div>
                        ))}
                        {mockEscalations.length === 0 && (
                          <p className="text-center text-xs text-muted-foreground py-8">لا توجد تصعيدات</p>
                        )}
                      </>
                    )}

                    {sidePanel === "calling" && (
                      <>
                        {mockCallingList.map((item) => (
                          <div key={item.id} className="p-3 rounded-xl border border-border/30 bg-card shadow-[0_2px_8px_rgba(0,0,0,0.2),_inset_0_1px_0_rgba(255,255,255,0.03)] space-y-1.5">
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-foreground">{item.customerName}</span>
                              <Badge className={`text-[8px] h-4 ${
                                item.status === "pending" ? "bg-blue-500/10 text-blue-400" :
                                item.status === "called" ? "bg-emerald-500/10 text-emerald-400" :
                                item.status === "success" ? "bg-primary/10 text-primary" :
                                item.status === "rescheduled" ? "bg-violet-500/10 text-violet-400" :
                                "bg-red-500/10 text-red-400"
                              }`}>
                                {item.status === "pending" ? "في الانتظار" :
                                 item.status === "called" ? "تم الاتصال" :
                                 item.status === "success" ? "نجاح" :
                                 item.status === "rescheduled" ? "مؤجل" : "فشل"}
                              </Badge>
                            </div>
                            <p className="text-[10px] text-muted-foreground">{item.target}</p>
                            <p className="text-[9px] text-muted-foreground/60">{item.notes}</p>
                            <div className="flex items-center justify-between">
                              <span className="text-[9px] text-muted-foreground">
                                نسبة النجاح المتوقعة: <span className="text-primary">{item.expectedSuccessRate}%</span>
                              </span>
                              {item.status === "pending" && (
                                <Button size="sm" variant="outline" className="h-6 text-[9px] gap-1">
                                  <Phone className="w-2.5 h-2.5" />
                                  اتصال
                                </Button>
                              )}
                            </div>
                          </div>
                        ))}
                      </>
                    )}

                    {sidePanel === "templates" && (
                      <>
                        {ocTemplates.map((tpl) => (
                          <button
                            key={tpl.id}
                            className="w-full text-start p-3 rounded-xl border border-border/30 bg-card shadow-[0_2px_8px_rgba(0,0,0,0.2),_inset_0_1px_0_rgba(255,255,255,0.03)] hover:border-primary/30 hover:shadow-[0_4px_14px_rgba(0,0,0,0.25),_inset_0_1px_0_rgba(255,255,255,0.05)] hover:-translate-y-0.5 transition-all duration-200 space-y-1"
                            onClick={() => setMessageInput(tpl.content)}
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-xs text-foreground">{tpl.name}</span>
                              <Badge className="bg-muted/30 text-muted-foreground text-[7px] h-4">
                                {tpl.channel === "all" ? "عام" : channelConfigs.find((c) => c.id === tpl.channel)?.label}
                              </Badge>
                            </div>
                            <p className="text-[10px] text-muted-foreground line-clamp-2">{tpl.content}</p>
                          </button>
                        ))}
                      </>
                    )}

                    {sidePanel === "missed" && (
                      <>
                        {/* Summary bar */}
                        <div className="flex items-center justify-between px-1 pb-1">
                          <span className="text-[9px] text-red-400 flex items-center gap-1">
                            <PhoneMissed className="w-3 h-3" />
                            {mockOCMissedCalls.filter((c) => c.status === "pending").length} بانتظار الرد
                          </span>
                          <span className="text-[8px] text-muted-foreground">{mockOCMissedCalls.length} مكالمة</span>
                        </div>

                        {mockOCMissedCalls
                          .sort((a, b) => {
                            const order: Record<MissedCallAgentStatus, number> = { pending: 0, "callback-scheduled": 1, returned: 2, resolved: 3 };
                            return order[a.status] - order[b.status];
                          })
                          .map((call) => {
                            const isPending = call.status === "pending";
                            const statusLabel = call.status === "pending" ? "بانتظار الرد" : call.status === "callback-scheduled" ? "موعد إعادة" : call.status === "returned" ? "تم الاتصال" : "تم الحل";
                            const statusClass = call.status === "pending" ? "bg-red-500/15 text-red-400" : call.status === "callback-scheduled" ? "bg-primary/15 text-primary" : call.status === "returned" ? "bg-blue-500/15 text-blue-400" : "bg-emerald-500/15 text-emerald-400";

                            return (
                              <div
                                key={call.id}
                                className={`p-3 rounded-xl border bg-card shadow-[0_2px_8px_rgba(0,0,0,0.2),_inset_0_1px_0_rgba(255,255,255,0.03)] space-y-1.5 ${
                                  isPending ? "border-red-500/25" : "border-border/30"
                                }`}
                              >
                                <div className="flex items-center justify-between">
                                  <span className="text-xs text-foreground">{call.customerName}</span>
                                  <Badge className={`text-[7px] h-4 ${statusClass}`}>{statusLabel}</Badge>
                                </div>

                                <div className="flex items-center gap-2.5 text-[9px] text-muted-foreground">
                                  <span className="flex items-center gap-1" dir="ltr">
                                    <Phone className="w-2.5 h-2.5" />
                                    {call.customerPhone}
                                  </span>
                                </div>

                                <div className="flex items-center gap-2.5 text-[9px] text-muted-foreground">
                                  <span className="flex items-center gap-1">
                                    <Clock className="w-2.5 h-2.5" />
                                    {new Date(call.missedAt).toLocaleTimeString("ar-SA", { hour: "2-digit", minute: "2-digit" })}
                                  </span>
                                  <span className="flex items-center gap-1">
                                    <RotateCcw className="w-2.5 h-2.5" />
                                    {call.attempts} {call.attempts > 1 ? "محاولات" : "محاولة"}
                                  </span>
                                  <span className="text-[8px] px-1 py-0.5 rounded bg-muted/20">{call.channel === "phone" ? "هاتف" : channelConfigs.find((c) => c.id === call.channel)?.label ?? call.channel}</span>
                                </div>

                                <p className="text-[9px] text-muted-foreground/70">{call.reason}</p>

                                {call.note && (
                                  <p className="text-[9px] text-muted-foreground/80 border-s-2 border-primary/20 ps-2">{call.note}</p>
                                )}

                                <div className="text-[8px] text-muted-foreground/60">
                                  عيّنها: {call.assignedBy}
                                  {call.callbackTime && (
                                    <span> — موعد الاتصال: {new Date(call.callbackTime).toLocaleTimeString("ar-SA", { hour: "2-digit", minute: "2-digit" })}</span>
                                  )}
                                </div>

                                {(call.status === "pending" || call.status === "callback-scheduled") && (
                                  <Button size="sm" className="w-full h-7 text-[10px] mt-1 gap-1">
                                    <PhoneCall className="w-3 h-3" />
                                    إعادة الاتصال
                                  </Button>
                                )}
                                {call.status === "returned" && (
                                  <Button size="sm" variant="outline" className="w-full h-7 text-[10px] mt-1 gap-1 text-emerald-400 border-emerald-500/30">
                                    <CheckCircle2 className="w-3 h-3" />
                                    تأكيد الحل
                                  </Button>
                                )}
                              </div>
                            );
                          })}

                        {mockOCMissedCalls.length === 0 && (
                          <div className="text-center py-8">
                            <CheckCircle2 className="w-6 h-6 mx-auto mb-2 text-emerald-400/30" />
                            <p className="text-xs text-muted-foreground">لا توجد مكالمات فائتة</p>
                          </div>
                        )}
                      </>
                    )}

                    {sidePanel === "transfers" && (
                      <>
                        {/* Summary stats */}
                        <div className="flex items-center justify-between px-1 pb-2">
                          <span className="text-[9px] text-primary flex items-center gap-1">
                            <ArrowLeftRight className="w-3 h-3" />
                            {transferRequests.filter((t) => t.status === "pending").length} معلّق
                          </span>
                          <div className="flex items-center gap-2 text-[8px] text-muted-foreground">
                            <span className="flex items-center gap-0.5"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" /> {transferRequests.filter((t) => t.status === "approved").length} مقبول</span>
                            <span className="flex items-center gap-0.5"><span className="w-1.5 h-1.5 rounded-full bg-red-500 inline-block" /> {transferRequests.filter((t) => t.status === "rejected").length} مرفوض</span>
                          </div>
                        </div>

                        {transferRequests
                          .sort((a, b) => {
                            const order: Record<string, number> = { pending: 0, rejected: 1, approved: 2, cancelled: 3 };
                            const diff = order[a.status] - order[b.status];
                            if (diff !== 0) return diff;
                            return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
                          })
                          .map((tr) => {
                            const ChIcon = channelIcons[tr.channel];
                            const statusConfig = {
                              pending: { label: "معلّق", cls: "bg-primary/15 text-primary" },
                              approved: { label: "مقبول", cls: "bg-emerald-500/15 text-emerald-400" },
                              rejected: { label: "مرفوض", cls: "bg-red-500/15 text-red-400" },
                              cancelled: { label: "ملغي", cls: "bg-muted/30 text-muted-foreground" },
                            }[tr.status];

                            return (
                              <div
                                key={tr.id}
                                className={`p-3 rounded-xl border bg-card shadow-[0_2px_8px_rgba(0,0,0,0.2),_inset_0_1px_0_rgba(255,255,255,0.03)] space-y-2 ${
                                  tr.status === "pending" ? "border-primary/25" :
                                  tr.status === "rejected" ? "border-red-500/20" :
                                  "border-border/30"
                                }`}
                              >
                                {/* Header: customer + status */}
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-1.5">
                                    <ChIcon className="w-3 h-3" style={{ color: getChannelColor(tr.channel) }} />
                                    <span className="text-xs text-foreground">{tr.customerName}</span>
                                  </div>
                                  <Badge className={`text-[7px] h-4 ${statusConfig.cls}`}>{statusConfig.label}</Badge>
                                </div>

                                {/* From → To */}
                                <div className="flex items-center gap-1.5 text-[9px]">
                                  <Avatar className="h-5 w-5">
                                    <AvatarFallback className="text-[7px] bg-primary/10 text-primary">
                                      {tr.fromAgentName.slice(0, 2)}
                                    </AvatarFallback>
                                  </Avatar>
                                  <span className="text-foreground">{tr.fromAgentName}</span>
                                  <ArrowLeftRight className="w-3 h-3 text-muted-foreground shrink-0" />
                                  <Avatar className="h-5 w-5">
                                    <AvatarFallback className="text-[7px] bg-primary/10 text-primary">
                                      {tr.toAgentName.slice(0, 2)}
                                    </AvatarFallback>
                                  </Avatar>
                                  <span className="text-foreground">{tr.toAgentName}</span>
                                </div>

                                {/* Transfer reason (always present — required) */}
                                <div className="space-y-0.5">
                                  <span className="text-[8px] text-muted-foreground/60">سبب النقل:</span>
                                  <p className="text-[10px] text-muted-foreground border-s-2 border-primary/20 ps-2">{tr.reason}</p>
                                </div>

                                {/* Rejection reason (highlighted) */}
                                {tr.status === "rejected" && tr.rejectionReason && (
                                  <div className="space-y-0.5">
                                    <span className="text-[8px] text-red-400">سبب الرفض:</span>
                                    <p className="text-[10px] text-red-300 bg-red-500/[0.06] border border-red-500/15 rounded-md px-2 py-1.5">{tr.rejectionReason}</p>
                                  </div>
                                )}

                                {/* Time info */}
                                <div className="flex items-center gap-2 text-[8px] text-muted-foreground/60">
                                  <span className="flex items-center gap-0.5">
                                    <Clock className="w-2.5 h-2.5" />
                                    {new Date(tr.createdAt).toLocaleTimeString("ar-SA", { hour: "2-digit", minute: "2-digit" })}
                                  </span>
                                  {tr.respondedAt && (
                                    <span>
                                      الرد: {new Date(tr.respondedAt).toLocaleTimeString("ar-SA", { hour: "2-digit", minute: "2-digit" })}
                                    </span>
                                  )}
                                </div>
                              </div>
                            );
                          })}

                        {transferRequests.length === 0 && (
                          <div className="text-center py-8">
                            <ArrowLeftRight className="w-6 h-6 mx-auto mb-2 text-muted-foreground/20" />
                            <p className="text-xs text-muted-foreground">لا توجد عمليات نقل</p>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </ScrollArea>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ═══ Far Right: Internal Notes Panel (when chat active) ═══ */}
        {activeConv && (
          <div className="w-56 shrink-0 border-s-2 border-s-yellow-500/40 bg-yellow-500/[0.04] flex flex-col">
            <div className="shrink-0 px-3 py-2.5 border-b border-yellow-500/20 bg-yellow-500/10 flex items-center gap-2">
              <div className="w-5 h-5 rounded-md bg-yellow-500/20 flex items-center justify-center">
                <FileText className="w-3 h-3 text-yellow-600 dark:text-yellow-400" />
              </div>
              <span className="text-[11px] text-yellow-700 dark:text-yellow-400">ملاحظات داخلية</span>
            </div>
            <ScrollArea dir="rtl" className="flex-1 min-h-0">
              <div className="p-2 space-y-2">
                {activeMessages.filter((m) => m.isInternalNote).map((note) => (
                  <div key={note.id} className="p-2.5 rounded-lg bg-yellow-500/[0.07] border border-yellow-500/15 space-y-1.5">
                    <div className="flex items-center gap-1.5">
                      <User className="w-2.5 h-2.5 text-yellow-600 dark:text-yellow-400" />
                      <span className="text-[9px] text-yellow-700 dark:text-yellow-400">{note.senderName}</span>
                    </div>
                    <p className="text-[10px] text-foreground/80">{note.content}</p>
                    <div className="flex items-center gap-1 text-[8px] text-muted-foreground/70">
                      <Clock className="w-2.5 h-2.5" />
                      <span>{new Date(note.timestamp).toLocaleDateString("ar-SA", { day: "numeric", month: "short" })}</span>
                      <span className="opacity-50">·</span>
                      <span>{formatTime(note.timestamp)}</span>
                    </div>
                  </div>
                ))}
                {activeMessages.filter((m) => m.isInternalNote).length === 0 && (
                  <p className="text-center text-[9px] text-muted-foreground py-4">لا توجد ملاحظات</p>
                )}
              </div>
            </ScrollArea>
            <div className="shrink-0 p-2 border-t border-yellow-500/20 bg-yellow-500/[0.04] flex items-center gap-1.5">
              <Input
                placeholder="أضف ملاحظة @mention..."
                className="h-7 text-[10px] border-yellow-500/20 focus:border-yellow-500/40 flex-1"
                value={noteInput}
                onChange={(e) => setNoteInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && noteInput.trim()) {
                    handleAddNote();
                  }
                }}
              />
              <Button
                size="icon"
                className="h-7 w-7 shrink-0 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-700 dark:text-yellow-400 border-none"
                disabled={!noteInput.trim()}
                onClick={handleAddNote}
              >
                <Send className="w-3 h-3" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}

// ── Conversation Card ───────────────────────────────────

function ConversationCard({
  conv,
  isActive,
  onClick,
}: {
  conv: OCConversation;
  isActive: boolean;
  onClick: () => void;
}) {
  const Icon = channelIcons[conv.channel];
  const isOpen = conv.status === "open" || conv.status === "waiting";

  return (
    <motion.button
      onClick={onClick}
      className={`w-full text-start p-3 rounded-xl border transition-all duration-200 ${
        isActive
          ? "border-primary/50 bg-card shadow-[0_4px_16px_rgba(0,0,0,0.25),_0_1px_3px_rgba(0,0,0,0.15),_inset_0_1px_0_rgba(255,255,255,0.04)] ring-1 ring-primary/20"
          : isOpen
            ? "border-border/30 bg-card shadow-[0_2px_8px_rgba(0,0,0,0.2),_0_1px_2px_rgba(0,0,0,0.12),_inset_0_1px_0_rgba(255,255,255,0.03)] hover:shadow-[0_6px_20px_rgba(0,0,0,0.3),_0_2px_6px_rgba(0,0,0,0.15),_inset_0_1px_0_rgba(255,255,255,0.05)] hover:border-primary/25 hover:-translate-y-0.5"
            : "border-border/20 bg-card/80 shadow-[0_1px_4px_rgba(0,0,0,0.15),_inset_0_1px_0_rgba(255,255,255,0.02)] hover:shadow-[0_3px_10px_rgba(0,0,0,0.2),_inset_0_1px_0_rgba(255,255,255,0.03)] hover:border-border/40 hover:-translate-y-0.5"
      }`}
      whileTap={{ scale: 0.97 }}
    >
      <div className="flex items-start gap-2.5">
        <div className="relative shrink-0 mt-0.5">
          <Avatar className="h-8 w-8">
            <AvatarFallback
              className="text-[9px]"
              style={{ backgroundColor: getChannelColor(conv.channel) + "20", color: getChannelColor(conv.channel) }}
            >
              {conv.customerName.slice(0, 2)}
            </AvatarFallback>
          </Avatar>
          <span
            className="absolute -bottom-0.5 -end-0.5 w-4 h-4 rounded-full flex items-center justify-center"
            style={{ backgroundColor: getChannelColor(conv.channel) }}
          >
            <Icon className="w-2.5 h-2.5" style={{ color: "#fff" }} />
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-1">
            <div className="flex items-center gap-1 min-w-0">
              <span className={`text-[11px] truncate ${isOpen ? "text-foreground" : "text-muted-foreground"}`}>
                {conv.customerName}
              </span>
              {conv.isVip && <Star className="w-3 h-3 text-primary fill-primary shrink-0" />}
            </div>
            <span className="text-[8px] text-muted-foreground shrink-0">{timeAgo(conv.lastMessageTime)}</span>
          </div>

          <p className={`text-[10px] truncate mt-0.5 ${isOpen ? "text-foreground/70" : "text-muted-foreground/60"}`}>
            {conv.lastMessage}
          </p>

          <div className="flex items-center gap-1.5 mt-1">
            {conv.unreadCount > 0 && (
              <span className="w-4 h-4 rounded-full bg-primary text-[7px] text-white flex items-center justify-center">
                {conv.unreadCount}
              </span>
            )}
            {conv.isUnregistered && (
              <span className="text-[7px] px-1 py-0.5 rounded bg-red-500/10 text-red-400">غير مسجل</span>
            )}
            {conv.isEscalated && (
              <span className="text-[7px] px-1 py-0.5 rounded bg-red-500/10 text-red-400 flex items-center gap-0.5">
                <AlertTriangle className="w-2 h-2" /> تصعيد
              </span>
            )}
            {conv.aiHandled && (
              <span className="text-[7px] px-1 py-0.5 rounded bg-violet-500/10 text-violet-400 flex items-center gap-0.5">
                <Bot className="w-2 h-2" /> AI
              </span>
            )}
            {conv.openedBy.length > 0 && conv.status === "open" && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="text-[7px] px-1 py-0.5 rounded bg-muted/30 text-muted-foreground flex items-center gap-0.5">
                    <Eye className="w-2 h-2" /> {conv.openedBy.length}
                  </span>
                </TooltipTrigger>
                <TooltipContent className="text-[10px]">
                  فتحها: {conv.openedBy.map((id) => mockAgents.find((a) => a.id === id)?.name).join("، ")}
                </TooltipContent>
              </Tooltip>
            )}
          </div>
        </div>
      </div>
    </motion.button>
  );
}

// ── Message Bubble ──────────────────────────────────────

function MessageBubble({ msg }: { msg: OCMessage }) {
  if (msg.isInternalNote) return null;

  const isCustomer = msg.sender === "customer";
  const isSystem = msg.sender === "system";
  const isAi = msg.sender === "ai";

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <span className="text-[9px] text-muted-foreground bg-muted/20 px-3 py-1 rounded-full">
          {msg.content}
        </span>
      </div>
    );
  }

  return (
    <div className={`flex ${isCustomer ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[70%] rounded-xl px-4 py-2.5 space-y-1 ${
          isCustomer
            ? "bg-primary/10 border border-primary/20 rounded-te-sm"
            : isAi
              ? "bg-violet-500/10 border border-violet-500/20 rounded-ts-sm"
              : "bg-muted/50 border border-border/50 rounded-ts-sm"
        }`}
      >
        <div className="flex items-center gap-2">
          <span className={`text-[9px] ${isCustomer ? "text-primary" : isAi ? "text-violet-400" : "text-foreground/70"}`}>
            {msg.senderName}
            {isAi && " (AI)"}
          </span>
        </div>
        <p className="text-xs text-foreground/90">{msg.content}</p>
        <div className="flex items-center justify-end gap-1.5">
          <span className="text-[8px] text-muted-foreground">{formatTime(msg.timestamp)}</span>
          {!isCustomer && msg.read && (
            <Check className="w-3 h-3 text-primary" />
          )}
        </div>
      </div>
    </div>
  );
}