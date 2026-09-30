const LOCALE_STORAGE_KEY = "diamant_locale";
const DEFAULT_LOCALE = "en";
const SUPPORTED_LOCALES = ["en", "uk"];

const catalogs = {
  en: {
    "app.title": "Diamant ID",
    "brand.home": "Diamant ID home",
    "navigation.primary": "Primary navigation",
    "navigation.verifyPassport": "Verify passport",
    "navigation.signIn": "Sign in",
    "navigation.allReports": "All reports",
    "navigation.demo": "Demo",
    "navigation.experts": "Experts",
    "navigation.references": "References",
    "navigation.marketData": "Market data",
    "navigation.analytics": "Analytics",
    "navigation.profile": "Profile",
    "navigation.newReport": "New report",
    "auth.administrator": "Administrator",
    "auth.gemologist": "Gemologist",
    "auth.user": "User",
    "auth.signOut": "Sign out",
    "menu.open": "Open menu",
    "session.saved": "Your session is preserved. The API is temporarily unavailable.",
    "session.retry": "Try again",
    "footer.privacy": "Privacy policy",
    "footer.documentation": "Documentation",
    "locale.switcher": "Language",
    "locale.en": "English",
    "locale.uk": "Ukrainian",
    "landing.title": "Diamond identification and assessment",
    "landing.subtitle": "Reliable passport verification and expert diamond reports in one workspace.",
    "landing.verifyPassport": "Verify passport",
    "landing.signIn": "Sign in to work with reports",
    "landing.heroAlt": "Diamond held in gemological tweezers",
    "landing.passportTitle": "Verification you can trust",
    "landing.passportDescription": "A public passport opens from a direct link, a QR-code link, or a code on the report page. Enter only the code here; an internal report number is not used for this.",
    "landing.passportCode": "Public passport code",
    "landing.passportPlaceholder": "Enter the code from the report page",
    "landing.verify": "Verify",
    "landing.principles": "Diamant ID capabilities",
    "landing.expertReports": "Expert reports",
    "landing.expertReportsText": "Consistent recording of stone characteristics and assessment results.",
    "landing.dataControl": "Data control",
    "landing.dataControlText": "A clear distinction between an expert conclusion and a calculated system result.",
    "landing.passportVerification": "Passport verification",
    "landing.passportVerificationText": "A dedicated public route for issued reports after passport and QR issuance.",
    "login.title": "Sign in",
    "login.subtitle": "Please authenticate to continue",
    "login.username": "Username",
    "login.password": "Password",
    "login.submit": "Sign in",
    "login.error": "Sign-in failed: {message}",
    "passport.invalidInternalNumber": "An internal report number is not a public passport code.",
    "passport.invalidCode": "Enter the public passport code shown on the report page.",
    "wizard.notSpecified": "Not specified",
    "wizard.requiredStep": "Complete the required fields in step {step}.",
    "wizard.referencesFailed": "Reference data could not be loaded: {message}",
    "wizard.noFile": "No file selected",
    "wizard.noMarketReference": "No system reference is available for the entered characteristics.",
    "wizard.referenceSnapshot": "{provider} · snapshot #{snapshot}. The value will be recorded when the draft is saved.",
    "wizard.snapshotValue": "{currency} {amount} · snapshot #{snapshot}",
    "wizard.startedNew": "A new unsaved entry has started.",
    "wizard.restored": "Unsaved entry restored. Add attachments again.",
    "wizard.leaveNavigation": "The entered data has not become a server draft. It remains only in this tab and can be explicitly restored after you return.",
    "wizard.leaveLogout": "The entered data has not become a server draft. After signing out it remains only in this tab and can be explicitly restored only after you sign in again with this account.",
    "wizard.signOut": "Sign out",
    "wizard.go": "Go",
    "wizard.saving": "Saving draft…",
    "wizard.saveFailed": "Draft could not be saved: {message}",
    "wizard.pageTitle": "New report",
    "wizard.pageSubtitle": "Create an expert stone-report draft.",
    "wizard.steps": "Report creation steps",
    "wizard.step1Short": "1. Basics",
    "wizard.step1": "1. Identification and 4C",
    "wizard.step2Short": "2. Geometry",
    "wizard.step2": "2. Geometry (IDC)",
    "wizard.step3Short": "3. Conclusion",
    "wizard.step3": "3. Conclusion and media",
    "wizard.identification": "Identification",
    "wizard.nextReportId": "Next report number",
    "wizard.idServerAssigned": "The server assigns the final number when saving.",
    "wizard.examinationDate": "Examination / assessment date",
    "wizard.shape": "Shape",
    "wizard.origin": "Origin",
    "wizard.fourCs": "4C characteristics",
    "wizard.caratWeight": "Carat weight",
    "wizard.color": "Color",
    "wizard.clarity": "Clarity",
    "wizard.loadingReference": "Loading reference data…",
    "wizard.dimensions": "Dimensions",
    "wizard.length": "Length (mm)", "wizard.width": "Width (mm)", "wizard.depth": "Depth (mm)",
    "wizard.cuttingParameters": "Cutting parameters (IDC)", "wizard.table": "Table (%)", "wizard.totalDepth": "Total depth (%)",
    "wizard.crownAngle": "Crown angle (°)", "wizard.pavilionAngle": "Pavilion angle (°)", "wizard.girdle": "Girdle thickness", "wizard.culet": "Culet size",
    "wizard.finish": "Finish", "wizard.polish": "Polish", "wizard.symmetry": "Symmetry", "wizard.fluorescence": "Fluorescence",
    "wizard.expertConclusion": "Expert conclusion", "wizard.treatment": "Treatment indication", "wizard.identificationStatus": "Identification confidence",
    "wizard.identificationMethod": "Identification method", "wizard.identificationConclusion": "Identification conclusion", "wizard.expertComment": "Expert comment",
    "wizard.media": "Media", "wizard.plotting": "Plotting diagram", "wizard.stonePhoto": "Stone photo", "wizard.chooseFile": "Choose file",
    "wizard.privateMediaHelp": "JPEG, PNG or WebP, up to 10 MB. Stored privately.", "wizard.back": "Back", "wizard.clearEntry": "Clear entry", "wizard.saveDraft": "Save draft", "wizard.next": "Next",
    "wizard.restoreTitle": "Restore unsaved entry?", "wizard.restoreDescription": "Unsaved data for this tab was found. It was not sent to the server.", "wizard.restoreMedia": "Attachments are not restored — add files again after restoring.", "wizard.startNew": "Start over", "wizard.restore": "Restore",
    "wizard.clearTitle": "Clear unsaved entry?", "wizard.close": "Close", "wizard.clearDescription": "This tab's data will be removed from the form and local storage. No saved report will change.", "wizard.cancel": "Cancel", "wizard.stay": "Stay", "wizard.leaveTitle": "Leave wizard?",
    "detail.privateReport": "Private report", "detail.loadingReport": "Loading report…", "detail.subtitle": "Data, expert conclusion, attachments, and change history.", "detail.backToReports": "Back to all reports", "detail.editDraft": "Edit draft", "detail.saveChanges": "Save changes", "detail.reportState": "Report state", "detail.transitionReason": "Status-change comment", "detail.transitionReasonPlaceholder": "Optional, but recommended when returning or voiding", "detail.narrativeQuality": "Text-field check", "detail.narrativeHelp": "Automated completion signals do not assess the professional conclusion and do not block saving.", "detail.loading": "Loading…", "detail.marketReference": "Market reference value", "detail.marketReferenceHelp": "A market reference is not an expert, sale, or transaction price.", "detail.attachments": "Attachments", "detail.history": "Change history",
    "dashboard.statusDraft": "Draft", "dashboard.statusReview": "In review", "dashboard.statusIssued": "Issued", "dashboard.statusVoid": "Voided", "dashboard.notSold": "Not sold", "dashboard.sold": "Sold",
    "dashboard.view": "View", "dashboard.edit": "Edit", "dashboard.editDraftOnly": "Editing is available only for a draft", "dashboard.print": "Print", "dashboard.loading": "Loading reports…", "dashboard.empty": "No reports match the current conditions.", "dashboard.loadFailed": "Reports could not be loaded. Refresh the page or try again later.",
    "dashboard.title": "All reports", "dashboard.subtitle": "Manage certificates and assessments.", "dashboard.newReport": "New report", "dashboard.search": "Search by report number", "dashboard.filters": "Filters", "dashboard.allReportStatuses": "All report statuses", "dashboard.allSaleStatuses": "All sale statuses", "dashboard.allExperts": "All experts",
    "dashboard.reportStatus": "Report status", "dashboard.saleStatus": "Sale status", "dashboard.expert": "Expert", "dashboard.shape": "Shape", "dashboard.any": "Any", "dashboard.carat": "Carat", "dashboard.from": "From", "dashboard.to": "To", "dashboard.color": "Color", "dashboard.clarity": "Clarity", "dashboard.cut": "Cut", "dashboard.referenceUsd": "Reference value (USD)", "dashboard.createdFrom": "Created from", "dashboard.createdTo": "Created to", "dashboard.apply": "Apply", "dashboard.clear": "Clear", "dashboard.referenceNote": "Reference values (USD) are generated for new or changed drafts by the configured provider (currently OpenFacet). SYS means a system reference value and ADM means an administrator-confirmed applicable reference; the source is always shown. This is not an expert, sale, or transaction price. A UAH equivalent is added only when the NBU exchange rate is enabled and is fixed at creation.",
    "dashboard.reportId": "Report ID", "dashboard.date": "Date", "dashboard.caratColumn": "Carat (ct)", "dashboard.priceUsd": "Value (USD)", "dashboard.actions": "Actions", "dashboard.pagination": "Report pagination", "dashboard.sortReportId": "Sort by report ID", "dashboard.sortDate": "Sort by date", "dashboard.sortShape": "Sort by shape", "dashboard.sortCarat": "Sort by carat", "dashboard.sortColor": "Sort by color", "dashboard.sortClarity": "Sort by clarity", "dashboard.sortCut": "Sort by cut", "dashboard.sortPrice": "Sort by reference value", "dashboard.sortReportStatus": "Sort by report status", "dashboard.sortSaleStatus": "Sort by sale status",
    "dashboard.openActions": "Open actions for report {reportId}", "dashboard.referenceTypeDemo": "Demo reference value", "dashboard.referenceTypeSystem": "System reference value", "dashboard.referenceTypeAdmin": "Administrator-confirmed reference value", "dashboard.referenceExplanation": "Reference value explanation for report {reportId}", "dashboard.referenceType": "Type", "dashboard.provider": "Provider", "dashboard.providerSnapshot": "Provider snapshot", "dashboard.observed": "Observed", "dashboard.equivalent": "Equivalent", "dashboard.nbuRate": "NBU rate", "dashboard.notAvailableForDemo": "Not available for synthetic demo", "dashboard.notCalculatedForDemo": "Not calculated for synthetic demo", "dashboard.notApplicableForDemo": "Not applicable for synthetic demo", "dashboard.nbuRateValue": "{rate} UAH/USD · {date} · snapshot #{snapshot}", "dashboard.otherReferences": "Other available reference values:", "dashboard.demoReferenceWarning": "Synthetic demo value; it is not a market, expert, sale, or transaction price.", "dashboard.systemReferenceWarning": "Calculated by the system from the latest approved snapshot; it is not an expert, sale, or transaction price.", "dashboard.adminReferenceWarning": "Applicability was confirmed by an administrator; it is not an expert, sale, or transaction price.", "dashboard.openPrivateReport": "Open private report view", "dashboard.firstPage": "First page", "dashboard.previousPage": "Previous page", "dashboard.nextPage": "Next page", "dashboard.lastPage": "Last page",
    "narrative.fields": "Text fields", "narrative.identificationMethod": "Identification method", "narrative.identificationConclusion": "Identification conclusion", "narrative.expertComment": "Expert comment", "narrative.statusTransition": "Status-change event without a comment", "narrative.show": "Show:", "narrative.showFields": "Show text fields", "narrative.empty": "Empty", "narrative.filled": "Filled", "narrative.demoNote": "Synthetic lifecycle has no text comments, so this option is not modeled.", "narrative.realNote": "The status-change event is checked in the selected date range.",
  },
  uk: {
    "app.title": "Diamant ID",
    "brand.home": "Головна Diamant ID",
    "navigation.primary": "Основна навігація",
    "navigation.verifyPassport": "Перевірити паспорт",
    "navigation.signIn": "Увійти",
    "navigation.allReports": "Всі звіти",
    "navigation.demo": "Демо",
    "navigation.experts": "Експерти",
    "navigation.references": "Довідники",
    "navigation.marketData": "Ринкові дані",
    "navigation.analytics": "Аналітика",
    "navigation.profile": "Профіль",
    "navigation.newReport": "Новий звіт",
    "auth.administrator": "Адміністратор",
    "auth.gemologist": "Експерт",
    "auth.user": "Користувач",
    "auth.signOut": "Вийти",
    "menu.open": "Відкрити меню",
    "session.saved": "Сеанс збережено. API тимчасово недоступний.",
    "session.retry": "Спробувати знову",
    "footer.privacy": "Політика конфіденційності",
    "footer.documentation": "Документація",
    "locale.switcher": "Мова",
    "locale.en": "Англійська",
    "locale.uk": "Українська",
    "landing.title": "Ідентифікація та оцінювання діамантів",
    "landing.subtitle": "Надійна перевірка паспортів та експертні звіти про діаманти — в одному робочому середовищі.",
    "landing.verifyPassport": "Перевірити паспорт",
    "landing.signIn": "Увійти для роботи зі звітами",
    "landing.heroAlt": "Діамант у гемологічному пінцеті",
    "landing.passportTitle": "Перевірка, якій можна довіряти",
    "landing.passportDescription": "Публічний паспорт відкривається за прямим посиланням, посиланням із QR-коду або кодом зі сторінки звіту. Тут введіть лише код; внутрішній номер звіту для цього не використовується.",
    "landing.passportCode": "Код публічного паспорта",
    "landing.passportPlaceholder": "Введіть код зі сторінки звіту",
    "landing.verify": "Перевірити",
    "landing.principles": "Можливості Diamant ID",
    "landing.expertReports": "Експертні звіти",
    "landing.expertReportsText": "Послідовна фіксація характеристик каменю та результатів оцінювання.",
    "landing.dataControl": "Контроль даних",
    "landing.dataControlText": "Чітке розмежування експертного висновку й розрахункового результату системи.",
    "landing.passportVerification": "Перевірка паспорта",
    "landing.passportVerificationText": "Окремий публічний маршрут для виданих звітів — після реалізації паспорта й QR.",
    "login.title": "Вхід у систему",
    "login.subtitle": "Будь ласка, авторизуйтесь",
    "login.username": "Логін",
    "login.password": "Пароль",
    "login.submit": "Увійти",
    "login.error": "Помилка входу: {message}",
    "passport.invalidInternalNumber": "Внутрішній номер звіту не є кодом публічного паспорта.",
    "passport.invalidCode": "Введіть код публічного паспорта зі сторінки звіту.",
    "wizard.notSpecified": "Не зазначено",
    "wizard.requiredStep": "Заповніть коректно обов’язкові поля кроку {step}.",
    "wizard.referencesFailed": "Не вдалося завантажити довідники: {message}",
    "wizard.noFile": "Файл не вибрано",
    "wizard.noMarketReference": "Немає доступного системного орієнтиру для введених характеристик.",
    "wizard.referenceSnapshot": "{provider} · знімок #{snapshot}. Значення буде зафіксовано під час збереження чернетки.",
    "wizard.snapshotValue": "{currency} {amount} · знімок #{snapshot}",
    "wizard.startedNew": "Почато нове незбережене введення.",
    "wizard.restored": "Незбережене введення відновлено. Вкладення додайте повторно.",
    "wizard.leaveNavigation": "Введені дані ще не стали чернеткою на сервері. Вони залишаться лише в цій вкладці, і після повернення їх можна буде явно відновити.",
    "wizard.leaveLogout": "Введені дані ще не стали чернеткою на сервері. Після виходу вони залишаться лише в цій вкладці та будуть доступні для явного відновлення лише після повторного входу цим самим обліковим записом.",
    "wizard.signOut": "Вийти",
    "wizard.go": "Перейти",
    "wizard.saving": "Збереження чернетки…",
    "wizard.saveFailed": "Не вдалося зберегти чернетку: {message}",
    "wizard.pageTitle": "Новий звіт",
    "wizard.pageSubtitle": "Створення чернетки експертного звіту про камінь.",
    "wizard.steps": "Кроки створення звіту",
    "wizard.step1Short": "1. Основне",
    "wizard.step1": "1. Ідентифікація та 4C",
    "wizard.step2Short": "2. Геометрія",
    "wizard.step2": "2. Геометрія (IDC)",
    "wizard.step3Short": "3. Висновок",
    "wizard.step3": "3. Висновок та медіа",
    "wizard.identification": "Ідентифікація",
    "wizard.nextReportId": "Наступний номер звіту",
    "wizard.idServerAssigned": "Номер остаточно присвоюється сервером під час збереження.",
    "wizard.examinationDate": "Дата дослідження / оцінки",
    "wizard.shape": "Форма",
    "wizard.origin": "Походження",
    "wizard.fourCs": "Характеристики 4C",
    "wizard.caratWeight": "Вага",
    "wizard.color": "Колір",
    "wizard.clarity": "Чистота",
    "wizard.loadingReference": "Завантаження довідника…",
    "wizard.dimensions": "Розміри", "wizard.length": "Довжина (мм)", "wizard.width": "Ширина (мм)", "wizard.depth": "Висота (мм)",
    "wizard.cuttingParameters": "Параметри огранювання (IDC)", "wizard.table": "Таблиця (%)", "wizard.totalDepth": "Загальна глибина (%)",
    "wizard.crownAngle": "Кут корони (°)", "wizard.pavilionAngle": "Кут павільйону (°)", "wizard.girdle": "Товщина рундиста", "wizard.culet": "Калета",
    "wizard.finish": "Якість обробки", "wizard.polish": "Поліровка", "wizard.symmetry": "Симетрія", "wizard.fluorescence": "Флуоресценція",
    "wizard.expertConclusion": "Висновок експерта", "wizard.treatment": "Ознаки обробки", "wizard.identificationStatus": "Рівень підтвердження",
    "wizard.identificationMethod": "Метод ідентифікації", "wizard.identificationConclusion": "Висновок щодо ідентифікації", "wizard.expertComment": "Коментар експерта",
    "wizard.media": "Медіа", "wizard.plotting": "Схема дефектів", "wizard.stonePhoto": "Фото каменя", "wizard.chooseFile": "Вибрати файл",
    "wizard.privateMediaHelp": "JPEG, PNG або WebP, до 10 МБ. Зберігається приватно.", "wizard.back": "Назад", "wizard.clearEntry": "Очистити введення", "wizard.saveDraft": "Зберегти чернетку", "wizard.next": "Далі",
    "wizard.restoreTitle": "Відновити незбережене введення?", "wizard.restoreDescription": "Знайдено незбережені дані цієї вкладки. Вони не були надіслані на сервер.", "wizard.restoreMedia": "Вкладення не відновлюються — після відновлення додайте файли повторно.", "wizard.startNew": "Почати заново", "wizard.restore": "Відновити",
    "wizard.clearTitle": "Очистити незбережене введення?", "wizard.close": "Закрити", "wizard.clearDescription": "Дані цієї вкладки буде видалено з форми й локального сховища. Це не змінить жодного збереженого звіту.", "wizard.cancel": "Скасувати", "wizard.stay": "Залишитися", "wizard.leaveTitle": "Залишити майстер?",
    "detail.privateReport": "Приватний звіт", "detail.loadingReport": "Завантаження звіту…", "detail.subtitle": "Дані, висновок експерта, вкладення та історія змін.", "detail.backToReports": "До всіх звітів", "detail.editDraft": "Редагувати чернетку", "detail.saveChanges": "Зберегти зміни", "detail.reportState": "Стан звіту", "detail.transitionReason": "Коментар до зміни статусу", "detail.transitionReasonPlaceholder": "Необов’язково, але бажано для повернення чи анулювання", "detail.narrativeQuality": "Перевірка текстових полів", "detail.narrativeHelp": "Автоматичні сигнали заповнення не оцінюють професійний висновок і не блокують збереження.", "detail.loading": "Завантаження…", "detail.marketReference": "Довідковий ринковий орієнтир", "detail.marketReferenceHelp": "Ринковий орієнтир не є експертною, продажною чи транзакційною ціною.", "detail.attachments": "Вкладення", "detail.history": "Історія змін",
    "dashboard.statusDraft": "Чернетка", "dashboard.statusReview": "На перевірці", "dashboard.statusIssued": "Видано", "dashboard.statusVoid": "Анульовано", "dashboard.notSold": "Не продано", "dashboard.sold": "Продано",
    "dashboard.view": "Переглянути", "dashboard.edit": "Редагувати", "dashboard.editDraftOnly": "Редагування доступне лише для чернетки", "dashboard.print": "Друк", "dashboard.loading": "Завантаження звітів…", "dashboard.empty": "Звітів за поточними умовами не знайдено.", "dashboard.loadFailed": "Не вдалося завантажити звіти. Оновіть сторінку або спробуйте пізніше.",
    "dashboard.title": "Всі звіти", "dashboard.subtitle": "Управління сертифікатами та оцінками.", "dashboard.newReport": "Новий звіт", "dashboard.search": "Пошук за номером звіту", "dashboard.filters": "Фільтри", "dashboard.allReportStatuses": "Усі статуси звіту", "dashboard.allSaleStatuses": "Усі статуси продажу", "dashboard.allExperts": "Усі експерти",
    "dashboard.reportStatus": "Статус звіту", "dashboard.saleStatus": "Статус продажу", "dashboard.expert": "Експерт", "dashboard.shape": "Форма", "dashboard.any": "Будь-яка", "dashboard.carat": "Вага (карат)", "dashboard.from": "Від", "dashboard.to": "До", "dashboard.color": "Колір", "dashboard.clarity": "Чистота", "dashboard.cut": "Якість (Cut)", "dashboard.referenceUsd": "Довідковий орієнтир (USD)", "dashboard.createdFrom": "Дата створення: від", "dashboard.createdTo": "Дата створення: до", "dashboard.apply": "Застосувати", "dashboard.clear": "Очистити", "dashboard.referenceNote": "Довідкові орієнтири (USD) формуються для нових або змінених чернеток за налаштованим провайдером (поточне джерело — OpenFacet). Позначка SYS означає системний довідковий орієнтир, ADM — орієнтир, застосовність якого підтвердив адміністратор; поруч завжди вказано джерело. Це не експертна, продажна чи транзакційна ціна; еквівалент у UAH додається лише за увімкненим курсом НБУ та фіксується під час створення.",
    "dashboard.reportId": "ID звіту", "dashboard.date": "Дата", "dashboard.caratColumn": "Вага (ct)", "dashboard.priceUsd": "Ціна (USD)", "dashboard.actions": "Дії", "dashboard.pagination": "Пагінація звітів", "dashboard.sortReportId": "Сортувати за ID звіту", "dashboard.sortDate": "Сортувати за датою", "dashboard.sortShape": "Сортувати за формою", "dashboard.sortCarat": "Сортувати за вагою", "dashboard.sortColor": "Сортувати за кольором", "dashboard.sortClarity": "Сортувати за чистотою", "dashboard.sortCut": "Сортувати за Cut", "dashboard.sortPrice": "Сортувати за довідковим орієнтиром", "dashboard.sortReportStatus": "Сортувати за статусом звіту", "dashboard.sortSaleStatus": "Сортувати за статусом продажу",
    "dashboard.openActions": "Відкрити дії для звіту {reportId}", "dashboard.referenceTypeDemo": "Демонстраційний орієнтир", "dashboard.referenceTypeSystem": "Системний довідковий орієнтир", "dashboard.referenceTypeAdmin": "Підтверджений довідковий орієнтир", "dashboard.referenceExplanation": "Пояснення ринкового орієнтира звіту {reportId}", "dashboard.referenceType": "Тип", "dashboard.provider": "Провайдер", "dashboard.providerSnapshot": "Знімок провайдера", "dashboard.observed": "Отримано", "dashboard.equivalent": "Еквівалент", "dashboard.nbuRate": "Курс НБУ", "dashboard.notAvailableForDemo": "Не передбачено для synthetic demo", "dashboard.notCalculatedForDemo": "Не розраховується для synthetic demo", "dashboard.notApplicableForDemo": "Не застосовується для synthetic demo", "dashboard.nbuRateValue": "{rate} UAH/USD · {date} · знімок #{snapshot}", "dashboard.otherReferences": "Інші доступні орієнтири:", "dashboard.demoReferenceWarning": "Синтетичне демонстраційне значення; не є ринковою, експертною, продажною чи транзакційною ціною.", "dashboard.systemReferenceWarning": "Розраховано системою за останнім затвердженим знімком; не є експертною, продажною чи транзакційною ціною.", "dashboard.adminReferenceWarning": "Застосовність підтверджена адміністратором; не є експертною, продажною чи транзакційною ціною.", "dashboard.openPrivateReport": "Відкрити приватний перегляд звіту", "dashboard.firstPage": "На першу сторінку", "dashboard.previousPage": "На попередню сторінку", "dashboard.nextPage": "На наступну сторінку", "dashboard.lastPage": "На останню сторінку",
    "narrative.fields": "Текстові поля", "narrative.identificationMethod": "Метод ідентифікації", "narrative.identificationConclusion": "Висновок щодо ідентифікації", "narrative.expertComment": "Коментар експерта", "narrative.statusTransition": "Подія зміни статусу без коментаря", "narrative.show": "Показувати:", "narrative.showFields": "Показувати текстові поля", "narrative.empty": "Порожні", "narrative.filled": "Заповнені", "narrative.demoNote": "Synthetic lifecycle не має текстових коментарів; цю опцію не моделюємо.", "narrative.realNote": "Подія зміни статусу перевіряється у вибраному зрізі дат.",
  },
};

let activeLocale = DEFAULT_LOCALE;

function normalizeLocale(value) {
  return SUPPORTED_LOCALES.includes(value) ? value : DEFAULT_LOCALE;
}

function interpolate(message, values) {
  return message.replace(/\{(\w+)\}/g, (_match, name) => String(values[name] ?? `{${name}}`));
}

export function validateCatalogs() {
  const englishKeys = Object.keys(catalogs.en).sort();
  for (const locale of SUPPORTED_LOCALES) {
    const localeKeys = Object.keys(catalogs[locale]).sort();
    if (englishKeys.length !== localeKeys.length || englishKeys.some((key, index) => key !== localeKeys[index])) {
      throw new Error(`i18n catalog keys do not match for locale ${locale}.`);
    }
    for (const key of localeKeys) {
      if (!catalogs[locale][key]?.trim()) throw new Error(`i18n catalog value is missing for ${locale}.${key}.`);
    }
  }
}

export function getLocale() {
  return activeLocale;
}

export function resolveLocale(search = globalThis.window?.location?.search ?? "", storedLocale = globalThis.localStorage?.getItem(LOCALE_STORAGE_KEY)) {
  const requestedLocale = new URLSearchParams(search).get("lang");
  if (SUPPORTED_LOCALES.includes(requestedLocale)) return requestedLocale;
  return normalizeLocale(storedLocale);
}

export function t(key, values = {}) {
  const message = catalogs[activeLocale]?.[key];
  if (!message) throw new Error(`Missing i18n key: ${key}`);
  return interpolate(message, values);
}

export function formatDate(value, options = {}) {
  return new Intl.DateTimeFormat(activeLocale === "uk" ? "uk-UA" : "en-US", options).format(value);
}

export function formatNumber(value, options = {}) {
  return new Intl.NumberFormat(activeLocale === "uk" ? "uk-UA" : "en-US", options).format(value);
}

export function formatCurrency(value, currency, options = {}) {
  return formatNumber(value, { style: "currency", currency, ...options });
}

export function applyTranslations(root = globalThis.document) {
  if (!root) return;
  root.documentElement?.setAttribute("lang", activeLocale);
  if (root.title !== undefined) root.title = t("app.title");
  root.querySelectorAll?.("[data-i18n]").forEach((node) => { node.textContent = t(node.dataset.i18n); });
  root.querySelectorAll?.("[data-i18n-placeholder]").forEach((node) => { node.placeholder = t(node.dataset.i18nPlaceholder); });
  root.querySelectorAll?.("[data-i18n-alt]").forEach((node) => { node.alt = t(node.dataset.i18nAlt); });
  root.querySelectorAll?.("[data-i18n-aria-label]").forEach((node) => { node.setAttribute("aria-label", t(node.dataset.i18nAriaLabel)); });
  root.querySelectorAll?.("[data-locale-switch]").forEach((node) => {
    const isActive = node.dataset.localeSwitch === activeLocale;
    node.setAttribute("aria-pressed", String(isActive));
    node.classList.toggle("is-active", isActive);
  });
}

export function setLocale(locale, { updateUrl = true } = {}) {
  activeLocale = normalizeLocale(locale);
  globalThis.localStorage?.setItem(LOCALE_STORAGE_KEY, activeLocale);
  if (updateUrl && globalThis.window?.location && globalThis.window?.history?.replaceState) {
    const url = new URL(globalThis.window.location.href);
    url.searchParams.set("lang", activeLocale);
    globalThis.window.history.replaceState(globalThis.window.history.state, "", `${url.pathname}${url.search}${url.hash}`);
  }
  applyTranslations();
  const LocaleChangeEvent = globalThis.window?.CustomEvent ?? globalThis.CustomEvent;
  if (LocaleChangeEvent) globalThis.window?.dispatchEvent?.(new LocaleChangeEvent("diamant:locale-change", { detail: { locale: activeLocale } }));
  return activeLocale;
}

export function initializeI18n() {
  validateCatalogs();
  activeLocale = resolveLocale();
  applyTranslations();
  return activeLocale;
}

export const i18nCatalogs = catalogs;
