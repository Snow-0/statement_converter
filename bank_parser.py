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
        r"(\d{2}/\d{2})\s+\**(.+?)\s+(\d{1,3}(?:,\d{3})*\.\d{2})"
    )
    second_instance_found = False
    extracted_text = []
    stop_phrase_count = 0

    with pp.open(statement) as pdf:
        pages = pdf.pages

        filtered_list = []
        
        # parse through withdrawal pages
        stop_phrase = "Deposits,creditsandinterest"
        for page in pages: 
            page_text = page.extract_text()
            if page_text is None:
                continue  # Skip pages that do not have text

            # Split the text by lines
            lines = page_text.split('\n')

            # Process each line
            for line in lines:
                # If the stop phrase is found, increment the count
                if stop_phrase in line:
                    stop_phrase_count += 1

                # If the second instance of the phrase is found, stop extraction
                if stop_phrase_count == 2:
                    second_instance_found = True
                    break
                # Otherwise, continue appending the line to the extracted text
                extracted_text.append(line)

            # If the second instance is found, break out of the outer loop as well
            if second_instance_found:
                break

        # Join the lines and return the extracted text
        withdrawal_only =  '\n'.join(extracted_text)

        for line in withdrawal_only.split("\n"):
            result = pattern.findall(line)

            # removes checks that got in 
            for tup in result:
                if not tup[1][0].isdigit():
                    filtered_list.append(result)

                

        # # add 9999 check number
        ##
        filtered_list = list(chain.from_iterable(filtered_list))
        withdraw_amt = [("9999", amt[2]) for amt in filtered_list]
        return withdraw_amt


def truist_get_date(statement):
    pattern = re.compile(r"For \d{2}/\d{2}/\d{4}")
    with pp.open(statement) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        for line in text.split("\n"):
            result = pattern.findall(line)
            if len(result) != 0:
                break
    
    # .split() to just get the date
    return "".join(result).split(" ")[1]



def wf_get_checks(statement):
    # looks for a pattern that has date, check number, negative amount
    pattern = re.compile(r"(\d+)\s*\*? \d{1,}/\d{1,} (\d{1,3}(?:,\d{3})*\.\d{2})")
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
    # find the pattern MM/DD/YYYY DESC -amount
    pattern = re.compile(r"(\d{1,}/\d{1,})\s*(.+?)\**\s*(\d{1,3}(?:,\d{3})*\.\d{2})")

    with pp.open(statement) as pdf:
        pages = pdf.pages

        filtered_list = []

        # parse through withdrawal pages
        for page in pages:
            text = page.extract_text()

            for line in text.split("\n"):
                result = pattern.findall(line)
                if len(result) >= 1:
                    if result[0][1][0] == "<":
                        filtered_list.append(result)

        # # add 9999 check number
        filtered_list = list(chain.from_iterable(filtered_list))
        withdraw_amt = [("9999", amt[2]) for amt in filtered_list]
        return withdraw_amt


# def wf_get_date(statement):
#     pattern = re.compile(
#         "r\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b"
#     )
#     with pp.open(statement) as pdf:
#         page = pdf.pages[0]
#         text = page.extract_text().split("\n")[1]
#         date = text.split(" Page")[0]

#     return date


def chase_get_checks(statement):
    # looks for a pattern that has date, check number, negative amount
    pattern = re.compile(r"(\d+)\s*\**\^+ \d{2}/\d{2} \$*(\d{1,3}(?:,\d{3})*\.\d{2})")
    # find edge case where the description has a duplicate date
    pattern_two = re.compile(
        r"(\d+)\s*\**\^+ \d{2}/\d{2} \d{2}/\d{2} \$*(\d{1,3}(?:,\d{3})*\.\d{2})"
    )
    a_list = []

    with pp.open(statement) as pdf:
        pages = pdf.pages
        for page in pages:
            text = page.extract_text()

            for line in text.split("\n"):
                result = pattern.findall(line)
                result_two = pattern_two.findall(line)
                if len(result) != 0 or len(result_two) != 0:
                    a_list.append(result)
                    a_list.append(result_two)

    # flatten the nested tuple list
    a_list = list(chain.from_iterable(a_list))

    return a_list


def chase_get_withdrawals(statement):
    # find the pattern MM/DD/YYYY DESC -amount
    pattern = re.compile(r"(\d{2}/\d{2}) (.+?) \$*(\d{1,3}(?:,\d{3})*\.\d{2})")

    with pp.open(statement) as pdf:
        pages = pdf.pages
        matching_pages = []

        filtered_list = []

        text = ""
        # get only pages that have withdrawals/checks in them
        for page_number, page in enumerate(pages, start=1):
            text = page.extract_text()

            if "WITHDRAWALS" in text:
                matching_pages.append(page)
        # parse through withdrawal pages
        for page in matching_pages:
            text = page.extract_text()
            phrase = "DAILY ENDING BALANCE"

            for line in text.split("\n"):
                # ignore daily ledger balance data
                if phrase == line:
                    break
                result = pattern.findall(line)
                for tup in result:
                    if not tup[1].isdigit():
                        filtered_list.append(result)

    # # add 9999 check number

    filtered_list = list(chain.from_iterable(filtered_list))
    withdraw_amt = [("9999", amt[2]) for amt in filtered_list]
    return withdraw_amt


def chase_get_date(statement):
    pattern = re.compile(r"through([A-Z].+)")

    with pp.open(statement) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        for line in text.split("\n"):
            result = pattern.findall(line)
            if len(result) != 0:
                break

    return "".join(result)





