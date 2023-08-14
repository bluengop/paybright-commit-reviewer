from headers import print_headers,get_filename,writeout;
from github import Github, RateLimitExceededException;
import hashlib
from datetime import datetime,timedelta;
from time import sleep;
import sys;
import os


PAT=sys.argv[1]
repository= f'Paybright/{sys.argv[2]}'  #"Paybright/Looker_paybright_project"
file_name = get_filename(sys.argv[3]) ##"export.csv"
branch = sys.argv[4]
required_review_num= int(sys.argv[5] or '2') # required amount of reviews
weeks=12 # weeks to go back

print(f'{sys.argv}')

now = datetime.now()

file_date_format = now.strftime("%Y-%m-%d")

github_api = Github(PAT)

now = datetime.today()
# startDate = datetime(2021,6,1,0,0,0,0)  #datetime.strptime("01/06/2021", '%d/%m/%y')
# endDate = datetime(2022,7,1,0,0,0,0)  #datetime.strptime("01/06/2021", '%d/%m/%y')

date_offset=7*weeks
startDate = now - timedelta(days=now.weekday()+1, hours=now.hour, seconds=now.second ,minutes=now.minute,microseconds=now.microsecond) -  timedelta(days=date_offset)
endDate = startDate + timedelta(days=date_offset)

file_name = f"{file_name}_{startDate.strftime('%Y-%m-%d')}_{endDate.strftime('%Y-%m-%d')}"
csv_file =f"{file_name}.csv"
fp = open(csv_file, "w", buffering=1)

index=0
print_headers(fp)

repo = github_api.get_repo(repository)
commits = repo.get_commits(branch, "", since=startDate, until=endDate)



def write_commit_to_file(fp,repository,commit,reviews):
    commit_detail = commit.commit
    detail=f'{commit_detail.author.date},{reviews},{commit.sha},{commit_detail.author.name},{commit_detail.author.email},https://github.com/{repository}/commit/{commit.sha}\n'
    print(detail)
    writeout(fp,detail)
    fp.flush()



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