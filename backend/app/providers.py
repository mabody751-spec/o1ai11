import os
import re
from typing import Any, Dict, List, Optional
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

    async def code_generate(self, description: str, language: str = "") -> str:
        raise NotImplementedError

    async def code_test(self, code: str, language: str = "") -> str:
        raise NotImplementedError

    async def code_patterns(self, domain: str = "") -> str:
        raise NotImplementedError

    async def explain_algorithm(self, algorithm: str) -> str:
        raise NotImplementedError


class SmartDemoProvider(BaseProvider):
    """V4 Smart provider with extensive programming and conversation knowledge."""

    KNOWLEDGE_BASE = {
        "python": {
            "basics": "Python - لغة متعددة الاستخدام. قوانين: indentation (4 مسافات), snake_case للأسماء، no semicolons. Built-ins: range, enumerate, zip, map, filter, list/dict/set comprehensions.",
            "data_structures": "list: ثابت/متحرك. dict: {key: value}. set: للتمثيل الفريد. tuple: غير قابل للتغيير. deque من collections للـ O(1) operations.",
            "oop": "class Name(BaseClass):. __init__, __str__, __repr__, __len__, __getitem__, __setitem__. Inheritance, polymorphism, encapsulation (_prefix, __mangled). abstractmethod من abc.",
            "decorators": "def decorator(func): @wraps(func) def wrapper: return func(). @property للgetter. @classmethod للكلاس. @staticmethod للدوال العامة.",
            "generators": "yield for lazy evaluation. yield from للكوليكتشن. async generators: async def + yield. Memory efficient للـ streams.",
            "metaprogramming": "metaclass, __new__, __init_subclass__, type() لإنشاء كلاس ديناميكي. Decorator factories.",
            "concurrency": "threading (GIL-bound), multiprocessing (true parallel), asyncio (async/await). aiohttp للـ HTTP, Celery للـ background tasks.",
            "memory": "gc.collect(), sys.getsizeof(), weakref, __slots__ لتقليل memory footprint.",
            "testing": "pytest: fixtures, parametrize, mock, monkeypatch. unittest.mock. test discovery.",
        },
        "javascript": {
            "basics": "ES6+: const/let, arrow functions, template literals `${}`. Scope: let (block), var (function). this: تعتمد على context.",
            "closures": "function outer() { let x; return function inner() { return x; } } — الـ closure يحتفظ بالمتغيرات المغلقة.",
            "prototypes": "الوراثة عبر prototype. Object.create(proto). __proto__ vs prototype. ES6 classes syntactical sugar.",
            "async": "Promise: .then().catch().finally(). async/await. Event loop: microtasks (promises) vs macrotasks (setTimeout, I/O).",
            "modules": "ES modules: import/export. CommonJS: require/module.exports. Dynamic import() للتحميل الكسري.",
            "dom": "querySelector/querySelectorAll. addEventListener. classList, dataset. createElement, appendChild.",
            "modern": "Optional chaining ?., Nullish coalescing ??, Spread (...rest, ...spread), Destructuring.",
        },
        "typescript": {
            "basics": "Static typing. type, interface, enum. Generics <T>. Utility types: Partial<T>, Pick<T>, Omit<T>, Record<K,T>.",
            "types": "Union |, Intersection &, Type guards, Type inference, Literal types.",
            "classes": "public/private/protected. readonly. abstract classes. implement interface.",
        },
        "react": {
            "hooks": "useState, useEffect (cleanup, deps), useRef (DOM access + mutable ref), useMemo (memoize), useCallback (memoize function), useContext (global state), useReducer (complex state), useLayoutEffect (sync after DOM), useTransition (concurrent features).",
            "patterns": "Compound components, render props, custom hooks, HOC, Context + useReducer for state management, error boundaries, lazy loading + Suspense.",
            "performance": "React.memo, useMemo, useCallback, avoid anonymous functions in render, keying list items, virtualize long lists (react-window), code splitting, prefetching.",
            "state_management": "Context API (small), Redux Toolkit (large), Zustand (medium), Jotai (atomic), Recoil (FB), Jotai (minimal).",
            "styling": "CSS Modules, styled-components, emotion, Tailwind CSS, CSS-in-JS.",
        },
        "nextjs": {
            "routing": "File-based routing. /[id].js للديناميك. Catch-all [...slug]. Middleware. Link prefetching.",
            "data_fetching": "SSG (getStaticProps), SSR (getServerSideProps), ISR (revalidate), Client-side (SWR, React Query).",
            "api_routes": "pages/api/. GET, POST, PUT, DELETE. Middleware with CORS, auth.",
        },
        "vue": {
            "composition_api": "setup(), ref(), reactive(), computed(), watch(), watchEffect(). Template refs.",
            "options_vs_composition": "Options API (data, methods, computed, watch). Composition API (setup + refs). Composition preferred for large components.",
        },
        "angular": {
            "concepts": "Components, modules, services, dependency injection, pipes, directives. RxJS for reactive programming. CLI for scaffolding.",
            "rxjs": "Observables, Subject, BehaviorSubject, operators (pipe, map, switchMap, debounceTime).",
        },
        "node": {
            "modules": "CommonJS (require/module.exports) vs ESM (import/export). package.json: type module, exports field. Dynamic import().",
            "streams": "Readable, Writable, Transform, Duplex, PassThrough. pipe() for backpressure. Async iterators.",
            "performance": "Cluster module, worker_threads for CPU. Connection pooling. Caching (Redis). Compression (compression.js).",
            "security": "helmet.js, cors, rate limiting (express-rate-limit), input validation (joi), sanitization (xss), CSRF protection.",
        },
        "express": {
            "middleware": "app.use(), req/res objects. Body parsing (express.json()). Error handling. CORS. Static files. Sessions (express-session).",
            "routing": "Router, route params (:id), query params. Express 4.x vs 5.x differences.",
            "orm": "Prisma (modern), Sequelize (legacy), TypeORM (TypeScript-first), Drizzle (lightweight).",
        },
        "database": {
            "postgresql": "ACID. JSONB columns. CTEs (WITH). Window functions. Indexes (B-tree, Hash, GIN, GiST). Transactions.",
            "mongodb": "Document model. Collections, BSON. Aggregation pipeline. Indexes. Sharding. Replication.",
            "redis": "In-memory. Key-value, strings, hashes, lists, sets, sorted sets. Pub/Sub. Transactions. Lua scripting.",
            "orm_patterns": "Active Record vs Data Mapper. Lazy vs Eager loading. N+1 problem solutions.",
        },
        "sql": {
            "basics": "SELECT, INSERT, UPDATE, DELETE. JOIN types. GROUP BY, HAVING. ORDER BY. LIMIT/OFFSET.",
            "advanced": "CTEs (WITH name AS). Window functions (RANK, ROW_NUMBER, LAG, LEAD). Subqueries. UNION.",
            "optimization": "EXPLAIN ANALYZE. Index types. Normalization (1NF, 2NF, 3NF). Denormalization tradeoffs.",
        },
        "docker": {
            "basics": "Dockerfile, .dockerignore. Images vs containers. Layers. Docker Compose for multi-container.",
            "best_practices": "Multi-stage builds. .dockerignore. Non-root user. Health checks. Environment variables.",
        },
        "cloud": {
            "aws": "EC2 (servers), S3 (storage), Lambda (serverless), RDS (database), ECS/EKS (containers), CloudFront (CDN), API Gateway.",
            "ci_cd": "GitHub Actions, GitLab CI, CircleCI, Jenkins. Test, build, deploy pipeline.",
            "serverless": "AWS Lambda, Firebase Functions, Vercel Functions. Cold start problem.",
        },
        "algorithms": {
            "sorting": "Bubble O(n²), Selection O(n²), Insertion O(n²), Merge O(n log n), Quick O(n log n avg), Heap O(n log n), Counting O(n+k), Radix O(dn).",
            "searching": "Linear O(n), Binary O(log n), DFS, BFS. Hash table O(1) average.",
            "data_structures": "Arrays, Linked Lists, Stacks, Queues, Hash Tables, Trees (BST, AVL, Red-Black), Heaps, Tries, Graphs, Disjoint Sets.",
            "dp": "Memoization (top-down) vs Tabulation (bottom-up). Fibonacci, Knapsack, LIS, LCS. State transition.",
            "graphs": "Traversal: DFS, BFS. Shortest path: Dijkstra, Bellman-Ford, Floyd-Warshall. MST: Kruskal, Prim. Topological sort. SCC (Kosaraju, Tarjan).",
        },
        "system_design": {
            "scalability": "Vertical vs horizontal scaling. Load balancing (L4/L7). CDN. Caching (Redis, Memcached). Database sharding.",
            "patterns": "Microservices vs monolith. API Gateway. Service mesh. Circuit breaker. Retry with backoff. Rate limiting.",
            "messaging": "Message queues (RabbitMQ, Kafka, SQS). Pub/Sub. Event-driven architecture.",
            "storage": "SQL vs NoSQL. OLTP vs OLAP. Data warehousing. Data lakes. CDN for static assets.",
        },
        "web_frontend": {
            "performance": "Lazy loading, code splitting, image optimization, minification, compression (gzip/brotli), caching, CDN.",
            "accessibility": "ARIA labels, semantic HTML, keyboard navigation, screen reader support.",
            "security": "XSS prevention (escaping), CSRF tokens, Content-Security-Policy, secure cookies, CORS.",
        },
    }

    COMMON_PATTERNS = {
        "python": {
            "factory": "from abc import ABC, abstractmethod\n\nclass Product(ABC):\n    @abstractmethod\n    def create(self):\n        pass\n\nclass ConcreteProductA(Product):\n    def create(self):\n        return \"Product A\"\n\nclass Creator(ABC):\n    @abstractmethod\n    def factory_method(self):\n        pass\n\nclass ConcreteCreatorA(Creator):\n    def factory_method(self):\n        return ConcreteProductA()",
            "singleton": "class Singleton:\n    _instance = None\n    def __new__(cls):\n        if cls._instance is None:\n            cls._instance = super().__new__(cls)\n        return cls._instance",
            "observer": "from abc import ABC, abstractmethod\n\nclass Subject:\n    def __init__(self):\n        self._observers = set()\n    def attach(self, observer):\n        self._observers.add(observer)\n    def notify(self):\n        for obs in self._observers:\n            obs.update(self)",
            "builder": "class Builder:\n    def __init__(self):\n        self.product = Product()\n    def set_part_a(self):\n        self.product.parts.append('A')\n        return self\n    def build(self):\n        return self.product",
        },
        "javascript": {
            "observer": "class Subject {\n  constructor() {\n    this.observers = new Set();\n  }\n  subscribe(observer) {\n    this.observers.add(observer);\n  }\n  notify(data) {\n    this.observers.forEach(obs => obs(data));\n  }\n}",
            "factory": "function createProduct(type) {\n  const products = {\n    A: () => new ProductA(),\n    B: () => new ProductB(),\n  };\n  return products[type]?.() || null;\n}",
            "module": "(function() {\n  let privateVar = 0;\n  function privateMethod() { return privateVar; }\n  window.publicAPI = {\n    publicMethod: () => privateMethod() + 1,\n  };\n})();",
        },
    }

    ALGORITHMS = {
        "binary search": "البحث الثنائي: O(log n). يعمل على مصفوفة مرتبة. نقارن العنصر المنتصف مع الهدف، نتخذ نصف المصفوفة.",
        "merge sort": "دمج الترتيب: O(n log n). Divide and conquer. نقسم المصفوفة للنصفين، نرتب كل نصف، ندمجهما.",
        "quick sort": "الترتيب السريع: O(n log n) متوسط، O(n²) أسوأ. نختار pivot، نقسم حوله. In-place.",
        "dijkstra": "البحث عن أقصر مسار: O((V+E) log V) مع heap. من رأس مبدئي لجميع الرؤوس. لا يدعم أوزان سالبة.",
        "bfs": "BFS (البحث بالعرض أولاً): O(V+E). استخدام Queue. مناسب لأقصر مسار في رسم بياني غير وزنه.",
        "dfs": "DFS (البحث في العمق أولاً): O(V+E). استخدام Stack أو recursion. مناسب للكتشاف، الدورات، ترتيب أعمال.",
        "dynamic programming": "برمجة ديناميكية: تحل المشاكل المتداخلة باستخدام تخزين النتائج (memoization/tabulation). Fibonacci, Knapsack, LCS.",
    }

    def __init__(self):
        self.conversation_context = ""

    def _build_context(self, messages: list[dict[str, str]]) -> str:
        recent = messages[-8:] if len(messages) > 8 else messages
        parts = []
        for m in recent[:-1]:
            role = "المستخدم" if m["role"] == "user" else "NADOS AI"
            parts.append(f"{role}: {m['content'][:200]}")
        return "\n".join(parts)

    def _detect_language(self, text: str) -> str:
        patterns = {
            "python": [r'\bdef\s+\w+\s*\(', r'\bimport\s+\w+', r'\bfrom\s+\w+\s+import', r'\bself\.\w+', r'@\w+\s*\(', r'\bprint\s*\(', r'\bclass\s+\w+', r':\s*$'],
            "javascript": [r'\bconst\s+\w+\s*=', r'\bfunction\s+\w+\s*\(', r'=>\s*\{', r'\.then\s*\(', r'console\.log', r'\bvar\s+\w+\s*=', r'let\s+\w+'],
            "typescript": [r':\s*(string|number|boolean|any)\b', r'interface\s+\w+', r'type\s+\w+\s*=', r'<\w+>', r'=>\s*\{'],
            "html": [r'<\w+[^>]*>', r'</\w+>', r'<!DOCTYPE'],
            "css": [r'\.\w+\s*\{', r'@media', r'@keyframes', r'display\s*:'],
            "sql": [r'\bSELECT\b', r'\bINSERT\s+INTO\b', r'\bCREATE\s+TABLE\b', r'\bJOIN\b', r'\bWHERE\b', r'\bFROM\s+\w+'],
            "bash": [r'#!\s*/bin', r'\$\(', r'\becho\b', r'\bgrep\b', r'#!/usr/bin/env'],
            "java": [r'\bpublic\s+(static\s+)?class\b', r'\bSystem\.out\.print', r'import\s+java\.'],
            "cpp": [r'#include\s*<', r'cout\s*<<', r'std::', r'class\s+\w+\s*:'],
            "go": [r'\bfunc\s+\w+\s*\(', r'\bpackage\s+\w+', r'fmt\.Print', r':=\s*'],
            "rust": [r'\bfn\s+\w+\s*\(', r'\blet\s+mut\s+', r'println!\s*\(', r'\bimpl\s+\w+'],
            "c": [r'#include\s*<', r'\bint\s+main\s*\(', r'\bprintf\s*\('],
        }
        for lang, pats in sorted(patterns.items(), key=lambda x: -len(x[1])):
            score = sum(1 for p in pats if re.search(p, text))
            if score >= 2:
                return lang
        return ""

    def _search_knowledge(self, query: str) -> str:
        results = []
        q = query.lower()
        for lang, topics in self.KNOWLEDGE_BASE.items():
            if lang in q:
                for topic, info in topics.items():
                    if any(word in q for word in topic.replace("_", " ").split()):
                        results.append(f"\n**{lang} - {topic.replace('_', ' ').title()}:**\n{info}")
        for pattern_name, patterns in self.COMMON_PATTERNS.items():
            if pattern_name in q:
                results.append(f"\n**نمط {pattern_name.title()} (Python):**\n```python\n{patterns.get(pattern_name, '')}\n```")
        for algo_name, desc in self.ALGORITHMS.items():
            if algo_name in q:
                results.append(f"\n**خوارزمية {algo_name.title()}:**\n{desc}")
        if results:
            return "\n".join(results[:8])
        return ""

    async def chat(self, messages: list[dict[str, str]]) -> str:
        user_msg = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
        if not user_msg.strip():
            return "المرجو إرسال رسالة صالحة."

        context = self._build_context(messages)
        lang = self._detect_language(user_msg)
        knowledge = self._search_knowledge(user_msg)

        response = "**o1ai V4** — ⚡ ذكاء اصطناعي متقدم للمحادثة والبرمجة\n\n"

        if lang:
            response += f"🔍 **تحليل اللغة:** `{lang}`\n\n"

        if context:
            response += f"**السياق الأخير:**\n{context}\n\n"

        if knowledge:
            response += f"📚 **معرفة ذات صلة:**\n{knowledge}\n\n"

        response += f"**تحليلك:** {user_msg}\n\n"
        response += "**يمكنني مساعدتك في:**\n"
        response += "• ✍️ كتابة أكواد بأي لغة (Python, JS, TS, Java, C/C++, Go, Rust, SQL, HTML/CSS, Bash)\n"
        response += "• 🐛 تصحيح الأخطاء البرمجية\n"
        response += "• 📖 شرح المفاهيم والمصطلحات\n"
        response += "• 🏗️ تصميم الأنظمة والهندسة\n"
        response += "• 📊 تحسين الأداء والتحسين\n"
        response += "• 🔍 مراجعة الكود\n"
        response += "• 🧪 كتابة اختبارات وحدة\n"
        response += "• 🎨 نمط التصميم (Design Patterns)\n"
        response += "• 🧮 شرح خوارزميات\مختلفة\n"
        response += "• ☁️ بنية سحابية و DevOps\n\n"
        response += "استخدم أزرار الإجراءات لتحليل الكود مباشرة!"
        return response

    async def code_explain(self, code: str, language: str = "") -> str:
        if not code.strip():
            return "المرجو إرسال كود للتفسير."
        if not language:
            language = self._detect_language(code) or "عام"
        return f"📖 **شرح الكود ({language})**\n\n" \
               f"```{language}\n{code.strip()}\n```\n\n" \
               f"**التحليل:**\n" \
               f"هذا الكود مكتوب بلغة **{language}**. إليك شرح مفصل:\n\n" \
               f"• **الهيكل العام:** يحتوي على `{code.strip().count(chr(10))}` سطراً\n" \
               f"• **المتطلبات:** تأكد من تثبيت المكتبات المطلوبة\n" \
               f"• **نقاط مراجعة:** تحقق من معالجة الأخطاء والـ edge cases\n\n" \
               f"**أسئلة ممكن طرحها:**\n" \
               f"• ما هو الهدف من هذا الكود؟\n" \
               f"• كيف يمكن تحسينه؟\n" \
               f"• ما هي التعقيد الزمني والمكاني؟"

    async def code_format(self, code: str, language: str = "") -> str:
        if not code.strip():
            return "المرجو إرسال كود للتنسيق."
        if not language:
            language = self._detect_language(code) or "python"
        formatted = code.strip().replace("    ", "  ").replace("\t", "  ")
        return f"✨ **كود منسق ({language})**\n\n" \
               f"```{language}\n{formatted}\n```\n\n" \
               f"✅ تم التنسيق. استخدم 2 أو 4 مسافات بشكل متسق."

    async def detect_bugs(self, code: str, language: str = "") -> str:
        if not code.strip():
            return "المرجو إرسال كود للكشف عن الأخطاء."
        if not language:
            language = self._detect_language(code) or "عام"
        bugs = []
        if language in ("python", "general"):
            if "except:" in code:
                bugs.append("⚠️ استخدم `except Exception` بدلاً من bare `except`")
            if "eval(" in code:
                bugs.append("⚠️ استخدام eval() غير آمن")
            if "==" in code and "===" not in code and language in ("python",):
                pass
            if "for i in range" in code and "[i]" in code:
                bugs.append("💡 استخدم list comprehension بدلاً من حلقة for يدوياً")
            if "global " in code:
                bugs.append("⚠️ تجنب استخدام global - استخدم إرجاع القيم")
            if "open(" in code and "with " not in code:
                bugs.append("⚠️ استخدم context manager (with) لملفات الـ I/O")
        if language in ("javascript", "typescript", "general"):
            if "==" in code and "===" not in code:
                bugs.append("⚠️ استخدم === بدلاً من == للمقارنة الصارمة")
            if "var " in code:
                bugs.append("💡 استخدم let أو const بدلاً من var")
            if "console.log" in code:
                bugs.append("ℹ️ احذف console.log قبل النشر")
            if "eval(" in code:
                bugs.append("⚠️ استخدام eval() غير آمن")
            if "document.write" in code:
                bugs.append("⚠️ تجنب document.write لأنه يحذف DOM")
        if not bugs:
            bugs.append("✅ لم يتم اكتشاف أخطاء واضحة في الكود")
        return f"🐛 **فحص الأخطاء ({language})**\n\n" + "\n".join(f"• {b}" for b in bugs) + "\n\n" \
               f"أرسل `مراجعة` للحصول على تحليل أعمق."

    async def code_generate(self, description: str, language: str = "") -> str:
        if not language:
            language = self._detect_language(description) or "python"
        return f"✍️ **كود مُنشأ ({language})**\n\n" \
               f"الوصف: {description}\n\n" \
               f"```{language}\n# TODO: Implement solution based on the description\n# This is a template - customize as needed\n```\n\n" \
               f"💡 نصيحة: قسم المشكلة لخطوات صغيرة ونفذها واحدة تلو الأخرى."

    async def code_test(self, code: str, language: str = "") -> str:
        if not language:
            language = self._detect_language(code) or "python"
        return f"🧪 **اختبارات وحدة ({language})**\n\n" \
               f"```{language}\n# Test cases for the provided code\ndef test_main():\n    assert True  # TODO: Replace with actual test\n\ndef test_edge_cases():\n    assert True  # TODO: Test edge cases\n\nif __name__ == '__main__':\n    test_main()\n    test_edge_cases()\n    print('All tests passed!')\n```\n\n" \
               f"📌 استخدم pytest أو unittest لتشغيل الاختبارات."

    async def code_patterns(self, domain: str = "") -> str:
        domain = domain.lower() if domain else "general"
        result = f"🎨 **أنماط التصميم (Design Patterns) لـ {domain.title()}**\n\n"
        relevant = []
        for lang, patterns in self.COMMON_PATTERNS.items():
            result += f"\n## {lang.title()}\n\n"
            for name, code in patterns.items():
                if any(kw in domain for kw in [lang, "general", "all"]):
                    relevant.append(name)
                    result += f"### {name.title()}\n```{lang}\n{code}\n```\n\n"
        if not relevant:
            result = "🎨 **أنماط التصميم الشائعة:**\n\n"
            result += "• **Creational:** Factory, Abstract Factory, Builder, Prototype, Singleton\n"
            result += "• **Structural:** Adapter, Bridge, Composite, Decorator, Facade, Proxy\n"
            result += "• **Behavioral:** Observer, Strategy, Command, Template, Iterator, State\n"
            result += "• **Architectural:** MVC, MVP, MVVM, Clean Architecture, Microservices\n"
        return result

    async def explain_algorithm(self, algorithm: str) -> str:
        algo_info = self.ALGORITHMS.get(algorithm.lower(), "")
        lang = "الخوارزمية"
        if algo_info:
            return f"🧮 **{algorithm.title()}**\n\n{algo_info}\n\n**التعقيد:** O(log n) - O(n²)\n**استخدامات:** البحث، الترتيب، الرسوم المنحنية"
        return f"🧮 **خوارزمية {algorithm.title()}**\n\nأرسل لي اسم خوارزمية أو موضوع للحصول على شرح مفصل."


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
