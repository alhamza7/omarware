import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Mail, Phone, MapPin, ShoppingBag, Calendar, Crown, Link2, ShieldCheck } from "lucide-react";
import { motion } from "motion/react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./ui/tooltip";

// ─── Channel config for identity icons ───
import { getChannelIcon } from "./analytics/channel-icons";

const channelMini: Record<string, { label: string; icon: React.ReactNode; color: string; bg: string }> = {
  whatsapp: { label: "واتساب", icon: getChannelIcon("whatsapp", "w-3 h-3"), color: "text-green-600 dark:text-green-400", bg: "bg-green-100 dark:bg-green-500/15" },
  instagram: { label: "إنستغرام", icon: getChannelIcon("instagram", "w-3 h-3"), color: "text-pink-600 dark:text-pink-400", bg: "bg-pink-100 dark:bg-pink-500/15" },
  x: { label: "X", icon: getChannelIcon("x", "w-3 h-3"), color: "text-slate-700 dark:text-slate-300", bg: "bg-slate-100 dark:bg-slate-500/15" },
  snapchat: { label: "سناب شات", icon: getChannelIcon("snapchat", "w-3 h-3"), color: "text-yellow-600 dark:text-yellow-400", bg: "bg-yellow-100 dark:bg-yellow-500/15" },
  tiktok: { label: "تيك توك", icon: getChannelIcon("tiktok", "w-3 h-3"), color: "text-slate-800 dark:text-slate-200", bg: "bg-slate-100 dark:bg-slate-500/15" },
  telegram: { label: "تيليجرام", icon: getChannelIcon("telegram", "w-3 h-3"), color: "text-blue-600 dark:text-blue-400", bg: "bg-blue-100 dark:bg-blue-500/15" },
  website: { label: "الموقع", icon: getChannelIcon("website", "w-3 h-3"), color: "text-cyan-600 dark:text-primary", bg: "bg-cyan-100 dark:bg-primary/15" },
  email: { label: "البريد", icon: getChannelIcon("email", "w-3 h-3"), color: "text-red-600 dark:text-red-400", bg: "bg-red-100 dark:bg-red-500/15" },
  store: { label: "المتجر", icon: getChannelIcon("store", "w-3 h-3"), color: "text-purple-600 dark:text-purple-400", bg: "bg-purple-100 dark:bg-purple-500/15" },
};

interface ChannelIdentityMini {
  channel: string;
  handle: string;
  verified: boolean;
}

interface CustomerCardProps {
  customer: {
    id: string;
    name: string;
    email: string;
    phone: string;
    address: string;
    totalPurchases: number;
    joinDate: string;
    vipStatus: boolean;
    favoriteFragrance?: string;
    channelIdentities?: ChannelIdentityMini[];
  };
}

export function CustomerCard({ customer }: CustomerCardProps) {
  // Default channel identities if not provided
  const channels: ChannelIdentityMini[] = customer.channelIdentities || [
    { channel: "whatsapp", handle: customer.phone, verified: true },
    { channel: "instagram", handle: "@noor_client", verified: true },
    { channel: "x", handle: "@client_x", verified: false },
    { channel: "snapchat", handle: "client.snap", verified: false },
    { channel: "tiktok", handle: "@client_tt", verified: true },
    { channel: "email", handle: customer.email, verified: true },
    { channel: "store", handle: "فرع الرياض", verified: true },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ y: -8, scale: 1.02 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="relative overflow-hidden group hover:shadow-2xl hover:shadow-primary/10 transition-all duration-300 hover:border-primary/40">
        {/* Decorative gradient overlay */}
        <motion.div 
          className="absolute top-0 end-0 w-32 h-32 bg-gradient-to-br from-primary/10 to-transparent rounded-full blur-3xl"
          animate={{
            scale: [1, 1.3, 1],
            rotate: [0, 90, 0],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
        
        <CardHeader className="relative">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="flex items-center gap-2">
                {customer.name}
                {customer.vipStatus && (
                  <Crown className="w-5 h-5 text-primary animate-pulse" />
                )}
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">رقم العميل: {customer.id}</p>
            </div>
            {customer.vipStatus && (
              <div className="px-3 py-1 rounded-full bg-primary/20 border border-primary/40">
                <span className="text-xs text-primary">عميل VIP</span>
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-4 relative">
          {/* Contact Information */}
          <div className="space-y-3">
            <div className="flex items-center gap-3 text-sm group/item">
              <div className="p-2 rounded-lg bg-secondary group-hover/item:bg-primary/20 transition-colors">
                <Mail className="w-4 h-4 text-primary" />
              </div>
              <span className="text-foreground/80">{customer.email}</span>
            </div>

            <div className="flex items-center gap-3 text-sm group/item">
              <div className="p-2 rounded-lg bg-secondary group-hover/item:bg-primary/20 transition-colors">
                <Phone className="w-4 h-4 text-primary" />
              </div>
              <span className="text-foreground/80" dir="ltr">{customer.phone}</span>
            </div>

            <div className="flex items-center gap-3 text-sm group/item">
              <div className="p-2 rounded-lg bg-secondary group-hover/item:bg-primary/20 transition-colors">
                <MapPin className="w-4 h-4 text-primary" />
              </div>
              <span className="text-foreground/80">{customer.address}</span>
            </div>
          </div>

          {/* Divider */}
          <div className="h-px bg-gradient-to-r from-transparent via-border to-transparent" />

          {/* Identity Resolution - Channel Icons */}
          <div>
            <div className="flex items-center gap-1.5 mb-2.5">
              <Link2 className="w-3.5 h-3.5 text-primary" />
              <span className="text-[11px] text-muted-foreground font-medium">هوية القنوات</span>
              <span className="text-[9px] bg-primary/10 text-primary px-1.5 py-0.5 rounded-full border border-primary/20 ms-auto">
                {channels.filter(c => c.verified).length}/{channels.length}
              </span>
            </div>
            <TooltipProvider delayDuration={200}>
              <div className="flex flex-wrap gap-1.5">
                {channels.map((ch, i) => {
                  const cfg = channelMini[ch.channel];
                  if (!cfg) return null;
                  return (
                    <Tooltip key={i}>
                      <TooltipTrigger asChild>
                        <div className={`relative p-1.5 rounded-lg border border-border/50 ${cfg.bg} cursor-default transition-all hover:scale-110 hover:shadow-sm`}>
                          <span className={cfg.color}>{cfg.icon}</span>
                          {ch.verified && (
                            <div className="absolute -top-0.5 -end-0.5 w-2.5 h-2.5 bg-cyan-500 dark:bg-primary rounded-full border border-card flex items-center justify-center">
                              <ShieldCheck className="w-1.5 h-1.5 text-white" />
                            </div>
                          )}
                        </div>
                      </TooltipTrigger>
                      <TooltipContent side="top" className="text-[10px] max-w-[200px]">
                        <div className="text-center">
                          <p className="font-medium">{cfg.label}</p>
                          <p className="text-muted-foreground truncate" dir={ch.channel === "whatsapp" ? "ltr" : undefined}>{ch.handle}</p>
                          {ch.verified && <p className="text-primary text-[9px]">موثّق</p>}
                        </div>
                      </TooltipContent>
                    </Tooltip>
                  );
                })}
              </div>
            </TooltipProvider>
          </div>

          {/* Divider */}
          <div className="h-px bg-gradient-to-r from-transparent via-border to-transparent" />

          {/* Purchase Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3 rounded-lg bg-secondary/50 border border-border">
              <div className="flex items-center gap-2 mb-1">
                <ShoppingBag className="w-4 h-4 text-primary" />
                <span className="text-xs text-muted-foreground">إجمالي المشتريات</span>
              </div>
              <p className="font-semibold text-primary">{customer.totalPurchases} ريال</p>
            </div>

            <div className="p-3 rounded-lg bg-secondary/50 border border-border">
              <div className="flex items-center gap-2 mb-1">
                <Calendar className="w-4 h-4 text-primary" />
                <span className="text-xs text-muted-foreground">تاريخ الانضمام</span>
              </div>
              <p className="font-semibold">{customer.joinDate}</p>
            </div>
          </div>

          {/* Favorite Fragrance */}
          {customer.favoriteFragrance && (
            <div className="p-4 rounded-lg bg-gradient-to-br from-primary/5 to-accent/5 border border-primary/20">
              <p className="text-xs text-muted-foreground mb-1">العطر المفضل</p>
              <p className="font-semibold text-primary">{customer.favoriteFragrance}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}