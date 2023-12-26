import re
import pdfplumber as pp
import pandas as pd
import pprint
from itertools import chain
from bank_parser import *
from ocr import run_ocr


def check_ocr(statement):
    with pp.open(statement) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        if len(text) == 0:
            run_ocr(statement)


def convert_csv(statement, bank, path, file_name):
    # mb not don't overwrite original file if user wants to keep non ocr version
    print(statement)
    check_ocr(statement)
    checks = ""
    withdraws = ""
    date = ""
    if bank == "Bank of America":
        checks = boa_get_checks(statement)
        withdraws = boa_get_withdrawals(statement)
        date = boa_get_date(statement)
    if bank == "Wells Fargo":
        checks = wf_get_checks(statement)
        # withdraws does not work
        withdraws = []
    if bank == "EastWest Bank":
        pass
    if bank == "Truist":
        checks = truist_get_checks(statement)
        withdraws = truist_get_withdrawals(statement)

    df = pd.DataFrame(data=checks, columns=["Check Number", "Amount"])
    df1 = pd.DataFrame(data=withdraws, columns=["Check Number", "Amount"])
    df["Check Number"] = df["Check Number"].astype(int)
    df.sort_values(by=["Check Number"], inplace=True)
    new_df = pd.concat([df, df1], axis=0)
    # remove negatives from string
    if bank == "Bank of America":
        new_df["Amount"] = new_df["Amount"].str[1:]
        new_df.insert(1, "Date", date)
        new_df.insert(2, "ID", "O01")
        new_df.insert(3, "Code", "5040")
        new_df["Description"] = "Other Debit"
        new_df["Date"] = pd.to_datetime(new_df["Date"])
        new_df["Date"] = new_df["Date"].dt.strftime("%m%d%y")
    new_df.to_csv(f"{path}/{file_name}.csv", index=False, header=False)


## Todo
# fix dates for single digit ones i.e 4 for april should be 04
# EastWest Bank implement

# file = "/Users/max/personalProjects/test/crashboa.pdf"
