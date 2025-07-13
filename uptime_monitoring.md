# Настройка мониторинга для предотвращения засыпания бота

## Проблема
Replit может "засыпать" бесплатные проекты при неактивности, что останавливает работу бота.

## Решение: UptimeRobot (бесплатно)

### 1. Регистрация
1. Зайдите на [UptimeRobot](https://uptimerobot.com/)
2. Создайте бесплатный аккаунт

### 2. Настройка мониторинга
1. Нажмите **"Add New Monitor"**
2. Настройте следующие параметры:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: Telegram Bot Keep-Alive
   - **URL**: `https://[your-replit-url].replit.app/health`
   - **Monitoring Interval**: 5 minutes
   - **Monitor Timeout**: 30 seconds

### 3. Получение URL Replit
1. В Replit нажмите кнопку **"Run"**
2. Скопируйте URL из адресной строки веб-просмотра (обычно `https://[project-name].[username].replit.app`)
3. Добавьте `/health` в конец URL

### 4. Альтернативные сервисы
- **Pingdom** - https://www.pingdom.com/ (бесплатная версия)
- **StatusCake** - https://www.statuscake.com/ (бесплатная версия)
- **Freshping** - https://www.freshworks.com/website-monitoring/

## Встроенный Keep-Alive
Бот уже имеет встроенный keep-alive сервер на порту 5000 с эндпоинтами:
- `/` - основная страница статуса
- `/health` - проверка работоспособности

## Результат
После настройки мониторинга бот будет работать 24/7 без засыпания.