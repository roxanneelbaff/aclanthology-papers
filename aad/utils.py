


import pathlib
import  os
from pathlib import Path
import re

def create_folder(folder_path):
    pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)

def file_exists(file_path):
    return os.path.isfile(file_path)


def get_alphanumeric(str):
    pattern = re.compile('[\W_]+', re.UNICODE)
    return  re.sub(pattern, '', str)

def get_file_name_from_fields(title, year, first_author):
    author = "-".join(get_alphanumeric(first_author.lower()).split(" "))
    title = "-".join(get_alphanumeric(title.lower()).split(" "))
    name = f"{author}{year}_{title}"

    return name