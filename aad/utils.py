import pathlib
import os
import re
from cleantext import clean


def create_folder(folder_path):
    pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)


def file_exists(file_path):
    return os.path.isfile(file_path)


def get_alphanumeric(str):
    pattern = re.compile("[\W_]+", re.UNICODE)
    return re.sub(pattern, "", str)


def get_file_name_from_fields(title, year, first_author):
    author = "-".join(get_alphanumeric(first_author.lower()).split(" "))

    title = clean(title, lower=True, no_line_breaks=True, no_punct=True)
    title_joined = "-".join(title.split(" "))
    name = f"{author}{year}_{title_joined}"

    return name
