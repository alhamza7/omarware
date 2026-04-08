import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  Building2,
  BookOpen,
  CalendarDays,
  Megaphone,
  Lightbulb,
  HelpCircle,
  GraduationCap,
  FolderOpen,
  Home,
  ChevronLeft,
} from "lucide-react";
import { Button } from "../ui/button";
import { KBOverview } from "./kb-overview";
import { KBCompanyPolicies } from "./kb-company-policies";
import { KBJournals } from "./kb-journals";
import { KBEvents } from "./kb-events";
import { KBCirculars } from "./kb-circulars";
import { KBIdeas } from "./kb-ideas";
import { KBFAQ } from "./kb-faq";
import { KBTraining } from "./kb-training";
import { KBDocuments } from "./kb-documents";

const sections = [
  { id: "overview", label: "الرئيسية", icon: Home },
  { id: "company", label: "الشركة والسياسات", icon: Building2 },
  { id: "journals", label: "المجلات", icon: BookOpen },
  { id: "events", label: "الفعاليات", icon: CalendarDays },
  { id: "circulars", label: "التعاميم", icon: Megaphone },
  { id: "ideas", label: "الأفكار والإجابات", icon: Lightbulb },
  { id: "faq", label: "الأسئلة الشائعة", icon: HelpCircle },
  { id: "training", label: "التدريب والتطوير", icon: GraduationCap },
  { id: "documents", label: "مكتبة المستندات", icon: FolderOpen },
];

export function KnowledgeBase() {
  const [activeSection, setActiveSection] = useState("overview");

  const currentSection = sections.find((s) => s.id === activeSection);

  const renderContent = () => {
    switch (activeSection) {
      case "overview":
        return <KBOverview onNavigate={setActiveSection} />;
      case "company":
        return <KBCompanyPolicies />;
      case "journals":
        return <KBJournals />;
      case "events":
        return <KBEvents />;
      case "circulars":
        return <KBCirculars />;
      case "ideas":
        return <KBIdeas />;
      case "faq":
        return <KBFAQ />;
      case "training":
        return <KBTraining />;
      case "documents":
        return <KBDocuments />;
      default:
        return <KBOverview onNavigate={setActiveSection} />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Section Navigation */}
      <div className="flex items-center gap-3 overflow-x-auto pb-1 scrollbar-hide">
        {/* Breadcrumb-style back button (only when not on overview) */}
        {activeSection !== "overview" && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0 text-muted-foreground hover:text-primary"
            onClick={() => setActiveSection("overview")}
          >
            <ChevronLeft className="w-4 h-4 rotate-180" />
          </Button>
        )}

        {/* Nav Tabs */}
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
              </Button>
            );
          })}
        </div>
      </div>

      {/* Section Title */}
      {activeSection !== "overview" && currentSection && (
        <motion.div
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
              {activeSection === "company" && "رؤية الشركة، السياسات، والإرشادات الداخلية"}
              {activeSection === "journals" && "مقالات ودراسات متخصصة في صناعة العطور"}
              {activeSection === "events" && "الفعاليات والاجتماعات والأنشطة"}
              {activeSection === "circulars" && "التعاميم الرسمية والإشعارات الإدارية"}
              {activeSection === "ideas" && "اقترح وناقش وصوّت على أفكار لتطوير العمل"}
              {activeSection === "faq" && "إجابات سريعة على الأسئلة الأكثر تكراراً"}
              {activeSection === "training" && "دورات تدريبية ومواد تعليمية"}
              {activeSection === "documents" && "نماذج ووثائق وملفات مرجعية"}
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
