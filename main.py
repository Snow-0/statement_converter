import re
import pdfplumber as pp
import pandas as pd 
import pprint 
from itertools import chain


def boa_get_checks(statement):

    # looks for a pattern that has date, check number, negative amount 
    pattern = re.compile(r"\d{2}/\d{2}/\d{2} (\d+)\*? (-?\d{1,3}(?:,\d{3})*\.\d{2})")
    a_list = []

    with pp.open(statement) as pdf:
        pages = pdf.pages

        for page in pages:
            text = page.extract_text()
            for line in text.split("\n"):
                result = pattern.findall(line)
                if len(result) != 0:
                    a_list.append(result)


    # flatten the nested tuple list 
    a_list = list(chain.from_iterable(a_list))

    return a_list


def boa_get_withdrawals(statement):
    # find the pattern MM/DD/YYYY DESC -amount
    pattern = re.compile(r"(\d{2}/\d{2}/\d{2}.*?)\s*(.+?)\**\s*(-\d{1,3}(?:,\d{3})*\.\d{2})")

    with pp.open(statement) as pdf:
        pages = pdf.pages
        matching_pages = []

        filtered_list = [] 

        # get only pages that have withdrawals/checks in them 
        for page_number, page in enumerate(pages, start=1):
            text = page.extract_text()
            
            if "Withdrawals" in text:
                matching_pages.append(page)

        # parse through withdrawal pages 
        for page in matching_pages:   
            text = page.extract_text()

            for line in text.split("\n"):
                result = pattern.findall(line)
                # edge case where the checks and other withdrawal amounts are 
                # on the same page
                ## not sure how to exclude this in regex pattern search
                for tup in result:
                    if not tup[1].isdigit():
                        filtered_list.append(result)  

        
        # # add 9999 check number
        filtered_list = list(chain.from_iterable(filtered_list))
        withdraw_amt = [("9999", amt[2]) for amt in filtered_list]
        return withdraw_amt


def truist_get_checks(statement):

    # looks for a pattern that has date, check number, negative amount 
    pattern = re.compile(r"\d{2}/\d{2} \**(\d+)? (\d{1,3}(?:,\d{3})*\.\d{2})")
    a_list = []

    with pp.open(statement) as pdf:
        pages = pdf.pages

        for page in pages:
            text = page.extract_text()
            for line in text.split("\n"):
                result = pattern.findall(line)
                if len(result) != 0:
                    a_list.append(result)


    # flatten the nested tuple list 
    a_list = list(chain.from_iterable(a_list))

    return a_list


def truist_get_withdrawals(statement):
    # find the pattern MM/DD/YYYY DESC -amount
    pattern = re.compile(r"(\d{2}/\d{2})\s+\**(.+?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})")

    with pp.open(statement) as pdf:
        pages = pdf.pages
        matching_pages = []

        filtered_list = [] 

        # get only pages that have withdrawals in them 
        for page_number, page in enumerate(pages, start=1):
            text = page.extract_text()
            
            if "withdrawals" in text:
                matching_pages.append(page)

        # parse through withdrawal pages 
        for page in matching_pages:   
            text = page.extract_text()

            for line in text.split("\n"):
                result = pattern.findall(line)
                print(result)
                # edge case where the checks and other withdrawal amounts are 
                # on the same page
                ## not sure how to exclude this in regex pattern search
                for tup in result:
                    if not tup[1].isdigit():
                        filtered_list.append(result)  
        
        # # add 9999 check number
        ## 
        filtered_list = list(chain.from_iterable(filtered_list))
        withdraw_amt = [("9999", amt[2]) for amt in filtered_list]
        return withdraw_amt




def convert_csv(statement, bank, path):
    checks = ""
    withdraws = ""
    if bank == "Bank of America":
        checks = boa_get_checks(statement)
        withdraws = boa_get_withdrawals(statement) 
    if bank == "Wells Fargo":
        pass 
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
    #remove negatives from string 
    new_df["Amount"] = new_df["Amount"].str[1:]
    new_df.to_csv(f"{path}/output.csv", index=False)
    



file = "test/sample.pdf"
file2 = "test/testdoc.pdf"
file3 = "test/test2.pdf"
file4 = "test/test4.pdf"
file5 = "bofatest.pdf"



# convert_csv(file)
# convert_csv(file2)
# convert_csv(file3)
# convert_csv(file4, "Bank of America")

# convert_csv(file4, "Truist Bank")
# print(truist_get_checks(file4))
# print(truist_get_withdrawals(fßßile4))
# print(boa_get_withdrawals(file4))











