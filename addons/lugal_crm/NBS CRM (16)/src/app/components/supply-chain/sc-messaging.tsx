import { useState } from "react";
import { motion } from "motion/react";
import {
  Send,
  Mail,
  MessageCircle,
  AtSign,
  Paperclip,
  Circle,
  MailOpen,
  Search,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "../ui/dialog";
import {
  internalMessages,
  scEmails,
  systemUsers,
  type SCEmail,
} from "./sc-data";

type Tab = "chat" | "email";

const channelConfig: Record<string, { label: string; color: string }> = {
  internal: { label: "داخلي", color: "bg-blue-500/15 text-blue-500" },
  whatsapp: { label: "واتساب", color: "bg-emerald-500/15 text-emerald-500" },
  wechat: { label: "ويتشات", color: "bg-emerald-500/15 text-emerald-500" },
  email: { label: "بريد", color: "bg-primary/15 text-primary" },
};

const divisionLabel = (d: string) =>
  d === "europe" ? "أوروبا" : d === "china" ? "الصين" : "بغداد";

export function SCMessaging() {
  const [tab, setTab] = useState<Tab>("chat");
  const [selectedEmail, setSelectedEmail] = useState<SCEmail | null>(null);

  return (
    <div className="space-y-4">
      {/* Tab Toggle */}
      <div className="flex gap-1 p-0.5 rounded-md bg-secondary/40 border border-border/40 w-fit">
        <button
          onClick={() => setTab("chat")}
          className={`px-3 py-1.5 rounded text-xs flex items-center gap-1.5 transition-all ${
            tab === "chat"
              ? "bg-card text-primary shadow-sm border border-primary/20"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <MessageCircle className="w-3.5 h-3.5" />
          المحادثات الداخلية
        </button>
        <button
          onClick={() => setTab("email")}
          className={`px-3 py-1.5 rounded text-xs flex items-center gap-1.5 transition-all ${
            tab === "email"
              ? "bg-card text-primary shadow-sm border border-primary/20"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <Mail className="w-3.5 h-3.5" />
          البريد الإلكتروني
          {scEmails.filter((e) => !e.read).length > 0 && (
            <span className="w-2 h-2 rounded-full bg-red-500" />
          )}
        </button>
      </div>

      {tab === "chat" && (
        <div className="grid grid-cols-3 gap-4">
          {/* Users Sidebar */}
          <Card className="border-border/50">
            <CardContent className="p-3 space-y-2">
              <p className="text-[10px] text-muted-foreground px-1">الفريق</p>
              {systemUsers.map((user) => (
                <div key={user.id} className="flex items-center gap-2.5 p-2 rounded-lg hover:bg-muted/30 transition-colors cursor-pointer">
                  <div className="relative">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-[10px] text-primary">
                      {user.avatar}
                    </div>
                    <Circle className={`absolute -bottom-0.5 -end-0.5 w-3 h-3 ${
                      user.online ? "fill-emerald-500 text-emerald-500" : "fill-muted text-muted"
                    }`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-foreground truncate">{user.name}</p>
                    <p className="text-[9px] text-muted-foreground">{divisionLabel(user.division)} • {user.role}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Chat Messages */}
          <div className="col-span-2">
            <Card className="border-border/50">
              <CardContent className="p-0">
                <ScrollArea className="h-[450px]" dir="rtl">
                  <div className="p-4 space-y-4">
                    {internalMessages.map((msg) => {
                      const chConf = channelConfig[msg.channel];
                      const highlightedText = msg.text.replace(
                        /@[\u0600-\u06FF]+/g,
                        (match) => `<span class="text-primary">${match}</span>`
                      );
                      return (
                        <motion.div
                          key={msg.id}
                          initial={{ opacity: 0, y: 5 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="flex gap-3"
                        >
                          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0 text-[9px] text-primary">
                            {msg.sender.slice(0, 2)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-foreground">{msg.sender}</span>
                              <Badge className={`text-[7px] h-3.5 px-1 border-transparent ${chConf.color}`}>{chConf.label}</Badge>
                              <Badge variant="outline" className="text-[7px] h-3.5 px-1">{divisionLabel(msg.senderDivision)}</Badge>
                              <span className="text-[8px] text-muted-foreground ms-auto">{msg.date}</span>
                            </div>
                            <div
                              className="mt-1.5 p-3 rounded-lg bg-muted/30 text-xs text-foreground rounded-ss-none"
                              dangerouslySetInnerHTML={{ __html: highlightedText }}
                            />
                            {msg.mentions.length > 0 && (
                              <div className="flex items-center gap-1 mt-1">
                                <AtSign className="w-3 h-3 text-primary" />
                                {msg.mentions.map((m) => (
                                  <span key={m} className="text-[8px] text-primary">{m}</span>
                                ))}
                              </div>
                            )}
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </ScrollArea>
                {/* Input */}
                <div className="p-3 border-t border-border/40 flex gap-2 items-end">
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0 shrink-0">
                    <Paperclip className="w-3.5 h-3.5" />
                  </Button>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0 shrink-0">
                    <AtSign className="w-3.5 h-3.5" />
                  </Button>
                  <textarea
                    className="flex-1 h-10 rounded-md border border-input bg-input-background px-3 py-2 text-xs text-foreground resize-none"
                    placeholder="اكتب رسالة... استخدم @ لذكر شخص"
                  />
                  <Button size="sm" className="h-8 px-3 shrink-0">
                    <Send className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {tab === "email" && (
        <div className="space-y-2">
          {/* Email Toolbar */}
          <div className="flex items-center justify-between">
            <div className="relative">
              <Search className="absolute start-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <Input placeholder="بحث في البريد..." className="h-8 text-xs ps-8 w-52" />
            </div>
            <Button size="sm" className="text-xs gap-1.5">
              <Mail className="w-3.5 h-3.5" />
              رسالة جديدة
            </Button>
          </div>

          {/* Email List */}
          {scEmails.map((email, i) => (
            <motion.div
              key={email.id}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
            >
              <Card
                className={`border-border/50 cursor-pointer hover:border-primary/30 transition-all ${
                  !email.read ? "border-s-2 border-s-primary bg-primary/[0.02]" : ""
                }`}
                onClick={() => setSelectedEmail(email)}
              >
                <CardContent className="p-3 flex items-start gap-3">
                  <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                    {email.read ? (
                      <MailOpen className="w-4 h-4 text-muted-foreground" />
                    ) : (
                      <Mail className="w-4 h-4 text-primary" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-foreground truncate" style={{ direction: "ltr", unicodeBidi: "embed" }}>{email.from}</span>
                      <span className="text-[9px] text-muted-foreground shrink-0">{email.date}</span>
                    </div>
                    <p className={`text-xs mt-0.5 truncate ${!email.read ? "text-foreground" : "text-muted-foreground"}`}>{email.subject}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {email.relatedPO && (
                        <Badge variant="outline" className="text-[7px] h-3.5" style={{ direction: "ltr", unicodeBidi: "embed" }}>{email.relatedPO}</Badge>
                      )}
                      {email.relatedContainer && (
                        <Badge variant="outline" className="text-[7px] h-3.5">{email.relatedContainer}</Badge>
                      )}
                      {email.attachments.length > 0 && (
                        <span className="text-[8px] text-muted-foreground flex items-center gap-0.5">
                          <Paperclip className="w-2.5 h-2.5" />
                          {email.attachments.length}
                        </span>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {/* Email Detail Dialog */}
      <Dialog open={!!selectedEmail} onOpenChange={(open) => { if (!open) setSelectedEmail(null); }}>
        <DialogContent className="!max-w-2xl !p-0 !gap-0">
          <DialogTitle className="sr-only">تفاصيل البريد</DialogTitle>
          <DialogDescription className="sr-only">عرض البريد الإلكتروني</DialogDescription>
          {selectedEmail && (
            <div>
              <div className="p-5 border-b border-border/40 bg-gradient-to-l from-primary/5 to-transparent">
                <h3 className="text-sm text-foreground">{selectedEmail.subject}</h3>
                <div className="flex items-center gap-3 mt-2 text-[10px] text-muted-foreground">
                  <span>من: <span className="text-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>{selectedEmail.from}</span></span>
                  <span>إلى: <span className="text-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>{selectedEmail.to}</span></span>
                  <span className="ms-auto">{selectedEmail.date}</span>
                </div>
              </div>
              <div className="p-5">
                <pre className="text-xs text-foreground whitespace-pre-wrap font-[inherit]" style={{ direction: "ltr", unicodeBidi: "plaintext" }}>
                  {selectedEmail.body}
                </pre>
                {selectedEmail.attachments.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-border/30 space-y-1.5">
                    <p className="text-[10px] text-muted-foreground">المرفقات:</p>
                    {selectedEmail.attachments.map((att, i) => (
                      <div key={i} className="flex items-center gap-2 p-2 rounded bg-muted/30 text-xs text-foreground">
                        <Paperclip className="w-3 h-3 text-primary" />
                        <span style={{ direction: "ltr", unicodeBidi: "embed" }}>{att}</span>
                      </div>
                    ))}
                  </div>
                )}
                <div className="mt-4 flex justify-end gap-2">
                  <Button variant="outline" size="sm" className="text-xs gap-1">
                    <Send className="w-3 h-3" />
                    رد
                  </Button>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
