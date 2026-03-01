import { motion } from "motion/react";
import {
  Star,
  Phone,
  Clock,
  CheckCircle2,
  Trophy,
  Medal,
  Award,
  TrendingUp,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { Progress } from "../ui/progress";
import { agents } from "./cc-data";

const statusColors = {
  available: "bg-emerald-500",
  busy: "bg-red-500",
  break: "bg-primary",
  offline: "bg-muted-foreground",
};

const rankIcons = [Trophy, Medal, Award];
const rankColors = ["text-primary", "text-muted-foreground", "text-primary/60"];

export function CCAgentPerformance() {
  // Sort by satisfaction desc, then calls desc
  const sorted = [...agents]
    .filter((a) => a.callsToday > 0 || a.ticketsResolved > 0)
    .sort((a, b) => b.satisfaction - a.satisfaction || b.callsToday - a.callsToday);

  const totalCalls = agents.reduce((s, a) => s + a.callsToday, 0);
  const totalTickets = agents.reduce((s, a) => s + a.ticketsResolved, 0);
  const avgSatisfaction = agents.filter((a) => a.satisfaction > 0).length > 0
    ? (agents.filter((a) => a.satisfaction > 0).reduce((s, a) => s + a.satisfaction, 0) /
       agents.filter((a) => a.satisfaction > 0).length).toFixed(1)
    : "0";

  return (
    <div className="space-y-6">
      {/* Team Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "إجمالي مكالمات اليوم", value: totalCalls.toString(), icon: Phone, color: "text-blue-500", bg: "bg-blue-500/10" },
          { label: "تذاكر تم حلها", value: totalTickets.toString(), icon: CheckCircle2, color: "text-emerald-500", bg: "bg-emerald-500/10" },
          { label: "متوسط الرضا", value: `${avgSatisfaction}/5`, icon: Star, color: "text-primary", bg: "bg-primary/10" },
          { label: "الوكلاء النشطين", value: agents.filter((a) => a.status !== "offline").length.toString(), icon: TrendingUp, color: "text-cyan-500", bg: "bg-cyan-500/10" },
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
        {/* Leaderboard */}
        <div>
          <Card className="border-primary/20">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Trophy className="w-4 h-4 text-primary" />
                ترتيب الوكلاء
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {sorted.map((agent, i) => {
                const RankIcon = i < 3 ? rankIcons[i] : null;
                const rankColor = i < 3 ? rankColors[i] : "";
                return (
                  <motion.div
                    key={agent.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.06 }}
                    className={`flex items-center gap-3 p-3 rounded-lg ${
                      i === 0 ? "bg-primary/10 border border-primary/20" : "bg-secondary/30"
                    }`}
                  >
                    <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0">
                      {RankIcon ? (
                        <RankIcon className={`w-5 h-5 ${rankColor}`} />
                      ) : (
                        <span className="text-xs text-muted-foreground">{i + 1}</span>
                      )}
                    </div>
                    <div className="relative shrink-0">
                      <Avatar className="h-8 w-8 border border-border/50">
                        <AvatarFallback className="bg-secondary text-foreground text-xs">
                          {agent.avatar}
                        </AvatarFallback>
                      </Avatar>
                      <span className={`absolute -bottom-0.5 -end-0.5 w-2.5 h-2.5 rounded-full ${statusColors[agent.status]} border-2 border-card`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-foreground truncate">{agent.name}</p>
                      <div className="flex items-center gap-1 mt-0.5">
                        {Array.from({ length: 5 }).map((_, idx) => (
                          <Star
                            key={idx}
                            className={`w-2.5 h-2.5 ${
                              idx < Math.round(agent.satisfaction)
                                ? "text-primary fill-primary"
                                : "text-muted-foreground/30"
                            }`}
                          />
                        ))}
                        <span className="text-[10px] text-muted-foreground ms-1">{agent.satisfaction}</span>
                      </div>
                    </div>
                    <div className="text-start shrink-0">
                      <p className="text-sm text-foreground">{agent.callsToday}</p>
                      <p className="text-[10px] text-muted-foreground">مكالمة</p>
                    </div>
                  </motion.div>
                );
              })}
            </CardContent>
          </Card>
        </div>

        {/* Detailed Agent Cards */}
        <div className="lg:col-span-2 space-y-4">
          <h4 className="text-sm text-muted-foreground">تفاصيل أداء الوكلاء</h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {agents.map((agent, i) => {
              const maxCalls = Math.max(...agents.map((a) => a.callsToday), 1);
              const callPercent = Math.round((agent.callsToday / maxCalls) * 100);
              const satisfactionPercent = Math.round((agent.satisfaction / 5) * 100);

              return (
                <motion.div
                  key={agent.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.06 }}
                >
                  <Card className={`border-border/50 transition-all hover:shadow-sm ${
                    agent.status === "offline" ? "opacity-60" : ""
                  }`}>
                    <CardContent className="p-4">
                      {/* Header */}
                      <div className="flex items-center gap-3 mb-4">
                        <div className="relative shrink-0">
                          <Avatar className="h-10 w-10 border border-border/50">
                            <AvatarFallback className="bg-secondary text-foreground text-sm">
                              {agent.avatar}
                            </AvatarFallback>
                          </Avatar>
                          <span className={`absolute -bottom-0.5 -end-0.5 w-3 h-3 rounded-full ${statusColors[agent.status]} border-2 border-card`} />
                        </div>
                        <div className="flex-1">
                          <p className="text-sm text-foreground">{agent.name}</p>
                          <p className="text-[10px] text-muted-foreground">الوردية: {agent.shift}</p>
                        </div>
                        <Badge className={`text-[10px] border-transparent ${
                          agent.status === "available" ? "bg-emerald-500/10 text-emerald-500" :
                          agent.status === "busy" ? "bg-red-500/10 text-red-500" :
                          agent.status === "break" ? "bg-primary/10 text-primary" :
                          "bg-muted text-muted-foreground"
                        }`}>
                          {agent.status === "available" ? "متاح" :
                           agent.status === "busy" ? "مشغول" :
                           agent.status === "break" ? "استراحة" : "غير متصل"}
                        </Badge>
                      </div>

                      {/* Stats */}
                      <div className="space-y-3">
                        <div>
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span className="text-muted-foreground flex items-center gap-1.5">
                              <Phone className="w-3 h-3" />
                              المكالمات
                            </span>
                            <span className="text-foreground">{agent.callsToday}</span>
                          </div>
                          <Progress value={callPercent} className="h-1.5" />
                        </div>

                        <div>
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span className="text-muted-foreground flex items-center gap-1.5">
                              <Star className="w-3 h-3" />
                              الرضا
                            </span>
                            <span className="text-foreground">{agent.satisfaction}/5</span>
                          </div>
                          <Progress value={satisfactionPercent} className="h-1.5" />
                        </div>

                        <div className="flex items-center justify-between text-xs pt-1">
                          <span className="text-muted-foreground flex items-center gap-1.5">
                            <Clock className="w-3 h-3" />
                            متوسط المدة
                          </span>
                          <span className="text-foreground font-mono" dir="ltr">{agent.avgDuration}</span>
                        </div>

                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground flex items-center gap-1.5">
                            <CheckCircle2 className="w-3 h-3" />
                            تذاكر محلولة
                          </span>
                          <span className="text-foreground">{agent.ticketsResolved}</span>
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