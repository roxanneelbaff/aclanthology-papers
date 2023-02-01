import os
from typing import ClassVar
import urllib.request
import pandas as pd
import urllib.request
import gzip
import shutil
import bibtexparser
import aad.utils as utils


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

    def process_bib(self):
        if (
            not (
                utils.file_exists(AADSearch.COMPRESSED_BIB)
                or utils.file_exists(AADSearch.BIB_FILE)
            )
        ) or self.force_download:
            urllib.request.urlretrieve(
                AADSearch.ACLWEB_ANTH_URL, AADSearch.COMPRESSED_BIB
            )

        if (not utils.file_exists(AADSearch.BIB_FILE)) or self.force_download:
            with gzip.open(AADSearch.COMPRESSED_BIB, "rb") as f_in:
                with open(AADSearch.BIB_FILE, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

        if (
            not utils.file_exists(AADSearch.PROCESSED_DATA_PATH)
        ) or self.force_download:
            with open(AADSearch.BIB_FILE, encoding="utf-8") as bibtex_file:
                bibtex_database = bibtexparser.load(bibtex_file)
                self.df = pd.DataFrame(bibtex_database.entries)
                self.df.to_parquet(AADSearch.PROCESSED_DATA_PATH)
        else:
            self.df = pd.read_parquet(AADSearch.PROCESSED_DATA_PATH)

    def filter(self) -> pd.DataFrame:
        filter_str_lst = [
            f"({'|'.join([x.lower() for x in lst_])})" for lst_ in self.keywords
        ]
        # filter_str = "&".join([f"({'|'.join([x.lower() for x in lst_])})" for lst_ in self.keywords])
        # filter_str = f"({filter_str})"
        # self.filtered_df = self.df.copy()
        # print(filter_str)
        def _add_lower_case(row, fields):
            for f in fields:
                row[f"{f}_lower"] = row[f].lower() if row[f] is not None else ""
            return row

        processed_df = self.df[self.fields + ["ID"]].copy()
        processed_df.fillna("", inplace=True)
        processed_df = processed_df.apply(
            _add_lower_case,
            axis=1,
            args=(self.fields,),
        )

        keep_lst = []
        for field_ in self.fields:
            field_df = processed_df.copy()
            for f in filter_str_lst:
                ##print(f)
                field_df = field_df[
                    field_df[f"{field_}_lower"].astype(str).str.contains(f)
                ]
            keep_lst.extend(field_df["ID"].values)

        keep_lst = list(set(keep_lst))
        self.filtered_df = self.df[self.df["ID"].isin(keep_lst)]
        print(f"There are {len(self.filtered_df)} papers")

        return self.filtered_df

    def download_papers(self, folder_name):
        if self.filtered_df is None:
            self.filter()
        utils.create_folder(folder_name)
        self.filtered_df[
            [
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
        ].to_csv(f"{folder_name}/papers.csv")

        for _, row in self.filtered_df.iterrows():
            try:
                url = row["url"] if row["url"].endswith(".pdf") else row["url"] + ".pdf"

                author = (
                    row["author"].split(",")[0]
                    if row["author"] is not None and len(row["author"]) > 0
                    else ""
                )
                name = utils.get_file_name_from_fields(
                    row["title"], row["year"], author
                )

                urllib.request.urlretrieve(
                    url, os.path.join(folder_name, f"{name}.pdf")
                )
            except Exception as e:
                print(f"Error occurred for URL { row['url']}")


def download_from_urls(url_arr: list, folder_name):
    utils.create_folder(folder_name)
    for url in url_arr:
        try:
            url = url if url.endswith(".pdf") else url + ".pdf"

            name = url.split("/")[-1].replace(".pdf", "")

            urllib.request.urlretrieve(url, os.path.join(folder_name, f"{name}.pdf"))
        except Exception as e:
            print(f"Error occurred for URL { url}")
