import { Home, Users, ShoppingBag, Package, Settings, BarChart3, Headset, BookMarked, Container, ShieldCheck, MessageSquareDot, Ticket, UserCog, Megaphone, Eye, Target, ScrollText, TrendingUp, LogOut } from "lucide-react";
import { cn } from "../lib/utils";
import { motion } from "motion/react";
import { LogoAnimation } from "./logo-animation";

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  onLogout?: () => void;
}

export function Sidebar({ activeTab, onTabChange, onLogout }: SidebarProps) {
  const menuItems = [
    { id: "dashboard", label: "لوحة التحكم", icon: Home },
    { id: "customers", label: "العملاء", icon: Users },
    { id: "products", label: "المنتجات", icon: Package },
    { id: "orders", label: "الطلبات", icon: ShoppingBag },
    { id: "omni-channel", label: "القنوات الموحدة", icon: MessageSquareDot },
    { id: "tickets", label: "التذاكر", icon: Ticket },
    { id: "agents", label: "الموظفون", icon: UserCog },
    { id: "sales-pipeline", label: "خط المبيعات", icon: Target },
    { id: "forecasting", label: "التنبؤات", icon: TrendingUp },
    { id: "supply-chain", label: "سلسلة التوريد", icon: Container },
    { id: "promotions", label: "مركز العروض", icon: Megaphone },
    { id: "analytics", label: "التحليلات", icon: BarChart3 },
    { id: "knowledge-base", label: "قاعدة المعرفة", icon: BookMarked },
    { id: "call-centre", label: "مركز الاتصال", icon: Headset },
    { id: "event-log", label: "سجل الأحداث", icon: ScrollText },
    { id: "admin-dashboard", label: "لوحة المشرف", icon: ShieldCheck },
    { id: "settings", label: "الإعدادات", icon: Settings },
  ];

  return (
    <aside className="w-64 bg-sidebar border-e border-sidebar-border flex flex-col relative overflow-hidden">
      {/* Subtle gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-primary/5 via-transparent to-accent/5 pointer-events-none" />
      
      {/* Logo / Brand */}
      <div className="p-6 border-b border-sidebar-border relative z-10">
        <LogoAnimation />
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 relative z-10 overflow-y-auto">
        {menuItems.map((item, index) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          
          return (
            <motion.button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-200 relative overflow-hidden",
                isActive
                  ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                  : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
              )}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ x: -5 }}
              whileTap={{ scale: 0.98 }}
            >
              {isActive && (
                <motion.div
                  className="absolute inset-0 bg-gradient-to-l from-primary via-primary to-gold-dark"
                  layoutId="activeTab"
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
              <motion.div
                className="relative z-10"
                animate={isActive ? { rotate: [0, 5, -5, 0] } : {}}
                transition={{ duration: 0.5 }}
              >
                <Icon className="w-5 h-5" />
              </motion.div>
              <span className="relative z-10">{item.label}</span>
            </motion.button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-sidebar-border relative z-10">
        <motion.div 
          className="p-4 rounded-lg bg-gradient-to-br from-primary/10 to-accent/5 border border-primary/20 relative overflow-hidden"
          whileHover={{ scale: 1.02 }}
        >
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-primary/10 to-transparent"
            animate={{
              x: ["-100%", "200%"],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              repeatDelay: 5,
              ease: "easeInOut",
            }}
          />
          <p className="text-xs text-muted-foreground mb-1 relative z-10">الإصدار</p>
          <p className="text-sm font-semibold text-primary relative z-10">v3.0.0</p>
        </motion.div>
        {onLogout && (
          <motion.button
            whileHover={{ x: -3 }}
            whileTap={{ scale: 0.97 }}
            className="w-full flex items-center gap-3 px-4 py-2.5 mt-2 rounded-lg transition-all duration-200 text-red-400 hover:bg-red-500/10 hover:text-red-300 cursor-pointer"
            onClick={onLogout}
          >
            <LogOut className="w-5 h-5" />
            <span>تسجيل الخروج</span>
          </motion.button>
        )}
      </div>
    </aside>
  );
}