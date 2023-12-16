import re
import pdfplumber as pp
import pandas as pd 
import pprint 
from itertools import chain


file = "sample.pdf"
file2 = "testdoc.pdf"
file3 = "test2.pdf"

def get_checks(statement):

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


def get_withdrawals(statement):
    pattern = re.compile(r"(\d{2}/\d{2}/\d{2}.*?)\s*(.+?)\s*(-\d{1,3}(?:,\d{3})*\.\d{2})")

    with pp.open(statement) as pdf:
        pages = pdf.pages
        matching_pages = []

        filtered_list = [] 

        # get only pages that have withdrawals in them 
        for page_number, page in enumerate(pages, start=1):
            text = page.extract_text()
            
            if "Withdrawals" in text:
                matching_pages.append(page)

        # parse through withdrawal pages 
        for page in matching_pages[1:]:   
            text = page.extract_text()

            for line in text.split("\n"):
                result = pattern.findall(line)
            
                
                for tup in result:
                    if not tup[1].isdigit():
                        filtered_list.append(result)             
        
        # # add 9999 check number
        ## 
        filtered_list = list(chain.from_iterable(filtered_list))
        withdraw_amt = [("9999", amt[2]) for amt in filtered_list]
        return withdraw_amt

## NOTE: Possible edge case in which checks and withdrawals 


def convert_csv(checks, withdraws): 
            
    df = pd.DataFrame(data=checks, columns=["Check Number", "Amount"])
    df1 = pd.DataFrame(data=withdraws, columns=["Check Number", "Amount"])
    df["Check Number"] = df["Check Number"].astype(int)
    df.sort_values(by=["Check Number"], inplace=True)
    new_df = pd.concat([df, df1], axis=0)
    #remove negatives from string 
    new_df["Amount"] = new_df["Amount"].str[1:]
    new_df.to_csv("output.csv", index=False)
    
# test cases
# a = get_checks(file)
# a = get_checks(file2)
a = get_checks(file3)

# test cases
# b = get_withdrawals(file)
# b = get_withdrawals(file2)
b = get_withdrawals(file3)     
            
    

        


  



        
        