# منصة «بناء وتأثيث» — تعليمات Claude Code

منصة ويب (Python/Flask) تربط المالك والمكتب الهندسي والمقاول والمطور العقاري. صاحب المشروع: تركي الألمعي. التواصل والواجهة بالعربية (RTL).

## قبل أي عمل
1. اقرأ `PROGRESS.md` (أين وصلنا والمهمة التالية) ثم `LEARNINGS.md` (القرارات والدروس).
2. لأي عمل على الواجهة: اتبع مهارة `bina-tatheeth-design` في `.claude/skills/`، واستعن بـ `ui-ux-pro-max` للمراجعة.
3. **بعد كل مهمة: أضف ما تعلمناه أو قررناه إلى أعلى `LEARNINGS.md`.**

## هيكل الكود
- `app.py` المسارات والصلاحيات والترشيح والإشعارات.
- `database.py` طبقة موحّدة: PostgreSQL عند وجود `DATABASE_URL`، وإلا SQLite (`platform.db`). اكتب الاستعلامات بعلامة `?`.
- `notifications.py` واتساب/SMS (`NOTIFY_PROVIDER`: console | unifonic | twilio).
- `templates/` قوالب Jinja، و`static/style.css` التصميم.
- `render.yaml` النشر على Render (موقع + PostgreSQL).

## التشغيل والاختبار
```bash
pip install -r requirements.txt
python app.py        # http://127.0.0.1:5000 — admin/owner/developer/office/client بكلمة 123456 (محليًا فقط)
```
اختبر أي تعديل بتسجيل الدخول بالأدوار وإنشاء طلب وتحديثه قبل الرفع.

## النشر
كل رفع إلى الفرع `main` على GitHub ينشره Render تلقائيًا. لا ترفع أسرارًا أو `platform.db`.

## قواعد ثابتة
- لا أرقام أو تقييمات مخترعة في الواجهة؛ الناقص بين [ ].
- رقم الطلب `BT-<السنة>-<5 أرقام>`.
- كل تحديث على الطلب يُسجَّل في `request_updates` ويُرسل إشعارًا للمستفيد.
- كل دور يرى ما يخصه فقط (`visible_requests_query`).
