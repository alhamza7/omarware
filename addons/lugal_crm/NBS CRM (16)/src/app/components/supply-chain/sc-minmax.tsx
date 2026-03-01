import { useState } from "react";
import { motion } from "motion/react";
import {
  ArrowDown,
  ArrowUp,
  AlertTriangle,
  CheckCircle2,
  Edit3,
  BarChart3,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
import { minMaxItems } from "./sc-data";

const fmt = (n: number) => new Intl.NumberFormat("ar-SA").format(n);

export function SCMinMax() {
  const [filter, setFilter] = useState<"all" | "below" | "ok" | "above">("all");

  const categorized = minMaxItems.map((item) => {
    const status: "below" | "ok" | "above" =
      item.currentStock < item.minStock ? "below" :
      item.currentStock > item.maxStock ? "above" : "ok";
    const fillPct = Math.min(100, (item.currentStock / item.maxStock) * 100);
    return { ...item, status, fillPct };
  });

  const filtered = filter === "all" ? categorized : categorized.filter((i) => i.status === filter);

  const belowCount = categorized.filter((i) => i.status === "below").length;
  const okCount = categorized.filter((i) => i.status === "ok").length;
  const aboveCount = categorized.filter((i) => i.status === "above").length;

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-3">
        <Card className={`border-border/50 cursor-pointer ${filter === "below" ? "border-red-500/40" : ""}`} onClick={() => setFilter(filter === "below" ? "all" : "below")}>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center">
              <ArrowDown className="w-5 h-5 text-red-500" />
            </div>
            <div>
              <p className="text-2xl text-red-500">{belowCount}</p>
              <p className="text-[10px] text-muted-foreground">أقل من الحد الأدنى</p>
            </div>
          </CardContent>
        </Card>
        <Card className={`border-border/50 cursor-pointer ${filter === "ok" ? "border-emerald-500/40" : ""}`} onClick={() => setFilter(filter === "ok" ? "all" : "ok")}>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            </div>
            <div>
              <p className="text-2xl text-emerald-500">{okCount}</p>
              <p className="text-[10px] text-muted-foreground">ضمن النطاق</p>
            </div>
          </CardContent>
        </Card>
        <Card className={`border-border/50 cursor-pointer ${filter === "above" ? "border-primary/40" : ""}`} onClick={() => setFilter(filter === "above" ? "all" : "above")}>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <ArrowUp className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="text-2xl text-primary">{aboveCount}</p>
              <p className="text-[10px] text-muted-foreground">أعلى من الحد الأقصى</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Table */}
      <Card className="border-border/50">
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-start">الصنف</TableHead>
                <TableHead className="text-start">التصنيف</TableHead>
                <TableHead className="text-center">الحد الأدنى</TableHead>
                <TableHead className="text-center">المخزون الحالي</TableHead>
                <TableHead className="text-center">الحد الأقصى</TableHead>
                <TableHead className="text-start w-40">مستوى المخزون</TableHead>
                <TableHead className="text-center">الحالة</TableHead>
                <TableHead className="text-center">تعديل</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((item, i) => (
                <motion.tr
                  key={item.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.03 }}
                  className="border-b border-border/20"
                >
                  <TableCell className="text-start text-xs text-foreground">{item.name}</TableCell>
                  <TableCell className="text-start">
                    <Badge variant="outline" className="text-[8px] h-4">{item.category}</Badge>
                  </TableCell>
                  <TableCell className="text-center text-xs text-muted-foreground">{fmt(item.minStock)}</TableCell>
                  <TableCell className="text-center">
                    <span className={`text-xs ${
                      item.status === "below" ? "text-red-500" :
                      item.status === "above" ? "text-primary" :
                      "text-emerald-500"
                    }`}>{fmt(item.currentStock)}</span>
                  </TableCell>
                  <TableCell className="text-center text-xs text-muted-foreground">{fmt(item.maxStock)}</TableCell>
                  <TableCell className="text-start">
                    <div className="flex items-center gap-2">
                      <div className="flex-1">
                        <Progress
                          value={item.fillPct}
                          className={`h-2 ${
                            item.status === "below" ? "[&>div]:bg-red-500" :
                            item.status === "above" ? "[&>div]:bg-primary" :
                            "[&>div]:bg-emerald-500"
                          }`}
                        />
                      </div>
                      <span className="text-[9px] text-muted-foreground w-8 text-end">{item.fillPct.toFixed(0)}%</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-center">
                    {item.status === "below" ? (
                      <Badge className="text-[8px] h-4 bg-red-500/15 text-red-500 border-transparent gap-0.5">
                        <AlertTriangle className="w-2.5 h-2.5" />
                        منخفض
                      </Badge>
                    ) : item.status === "above" ? (
                      <Badge className="text-[8px] h-4 bg-primary/15 text-primary border-transparent gap-0.5">
                        <ArrowUp className="w-2.5 h-2.5" />
                        مرتفع
                      </Badge>
                    ) : (
                      <Badge className="text-[8px] h-4 bg-emerald-500/15 text-emerald-500 border-transparent gap-0.5">
                        <CheckCircle2 className="w-2.5 h-2.5" />
                        طبيعي
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-center">
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                      <Edit3 className="w-3 h-3" />
                    </Button>
                  </TableCell>
                </motion.tr>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
