import re
import pdfplumber as pp
import pandas as pd
import pprint
from itertools import chain
import os
import re
from PyPDF2 import PdfReader
from datetime import datetime

# 📂 Folders
input_folder = "input_pdfs"
output_folder = "monthly_csvs"
os.makedirs(output_folder, exist_ok=True)

MONTH_END_DATES = {
    "01": "013125",  # January 31, 2025
    "02": "022825",  # February 28, 2025  
    "03": "033125",  # March 31, 2025
    "04": "043025",  # April 30, 2025
    "05": "053125",  # May 31, 2025
    "06": "063025",  # June 30, 2025
    "07": "073125",  # July 31, 2025
    "08": "083125",  # August 31, 2025
    "09": "093025",  # September 30, 2025
    "10": "103125",  # October 31, 2025
    "11": "112825",  # November 28, 2025
    "12": "123125",  # December 31, 2025
}

def boa_get_dates(statement):


    pattern = re.compile(r'\d{2}/\d{2}/\d{2}')
    a_list = []
    month = ""
    with pp.open(statement) as pdf:
        pages = pdf.pages
        for page in pages:
            text = page.extract_text()


            month_match = pattern.search(text)
            if month_match:
                month = month_match.group(0)
                month = month.split("/")[0]
                
                if month in MONTH_END_DATES:
                    return MONTH_END_DATES[month]

    # Fallback: use current month
    current_month = datetime.now().strftime("%m")
    return MONTH_END_DATES.get(current_month, "013125")  # Default to January




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


def extract_text_from_pdf(statement):
    checks = boa_get_checks(statement)
    withdrawals = boa_get_withdrawals(statement)


    with pp.open(statement) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        if len(text) == 0:
            return ""

    return checks, withdrawals

def debug_text_extraction(text, filename):
    """Save extracted text for debugging"""
    debug_folder = "debug_texts"
    os.makedirs(debug_folder, exist_ok=True)
    
    debug_file = os.path.join(debug_folder, f"{os.path.splitext(filename)[0]}.txt")
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"🔍 Debug text saved: {debug_file}")

# --- MAIN PROCESSING LOOP ---

def main_boa():
    print("📄 Starting extraction...")
    processed_files = 0

    for file in os.listdir(input_folder):


        pdf_path = os.path.join(input_folder, file)

        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_folder, file)
            print(f"\n🔍 Processing {file}...")

            text = extract_text_from_pdf(pdf_path)


            if not text.strip():
                print(f"❌ No text extracted from {file}")
                continue
                
            # Debug: save extracted text
            # debug_text_extraction(text, file)
            
            # Get appropriate month-end date
            month_end_date = boa_get_dates(pdf_path)
            print(f"📅 Using month-end date: {month_end_date}")
            
            extracted_data = extract_text_from_pdf(pdf_path)
            checks = extracted_data[0]
            withdraws = extracted_data[1]

            df = pd.DataFrame(data=checks, columns=["Check Number", "Amount"])
            df1 = pd.DataFrame(data=withdraws, columns=["Check Number", "Amount"])
            df.sort_values(by=["Check Number"], inplace=True)
            new_df = pd.concat([df, df1], ignore_index=True)
            new_df["Check Number"] = new_df["Check Number"].astype(int)


            # add filler values
            new_df.insert(1, "Date", month_end_date)
            new_df.insert(2, "ID", "O01")
            new_df.insert(3, "Code", "5040")
            new_df["Description"] = "Other Debit"
            new_df["Date"] = month_end_date
            print(f"✅ Extracted {len(new_df)} total transactions")
            print(f"   - Checks: {len(new_df[new_df['Check Number'] != 9999])}")
            print(f"   - Other: {len(new_df[new_df['Check Number'] == 9999])}")


            output_file = os.path.join(output_folder, f"{os.path.splitext(file)[0]}.csv")
            
            # Save CSV without headers
            new_df.to_csv(output_file, index=False, header=False)
            print(f"💾 Saved: {output_file} (without headers)")
            
            processed_files += 1

    print(f"Extraction complete. Processed {processed_files} files.")

