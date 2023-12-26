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
    pattern = re.compile(
        r"(\d{2}/\d{2}/\d{2}.*?)\s*(.+?)\**\s*(-\d{1,3}(?:,\d{3})*\.\d{2})"
    )

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


def boa_get_date(statement):
    pattern = re.compile(r"to\s([A-Z].+) A")

    with pp.open(statement) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        for line in text.split("\n"):
            result = pattern.findall(line)
            if len(result) != 0:
                break

    return "".join(result)


def truist_get_checks(statement):
    # looks for a pattern that has date, check number, negative amount
    # can't find amounts without an associated check
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
    ### Hardcode EDI a possible deposit description
    pattern = re.compile(
        r"(\d{2}/\d{2})\s+(?!DEPOSIT|EDI)\**(.+?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})"
    )
    with pp.open(statement) as pdf:
        pages = pdf.pages

        filtered_list = []
        # # get only pages that have withdrawals in them
        # for page_number, page in enumerate(pages, start=1):
        #     text = page.extract_text()

        #     if "withdrawals" in text:
        #         matching_pages.append(page)

        # parse through withdrawal pages
        for page in pages:
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


def wf_get_checks(statement):
    # looks for a pattern that has date, check number, negative amount
    pattern = re.compile(r"(\d+)\*? \d{2}/\d{1,} (\d{1,3}(?:,\d{3})*\.\d{2})")
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


def wf_get_withdrawals(statement):
    pass
