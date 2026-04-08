import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { UserPlus, Save } from "lucide-react";

interface CustomerFormData {
  name: string;
  email: string;
  phone: string;
  address: string;
  favoriteFragrance: string;
}

interface CustomerFormProps {
  onSubmit?: (data: CustomerFormData) => void;
}

export function CustomerForm({ onSubmit }: CustomerFormProps) {
  const [formData, setFormData] = useState<CustomerFormData>({
    name: "",
    email: "",
    phone: "",
    address: "",
    favoriteFragrance: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit?.(formData);
    // Reset form
    setFormData({
      name: "",
      email: "",
      phone: "",
      address: "",
      favoriteFragrance: "",
    });
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

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
              أدخل معلومات العميل الجديد في النموذج أدناه
            </CardDescription>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="name">الاسم الكامل</Label>
            <Input
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="أدخل اسم العميل"
              required
              className="transition-all duration-200"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">البريد الإلكتروني</Label>
            <Input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="example@email.com"
              required
              dir="ltr"
              className="transition-all duration-200"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone">رقم الهاتف</Label>
            <Input
              id="phone"
              name="phone"
              type="tel"
              value={formData.phone}
              onChange={handleChange}
              placeholder="+966 5X XXX XXXX"
              required
              dir="ltr"
              className="transition-all duration-200"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="address">العنوان</Label>
            <Input
              id="address"
              name="address"
              value={formData.address}
              onChange={handleChange}
              placeholder="أدخل عنوان العميل"
              required
              className="transition-all duration-200"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="favoriteFragrance">العطر المفضل (اختياري)</Label>
            <Input
              id="favoriteFragrance"
              name="favoriteFragrance"
              value={formData.favoriteFragrance}
              onChange={handleChange}
              placeholder="أدخل اسم العطر المفضل"
              className="transition-all duration-200"
            />
          </div>

          <Button type="submit" className="w-full mt-6 gap-2" size="lg">
            <Save className="w-4 h-4" />
            حفظ معلومات العميل
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
