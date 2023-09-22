#!/usr/bin/env python3

"""Paybright Commit Review v2.0.0"""

import argparse
import sys
import os
import csv
import json
import logging
from datetime import datetime, timedelta
from git_repo import get_commits


PROJECT = 'Paybright'
CSV_FIELDS = [
    'Commit Date',
    'No. Reviews',
    'Commit',
    'Author',
    'Email',
    'Commit link'
]


class CommitInfo:
    """Class to hold Commit information"""
    def __init__(self, date, reviews, sha, author, email, url):
        self.date = date
        self.reviews = reviews
        self.sha = sha
        self.author = author
        self.email = email
        self.url = url

    def list_info(self) -> list:
        """Print Commit information as list"""
        return [
            str(self.date),
            str(self.reviews),
            str(self.sha),
            str(self.author),
            str(self.email),
            str(self.url)
        ]


def setup_logger(loglevel: str) -> logging.Logger:
    """Configure logging"""
    levels = {
        "FATAL",
        "ERROR",
        "WARN",
        "INFO",
        "DEBUG",
        "TRACE",
        "ALL",
        "OFF"
    }
    if loglevel not in levels:
        loglevel = "INFO"

    # Get logging level numeric value 
    log_level = getattr(logging, loglevel)

    # Logging config
    logging.basicConfig(stream=sys.stdout,
                        format='[%(asctime)s] - %(levelname)s: %(message)s',
                        level=log_level)

    return logging.getLogger(__name__)


def parse_arguments():
    """Parse necessary arguments"""
    parser = argparse.ArgumentParser(description="Paybright commit reviewer script")

    parser.add_argument("--access-token",
                        help="Access Token to access Git repos (PAT)",
                        default=os.getenv("GH_PAT"),
                        type=str,
                        )
    parser.add_argument("--required_review_num",
                        help="Required amount of reviews",
                        type=int,
                        default=2)
    parser.add_argument("--weeks",
                        help="Number of weeks to go back",
                        type=int,
                        default=12)
    parser.add_argument("--loglevel",
                        help="Loglevel for the script",
                        type=str,
                        default="INFO")

    return parser.parse_args()


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
                 fields: list,
                 inputs: list,
                 csv_path: str) -> None:
    """Generate a CSV file from a list of string lists"""
    rows = []

    for line in inputs:
        logger.debug("Appending line %s", line)
        rows.append(line)

    # Don't write empty CSV files
    if len(rows) > 1:

        try:
            logger.info("Generating CSV file: %s",
                        csv_path)
            with open(csv_path, "w", encoding="utf-8") as file:
                write = csv.writer(file)
                write.writerow(fields)
                write.writerows(rows)
            file.close()

        except FileNotFoundError:
            logger.error("File %s not found",
                         csv_path)

        except OSError as ose:
            logger.error("OS error occurred trying to open %s: %s",
                         csv_path,
                         ose)

        except Exception as err:
            logger.error("Unable to write CSV file %s: %s",
                         csv_path,
                         err)


#def generate_hashfile():
#   file_checksum = hashlib.md5(open(csv_file,'rb').read()).hexdigest()
#   checksum_filename = f'{file_name}.hash'
#   fp = open(checksum_filename,"w",buffering=1)
#   writeout(fp,f"Checksum: {file_checksum}\n")
#   writeout(fp,f"Records: {index}\n")
#   writeout(fp,f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")


def check_commit_pulls(logger: logging.Logger,
                       commits,
                       required_reviews: int):
    """Check Pull-Requests per each Commit to check minimum reviews"""
    results = []

    for commit in commits:

        # Write commit information
        row = CommitInfo(
            date=commit.commit.author.date,
            reviews=0,
            sha=commit.sha,
            author=commit.commit.author.name,
            email=commit.commit.author.email,
            url=f"https://github.com/{PROJECT}/commit/{commit.sha}"
        )

        # Get PRs associated to the commit
        pull_requests = commit.get_pulls()

        # If the commit has no PR, add it with 0 reviews
        if pull_requests.totalCount == 0:
            logger.info("No PR associated to this commit, adding %s",
                        commit.sha)
            logger.debug("Full commit information: %s",
                         row.list_info())

            results.append(row.list_info())
            continue

        # Check the number of reviews of each PR
        for pull_request in pull_requests:
            reviews = pull_request.get_reviews()

            # Skip commit if reviews reach the required number
            if reviews.totalCount < required_reviews:
                logger.info("Apending found commit: %s",
                            commit.sha)
                logger.debug("Full commit information: %s",
                             row.list_info())

                row.reviews = reviews.totalCount
                results.append(row.list_info())

    return results


def main() -> None:
    """Main"""

    # Setup logger and parse arguments
    args = parse_arguments()
    logger = setup_logger(args.loglevel.upper())

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
                              start_date=timerange['start_date'],
                              end_date=timerange['end_date'])

        results = check_commit_pulls(logger=logger,
                                     commits=commits,
                                     required_reviews=args.required_review_num)

        # Generate CSV file with results
        csv_filename = (
            f"{repo}_"
            f"{timerange['start_date'].strftime('%Y-%m-%d')}_"
            f"{timerange['end_date'].strftime('%Y-%m-%d')}.csv"
        )
        generate_csv(logger=logger,
                     fields=CSV_FIELDS,
                     inputs=results,
                     csv_path=f"./{csv_filename}")


if __name__ == "__main__":
    main()
    sys.exit(0)
