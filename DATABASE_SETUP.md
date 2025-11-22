# הוראות הגדרת PostgreSQL ב-Render

## שלב 1: יצירת PostgreSQL Database ב-Render

1. היכנסי ל-Render Dashboard: https://dashboard.render.com
2. לחצי על **"New +"** → **"PostgreSQL"**
3. מלאי את הפרטים:
   - **Name**: `recipeapp-db` (או כל שם אחר)
   - **Database**: `recipeapp` (או כל שם אחר)
   - **User**: `recipeapp_user` (או כל שם אחר)
   - **Region**: בחרי את האזור הקרוב אלייך
   - **PostgreSQL Version**: השאירי את הגרסה האחרונה
   - **Plan**: בחרי את התוכנית המתאימה (Free tier זמין)
4. לחצי על **"Create Database"**

## שלב 2: הוספת ה-Database URL ל-Web Service

1. לכי ל-Web Service שלך ב-Render
2. לכי לטאב **"Environment"**
3. לחצי על **"Add Environment Variable"**
4. הוסיפי:
   - **Key**: `DATABASE_URL`
   - **Value**: העתיקי את ה-Connection String מה-PostgreSQL service
     - לכי ל-PostgreSQL service שיצרת
     - תחת **"Connections"** תראי את ה-Connection String
     - העתיקי אותו (נראה כמו: `postgres://user:pass@host:port/dbname`)
5. לחצי **"Save Changes"**

## שלב 3: העברת נתונים קיימים (אופציונלי)

אם יש לך מתכונים קיימים ב-`data/recipes.json`:

1. **מקומי (Local)**:
   ```bash
   # הגדירי את DATABASE_URL ב-.env או כ-environment variable
   export DATABASE_URL="postgresql://user:pass@host:port/dbname"
   
   # הרצי את סקריפט ההעברה
   python3 migrate_to_db.py
   ```

2. **ב-Render** (אחרי deployment):
   - הנתונים יועברו אוטומטית כשהשרת יעלה (אם יש קובץ recipes.json)
   - או תוכלי להריץ את הסקריפט דרך Render Shell

## שלב 4: Deployment

1. ודאי שהקוד שלך ב-GitHub כולל את כל השינויים
2. Push את השינויים:
   ```bash
   git add .
   git commit -m "Migrate to PostgreSQL"
   git push
   ```
3. Render יבצע deployment אוטומטי
4. הטבלאות ייווצרו אוטומטית כשהשרת יעלה בפעם הראשונה

## בדיקה

לאחר ה-deployment:
1. פתחי את האפליקציה
2. נסי להוסיף מתכון חדש
3. המתכון צריך להישמר ולא להיעלם אחרי restart

## הערות חשובות

- **הטבלאות נוצרות אוטומטית** - הקוד יוצר את הטבלאות בפעם הראשונה שהשרת עולה
- **Cascade Delete** - מחיקת מתכון תמחק אוטומטית את התרגומים והקטגוריות שלו
- **Fallback ל-SQLite** - אם אין DATABASE_URL, האפליקציה תשתמש ב-SQLite מקומי (רק לפיתוח)
- **Backup** - Render מבצע backup אוטומטי של ה-PostgreSQL, אבל מומלץ גם לבצע backup ידני מדי פעם

## פתרון בעיות

אם יש שגיאות:
1. ודאי שה-DATABASE_URL מוגדר נכון
2. ודאי שה-PostgreSQL service פעיל
3. בדקי את ה-logs ב-Render Dashboard
4. ודאי שה-requirements.txt כולל את כל החבילות הנדרשות

