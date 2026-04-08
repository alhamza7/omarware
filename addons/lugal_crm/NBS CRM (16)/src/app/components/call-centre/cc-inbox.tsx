import { useState } from "react";
import { motion } from "motion/react";
import {
  Search,
  MessageCircle,
  Mail,
  Crown,
  Send,
  User,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { inboxMessages, type InboxMessage } from "./cc-data";

const channelConfig: Record<InboxMessage["channel"], { label: string; color: string; bg: string; icon: string }> = {
  whatsapp: { label: "واتساب", color: "text-emerald-500", bg: "bg-emerald-500/10", icon: "💬" },
  email: { label: "البريد", color: "text-blue-500", bg: "bg-blue-500/10", icon: "📧" },
  instagram: { label: "انستقرام", color: "text-pink-500", bg: "bg-pink-500/10", icon: "📸" },
  x: { label: "X", color: "text-foreground", bg: "bg-secondary", icon: "𝕏" },
  "live-chat": { label: "الدردشة", color: "text-purple-500", bg: "bg-purple-500/10", icon: "💭" },
};

export function CCInbox() {
  const [search, setSearch] = useState("");
  const [channelFilter, setChannelFilter] = useState<"all" | InboxMessage["channel"]>("all");
  const [selectedMsg, setSelectedMsg] = useState<InboxMessage | null>(null);
  const [replyText, setReplyText] = useState("");

  const filtered = inboxMessages.filter((m) => {
    const matchSearch =
      m.customerName.includes(search) || m.lastMessage.includes(search);
    const matchChannel = channelFilter === "all" || m.channel === channelFilter;
    return matchSearch && matchChannel;
  });

  const unreadTotal = inboxMessages.reduce((s, m) => s + m.unreadCount, 0);

  return (
    <div className="space-y-6">
      {/* Channel Summary */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
        {[
          { key: "all" as const, label: "الكل", count: inboxMessages.length, icon: "📥" },
          ...Object.entries(channelConfig).map(([key, conf]) => ({
            key: key as InboxMessage["channel"],
            label: conf.label,
            count: inboxMessages.filter((m) => m.channel === key).length,
            icon: conf.icon,
          })),
        ].map((ch, i) => (
          <motion.div
            key={ch.key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.03 }}
          >
            <Card
              className={`cursor-pointer transition-all border-border/50 hover:shadow-sm ${
                channelFilter === ch.key ? "border-primary/40 bg-primary/5" : ""
              }`}
              onClick={() => setChannelFilter(ch.key)}
            >
              <CardContent className="p-3 text-center">
                <p className="text-lg mb-0.5">{ch.icon}</p>
                <p className="text-[10px] text-muted-foreground">{ch.label}</p>
                <p className="text-sm text-foreground">{ch.count}</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute end-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="بحث في الرسائل..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pe-9 bg-secondary/30 border-border/50"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Messages List */}
        <div className={`${selectedMsg ? "lg:col-span-1" : "lg:col-span-3"} space-y-2`}>
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm text-muted-foreground">
              الرسائل ({filtered.length})
              {unreadTotal > 0 && (
                <Badge className="ms-2 bg-red-500/10 text-red-500 border-red-500/20 text-[10px]">
                  {unreadTotal} جديدة
                </Badge>
              )}
            </h4>
          </div>

          {filtered.map((msg, i) => {
            const channel = channelConfig[msg.channel];
            const isSelected = selectedMsg?.id === msg.id;

            return (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
              >
                <Card
                  className={`cursor-pointer transition-all ${
                    isSelected
                      ? "border-primary/40 bg-primary/5"
                      : msg.unread
                      ? "border-primary/20 bg-primary/[0.02]"
                      : "border-border/50"
                  } hover:shadow-sm`}
                  onClick={() => setSelectedMsg(msg)}
                >
                  <CardContent className="p-3">
                    <div className="flex items-start gap-3">
                      <div className="relative shrink-0">
                        <Avatar className="h-9 w-9 border border-border/50">
                          <AvatarFallback className="bg-secondary text-foreground text-xs">
                            {msg.customerName.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                          </AvatarFallback>
                        </Avatar>
                        <span className={`absolute -bottom-0.5 -start-0.5 text-[10px] w-4 h-4 rounded-full ${channel.bg} flex items-center justify-center`}>
                          {channel.icon}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <p className={`text-sm truncate ${msg.unread ? "text-foreground" : "text-muted-foreground"}`}>
                            {msg.customerName}
                          </p>
                          {msg.vip && (
                            <Crown className="w-3 h-3 text-primary shrink-0" />
                          )}
                          {msg.unreadCount > 0 && (
                            <span className="w-4.5 h-4.5 rounded-full bg-primary text-primary-foreground text-[10px] flex items-center justify-center shrink-0">
                              {msg.unreadCount}
                            </span>
                          )}
                        </div>
                        <p className={`text-xs truncate ${msg.unread ? "text-foreground/80" : "text-muted-foreground"}`}>
                          {msg.lastMessage}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge className={`text-[8px] border-transparent ${channel.bg} ${channel.color}`}>
                            {channel.label}
                          </Badge>
                          <span className="text-[10px] text-muted-foreground">{msg.time}</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>

        {/* Conversation Panel */}
        {selectedMsg && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-2"
          >
            <Card className="border-border/50 h-full flex flex-col">
              {/* Header */}
              <div className="p-4 border-b border-border/50 flex items-center gap-3">
                <Avatar className="h-10 w-10 border border-border/50">
                  <AvatarFallback className="bg-secondary text-foreground text-sm">
                    {selectedMsg.customerName.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm text-foreground">{selectedMsg.customerName}</h4>
                    {selectedMsg.vip && (
                      <Badge className="bg-primary/10 text-primary border-primary/20 text-[10px] gap-0.5">
                        <Crown className="w-2.5 h-2.5" />
                        VIP
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={`text-[10px] border-transparent ${channelConfig[selectedMsg.channel].bg} ${channelConfig[selectedMsg.channel].color}`}>
                      {channelConfig[selectedMsg.channel].label}
                    </Badge>
                    <span className="text-[10px] text-muted-foreground">{selectedMsg.customerId}</span>
                    {selectedMsg.assignee && (
                      <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                        <User className="w-2.5 h-2.5" />
                        {selectedMsg.assignee}
                      </span>
                    )}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-xs text-muted-foreground"
                  onClick={() => setSelectedMsg(null)}
                >
                  إغلاق
                </Button>
              </div>

              {/* Messages Area */}
              <div className="flex-1 p-4 space-y-4 min-h-[200px] max-h-[400px] overflow-y-auto">
                {/* Customer message */}
                <div className="flex gap-3">
                  <Avatar className="h-7 w-7 border border-border/50 shrink-0">
                    <AvatarFallback className="bg-secondary text-foreground text-[10px]">
                      {selectedMsg.customerName.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="bg-secondary/50 rounded-2xl rounded-ss-sm p-3 max-w-md">
                      <p className="text-sm text-foreground">{selectedMsg.lastMessage}</p>
                    </div>
                    <p className="text-[10px] text-muted-foreground mt-1 ps-1">{selectedMsg.time}</p>
                  </div>
                </div>

                {/* Demo placeholder */}
                <div className="text-center text-xs text-muted-foreground py-4">
                  سيتم عرض المحادثة الكاملة عند الربط بقاعدة البيانات
                </div>
              </div>

              {/* Reply Input */}
              <div className="p-3 border-t border-border/50">
                <div className="flex items-center gap-2">
                  <Input
                    placeholder="اكتب ردك هنا..."
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    className="flex-1 bg-secondary/30"
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && replyText.trim()) {
                        setReplyText("");
                      }
                    }}
                  />
                  <Button
                    size="icon"
                    className="shrink-0"
                    onClick={() => { if (replyText.trim()) setReplyText(""); }}
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </Card>
          </motion.div>
        )}
      </div>
    </div>
  );
}