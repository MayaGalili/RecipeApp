// Share page (recipe not found): language toggle.

// Error page translations
const langTranslations = {
  he: {
    error_title: "מתכון לא נמצא",
    error_message: "המתכון שביקשת לא קיים או נמחק.",
    error_back: "חזור לדף הראשי"
  },
  en: {
    error_title: "Recipe Not Found",
    error_message: "The recipe you requested does not exist or has been deleted.",
    error_back: "Back to Home"
  }
};

let currentLanguage = 'he';

// Language button handlers for error page
const errorLangButtons = document.querySelectorAll('.language-btn');
if (errorLangButtons.length > 0) {
  errorLangButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      currentLanguage = btn.dataset.lang;
      const html = document.documentElement;
      if (currentLanguage === 'he') {
        html.setAttribute('dir', 'rtl');
        html.setAttribute('lang', 'he');
      } else {
        html.setAttribute('dir', 'ltr');
        html.setAttribute('lang', 'en');
      }
      
      const lang = langTranslations[currentLanguage];
      document.getElementById('error-title').textContent = lang.error_title;
      document.getElementById('error-message').textContent = lang.error_message;
      document.getElementById('error-back-link').textContent = lang.error_back;
      
      // Update button states
      document.querySelectorAll('.language-btn').forEach(b => {
        if (b.dataset.lang === currentLanguage) {
          b.classList.add('bg-orange-500', 'text-white');
          b.classList.remove('text-gray-600', 'hover:bg-gray-100');
        } else {
          b.classList.remove('bg-orange-500', 'text-white');
          b.classList.add('text-gray-600', 'hover:bg-gray-100');
        }
      });
    });
  });
}
