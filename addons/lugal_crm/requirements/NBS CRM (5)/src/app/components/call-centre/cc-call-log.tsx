import { useState } from "react";
import { motion } from "motion/react";
import {
  Search,
  PhoneIncoming,
  PhoneOutgoing,
  PhoneMissed,
  Voicemail,
  Star,
  Play,
  Clock,
  Filter,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
import { callRecords, type CallRecord } from "./cc-data";

const typeConfig: Record<CallRecord["type"], { label: string; icon: typeof PhoneIncoming; color: string }> = {
  inbound: { label: "وارد", icon: PhoneIncoming, color: "text-emerald-500" },
  outbound: { label: "صادر", icon: PhoneOutgoing, color: "text-blue-500" },
  missed: { label: "فائت", icon: PhoneMissed, color: "text-red-500" },
};

const statusConfig: Record<CallRecord["status"], { label: string; color: string }> = {
  completed: { label: "مكتمل", color: "bg-emerald-500/10 text-emerald-500" },
  missed: { label: "فائت", color: "bg-red-500/10 text-red-500" },
  voicemail: { label: "بريد صوتي", color: "bg-purple-500/10 text-purple-500" },
};

export function CCCallLog() {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<"all" | CallRecord["type"]>("all");

  const filtered = callRecords.filter((r) => {
    const matchSearch =
      r.customerName.includes(search) || r.topic.includes(search) || r.agentName.includes(search);
    const matchType = typeFilter === "all" || r.type === typeFilter;
    return matchSearch && matchType;
  });

  const totalCalls = callRecords.length;
  const completedCalls = callRecords.filter((r) => r.status === "completed").length;
  const missedCalls = callRecords.filter((r) => r.status === "missed").length;
  const avgSatisfaction = (
    callRecords.filter((r) => r.satisfaction).reduce((s, r) => s + (r.satisfaction || 0), 0) /
    callRecords.filter((r) => r.satisfaction).length
  ).toFixed(1);

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "إجمالي المكالمات", value: totalCalls.toString(), color: "text-foreground" },
          { label: "مكتملة", value: completedCalls.toString(), color: "text-emerald-500" },
          { label: "فائتة", value: missedCalls.toString(), color: "text-red-500" },
          { label: "متوسط التقييم", value: `${avgSatisfaction}/5`, color: "text-primary" },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <Card className="border-border/50">
              <CardContent className="p-4 text-center">
                <p className={`text-2xl ${stat.color}`}>{stat.value}</p>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="بحث بالعميل أو الموضوع أو الوكيل..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pr-9 bg-secondary/30 border-border/50"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {[
            { key: "all" as const, label: "الكل" },
            { key: "inbound" as const, label: "واردة" },
            { key: "outbound" as const, label: "صادرة" },
            { key: "missed" as const, label: "فائتة" },
          ].map((f) => (
            <Button
              key={f.key}
              variant={typeFilter === f.key ? "default" : "outline"}
              size="sm"
              onClick={() => setTypeFilter(f.key)}
              className="text-xs"
            >
              {f.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Call Log Table */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="border-border/50 overflow-hidden">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader className="bg-muted/30">
                <TableRow className="hover:bg-transparent border-border/40">
                  <TableHead className="text-right w-[50px]">النوع</TableHead>
                  <TableHead className="text-right">العميل</TableHead>
                  <TableHead className="text-right hidden md:table-cell">الوكيل</TableHead>
                  <TableHead className="text-right hidden md:table-cell">الموضوع</TableHead>
                  <TableHead className="text-right hidden lg:table-cell">التاريخ</TableHead>
                  <TableHead className="text-right">المدة</TableHead>
                  <TableHead className="text-right hidden lg:table-cell">التقييم</TableHead>
                  <TableHead className="text-center w-[50px]">الحالة</TableHead>
                  <TableHead className="text-center w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((record) => {
                  const type = typeConfig[record.type];
                  const status = statusConfig[record.status];
                  const TypeIcon = type.icon;

                  return (
                    <TableRow
                      key={record.id}
                      className="hover:bg-primary/5 border-border/40 transition-colors group cursor-pointer"
                    >
                      <TableCell>
                        <div className={`w-8 h-8 rounded-lg ${type.color === "text-emerald-500" ? "bg-emerald-500/10" : type.color === "text-blue-500" ? "bg-blue-500/10" : "bg-red-500/10"} flex items-center justify-center`}>
                          <TypeIcon className={`w-4 h-4 ${type.color}`} />
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="text-sm text-foreground group-hover:text-primary transition-colors">
                            {record.customerName}
                          </p>
                          <p className="text-[10px] text-muted-foreground">{record.customerId}</p>
                        </div>
                      </TableCell>
                      <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                        {record.agentName}
                      </TableCell>
                      <TableCell className="hidden md:table-cell text-sm text-muted-foreground max-w-[200px] truncate">
                        {record.topic}
                      </TableCell>
                      <TableCell className="hidden lg:table-cell">
                        <div className="text-xs text-muted-foreground">
                          <p>{new Date(record.date).toLocaleDateString("ar-SA")}</p>
                          <p dir="ltr" className="text-left">{record.time}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className={`text-sm font-mono tabular-nums ${
                          record.status === "missed" ? "text-red-500" : "text-foreground"
                        }`} dir="ltr">
                          {record.duration === "0:00" ? "—" : record.duration}
                        </span>
                      </TableCell>
                      <TableCell className="hidden lg:table-cell">
                        {record.satisfaction ? (
                          <div className="flex items-center gap-1">
                            {Array.from({ length: 5 }).map((_, idx) => (
                              <Star
                                key={idx}
                                className={`w-3 h-3 ${
                                  idx < record.satisfaction!
                                    ? "text-primary fill-primary"
                                    : "text-muted-foreground/30"
                                }`}
                              />
                            ))}
                          </div>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge className={`text-[10px] border-transparent ${status.color}`}>
                          {status.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        {record.hasRecording && (
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-7 w-7 text-muted-foreground hover:text-primary opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <Play className="w-3.5 h-3.5" />
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </Card>
      </motion.div>
    </div>
  );
}
