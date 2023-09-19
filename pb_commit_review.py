#!/usr/bin/env python3

"""Paybright Commit Review v2.0.0"""

import argparse
import sys
import logging
from datetime import datetime, timedelta
import github


def setup_logger() -> logging.Logger:
    """Configure logging"""
    logging.basicConfig(stream=sys.stdout,
                        format='[%(asctime)s] - %(levelname)s: %(message)s',
                        level=logging.INFO)
    return logging.getLogger(__name__)


def parse_arguments():
    """Parse necessary arguments"""
    parser = argparse.ArgumentParser(description="Paybright commit reviewer script")

    parser.add_argument("--github-pat",
                        help="GitHub's Personal Access Token to access repos",
                        type=str,
                        required=True)
    parser.add_argument("--filename",
                        help="Name for the CSV report file",
                        type=str,
                        default="export.csv")
    parser.add_argument("--required_review_num",
                        help="Required amount of reviews",
                        type=int,
                        default=2)
    parser.add_argument("--weeks",
                        help="Number of weeks to go back",
                        type=int,
                        default=12)

    args = parser.parse_args()
    return args


def calculate_timerange(weeks: int) -> tuple[datetime, datetime]:
    """Calculates datetimes for start and end dates"""
    now = datetime.today()
    date_offset = 7 * weeks
    start_date = now - timedelta(days=now.weekday()+1,
                                 hours=now.hour,
                                 seconds=now.second,
                                 minutes=now.minute,
                                 microseconds=now.microsecond) - timedelta(days=date_offset)
    end_date = start_date + timedelta(days=date_offset)
    logger.info("Start date: %s", start_date)
    logger.info("End date: %s", end_date)

    return start_date, end_date


def generate_csv() -> str:
    """Generates a CSV with the Commits that need to be reviewed"""
    path: str = "/csv/path"
    return path

"""===== Move this function to a github.py client ====="""
def get_commits_by_dates(client: github.Github,
                         repo_name: str,
                         branch: str,
                         start_date: datetime,
                         end_date: datetime) -> github.PaginatedList.PaginatedList[github.Commit.Commit]:
    """Get all commits in PRs with less than the required ammount of reviews"""
    try:
        repo: github.Repository.Repository = client.get_repo(repo_name)
        commits = repo.get_commits(branch,
                                   "",
                                   since=start_date, until=end_date)
    except github.GithubException as ghe:
        logger.fatal("Unable to get commits from repo %s: %s",
                     repo_name,
                     ghe)

    return commits


def github_login(token: str) -> github.Github:
    """Authenticate against GitHub API"""
    try:
        auth = github.Github(token)
        return auth
    except github.GithubException as ghe:
        logger.error("Unable to authenticate against GitHub: %s",
                     ghe)
        return None
"""===== Move this function to a github.py client ====="""


def main() -> None:
    """Main"""
    logger.info("Hello, Paybright!")
    github_login("secret1234")
    sys.exit(0)


if __name__ == "__main__":
    logger = setup_logger()
    main()
