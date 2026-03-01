import { useState, useRef } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import {
  UserPlus,
  Save,
  Upload,
  MapPin,
  Star,
  Building2,
  FileText,
  X,
  ImageIcon,
  ShieldCheck,
  File as FileIcon,
  Eye,
} from "lucide-react";

// ── Data ──────────────────────────────────────────────────

export type DocumentType =
  | "national_id"
  | "shop_license"
  | "tax_certificate"
  | "commerce_registration"
  | "residence_card"
  | "other";

export interface CustomerDocument {
  file: File;
  type: DocumentType;
  preview: string;
  name: string;
}

const documentTypeLabels: Record<DocumentType, string> = {
  national_id: "هوية وطنية / بطاقة أحوال",
  shop_license: "إجازة المحل",
  tax_certificate: "شهادة ضريبية",
  commerce_registration: "سجل تجاري",
  residence_card: "بطاقة سكن",
  other: "مستمسك آخر",
};

export interface CustomerFormData {
  customerName: string;
  shopName: string;
  phone: string;
  altPhone: string;
  activityType: string;
  address: string;
  governorate: string;
  city: string;
  district: string;
  landmark: string;
  shopImages: File[];
  customerDocs: CustomerDocument[];
  customerStrength: string;
  dealingMethod: string;
  customerRating: number;
  assignedAgent: string;
  createdAt: string;
  notes: string;
}

const activityTypes = [
  "عطور ومستحضرات تجميل",
  "بخور وعود",
  "هدايا ومناسبات",
  "مول تجاري",
  "سوبرماركت",
  "صيدلية",
  "محل متنوع",
  "بيع بالجملة",
  "أخرى",
];

const governorates = [
  "بغداد",
  "البصرة",
  "نينوى",
  "أربيل",
  "النجف",
  "كربلاء",
  "ذي قار",
  "بابل",
  "ديالى",
  "الأنبار",
  "كركوك",
  "صلاح الدين",
  "واسط",
  "ميسان",
  "المثنى",
  "القادسية",
  "دهوك",
  "السليمانية",
];

const strengthOptions = [
  "ممتاز - عميل رئيسي",
  "جيد جداً - عميل منتظم",
  "جيد - عميل نشط",
  "متوسط - عميل موسمي",
  "ضعيف - عميل جديد",
];

const dealingMethods = [
  "نقدي فوري",
  "آجل - أسبوعي",
  "آجل - شهري",
  "شيكات",
  "تحويل بنكي",
  "مختلط",
];

const agents = [
  { id: "emp-01", name: "سعود المالكي" },
  { id: "emp-02", name: "منى الشهري" },
  { id: "emp-03", name: "عبدالله الحربي" },
  { id: "emp-04", name: "فهد الراشد" },
  { id: "emp-05", name: "ريم الحسين" },
];

interface CustomerFormProps {
  onSubmit?: (data: CustomerFormData) => void;
}

// ── Helpers ───────────────────────────────────────────────
function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

// ── Component ─────────────────────────────────────────────
export function CustomerForm({ onSubmit }: CustomerFormProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const docsInputRef = useRef<HTMLInputElement>(null);

  const [formData, setFormData] = useState<CustomerFormData>({
    customerName: "",
    shopName: "",
    phone: "",
    altPhone: "",
    activityType: "",
    address: "",
    governorate: "",
    city: "",
    district: "",
    landmark: "",
    shopImages: [],
    customerDocs: [],
    customerStrength: "",
    dealingMethod: "",
    customerRating: 0,
    assignedAgent: "",
    createdAt: todayISO(),
    notes: "",
  });

  const [imagePreviews, setImagePreviews] = useState<string[]>([]);

  // ── Handlers ──────────────────────────────────────────
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleSelectChange = (name: string, value: string) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    const newFiles = Array.from(files);
    setFormData((prev) => ({
      ...prev,
      shopImages: [...prev.shopImages, ...newFiles],
    }));
    newFiles.forEach((file) => {
      const reader = new FileReader();
      reader.onload = (ev) => {
        setImagePreviews((prev) => [...prev, ev.target?.result as string]);
      };
      reader.readAsDataURL(file);
    });
  };

  const removeImage = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      shopImages: prev.shopImages.filter((_, i) => i !== index),
    }));
    setImagePreviews((prev) => prev.filter((_, i) => i !== index));
  };

  const handleDocFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    const newFiles = Array.from(files);
    newFiles.forEach((file) => {
      const reader = new FileReader();
      reader.onload = (ev) => {
        setFormData((prev) => ({
          ...prev,
          customerDocs: [
            ...prev.customerDocs,
            {
              file,
              type: "other" as DocumentType,
              preview: ev.target?.result as string,
              name: file.name,
            },
          ],
        }));
      };
      reader.readAsDataURL(file);
    });
  };

  const removeDoc = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      customerDocs: prev.customerDocs.filter((_, i) => i !== index),
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit?.(formData);
    setFormData({
      customerName: "",
      shopName: "",
      phone: "",
      altPhone: "",
      activityType: "",
      address: "",
      governorate: "",
      city: "",
      district: "",
      landmark: "",
      shopImages: [],
      customerDocs: [],
      customerStrength: "",
      dealingMethod: "",
      customerRating: 0,
      assignedAgent: "",
      createdAt: todayISO(),
      notes: "",
    });
    setImagePreviews([]);
  };

  // ── Section wrapper ────────────────────────────────────
  const Section = ({
    icon,
    title,
    children,
  }: {
    icon: React.ReactNode;
    title: string;
    children: React.ReactNode;
  }) => (
    <div className="space-y-4">
      <div className="flex items-center gap-2 pb-2 border-b border-border/30">
        <span className="text-primary">{icon}</span>
        <h3 className="text-sm text-foreground/80">{title}</h3>
      </div>
      {children}
    </div>
  );

  // ── Star Rating ────────────────────────────────────────
  const StarRating = () => (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          onClick={() =>
            setFormData((prev) => ({ ...prev, customerRating: star }))
          }
          className="p-0.5 transition-transform hover:scale-125 cursor-pointer"
        >
          <Star
            className="w-6 h-6 transition-colors"
            style={{
              fill:
                star <= formData.customerRating
                  ? "var(--color-primary)"
                  : "transparent",
              color:
                star <= formData.customerRating
                  ? "var(--color-primary)"
                  : "var(--color-muted-foreground)",
            }}
          />
        </button>
      ))}
      {formData.customerRating > 0 && (
        <span className="text-xs text-muted-foreground ms-2">
          {formData.customerRating === 1 && "منخفض"}
          {formData.customerRating === 2 && "مقبول"}
          {formData.customerRating === 3 && "متوسط"}
          {formData.customerRating === 4 && "مرتفع"}
          {formData.customerRating === 5 && "أولوية قصوى"}
        </span>
      )}
    </div>
  );

  return (
    <Card className="hover:shadow-2xl hover:shadow-primary/10 transition-all duration-300 hover:border-primary/40">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-lg bg-primary/20 border border-primary/40">
            <UserPlus className="w-5 h-5 text-primary" />
          </div>
          <div>
            <CardTitle>إضافة عميل جديد</CardTitle>
            <CardDescription className="mt-1">
              أدخل معلومات العميل الجديد بالتفصيل لإضافته إلى قاعدة البيانات
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* ═══ 1) المعلومات الأساسية ═══ */}
          <Section
            icon={<UserPlus className="w-4 h-4" />}
            title="المعلومات الأساسية"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="customerName">
                  اسم العميل <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="customerName"
                  name="customerName"
                  value={formData.customerName}
                  onChange={handleChange}
                  placeholder="أدخل اسم العميل الكامل"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="shopName">
                  اسم المحل <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="shopName"
                  name="shopName"
                  value={formData.shopName}
                  onChange={handleChange}
                  placeholder="أدخل اسم المحل التجاري"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="phone">
                  رقم الهاتف <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="phone"
                  name="phone"
                  type="tel"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="07XX XXX XXXX"
                  required
                  dir="ltr"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="altPhone">رقم هاتف بديل</Label>
                <Input
                  id="altPhone"
                  name="altPhone"
                  type="tel"
                  value={formData.altPhone}
                  onChange={handleChange}
                  placeholder="07XX XXX XXXX"
                  dir="ltr"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>
                نوع النشاط <span className="text-destructive">*</span>
              </Label>
              <Select
                value={formData.activityType}
                onValueChange={(v) => handleSelectChange("activityType", v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="اختر نوع النشاط" />
                </SelectTrigger>
                <SelectContent>
                  {activityTypes.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </Section>

          {/* ═══ 2) العنوان والموقع ═══ */}
          <Section
            icon={<MapPin className="w-4 h-4" />}
            title="العنوان والموقع"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>
                  المحافظة <span className="text-destructive">*</span>
                </Label>
                <Select
                  value={formData.governorate}
                  onValueChange={(v) => handleSelectChange("governorate", v)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="اختر المحافظة" />
                  </SelectTrigger>
                  <SelectContent>
                    {governorates.map((g) => (
                      <SelectItem key={g} value={g}>
                        {g}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="city">المدينة / المركز</Label>
                <Input
                  id="city"
                  name="city"
                  value={formData.city}
                  onChange={handleChange}
                  placeholder="أدخل المدينة أو المركز"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="district">المنطقة / الحي</Label>
                <Input
                  id="district"
                  name="district"
                  value={formData.district}
                  onChange={handleChange}
                  placeholder="أدخل المنطقة أو الحي"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="address">العنوان التفصيلي</Label>
                <Input
                  id="address"
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  placeholder="شارع، رقم بناية..."
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="landmark">أقرب نقطة دالة</Label>
                <Input
                  id="landmark"
                  name="landmark"
                  value={formData.landmark}
                  onChange={handleChange}
                  placeholder="مثال: مقابل جامع الرحمن"
                />
              </div>
            </div>
          </Section>

          {/* ═══ 3) صورة المحل والموقع ═══ */}
          <Section
            icon={<ImageIcon className="w-4 h-4" />}
            title="صورة المحل والموقع"
          >
            <div className="space-y-3">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={handleFileChange}
                className="hidden"
              />
              <Button
                type="button"
                variant="outline"
                className="gap-2 border-dashed border-2 border-primary/30 hover:border-primary/60 w-full h-20"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-5 h-5 text-primary" />
                <span>اضغط لرفع صور المحل أو الموقع</span>
              </Button>

              {imagePreviews.length > 0 && (
                <div className="flex gap-3 flex-wrap">
                  {imagePreviews.map((src, i) => (
                    <div
                      key={`img-${i}`}
                      className="relative group w-20 h-20 rounded-lg overflow-hidden border border-border/40"
                    >
                      <img
                        src={src}
                        alt={`صورة ${i + 1}`}
                        className="w-full h-full object-cover"
                      />
                      <button
                        type="button"
                        onClick={() => removeImage(i)}
                        className="absolute top-0.5 end-0.5 bg-destructive/80 text-white rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Section>

          {/* ═══ 4) التقييم وطريقة التعامل ═══ */}
          <Section
            icon={<Star className="w-4 h-4" />}
            title="قوة العميل وطريقة التعامل"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>قوة العميل</Label>
                <Select
                  value={formData.customerStrength}
                  onValueChange={(v) =>
                    handleSelectChange("customerStrength", v)
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="اختر مستوى قوة العميل" />
                  </SelectTrigger>
                  <SelectContent>
                    {strengthOptions.map((s) => (
                      <SelectItem key={s} value={s}>
                        {s}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>طريقة التعامل</Label>
                <Select
                  value={formData.dealingMethod}
                  onValueChange={(v) =>
                    handleSelectChange("dealingMethod", v)
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="اختر طريقة التعامل" />
                  </SelectTrigger>
                  <SelectContent>
                    {dealingMethods.map((d) => (
                      <SelectItem key={d} value={d}>
                        {d}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>تقييم العميل (الأولوية)</Label>
              <StarRating />
            </div>
          </Section>

          {/* ═══ 5) المندوب وتاريخ الإنشاء ═══ */}
          <Section
            icon={<Building2 className="w-4 h-4" />}
            title="المندوب وتاريخ الإنشاء"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>اسم المندوب</Label>
                <Select
                  value={formData.assignedAgent}
                  onValueChange={(v) =>
                    handleSelectChange("assignedAgent", v)
                  }
                >
                  <SelectTrigger>
                    <SelectValue placeholder="اختر المندوب المسؤول" />
                  </SelectTrigger>
                  <SelectContent>
                    {agents.map((a) => (
                      <SelectItem key={a.id} value={a.id}>
                        {a.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="createdAt">تاريخ الإنشاء</Label>
                <Input
                  id="createdAt"
                  name="createdAt"
                  type="date"
                  value={formData.createdAt}
                  onChange={handleChange}
                  dir="ltr"
                />
              </div>
            </div>
          </Section>

          {/* ═══ 6) ملاحظات ═══ */}
          <Section
            icon={<FileText className="w-4 h-4" />}
            title="ملاحظات"
          >
            <Textarea
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              placeholder="أدخل أي ملاحظات إضافية عن العميل..."
              rows={3}
            />
          </Section>

          {/* ═══ 7) المستندات ═══ */}
          <Section
            icon={<ShieldCheck className="w-4 h-4" />}
            title="مستمسكات الزبون"
          >
            <p className="text-xs text-muted-foreground -mt-2">
              ارفع صور الهوية، إجازة المحل، السجل التجاري، أو أي مستمسك رسمي
            </p>
            <div className="space-y-4">
              <input
                ref={docsInputRef}
                type="file"
                accept="image/*,.pdf"
                multiple
                onChange={handleDocFileChange}
                className="hidden"
              />
              <Button
                type="button"
                variant="outline"
                className="gap-2 border-dashed border-2 border-primary/30 hover:border-primary/60 w-full h-20"
                onClick={() => docsInputRef.current?.click()}
              >
                <Upload className="w-5 h-5 text-primary" />
                <span>اضغط لرفع المستمسكات (صور أو PDF)</span>
              </Button>

              {formData.customerDocs.length > 0 && (
                <div className="space-y-3">
                  {formData.customerDocs.map((doc, i) => (
                    <div
                      key={`doc-${i}`}
                      className="flex items-center gap-3 p-3 rounded-lg border border-border/40 bg-secondary/20"
                    >
                      {/* Thumbnail or PDF icon */}
                      {doc.file.type.startsWith("image/") ? (
                        <div className="w-14 h-14 rounded-md overflow-hidden border border-border/30 shrink-0">
                          <img
                            src={doc.preview}
                            alt={doc.name}
                            className="w-full h-full object-cover"
                          />
                        </div>
                      ) : (
                        <div className="w-14 h-14 rounded-md border border-border/30 shrink-0 flex items-center justify-center bg-destructive/10">
                          <FileText className="w-6 h-6 text-destructive" />
                        </div>
                      )}

                      {/* Doc info & type selector */}
                      <div className="flex-1 min-w-0 space-y-1.5">
                        <p className="text-xs text-foreground/70 truncate" title={doc.name}>
                          {doc.name}
                        </p>
                        <Select
                          value={doc.type}
                          onValueChange={(v) => {
                            setFormData((prev) => ({
                              ...prev,
                              customerDocs: prev.customerDocs.map((d, idx) =>
                                idx === i ? { ...d, type: v as DocumentType } : d
                              ),
                            }));
                          }}
                        >
                          <SelectTrigger className="h-8 text-xs">
                            <SelectValue placeholder="نوع المستمسك" />
                          </SelectTrigger>
                          <SelectContent>
                            {Object.entries(documentTypeLabels).map(([key, label]) => (
                              <SelectItem key={key} value={key}>
                                {label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-1 shrink-0">
                        {doc.file.type.startsWith("image/") && (
                          <button
                            type="button"
                            onClick={() => window.open(doc.preview, "_blank")}
                            className="p-1.5 rounded-md hover:bg-primary/10 text-primary transition-colors cursor-pointer"
                            title="عرض"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => removeDoc(i)}
                          className="p-1.5 rounded-md hover:bg-destructive/10 text-destructive transition-colors cursor-pointer"
                          title="حذف"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Section>

          {/* ═══ زر الحفظ ═══ */}
          <Button type="submit" className="w-full gap-2" size="lg">
            <Save className="w-4 h-4" />
            حفظ معلومات العميل
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}