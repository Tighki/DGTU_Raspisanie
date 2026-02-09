# Инструкция по пушу python_bot в Git

## Если вы находитесь в папке python_bot:

```bash
# Проверьте статус
git status

# Добавьте все файлы
git add .

# Создайте коммит
git commit -m "Initial commit: Python bot"

# Добавьте remote (если еще не добавлен)
git remote add origin https://git.fltrktv.ru/Tighki/DGTU_Raspisanie.git

# Запушьте в main
git push -u origin main
```

## Если вы находитесь в корне проекта (golang_timetable):

```bash
# Перейдите в папку python_bot
cd python_bot

# Инициализируйте git (если еще не инициализирован)
git init

# Создайте ветку main
git checkout -b main

# Добавьте все файлы
git add .

# Создайте коммит
git commit -m "Initial commit: Python bot"

# Добавьте remote
git remote add origin https://git.fltrktv.ru/Tighki/DGTU_Raspisanie.git

# Запушьте
git push -u origin main
```

## Если нужно запушить только python_bot из корня проекта:

```bash
# Из корня golang_timetable
git init
git checkout -b main

# Добавьте только папку python_bot
git add python_bot/

# Создайте коммит
git commit -m "Add Python bot"

# Добавьте remote
git remote add origin https://git.fltrktv.ru/Tighki/DGTU_Raspisanie.git

# Запушьте
git push -u origin main
```
