import os
from typing import ClassVar
import urllib.request
import pandas as pd
import urllib.request
import gzip
import shutil
import bibtexparser
import aad.utils as utils
from cleantext import clean


class AADSearch:
    ACLWEB_ANTH_URL: ClassVar = "https://aclanthology.org/anthology+abstracts.bib.gz"
    COMPRESSED_BIB: ClassVar = "../data/acl_anthology_bib_w_abstract.bib.gz"
    BIB_FILE: ClassVar = COMPRESSED_BIB.replace(".gz", "")

    PROCESSED_DATA_PATH: ClassVar = "../data/acl_anthology_w_abstract.parquet"

    def __init__(
        self,
        keywords: list,
        force_download: bool = False,
        fields: list = ["title", "abstract"],
        filter_all: bool = True,
    ) -> None:
        self.keywords = keywords
        self.force_download = force_download
        self.df: pd.DataFrame = None
        self.filtered_df: pd.DataFrame = None  #
        self.fields = fields
        self.filter_all = filter_all

        self.process_bib()

    @staticmethod
    def _clean_txt(row, fields):
        for f in fields:
            row[f"{f}_clean"] = clean(row[f], no_currency_symbols=True, no_punct=True)
        return row

    def process_bib(self):
        if (
            not (
                utils.file_exists(AADSearch.COMPRESSED_BIB)
                or utils.file_exists(AADSearch.BIB_FILE)
            )
        ) or self.force_download:
            utils.create_folder("../data")
            print("Retrieving bib from web...")

            urllib.request.urlretrieve(
                AADSearch.ACLWEB_ANTH_URL, AADSearch.COMPRESSED_BIB
            )

        if (not utils.file_exists(AADSearch.BIB_FILE)) or self.force_download:
            with gzip.open(AADSearch.COMPRESSED_BIB, "rb") as f_in:
                print("copying file...")
                with open(AADSearch.BIB_FILE, "wb") as f_out:
                    print("copying file...")
                    shutil.copyfileobj(f_in, f_out)

        if (
            not utils.file_exists(AADSearch.PROCESSED_DATA_PATH)
        ) or self.force_download:
            with open(AADSearch.BIB_FILE, encoding="utf-8") as bibtex_file:
                print("Loading bib...")
                bibtex_database = bibtexparser.load(bibtex_file)
                print("Loading dataframe...")
                self.df = pd.DataFrame(bibtex_database.entries)
                print("saving dataframe...")
                self.df.to_parquet(AADSearch.PROCESSED_DATA_PATH)
        else:
            self.df = pd.read_parquet(AADSearch.PROCESSED_DATA_PATH)

    def filter(self) -> pd.DataFrame:
        filter_str_lst = [f"({'|'.join(lst_)})" for lst_ in self.keywords]
        print(f"The processed keywords are: {filter_str_lst}")

        processed_df = self.df[self.fields + ["ID"]].copy()
        processed_df.fillna("", inplace=True)
        processed_df = processed_df.apply(
            AADSearch._clean_txt, args=(self.fields,), axis=1
        )
        keep_lst = []

        for field_ in self.fields:
            field_df = processed_df.copy()

            for f in filter_str_lst:
                field_df = field_df[
                    field_df[f"{field_}_clean"].str.contains(rf"\b({f})", case=False)
                ]
            keep_lst.extend(field_df["ID"].values)

        keep_lst = list(set(keep_lst))
        self.filtered_df = self.df[self.df["ID"].isin(keep_lst)]
        print(f"There are {len(self.filtered_df)} papers")

        return self.filtered_df

    def download_papers(self, folder_name: str, overview_only=False):
        if self.filtered_df is None:
            self.filter()
        keep_cols = [
            "url",
            "year",
            "editor",
            "title",
            "ENTRYTYPE",
            "ID",
            "booktitle",
            "author",
            "journal",
            "note",
        ]
        utils.create_folder(folder_name)
        self.filtered_df[keep_cols].to_csv(f"{folder_name}/papers.csv")

        if not overview_only:
            self.filtered_df = self.filtered_df.apply(
                                                AADSearch._download_url,
                                                axis=1,
                                                args=(folder_name,))
            self.filtered_df[keep_cols + ["local_path"]].to_csv(
                f"{folder_name}/papers_w_local_links.csv"
            )

    def _download_url(row, folder_name):
        try:
            url = row["url"] if row["url"].endswith(".pdf") else row["url"] + ".pdf"
            row["local_path"] = ""
            author = (
                row["author"].split(",")[0]
                if row["author"] is not None and len(row["author"]) > 0
                else ""
            )
            name = utils.get_file_name_from_fields(row["title"],
                                                   row["year"],
                                                   author)

            new_filename, _ = urllib.request.urlretrieve(
                url, os.path.join(folder_name, f"{name}.pdf")
            )
            row["local_path"] = new_filename
        except Exception as e:
            print(f"Error occurred for URL { row['url']}" f"with {e}")
        return row


def download_from_urls(url_arr: list, folder_name: str):
    utils.create_folder(folder_name)
    for url in url_arr:
        try:
            url = url if url.endswith(".pdf") else url + ".pdf"

            name = url.split("/")[-1].replace(".pdf", "")

            urllib.request.urlretrieve(url, os.path.join(folder_name, f"{name}.pdf"))
        except Exception as e:
            print(f"Error occurred for URL {url}" f"with {e}")
