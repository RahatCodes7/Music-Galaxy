import asyncio
import shlex
import sys
from typing import Tuple

import config

from ..logging import LOGGER

GIT_TIMEOUT = 120

try:
    from git import Repo
    from git.exc import GitCommandError, InvalidGitRepositoryError
except ImportError as e:
    # gitpython raises at import time when the git binary is missing, the bot
    # has to start anyway, the runtime auto update is simply skipped
    Repo = None
    GitCommandError = InvalidGitRepositoryError = RuntimeError
    LOGGER(__name__).info(f"Git Client Unavailable: {e}")


def install_req(cmd: str) -> Tuple[str, str, int, int]:
    async def install_requirements():
        args = shlex.split(cmd)
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return (
            stdout.decode("utf-8", "replace").strip(),
            stderr.decode("utf-8", "replace").strip(),
            process.returncode,
            process.pid,
        )

    return asyncio.run(install_requirements())


def git():
    if Repo is None:
        return
    if not config.AUTO_UPDATE:
        LOGGER(__name__).info("Auto update disabled")
        return
    REPO_LINK = config.UPSTREAM_REPO
    if config.GIT_TOKEN:
        GIT_USERNAME = REPO_LINK.split("com/")[1].split("/")[0]
        TEMP_REPO = REPO_LINK.split("https://")[1]
        UPSTREAM_REPO = f"https://{GIT_USERNAME}:{config.GIT_TOKEN}@{TEMP_REPO}"
    else:
        UPSTREAM_REPO = config.UPSTREAM_REPO
    try:
        repo = Repo()
        LOGGER(__name__).info(f"Git Client Found [VPS DEPLOYER]")
    except GitCommandError:
        LOGGER(__name__).info(f"Invalid Git Command")
    except InvalidGitRepositoryError:
        try:
            LOGGER(__name__).info("Fetching updates from upstream repository...")
            repo = Repo.init()
            if "origin" in repo.remotes:
                origin = repo.remote("origin")
            else:
                origin = repo.create_remote("origin", UPSTREAM_REPO)
            origin.fetch(timeout=GIT_TIMEOUT)
            repo.create_head(
                config.UPSTREAM_BRANCH,
                origin.refs[config.UPSTREAM_BRANCH],
            )
            repo.heads[config.UPSTREAM_BRANCH].set_tracking_branch(
                origin.refs[config.UPSTREAM_BRANCH]
            )
            repo.heads[config.UPSTREAM_BRANCH].checkout(True)
            try:
                repo.create_remote("origin", config.UPSTREAM_REPO)
            except BaseException:
                pass
            nrs = repo.remote("origin")
            nrs.fetch(config.UPSTREAM_BRANCH, timeout=GIT_TIMEOUT)
            try:
                nrs.pull(config.UPSTREAM_BRANCH, timeout=GIT_TIMEOUT)
            except GitCommandError:
                repo.git.reset("--hard", "FETCH_HEAD")
            install_req(
                f"{sys.executable} -m pip install --no-cache-dir -r requirements.txt"
            )
            LOGGER(__name__).info("Updates applied from upstream repository")
        except Exception as e:
            LOGGER(__name__).warning(
                f"Auto update skipped: {type(e).__name__}: {e}"
            )
    except Exception as e:
        LOGGER(__name__).info(f"Git Client Unavailable: {type(e).__name__}")
