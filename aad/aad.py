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
    COMPRESSED_BIB : ClassVar = "../data/acl_anthology_bib_w_abstract.bib.gz"
    BIB_FILE : ClassVar = COMPRESSED_BIB.replace(".gz", "")
    PROCESSED_DATA_PATH: ClassVar="../data/acl_anthology_w_abstract.parquet"

    

    def __init__(self, keywords:list,
                force_download:bool = False,
                fields:list=["title", "abstract"],
                filter_all:bool= True) -> None:
        self.keywords = keywords
        self.force_download = force_download
        self.df :pd.DataFrame= None
        self.filtered_df :pd.DataFrame= None#
        self.fields = fields
        self.filter_all = filter_all
        
        self.process_bib()

    def process_bib(self):
        if (not (utils.file_exists(AADSearch.COMPRESSED_BIB) or utils.file_exists(AADSearch.BIB_FILE))) or self.force_download:
            urllib.request.urlretrieve(AADSearch.ACLWEB_ANTH_URL, AADSearch.COMPRESSED_BIB)
            
        if (not utils.file_exists(AADSearch.BIB_FILE)) or self.force_download:
            with gzip.open(AADSearch.COMPRESSED_BIB, 'rb') as f_in:
                with open(AADSearch.BIB_FILE, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)


        if (not utils.file_exists(AADSearch.PROCESSED_DATA_PATH)) or self.force_download:
            with open(AADSearch.BIB_FILE, encoding="utf-8") as bibtex_file:
                bibtex_database = bibtexparser.load(bibtex_file)
                self.df =  self.parse_bib(bibtex_database.entries)
                self.df.to_parquet()
        else:
            self.df = pd.read_parquet(AADSearch.PROCESSED_DATA_PATH)

    def filter(self) -> pd.DataFrame:
        filter_str_lst = ["|".join([x.lower() for x in lst_]) for lst_ in self.keywords] 
        #self.filtered_df = self.df.copy()

        def _add_lower_case(row, fields):
            for f in fields:
                row[f"{f}_lower"] = row[f].lower() if row[f] is not None and len(row[f])>0 else ""
            return row

        processed_df = self.df.apply(_add_lower_case,   axis=1, args=(self.fields,),).copy()

        keep_lst = []
        for field_ in self.fields:
            field_df = processed_df.copy() 
            for filter_ in filter_str_lst:
                field_df = field_df[field_df[f"{field_}_lower"].astype(str).str.contains(filter_)]
            keep_lst.extend(field_df["ID"].values)
        

        keep_lst = list(set(keep_lst))
        self.filtered_df = self.df[self.df["ID"].isin(keep_lst)]
        
        return self.filtered_df

    def download_papers(self, folder_name):
        if self.filtered_df is None:
            self.filter()
        utils.create_folder(folder_name)
        self.filtered_df.to_csv(f"{folder_name}/papers.csv")

        for _, row in self.filtered_df.iterrows():
            try:
                url = row['url'] if row["url"].endswith(".pdf")  else row['url'] +".pdf"
                
                author =row["author"].split(",")[0] if row["author"] is not None and len(row["author"]) >0 else ""
                name = utils.get_file_name_from_fields(row["title"], row["year"], author)

                urllib.request.urlretrieve(url, os.path.join(folder_name, f"{name}.pdf"))
            except Exception as e:
                print(f"Error occurred for URL { row['url']}")
        