import { useState, useCallback, useEffect } from "react";
import { Card, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { Avatar, AvatarFallback } from "./ui/avatar";
import { ScrollArea } from "./ui/scroll-area";
import {
  Crown, Phone, Mail, ShoppingBag,
  ShieldCheck, MoreHorizontal, Plus
} from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./ui/tooltip";

// ─── Types ───────────────────────────────────────────────
export type CustomerStage = "lead" | "interested" | "active" | "vip" | "dormant";

export interface KanbanCustomer {
  id: string;
  name: string;
  email: string;
  phone: string;
  address: string;
  totalPurchases: number;
  joinDate: string;
  vipStatus: boolean;
  favoriteFragrance?: string;
  stage: CustomerStage;
  lastActivity?: string;
  channelIdentities?: { channel: string; handle: string; verified: boolean }[];
}

interface CustomerKanbanProps {
  customers: KanbanCustomer[];
  onCustomerClick: (customer: KanbanCustomer) => void;
  onStageChange?: (customerId: string, newStage: CustomerStage) => void;
}

// ─── Stage Configuration ─────────────────────────────────
const stageConfig: Record<CustomerStage, {
  label: string;
  color: string;
  bg: string;
  border: string;
  headerBg: string;
  dot: string;
  icon: string;
}> = {
  lead: {
    label: "عميل محتمل",
    color: "text-blue-600 dark:text-blue-400",
    bg: "bg-blue-50 dark:bg-blue-500/5",
    border: "border-blue-200 dark:border-blue-500/20",
    headerBg: "bg-blue-100/80 dark:bg-blue-500/10",
    dot: "bg-blue-500",
    icon: "💎",
  },
  interested: {
    label: "مهتم",
    color: "text-purple-600 dark:text-purple-400",
    bg: "bg-purple-50 dark:bg-purple-500/5",
    border: "border-purple-200 dark:border-purple-500/20",
    headerBg: "bg-purple-100/80 dark:bg-purple-500/10",
    dot: "bg-purple-500",
    icon: "✨",
  },
  active: {
    label: "عميل نشط",
    color: "text-green-600 dark:text-green-400",
    bg: "bg-green-50 dark:bg-green-500/5",
    border: "border-green-200 dark:border-green-500/20",
    headerBg: "bg-green-100/80 dark:bg-green-500/10",
    dot: "bg-green-500",
    icon: "🛒",
  },
  vip: {
    label: "VIP",
    color: "text-[#B8860B] dark:text-primary",
    bg: "bg-[#FDF5E6] dark:bg-primary/5",
    border: "border-[#D4AF37]/30 dark:border-primary/20",
    headerBg: "bg-[#FDF5E6] dark:bg-primary/10",
    dot: "bg-[#D4AF37] dark:bg-primary",
    icon: "👑",
  },
  dormant: {
    label: "راكد",
    color: "text-slate-500 dark:text-slate-400",
    bg: "bg-slate-50 dark:bg-slate-500/5",
    border: "border-slate-200 dark:border-slate-500/20",
    headerBg: "bg-slate-100/80 dark:bg-slate-500/10",
    dot: "bg-slate-400",
    icon: "💤",
  },
};

const stageOrder: CustomerStage[] = ["lead", "interested", "active", "vip", "dormant"];

// ─── Channel mini icons (same as customer card) ──────────
import { getChannelIcon } from "./analytics/channel-icons";

const channelMini: Record<string, { label: string; icon: React.ReactNode; color: string; bg: string }> = {
  whatsapp: { label: "واتساب", icon: getChannelIcon("whatsapp", "w-2.5 h-2.5"), color: "text-green-600 dark:text-green-400", bg: "bg-green-100 dark:bg-green-500/15" },
  instagram: { label: "إنستغرام", icon: getChannelIcon("instagram", "w-2.5 h-2.5"), color: "text-pink-600 dark:text-pink-400", bg: "bg-pink-100 dark:bg-pink-500/15" },
  x: { label: "X", icon: getChannelIcon("x", "w-2.5 h-2.5"), color: "text-slate-700 dark:text-slate-300", bg: "bg-slate-100 dark:bg-slate-500/15" },
  snapchat: { label: "سناب شات", icon: getChannelIcon("snapchat", "w-2.5 h-2.5"), color: "text-yellow-600 dark:text-yellow-400", bg: "bg-yellow-100 dark:bg-yellow-500/15" },
  tiktok: { label: "تيك توك", icon: getChannelIcon("tiktok", "w-2.5 h-2.5"), color: "text-slate-800 dark:text-slate-200", bg: "bg-slate-100 dark:bg-slate-500/15" },
  telegram: { label: "تيليجرام", icon: getChannelIcon("telegram", "w-2.5 h-2.5"), color: "text-blue-600 dark:text-blue-400", bg: "bg-blue-100 dark:bg-blue-500/15" },
  website: { label: "الموقع", icon: getChannelIcon("website", "w-2.5 h-2.5"), color: "text-cyan-600 dark:text-primary", bg: "bg-cyan-100 dark:bg-primary/15" },
  email: { label: "البريد", icon: getChannelIcon("email", "w-2.5 h-2.5"), color: "text-red-600 dark:text-red-400", bg: "bg-red-100 dark:bg-red-500/15" },
  store: { label: "المتجر", icon: getChannelIcon("store", "w-2.5 h-2.5"), color: "text-purple-600 dark:text-purple-400", bg: "bg-purple-100 dark:bg-purple-500/15" },
};

// ─── Kanban Card ─────────────────────────────────────────
function KanbanCard({
  customer,
  onClick,
  index,
}: {
  customer: KanbanCustomer;
  onClick: () => void;
  index: number;
}) {
  const channels = customer.channelIdentities || [];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2, delay: index * 0.03 }}
    >
      <Card
        className="bg-white dark:bg-[#1a1d24] border-slate-150 dark:border-white/[0.06] shadow-sm hover:shadow-md hover:border-primary/30 dark:hover:border-primary/20 transition-all duration-200 cursor-pointer group overflow-hidden"
        onClick={onClick}
      >
        <CardContent className="p-3.5">
          {/* Top: Avatar + Name + VIP */}
          <div className="flex items-start gap-3 mb-3">
            <Avatar className="h-9 w-9 border border-border/50 shrink-0 group-hover:border-primary/40 transition-colors">
              <AvatarFallback className="bg-primary/10 text-primary text-[11px] font-bold">
                {customer.name.split(" ").map(n => n[0]).join("").slice(0, 2)}
              </AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5">
                <p className="text-xs font-bold text-foreground truncate group-hover:text-primary transition-colors">
                  {customer.name}
                </p>
                {customer.vipStatus && (
                  <Crown className="w-3.5 h-3.5 text-primary shrink-0" />
                )}
              </div>
              <p className="text-[10px] text-muted-foreground font-mono">{customer.id}</p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 text-muted-foreground hover:text-primary opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
              onClick={(e) => { e.stopPropagation(); }}
            >
              <MoreHorizontal className="w-3.5 h-3.5" />
            </Button>
          </div>

          {/* Contact row */}
          <div className="space-y-1.5 mb-3">
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
              <Mail className="w-3 h-3 shrink-0" />
              <span className="truncate">{customer.email}</span>
            </div>
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
              <Phone className="w-3 h-3 shrink-0" />
              <span className="font-mono" dir="ltr">{customer.phone}</span>
            </div>
          </div>

          {/* Channel Identity Icons */}
          {channels.length > 0 && (
            <div className="mb-3">
              <TooltipProvider delayDuration={200}>
                <div className="flex flex-wrap gap-1">
                  {channels.slice(0, 6).map((ch, i) => {
                    const cfg = channelMini[ch.channel];
                    if (!cfg) return null;
                    return (
                      <Tooltip key={i}>
                        <TooltipTrigger asChild>
                          <div className={`relative p-1 rounded border border-border/30 ${cfg.bg} cursor-default transition-transform hover:scale-110`}>
                            <span className={cfg.color}>{cfg.icon}</span>
                            {ch.verified && (
                              <div className="absolute -top-0.5 -end-0.5 w-2 h-2 bg-cyan-500 dark:bg-primary rounded-full border border-card" />
                            )}
                          </div>
                        </TooltipTrigger>
                        <TooltipContent side="top" className="text-[9px]">
                          <p>{cfg.label}: {ch.handle}</p>
                        </TooltipContent>
                      </Tooltip>
                    );
                  })}
                  {channels.length > 6 && (
                    <div className="p-1 rounded border border-border/30 bg-muted/50 text-[9px] text-muted-foreground flex items-center justify-center min-w-[22px]">
                      +{channels.length - 6}
                    </div>
                  )}
                </div>
              </TooltipProvider>
            </div>
          )}

          {/* Divider */}
          <div className="h-px bg-gradient-to-l from-transparent via-border to-transparent mb-3" />

          {/* Bottom: Stats */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <ShoppingBag className="w-3 h-3 text-primary" />
              <span className="text-[11px] font-bold text-primary font-mono">
                {customer.totalPurchases.toLocaleString()}
              </span>
              <span className="text-[9px] text-muted-foreground">ر.س</span>
            </div>
            {customer.favoriteFragrance && (
              <span className="text-[9px] bg-primary/5 text-primary/80 px-1.5 py-0.5 rounded-md border border-primary/10 truncate max-w-[100px]">
                {customer.favoriteFragrance}
              </span>
            )}
          </div>

          {/* Last activity */}
          {customer.lastActivity && (
            <p className="text-[9px] text-muted-foreground mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
              آخر نشاط: {customer.lastActivity}
            </p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

// ─── Kanban Column ───────────────────────────────────────
function KanbanColumn({
  stage,
  customers,
  onCustomerClick,
  onDrop,
  draggedCustomerId,
  onDragStart,
  onDragEnd,
}: {
  stage: CustomerStage;
  customers: KanbanCustomer[];
  onCustomerClick: (customer: KanbanCustomer) => void;
  onDrop: (customerId: string, targetStage: CustomerStage) => void;
  draggedCustomerId: string | null;
  onDragStart: (customerId: string) => void;
  onDragEnd: () => void;
}) {
  const config = stageConfig[stage];
  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const customerId = e.dataTransfer.getData("text/plain");
    if (customerId) {
      onDrop(customerId, stage);
    }
  }, [onDrop, stage]);

  return (
    <div
      className={`flex flex-col min-w-[280px] w-[280px] lg:w-auto lg:flex-1 rounded-xl border transition-all duration-200 ${
        isDragOver
          ? `${config.border} ${config.bg} ring-2 ring-primary/30 shadow-lg`
          : "border-slate-200 dark:border-white/[0.06] bg-slate-50/50 dark:bg-[#111318]/50"
      }`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Column Header */}
      <div className={`px-4 py-3 rounded-t-xl ${config.headerBg} border-b ${config.border}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${config.dot}`} />
            <h3 className={`text-xs font-bold ${config.color}`}>{config.label}</h3>
            <span className="text-[10px] bg-white/60 dark:bg-white/10 text-muted-foreground px-1.5 py-0.5 rounded-full font-mono min-w-[20px] text-center">
              {customers.length}
            </span>
          </div>
          <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-primary">
            <Plus className="w-3.5 h-3.5" />
          </Button>
        </div>
        {/* Total value */}
        <p className="text-[10px] text-muted-foreground mt-1">
          الإجمالي: <span className="font-mono font-bold">{customers.reduce((sum, c) => sum + c.totalPurchases, 0).toLocaleString()}</span> ر.س
        </p>
      </div>

      {/* Cards */}
      <ScrollArea className="flex-1 min-h-0" dir="rtl">
        <div className="p-2.5 space-y-2.5">
          <AnimatePresence mode="popLayout">
            {customers.map((customer, i) => (
              <div
                key={customer.id}
                draggable
                onDragStart={(e) => {
                  e.dataTransfer.setData("text/plain", customer.id);
                  onDragStart(customer.id);
                }}
                onDragEnd={onDragEnd}
                className={`${
                  draggedCustomerId === customer.id ? "opacity-40 scale-95" : ""
                } transition-all duration-200`}
              >
                <KanbanCard
                  customer={customer}
                  onClick={() => onCustomerClick(customer)}
                  index={i}
                />
              </div>
            ))}
          </AnimatePresence>

          {customers.length === 0 && (
            <div className="py-8 text-center">
              <p className="text-xs text-muted-foreground">لا يوجد عملاء</p>
              <p className="text-[10px] text-muted-foreground/60 mt-1">اسحب عميلاً هنا</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

// ─── Main Kanban Component ───────────────────────────────
export function CustomerKanban({ customers, onCustomerClick, onStageChange }: CustomerKanbanProps) {
  const [localCustomers, setLocalCustomers] = useState(customers);
  const [draggedCustomerId, setDraggedCustomerId] = useState<string | null>(null);

  // Sync with parent when customers prop changes
  useEffect(() => { setLocalCustomers(customers); }, [customers]);

  const handleDrop = useCallback((customerId: string, targetStage: CustomerStage) => {
    setLocalCustomers(prev =>
      prev.map(c =>
        c.id === customerId
          ? { ...c, stage: targetStage, vipStatus: targetStage === "vip" ? true : c.vipStatus }
          : c
      )
    );
    onStageChange?.(customerId, targetStage);
    setDraggedCustomerId(null);
  }, [onStageChange]);

  const customersByStage = stageOrder.reduce((acc, stage) => {
    acc[stage] = localCustomers.filter(c => c.stage === stage);
    return acc;
  }, {} as Record<CustomerStage, KanbanCustomer[]>);

  return (
    <div className="flex gap-3 h-[calc(100vh-280px)] overflow-x-auto pb-4">
      {stageOrder.map((stage) => (
        <KanbanColumn
          key={stage}
          stage={stage}
          customers={customersByStage[stage]}
          onCustomerClick={onCustomerClick}
          onDrop={handleDrop}
          draggedCustomerId={draggedCustomerId}
          onDragStart={setDraggedCustomerId}
          onDragEnd={() => setDraggedCustomerId(null)}
        />
      ))}
    </div>
  );
}