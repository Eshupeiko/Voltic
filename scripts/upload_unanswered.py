import os
import git
import shutil
import tempfile
import logging

logger = logging.getLogger(__name__)

def upload_unanswered_to_github():
    repo_url = f"https://{os.getenv('GITHUB_TOKEN')}@github.com/{os.getenv('GITHUB_REPO')}.git"
    branch = os.getenv("GITHUB_BRANCH", "main")
    local_path = os.getenv("UNANSWERED_PATH", "data/unanswered_questions.csv")
    remote_path = "data/unanswered_questions.csv"

    try:
        # Создаём временную папку
        temp_dir = tempfile.mkdtemp()
        repo = git.Repo.clone_from(repo_url, temp_dir, branch=branch)

        # Копируем файл
        shutil.copy(local_path, os.path.join(temp_dir, remote_path))

        # Добавляем изменения
        repo.git.add('--all')
        repo.git.commit('-m', 'Update unanswered_questions.csv', '--allow-empty')
        repo.git.push()

        logger.info("Файл unanswered_questions.csv успешно обновлён в репозитории.")
    except Exception as e:
        logger.error(f"Ошибка при обновлении файла в GitHub: {e}")
    finally:
        # Удаляем временную папку
        shutil.rmtree(temp_dir, ignore_errors=True)