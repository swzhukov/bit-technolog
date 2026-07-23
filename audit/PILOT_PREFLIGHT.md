# 🚀 PILOT PREFLIGHT CHECKLIST (27.07.2026)

**Дата:** 2026-07-23 (за 4 дня до пилота)  
**Сергей:** A1 — звонки 4 пользователям, A2 — bug-fix после фидбэка  
**Система:** БИТ.Технолог v9 (HEAD `9ee9a3d`, prod)

## ✅ Что готово к пилоту

| # | Проверка | Статус | Дата |
|---|----------|--------|------|
| 1 | URL: `https://seefeesnahurid.beget.app/bit-technolog/` | ✅ Работает | 2026-07-23 |
| 2 | SSL: валидный Let's Encrypt | ✅ CN=seefeesnahurid.beget.app | 2026-07-23 |
| 3 | Kaspersky совместимость | ✅ Не режет | 2026-07-23 |
| 4 | Yandex Browser совместимость | ✅ Доверяет | 2026-07-23 |
| 5 | Docker контейнер | ✅ Up 33+ min healthy | 2026-07-23 |
| 6 | 42 теста (TR.py) | ✅ 42/42 | 2026-07-23 |
| 7 | 4 роли × 16 проверок (UI_SMOKE) | ✅ 0 замечаний | 2026-07-23 |
| 8 | 5 сценариев технолога | ✅ 0 замечаний | 2026-07-23 |
| 9 | RBAC матрица | ✅ 4/4 | 2026-07-23 |
| 10 | Backup prod БД | ✅ `/opt/beget/backups/bit-technolog/pilot-27.07.2026/db-snapshot-20260723_145909.sql` (1.6MB) | 2026-07-23 |

## 📊 Состояние prod БД (2026-07-23, до пилота)

| Таблица | Кол-во | Комментарий |
|---------|--------|-------------|
| items | 200 | 177 demo + 23 test (TEST-A*) |
| tech_cards | 50 | 49 demo + 1 test (T2) |
| etalons | 19 | без изменений |
| equipment | 57 | без изменений |
| workshops | 5 | без изменений |
| professions | 12 | без изменений |
| change_notices | 99 | без изменений |
| audit_logins | 5206+ | растёт (login events) |
| sessions | 1635+ | растёт (активные сессии) |
| pilot_users | 6 | 6 demo-учёток |
| pilot_runs | 3 | 3 теста LLM |

## 👥 4 пользователя для пилота (A1)

| Login | Роль | Что проверит |
|-------|------|--------------|
| `techadmin` | admin | полный функционал, настройки, /audit |
| `vorobyev` или `baranov` | main_technologist | создание, approve, извещения |
| `tarrietsky` | technologist | создание, inline-edit, генерация ТК |
| `golubev` | workshop_chief | read-only, просмотр РС |

Пароль для всех: `demo`

## 📋 Что нужно сделать до пилота (A1)

1. **Сергей** звонит 4 пользователям, сообщает:
   - URL: `https://seefeesnahurid.beget.app/bit-technolog/`
   - Логин/пароль (см. таблицу выше)
   - **Сценарий для проверки** (см. ниже)

2. **Каждый пользователь** проходит 5 сценариев (10-15 мин):
   - Сценарий 1: открыть URL, login, увидеть дашборд
   - Сценарий 2: открыть "Изделия" (для tech/main) — увидеть список 200 items
   - Сценарий 3: создать новую деталь (для tech/main)
   - Сценарий 4: просмотр существующей детали (для всех)
   - Сценарий 5: создать извещение (для tech/main)

3. **Сергей** собирает фидбэк (что непонятно, что не работает, что улучшить).

4. **Я (Mavis)** фикшу баги → A2 → перезапуск пилота.

## 🔧 Что я делаю в фоне (пока Сергей готовит A1)

- [x] Snapshot БД (сделано)
- [x] Backup файлов на `/opt/beget/backups/`
- [ ] Cleanup test items (TEST-A*, TEST-B*, TEST-RBAC-*) — TODO
- [ ] Update USER_GUIDE.md со скриншотами v9 (новый URL)
- [ ] Добавить "Пилот 27.07" в pilot_runs

## 🐛 Cleanup test items (TODO)

Test items засоряют БД. Нужно:
```sql
DELETE FROM items WHERE designation LIKE 'TEST-%' OR designation LIKE 'TEST-A%' OR designation LIKE 'TEST-B%' OR designation LIKE 'RBAC-%';
DELETE FROM tech_cards WHERE id NOT IN (SELECT DISTINCT tech_card_id FROM operations WHERE tech_card_id IS NOT NULL) AND created_at > '2026-07-20';
```

Сделаю перед пилотом (24-25.07).

## 🔄 Rollback (если что-то критично сломается)

```bash
ssh root@seefeesnahurid.beget.app
cd /opt/beget/bit-technolog
docker compose down
systemctl start bit-technolog
# → вернётся старый URL https://217.114.7.5:8081/
```

После фикса:
```bash
cd /opt/beget/bit-technolog
docker compose up -d
```

## 📞 Контакты для эскалации

- **Сергей** — owner, A1/A2 coordinator
- **Mavis (я)** — bug fixes, развёртывание
- **YandexGPT** — fallback LLM, нужен folder_id от Сергея (для D7)

## 🎯 Definition of Success для пилота

- 4 пользователя **открыли** URL без помощи IT
- 4 пользователя **залогинились** под своими credentials
- ≥ 3 из 4 прошли **все 5 сценариев** без блокеров
- 0 **критических** багов (потеря данных, security, невозможность работы)
- < 5 **мелких** багов (UI неудобство, медленная загрузка, опечатки)

Если все критерии выполнены — пилот успешен, переходим в Sprint 7 (production-ready).
