Сначала

```
export_titles.py titles.json
```

затем

```
generate_thumbnails.py <путь до .psd файла> titles.json out
```

а потом

```
upload_thumbnails.py titles.json out
```

Необходимо присутствие файла `client_id_sected.json` в папке со скриптами.

Чтобы авторизироваться заново, необходимо удалить файл `token.pickle`