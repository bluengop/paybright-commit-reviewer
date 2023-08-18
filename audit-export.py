from headers import print_headers,get_filename,writeout
from github import Github, RateLimitExceededException
import hashlib
from datetime import datetime,timedelta
from time import sleep
import sys
import argparse

def write_commit_to_file(fp,repository,commit,reviews):
    commit_detail = commit.commit
    detail=f'{commit_detail.author.date},{reviews},{commit.sha},{commit_detail.author.name},{commit_detail.author.email},https://github.com/{repository}/commit/{commit.sha}\n'
    print(detail)
    writeout(fp,detail)
    fp.flush()

def main():
    # Create argument parser
    parser = argparse.ArgumentParser(description="Paybright commit reviewer script")

    # Add arguments
    parser.add_argument("--github-pat",
                        help="GitHub's Personal Access Token to access repos",
                        type=str,
                        required=True)
    parser.add_argument("--repository",
                        help="GitHub's repo for the commit review",
                        type=str,
                        required=True)      ### repository= f'Paybright/{sys.argv[2]}'  #"Paybright/Looker_paybright_project"
    parser.add_argument("--filename",
                        help="Name for the CSV report file",
                        type=str,
                        required=True)      ### filename = get_filename(sys.argv[3])    #"export.csv"
    parser.add_argument("--branch",
                        help="Git branch to review inside the repo",
                        type=str,
                        required=True)
    parser.add_argument("--required_review_num",
                        help="Required amount of reviews",
                        type=int,
                        default=2)
    parser.add_argument("--weeks",
                        help="Number of weeks to go back",
                        type=int,
                        default=12)
    
    args = parser.parse_args()

    # Authenticate against GitHub's API using Personal Access Token
    github_api = Github(args.github_pat)

    # Calculate Start date and End date
    now = datetime.today()

    date_offset=7*args.weeks

    startDate = now - timedelta(days=now.weekday()+1,
                                hours=now.hour,
                                seconds=now.second,
                                minutes=now.minute,
                                microseconds=now.microsecond) - timedelta(days=date_offset)
    endDate = startDate + timedelta(days=date_offset)

    # Generating filename for the resultant CSV report
    file_name = f"{args.filename}_{startDate.strftime('%Y-%m-%d')}_{endDate.strftime('%Y-%m-%d')}"
    csv_file = f"{file_name}.csv"
    fp = open(csv_file, "w", buffering=1)
    print_headers(fp)
    
    index=0
   
    repo = github_api.get_repo(args.repository)
    commits = repo.get_commits(args.branch, "", since=startDate, until=endDate)

    for commit in commits:
        while True:
            try:
                pull_requests = commit.get_pulls()

                if pull_requests.totalCount == 0:
                    print(f'no commits, adding {commit.sha}')
                    write_commit_to_file(fp,repository,commit,0)
                    # writeout(fp,f'{commit_detail.author.date},0,{commit.sha},{commit_detail.author.name},{commit_detail.author.email},https://github.com/{repository}/commit/{commit.sha}\n')
                    fp.flush()
                    index+=1
                else:
                    for pull_request in pull_requests:
                        completed=False
                        while True:
                            try:
                                reviews = pull_request.get_reviews()
                                if reviews.totalCount < required_review_num:
                                    commit_detail = commit.commit
                                    write_commit_to_file(fp,repository,commit,reviews.totalCount)
                                    # writeout(fp,f'{commit_detail.author.date},{reviews.totalCount},{commit.sha},{commit_detail.author.name},{commit_detail.author.email},https://github.com/{repository}/commit/{commit.sha}\n')
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
    fp = open(checksum_filename,"w",buffering=1)

    writeout(fp,f"Checksum: {file_checksum}\n")
    writeout(fp,f"Records: {index}\n")
    writeout(fp,f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")


    fp.close()


if __name__ == "__main__":
    main()
