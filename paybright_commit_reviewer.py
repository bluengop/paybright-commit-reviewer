#!/usr/bin/env python3

"""PayBright Commit Reviewer"""

import argparse
import hashlib
import io
import logging
import os
import sys
from datetime import datetime, timedelta
from time import sleep
from github import Github, GithubException, RateLimitExceededException, UnknownObjectException


def create_logger(name: str) -> logging.Logger:
    """Function creating a logger"""
    fmt = '%(asctime)s - %(levelname)s: %(message)s'
    formatter = logging.Formatter(fmt=fmt,
                                  datefmt='%Y-%m-%d %H:%M:%S')

    # Use stdout as the stream to write log messages to
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Create logger with level INFO
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


def get_filename(file_name: str) -> str:
    """Function getting the filename for the resultant CSV report"""
    basename: str = os.path.basename(file_name)
    segments = basename.split(".")
    segment_count = len(segments)
    if segment_count > 1:
        segments.pop()
        return ".".join(segments)
    return file_name


def write_commit_to_file(logger: logging.Logger,
                         file: io.IOBase,
                         repository: str,
                         commit: str,
                         reviews: int):
    """Function to write the commits out to a CSV file"""
    commit_detail = commit.commit
    detail = (
        f'{commit_detail.author.date},'
        f'{reviews},'
        f'{commit.sha},'
        f'{commit_detail.author.name},'
        f'{commit_detail.author.email},'
        f'https://github.com/{repository}/commit/{commit.sha}\n'
    )
    logger.info(detail)

    writeout(logger, file, detail)

    file.flush()


def writeout(logger: logging.Logger,
             file: io.IOBase,
             content: str) -> None:
    """Writes content to both a file and through a logger"""
    file.write(content)
    logger.info(content)


def commit_report(logger: logging.Logger,
                  file: io.IOBase,
                  github_api: Github,
                  repository: str,
                  branch: str,
                  required_review_num: int,
                  start_date,
                  end_date,
                  csv_file: str,
                  file_name: str):
    """Creates the report of the commits with less reviews than required"""

    # Print headers
    file.write("Commit Date,No. Reviews,Commit,Author,Email,Commit link\n")

    index = 0

    # Retreive all commits from the repository ('repo' class)
    # and hold them inside 'commits' object (list of 'github.Commit.Commit')
    try:
        repo = github_api.get_repo(repository)
    except GithubException as ghe:
        logger.fatal("Unable to retreive repo %s info: %s",
                     repository,
                     ghe)
        sys.exit(2)

    try:
        commits = repo.get_commits(branch,
                                   "",
                                   since=start_date, until=end_date)
    except GithubException as ghe:
        logger.fatal("Unable to get commits from repo %s: %s",
                     repository,
                     ghe)
        sys.exit(3)

    # For each of the commits, get all the pulls.
    # If the number is 0
    for commit in commits:
        while True:
            try:
                # Get pulls from the commit
                pull_requests = commit.get_pulls()

                # If there is no pulls, add the commit sha
                if pull_requests.totalCount == 0:
                    logger.warning(f'No commits, adding {commit.sha}')
                    write_commit_to_file(logger, file, repository, commit, 0)
                    file.flush()
                    index += 1
                else:
                    for pull_request in pull_requests:
                        while True:
                            try:
                                reviews = pull_request.get_reviews()
                                if reviews.totalCount < required_review_num:
                                    write_commit_to_file(logger,
                                                         file,
                                                         repository,
                                                         commit,
                                                         reviews.totalCount)
                                    index += 1
                                break
                            except RateLimitExceededException:
                                logger.error(f'{commit.sha} exceeded rate limit waiting')
                                sleep(3600/4)
                                continue

                            except GithubException as excpt:
                                logger.error(f'{commit.sha} Unknown exception occurred')
                                logger.error(f'{commit.sha} {excpt.args}')
                                sleep(3600/4)
                                continue
                break

            except GithubException as excpt:
                print(f"An exception occurred: {excpt}")
                sleep(3600/4)
                continue

    file.close()

    file_checksum = hashlib.md5(open(csv_file, 'rb').read()).hexdigest()
    checksum_filename = f'{file_name}.hash'
    
    file = open(checksum_filename,
                "w",
                buffering=1,
                encoding="utf-8")

    writeout(logger, file, f"Checksum: {file_checksum}\n")
    writeout(logger, file, f"Records: {index}\n")
    writeout(logger, file, f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")

    file.close()


def main() -> None:
    """Main"""
    # Create logger
    logger = create_logger("paybright_commit_review")

    # Create argument parser
    parser = argparse.ArgumentParser(description="Paybright commit reviewer script")

    # Add arguments
    parser.add_argument("--github-pat",
                        help="GitHub's Personal Access Token to access repos",
                        type=str,
                        required=True)
    parser.add_argument("--repo",
                        help="GitHub's repo for the commit review",
                        type=str,
                        required=True)
    parser.add_argument("--branch",
                        help="Git branch to review inside the repo",
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

    # Format repo name
    repository = f"Paybright/{args.repo}"
    logger.info("Reviewing commits from: https://github.com/%s", repository)
    logger.info("Looking into branch: %s", args.branch)

    # Authenticate against GitHub's API using Personal Access Token
    logger.info("Trying to authenticate against GitHub API")
    try:
        github_api = Github(args.github_pat)
    except GithubException as excpt:
        logger.fatal("Unable to login to GitHub: %s", excpt)
        sys.exit(1)

    # Calculate Start date and End date
    now = datetime.today()
    date_offset = 7*args.weeks
    start_date = now - timedelta(days=now.weekday()+1,
                                 hours=now.hour,
                                 seconds=now.second,
                                 minutes=now.minute,
                                 microseconds=now.microsecond) - timedelta(days=date_offset)
    end_date = start_date + timedelta(days=date_offset)
    logger.info("Checking for commits between %s and %s", start_date, end_date)

    # Generating filename for the resultant CSV report
    fname = get_filename(args.filename)
    file_name = f"{fname}_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"
    csv_file = f"{file_name}.csv"
    file = open(csv_file,
                "w",
                buffering=1,
                encoding="utf-8")

    # Write down the report
    commit_report(logger,
                  file,
                  github_api,
                  repository,
                  args.branch,
                  args.required_review_num,
                  start_date,
                  end_date,
                  csv_file,
                  file_name)


if __name__ == "__main__":
    main()
