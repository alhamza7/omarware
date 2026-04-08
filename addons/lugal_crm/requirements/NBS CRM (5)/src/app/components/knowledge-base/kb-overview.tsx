import { motion } from "motion/react";
import {
  Building2,
  BookOpen,
  CalendarDays,
  Megaphone,
  Lightbulb,
  HelpCircle,
  GraduationCap,
  FolderOpen,
  Users,
  TrendingUp,
  FileText,
  Star,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";

interface KBOverviewProps {
  onNavigate: (section: string) => void;
}

const sections = [
  {
    id: "company",
    title: "عن الشركة والسياسات",
    description: "رؤية الشركة، الهيكل التنظيمي، والسياسات الداخلية",
    icon: Building2,
    color: "text-primary",
    bg: "bg-primary/10",
    border: "border-primary/20",
    count: "6 مقالات",
  },
  {
    id: "journals",
    title: "المجلات",
    description: "مقالات ودراسات متخصصة في عالم العطور",
    icon: BookOpen,
    color: "text-emerald-500",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    count: "5 مقالات",
  },
  {
    id: "events",
    title: "الفعاليات",
    description: "ورش عمل، اجتماعات، واحتفالات الشركة",
    icon: CalendarDays,
    color: "text-blue-500",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
    count: "5 فعاليات",
  },
  {
    id: "circulars",
    title: "التعاميم والإشعارات",
    description: "تعاميم رسمية وإشعارات إدارية مهمة",
    icon: Megaphone,
    color: "text-red-500",
    bg: "bg-red-500/10",
    border: "border-red-500/20",
    count: "2 غير مقروءة",
  },
  {
    id: "ideas",
    title: "الأفكار والإجابات",
    description: "اقترح وناقش وصوّت على أفكار جديدة",
    icon: Lightbulb,
    color: "text-yellow-500",
    bg: "bg-yellow-500/10",
    border: "border-yellow-500/20",
    count: "6 أفكار",
  },
  {
    id: "faq",
    title: "الأسئلة الشائعة",
    description: "إجابات سريعة على الأسئلة الأكثر تكراراً",
    icon: HelpCircle,
    color: "text-purple-500",
    bg: "bg-purple-500/10",
    border: "border-purple-500/20",
    count: "8 أسئلة",
  },
  {
    id: "training",
    title: "التدريب والتطوير",
    description: "دورات تدريبية ومواد تعليمية لتطوير المهارات",
    icon: GraduationCap,
    color: "text-cyan-500",
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/20",
    count: "5 دورات",
  },
  {
    id: "documents",
    title: "مكتبة المستندات",
    description: "نماذج وملفات ووثائق رسمية",
    icon: FolderOpen,
    color: "text-pink-500",
    bg: "bg-pink-500/10",
    border: "border-pink-500/20",
    count: "8 مستندات",
  },
];

const quickStats = [
  { label: "إجمالي المقالات", value: "24", icon: FileText },
  { label: "الموظفين النشطين", value: "45", icon: Users },
  { label: "الأفكار المعتمدة", value: "12", icon: Star },
  { label: "معدل القراءة", value: "87%", icon: TrendingUp },
];

export function KBOverview({ onNavigate }: KBOverviewProps) {
  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl p-8 border border-primary/20"
        style={{
          background: "linear-gradient(135deg, var(--primary) 0%, var(--gold-dark) 50%, var(--primary) 100%)",
          backgroundSize: "200% 200%",
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-l from-black/30 to-transparent" />
        <div className="relative z-10">
          <h2 className="text-2xl text-primary-foreground mb-2">
            مرحباً بك في قاعدة المعرفة
          </h2>
          <p className="text-primary-foreground/80 max-w-xl">
            مصدرك الشامل للمعلومات والسياسات والموارد. استكشف الأقسام المختلفة للوصول
            إلى كل ما تحتاجه لأداء عملك بتميز.
          </p>
        </div>
        {/* Decorative circles */}
        <div className="absolute -top-10 -left-10 w-40 h-40 rounded-full bg-white/5" />
        <div className="absolute -bottom-10 -left-20 w-60 h-60 rounded-full bg-white/5" />
      </motion.div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {quickStats.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Card className="border-border/50 hover:border-primary/30 transition-all">
                <CardContent className="p-4 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                    <Icon className="w-5 h-5 text-primary" />
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

      {/* Section Cards Grid */}
      <div>
        <h3 className="text-lg text-foreground mb-4">أقسام قاعدة المعرفة</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {sections.map((section, i) => {
            const Icon = section.icon;
            return (
              <motion.div
                key={section.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.05 }}
              >
                <Card
                  className={`group cursor-pointer hover:shadow-lg transition-all duration-300 border ${section.border} hover:border-primary/40 h-full`}
                  onClick={() => onNavigate(section.id)}
                >
                  <CardContent className="p-5 flex flex-col h-full">
                    <div className={`w-12 h-12 rounded-xl ${section.bg} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                      <Icon className={`w-6 h-6 ${section.color}`} />
                    </div>
                    <h4 className="text-foreground mb-1 group-hover:text-primary transition-colors">
                      {section.title}
                    </h4>
                    <p className="text-xs text-muted-foreground flex-1 mb-3">
                      {section.description}
                    </p>
                    <Badge variant="secondary" className="w-fit text-[10px]">
                      {section.count}
                    </Badge>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Recent Activity */}
      <div>
        <h3 className="text-lg text-foreground mb-4">آخر التحديثات</h3>
        <Card className="border-border/50">
          <CardContent className="p-0 divide-y divide-border/50">
            {[
              { text: "تم إضافة تعميم جديد: تحديث ساعات العمل", time: "منذ ساعتين", type: "circular" },
              { text: "فكرة جديدة: خط عطور صديق للبيئة", time: "منذ 4 ساعات", type: "idea" },
              { text: "مقال جديد: أسرار صناعة العود", time: "أمس", type: "journal" },
              { text: "فعالية قادمة: ورشة عمل فن مزج العطور", time: "منذ يومين", type: "event" },
              { text: "تم تحديث: دليل الموظف الشامل", time: "منذ 3 أيام", type: "policy" },
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.05 }}
                className="flex items-center justify-between p-4 hover:bg-secondary/30 transition-colors cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full shrink-0 ${
                    item.type === "circular" ? "bg-red-500" :
                    item.type === "idea" ? "bg-yellow-500" :
                    item.type === "journal" ? "bg-emerald-500" :
                    item.type === "event" ? "bg-blue-500" :
                    "bg-primary"
                  }`} />
                  <p className="text-sm text-foreground">{item.text}</p>
                </div>
                <span className="text-xs text-muted-foreground whitespace-nowrap ps-4">{item.time}</span>
              </motion.div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
