import { motion } from "motion/react";
import { GraduationCap, Clock, User, Play, CheckCircle2, BookOpen } from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Progress } from "../ui/progress";
import { trainingCourses } from "./kb-data";

const levelConfig = {
  beginner: { label: "مبتدئ", color: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" },
  intermediate: { label: "متوسط", color: "bg-primary/10 text-primary border-primary/20" },
  advanced: { label: "متقدم", color: "bg-purple-500/10 text-purple-500 border-purple-500/20" },
};

export function KBTraining() {
  const inProgress = trainingCourses.filter((c) => c.progress > 0 && c.progress < 100);
  const completed = trainingCourses.filter((c) => c.progress === 100);
  const available = trainingCourses.filter((c) => c.progress === 0);

  return (
    <div className="space-y-8">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "إجمالي الدورات", value: trainingCourses.length.toString(), icon: BookOpen },
          { label: "قيد التقدم", value: inProgress.length.toString(), icon: Play },
          { label: "مكتملة", value: completed.length.toString(), icon: CheckCircle2 },
          { label: "متاحة للبدء", value: available.length.toString(), icon: GraduationCap },
        ].map((stat, i) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Card className="border-border/50">
                <CardContent className="p-4 flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                    <Icon className="w-4.5 h-4.5 text-primary" />
                  </div>
                  <div>
                    <p className="text-xl text-foreground">{stat.value}</p>
                    <p className="text-xs text-muted-foreground">{stat.label}</p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* In Progress */}
      {inProgress.length > 0 && (
        <div>
          <h4 className="text-sm text-muted-foreground mb-3 flex items-center gap-2">
            <Play className="w-3.5 h-3.5 text-primary" />
            قيد التقدم
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {inProgress.map((course, i) => {
              const level = levelConfig[course.level];
              return (
                <motion.div
                  key={course.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card className="border-primary/20 bg-primary/5 hover:shadow-md transition-all group">
                    <CardContent className="p-5">
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <h4 className="text-foreground group-hover:text-primary transition-colors">
                          {course.title}
                        </h4>
                        <Badge className={`text-[10px] shrink-0 ${level.color}`}>{level.label}</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mb-4">
                        {course.description}
                      </p>

                      {/* Progress */}
                      <div className="space-y-2 mb-4">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">التقدم</span>
                          <span className="text-primary">{course.progress}%</span>
                        </div>
                        <Progress value={course.progress} className="h-2" />
                        <p className="text-[10px] text-muted-foreground">
                          {course.completedModules} من {course.modules} وحدات مكتملة
                        </p>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {course.instructor}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {course.duration}
                          </span>
                        </div>
                        <Button variant="default" size="sm" className="text-xs h-7 gap-1.5">
                          <Play className="w-3 h-3" />
                          متابعة
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* Available */}
      {available.length > 0 && (
        <div>
          <h4 className="text-sm text-muted-foreground mb-3 flex items-center gap-2">
            <GraduationCap className="w-3.5 h-3.5 text-muted-foreground" />
            متاحة للبدء
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {available.map((course, i) => {
              const level = levelConfig[course.level];
              return (
                <motion.div
                  key={course.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card className="border-border/50 hover:shadow-md hover:border-primary/30 transition-all group">
                    <CardContent className="p-5">
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <h4 className="text-foreground group-hover:text-primary transition-colors">
                          {course.title}
                        </h4>
                        <Badge className={`text-[10px] shrink-0 ${level.color}`}>{level.label}</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mb-4">
                        {course.description}
                      </p>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {course.instructor}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {course.duration}
                          </span>
                          <Badge variant="outline" className="text-[10px] h-5">
                            {course.modules} وحدات
                          </Badge>
                        </div>
                        <Button variant="outline" size="sm" className="text-xs h-7 gap-1.5">
                          <Play className="w-3 h-3" />
                          بدء
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* Completed */}
      {completed.length > 0 && (
        <div>
          <h4 className="text-sm text-muted-foreground mb-3 flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            مكتملة
          </h4>
          <div className="space-y-3">
            {completed.map((course, i) => {
              const level = levelConfig[course.level];
              return (
                <motion.div
                  key={course.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card className="border-emerald-500/20 bg-emerald-500/5">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-4">
                        <div className="w-9 h-9 rounded-lg bg-emerald-500/10 flex items-center justify-center shrink-0">
                          <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm text-foreground">{course.title}</h4>
                          <p className="text-xs text-muted-foreground">
                            {course.instructor} · {course.duration} · {course.modules} وحدات
                          </p>
                        </div>
                        <Badge className={`text-[10px] shrink-0 ${level.color}`}>{level.label}</Badge>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
