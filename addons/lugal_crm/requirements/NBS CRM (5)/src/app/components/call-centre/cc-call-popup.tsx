import { motion, AnimatePresence } from "motion/react";
import {
  Phone,
  PhoneOff,
  PhoneIncoming,
  PhoneOutgoing,
  UserPlus,
  Crown,
  MapPin,
  Star,
} from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Avatar, AvatarFallback } from "../ui/avatar";
import type { CallCustomerProfile } from "./cc-data";

interface CallPopupProps {
  customer: CallCustomerProfile;
  type: "inbound" | "outbound";
  channel: string;
  visible: boolean;
  onAnswer: () => void;
  onReject: () => void;
  onAssign: () => void;
}

export function CCCallPopup({
  customer,
  type,
  channel,
  visible,
  onAnswer,
  onReject,
  onAssign,
}: CallPopupProps) {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: -40, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -40, scale: 0.95 }}
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
          className="fixed top-6 left-1/2 -translate-x-1/2 z-[100] w-[420px] max-w-[95vw]"
        >
          {/* Outer glow */}
          <div className="absolute -inset-1 rounded-3xl bg-primary/20 blur-xl animate-pulse" />

          <div className="relative rounded-2xl border border-primary/30 bg-card/95 backdrop-blur-2xl shadow-2xl shadow-primary/20 overflow-hidden">
            {/* Animated top stripe */}
            <div className="h-1 w-full bg-gradient-to-r from-transparent via-primary to-transparent animate-pulse" />

            {/* Content */}
            <div className="p-5">
              {/* Type Badge */}
              <div className="flex items-center justify-between mb-4">
                <Badge
                  className={`gap-1.5 text-xs border-transparent ${
                    type === "inbound"
                      ? "bg-emerald-500/10 text-emerald-500"
                      : "bg-blue-500/10 text-blue-500"
                  }`}
                >
                  {type === "inbound" ? (
                    <PhoneIncoming className="w-3 h-3" />
                  ) : (
                    <PhoneOutgoing className="w-3 h-3" />
                  )}
                  {type === "inbound" ? "مكالمة واردة" : "مكالمة صادرة"}
                </Badge>
                <Badge variant="outline" className="text-[10px] text-muted-foreground">
                  {channel}
                </Badge>
              </div>

              {/* Customer Info */}
              <div className="flex items-center gap-4 mb-5">
                {/* Pulsing avatar */}
                <div className="relative">
                  <div className="absolute inset-0 rounded-full bg-primary/30 animate-ping" />
                  <Avatar className="h-16 w-16 border-2 border-primary/40 relative z-10">
                    <AvatarFallback className="bg-primary/10 text-primary text-xl">
                      {customer.avatar}
                    </AvatarFallback>
                  </Avatar>
                  {customer.vip && (
                    <div className="absolute -top-1 -right-1 z-20 w-6 h-6 rounded-full bg-primary flex items-center justify-center border-2 border-card">
                      <Crown className="w-3 h-3 text-primary-foreground" />
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <h3 className="text-lg text-foreground truncate">{customer.name}</h3>
                  <p className="text-sm text-primary font-mono" dir="ltr">
                    {customer.phone}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    {customer.vip && (
                      <Badge className="bg-primary/10 text-primary border-primary/20 text-[10px] gap-0.5">
                        <Crown className="w-2.5 h-2.5" />
                        VIP
                      </Badge>
                    )}
                    <Badge variant="outline" className="text-[10px]">
                      {customer.segment}
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Quick Info */}
              <div className="grid grid-cols-3 gap-2 mb-5 p-3 rounded-xl bg-secondary/30 border border-border/50">
                <div className="text-center">
                  <p className="text-xs text-muted-foreground">المشتريات</p>
                  <p className="text-sm text-foreground">
                    {customer.finance.totalCollected.toLocaleString()}
                    <span className="text-[10px] text-muted-foreground ms-0.5">ر.س</span>
                  </p>
                </div>
                <div className="text-center border-x border-border/50">
                  <p className="text-xs text-muted-foreground">الرصيد</p>
                  <p className={`text-sm ${customer.finance.currentBalance > 0 ? "text-red-500" : "text-emerald-500"}`}>
                    {customer.finance.currentBalance.toLocaleString()}
                    <span className="text-[10px] ms-0.5">ر.س</span>
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-muted-foreground">آخر طلب</p>
                  <p className="text-sm text-foreground">
                    {new Date(customer.lastOrder.date).toLocaleDateString("ar-SA", { month: "short", day: "numeric" })}
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2">
                {/* Answer */}
                <Button
                  onClick={onAnswer}
                  className="flex-1 h-12 gap-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl shadow-lg shadow-emerald-600/30"
                >
                  <div className="relative">
                    <Phone className="w-5 h-5" />
                    <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-white rounded-full animate-ping" />
                  </div>
                  <span>رد</span>
                </Button>

                {/* Assign */}
                <Button
                  onClick={onAssign}
                  variant="outline"
                  className="h-12 gap-2 rounded-xl border-primary/30 text-primary hover:bg-primary/10"
                >
                  <UserPlus className="w-4 h-4" />
                  <span>تحويل</span>
                </Button>

                {/* Reject */}
                <Button
                  onClick={onReject}
                  variant="outline"
                  className="h-12 gap-2 rounded-xl border-red-500/30 text-red-500 hover:bg-red-500/10"
                >
                  <PhoneOff className="w-4 h-4" />
                  <span>رفض</span>
                </Button>
              </div>
            </div>

            {/* Ripple effect at bottom */}
            <div className="h-0.5 w-full bg-gradient-to-r from-transparent via-primary/50 to-transparent" />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
