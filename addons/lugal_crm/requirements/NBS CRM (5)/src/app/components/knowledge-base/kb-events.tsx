import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  CalendarDays,
  Clock,
  MapPin,
  Users,
  Bell,
  Send,
  Briefcase,
  PartyPopper,
  GraduationCap,
  ClipboardList,
  X,
  CheckCircle2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { events, type Event } from "./kb-data";

const typeConfig: Record<Event["type"], { label: string; icon: typeof CalendarDays; color: string; bg: string }> = {
  workshop: { label: "ورشة عمل", icon: Briefcase, color: "text-blue-500", bg: "bg-blue-500/10" },
  meeting: { label: "اجتماع", icon: Users, color: "text-emerald-500", bg: "bg-emerald-500/10" },
  celebration: { label: "احتفال", icon: PartyPopper, color: "text-pink-500", bg: "bg-pink-500/10" },
  training: { label: "تدريب", icon: GraduationCap, color: "text-cyan-500", bg: "bg-cyan-500/10" },
  survey: { label: "استبيان", icon: ClipboardList, color: "text-purple-500", bg: "bg-purple-500/10" },
};

const statusConfig: Record<Event["status"], { label: string; color: string }> = {
  upcoming: { label: "قادم", color: "bg-blue-500/10 text-blue-500 border-blue-500/20" },
  ongoing: { label: "جاري", color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" },
  completed: { label: "مكتمل", color: "bg-muted text-muted-foreground border-border" },
};

export function KBEvents() {
  const [showNotifyPanel, setShowNotifyPanel] = useState(false);
  const [notifyTitle, setNotifyTitle] = useState("");
  const [notifyMessage, setNotifyMessage] = useState("");
  const [notifySent, setNotifySent] = useState(false);
  const [filter, setFilter] = useState<"all" | Event["status"]>("all");

  const filtered = filter === "all" ? events : events.filter((e) => e.status === filter);

  const handleSendNotification = () => {
    if (!notifyTitle.trim() || !notifyMessage.trim()) return;
    setNotifySent(true);
    setTimeout(() => {
      setNotifySent(false);
      setShowNotifyPanel(false);
      setNotifyTitle("");
      setNotifyMessage("");
    }, 2000);
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-2 flex-wrap">
          {[
            { key: "all" as const, label: "الكل" },
            { key: "ongoing" as const, label: "جاري" },
            { key: "upcoming" as const, label: "قادم" },
            { key: "completed" as const, label: "مكتمل" },
          ].map((f) => (
            <Button
              key={f.key}
              variant={filter === f.key ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter(f.key)}
              className="text-xs"
            >
              {f.label}
            </Button>
          ))}
        </div>

        {/* Admin: Push Notification */}
        <Button
          onClick={() => setShowNotifyPanel(true)}
          size="sm"
          className="gap-2"
        >
          <Bell className="w-4 h-4" />
          إرسال إشعار
        </Button>
      </div>

      {/* Notification Panel */}
      <AnimatePresence>
        {showNotifyPanel && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <Card className="border-primary/30 bg-primary/5">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Bell className="w-4 h-4 text-primary" />
                    إرسال إشعار للموظفين
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    onClick={() => setShowNotifyPanel(false)}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {notifySent ? (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex items-center justify-center gap-3 py-6"
                  >
                    <CheckCircle2 className="w-8 h-8 text-emerald-500" />
                    <p className="text-emerald-500">تم إرسال الإشعار بنجاح!</p>
                  </motion.div>
                ) : (
                  <>
                    <Input
                      placeholder="عنوان الإشعار"
                      value={notifyTitle}
                      onChange={(e) => setNotifyTitle(e.target.value)}
                      className="bg-background"
                    />
                    <textarea
                      placeholder="نص الإشعار..."
                      value={notifyMessage}
                      onChange={(e) => setNotifyMessage(e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/30"
                    />
                    <div className="flex items-center gap-3">
                      <Button onClick={handleSendNotification} size="sm" className="gap-2">
                        <Send className="w-3.5 h-3.5" />
                        إرسال
                      </Button>
                      <p className="text-xs text-muted-foreground">
                        سيتم إرسال الإشعار لجميع الموظفين (45 موظف)
                      </p>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Events Timeline */}
      <div className="space-y-4">
        {filtered.map((event, i) => {
          const config = typeConfig[event.type];
          const status = statusConfig[event.status];
          const Icon = config.icon;
          const progress = event.maxAttendees
            ? Math.round((event.attendees / event.maxAttendees) * 100)
            : null;

          return (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
            >
              <Card className={`border-border/50 hover:shadow-md transition-all group ${
                event.status === "completed" ? "opacity-70" : ""
              }`}>
                <CardContent className="p-5">
                  <div className="flex gap-4">
                    {/* Icon */}
                    <div className={`w-12 h-12 rounded-xl ${config.bg} flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform`}>
                      <Icon className={`w-6 h-6 ${config.color}`} />
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <div>
                          <h4 className="text-foreground group-hover:text-primary transition-colors">
                            {event.title}
                          </h4>
                          <p className="text-xs text-muted-foreground mt-1">
                            {event.description}
                          </p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <Badge className={`text-[10px] ${status.color}`}>
                            {status.label}
                          </Badge>
                          <Badge className={`text-[10px] ${config.bg} ${config.color} border-transparent`}>
                            {config.label}
                          </Badge>
                        </div>
                      </div>

                      {/* Meta Info */}
                      <div className="flex items-center gap-4 text-xs text-muted-foreground mt-3 flex-wrap">
                        <span className="flex items-center gap-1.5">
                          <CalendarDays className="w-3.5 h-3.5" />
                          {new Date(event.date).toLocaleDateString("ar-SA", {
                            weekday: "long",
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          })}
                        </span>
                        <span className="flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5" />
                          {event.time}
                        </span>
                        <span className="flex items-center gap-1.5">
                          <MapPin className="w-3.5 h-3.5" />
                          {event.location}
                        </span>
                      </div>

                      {/* Attendance Progress */}
                      {progress !== null && (
                        <div className="mt-3 flex items-center gap-3">
                          <div className="flex-1 h-1.5 rounded-full bg-secondary">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                progress >= 100 ? "bg-red-500" : progress >= 75 ? "bg-primary" : "bg-emerald-500"
                              }`}
                              style={{ width: `${Math.min(progress, 100)}%` }}
                            />
                          </div>
                          <span className="text-[10px] text-muted-foreground whitespace-nowrap">
                            {event.attendees}/{event.maxAttendees} مشارك
                          </span>
                        </div>
                      )}

                      {/* Action */}
                      {event.status !== "completed" && (
                        <div className="mt-3">
                          <Button variant="outline" size="sm" className="text-xs h-7 gap-1.5">
                            {event.type === "survey" ? (
                              <>
                                <ClipboardList className="w-3 h-3" />
                                المشاركة في الاستبيان
                              </>
                            ) : (
                              <>
                                <Users className="w-3 h-3" />
                                تسجيل الحضور
                              </>
                            )}
                          </Button>
                        </div>
                      )}
                    </div>
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
