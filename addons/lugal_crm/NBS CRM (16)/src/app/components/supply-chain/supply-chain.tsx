import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  ClipboardList,
  Container as ContainerIcon,
  Users,
  ShieldCheck,
  PackagePlus,
  Handshake,
  Bell,
  MessageSquare,
  BarChart3,
  PanelRightClose,
  PanelRightOpen,
} from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { ScrollArea } from "../ui/scroll-area";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../ui/tooltip";
import { SCPurchaseOrders } from "./sc-purchase-orders";
import { SCContainers } from "./sc-containers";
import { SCSuppliers } from "./sc-suppliers";
import { SCRequests } from "./sc-requests";
import { SCNegotiations } from "./sc-negotiations";
import { scNotifications } from "./sc-data";
import { SCClearance } from "./sc-clearance";
import { SCNotifications } from "./sc-notifications";
import { SCMessaging } from "./sc-messaging";
import { SCMinMax } from "./sc-minmax";
import type { ApiSupplyPo } from "./sc-purchase-orders";

const sections = [
  { id: "purchase-orders", label: "أوامر الشراء", icon: ClipboardList },
  { id: "containers", label: "الحاويات", icon: ContainerIcon },
  { id: "suppliers", label: "الموردين", icon: Users },
  { id: "clearance", label: "التخليص الجمركي", icon: ShieldCheck },
  { id: "requests", label: "طلبات الأصناف", icon: PackagePlus },
  { id: "negotiations", label: "المفاوضات", icon: Handshake },
  { id: "minmax", label: "الحد الأدنى/الأقصى", icon: BarChart3 },
  { id: "messaging", label: "المراسلات", icon: MessageSquare },
  { id: "notifications", label: "الإشعارات", icon: Bell },
];

const sectionDescriptions: Record<string, string> = {
  "purchase-orders": "إنشاء وإدارة أوامر الشراء وقوائم التعبئة",
  containers: "تتبع الحاويات النشطة والواصلة والمكتملة",
  suppliers: "بطاقات الموردين ومعلومات التواصل",
  clearance: "شركات التخليص الجمركي والممثلين المعتمدين",
  requests: "طلبات الأصناف من الأقسام المختلفة",
  negotiations: "مفاوضات الأسعار مع الموردين",
  minmax: "الحد الأدنى والأقصى لمخزون الأصناف",
  messaging: "المحادثات الداخلية والبريد الإلكتروني",
  notifications: "التذكيرات والإشعارات والتنبيهات",
};

export type SupplyChainProps = {
  /** Live PO rows from Odoo (`/api/crm/supply/po/list`). Omit to use in-module demo data. */
  apiPurchaseOrders?: ApiSupplyPo[];
};

export function SupplyChain({ apiPurchaseOrders }: SupplyChainProps = {}) {
  const [activeSection, setActiveSection] = useState("purchase-orders");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const currentSection = sections.find((s) => s.id === activeSection);
  const unreadNotifs = scNotifications.filter((n) => !n.read).length;

  const renderContent = () => {
    switch (activeSection) {
      case "purchase-orders":
        return <SCPurchaseOrders apiPos={apiPurchaseOrders} />;
      case "containers":
        return <SCContainers />;
      case "suppliers":
        return <SCSuppliers />;
      case "clearance":
        return <SCClearance />;
      case "requests":
        return <SCRequests />;
      case "negotiations":
        return <SCNegotiations />;
      case "minmax":
        return <SCMinMax />;
      case "messaging":
        return <SCMessaging />;
      case "notifications":
        return <SCNotifications />;
      default:
        return <SCPurchaseOrders apiPos={apiPurchaseOrders} />;
    }
  };

  return (
    <TooltipProvider delayDuration={300}>
      <div className="flex gap-0 min-h-[calc(100vh-220px)]">
        {/* ═══ Right Sidebar Navigation (appears on right in RTL) ═══ */}
        <motion.aside
          initial={false}
          animate={{ width: sidebarCollapsed ? 56 : 200 }}
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
                سلسلة التوريد
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
                const hasNotif = section.id === "notifications" && unreadNotifs > 0;

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
                        layoutId="sidebar-active-indicator"
                        className="absolute end-0 top-1.5 bottom-1.5 w-[3px] rounded-s-full bg-primary"
                        transition={{ type: "spring", stiffness: 350, damping: 30 }}
                      />
                    )}

                    {/* Icon */}
                    <div className="relative shrink-0">
                      <Icon className={`w-4 h-4 transition-colors ${isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"}`} />
                      {/* Notification dot (collapsed mode) */}
                      {hasNotif && sidebarCollapsed && (
                        <span className="absolute -top-1 -start-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-card" />
                      )}
                    </div>

                    {/* Label + Badge (expanded mode) */}
                    {!sidebarCollapsed && (
                      <motion.div
                        initial={{ opacity: 0, x: -8 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex items-center justify-between flex-1 min-w-0"
                      >
                        <span className={`text-xs truncate ${isActive ? "text-primary" : ""}`}>
                          {section.label}
                        </span>
                        {hasNotif && (
                          <Badge className="bg-red-500 text-white text-[9px] h-4 min-w-[16px] px-1 border-transparent ms-1 shrink-0">
                            {unreadNotifs}
                          </Badge>
                        )}
                      </motion.div>
                    )}
                  </button>
                );

                // Wrap in tooltip when collapsed
                if (sidebarCollapsed) {
                  return (
                    <Tooltip key={section.id}>
                      <TooltipTrigger asChild>
                        {buttonContent}
                      </TooltipTrigger>
                      <TooltipContent side="left" className="text-xs flex items-center gap-2">
                        {section.label}
                        {hasNotif && (
                          <Badge className="bg-red-500 text-white text-[9px] h-4 min-w-[16px] px-1 border-transparent">
                            {unreadNotifs}
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