# o1ai — نموذج ذكاء اصطناعي متخصص في المحادثة والبرمجة

## ما هو o1ai

o1ai هو منصة ذكاء اصطناعي ويب متخصصة في:
- **المحادثة**: الإجابة عن الأسئلة العامة والمحادثة الذكية
- **البرمجة**: كتابة الأكواد، شرح المفاهيم البرمجية، وتصحيح الأخطاء

## التشغيل

```bash
cd NADOS_AI_V1
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 3131
```

افتح `http://127.0.0.1:3131`

## توصيل نموذج حقيقي

```bash
export NADOS_PROVIDER=openai_compatible
export NADOS_API_URL=https://YOUR_PROVIDER/v1/chat/completions
export NADOS_API_KEY=YOUR_KEY
export NADOS_MODEL=YOUR_MODEL
```

## الهندسة المعمارية

- `frontend/`: واجهة المستخدم (HTML, CSS, JS)
- `backend/app/`: واجهة برمجة التطبيقات FastAPI ومزود الخدمة
- `ai/assets/`: الأصول المحلية (نماذج صوتية)
- `config/`: سجل النماذج
- `scripts/`: أدوات فحص الأصول
- `tests/`: اختبارات

## الملكية / المصدر

تم إنشاء هذه الحزمة من الأرشيف المقدم من المستخدم لمشروع o1ai.
