#!/usr/bin/env python3

import argparse
import hashlib
import logging
import os
import sys
from github import Github, RateLimitExceededException
from datetime import datetime,timedelta
from time import sleep

def create_logger(name:str):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s: %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    
    # Use stdout as the stream to write log messages to
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Create logger with level INFO
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    return logger

def get_filename(file_name:str):
    basename:str = os.path.basename(file_name)
    segments = basename.split(".")
    segment_count = len(segments)
    if segment_count > 1:
        segments.pop()
        return ".".join(segments)
    else:
        return file_name
    
def write_commit_to_file(fp, repository, commit, reviews):
    commit_detail = commit.commit
    detail=f'{commit_detail.author.date},{reviews},{commit.sha},{commit_detail.author.name},{commit_detail.author.email},https://github.com/{repository}/commit/{commit.sha}\n'
    print(detail)
    writeout(fp, detail)
    fp.flush()

def writeout(fp, content:str):
    fp.write(content)
    print(content)

def main():
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
    logger.info(f"Reviewing commits from: https://github.com/{repository}")
    logger.info(f"Looking into branch: {args.branch}")

    # Authenticate against GitHub's API using Personal Access Token
    logger.info("Trying to authenticate against GitHub API")
    try:
        github_api = Github(args.github_pat)
    except Exception as e:
        logger.fatal(f"Unable to login to GitHub: {e}")
        sys.exit(1)

    # Calculate Start date and End date
    now = datetime.today()
    date_offset=7*args.weeks
    startDate = now - timedelta(days=now.weekday()+1,
                                hours=now.hour,
                                seconds=now.second,
                                minutes=now.minute,
                                microseconds=now.microsecond) - timedelta(days=date_offset)
    endDate = startDate + timedelta(days=date_offset)
    logger.info(f"Checking for commits between {startDate} and {endDate}")

    # Generating filename for the resultant CSV report
    fname = get_filename(args.filename)
    file_name = f"{fname}_{startDate.strftime('%Y-%m-%d')}_{endDate.strftime('%Y-%m-%d')}"
    csv_file = f"{file_name}.csv"
    fp = open(csv_file, "w", buffering=1)

    # Print headers
    fp.write("Commit Date,No. Reviews,Commit,Author,Email,Commit link\n")
    
    # 
    index=0
   
    try:
        repo = github_api.get_repo(repository)
    except Exception as e:
        logger.fatal(f"Unable to retreive repo {repository} info: {e}")
    
    try:
        commits = repo.get_commits(args.branch, "", since=startDate, until=endDate)
    except Exception as e:
        logger.fatal(f"Unable to get commits from repo {repository}: {e}")

    for commit in commits:
        while True:
            try:
                pull_requests = commit.get_pulls()

                if pull_requests.totalCount == 0:
                    print(f'no commits, adding {commit.sha}')
                    write_commit_to_file(fp, repository, commit, 0)
                    fp.flush()
                    index+=1
                else:
                    for pull_request in pull_requests:
                        while True:
                            try:
                                reviews = pull_request.get_reviews()
                                if reviews.totalCount < args.required_review_num:
                                    commit_detail = commit.commit
                                    write_commit_to_file(fp, repository, commit, reviews.totalCount)
                                    index+=1
                                break
                            except RateLimitExceededException:
                                print(f'{commit.sha} exceeded rate limit waiting')
                                sleep(3600/4)
                                continue
                            except Exception as e:
                                print(f'{commit.sha} unknown exception occurred')
                                print(f'{commit.sha} {e.args}')
                                sleep(3600/4)
                                continue
                break
            except Exception as e:
                print(f"An exception occurred: {e}")
                sleep(3600/4)
                continue
    fp.close()

    file_checksum = hashlib.md5(open(csv_file,'rb').read()).hexdigest()
    checksum_filename = f'{file_name}.hash'
    fp = open(checksum_filename, "w", buffering=1)

    writeout(fp,f"Checksum: {file_checksum}\n")
    writeout(fp,f"Records: {index}\n")
    writeout(fp,f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")

    fp.close()


if __name__ == "__main__":
    main()
