# Требования

- Windows
- Python 3+
- Adobe Photoshop

# Нужно сделать один раз в самом начале

- Установить зависимости из `requirements.txt` - `pip3 install -r requirements.txt`

- Закинуть шаблоны в папку `templates` (`templates/dashkov.psd`, ...).

- Выполнить  `generate_template_metainfo.py templates/`.

- Найти на диске `client_id_sected.json` и закинуть его в папку `youtube` (_// наверное, лучше держать его в корне_)

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

*Попав на страницу очередного плейлиста, нужно обновить страницу (`F5`), т.к. расришение (пока) не умеет обнаруживать переходы на страницах youtube*.

Чтобы авторизироваться другим аккаунтом, необходимо удалить файл `youtube/token.pickle`.
