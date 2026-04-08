import { motion } from "motion/react";
import {
  ShieldCheck,
  Phone,
  Mail,
  MapPin,
  User,
  Ship,
  CheckCircle2,
  Wallet,
} from "lucide-react";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { clearanceCompanies, currencySymbols } from "./sc-data";

const fmt = (n: number) => new Intl.NumberFormat("ar-SA").format(n);

export function SCClearance() {
  return (
    <div className="grid grid-cols-2 gap-4">
      {clearanceCompanies.map((company, i) => (
        <motion.div
          key={company.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05 }}
        >
          <Card className="border-border/50 hover:border-primary/30 transition-all">
            <CardContent className="p-5 space-y-4">
              {/* Header */}
              <div className="flex items-start gap-3">
                <div className="w-11 h-11 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
                  <ShieldCheck className="w-5 h-5 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-foreground">{company.name}</p>
                  <p className="text-[10px] text-muted-foreground mt-0.5" style={{ direction: "ltr", unicodeBidi: "embed" }}>{company.id}</p>
                </div>
              </div>

              {/* Contact Info */}
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <MapPin className="w-3.5 h-3.5 shrink-0" />
                  <span>{company.address}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Phone className="w-3.5 h-3.5 shrink-0" />
                  <span style={{ direction: "ltr", unicodeBidi: "embed" }}>{company.phone}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Mail className="w-3.5 h-3.5 shrink-0" />
                  <span style={{ direction: "ltr", unicodeBidi: "embed" }}>{company.email}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <User className="w-3.5 h-3.5 shrink-0" />
                  <span>الممثل المعتمد: <span className="text-foreground">{company.authorizedRep}</span></span>
                </div>
              </div>

              {/* Financial Info */}
              <div className="p-3 rounded-lg bg-primary/5 border border-primary/10 space-y-2">
                <div className="flex items-center gap-1.5 text-[10px] text-primary">
                  <Wallet className="w-3 h-3" />
                  المعلومات المالية
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">الرصيد المستحق</span>
                  <span className="text-foreground" style={{ direction: "ltr", unicodeBidi: "embed" }}>
                    {currencySymbols[company.financialCurrency]} {fmt(company.financialBalance)}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">شروط الدفع</span>
                  <span className="text-foreground">{company.paymentTerms}</span>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg bg-blue-500/5 border border-blue-500/10 text-center">
                  <div className="flex items-center justify-center gap-1.5 text-[10px] text-blue-500">
                    <Ship className="w-3 h-3" />
                    حاويات نشطة
                  </div>
                  <p className="text-lg text-blue-500 mt-1">{company.activeContainers}</p>
                </div>
                <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/10 text-center">
                  <div className="flex items-center justify-center gap-1.5 text-[10px] text-emerald-500">
                    <CheckCircle2 className="w-3 h-3" />
                    مكتملة
                  </div>
                  <p className="text-lg text-emerald-500 mt-1">{company.completedContainers}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}