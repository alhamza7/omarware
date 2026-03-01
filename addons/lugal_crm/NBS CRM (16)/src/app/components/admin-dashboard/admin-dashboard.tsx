import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Users, Crown, ListTodo, AlertTriangle, CalendarCheck,
  ScrollText, Eye, ShieldCheck,
  PanelRightClose, PanelRightOpen,
  Settings2,
} from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { ScrollArea } from "../ui/scroll-area";
import {
  Tooltip, TooltipContent, TooltipProvider, TooltipTrigger,
} from "../ui/tooltip";
import { tasks, complaints } from "./ad-data";
import { ADEmployees } from "./ad-employees";
import { ADVipCustomers } from "./ad-vip-customers";
import { ADTasks } from "./ad-tasks";
import { ADComplaints } from "./ad-complaints";
import { ADAttendance } from "./ad-attendance";
import { ADAuditLog } from "./ad-audit-log";
import { ADQaDashboard } from "./ad-qa-dashboard";
import { ADQaSupervisor } from "./ad-qa-supervisor";
import { ADRuleEngine } from "./ad-rule-engine";
import { Supervisor } from "../supervisor/supervisor";
import { Monitor } from "lucide-react";

const sections = [
  { id: "employees", label: "الموظفون", icon: Users },
  { id: "vip", label: "عملاء VIP", icon: Crown },
  { id: "tasks", label: "المتابعات والمهام", icon: ListTodo },
  { id: "complaints", label: "الشكاوى والتكتات", icon: AlertTriangle },
  { id: "attendance", label: "الحضور والدوام", icon: CalendarCheck },
  { id: "audit-log", label: "سجل العمليات", icon: ScrollText },
  { id: "qa-dashboard", label: "لوحة المدقق", icon: Eye },
  { id: "qa-supervisor", label: "مشرف المدققين", icon: ShieldCheck },
  { id: "rule-engine", label: "محرك القواعد", icon: Settings2 },
  { id: "live-supervisor", label: "المشرف المباشر", icon: Monitor },
];

const sectionDescriptions: Record<string, string> = {
  employees: "حالة الموظفين والقنوات والمحادثات ومعايير SLA",
  vip: "عملاء VIP وبياناتهم ومشاكلهم المفتوحة",
  tasks: "المتابعات والمهام والمحادثات بدون رد",
  complaints: "الشكاوى والتكتات وتتبع الحل",
  attendance: "الحضور والانصراف والعمل عن بعد",
  "audit-log": "سجل كل العمليات - قراءة فقط",
  "qa-dashboard": "لوحة المدقق - التقييمات والملاحظات",
  "qa-supervisor": "مراقبة أداء وإنتاجية المدققين",
  "rule-engine": "القواعد القابلة للتعديل — مجمّعة ومصنّفة حسب المنطق",
  "live-supervisor": "لوحة المشرف المباشرة — مراقبة حية للعمليات والأداء",
};

export function AdminDashboard() {
  const [activeSection, setActiveSection] = useState("employees");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const currentSection = sections.find((s) => s.id === activeSection);
  const openTasks = tasks.filter((t) => t.status === "open" || t.status === "overdue").length;
  const openComplaints = complaints.filter((c) => ["open", "escalated"].includes(c.status)).length;

  const renderContent = () => {
    switch (activeSection) {
      case "employees": return <ADEmployees />;
      case "vip": return <ADVipCustomers />;
      case "tasks": return <ADTasks />;
      case "complaints": return <ADComplaints />;
      case "attendance": return <ADAttendance />;
      case "audit-log": return <ADAuditLog />;
      case "qa-dashboard": return <ADQaDashboard />;
      case "qa-supervisor": return <ADQaSupervisor />;
      case "rule-engine": return <ADRuleEngine />;
      case "live-supervisor": return <Supervisor />;
      default: return <ADEmployees />;
    }
  };

  const getBadge = (sectionId: string) => {
    if (sectionId === "tasks" && openTasks > 0) return openTasks;
    if (sectionId === "complaints" && openComplaints > 0) return openComplaints;
    return 0;
  };

  return (
    <TooltipProvider delayDuration={300}>
      <div className="flex gap-0 min-h-[calc(100vh-220px)]">
        {/* ═══ Right Sidebar Navigation ═══ */}
        <motion.aside
          initial={false}
          animate={{ width: sidebarCollapsed ? 56 : 210 }}
          transition={{ duration: 0.2, ease: "easeInOut" }}
          className="shrink-0 border-e border-border/40 bg-card/30 dark:bg-[#0d0f12]/60 flex flex-col overflow-hidden"
        >
          {/* Sidebar Header */}
          <div className={`flex items-center shrink-0 px-2 py-3 border-b border-border/30 ${sidebarCollapsed ? "justify-center" : "justify-between"}`}>
            {!sidebarCollapsed && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-[11px] text-muted-foreground pe-1 truncate"
              >
                لوحة المشرف
              </motion.span>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-muted-foreground hover:text-foreground shrink-0"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            >
              {sidebarCollapsed ? (
                <PanelRightOpen className="w-3.5 h-3.5" />
              ) : (
                <PanelRightClose className="w-3.5 h-3.5" />
              )}
            </Button>
          </div>

          {/* Navigation Items */}
          <ScrollArea className="flex-1 min-h-0" dir="rtl">
            <nav className="flex flex-col gap-1 p-2">
              {sections.map((section) => {
                const Icon = section.icon;
                const isActive = activeSection === section.id;
                const badgeCount = getBadge(section.id);

                const buttonContent = (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`group relative flex items-center gap-2.5 w-full rounded-lg transition-all duration-200 outline-none ${
                      sidebarCollapsed ? "justify-center p-2.5" : "px-3 py-2.5"
                    } ${
                      isActive
                        ? "bg-primary/10 dark:bg-primary/15 text-primary shadow-sm"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted/40 dark:hover:bg-white/[0.04]"
                    }`}
                  >
                    {/* Active indicator bar */}
                    {isActive && (
                      <motion.div
                        layoutId="admin-sidebar-active"
                        className="absolute end-0 top-1.5 bottom-1.5 w-[3px] rounded-s-full bg-primary"
                        transition={{ type: "spring", stiffness: 350, damping: 30 }}
                      />
                    )}

                    {/* Icon */}
                    <div className="relative shrink-0">
                      <Icon className={`w-4 h-4 transition-colors ${isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"}`} />
                      {badgeCount > 0 && sidebarCollapsed && (
                        <span className="absolute -top-1 -start-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-card" />
                      )}
                    </div>

                    {/* Label + Badge */}
                    {!sidebarCollapsed && (
                      <motion.div
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex items-center justify-between flex-1 min-w-0"
                      >
                        <span className={`text-xs truncate ${isActive ? "text-primary" : ""}`}>
                          {section.label}
                        </span>
                        {badgeCount > 0 && (
                          <Badge className="bg-red-500 text-white text-[9px] h-4 min-w-[16px] px-1 border-transparent ms-1 shrink-0">
                            {badgeCount}
                          </Badge>
                        )}
                      </motion.div>
                    )}
                  </button>
                );

                if (sidebarCollapsed) {
                  return (
                    <Tooltip key={section.id}>
                      <TooltipTrigger asChild>{buttonContent}</TooltipTrigger>
                      <TooltipContent side="left" className="text-xs flex items-center gap-2">
                        {section.label}
                        {badgeCount > 0 && (
                          <Badge className="bg-red-500 text-white text-[9px] h-4 min-w-[16px] px-1 border-transparent">
                            {badgeCount}
                          </Badge>
                        )}
                      </TooltipContent>
                    </Tooltip>
                  );
                }

                return buttonContent;
              })}
            </nav>
          </ScrollArea>
        </motion.aside>

        {/* ═══ Main Content Area ═══ */}
        <div className="flex-1 min-w-0 flex flex-col">
          {/* Section Title Bar */}
          {currentSection && (
            <div className="shrink-0 px-5 py-4 border-b border-border/30 bg-card/20">
              <motion.div
                key={activeSection}
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2 }}
                className="flex items-center gap-3"
              >
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                  <currentSection.icon className="w-5 h-5 text-primary" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-lg text-foreground truncate">{currentSection.label}</h3>
                  <p className="text-xs text-muted-foreground truncate">
                    {sectionDescriptions[activeSection]}
                  </p>
                </div>
              </motion.div>
            </div>
          )}

          {/* Content */}
          <div className="flex-1 min-h-0 p-5 overflow-y-auto">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeSection}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                {renderContent()}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}