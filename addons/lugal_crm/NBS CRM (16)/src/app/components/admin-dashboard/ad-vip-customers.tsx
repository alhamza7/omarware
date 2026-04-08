import { motion } from "motion/react";
import {
  Crown, Star, Phone, MessageSquare, Mail, Instagram, Hash, MessagesSquare,
  AlertCircle, ShoppingBag, Calendar,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { vipCustomers, fmt, channelLabels, type ChannelType } from "./ad-data";

const channelIcons: Record<ChannelType, typeof Phone> = {
  phone: Phone, whatsapp: MessageSquare, email: Mail,
  instagram: Instagram, x: Hash, "live-chat": MessagesSquare,
};

const segmentColors: Record<string, string> = {
  "بلاتيني": "bg-primary/15 text-primary border-primary/30",
  "ذهبي": "bg-yellow-500/15 text-yellow-600 dark:text-yellow-400 border-yellow-500/30",
  "فضي": "bg-zinc-400/15 text-zinc-500 border-zinc-400/30",
};

export function ADVipCustomers() {
  const totalSpent = vipCustomers.reduce((s, c) => s + c.totalSpent, 0);
  const avgSatisfaction = (vipCustomers.reduce((s, c) => s + c.satisfaction, 0) / vipCustomers.length).toFixed(1);
  const openIssues = vipCustomers.reduce((s, c) => s + c.openIssues, 0);

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "عملاء VIP", value: vipCustomers.length, icon: Crown, color: "text-primary" },
          { label: "إجمالي الإنفاق", value: `${fmt(totalSpent)} ر.س`, icon: ShoppingBag, color: "text-emerald-500" },
          { label: "متوسط الرضا", value: avgSatisfaction, icon: Star, color: "text-yellow-500" },
          { label: "مشاكل مفتوحة", value: openIssues, icon: AlertCircle, color: openIssues > 0 ? "text-red-500" : "text-emerald-500" },
        ].map((kpi, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
            <Card className="border-border/40">
              <CardContent className="p-3 flex items-center gap-3">
                <div className={`w-9 h-9 rounded-lg bg-primary/5 flex items-center justify-center shrink-0 ${kpi.color}`}>
                  <kpi.icon className="w-4 h-4" />
                </div>
                <div>
                  <p className="text-[10px] text-muted-foreground">{kpi.label}</p>
                  <p className={`text-lg ${kpi.color}`}>{kpi.value}</p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* VIP Cards */}
      <div className="grid grid-cols-3 gap-3">
        {vipCustomers.map((customer, i) => {
          const ChIcon = channelIcons[customer.preferredChannel];
          const chInfo = channelLabels[customer.preferredChannel];
          const segClass = segmentColors[customer.segment] || segmentColors["فضي"];

          return (
            <motion.div
              key={customer.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
            >
              <Card className="border-border/40 hover:border-primary/30 transition-all cursor-pointer group">
                <CardContent className="p-4 space-y-3">
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <Avatar className="w-11 h-11 border-2 border-primary/20">
                          <AvatarFallback className="bg-primary/10 text-primary text-sm">{customer.avatar}</AvatarFallback>
                        </Avatar>
                        <Crown className="absolute -top-1.5 -end-1.5 w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <p className="text-sm text-foreground group-hover:text-primary transition-colors">{customer.name}</p>
                        <Badge className={`text-[9px] mt-0.5 ${segClass}`}>{customer.segment}</Badge>
                      </div>
                    </div>
                    {customer.openIssues > 0 && (
                      <Badge className="bg-red-500/10 text-red-500 text-[9px] border-transparent">
                        <AlertCircle className="w-2.5 h-2.5 me-0.5" />
                        {customer.openIssues} مشكلة
                      </Badge>
                    )}
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-2 rounded-md bg-muted/20">
                      <p className="text-[9px] text-muted-foreground">إجمالي الإنفاق</p>
                      <p className="text-xs text-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>{fmt(customer.totalSpent)} ر.س</p>
                    </div>
                    <div className="p-2 rounded-md bg-muted/20">
                      <p className="text-[9px] text-muted-foreground">الرضا</p>
                      <div className="flex items-center gap-1">
                        <Star className="w-3 h-3 fill-yellow-500 text-yellow-500" />
                        <span className="text-xs text-foreground">{customer.satisfaction}</span>
                      </div>
                    </div>
                  </div>

                  {/* Details */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-muted-foreground">آخر طلب</span>
                      <span className="text-foreground flex items-center gap-1">
                        <Calendar className="w-2.5 h-2.5" />
                        {customer.lastOrder}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-muted-foreground">آخر تواصل</span>
                      <span className={`${customer.lastContact === "اليوم" ? "text-emerald-500" : customer.lastContact.includes("أسبوع") ? "text-red-500" : "text-foreground"}`}>
                        {customer.lastContact}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-muted-foreground">القناة المفضلة</span>
                      <span className={`flex items-center gap-1 ${chInfo.color}`}>
                        <ChIcon className="w-3 h-3" />
                        {chInfo.label}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-muted-foreground">الوكيل المسؤول</span>
                      <span className="text-foreground">{customer.assignedAgent}</span>
                    </div>
                  </div>

                  {/* Tags */}
                  <div className="flex items-center gap-1 flex-wrap">
                    {customer.tags.map((tag) => (
                      <Badge key={tag} variant="outline" className="text-[8px] h-4 px-1.5">{tag}</Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
