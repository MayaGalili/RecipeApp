import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js';
import { getAuth, RecaptchaVerifier, signInWithPhoneNumber, onAuthStateChanged, signOut } from 'https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js';

const configEl = document.getElementById('firebase-config');
const firebaseConfig = {
  apiKey: configEl.dataset.apiKey, authDomain: configEl.dataset.authDomain,
  projectId: configEl.dataset.projectId, storageBucket: configEl.dataset.storageBucket,
  messagingSenderId: configEl.dataset.messagingSenderId, appId: configEl.dataset.appId,
  measurementId: configEl.dataset.measurementId
};
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const $ = (id) => document.getElementById(id);
let confirmationResult = null;
let verifier = null;
const setStatus = (message) => { $('status').textContent = message; };

async function api(path, options = {}) {
  const user = auth.currentUser;
  if (!user) throw new Error('יש להתחבר מחדש');
  const token = await user.getIdToken();
  const response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json', ...(options.headers || {}), Authorization: `Bearer ${token}` } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || 'הבקשה נכשלה');
  return data;
}

function getDeviceId() {
  let id = localStorage.getItem('recipeapp_device_id');
  if (!id) { id = crypto.randomUUID(); localStorage.setItem('recipeapp_device_id', id); }
  return id;
}

async function showAccount(user) {
  $('signed-out').classList.add('hidden'); $('signed-in').classList.remove('hidden');
  try {
    const profile = await api('/api/account');
    $('account-info').textContent = `מחוברת: ${profile.phoneNumber || user.phoneNumber || 'חשבון מאומת'}`;
    const deviceId = getDeviceId();
    await api('/api/devices', { method: 'POST', body: JSON.stringify({ deviceId, label: navigator.userAgent.includes('Mobile') ? 'דפדפן בטלפון' : 'דפדפן במחשב' }) });
    const result = await api('/api/devices');
    $('device-list').replaceChildren(...result.devices.map(d => { const li = document.createElement('li'); li.textContent = `${d.label || 'מכשיר'}${d.id === deviceId ? ' (המכשיר הזה)' : ''}`; return li; }));
    setStatus('החשבון מחובר בהצלחה.');
  } catch (error) { setStatus(error.message); }
}

$('send-code').addEventListener('click', async () => {
  try {
    const phone = $('phone').value.trim();
    if (!/^\+[1-9]\d{7,14}$/.test(phone)) throw new Error('הכניסי מספר טלפון בפורמט בינלאומי, למשל ‎+972501234567');
    $('send-code').disabled = true; setStatus('שולחת קוד אימות…');
    if (!verifier) verifier = new RecaptchaVerifier(auth, 'recaptcha-container', { size: 'normal' });
    confirmationResult = await signInWithPhoneNumber(auth, phone, verifier);
    $('code-area').classList.remove('hidden'); setStatus('נשלח קוד. בדקי את הודעת ה־SMS.');
  } catch (error) { setStatus(error.message || 'לא ניתן לשלוח קוד כרגע'); if (verifier) { try { await verifier.render(); verifier.clear(); } catch {} verifier = null; } }
  finally { $('send-code').disabled = false; }
});

$('verify-code').addEventListener('click', async () => {
  try { if (!confirmationResult) throw new Error('תחילה בקשי קוד אימות'); await confirmationResult.confirm($('code').value.trim()); setStatus('האימות הצליח.'); }
  catch (error) { setStatus(error.message || 'קוד האימות אינו תקין'); }
});
$('sign-out').addEventListener('click', async () => { await signOut(auth); setStatus('התנתקת מהחשבון.'); });
onAuthStateChanged(auth, user => {
  if (user) showAccount(user);
  else { $('signed-in').classList.add('hidden'); $('signed-out').classList.remove('hidden'); }
});
