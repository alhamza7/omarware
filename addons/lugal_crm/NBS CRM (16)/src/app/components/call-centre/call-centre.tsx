import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Phone,
  ClipboardList,
  MessageSquare,
  Users,
  FileText,
  BarChart3,
  CalendarClock,
  Headset,
  ChevronLeft,
  History,
} from "lucide-react";
import { Button } from "../ui/button";
import { CCLiveDashboard } from "./cc-live-dashboard";
import { CCCallLog } from "./cc-call-log";
import { CCTickets } from "./cc-tickets";
import { CCInbox } from "./cc-inbox";
import { CCAgentPerformance } from "./cc-agent-performance";
import { CCScripts } from "./cc-scripts";
import { CCAnalytics } from "./cc-analytics";
import { CCFollowUps } from "./cc-followups";

const sections = [
  { id: "live", label: "المكالمات الحية", icon: Phone },
  { id: "call-log", label: "سجل المكالمات", icon: History },
  { id: "tickets", label: "التذاكر", icon: ClipboardList },
  { id: "inbox", label: "صندوق الوارد", icon: MessageSquare },
  { id: "agents", label: "أداء الوكلاء", icon: Users },
  { id: "scripts", label: "النصوص الجاهزة", icon: FileText },
  { id: "analytics", label: "تقارير المركز", icon: BarChart3 },
  { id: "followups", label: "المتابعات", icon: CalendarClock },
];

export function CallCentre() {
  const [activeSection, setActiveSection] = useState("live");

  const currentSection = sections.find((s) => s.id === activeSection);

  const renderContent = () => {
    switch (activeSection) {
      case "live":
        return <CCLiveDashboard />;
      case "call-log":
        return <CCCallLog />;
      case "tickets":
        return <CCTickets />;
      case "inbox":
        return <CCInbox />;
      case "agents":
        return <CCAgentPerformance />;
      case "scripts":
        return <CCScripts />;
      case "analytics":
        return <CCAnalytics />;
      case "followups":
        return <CCFollowUps />;
      default:
        return <CCLiveDashboard />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Section Navigation */}
      <div className="flex items-center gap-3 overflow-x-auto pb-1 scrollbar-hide">
        <div className="flex gap-1.5 flex-nowrap">
          {sections.map((section) => {
            const Icon = section.icon;
            const isActive = activeSection === section.id;
            return (
              <Button
                key={section.id}
                variant={isActive ? "default" : "ghost"}
                size="sm"
                className={`text-xs gap-1.5 whitespace-nowrap shrink-0 transition-all ${
                  isActive
                    ? ""
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                }`}
                onClick={() => setActiveSection(section.id)}
              >
                <Icon className="w-3.5 h-3.5" />
                {section.label}
                {/* Live indicator for active calls tab */}
                {section.id === "live" && (
                  <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                )}
              </Button>
            );
          })}
        </div>
      </div>

      {/* Section Title */}
      {currentSection && (
        <motion.div
          key={activeSection}
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3"
        >
          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <currentSection.icon className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="text-lg text-foreground">{currentSection.label}</h3>
            <p className="text-xs text-muted-foreground">
              {activeSection === "live" && "المكالمات النشطة وقائمة الانتظار وحالة الوكلاء"}
              {activeSection === "call-log" && "سجل جميع المكالمات الواردة والصادرة"}
              {activeSection === "tickets" && "إدارة تذاكر الدعم والشكاوى"}
              {activeSection === "inbox" && "جميع الرسائل من واتساب والبريد والسوشال ميديا"}
              {activeSection === "agents" && "إحصائيات الأداء وترتيب الوكلاء"}
              {activeSection === "scripts" && "نصوص وردود جاهزة للمكالمات"}
              {activeSection === "analytics" && "تقارير وإحصائيات شاملة للمركز"}
              {activeSection === "followups" && "جدولة ومتابعة معاودة الاتصال بالعملاء"}
            </p>
          </div>
        </motion.div>
      )}

      {/* Content */}
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
  );
}
