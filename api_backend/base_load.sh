#!/bin/bash

### BASE ###
python manage.py loaddata json/base_backup/education.json
python manage.py loaddata json/base_backup/specialty.json
python manage.py loaddata json/base_backup/program.json
python manage.py loaddata json/base_backup/experience.json
python manage.py loaddata json/base_backup/legal_entity_type.json
python manage.py loaddata json/base_backup/category.json
python manage.py loaddata json/base_backup/project_complexity.json
python manage.py loaddata json/base_backup/project_template.json
python manage.py loaddata json/base_backup/default_project_template_task.json
python manage.py loaddata json/base_backup/project_template_task.json

### ACCOUNTS ###
python manage.py loaddata json/accounts_backup/user.json
python manage.py loaddata json/accounts_backup/legal_profile.json
python manage.py loaddata json/accounts_backup/physical_profile.json


# python manage.py loaddata json/accounts_backup/gip_profile.json # НЕ НУЖНО, ДОБАВЛЯЕТСЯ САМОСТОЯТЕЛЬНО

### CHATS ###
# python manage.py loaddata json/chat_backup/chat.json
# python manage.py loaddata json/chat_backup/participant.json
# python manage.py loaddata json/chat_backup/message.json

### NEWS ###
python manage.py loaddata json/news_backup/news.json

### Folders ###
# python manage.py loaddata json/folders_backup/folder.json
# python manage.py loaddata json/folders_backup/file.json
# python manage.py loaddata json/folders_backup/folder_access.json
# python manage.py loaddata json/folders_backup/folder_action_log.json

### Projects ###
# python manage.py loaddata json/projects_backup/project.json
# python manage.py loaddata json/projects_backup/project_specialty_budget.json
# python manage.py loaddata json/projects_backup/project_response.json
# python manage.py loaddata json/projects_backup/project_member.json

echo "Восстановление данных завершено."