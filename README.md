# منصة «بناء وتأثيث»

منصة ويب بلغة Python (Flask) تربط **المالك** و**العميل** و**المطور العقاري** و**المكتب الهندسي** تحت إشراف **مدير النظام**.
تعمل على **PostgreSQL** في الإنتاج (Render) وعلى **SQLite** محليًا.

## المزايا
- 5 أدوار بصلاحيات مستقلة، كل دور يرى ما يخصه فقط.
- رقم طلب تلقائي `BT-2026-00001`.
- ترشيح ذكي لأفضل 3 مكاتب (المدينة 40٪، التقييم 35٪، السعر 25٪).
- سجل تحديثات لكل طلب، وإشعار واتساب/SMS للمستفيد عند كل تحديث.
- صفحة تتبع عامة برقم الطلب وآخر 4 أرقام من الجوال.
- لوحة مؤشرات وإدارة مستخدمين لمدير النظام.

## النشر على Render (مرة واحدة)
1. ارفع محتويات هذا المجلد إلى مستودع جديد على GitHub.
2. في Render: **New → Blueprint** واختر المستودع. Render يقرأ `render.yaml` وينشئ:
   - الموقع `bina-tatheeth`
   - قاعدة البيانات `bina-tatheeth-db` (PostgreSQL) ويربطها بالموقع تلقائيًا.
3. يطلب منك Render قيمة `ADMIN_PASSWORD`: اكتب كلمة مرور قوية لحساب المدير (اسم المستخدم: `admin`).
4. بعد اكتمال البناء يظهر رابط الموقع بالشكل `https://bina-tatheeth.onrender.com`.

أي تعديل ترفعه على GitHub بعد ذلك ينشره Render تلقائيًا.

## متغيرات البيئة
| المتغير | الغرض |
|---|---|
| `DATABASE_URL` | رابط PostgreSQL (يضبطه Render تلقائيًا) |
| `SECRET_KEY` | مفتاح الجلسات (يولّده Render تلقائيًا) |
| `ADMIN_PASSWORD` | كلمة مرور حساب `admin` عند أول تشغيل |
| `NOTIFY_PROVIDER` | `console` (تجريبي) أو `unifonic` أو `twilio` |
| `NOTIFY_CHANNEL` | `whatsapp` أو `sms` |
| `UNIFONIC_APP_SID`, `UNIFONIC_SENDER` | مفاتيح Unifonic |
| `TWILIO_SID`, `TWILIO_TOKEN`, `TWILIO_FROM` | مفاتيح Twilio |
| `DEMO_USERS` | `1` لإضافة حسابات تجريبية في الإنتاج |

## التشغيل المحلي
```bash
pip install -r requirements.txt
python app.py      # http://127.0.0.1:5000
```
محليًا: `admin` و `owner` و `developer` و `office` و `client`، وكلمة المرور `123456`.

## هيكل الملفات
```
app.py            المسارات والصلاحيات والترشيح
database.py       طبقة قاعدة البيانات (PostgreSQL / SQLite) والجداول
notifications.py  إرسال واتساب / SMS
templates/        صفحات الواجهة (عربي RTL)
static/style.css  التصميم
render.yaml       إعداد النشر على Render
```
