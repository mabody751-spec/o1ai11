# o1ai V2 — ذكاء اصطناعي متخصص في المحادثة والبرمجة

## ما هو o1ai V2

o1ai هو منصة ذكاء اصطناعي ويب متخصصة في:
- **المحادثة الذكية**: الإجابة عن الأسئلة مع سياق المحادثة
- **البرمجة**: كتابة الأكواد، شرحها، تصحيح الأخطاء، وتنسيقها
- **دعم لغات**: Python, JavaScript, TypeScript, Java, C, C++, Go, Rust, SQL, HTML/CSS, Bash

## الميزات الجديدة V2

- 🧠 **معرفة برمجية مدمجة**: قاعدة معرفة شاملة للغات والتقنيات
- 🔍 **اكتشاف اللغة تلقائياً**: يكتشف لغة الكود تلقائياً
- 📖 **شرح الكود**: شرح مفصل للأكواد البرمجية
- 🐛 **اكتشاف الأخطاء**: فحص الكود لاكتشاف الأخطاء الشائعة
- 🎨 **تنسيق الكود**: تنسيق الأكواد بشكل مرتب
- 📋 **نسخ الكود**: زر نسخ لكتل الكود
- 🔗 **سياق المحادثة**: يتذكر سياق المحادثة السابقة

## التشغيل

```bash
cd NADOS_AI_V1
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 3131
```

افتح `http://127.0.0.1:3131`

## النهايات API

| النهاية | الوصف |
|---------|--------|
| `/` | الواجهة الأمامية |
| `/health` | فحص الحالة |
| `/api/chat` | محادثة عادية |
| `/api/code/explain` | شرح كود |
| `/api/code/format` | تنسيق كود |
| `/api/code/detect-bugs` | اكتشاف أخطاء |
| `/api/context/analyze` | تحليل السياق |
| `/api/models` | قائمة الأصول |
| `/assets/{path}` | أصول صوتية |

## توصيل نموذج حقيقي

```bash
export NADOS_PROVIDER=openai_compatible
export NADOS_API_URL=https://YOUR_PROVIDER/v1/chat/completions
export NADOS_API_KEY=YOUR_KEY
export NADOS_MODEL=YOUR_MODEL
```

## الهندسة المعمارية

- `frontend/`: واجهة المستخدم (HTML, CSS, JS)
- `backend/app/`: واجهة برمجة التطبيقات ومزود الخدمة
- `ai/assets/`: الأصول المحلية (نماذج صوتية)
- `config/`: سجل النماذج
- `scripts/`: أدوات فحص الأصول
- `tests/`: اختبارات

## الملكية / المصدر

تم إنشاء هذه الحزمة من الأرشيف المقدم من المستخدم لمشروع o1ai.
