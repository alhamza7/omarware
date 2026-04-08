import { useState, useEffect } from "react";
import { motion } from "motion/react";
import {
  Phone,
  PhoneIncoming,
  PhoneOutgoing,
  PhoneOff,
  Clock,
  Crown,
  Users,
  Coffee,
  Wifi,
  WifiOff,
  Headset,
  AlertTriangle,
  Zap,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { agents, liveCalls, callQueue, sampleCallCustomer } from "./cc-data";
import { CCCallPopup } from "./cc-call-popup";
import { CCActiveCall } from "./cc-active-call";

const statusConfig = {
  available: { label: "متاح", color: "bg-emerald-500", textColor: "text-emerald-500", icon: Wifi },
  busy: { label: "مشغول", color: "bg-red-500", textColor: "text-red-500", icon: Phone },
  break: { label: "استراحة", color: "bg-primary", textColor: "text-primary", icon: Coffee },
  offline: { label: "غير متصل", color: "bg-muted-foreground", textColor: "text-muted-foreground", icon: WifiOff },
};

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function CCLiveDashboard() {
  const [callTimers, setCallTimers] = useState<Record<string, number>>({});
  const [showPopup, setShowPopup] = useState(false);
  const [showActiveCall, setShowActiveCall] = useState(false);
  const [simCallType, setSimCallType] = useState<"inbound" | "outbound">("inbound");

  // Initialize timers from live calls
  useEffect(() => {
    const initial: Record<string, number> = {};
    liveCalls.forEach((c) => { initial[c.id] = c.duration; });
    setCallTimers(initial);
  }, []);

  // Tick timers every second
  useEffect(() => {
    const interval = setInterval(() => {
      setCallTimers((prev) => {
        const next = { ...prev };
        Object.keys(next).forEach((k) => { next[k] += 1; });
        return next;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const available = agents.filter((a) => a.status === "available").length;
  const busy = agents.filter((a) => a.status === "busy").length;
  const onBreak = agents.filter((a) => a.status === "break").length;
  const offline = agents.filter((a) => a.status === "offline").length;

  const simulateCall = (type: "inbound" | "outbound") => {
    setSimCallType(type);
    setShowPopup(true);
  };

  const handleAnswer = () => {
    setShowPopup(false);
    setShowActiveCall(true);
  };

  const handleReject = () => {
    setShowPopup(false);
  };

  const handleAssign = () => {
    setShowPopup(false);
    // In real app, would open agent selection
  };

  return (
    <div className="space-y-6">
      {/* Incoming Call Popup */}
      <CCCallPopup
        customer={sampleCallCustomer}
        type={simCallType}
        channel="هاتف"
        visible={showPopup}
        onAnswer={handleAnswer}
        onReject={handleReject}
        onAssign={handleAssign}
      />

      {/* Active Call Dialog */}
      <CCActiveCall
        open={showActiveCall}
        onClose={() => setShowActiveCall(false)}
        customer={sampleCallCustomer}
        callType={simCallType}
        channel="هاتف"
      />

      {/* Simulate Call Buttons */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Card className="border-primary/30 bg-gradient-to-l from-primary/5 via-transparent to-transparent">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
              <Zap className="w-5 h-5 text-primary" />
            </div>
            <div className="flex-1">
              <h4 className="text-sm text-foreground">محاكاة مكالمة</h4>
              <p className="text-[10px] text-muted-foreground">اختبر تجربة المكالمة الكاملة مع بطاقة العميل والملف المالي</p>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                className="gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
                onClick={() => simulateCall("inbound")}
              >
                <PhoneIncoming className="w-3.5 h-3.5" />
                مكالمة واردة
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="gap-1.5 text-xs"
                onClick={() => simulateCall("outbound")}
              >
                <PhoneOutgoing className="w-3.5 h-3.5" />
                مكالمة صادرة
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "مكالمات نشطة", value: liveCalls.length.toString(), icon: Phone, color: "text-red-500", bg: "bg-red-500/10" },
          { label: "في الانتظار", value: callQueue.length.toString(), icon: Clock, color: "text-primary", bg: "bg-primary/10" },
          { label: "وكلاء متاحون", value: `${available}/${agents.length}`, icon: Headset, color: "text-emerald-500", bg: "bg-emerald-500/10" },
          { label: "مكالمات اليوم", value: agents.reduce((s, a) => s + a.callsToday, 0).toString(), icon: PhoneIncoming, color: "text-blue-500", bg: "bg-blue-500/10" },
        ].map((stat, i) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Card className="border-border/50">
                <CardContent className="p-4 flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl ${stat.bg} flex items-center justify-center shrink-0`}>
                    <Icon className={`w-5 h-5 ${stat.color}`} />
                  </div>
                  <div>
                    <p className="text-2xl text-foreground">{stat.value}</p>
                    <p className="text-xs text-muted-foreground">{stat.label}</p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Calls */}
        <div className="lg:col-span-2 space-y-4">
          <h4 className="text-sm text-muted-foreground flex items-center gap-2">
            <Phone className="w-3.5 h-3.5 text-red-500" />
            المكالمات النشطة
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          </h4>

          {liveCalls.length > 0 ? (
            liveCalls.map((call, i) => (
              <motion.div
                key={call.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <Card className="border-red-500/20 bg-red-500/5">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-4">
                      {/* Pulsing phone icon */}
                      <div className="relative shrink-0">
                        <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center">
                          {call.type === "inbound" ? (
                            <PhoneIncoming className="w-5 h-5 text-red-500" />
                          ) : (
                            <PhoneOutgoing className="w-5 h-5 text-blue-500" />
                          )}
                        </div>
                        <span className="absolute -top-0.5 -end-0.5 w-3 h-3 rounded-full bg-red-500 animate-ping" />
                        <span className="absolute -top-0.5 -end-0.5 w-3 h-3 rounded-full bg-red-500" />
                      </div>

                      {/* Call Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="text-sm text-foreground truncate">{call.customerName}</h4>
                          {call.vip && (
                            <Badge className="bg-primary/10 text-primary border-primary/20 text-[10px] gap-0.5">
                              <Crown className="w-2.5 h-2.5" />
                              VIP
                            </Badge>
                          )}
                          <Badge variant="outline" className="text-[10px]">
                            {call.type === "inbound" ? "وارد" : "صادر"}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">{call.topic}</p>
                        <p className="text-xs text-muted-foreground mt-1">الوكيل: {call.agentName}</p>
                      </div>

                      {/* Duration Timer */}
                      <div className="text-center shrink-0">
                        <div className="text-lg text-red-500 font-mono tabular-nums" dir="ltr">
                          {formatDuration(callTimers[call.id] || call.duration)}
                        </div>
                        <p className="text-[10px] text-muted-foreground">مدة المكالمة</p>
                      </div>

                      {/* Actions */}
                      <Button variant="outline" size="icon" className="h-9 w-9 border-red-500/30 text-red-500 hover:bg-red-500/10 shrink-0">
                        <PhoneOff className="w-4 h-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))
          ) : (
            <Card className="border-border/50">
              <CardContent className="p-8 text-center text-muted-foreground">
                <Phone className="w-10 h-10 mx-auto mb-2 opacity-30" />
                <p className="text-sm">لا توجد مكالمات نشطة حالياً</p>
              </CardContent>
            </Card>
          )}

          {/* Call Queue */}
          <h4 className="text-sm text-muted-foreground flex items-center gap-2 mt-6">
            <Clock className="w-3.5 h-3.5 text-primary" />
            قائمة الانتظار ({callQueue.length})
          </h4>

          {callQueue.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 + i * 0.05 }}
            >
              <Card className={`border-border/50 ${item.priority === "high" ? "border-s-2 border-s-red-500" : ""}`}>
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                      <Users className="w-4 h-4 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm text-foreground">{item.customerName}</p>
                        {item.vip && (
                          <Badge className="bg-primary/10 text-primary border-primary/20 text-[10px] gap-0.5">
                            <Crown className="w-2.5 h-2.5" />
                            VIP
                          </Badge>
                        )}
                        {item.priority === "high" && (
                          <Badge className="bg-red-500/10 text-red-500 border-red-500/20 text-[10px] gap-0.5">
                            <AlertTriangle className="w-2.5 h-2.5" />
                            عاجل
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground">{item.topic}</p>
                    </div>
                    <div className="text-center shrink-0">
                      <p className="text-sm text-primary font-mono tabular-nums" dir="ltr">
                        {formatDuration(item.waitTime)}
                      </p>
                      <p className="text-[10px] text-muted-foreground">انتظار</p>
                    </div>
                    <Button variant="default" size="sm" className="text-xs gap-1.5 shrink-0">
                      <Phone className="w-3 h-3" />
                      رد
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Agent Status Panel */}
        <div>
          <h4 className="text-sm text-muted-foreground mb-4 flex items-center gap-2">
            <Headset className="w-3.5 h-3.5" />
            حالة الوكلاء
          </h4>

          {/* Mini Summary */}
          <Card className="border-border/50 mb-4">
            <CardContent className="p-3">
              <div className="grid grid-cols-4 gap-2 text-center">
                {[
                  { count: available, label: "متاح", color: "text-emerald-500" },
                  { count: busy, label: "مشغول", color: "text-red-500" },
                  { count: onBreak, label: "استراحة", color: "text-primary" },
                  { count: offline, label: "غير متصل", color: "text-muted-foreground" },
                ].map((s) => (
                  <div key={s.label}>
                    <p className={`text-lg ${s.color}`}>{s.count}</p>
                    <p className="text-[10px] text-muted-foreground">{s.label}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Agent Cards */}
          <div className="space-y-3">
            {agents.map((agent, i) => {
              const config = statusConfig[agent.status];
              const StatusIcon = config.icon;
              return (
                <motion.div
                  key={agent.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card className={`border-border/50 hover:shadow-sm transition-all ${
                    agent.status === "offline" ? "opacity-60" : ""
                  }`}>
                    <CardContent className="p-3">
                      <div className="flex items-center gap-3">
                        <div className="relative shrink-0">
                          <Avatar className="h-9 w-9 border border-border/50">
                            <AvatarFallback className="bg-secondary text-foreground text-xs">
                              {agent.avatar}
                            </AvatarFallback>
                          </Avatar>
                          <span className={`absolute -bottom-0.5 -end-0.5 w-3 h-3 rounded-full ${config.color} border-2 border-card`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-foreground truncate">{agent.name}</p>
                          <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                            <StatusIcon className="w-3 h-3" />
                            <span className={config.textColor}>{config.label}</span>
                            {agent.currentCall && (
                              <span className="truncate">· {agent.currentCall}</span>
                            )}
                          </div>
                        </div>
                        <div className="text-start shrink-0">
                          <p className="text-xs text-foreground">{agent.callsToday}</p>
                          <p className="text-[10px] text-muted-foreground">مكالمة</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}