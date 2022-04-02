import datetime

from git import Repo, InvalidGitRepositoryError, GitCommandError, NoSuchPathError
from config import get_config


CONFIG = get_config()


def is_git_repo(path: str) -> bool:
    """
    Function that determines if the given path is a git repo.
    :return: True if is a repo, False otherwise.
    """
    try:
        _ = Repo(path).git_dir
        return True
    except (InvalidGitRepositoryError, NoSuchPathError):
        return False


class WikiRepoManager:
    """
    Class that manages the git repo of the wiki.
    The repo could be local or remote, according to the config.
    """

    def __init__(self, flask_app):
        self.flask_app = flask_app
        self.repo: Repo = self.git_repo_init()

    def get_existing_repo(self) -> Repo:
        """
        Function that gets the existing repo in the wiki_directory.
        Could be local or remote.
        :return: Repo
        """
        git_repo = None
        try:
            self.flask_app.logger.info("Initializing existing git repo ...")
            git_repo = Repo(CONFIG["wiki_directory"])
            git_repo.git.checkout()  # don't specify branch, it could be main or master
        except (InvalidGitRepositoryError, GitCommandError, NoSuchPathError) as e:
            self.flask_app.logger.error(f"Error during existing git repo initialization: {str(e)}")

        return git_repo

    def git_repo_init(self) -> Repo:
        """
        Function that initializes the git repo of the Wiki.
        The repo can be local or remote (it will be cloned), according to the config setting.
        :return: initialized repo
        """
        if is_git_repo(CONFIG["wiki_directory"]):
            git_repo = self.get_existing_repo()
        else:
            if CONFIG["remote_url"]:  # if a remote url has been set, clone the repo
                git_repo = self.git_clone_remote()
            else:
                git_repo = self.git_new_local()

        # Configure git username and email
        if git_repo:  # if the repo has been initialized
            git_repo.config_writer().set_value("user", "name", "wikmd").release()
            git_repo.config_writer().set_value("user", "email", "wikmd@no-mail.com").release()

        return git_repo

    def git_clone_remote(self) -> Repo:
        """
        Function that clones a remote git repo according to the remote_url and the wiki_directory set in the config.
        :return: Repo
        """
        git_repo = None
        try:
            self.flask_app.logger.info(f"Cloning {CONFIG['remote_url']} ...")
            git_repo = Repo.clone_from(url=CONFIG["remote_url"], to_path=CONFIG["wiki_directory"])
        except (InvalidGitRepositoryError, GitCommandError, NoSuchPathError) as e:
            self.flask_app.logger.error(f"Error during remote git repo cloning: {str(e)}")
        return git_repo

    def git_new_local(self) -> Repo:
        """
        Function that inits a new local git repo according to the wiki_directory set in the config.
        :return: Repo
        """
        git_repo = None
        try:
            self.flask_app.logger.info("Creating a new local git repo ...")
            git_repo = Repo.init(path=CONFIG["wiki_directory"])
            git_repo.git.checkout("-b", "main")  # create a new (-b) main branch
        except (InvalidGitRepositoryError, GitCommandError, NoSuchPathError) as e:
            self.flask_app.logger.error(f"Error during new local git repo initialization: {str(e)}")
        return git_repo

    def git_pull(self):
        """
        Function that pulls from the remote wiki repo.
        """
        try:
            # git pull
            self.repo.git.pull()
            self.flask_app.logger.info(f"Pulled from the repo")
        except Exception as e:
            self.flask_app.logger.info(f"Error during git pull: {str(e)}")

    def git_commit(self, page_name="", commit_type=""):
        """
        Function that commits changes to the wiki repo.
        :param commit_type: could be 'Add', 'Edit' or 'Remove'.
        :param page_name: name of the page that has been changed.
        """
        try:
            # git add --all
            self.repo.git.add("--all")
            date = datetime.datetime.now()
            commit_msg = f"{commit_type} page '{page_name}' on {str(date)}"
            # git commit -m
            self.repo.git.commit('-m', commit_msg)
            self.flask_app.logger.info(f"New git commit: {commit_msg}")
        except Exception as e:
            self.flask_app.logger.info(f"Nothing to commit: {str(e)}")

    def git_push(self):
        """
        Function that pushes changes to the remote wiki repo.
        """
        try:
            # git push
            self.repo.git.push("-u", "origin", "master")
            self.flask_app.logger.info("Pushed to the repo.")
        except Exception as e:
            self.flask_app.logger.info(f"Error during git push: {str(e)}")

    def git_sync(self, page_name="", commit_type=""):
        """
        Function that manages the synchronization with a git repo, that could be local or remote.
        If SYNC_WITH_REMOTE is set, it also pull before committing and then pushes changes to the remote repo.
        :param commit_type: could be 'Add', 'Edit' or 'Remove'.
        :param page_name: name of the page that has been changed.
        """
        if CONFIG["sync_with_remote"]:
            self.git_pull()

        self.git_commit(page_name=page_name, commit_type=commit_type)

        if CONFIG["sync_with_remote"]:
            self.git_push()
