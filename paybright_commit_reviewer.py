#!/usr/bin/env python3

"""Paybright Commit Review v2.0.0"""

import argparse
import sys
import os
import json
import logging
from datetime import datetime, timedelta
from git_repo import get_commits


PROJECT = 'Paybright'


def setup_logger() -> logging.Logger:
    """Configure logging"""
    logging.basicConfig(stream=sys.stdout,
                        format='[%(asctime)s] - %(levelname)s: %(message)s',
                        level=logging.DEBUG)
    return logging.getLogger(__name__)


def parse_arguments():
    """Parse necessary arguments"""
    parser = argparse.ArgumentParser(description="Paybright commit reviewer script")

    parser.add_argument("--access-token",
                        help="Access Token to access Git repos (PAT)",
                        default=os.getenv("GH_PAT"),
                        type=str,
                        )
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


def calculate_timerange(logger: logging.Logger,
                        weeks: int) -> dict:
    """Calculates datetimes for start and end dates"""
    timerange = {"start_date": None, "end_date": None}
    now = datetime.today()
    date_offset = 7 * weeks
    timerange["start_date"] = now - timedelta(days=now.weekday()+1,
                                              hours=now.hour,
                                              seconds=now.second,
                                              minutes=now.minute,
                                              microseconds=now.microsecond) - timedelta(days=date_offset)
    timerange["end_date"] = timerange["start_date"] + timedelta(days=date_offset)
    logger.info("Start date: %s", timerange["start_date"])
    logger.info("End date: %s", timerange["end_date"])

    return timerange


def load_config(path: str) -> dict:
    """Load config file with `"repo": "branch"` info"""
    with open(path, "r", encoding="utf-8") as conf:
        data = json.load(conf)
    conf.close()

    return data


def generate_csv(logger: logging.Logger,
                 inputs: list,
                 path: str) -> None:
    """Generates a CSV with the results"""
    contents = [['Commit Date,No. Reviews,Commit,Author,Email,Commit link']]
    logger.info("Writing content to %s", path)

    try:
        with open(path, "a", encoding="utf-8") as csv:
            contents.append(inputs)
            for row in contents:
                csv.write(str(row))
        csv.close()
    except Exception as err:
        logger.error("Unable to write contents to %s: %s",
                     path,
                     err)
    return


def check_commit_pulls(logger: logging.Logger,
                       commits,
                       required_reviews: int):
    """Check Pull-Requests per each Commit to check minimum reviews"""
    results = []

    for commit in commits:
        commit_detail = commit.commit
        pull_requests = commit.get_pulls()

        if pull_requests.totalCount == 0:
            row = (
                f'{commit_detail.author.date},'
                '0,'
                f'{commit.sha},'
                f'{commit_detail.author.name},'
                f'{commit_detail.author.email},'
                f'https://github.com/{repository}/commit/{commit.sha}\n'
            )
            logger.debug("No PR associated to this commit, adding %s", row)
            continue

        for pull_request in pull_requests:
            reviews = pull_request.get_reviews()
            if reviews.totalCount < required_reviews:
                row = (
                    f'{commit_detail.author.date},'
                    f'{reviews.totalCount},'
                    f'{commit.sha},'
                    f'{commit_detail.author.name},'
                    f'{commit_detail.author.email},'
                    f'https://github.com/{PROJECT}/commit/{commit.sha}\n'
                )
                logger.debug("Apending found commit: %s", row)
                results.append(row)

    return results


def main() -> None:
    """Main"""
    # Setup logger and parse arguments
    logger = setup_logger()
    args = parse_arguments()

    # Calculate timerange to retreive commits
    timerange = calculate_timerange(logger, args.weeks)

    # Load config
    config = load_config("./repos-branches.json")

    # Check repo by repo
    for repo in config:
        repository = f"{PROJECT}/{repo}"
        commits = get_commits(logger=logger,
                              token=args.access_token,
                              repo_name=repository,
                              branch=config[repo],
                              start_date=timerange["start_date"],
                              end_date=timerange["end_date"])

        results = check_commit_pulls(logger=logger,
                                     commits=commits,
                                     required_reviews=args.required_review_num)
        
        generate_csv(logger=logger,
                     inputs=results,
                     path=f"./export_{repo}_{timerange['end_date']}.csv")


if __name__ == "__main__":
    main()
    sys.exit(0)
