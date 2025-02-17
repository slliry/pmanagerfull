Команда для создания бэкапа:
	scripts/backup_db.sh

	pg_dump -U postgres -F c -b -v -f /backups/my_database_backup.dump bpm
Восстановление из бэкапа:
	pg_restore -U postgres -d bpm -v /backups/test.dump

Параллельный бэкап:
	pg_dump --format=custom --file=/backups/backup.dump --username=postgres bpm
	pg_restore --clean --dbname=bpm --username=postgres /backups/backup.dump

Инструкция по восстановлению автоматических бэкапов
	Для восстановления используйте команду:
	pg_restore --jobs=4 --clean --dbname=bpm --username=postgres /backups/backup.dump


### Task Scheduler ###

POST /api/tasks/
Content-Type: application/json

{
    "title": "Новая задача",
    "description": "Описание задачи",
    "assigned_to": 1,  // ID пользователя, которому назначена задача
    "project": "123e4567-e89b-12d3-a456-426614174000",  // UUID проекта
    "due_date": "2023-12-31T23:59:59Z"
}



projects/urls.py:

complexities/:

	GET /api/projects/complexities/: Получить список всех категорий сложности проекта.

	POST /api/projects/complexities/: Создать новую категорию сложности проекта.

	GET /api/projects/complexities/{id}/: Получить конкретную категорию сложности проекта по ID.

	PUT /api/projects/complexities/{id}/: Обновить конкретную категорию сложности проекта по ID.

	DELETE /api/projects/complexities/{id}/: Удалить конкретную категорию сложности проекта по ID.

projects/: (обрати внимание что у тебя basename='project' в роутере и это очень хуёво, нужно было оставить пустым)

	GET /api/projects/: Получить список всех проектов (для ГИПа) или список проектов для конкретного пользователя (для обычного пользователя, только те, которые соответствуют специальности пользователя и в статусе аукциона).

	POST /api/projects/: Создать новый проект (только для ГИПа).

	GET /api/projects/{uuid}/: Получить конкретный проект по UUID.

	PUT /api/projects/{uuid}/: Обновить конкретный проект по UUID (для ГИПа).

	DELETE /api/projects/{uuid}/: Удалить конкретный проект по UUID (для ГИПа).

	PUT /api/projects/{uuid}/ - для изменения статуса проекта

responses/: (обрати внимание что у тебя basename='projectresponse' в роутере и это очень хуёво, нужно было оставить пустым)

	GET /api/projects/responses/: Получить список всех откликов (для ГИПа) или список своих откликов (для обычного пользователя).

	POST /api/projects/responses/: Создать новый отклик на проект (только для обычного пользователя, проект должен быть в статусе аукциона, и специальность должна совпадать).

	GET /api/projects/responses/{uuid}/: Получить конкретный отклик по UUID.

	PUT /api/projects/responses/{uuid}/: Обновить конкретный отклик по UUID (не нужен).

	DELETE /api/projects/responses/{uuid}/: Удалить конкретный отклик по UUID (не нужен).

	POST /api/projects/responses/{uuid}/accept_response/ - Принять отклик (для ГИПа).

	POST /api/projects/responses/{uuid}/reject_response/ - Отклонить отклик (для ГИПа).

	DELETE /api/projects/responses/{uuid}/block_chat/ - Заблокировать чат отклика (для ГИПа).

members/: (обрати внимание что у тебя basename='projectmember' в роутере и это очень хуёво, нужно было оставить пустым)

	GET /api/projects/members/: Получить список всех участников проектов (для ГИПа) или список своих участий (для обычного пользователя).

	POST /api/projects/members/: Создать нового участника проекта (не нужен, создается при принятии отклика).

	GET /api/projects/members/{uuid}/: Получить конкретного участника проекта по UUID.

	PUT /api/projects/members/{uuid}/: Обновить конкретного участника проекта по UUID (не нужен).

	DELETE /api/projects/members/{uuid}/: Удалить конкретного участника проекта по UUID (не нужен).

templates/:

	GET /api/projects/templates/: Получить список всех шаблонов проектов.

	POST /api/projects/templates/: Создать новый шаблон проекта (только для администратора или специального пользователя).

	GET /api/projects/templates/{id}/: Получить конкретный шаблон проекта по ID.

	PUT /api/projects/templates/{id}/: Обновить конкретный шаблон проекта по ID (только для администратора или специального пользователя).

	DELETE /api/projects/templates/{id}/: Удалить конкретный шаблон проекта по ID (только для администратора или специального пользователя).

