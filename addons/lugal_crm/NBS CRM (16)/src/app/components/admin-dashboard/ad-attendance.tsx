import { motion } from "motion/react";
import {
  Monitor, Laptop, Smartphone, Tablet, Clock, MapPin, Globe, Wifi,
  UserCheck, UserX, Building2, Home, LogIn,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Avatar, AvatarFallback } from "../ui/avatar";
import { ScrollArea } from "../ui/scroll-area";
import { attendanceRecords, roleLabels, type AttendanceRecord } from "./ad-data";

const deviceIcons: Record<string, typeof Monitor> = {
  desktop: Monitor, laptop: Laptop, mobile: Smartphone, tablet: Tablet,
};

const statusConfig: Record<string, { color: string; label: string }> = {
  present: { color: "bg-emerald-500/10 text-emerald-500", label: "حاضر" },
  late: { color: "bg-yellow-500/10 text-yellow-500", label: "متأخر" },
  absent: { color: "bg-red-500/10 text-red-500", label: "غائب" },
  remote: { color: "bg-blue-500/10 text-blue-500", label: "عن بعد" },
  "half-day": { color: "bg-violet-500/10 text-violet-500", label: "نصف يوم" },
};

export function ADAttendance() {
  const present = attendanceRecords.filter((r) => ["present", "remote", "late"].includes(r.status));
  const absent = attendanceRecords.filter((r) => r.status === "absent");
  const remote = attendanceRecords.filter((r) => r.isRemote);

  const totalMessages = attendanceRecords.reduce((s, r) => s + r.messagesHandled, 0);
  const totalCalls = attendanceRecords.reduce((s, r) => s + r.callsHandled, 0);

  return (
    <div className="space-y-4">
      {/* KPIs */}
      <div className="grid grid-cols-6 gap-3">
        {[
          { label: "إجمالي الموظفين", value: attendanceRecords.length, icon: UserCheck, color: "text-foreground" },
          { label: "حاضرون", value: present.length, icon: Building2, color: "text-emerald-500" },
          { label: "عن بعد", value: remote.length, icon: Home, color: "text-blue-500" },
          { label: "غائبون", value: absent.length, icon: UserX, color: "text-red-500" },
          { label: "إجمالي الرسائل", value: totalMessages, icon: Globe, color: "text-violet-500" },
          { label: "إجمالي المكالمات", value: totalCalls, icon: LogIn, color: "text-primary" },
        ].map((kpi, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
            <Card className="border-border/40">
              <CardContent className="p-3 flex items-center gap-3">
                <div className={`w-8 h-8 rounded-lg bg-primary/5 flex items-center justify-center shrink-0 ${kpi.color}`}>
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

      {/* Attendance Table */}
      <Card className="border-border/40">
        <ScrollArea className="max-h-[calc(100vh-380px)]" dir="rtl">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border/40 bg-muted/20">
                  <th className="text-start p-3 text-muted-foreground">الموظف</th>
                  <th className="text-center p-3 text-muted-foreground">الحالة</th>
                  <th className="text-center p-3 text-muted-foreground">دخل</th>
                  <th className="text-center p-3 text-muted-foreground">خرج</th>
                  <th className="text-center p-3 text-muted-foreground">ساعات</th>
                  <th className="text-center p-3 text-muted-foreground">نشط</th>
                  <th className="text-center p-3 text-muted-foreground">خامل</th>
                  <th className="text-center p-3 text-muted-foreground">رسائل</th>
                  <th className="text-center p-3 text-muted-foreground">مكالمات</th>
                  <th className="text-center p-3 text-muted-foreground">الجهاز</th>
                  <th className="text-start p-3 text-muted-foreground">IP</th>
                  <th className="text-start p-3 text-muted-foreground">الموقع</th>
                </tr>
              </thead>
              <tbody>
                {attendanceRecords.map((record, i) => (
                  <AttendanceRow key={record.id} record={record} index={i} />
                ))}
              </tbody>
            </table>
          </div>
        </ScrollArea>
      </Card>
    </div>
  );
}

function AttendanceRow({ record, index }: { record: AttendanceRecord; index: number }) {
  const sc = statusConfig[record.status];
  const DeviceIcon = deviceIcons[record.deviceType] || Monitor;

  return (
    <motion.tr
      initial={{ opacity: 0, x: 10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03 }}
      className="border-b border-border/20 hover:bg-muted/10 transition-colors"
    >
      {/* Employee */}
      <td className="p-3">
        <div className="flex items-center gap-2.5">
          <Avatar className="w-7 h-7 border border-border/40">
            <AvatarFallback className="bg-primary/10 text-primary text-[9px]">
              {record.employeeName.slice(0, 2)}
            </AvatarFallback>
          </Avatar>
          <div>
            <p className="text-foreground">{record.employeeName}</p>
            <p className="text-[9px] text-muted-foreground">{roleLabels[record.role]}</p>
          </div>
        </div>
      </td>

      {/* Status */}
      <td className="p-3 text-center">
        <Badge className={`text-[9px] border-transparent ${sc.color}`}>
          {record.isRemote && record.status !== "absent" && <Home className="w-2.5 h-2.5 me-0.5" />}
          {sc.label}
        </Badge>
      </td>

      {/* Login */}
      <td className="p-3 text-center text-foreground">{record.loginTime}</td>

      {/* Logout */}
      <td className="p-3 text-center text-muted-foreground">{record.logoutTime || "—"}</td>

      {/* Hours */}
      <td className="p-3 text-center text-foreground">{record.hoursWorked}</td>

      {/* Active */}
      <td className="p-3 text-center">
        <span className="text-emerald-500">{record.activeTime}</span>
      </td>

      {/* Idle */}
      <td className="p-3 text-center">
        <span className={`${
          record.idleTime > "1:00" ? "text-red-500" : record.idleTime > "0:30" ? "text-yellow-500" : "text-muted-foreground"
        }`}>
          {record.idleTime}
        </span>
      </td>

      {/* Messages */}
      <td className="p-3 text-center text-foreground">{record.messagesHandled}</td>

      {/* Calls */}
      <td className="p-3 text-center text-foreground">{record.callsHandled}</td>

      {/* Device */}
      <td className="p-3 text-center">
        <div className="flex flex-col items-center gap-0.5">
          <DeviceIcon className="w-3.5 h-3.5 text-muted-foreground" />
          <span className="text-[8px] text-muted-foreground">{record.browser}</span>
        </div>
      </td>

      {/* IP */}
      <td className="p-3">
        <span className="text-[10px] text-muted-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>
          {record.ip}
        </span>
      </td>

      {/* Location */}
      <td className="p-3">
        <div className="flex items-center gap-1">
          <MapPin className="w-3 h-3 text-muted-foreground shrink-0" />
          <span className="text-[10px] text-muted-foreground truncate max-w-[120px]">{record.location}</span>
        </div>
      </td>
    </motion.tr>
  );
}
