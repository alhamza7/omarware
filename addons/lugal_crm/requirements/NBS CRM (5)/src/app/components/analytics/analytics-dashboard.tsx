import { useState, useCallback } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../ui/tabs";
import { Button } from "../ui/button";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { ScrollArea } from "../ui/scroll-area";
import {
  Download, FileSpreadsheet, BarChart3, Users, Ticket, Building2,
  Crown, Bot, TrendingUp, MessageCircle, Phone, Clock, Star,
} from "lucide-react";
import { ChannelsTab } from "./channels-tab";
import { EmployeesTab } from "./employees-tab";
import { TicketsTab } from "./tickets-tab";
import { BranchesTab } from "./branches-tab";
import { VipTab } from "./vip-tab";
import { AiHumanTab } from "./ai-human-tab";
import { overviewKPIs } from "./analytics-data";

// ─── Export Utility ──────────────────────────────────────
function exportToCSV(filename: string) {
  // Placeholder: In production, this would generate a real CSV/Excel
  const csvContent = "data:text/csv;charset=utf-8,\uFEFF" +
    "تقرير تحليلات نور النبراس\n" +
    `تاريخ التصدير: ${new Date().toLocaleDateString("ar-SA")}\n\n` +
    "المؤشر,القيمة\n" +
    `إجمالي العملاء,${overviewKPIs.totalCustomers}\n` +
    `إجمالي الإيرادات,${overviewKPIs.totalRevenue}\n` +
    `إجمالي التذاكر,${overviewKPIs.totalTickets}\n` +
    `متوسط الرضا,${overviewKPIs.avgSatisfaction}\n` +
    `إجمالي الرسائل,${overviewKPIs.totalMessages}\n` +
    `إجمالي المكالمات,${overviewKPIs.totalCalls}\n` +
    `متوسط FRT,${overviewKPIs.avgFrt}\n` +
    `متوسط TTR,${overviewKPIs.avgTtr}\n` +
    `عملاء VIP,${overviewKPIs.vipCustomers}\n` +
    `نسبة AI,${overviewKPIs.aiHandledPercent}%\n`;

  const link = document.createElement("a");
  link.setAttribute("href", encodeURI(csvContent));
  link.setAttribute("download", `${filename}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// ─── Overview KPI Grid ───────────────────────────────────
function OverviewKPIs() {
  const kpis = [
    { icon: <Users className="w-5 h-5" />, label: "إجمالي العملاء", value: overviewKPIs.totalCustomers.toLocaleString(), color: "text-blue-500", bg: "bg-blue-500/10" },
    { icon: <MessageCircle className="w-5 h-5" />, label: "إجمالي الرسائل", value: overviewKPIs.totalMessages.toLocaleString(), color: "text-green-500", bg: "bg-green-500/10" },
    { icon: <Phone className="w-5 h-5" />, label: "إجمالي المكالمات", value: overviewKPIs.totalCalls.toLocaleString(), color: "text-purple-500", bg: "bg-purple-500/10" },
    { icon: <Ticket className="w-5 h-5" />, label: "إجمالي التذاكر", value: overviewKPIs.totalTickets.toLocaleString(), color: "text-primary", bg: "bg-primary/10" },
    { icon: <Clock className="w-5 h-5" />, label: "متوسط FRT", value: `${overviewKPIs.avgFrt} دقيقة`, color: "text-cyan-500", bg: "bg-cyan-500/10" },
    { icon: <TrendingUp className="w-5 h-5" />, label: "متوسط TTR", value: `${overviewKPIs.avgTtr} ساعة`, color: "text-rose-500", bg: "bg-rose-500/10" },
    { icon: <Star className="w-5 h-5" />, label: "متوسط الرضا", value: overviewKPIs.avgSatisfaction.toString(), color: "text-primary", bg: "bg-primary/10" },
    { icon: <Crown className="w-5 h-5" />, label: "عملاء VIP", value: overviewKPIs.vipCustomers.toString(), color: "text-primary", bg: "bg-primary/10" },
    { icon: <Bot className="w-5 h-5" />, label: "نسبة AI", value: `${overviewKPIs.aiHandledPercent}%`, color: "text-blue-500", bg: "bg-blue-500/10" },
    { icon: <Building2 className="w-5 h-5" />, label: "الفروع", value: overviewKPIs.branchCount.toString(), color: "text-purple-500", bg: "bg-purple-500/10" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
      {kpis.map((kpi, i) => (
        <Card key={i} className="bg-card/30 backdrop-blur-md border-border/40 hover:border-primary/30 transition-colors">
          <CardContent className="p-3.5">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-xl ${kpi.bg} ${kpi.color}`}>{kpi.icon}</div>
              <div className="min-w-0">
                <p className="text-[10px] text-muted-foreground truncate">{kpi.label}</p>
                <p className="text-lg font-mono text-foreground">{kpi.value}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ─── Sub-tab config ──────────────────────────────────────
const analyticsTabs = [
  { id: "overview", label: "نظرة عامة", icon: <BarChart3 className="w-3.5 h-3.5" /> },
  { id: "channels", label: "القنوات", icon: <MessageCircle className="w-3.5 h-3.5" /> },
  { id: "employees", label: "الموظفين", icon: <Users className="w-3.5 h-3.5" /> },
  { id: "tickets", label: "التذاكر", icon: <Ticket className="w-3.5 h-3.5" /> },
  { id: "branches", label: "الفروع", icon: <Building2 className="w-3.5 h-3.5" /> },
  { id: "vip", label: "VIP", icon: <Crown className="w-3.5 h-3.5" /> },
  { id: "ai-human", label: "AI مقابل بشري", icon: <Bot className="w-3.5 h-3.5" /> },
];

// ─── Main Component ──────────────────────────────────────
export function AnalyticsDashboard() {
  const [activeSubTab, setActiveSubTab] = useState("overview");

  const handleExport = useCallback(() => {
    exportToCSV(`noor-analytics-${activeSubTab}-${new Date().toISOString().slice(0, 10)}`);
  }, [activeSubTab]);

  return (
    <div className="space-y-5">
      {/* Header Bar */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        {/* Sub-tab navigation */}
        <ScrollArea className="w-full md:w-auto" dir="rtl">
          <div className="flex gap-1 p-1 bg-secondary/30 border border-border/40 rounded-xl">
            {analyticsTabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] whitespace-nowrap transition-all ${
                  activeSubTab === tab.id
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/30"
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        </ScrollArea>

        {/* Export Button */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5 text-xs border-border/40 hover:border-primary/40"
            onClick={handleExport}
          >
            <Download className="w-3.5 h-3.5" />
            تصدير CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5 text-xs border-border/40 hover:border-primary/40"
            onClick={handleExport}
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            Pivot-Ready
          </Button>
        </div>
      </div>

      {/* Content */}
      {activeSubTab === "overview" && <OverviewKPIs />}
      {activeSubTab === "channels" && <ChannelsTab />}
      {activeSubTab === "employees" && <EmployeesTab />}
      {activeSubTab === "tickets" && <TicketsTab />}
      {activeSubTab === "branches" && <BranchesTab />}
      {activeSubTab === "vip" && <VipTab />}
      {activeSubTab === "ai-human" && <AiHumanTab />}
    </div>
  );
}