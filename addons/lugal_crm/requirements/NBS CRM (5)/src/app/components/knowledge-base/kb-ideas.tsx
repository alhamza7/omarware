import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  ThumbsUp,
  MessageCircle,
  Search,
  Plus,
  X,
  Send,
  User,
  Lightbulb,
  CheckCircle2,
  Clock,
  XCircle,
  Rocket,
  Filter,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { ideas as initialIdeas, type Idea } from "./kb-data";

const statusConfig: Record<Idea["status"], { label: string; color: string; icon: typeof Lightbulb }> = {
  new: { label: "جديدة", color: "bg-blue-500/10 text-blue-500 border-blue-500/20", icon: Lightbulb },
  "under-review": { label: "قيد المراجعة", color: "bg-primary/10 text-primary border-primary/20", icon: Clock },
  approved: { label: "معتمدة", color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20", icon: CheckCircle2 },
  implemented: { label: "مُنفّذة", color: "bg-cyan-500/10 text-cyan-500 border-cyan-500/20", icon: Rocket },
  declined: { label: "مرفوضة", color: "bg-red-500/10 text-red-500 border-red-500/20", icon: XCircle },
};

const roleColors: Record<string, string> = {
  "موظف": "bg-blue-500/10 text-blue-500",
  "موظفة": "bg-blue-500/10 text-blue-500",
  "عميل VIP": "bg-primary/10 text-primary",
  "شريك تجاري": "bg-emerald-500/10 text-emerald-500",
};

export function KBIdeas() {
  const [ideasList, setIdeasList] = useState(initialIdeas);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | Idea["status"]>("all");
  const [showNewForm, setShowNewForm] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newCategory, setNewCategory] = useState("");
  const [sortBy, setSortBy] = useState<"votes" | "date">("votes");

  const filtered = ideasList
    .filter((idea) => {
      const matchSearch =
        idea.title.includes(search) ||
        idea.description.includes(search) ||
        idea.category.includes(search);
      const matchStatus = statusFilter === "all" || idea.status === statusFilter;
      return matchSearch && matchStatus;
    })
    .sort((a, b) =>
      sortBy === "votes" ? b.votes - a.votes : new Date(b.date).getTime() - new Date(a.date).getTime()
    );

  const handleVote = (id: string) => {
    setIdeasList((prev) =>
      prev.map((idea) =>
        idea.id === id
          ? {
              ...idea,
              votes: idea.userVoted ? idea.votes - 1 : idea.votes + 1,
              userVoted: !idea.userVoted,
            }
          : idea
      )
    );
  };

  const handleSubmit = () => {
    if (!newTitle.trim() || !newDescription.trim()) return;
    const newIdea: Idea = {
      id: `i${Date.now()}`,
      title: newTitle,
      description: newDescription,
      author: "أحمد العلي",
      authorRole: "موظف",
      date: new Date().toISOString().split("T")[0],
      votes: 0,
      comments: 0,
      status: "new",
      category: newCategory || "عام",
    };
    setIdeasList((prev) => [newIdea, ...prev]);
    setNewTitle("");
    setNewDescription("");
    setNewCategory("");
    setShowNewForm(false);
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="بحث في الأفكار..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pr-9 bg-secondary/30 border-border/50"
          />
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={sortBy === "votes" ? "default" : "outline"}
            size="sm"
            className="text-xs gap-1.5"
            onClick={() => setSortBy("votes")}
          >
            <ThumbsUp className="w-3 h-3" />
            الأكثر تصويتاً
          </Button>
          <Button
            variant={sortBy === "date" ? "default" : "outline"}
            size="sm"
            className="text-xs gap-1.5"
            onClick={() => setSortBy("date")}
          >
            <Clock className="w-3 h-3" />
            الأحدث
          </Button>
          <Button
            size="sm"
            className="gap-1.5"
            onClick={() => setShowNewForm(true)}
          >
            <Plus className="w-4 h-4" />
            فكرة جديدة
          </Button>
        </div>
      </div>

      {/* Status Filters */}
      <div className="flex gap-2 flex-wrap">
        <Button
          variant={statusFilter === "all" ? "default" : "outline"}
          size="sm"
          className="text-xs"
          onClick={() => setStatusFilter("all")}
        >
          <Filter className="w-3 h-3 me-1.5" />
          الكل
        </Button>
        {Object.entries(statusConfig).map(([key, config]) => {
          const Icon = config.icon;
          return (
            <Button
              key={key}
              variant={statusFilter === key ? "default" : "outline"}
              size="sm"
              className="text-xs gap-1.5"
              onClick={() => setStatusFilter(key as Idea["status"])}
            >
              <Icon className="w-3 h-3" />
              {config.label}
            </Button>
          );
        })}
      </div>

      {/* New Idea Form */}
      <AnimatePresence>
        {showNewForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <Card className="border-primary/30 bg-primary/5">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-primary" />
                    اقتراح فكرة جديدة
                  </CardTitle>
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setShowNewForm(false)}>
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <Input
                  placeholder="عنوان الفكرة"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="bg-background"
                />
                <textarea
                  placeholder="وصف مفصل للفكرة..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
                <Input
                  placeholder="التصنيف (مثال: منتجات، خدمة العملاء...)"
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="bg-background"
                />
                <Button onClick={handleSubmit} size="sm" className="gap-2">
                  <Send className="w-3.5 h-3.5" />
                  إرسال الفكرة
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Ideas List */}
      <div className="space-y-4">
        {filtered.map((idea, i) => {
          const status = statusConfig[idea.status];
          const StatusIcon = status.icon;

          return (
            <motion.div
              key={idea.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04 }}
            >
              <Card className="border-border/50 hover:shadow-md transition-all group">
                <CardContent className="p-5">
                  <div className="flex gap-4">
                    {/* Vote Column */}
                    <div className="flex flex-col items-center gap-1 shrink-0">
                      <Button
                        variant="ghost"
                        size="icon"
                        className={`h-10 w-10 rounded-xl transition-all ${
                          idea.userVoted
                            ? "bg-primary/20 text-primary hover:bg-primary/30"
                            : "hover:bg-primary/10 hover:text-primary text-muted-foreground"
                        }`}
                        onClick={() => handleVote(idea.id)}
                      >
                        <ThumbsUp className={`w-5 h-5 ${idea.userVoted ? "fill-current" : ""}`} />
                      </Button>
                      <span className={`text-sm ${idea.userVoted ? "text-primary" : "text-muted-foreground"}`}>
                        {idea.votes}
                      </span>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <h4 className="text-foreground group-hover:text-primary transition-colors">
                          {idea.title}
                        </h4>
                        <Badge className={`text-[10px] shrink-0 gap-1 ${status.color}`}>
                          <StatusIcon className="w-3 h-3" />
                          {status.label}
                        </Badge>
                      </div>

                      <p className="text-sm text-muted-foreground mb-3">
                        {idea.description}
                      </p>

                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1.5">
                            <div className="w-5 h-5 rounded-full bg-secondary flex items-center justify-center">
                              <User className="w-3 h-3" />
                            </div>
                            {idea.author}
                          </span>
                          <Badge
                            className={`text-[10px] h-5 border-transparent ${
                              roleColors[idea.authorRole] || "bg-secondary text-foreground"
                            }`}
                          >
                            {idea.authorRole}
                          </Badge>
                          <Badge variant="outline" className="text-[10px] h-5">
                            {idea.category}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <MessageCircle className="w-3 h-3" />
                            {idea.comments} تعليق
                          </span>
                          <span>{new Date(idea.date).toLocaleDateString("ar-SA")}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}

        {filtered.length === 0 && (
          <div className="text-center py-12 text-muted-foreground">
            <Lightbulb className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>لا توجد أفكار تطابق البحث</p>
          </div>
        )}
      </div>
    </div>
  );
}
