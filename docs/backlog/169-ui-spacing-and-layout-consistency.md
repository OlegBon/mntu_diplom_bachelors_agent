# 169 — UI spacing і layout consistency

## Мета

Зробити вертикальні та горизонтальні відступи передбачуваними в усьому
інтерфейсі Diamant ID: між текстом, полями, checkbox/radio controls, кнопками,
таблицями, alert-блоками та секціями. Це UX-polish, не redesign і не зміна
бізнес-процесів.

## Scope

- Провести page-by-page audit public, auth, profile, dashboard, wizard, detail,
  admin, market, analytics і demo screens у desktop та mobile breakpoints.
- Узгодити scale через наявні SCSS variables/компонентні правила, без локальних
  випадкових magic numbers у Pug або JavaScript.
- Вирівняти типові relationships: label → control, helper/error → control,
  control group → primary action, section heading → content, table/filter →
  supporting text, action rows → сусідні блоки.
- Перевірити flex/grid wrapping, disabled controls, dialog/footer actions,
  burger navigation та keyboard focus, щоб spacing не ламав responsive UI або
  доступність.
- Виправляти лише доведені неузгодженості; не змінювати кольорову систему,
  domain copy, API, data model чи feature scope.

## Поза scope

- Повний visual redesign, новий component library або перехід на framework.
- Заміна конкретних UX flows, permissions чи форм валідації.

## Перевірки готовності

- `npm test` та `npm run test:e2e` без регресій.
- Ручний visual smoke: desktop і mobile для representative public, profile,
  create-report, report detail, dashboard, analytics та demo pages.
- Keyboard tab/focus не втрачає видимості; не з'являється horizontal scroll.
- `git diff --check`; у `docs/progress.md` зафіксовано перелік перевірених
  сторінок і свідомі винятки.
