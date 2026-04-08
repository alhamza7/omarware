import { useState } from "react";
import { motion } from "motion/react";
import {
  Bell,
  Ship,
  ClipboardList,
  PackagePlus,
  Handshake,
  Clock,
  CheckCircle2,
  Circle,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { scNotifications, type SCNotification } from "./sc-data";

const typeConfig: Record<SCNotification["type"], { icon: typeof Bell; color: string; bg: string }> = {
  reminder: { icon: Clock, color: "text-violet-500", bg: "bg-violet-500/10" },
  container: { icon: Ship, color: "text-blue-500", bg: "bg-blue-500/10" },
  po: { icon: ClipboardList, color: "text-primary", bg: "bg-primary/10" },
  request: { icon: PackagePlus, color: "text-emerald-500", bg: "bg-emerald-500/10" },
  negotiation: { icon: Handshake, color: "text-pink-500", bg: "bg-pink-500/10" },
};

export function SCNotifications() {
  const [notifications, setNotifications] = useState(scNotifications);

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const toggleRead = (id: string) => {
    setNotifications((prev) => prev.map((n) => n.id === id ? { ...n, read: !n.read } : n));
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">{unreadCount} غير مقروءة</span>
        </div>
        {unreadCount > 0 && (
          <Button variant="ghost" size="sm" className="text-xs text-primary" onClick={markAllRead}>
            <CheckCircle2 className="w-3.5 h-3.5 me-1" />
            تعليم الكل كمقروء
          </Button>
        )}
      </div>

      {/* Notification List */}
      <div className="space-y-2">
        {notifications.map((notif, i) => {
          const conf = typeConfig[notif.type];
          const Icon = conf.icon;
          return (
            <motion.div
              key={notif.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
            >
              <Card
                className={`border-border/50 transition-all cursor-pointer ${
                  !notif.read ? "border-s-2 border-s-primary bg-primary/[0.02]" : ""
                }`}
                onClick={() => toggleRead(notif.id)}
              >
                <CardContent className="p-3 flex items-start gap-3">
                  <div className={`w-9 h-9 rounded-lg ${conf.bg} flex items-center justify-center shrink-0`}>
                    <Icon className={`w-4 h-4 ${conf.color}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className={`text-sm ${!notif.read ? "text-foreground" : "text-muted-foreground"}`}>{notif.title}</p>
                      {!notif.read && (
                        <Circle className="w-2 h-2 fill-primary text-primary shrink-0" />
                      )}
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-0.5">{notif.description}</p>
                    <p className="text-[9px] text-muted-foreground mt-1">{notif.date}</p>
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
