/* global BarcodeDetector */

// منع الزوم في المتصفح على الموبايل
document.addEventListener('gesturestart', function (e) {
  e.preventDefault();
});

document.addEventListener('gesturechange', function (e) {
  e.preventDefault();
});

document.addEventListener('gestureend', function (e) {
  e.preventDefault();
});

const btnScan = document.getElementById("btnScan");
const video = document.getElementById("scanVideo");
const scanStatus = document.getElementById("scanStatus");

let stream = null;
let rafId = null;
let detector = null;
let lastText = null;
let lastAt = 0;
let running = false;

function setStatus(s) {
  if (scanStatus) scanStatus.textContent = s;
}

function supportsBarcodeDetector() {
  return typeof BarcodeDetector !== "undefined";
}

function ensureSecureContextOrExplain() {
  // أغلب المتصفحات تمنع الكاميرا على HTTP (عدا localhost)
  if (window.isSecureContext) return true;
  // بدون رسالة تحذير - نحاول تشغيل الكاميرا بصمت
  return false;
}

async function loadHtml5QrCodeFallback() {
  if (window.Html5Qrcode) return true;
  // تحميل مكتبة fallback بدون build step
  const s = document.createElement("script");
  s.src = "https://unpkg.com/html5-qrcode@2.3.8/minified/html5-qrcode.min.js";
  s.async = true;
  document.head.appendChild(s);
  await new Promise((resolve, reject) => {
    s.onload = resolve;
    s.onerror = reject;
  });
  return !!window.Html5Qrcode;
}

async function initDetector() {
  if (!supportsBarcodeDetector()) return null;
  const formats = [
    "qr_code",
    "code_128",
    "ean_13",
    "ean_8",
    "code_39",
    "itf",
    "upc_a",
    "upc_e",
  ];
  try {
    return new BarcodeDetector({ formats });
  } catch {
    return new BarcodeDetector();
  }
}

async function startCamera() {
  stream = await navigator.mediaDevices.getUserMedia({
    video: { facingMode: "environment" },
    audio: false,
  });
  video.srcObject = stream;
  await video.play();
}

function stopCamera() {
  if (rafId) cancelAnimationFrame(rafId);
  rafId = null;
  if (stream) {
    for (const t of stream.getTracks()) t.stop();
  }
  stream = null;
  lastText = null;
}

async function onDetected(text) {
  const clean = String(text || "").trim();
  if (!clean) return;

  // منع التكرار السريع لنفس القيمة
  const now = Date.now();
  if (clean === lastText && now - lastAt < 1000) return;
  lastText = clean;
  lastAt = now;

  // أوقف المسح مؤقتاً وافتح دايلوج الكمية مباشرة عبر app.js
  pauseScanning();
  if (typeof window.onBarcodeScanned === "function") {
    window.onBarcodeScanned(clean);
  }
}

async function loop() {
  if (!detector) return;
  if (!running) return;
  try {
    const barcodes = await detector.detect(video);
    if (barcodes && barcodes.length) {
      await onDetected(barcodes[0].rawValue);
      // استمر في المسح بدون توقف للسرعة
      if (running) {
        rafId = requestAnimationFrame(loop);
      }
      return;
    }
  } catch {
    // ignore
  }
  rafId = requestAnimationFrame(loop);
}

async function startScanning() {
  if (!ensureSecureContextOrExplain()) return;

  // المسار الأفضل: BarcodeDetector
  if (supportsBarcodeDetector()) {
    detector = await initDetector();
    setStatus("جاري تشغيل الكاميرا...");
    try {
      await startCamera();
      setStatus("جاري المسح...");
      running = true;
      rafId = requestAnimationFrame(loop);
      return;
    } catch (e) {
      setStatus("تعذر تشغيل الكاميرا.");
      // إزالة رسالة التحذير
      stopCamera();
      return;
    }
  }

  // Fallback: html5-qrcode (يدعم QR + Barcodes شائعة)
  setStatus("تحميل ماسح بديل...");
  try {
    const ok = await loadHtml5QrCodeFallback();
    if (!ok) throw new Error("fallback load failed");
  } catch {
    // إزالة رسالة التحذير - فقط تحديث الحالة
    setStatus("الماسح غير متوفر.");
    return;
  }

  setStatus("جاري تشغيل الماسح البديل...");
  running = true;

  // html5-qrcode يحتاج عنصر DOM وليس video مباشرة، لكنه يمكنه استخدام الكاميرا
  // سننشئ container مؤقت فوق الفيديو للحفاظ على UI
  const containerId = "html5qr-container";
  let container = document.getElementById(containerId);
  if (!container) {
    container = document.createElement("div");
    container.id = containerId;
    container.style.width = "100%";
    container.style.borderRadius = "12px";
    container.style.overflow = "hidden";
    // أخفِ فيديو الـ BarcodeDetector لأنه غير مستخدم هنا
    if (video) video.style.display = "none";
    video?.parentElement?.appendChild(container);
  }

  const qr = new window.Html5Qrcode(containerId);
  window.__html5qr = qr;
  try {
    await qr.start(
      { facingMode: "environment" },
      { 
        fps: 30, 
        qrbox: { width: 300, height: 300 },
        aspectRatio: 1.0
      },
      async (decodedText) => {
        if (!running) return;
        await onDetected(decodedText);
      },
      () => {}
    );
    setStatus("جاري المسح...");
  } catch (e) {
    running = false;
    setStatus("تعذر تشغيل الكاميرا.");
    // إزالة رسالة التحذير
  }
}

function pauseScanning() {
  running = false;
  if (rafId) cancelAnimationFrame(rafId);
  rafId = null;
  setStatus("متوقف مؤقتاً...");
}

function resumeScanning() {
  if (!stream || !detector) return startScanning();
  if (running) return;
  running = true;
  setStatus("جاري المسح...");
  rafId = requestAnimationFrame(loop);
}

function stopAll() {
  running = false;
  // أوقف fallback إن كان يعمل
  if (window.__html5qr) {
    window.__html5qr
      .stop()
      .catch(() => {})
      .finally(() => {
        window.__html5qr = null;
      });
  }
  stopCamera();
  setStatus("تم الإيقاف.");
}

// اجعلها متاحة لـ app.js
window.resumeScanning = resumeScanning;
window.pauseScanning = pauseScanning;

// زر واحد: تشغيل/إيقاف
btnScan?.addEventListener("click", () => {
  if (stream) stopAll();
  else startScanning();
});

// ابدأ المسح تلقائياً عند فتح الصفحة (بدون أزرار)
window.addEventListener("load", () => {
  startScanning().catch(() => {});
});


