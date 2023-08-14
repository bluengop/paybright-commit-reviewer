from importlib.resources import path
import os
from posixpath import basename
def print_headers(fp):
    fp.write("Commit Date,No. Reviews,Commit,Author,Email,Commit link\n")


def print_headers_audit(fp):
    fp.write("commit_sha,author,email,date,message,commit_url\n")


def get_filename(file_name:str):
    basename:str = os.path.basename(file_name)
    segments = basename.split(".")
    segment_count = len(segments)
    if segment_count>1:
        segments.pop()
        return ".".join(segments)
    else:
        return file_name
    


def writeout(fp,content:str):
    fp.write(content)
    print(content)