import { useState } from "react";
import { motion } from "motion/react";
import { AlertCircle, CheckCircle2, Circle, Clock, User } from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { circulars } from "./kb-data";

const priorityConfig = {
  high: { label: "عالية", color: "bg-red-500/10 text-red-500 border-red-500/20", dot: "bg-red-500" },
  medium: { label: "متوسطة", color: "bg-primary/10 text-primary border-primary/20", dot: "bg-primary" },
  low: { label: "منخفضة", color: "bg-muted text-muted-foreground border-border", dot: "bg-muted-foreground" },
};

export function KBCirculars() {
  const [items, setItems] = useState(circulars);
  const [filter, setFilter] = useState<"all" | "unread" | "read">("all");

  const filtered =
    filter === "all" ? items :
    filter === "unread" ? items.filter((c) => !c.read) :
    items.filter((c) => c.read);

  const unreadCount = items.filter((c) => !c.read).length;

  const markAsRead = (id: string) => {
    setItems((prev) => prev.map((c) => (c.id === id ? { ...c, read: true } : c)));
  };

  const markAllRead = () => {
    setItems((prev) => prev.map((c) => ({ ...c, read: true })));
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-2 flex-wrap">
          {[
            { key: "all" as const, label: "الكل" },
            { key: "unread" as const, label: `غير مقروءة (${unreadCount})` },
            { key: "read" as const, label: "مقروءة" },
          ].map((f) => (
            <Button
              key={f.key}
              variant={filter === f.key ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter(f.key)}
              className="text-xs"
            >
              {f.label}
            </Button>
          ))}
        </div>
        {unreadCount > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="text-xs text-muted-foreground hover:text-primary gap-1.5"
            onClick={markAllRead}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            تحديد الكل كمقروء
          </Button>
        )}
      </div>

      {/* Circulars List */}
      <div className="space-y-3">
        {filtered.map((circular, i) => {
          const priority = priorityConfig[circular.priority];

          return (
            <motion.div
              key={circular.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Card
                className={`transition-all hover:shadow-md ${
                  !circular.read
                    ? "border-primary/30 bg-primary/5"
                    : "border-border/50"
                }`}
              >
                <CardContent className="p-5">
                  <div className="flex gap-4">
                    {/* Read Indicator */}
                    <div className="pt-1 shrink-0">
                      {!circular.read ? (
                        <div className="w-3 h-3 rounded-full bg-primary animate-pulse" />
                      ) : (
                        <Circle className="w-3 h-3 text-muted-foreground/30" />
                      )}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <h4 className={`text-foreground ${!circular.read ? "" : "opacity-80"}`}>
                          {circular.title}
                        </h4>
                        <div className="flex items-center gap-2 shrink-0">
                          <Badge className={`text-[10px] ${priority.color}`}>
                            {circular.priority === "high" && <AlertCircle className="w-3 h-3 me-0.5" />}
                            {priority.label}
                          </Badge>
                        </div>
                      </div>

                      <p className="text-sm text-muted-foreground mb-3">
                        {circular.content}
                      </p>

                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1.5">
                            <User className="w-3 h-3" />
                            {circular.author}
                          </span>
                          <Badge variant="outline" className="text-[10px] h-5">
                            {circular.department}
                          </Badge>
                          <span className="flex items-center gap-1.5">
                            <Clock className="w-3 h-3" />
                            {new Date(circular.date).toLocaleDateString("ar-SA")}
                          </span>
                        </div>

                        {!circular.read && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-xs h-6 text-primary hover:text-primary"
                            onClick={() => markAsRead(circular.id)}
                          >
                            تحديد كمقروء
                          </Button>
                        )}
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
            <CheckCircle2 className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>لا توجد تعاميم {filter === "unread" ? "غير مقروءة" : ""}</p>
          </div>
        )}
      </div>
    </div>
  );
}
