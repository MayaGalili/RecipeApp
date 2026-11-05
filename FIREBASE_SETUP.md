# Firebase phone sign-in setup (RecipeApp)

This update adds a separate `/account` page, Firebase Phone Authentication in the browser, Firebase Admin ID-token verification on Flask, and account/device records. It does **not yet** move favorites, shopping lists, or user-created recipes into per-user cloud storage; those require separate data-model and UI work.

## Firebase Console
1. In Authentication → Sign-in method, enable **Phone**.
2. In Authentication → Settings → Authorized domains, add `recipeapp-lq4d.onrender.com`.
3. In Authentication settings, confirm the SMS region policy allows the countries you intend to support.
4. Add the exact production domain to any API-key HTTP-referrer restrictions you configure.

## Render environment variables
Add these to the Render web service Environment settings:
- `FIREBASE_PROJECT_ID` = `recipe-5f201`
- `FIREBASE_SERVICE_ACCOUNT_JSON` = the full JSON content of a Firebase service-account key for this project. Generate it in Google Cloud/Firebase service accounts. Keep this value only in Render environment variables. Never commit it, place it in the ZIP, or put it in browser JavaScript.
- Ensure `DATABASE_URL` points to persistent PostgreSQL and `SECRET_KEY` is configured.

The service account JSON is a high-privilege server credential. Do not share it in chat or with anyone. If it is exposed, revoke that key and create a new one.

## Deploy and test
1. Deploy the updated project to Render. `db.create_all()` creates the new `users` and `user_devices` tables on startup; existing recipe tables are not changed.
2. Visit `https://recipeapp-lq4d.onrender.com/account`.
3. Sign in with a phone number in international format, e.g. `+972...`; complete the reCAPTCHA and SMS verification.
4. After successful sign-in, the server should create the account and register this browser installation.
5. To link another device, open `/account` there and sign in with the same phone number.

## Important limitations
- This is the account-authentication foundation only. It does not yet synchronize favorites, selected recipes, or shopping lists.
- Browser phone authentication uses Firebase's reCAPTCHA and may require billing/quota or additional provider configuration depending on Firebase settings.
- The browser device identifier is a random installation ID stored in localStorage, not a hardware identifier. Clearing browser data creates a new installation record.
- The existing `/login` remains the separate administrator login.
