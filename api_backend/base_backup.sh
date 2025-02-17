#!/bin/bash

### BASE ###
python manage.py dumpdata accounts.Education --indent 2 > json/base_backup/education.json
python manage.py dumpdata accounts.Specialty --indent 2 > json/base_backup/specialty.json
python manage.py dumpdata accounts.Program --indent 2 > json/base_backup/program.json
python manage.py dumpdata accounts.Experience --indent 2 > json/base_backup/experience.json
python manage.py dumpdata accounts.LegalEntityType --indent 2 > json/base_backup/legal_entity_type.json
python manage.py dumpdata accounts.Category --indent 2 > json/base_backup/category.json
python manage.py dumpdata projects.ProjectComplexity --indent 2 > json/base_backup/project_complexity.json
python manage.py dumpdata projects.ProjectTemplate --indent 2 > json/base_backup/project_template.json
python manage.py dumpdata projects.DefaultProjectTemplateTask --indent 2 > json/base_backup/default_project_template_task.json
python manage.py dumpdata projects.ProjectTemplateTask --indent 2 > json/base_backup/project_template_task.json

### ACCOUNTS ###
python manage.py dumpdata accounts.User --indent 2 > json/accounts_backup/user.json
python manage.py dumpdata accounts.LegalProfile --indent 2 > json/accounts_backup/legal_profile.json
python manage.py dumpdata accounts.PhysicalProfile --indent 2 > json/accounts_backup/physical_profile.json
python manage.py dumpdata accounts.GIPProfile --indent 2 > json/accounts_backup/gip_profile.json

### CHATS ###
python manage.py dumpdata chat.Chat --indent 2 > json/chat_backup/chat.json
python manage.py dumpdata chat.Participant --indent 2 > json/chat_backup/participant.json
python manage.py dumpdata chat.Message --indent 2 > json/chat_backup/message.json

### NEWS ###
python manage.py dumpdata news.News --indent 2 > json/news_backup/news.json

### Folders ###
python manage.py dumpdata folders.Folder --indent 2 > json/folders_backup/folder.json
python manage.py dumpdata folders.File --indent 2 > json/folders_backup/file.json
python manage.py dumpdata folders.FolderAccess --indent 2 > json/folders_backup/folder_access.json
python manage.py dumpdata folders.FolderActionLog --indent 2 > json/folders_backup/folder_action_log.json

### Projects ###
python manage.py dumpdata projects.Project --indent 2 > json/projects_backup/project.json
python manage.py dumpdata projects.ProjectSpecialtyBudget --indent 2 > json/projects_backup/project_specialty_budget.json
python manage.py dumpdata projects.ProjectResponse --indent 2 > json/projects_backup/project_response.json
python manage.py dumpdata projects.ProjectMember --indent 2 > json/projects_backup/project_member.json

### Task_scheduler ###
python manage.py dumpdata task_scheduler.Task --indent 2 > json/task_scheduler_backup/task.json

echo "Бэкап данных завершен."
