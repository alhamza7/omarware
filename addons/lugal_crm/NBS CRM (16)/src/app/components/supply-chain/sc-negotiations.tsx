import { useState } from "react";
import { motion } from "motion/react";
import {
  Handshake,
  MessageCircle,
  ArrowDown,
  ArrowUp,
  Minus,
  Send,
  User,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { ScrollArea } from "../ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "../ui/dialog";
import {
  negotiations,
  negStatusConfig,
  currencySymbols,
  type Negotiation,
} from "./sc-data";

const fmt = (n: number) => new Intl.NumberFormat("ar-SA").format(n);

export function SCNegotiations() {
  const [selectedNeg, setSelectedNeg] = useState<Negotiation | null>(null);

  return (
    <div className="space-y-4">
      {/* Negotiation Cards */}
      <div className="grid grid-cols-2 gap-4">
        {negotiations.map((neg, i) => {
          const conf = negStatusConfig[neg.status];
          const diff = neg.lastOffer - neg.targetPrice;
          const gap = ((diff / neg.targetPrice) * 100).toFixed(1);
          return (
            <motion.div
              key={neg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <Card
                className="border-border/50 hover:border-primary/30 transition-all cursor-pointer group"
                onClick={() => setSelectedNeg(neg)}
              >
                <CardContent className="p-4 space-y-3">
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                        <Handshake className="w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <p className="text-sm text-foreground group-hover:text-primary transition-colors">{neg.itemName}</p>
                        <p className="text-[10px] text-muted-foreground">{neg.supplierName}</p>
                      </div>
                    </div>
                    <Badge className={`text-[9px] border-transparent ${conf.color}`}>{conf.label}</Badge>
                  </div>

                  {/* Price Comparison */}
                  <div className="grid grid-cols-3 gap-2">
                    <div className="p-2 rounded bg-muted/30 text-center">
                      <p className="text-[9px] text-muted-foreground">السعر الحالي</p>
                      <p className="text-xs text-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                        {currencySymbols[neg.currency]} {fmt(neg.currentPrice)}
                      </p>
                    </div>
                    <div className="p-2 rounded bg-primary/5 border border-primary/10 text-center">
                      <p className="text-[9px] text-muted-foreground">آخر عرض</p>
                      <p className="text-xs text-primary" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                        {currencySymbols[neg.currency]} {fmt(neg.lastOffer)}
                      </p>
                    </div>
                    <div className="p-2 rounded bg-emerald-500/5 border border-emerald-500/10 text-center">
                      <p className="text-[9px] text-muted-foreground">السعر المستهدف</p>
                      <p className="text-xs text-emerald-500" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                        {currencySymbols[neg.currency]} {fmt(neg.targetPrice)}
                      </p>
                    </div>
                  </div>

                  {/* Gap & Messages */}
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-muted-foreground flex items-center gap-1">
                      <MessageCircle className="w-3 h-3" />
                      {neg.messages.length} رسالة
                    </span>
                    <span className={diff > 0 ? "text-primary" : "text-emerald-500"}>
                      الفجوة: {gap}%
                      {diff > 0 ? <ArrowUp className="w-3 h-3 inline ms-0.5" /> : <Minus className="w-3 h-3 inline ms-0.5" />}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {/* ── Negotiation Detail Dialog ── */}
      <Dialog open={!!selectedNeg} onOpenChange={(open) => { if (!open) setSelectedNeg(null); }}>
        <DialogContent className="!max-w-lg !p-0 !gap-0">
          <DialogTitle className="sr-only">تفاصيل المفاوضة</DialogTitle>
          <DialogDescription className="sr-only">محادثات وعروض المفاوضة</DialogDescription>
          {selectedNeg && (
            <div className="flex flex-col max-h-[80vh]">
              {/* Header */}
              <div className="p-5 border-b border-border/40 bg-gradient-to-l from-primary/5 to-transparent shrink-0">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm text-foreground">{selectedNeg.itemName}</h3>
                    <p className="text-[10px] text-muted-foreground mt-0.5">{selectedNeg.supplierName} • {selectedNeg.division === "europe" ? "أوروبا" : "الصين"}</p>
                  </div>
                  <Badge className={`text-[9px] border-transparent ${negStatusConfig[selectedNeg.status].color}`}>
                    {negStatusConfig[selectedNeg.status].label}
                  </Badge>
                </div>
                {/* Price summary */}
                <div className="grid grid-cols-3 gap-2 mt-3">
                  <div className="p-2 rounded bg-muted/30 text-center">
                    <p className="text-[8px] text-muted-foreground">الحالي</p>
                    <p className="text-xs text-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                      {currencySymbols[selectedNeg.currency]} {fmt(selectedNeg.currentPrice)}
                    </p>
                  </div>
                  <div className="p-2 rounded bg-primary/10 text-center">
                    <p className="text-[8px] text-muted-foreground">آخر عرض</p>
                    <p className="text-xs text-primary" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                      {currencySymbols[selectedNeg.currency]} {fmt(selectedNeg.lastOffer)}
                    </p>
                  </div>
                  <div className="p-2 rounded bg-emerald-500/10 text-center">
                    <p className="text-[8px] text-muted-foreground">المستهدف</p>
                    <p className="text-xs text-emerald-500" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                      {currencySymbols[selectedNeg.currency]} {fmt(selectedNeg.targetPrice)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Messages */}
              <ScrollArea className="flex-1" dir="rtl">
                <div className="p-4 space-y-3">
                  {selectedNeg.messages.map((msg, idx) => {
                    const isUs = msg.sender !== selectedNeg.supplierName.split(" ").pop();
                    return (
                      <div key={idx} className={`flex gap-2.5 ${isUs ? "" : "flex-row-reverse"}`}>
                        <div className="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center shrink-0 text-[9px] text-primary">
                          {msg.sender.slice(0, 2)}
                        </div>
                        <div className={`flex-1 max-w-[80%] ${isUs ? "" : "text-end"}`}>
                          <div className={`inline-block p-3 rounded-lg text-xs ${
                            isUs
                              ? "bg-muted/40 text-foreground rounded-ss-none"
                              : "bg-primary/10 text-foreground rounded-se-none"
                          }`}>
                            {msg.text}
                          </div>
                          <p className="text-[9px] text-muted-foreground mt-1">
                            {msg.sender} • {msg.date}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>

              {/* Input */}
              <div className="p-4 border-t border-border/40 shrink-0">
                <div className="flex gap-2">
                  <textarea
                    className="flex-1 h-10 rounded-md border border-input bg-input-background px-3 py-2 text-xs text-foreground resize-none"
                    placeholder="اكتب رسالة..."
                  />
                  <Button size="sm" className="h-10 px-3">
                    <Send className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
