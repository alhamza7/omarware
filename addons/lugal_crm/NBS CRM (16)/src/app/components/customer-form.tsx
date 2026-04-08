import { useState, useRef, useCallback } from "react";
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
import { Switch } from "./ui/switch";
import { Badge } from "./ui/badge";
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
  Eye,
  Phone,
  Mail,
  Globe,
  CreditCard,
  Share2,
  Crown,
  Instagram,
  Youtube,
} from "lucide-react";
import type { CreateCustomerPayload } from "../../features/customers/types";

// ── Static data ─────────────────────────────────────────────────────────────

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

const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  national_id:            "هوية وطنية / بطاقة أحوال",
  shop_license:           "إجازة المحل",
  tax_certificate:        "شهادة ضريبية",
  commerce_registration:  "سجل تجاري",
  residence_card:         "بطاقة سكن",
  other:                  "مستمسك آخر",
};

const ACTIVITY_TYPES = [
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

const GOVERNORATES = [
  "بغداد", "البصرة", "نينوى", "أربيل", "النجف",
  "كربلاء", "ذي قار", "بابل", "ديالى", "الأنبار",
  "كركوك", "صلاح الدين", "واسط", "ميسان", "المثنى",
  "القادسية", "دهوك", "السليمانية",
];

const STRENGTH_OPTIONS = [
  "ممتاز - عميل رئيسي",
  "جيد جداً - عميل منتظم",
  "جيد - عميل نشط",
  "متوسط - عميل موسمي",
  "ضعيف - عميل جديد",
];

const DEALING_METHODS = [
  "نقدي فوري",
  "آجل - أسبوعي",
  "آجل - شهري",
  "شيكات",
  "تحويل بنكي",
  "مختلط",
];

const REFERRAL_SOURCES = [
  "مندوب مبيعات",
  "توصية عميل",
  "إنستغرام",
  "تيك توك",
  "واتساب",
  "بحث إنترنت",
  "معرض تجاري",
  "أخرى",
];

const CONTACT_CHANNELS = [
  "واتساب",
  "اتصال هاتفي",
  "إنستغرام",
  "تيك توك",
  "تيليغرام",
  "بريد إلكتروني",
  "زيارة مباشرة",
];

const CONTACT_TIMES = [
  "صباحاً (8 - 12)",
  "ظهراً (12 - 16)",
  "مساءً (16 - 20)",
  "في أي وقت",
];

const AGENTS = [
  { id: "emp-01", name: "سعود المالكي" },
  { id: "emp-02", name: "منى الشهري" },
  { id: "emp-03", name: "عبدالله الحربي" },
  { id: "emp-04", name: "فهد الراشد" },
  { id: "emp-05", name: "ريم الحسين" },
];

// ── Internal form state (flat, UI-friendly) ──────────────────────────────────

interface FormState {
  // Basic
  name:                    string;
  name_ar:                 string;
  phone_1:                 string;
  phone_2:                 string;
  phone_3:                 string;
  email:                   string;
  activity_type:           string;
  // Address
  governorate:             string;
  city:                    string;
  district:                string;
  address:                 string;
  landmark:                string;
  // Shop
  shop_name:               string;
  shop_location:           string;
  shopImages:              File[];
  // Classification
  vip_status:              boolean;
  is_enterprise:           boolean;
  customer_strength:       string;
  dealing_method:          string;
  customer_rating:         number;
  credit_limit:            string;
  preferred_contact_time:  string;
  preferred_contact_channel: string;
  referral_source:         string;
  // Agent
  assigned_agent:          string;
  // Social media
  instagram_handle:        string;
  tiktok_handle:           string;
  whatsapp_number:         string;
  snapchat_handle:         string;
  twitter_handle:          string;
  telegram_handle:         string;
  pinterest_handle:        string;
  youtube_handle:          string;
  // Notes & docs
  notes:                   string;
  customerDocs:            CustomerDocument[];
}

const DEFAULT_FORM: FormState = {
  name:                      "",
  name_ar:                   "",
  phone_1:                   "",
  phone_2:                   "",
  phone_3:                   "",
  email:                     "",
  activity_type:             "",
  governorate:               "",
  city:                      "",
  district:                  "",
  address:                   "",
  landmark:                  "",
  shop_name:                 "",
  shop_location:             "",
  shopImages:                [],
  vip_status:                false,
  is_enterprise:             false,
  customer_strength:         "",
  dealing_method:            "",
  customer_rating:           0,
  credit_limit:              "",
  preferred_contact_time:    "",
  preferred_contact_channel: "",
  referral_source:           "",
  assigned_agent:            "",
  instagram_handle:          "",
  tiktok_handle:             "",
  whatsapp_number:           "",
  snapchat_handle:           "",
  twitter_handle:            "",
  telegram_handle:           "",
  pinterest_handle:          "",
  youtube_handle:            "",
  notes:                     "",
  customerDocs:              [],
};

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Build a full address string from governorate / district / city / address / landmark */
function buildAddress(f: FormState): string {
  return [f.governorate, f.district, f.city, f.address, f.landmark]
    .filter(Boolean)
    .join(" - ");
}

/** Map FormState → CreateCustomerPayload */
function toPayload(f: FormState): CreateCustomerPayload {
  const payload: CreateCustomerPayload = {
    name:    f.name,
    phone_1: f.phone_1,
  };
  if (f.name_ar)                   payload.name_ar                   = f.name_ar;
  if (f.phone_2)                   payload.phone_2                   = f.phone_2;
  if (f.phone_3)                   payload.phone_3                   = f.phone_3;
  if (f.email)                     payload.email                     = f.email;
  if (f.city)                      payload.city                      = f.city;
  const addr = buildAddress(f);
  if (addr)                        payload.address                   = addr;
  if (f.shop_name)                 payload.shop_name                 = f.shop_name;
  if (f.shop_location)             payload.shop_location             = f.shop_location;
  if (f.vip_status)                payload.vip_status                = f.vip_status;
  if (f.is_enterprise)             payload.is_enterprise             = f.is_enterprise;
  if (f.activity_type)             payload.activity_type             = f.activity_type;
  if (f.customer_strength)         payload.customer_strength         = f.customer_strength;
  if (f.dealing_method)            payload.dealing_method            = f.dealing_method;
  if (f.customer_rating)           payload.customer_rating           = f.customer_rating;
  if (f.credit_limit)              payload.credit_limit              = Number(f.credit_limit);
  if (f.preferred_contact_time)    payload.preferred_contact_time    = f.preferred_contact_time;
  if (f.preferred_contact_channel) payload.preferred_contact_channel = f.preferred_contact_channel;
  if (f.referral_source)           payload.referral_source           = f.referral_source;
  if (f.assigned_agent)            payload.assigned_agent            = f.assigned_agent;
  if (f.instagram_handle)          payload.instagram_handle          = f.instagram_handle;
  if (f.tiktok_handle)             payload.tiktok_handle             = f.tiktok_handle;
  if (f.whatsapp_number)           payload.whatsapp_number           = f.whatsapp_number;
  if (f.snapchat_handle)           payload.snapchat_handle           = f.snapchat_handle;
  if (f.twitter_handle)            payload.twitter_handle            = f.twitter_handle;
  if (f.telegram_handle)           payload.telegram_handle           = f.telegram_handle;
  if (f.pinterest_handle)          payload.pinterest_handle          = f.pinterest_handle;
  if (f.youtube_handle)            payload.youtube_handle            = f.youtube_handle;
  if (f.notes)                     payload.notes                     = f.notes;
  return payload;
}

// ── Props ────────────────────────────────────────────────────────────────────

interface CustomerFormProps {
  /** Called with a fully mapped CreateCustomerPayload on valid submit */
  onSubmit?: (payload: CreateCustomerPayload) => void;
}

// ── Component ────────────────────────────────────────────────────────────────

export function CustomerForm({ onSubmit }: CustomerFormProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const docsInputRef = useRef<HTMLInputElement>(null);

  const [form, setForm]           = useState<FormState>(DEFAULT_FORM);
  const [imagePreviews, setImgPreviews] = useState<string[]>([]);

  // ── Field updaters ──────────────────────────────────────────────────────

  /** Generic text / number input handler */
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      const { name, value } = e.target;
      setForm((prev) => ({ ...prev, [name]: value }));
    },
    [],
  );

  /** Select component handler */
  const handleSelect = useCallback((name: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [name]: value }));
  }, []);

  /** Boolean toggle handler */
  const handleToggle = useCallback((name: keyof FormState, checked: boolean) => {
    setForm((prev) => ({ ...prev, [name]: checked }));
  }, []);

  // ── Image upload ────────────────────────────────────────────────────────

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    setForm((prev) => ({ ...prev, shopImages: [...prev.shopImages, ...files] }));
    files.forEach((file) => {
      const reader = new FileReader();
      reader.onload = (ev) =>
        setImgPreviews((prev) => [...prev, ev.target?.result as string]);
      reader.readAsDataURL(file);
    });
  };

  const removeImage = (index: number) => {
    setForm((prev) => ({
      ...prev,
      shopImages: prev.shopImages.filter((_, i) => i !== index),
    }));
    setImgPreviews((prev) => prev.filter((_, i) => i !== index));
  };

  // ── Document upload ─────────────────────────────────────────────────────

  const handleDocChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    files.forEach((file) => {
      const reader = new FileReader();
      reader.onload = (ev) =>
        setForm((prev) => ({
          ...prev,
          customerDocs: [
            ...prev.customerDocs,
            {
              file,
              type:    "other",
              preview: ev.target?.result as string,
              name:    file.name,
            },
          ],
        }));
      reader.readAsDataURL(file);
    });
  };

  const removeDoc = (index: number) =>
    setForm((prev) => ({
      ...prev,
      customerDocs: prev.customerDocs.filter((_, i) => i !== index),
    }));

  const setDocType = (index: number, type: DocumentType) =>
    setForm((prev) => ({
      ...prev,
      customerDocs: prev.customerDocs.map((d, i) =>
        i === index ? { ...d, type } : d,
      ),
    }));

  // ── Submit ──────────────────────────────────────────────────────────────

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit?.(toPayload(form));
    setForm(DEFAULT_FORM);
    setImgPreviews([]);
  };

  // ── Sub-components ──────────────────────────────────────────────────────

  /** Collapsible section wrapper with icon + title */
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
        <h3 className="text-sm font-medium text-foreground/80">{title}</h3>
      </div>
      {children}
    </div>
  );

  /** 1-5 star rating */
  const StarRating = () => (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          onClick={() => setForm((prev) => ({ ...prev, customer_rating: star }))}
          className="p-0.5 transition-transform hover:scale-125 cursor-pointer"
        >
          <Star
            className="w-6 h-6 transition-colors"
            style={{
              fill:  star <= form.customer_rating ? "var(--color-primary)" : "transparent",
              color: star <= form.customer_rating ? "var(--color-primary)" : "var(--color-muted-foreground)",
            }}
          />
        </button>
      ))}
      {form.customer_rating > 0 && (
        <span className="text-xs text-muted-foreground ms-2">
          {["", "منخفض", "مقبول", "متوسط", "مرتفع", "أولوية قصوى"][form.customer_rating]}
        </span>
      )}
    </div>
  );

  // ── Render ──────────────────────────────────────────────────────────────

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

          {/* ══════════════════════════════════════════════════════════
              1. المعلومات الأساسية
          ══════════════════════════════════════════════════════════ */}
          <Section icon={<UserPlus className="w-4 h-4" />} title="المعلومات الأساسية">
            {/* اسم العميل + اسم المحل */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">
                  اسم العميل <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="name"
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  placeholder="أدخل الاسم الكامل"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="name_ar">الاسم بالعربي</Label>
                <Input
                  id="name_ar"
                  name="name_ar"
                  value={form.name_ar}
                  onChange={handleChange}
                  placeholder="الاسم بالحروف العربية"
                />
              </div>
            </div>

            {/* اسم المحل + موقع المحل */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="shop_name">اسم المحل</Label>
                <Input
                  id="shop_name"
                  name="shop_name"
                  value={form.shop_name}
                  onChange={handleChange}
                  placeholder="أدخل اسم المحل التجاري"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="shop_location">موقع المحل (رابط خريطة)</Label>
                <Input
                  id="shop_location"
                  name="shop_location"
                  value={form.shop_location}
                  onChange={handleChange}
                  placeholder="https://maps.google.com/..."
                  dir="ltr"
                />
              </div>
            </div>

            {/* نوع النشاط */}
            <div className="space-y-2">
              <Label>نوع النشاط <span className="text-destructive">*</span></Label>
              <Select
                value={form.activity_type}
                onValueChange={(v) => handleSelect("activity_type", v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="اختر نوع النشاط" />
                </SelectTrigger>
                <SelectContent>
                  {ACTIVITY_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>{t}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* VIP + Enterprise toggles */}
            <div className="flex flex-wrap gap-6 pt-1">
              <div className="flex items-center gap-3">
                <Switch
                  id="vip_status"
                  checked={form.vip_status}
                  onCheckedChange={(c) => handleToggle("vip_status", c)}
                />
                <Label htmlFor="vip_status" className="flex items-center gap-1.5 cursor-pointer">
                  <Crown className="w-4 h-4 text-amber-400" />
                  عميل VIP
                </Label>
              </div>
              <div className="flex items-center gap-3">
                <Switch
                  id="is_enterprise"
                  checked={form.is_enterprise}
                  onCheckedChange={(c) => handleToggle("is_enterprise", c)}
                />
                <Label htmlFor="is_enterprise" className="flex items-center gap-1.5 cursor-pointer">
                  <Building2 className="w-4 h-4 text-blue-400" />
                  شركة / مؤسسة
                </Label>
              </div>
            </div>
          </Section>

          {/* ══════════════════════════════════════════════════════════
              2. معلومات التواصل
          ══════════════════════════════════════════════════════════ */}
          <Section icon={<Phone className="w-4 h-4" />} title="معلومات التواصل">
            {/* الهواتف */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="phone_1">
                  الهاتف الرئيسي <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="phone_1"
                  name="phone_1"
                  type="tel"
                  value={form.phone_1}
                  onChange={handleChange}
                  placeholder="07XX XXX XXXX"
                  required
                  dir="ltr"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone_2">هاتف بديل</Label>
                <Input
                  id="phone_2"
                  name="phone_2"
                  type="tel"
                  value={form.phone_2}
                  onChange={handleChange}
                  placeholder="07XX XXX XXXX"
                  dir="ltr"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone_3">هاتف ثالث</Label>
                <Input
                  id="phone_3"
                  name="phone_3"
                  type="tel"
                  value={form.phone_3}
                  onChange={handleChange}
                  placeholder="07XX XXX XXXX"
                  dir="ltr"
                />
              </div>
            </div>

            {/* البريد الإلكتروني */}
            <div className="space-y-2">
              <Label htmlFor="email" className="flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5" />
                البريد الإلكتروني
              </Label>
              <Input
                id="email"
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                placeholder="example@email.com"
                dir="ltr"
              />
            </div>

            {/* قناة التواصل المفضلة + الوقت المناسب */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>قناة التواصل المفضلة</Label>
                <Select
                  value={form.preferred_contact_channel}
                  onValueChange={(v) => handleSelect("preferred_contact_channel", v)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="اختر القناة المفضلة" />
                  </SelectTrigger>
                  <SelectContent>
                    {CONTACT_CHANNELS.map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>الوقت المناسب للتواصل</Label>
                <Select
                  value={form.preferred_contact_time}
                  onValueChange={(v) => handleSelect("preferred_contact_time", v)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="اختر الوقت المناسب" />
                  </SelectTrigger>
                  <SelectContent>
                    {CONTACT_TIMES.map((t) => (
                      <SelectItem key={t} value={t}>{t}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </Section>

          {/* ══════════════════════════════════════════════════════════
              3. العنوان والموقع
          ══════════════════════════════════════════════════════════ */}
          <Section icon={<MapPin className="w-4 h-4" />} title="العنوان والموقع">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>
                  المحافظة <span className="text-destructive">*</span>
                </Label>
                <Select
                  value={form.governorate}
                  onValueChange={(v) => handleSelect("governorate", v)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="اختر المحافظة" />
                  </SelectTrigger>
                  <SelectContent>
                    {GOVERNORATES.map((g) => (
                      <SelectItem key={g} value={g}>{g}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="city">المدينة / المركز</Label>
                <Input
                  id="city"
                  name="city"
                  value={form.city}
                  onChange={handleChange}
                  placeholder="أدخل المدينة"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="district">المنطقة / الحي</Label>
                <Input
                  id="district"
                  name="district"
                  value={form.district}
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
                  value={form.address}
                  onChange={handleChange}
                  placeholder="شارع، رقم بناية..."
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="landmark">أقرب نقطة دالة</Label>
                <Input
                  id="landmark"
                  name="landmark"
                  value={form.landmark}
                  onChange={handleChange}
                  placeholder="مثال: مقابل جامع الرحمن"
                />
              </div>
            </div>
          </Section>

          {/* ══════════════════════════════════════════════════════════
              4. صورة المحل
          ══════════════════════════════════════════════════════════ */}
          <Section icon={<ImageIcon className="w-4 h-4" />} title="صورة المحل والموقع">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              onChange={handleImageChange}
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
                    <img src={src} alt={`صورة ${i + 1}`} className="w-full h-full object-cover" />
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
          </Section>

          {/* ══════════════════════════════════════════════════════════
              5. وسائل التواصل الاجتماعي
          ══════════════════════════════════════════════════════════ */}
          <Section icon={<Share2 className="w-4 h-4" />} title="وسائل التواصل الاجتماعي">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* WhatsApp */}
              <div className="space-y-2">
                <Label htmlFor="whatsapp_number" className="flex items-center gap-1.5">
                  <span className="text-green-500 font-bold text-xs">WA</span>
                  واتساب
                </Label>
                <Input
                  id="whatsapp_number"
                  name="whatsapp_number"
                  value={form.whatsapp_number}
                  onChange={handleChange}
                  placeholder="07XX XXX XXXX"
                  dir="ltr"
                />
              </div>

              {/* Instagram */}
              <div className="space-y-2">
                <Label htmlFor="instagram_handle" className="flex items-center gap-1.5">
                  <Instagram className="w-3.5 h-3.5 text-pink-500" />
                  إنستغرام
                </Label>
                <Input
                  id="instagram_handle"
                  name="instagram_handle"
                  value={form.instagram_handle}
                  onChange={handleChange}
                  placeholder="@username"
                  dir="ltr"
                />
              </div>

              {/* TikTok */}
              <div className="space-y-2">
                <Label htmlFor="tiktok_handle" className="flex items-center gap-1.5">
                  <span className="font-bold text-xs">TT</span>
                  تيك توك
                </Label>
                <Input
                  id="tiktok_handle"
                  name="tiktok_handle"
                  value={form.tiktok_handle}
                  onChange={handleChange}
                  placeholder="@username"
                  dir="ltr"
                />
              </div>

              {/* Telegram */}
              <div className="space-y-2">
                <Label htmlFor="telegram_handle" className="flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5 text-sky-400" />
                  تيليغرام
                </Label>
                <Input
                  id="telegram_handle"
                  name="telegram_handle"
                  value={form.telegram_handle}
                  onChange={handleChange}
                  placeholder="@username"
                  dir="ltr"
                />
              </div>

              {/* Twitter / X */}
              <div className="space-y-2">
                <Label htmlFor="twitter_handle" className="flex items-center gap-1.5">
                  <span className="font-bold text-xs">𝕏</span>
                  تويتر / X
                </Label>
                <Input
                  id="twitter_handle"
                  name="twitter_handle"
                  value={form.twitter_handle}
                  onChange={handleChange}
                  placeholder="@username"
                  dir="ltr"
                />
              </div>

              {/* Snapchat */}
              <div className="space-y-2">
                <Label htmlFor="snapchat_handle" className="flex items-center gap-1.5">
                  <span className="text-yellow-400 font-bold text-xs">SC</span>
                  سناب شات
                </Label>
                <Input
                  id="snapchat_handle"
                  name="snapchat_handle"
                  value={form.snapchat_handle}
                  onChange={handleChange}
                  placeholder="username"
                  dir="ltr"
                />
              </div>

              {/* Pinterest */}
              <div className="space-y-2">
                <Label htmlFor="pinterest_handle" className="flex items-center gap-1.5">
                  <span className="text-red-500 font-bold text-xs">P</span>
                  بينتريست
                </Label>
                <Input
                  id="pinterest_handle"
                  name="pinterest_handle"
                  value={form.pinterest_handle}
                  onChange={handleChange}
                  placeholder="username"
                  dir="ltr"
                />
              </div>

              {/* YouTube */}
              <div className="space-y-2">
                <Label htmlFor="youtube_handle" className="flex items-center gap-1.5">
                  <Youtube className="w-3.5 h-3.5 text-red-600" />
                  يوتيوب
                </Label>
                <Input
                  id="youtube_handle"
                  name="youtube_handle"
                  value={form.youtube_handle}
                  onChange={handleChange}
                  placeholder="@channel"
                  dir="ltr"
                />
              </div>
            </div>
          </Section>

          {/* ══════════════════════════════════════════════════════════
              6. قوة العميل والتصنيف التجاري
          ══════════════════════════════════════════════════════════ */}
          <Section icon={<Star className="w-4 h-4" />} title="قوة العميل والتصنيف التجاري">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>قوة العميل</Label>
                <Select
                  value={form.customer_strength}
                  onValueChange={(v) => handleSelect("customer_strength", v)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="اختر مستوى قوة العميل" />
                  </SelectTrigger>
                  <SelectContent>
                    {STRENGTH_OPTIONS.map((s) => (
                      <SelectItem key={s} value={s}>{s}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>طريقة التعامل</Label>
                <Select
                  value={form.dealing_method}
                  onValueChange={(v) => handleSelect("dealing_method", v)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="اختر طريقة التعامل" />
                  </SelectTrigger>
                  <SelectContent>
                    {DEALING_METHODS.map((d) => (
                      <SelectItem key={d} value={d}>{d}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>مصدر الإحالة</Label>
                <Select
                  value={form.referral_source}
                  onValueChange={(v) => handleSelect("referral_source", v)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="كيف وصل إلينا؟" />
                  </SelectTrigger>
                  <SelectContent>
                    {REFERRAL_SOURCES.map((r) => (
                      <SelectItem key={r} value={r}>{r}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="credit_limit" className="flex items-center gap-1.5">
                  <CreditCard className="w-3.5 h-3.5" />
                  حد الائتمان (IQD)
                </Label>
                <Input
                  id="credit_limit"
                  name="credit_limit"
                  type="number"
                  min="0"
                  value={form.credit_limit}
                  onChange={handleChange}
                  placeholder="0"
                  dir="ltr"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>تقييم العميل (الأولوية)</Label>
              <StarRating />
            </div>
          </Section>

          {/* ══════════════════════════════════════════════════════════
              7. المندوب والإحالة
          ══════════════════════════════════════════════════════════ */}
          <Section icon={<Building2 className="w-4 h-4" />} title="المندوب المسؤول">
            <div className="space-y-2">
              <Label>اسم المندوب</Label>
              <Select
                value={form.assigned_agent}
                onValueChange={(v) => handleSelect("assigned_agent", v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="اختر المندوب المسؤول" />
                </SelectTrigger>
                <SelectContent>
                  {AGENTS.map((a) => (
                    <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Active social handles summary badge */}
            {(form.instagram_handle || form.tiktok_handle || form.whatsapp_number ||
              form.telegram_handle || form.twitter_handle || form.snapchat_handle ||
              form.pinterest_handle || form.youtube_handle) && (
              <div className="flex flex-wrap gap-2 pt-1">
                {form.instagram_handle  && <Badge variant="secondary">Instagram ✓</Badge>}
                {form.tiktok_handle     && <Badge variant="secondary">TikTok ✓</Badge>}
                {form.whatsapp_number   && <Badge variant="secondary">WhatsApp ✓</Badge>}
                {form.telegram_handle   && <Badge variant="secondary">Telegram ✓</Badge>}
                {form.twitter_handle    && <Badge variant="secondary">X ✓</Badge>}
                {form.snapchat_handle   && <Badge variant="secondary">Snapchat ✓</Badge>}
                {form.pinterest_handle  && <Badge variant="secondary">Pinterest ✓</Badge>}
                {form.youtube_handle    && <Badge variant="secondary">YouTube ✓</Badge>}
              </div>
            )}
          </Section>

          {/* ══════════════════════════════════════════════════════════
              8. ملاحظات
          ══════════════════════════════════════════════════════════ */}
          <Section icon={<FileText className="w-4 h-4" />} title="ملاحظات">
            <Textarea
              name="notes"
              value={form.notes}
              onChange={handleChange}
              placeholder="أدخل أي ملاحظات إضافية عن العميل..."
              rows={3}
            />
          </Section>

          {/* ══════════════════════════════════════════════════════════
              9. مستمسكات الزبون
          ══════════════════════════════════════════════════════════ */}
          <Section icon={<ShieldCheck className="w-4 h-4" />} title="مستمسكات الزبون">
            <p className="text-xs text-muted-foreground -mt-2">
              ارفع صور الهوية، إجازة المحل، السجل التجاري، أو أي مستمسك رسمي
            </p>

            <input
              ref={docsInputRef}
              type="file"
              accept="image/*,.pdf"
              multiple
              onChange={handleDocChange}
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

            {form.customerDocs.length > 0 && (
              <div className="space-y-3">
                {form.customerDocs.map((doc, i) => (
                  <div
                    key={`doc-${i}`}
                    className="flex items-center gap-3 p-3 rounded-lg border border-border/40 bg-secondary/20"
                  >
                    {doc.file.type.startsWith("image/") ? (
                      <div className="w-14 h-14 rounded-md overflow-hidden border border-border/30 shrink-0">
                        <img src={doc.preview} alt={doc.name} className="w-full h-full object-cover" />
                      </div>
                    ) : (
                      <div className="w-14 h-14 rounded-md border border-border/30 shrink-0 flex items-center justify-center bg-destructive/10">
                        <FileText className="w-6 h-6 text-destructive" />
                      </div>
                    )}

                    <div className="flex-1 min-w-0 space-y-1.5">
                      <p className="text-xs text-foreground/70 truncate" title={doc.name}>
                        {doc.name}
                      </p>
                      <Select
                        value={doc.type}
                        onValueChange={(v) => setDocType(i, v as DocumentType)}
                      >
                        <SelectTrigger className="h-8 text-xs">
                          <SelectValue placeholder="نوع المستمسك" />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(DOCUMENT_TYPE_LABELS).map(([key, label]) => (
                            <SelectItem key={key} value={key}>{label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

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
          </Section>

          {/* ══════════════════════════════════════════════════════════
              زر الحفظ
          ══════════════════════════════════════════════════════════ */}
          <Button type="submit" className="w-full gap-2" size="lg">
            <Save className="w-4 h-4" />
            حفظ معلومات العميل
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
