#!/usr/bin/env python3

"""Operations with a Git Repo"""

import logging
from datetime import datetime
import github


def github_auth(logger: logging.Logger,
                token: str) -> github.Github:
    """Authenticate against GitHub API"""
    try:
        logger.debug("Authenticating to GitHub API...")
        auth = github.Github(token)
        return auth
    except github.GithubException as ghe:
        logger.error("Unable to authenticate against GitHub: %s",
                     ghe)
        return ghe


def get_commits(logger: logging.Logger,
                token: str,
                repo_name: str,
                branch: str,
                start_date: datetime = None,
                end_date: datetime = None) -> github.PaginatedList.PaginatedList:
    """Get all commits in PRs with less than the required ammount of reviews"""
    try:
        client = github_auth(logger, token)
        repo: github.Repository.Repository = client.get_repo(repo_name)
    except github.GithubException as ghe:
        logger.error("Unable to get commits from repo %s: %s",
                     repo_name,
                     ghe)
        return ghe

    if start_date and end_date:
        commits = repo.get_commits(branch,
                                   "",
                                   since=start_date,
                                   until=end_date)
        return commits

    return repo.get_commits(branch)
