# Требования

- Windows
- Python 3+
- Adobe Photoshop CC 2019+ (с CC 2018 не рабоает, с CS не проверялось)

# Нужно сделать один раз в самом начале

- Установить зависимости из `requirements.txt` - `pip3 install -r requirements.txt`

- Закинуть шаблоны в папку `templates` (`templates/dashkov.psd`, ...)

- Выполнить  `generate_template_metainfo.py templates/`

- Найти на диске [client_id_sected.json](https://drive.google.com/open?id=1K10bgSX3oUwVHvW0lUL40E-DrrXNEmCU) и закинуть его в папку `youtube` (_// наверное, лучше держать его в корне_)

- В photoshop установить единицы измерения `Rulers` на `Pixels` и `Type` на `Points` в `Edit -> Preferences -> Units & Rulers`.
    (**TODO: делать это автоматически и предупредить убивать сервер нежно**) 

Все шаблоны должны иметь слои с именами
`Subject`, `Number`, `Topic`, `Rectangle` (прямоугольник вокруг номера), `Darkness` и `Bottom`.
У слоя `Darkness` должен быть подслой `Lamp`, у слоя `Bottom` должен быть подслой `Name` (имя лектора)

# Нужно делать для каждой сессии

- Запустить сервер, выполнив команду `server.py`
- Установить в браузер расширение. Пока это тестировалось только для firefox
    + Перейти на страницу `about:debugging`
    + Нажать на `Load Temporary Add-on...`
    + Выбрать файл `web/manifest.json`
- Перейти на страницу нужного плейлиста на youtube, на которой должен появиться новый вырвиглазный интерфейс
    + В самом начале превью обложег могут загружаться очень долго, т.к. должен запуститься photoshop

**Попав на страницу очередного плейлиста, нужно обновить страницу (`F5`), т.к. расришение (пока) не умеет обнаруживать переходы на страницах youtube**.

Чтобы авторизироваться другим аккаунтом, необходимо удалить файл `youtube/token.pickle`.
