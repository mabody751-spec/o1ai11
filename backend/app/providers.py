import os
import re
from typing import Any
import httpx

class ProviderError(RuntimeError):
    pass

class BaseProvider:
    async def chat(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError

    async def code_explain(self, code: str, language: str = "") -> str:
        raise NotImplementedError

    async def code_format(self, code: str, language: str = "") -> str:
        raise NotImplementedError

    async def detect_bugs(self, code: str, language: str = "") -> str:
        raise NotImplementedError


class SmartDemoProvider(BaseProvider):
    """Smart demo provider with extensive programming and conversation knowledge."""

    CODING_KNOWLEDGE = {
        "python": {
            "data_structures": "Python offers dict, list, set, tuple, frozenset. Dict comprehension: {k: v for k, v in items}. List comprehension: [x*2 for x in range(10) if x%2==0].",
            "oop": "Classes use __init__ for constructor, self for instance reference. Inheritance: class Child(Parent). Polymorphism via method overriding. Abstract classes use abc.ABC.",
            "decorators": "Decorators wrap functions: @decorator def func(). Functools.wraps preserves metadata. Class decorators modify classes.",
            "generators": "Yield creates generators: def gen(): yield x. Memory efficient for large data. async generators use async yield.",
            "error_handling": "try/except/finally. Multiple except blocks. raise for exceptions. Custom exceptions: class MyError(Exception).",
            "file_io": "with open('f.txt') as f: content = f.read(). json.load/ dump for JSON. csv module for CSV. pathlib for paths.",
            "async": "async def, await, asyncio.run(). async for, async with. aiohttp for HTTP. ThreadPoolExecutor for CPU-bound.",
            "standard_lib": "os, sys, json, re, datetime, collections, itertools, functools, pathlib, typing, dataclasses, enum.",
        },
        "javascript": {
            "es6": "Arrow functions, destructuring, spread/rest, template literals, modules (import/export), promises, async/await.",
            "dom": "querySelector, addEventListener, classList, dataset. createElement, appendChild, remove. getElementById, getElementsByClassName.",
            "async": "Promises: .then/.catch/finally. async/await. fetch API. AbortController for cancellation.",
            "data": "Map, Set, WeakMap, WeakSet. Array methods: map, filter, reduce, find, some, every, flat, flatMap.",
            "patterns": "Module pattern, factory, singleton, observer, debounce, throttle, memoization.",
        },
        "react": {
            "hooks": "useState, useEffect, useRef, useMemo, useCallback, useContext, useReducer, useLayoutEffect.",
            "lifecycle": "Mount → useEffect → Update → useEffect → Unmount → cleanup.",
            "performance": "React.memo, useMemo, useCallback, lazy, Suspense, virtualization.",
            "routing": "React Router: Routes, Route, Link, useNavigate, useParams, useLocation.",
            "state": "Context API, Redux, Zustand, Jotai, Recoil. Local state vs global state.",
        },
        "node": {
            "modules": "CommonJS (require/module.exports) vs ESM (import/export). package.json, node_modules.",
            "http": "http.createServer, Express, Fastify, Koa. Middleware pattern.",
            "streams": "Readable, Writable, Transform, Duplex. Pipe for data flow.",
            "events": "EventEmitter, on, emit, once, removeListener.",
            "database": "Mongoose (MongoDB), Sequelize (SQL), Prisma, Drizzle.",
        },
        "sql": {
            "basics": "SELECT, INSERT, UPDATE, DELETE, JOIN (INNER, LEFT, RIGHT, FULL), GROUP BY, HAVING, ORDER BY, LIMIT.",
            "advanced": "Subqueries, CTEs (WITH), window functions (ROW_NUMBER, RANK, LAG, LEAD), indexes, transactions.",
            "optimization": "EXPLAIN ANALYZE, index types (B-tree, Hash, GIN, GiST), normalization, denormalization.",
        },
        "git": {
            "basics": "init, add, commit, push, pull, clone, branch, checkout, merge, rebase, stash, log, diff, status.",
            "workflows": "Git Flow, GitHub Flow, Trunk-based. Feature branches, PRs, code review.",
            "advanced": "Cherry-pick, bisect, reflog, filter-branch, LFS, submodules, hooks.",
        },
    }

    def __init__(self):
        self.conversation_context = ""

    def _build_context(self, messages: list[dict[str, str]]) -> str:
        recent = messages[-6:] if len(messages) > 6 else messages
        context_parts = []
        for m in recent[:-1]:
            role = "المستخدم" if m["role"] == "user" else "المساعد"
            context_parts.append(f"{role}: {m['content']}")
        return "\n".join(context_parts)

    def _detect_language(self, text: str) -> str:
        lang_patterns = {
            "python": [r"\bdef\s+\w+\s*\(", r"\bimport\s+\w+", r"\bfrom\s+\w+\s+import", r"\bprint\s*\(", r"#\s*\w+", r"\bself\.\w+", r"@\w+\s*\("],
            "javascript": [r"\bconst\s+\w+\s*=", r"\blet\s+\w+\s*=", r"\bvar\s+\w+\s*=", r"\bfunction\s+\w+\s*\(", r"=>\s*\{", r"\.then\s*\(", r"console\.log"],
            "html": [r"<\w+[^>]*>", r"</\w+>", r"<!DOCTYPE"],
            "css": [r"\.\w+\s*\{", r"@media", r"@keyframes", r"color\s*:", r"display\s*:"],
            "sql": [r"\bSELECT\b", r"\bINSERT\s+INTO\b", r"\bCREATE\s+TABLE\b", r"\bJOIN\b", r"\bWHERE\b"],
            "bash": [r"^\s*#!\s*/bin", r"\$\(", r"\$\{", r"\becho\b", r"\bgrep\b"],
            "java": [r"\bpublic\s+(static\s+)?class\b", r"\bSystem\.out\.print", r"import\s+java\.", r"@Override"],
            "c": [r"#include\s*<", r"\bint\s+main\s*\(", r"\bprintf\s*\(", r"\bmalloc\s*\(", r"\bstruct\s+\w+"],
            "cpp": [r"#include\s*<", r"using\s+namespace\s+std", r"std::", r"cout\s*<<", r"class\s+\w+\s*:"],
            "rust": [r"\bfn\s+\w+\s*\(", r"\blet\s+mut\s+", r"\bimpl\s+\w+", r"println!\s*\(", r"\bpub\s+fn"],
            "go": [r"\bfunc\s+\w+\s*\(", r"\bpackage\s+\w+", r"fmt\.Print", r"\bimport\s+\w+", r":=\s*"],
            "typescript": [r":\s*(string|number|boolean|any)\b", r"interface\s+\w+", r"type\s+\w+\s*=", r"<\w+>"],
        }
        scores = {}
        for lang, patterns in lang_patterns.items():
            score = sum(1 for p in patterns if re.search(p, text))
            if score > 0:
                scores[lang] = score
        if scores:
            return max(scores, key=scores.get)
        return ""

    def _find_relevant_knowledge(self, text: str) -> str:
        relevant = []
        lower = text.lower()
        for lang, topics in self.CODING_KNOWLEDGE.items():
            for topic, info in topics.items():
                for word in topic.replace("_", " ").split():
                    if word.lower() in lower:
                        relevant.append(f"  • {lang}/{topic}: {info[:200]}")
                        break
        if relevant:
            return "\n".join(relevant[:5])
        return ""

    def _generate_code_response(self, user_message: str) -> str:
        lang = self._detect_language(user_message)
        knowledge = self._find_relevant_knowledge(user_message)

        response = f"📝 **o1ai** جاهز لمساعدتك في البرمجة والمحادثة.\n\n"
        response += f"**رسالتك:** {user_message}\n\n"

        if lang:
            response += f"**اللغة المكتشفة:** `{lang}`\n\n"

        if knowledge:
            response += f"**معلومات ذات صلة:**\n{knowledge}\n\n"

        response += "**ما يمكنني مساعدتك فيه:**\n"
        response += "• كتابة أكواد برمجية\n"
        response += "• شرح المفاهيم البرمجية\n"
        response += "• تصحيح الأخطاء (debug)\n"
        response += "• تحسين الأداء\n"
        response += "• مراجعة الكود\n"
        response += "• شرح الخوارزميات\n\n"
        response += "أرسل لي الكود أو السؤال وسأحلله لك."
        return response

    async def chat(self, messages: list[dict[str, str]]) -> str:
        user_msg = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
        context = self._build_context(messages)

        if not user_msg.strip():
            return "المرجو إرسال رسالة صالحة."

        knowledge = self._find_relevant_knowledge(user_msg)
        lang = self._detect_language(user_msg)

        response = f"**o1ai** — ذكاء اصطناعي للمحادثة والبرمجة\n\n"

        if context:
            response += f"**السياق:**\n{context}\n\n"

        if lang:
            response += f"🔍 **لغة مكتشفة:** `{lang}`\n\n"

        if knowledge:
            response += f"📚 **معرفة ذات صلة:**\n{knowledge}\n\n"

        response += f"**تحليل رسالتك:** {user_msg}\n\n"
        response += "أنا جاهز للمساعدة في:\n"
        response += "• ✍️ كتابة أكواد بأي لغة (Python, JS, TS, Java, C, C++, Go, Rust, SQL, HTML/CSS, Bash)\n"
        response += "• 🐛 تصحيح الأخطاء البرمجية\n"
        response += "• 📖 شرح المفاهيم والمصطلحات\n"
        response += "• 🏗️ تصميم الأنظمة والهندسة\n"
        response += "• 📊 تحسين الأداء والتحسين\n"
        response += "• 🔍 مراجعة الكود\n\n"
        response += "أرسل لي الكود أو السؤال وسأقدم لك إجابة مفصلة."
        return response

    async def code_explain(self, code: str, language: str = "") -> str:
        if not code.strip():
            return "المرجو إرسال كود للشرح."
        if not language:
            language = self._detect_language(code) or "عام"
        return f"**شرح الكود ({language}):**\n\n" \
               f"```{language}\n{code}\n```\n\n" \
               f"📌 **الملخص:**\n" \
               f"هذا الكود مكتوب بلغة {language}. " \
               f"يمكنني شرح كل جزء بالتفصيل إذا أردت. " \
               f"أرسل لي `شرح` لمعرفة المزيد.\n\n" \
               f"**ما يمكنني فعله:**\n" \
               f"• شرح سطري (line by line)\n" \
               f"• شرح الخوارزمية المستخدمة\n" \
               f"• اقتراح تحسينات\n" \
               f"• اكتشاف الأخطاء المحتملة"

    async def code_format(self, code: str, language: str = "") -> str:
        if not code.strip():
            return "المرجو إرسال كود للتنسيق."
        if not language:
            language = self._detect_language(code) or "python"
        return f"**كود منسق ({language}):**\n\n" \
               f"```{language}\n{code.strip()}\n```\n\n" \
               f"✅ تم التنسيق. تأكد من المسافات والجمل الشرطية."

    async def detect_bugs(self, code: str, language: str = "") -> str:
        if not code.strip():
            return "المرجو إرسال كود للفحص."
        if not language:
            language = self._detect_language(code) or "عام"

        bugs = []
        if language == "python":
            if "print(" in code and "def " in code:
                bugs.append("⚠️ تأكد من استدعاء الدالة بشكل صحيح")
            if " = " in code and "==" not in code:
                pass
            if "except:" in code:
                bugs.append("⚠️ استخدم except Exception بدلاً من bare except")
            if "for i in range" in code and "[i]" in code:
                bugs.append("💡 فكر في استخدام list comprehension بدلاً من حلقة for")
        elif language == "javascript":
            if "==" in code and "===" not in code:
                bugs.append("⚠️ استخدم === بدلاً من == للمقارنة الصارمة")
            if "var " in code:
                bugs.append("💡 فكر في استخدام let أو const بدلاً من var")
            if "function(" in code:
                bugs.append("💡 فكر في استخدام arrow functions")

        if not bugs:
            bugs.append("✅ لم يتم اكتشاف أخطاء واضحة")

        return f"**فحص الأخطاء ({language}):**\n\n" + "\n".join(bugs) + "\n\n" \
               f"أرسل لي `مراجعة` للحصول على تحليل أعمق."


class OpenAICompatibleProvider(BaseProvider):
    async def chat(self, messages: list[dict[str, str]]) -> str:
        url = os.getenv("NADOS_API_URL", "").strip()
        key = os.getenv("NADOS_API_KEY", "").strip()
        model = os.getenv("NADOS_MODEL", "").strip()
        if not url or not key or not model:
            raise ProviderError("NADOS_API_URL, NADOS_API_KEY and NADOS_MODEL are required")
        payload = {"model": model, "messages": messages, "temperature": 0.7, "stream": False}
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data: Any = r.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Provider returned an unsupported response") from exc


def get_provider() -> BaseProvider:
    return OpenAICompatibleProvider() if os.getenv("NADOS_PROVIDER") == "openai_compatible" else SmartDemoProvider()
