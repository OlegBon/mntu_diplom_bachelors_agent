import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(scriptDir, '..');
const auditDir = path.join(rootDir, 'docs', 'audits');
const latestReportPath = path.join(auditDir, 'api-audit-latest.md');
const localHosts = new Set(['localhost', '127.0.0.1', '::1']);

function getBaseUrl() {
  const configuredUrl = process.env.API_AUDIT_BASE_URL?.trim() || 'http://127.0.0.1:8000';
  let url;
  try {
    url = new URL(configuredUrl);
  } catch {
    throw new Error('API_AUDIT_BASE_URL має бути коректною HTTP-адресою.');
  }
  if (url.protocol !== 'http:' || !localHosts.has(url.hostname)) {
    throw new Error('Аудитор підтримує лише локальний HTTP API на localhost або 127.0.0.1.');
  }
  url.pathname = '/';
  url.search = '';
  url.hash = '';
  return url.toString().replace(/\/$/, '');
}

function createChecks(baseUrl) {
  const apiUrl = (pathname) => new URL(pathname, `${baseUrl}/`).toString();
  return [
    ['Корінь API', 'GET', '/', [200], (body) => body?.message === 'Diamond Identification System API is running', 'JSON з повідомленням про роботу API'],
    ['OpenAPI-специфікація', 'GET', '/openapi.json', [200], (body) => body?.info?.title === 'Diamond ID System API', 'OpenAPI JSON з назвою застосунку'],
    ['Приватний список звітів без токена', 'GET', '/reports', [401], (body) => typeof body?.detail === 'string', '401 для приватного маршруту списку звітів'],
    ['Довідники оцінок', 'GET', '/market/mappings', [200], Array.isArray, 'JSON-масив Grade Mapping'],
    ['Приватний detail звіту без токена', 'GET', '/reports/DR-AUDIT-NONEXISTENT', [401], (body) => typeof body?.detail === 'string', '401 для приватного маршруту detail звіту'],
    ['Неіснуючий публічний паспорт', 'GET', '/public/passports/audit-nonexistent-public-id', [404], (body) => typeof body?.detail === 'string', '404 без розкриття даних для вгаданого public ID'],
    ['Профіль без токена', 'GET', '/users/me', [401], (body) => typeof body?.detail === 'string', '401 для захищеного маршруту'],
    ['Користувачі без токена', 'GET', '/users/', [401], (body) => typeof body?.detail === 'string', '401 для admin-маршруту'],
    ['Експерти без токена', 'GET', '/experts/', [401], (body) => typeof body?.detail === 'string', '401 для захищеного маршруту'],
    ['Статистика експертів без токена', 'GET', '/statistics/expert-performance', [401], (body) => typeof body?.detail === 'string', '401 для admin-only operational analytics'],
    ['Статистика перевірок admin без токена', 'GET', '/statistics/admin-review-performance', [401], (body) => typeof body?.detail === 'string', '401 для admin-only review analytics'],
    ['Довідники звіту без токена', 'GET', '/reference-values', [401], (body) => typeof body?.detail === 'string', '401 для приватних довідників звіту'],
  ].map(([name, method, pathname, expectedStatuses, validate, contract]) => ({
    name, method, url: apiUrl(pathname), expectedStatuses, validate, contract,
  })).concat({
    name: 'CORS preflight токена', method: 'OPTIONS', url: apiUrl('/token'), expectedStatuses: [200],
    headers: { Origin: 'http://localhost:3000', 'Access-Control-Request-Method': 'POST' },
    validate: (_body, response) => response.headers.get('access-control-allow-origin') === 'http://localhost:3000',
    contract: 'CORS дозволяє локальний BrowserSync origin',
  });
}

async function runCheck(check) {
  try {
    const response = await fetch(check.url, { method: check.method, headers: check.headers, cache: 'no-store' });
    const contentType = response.headers.get('content-type') || '';
    const body = contentType.includes('application/json') ? await response.json() : null;
    const success = check.expectedStatuses.includes(response.status) && check.validate(body, response);
    return {
      ...check, actualStatus: response.status, success,
      result: success ? '✅ Пройдено' : '❌ Не пройдено',
      note: success ? 'Статус і контракт відповідають очікуванню.' : `Очікувані HTTP: ${check.expectedStatuses.join(' або ')}; отримано: ${response.status}.`,
    };
  } catch (error) {
    return { ...check, actualStatus: 'немає відповіді', success: false, result: '❌ Не пройдено', note: `Помилка запиту: ${error.message}` };
  }
}

function createReport(baseUrl, results) {
  const passed = results.filter((result) => result.success).length;
  const rows = results.map((result) => `| ${result.name} | ${result.method} | ${result.contract} | ${result.actualStatus} | ${result.result} | ${result.note} |`).join('\n');
  return `# Локальний аудит API Diamant ID\n\n- **Час UTC:** ${new Date().toISOString()}\n- **Режим:** лише локальний, читальні запити та CORS preflight\n- **API:** ${baseUrl}\n- **Результат:** ${passed}/${results.length} перевірок пройдено\n\n## Перевірки\n\n| Маршрут | Метод | Очікуваний контракт | HTTP | Результат | Примітка |\n| --- | --- | --- | --- | --- | --- |\n${rows}\n\n## Межі аудиту\n\nСкрипт не виконує POST, PUT або DELETE-запити, не запускає seed і не використовує облікові дані чи токени. Захищені GET-маршрути перевіряються лише як межа доступу без токена.\n`;
}

async function main() {
  const baseUrl = getBaseUrl();
  const results = await Promise.all(createChecks(baseUrl).map(runCheck));
  const report = createReport(baseUrl, results);
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  fs.mkdirSync(auditDir, { recursive: true });
  fs.writeFileSync(latestReportPath, report, 'utf8');
  fs.writeFileSync(path.join(auditDir, `api-audit-${timestamp}.md`), report, 'utf8');
  const failed = results.filter((result) => !result.success).length;
  console.log(`Аудит завершено: ${results.length - failed}/${results.length} перевірок пройдено.`);
  console.log(`Звіти: ${latestReportPath}`);
  process.exitCode = failed === 0 ? 0 : 1;
}

main().catch((error) => { console.error(`Аудит не запущено: ${error.message}`); process.exitCode = 1; });
