import os
import re
import pandas as pd
from PyPDF2 import PdfReader
from datetime import datetime

# 📂 Folders
input_folder = "input_pdfs"
output_folder = "monthly_csvs"
os.makedirs(output_folder, exist_ok=True)

# --- MONTH END DATE MAPPING ---
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

HARDCODED_BATCH = "O01"
HARDCODED_CODE = "5040"
HARDCODED_DESC = "Other Debit"

def extract_text_from_pdf(pdf_path):
    """Extracts all text from the PDF using PyPDF2 (non-OCR)."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += "\n" + page_text
    return text

def get_month_end_date(text, filename):
    """Extract month from statement and return appropriate month-end date."""
    # Try to find month in filename first
    month_match = re.search(r'(\d{2})[/\-]?(\d{2})[/\-]?(\d{2,4})', filename)
    if month_match:
        month = month_match.group(1)  # Get MM from filename
        if month in MONTH_END_DATES:
            return MONTH_END_DATES[month]
    
    # Try to find month in text (look for date patterns)
    month_pattern = r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})'
    dates = re.findall(month_pattern, text)
    if dates:
        for date_match in dates:
            month = date_match[0].zfill(2)  # Ensure 2-digit month
            if month in MONTH_END_DATES:
                return MONTH_END_DATES[month]
    
    # Fallback: use current month
    current_month = datetime.now().strftime("%m")
    return MONTH_END_DATES.get(current_month, "013125")  # Default to January

def extract_checks_and_other(text, month_end_date):
    """Extracts both 'Checks Paid' and 'Other Withdrawals' sections."""
    data = []

    # --- CHECKS EXTRACTION (WORKING VERSION WITH SORTING) ---
    print("🔍 Searching for checks in multi-column format...")
    
    # Pattern to match: DATE CHECK# AMOUNT (handles asterisks in check numbers)
    check_pattern = re.compile(
        r'(\d{2}/\d{2})\s+(\*?\d{3,5})\s+([\d,]+\.\d{2})'
    )
    
    all_checks = check_pattern.findall(text)
    print(f"📊 Found {len(all_checks)} total checks")
    
    # Sort checks by check number to keep them in order
    checks_list = []
    for date, check_no, amount in all_checks:
        clean_check_no = check_no.replace('*', '')
        clean_amount = amount.replace(',', '')
        
        checks_list.append({
            "check_number": clean_check_no,
            "date": month_end_date,
            "batch": HARDCODED_BATCH,
            "code": HARDCODED_CODE,
            "amount": clean_amount,
            "description": HARDCODED_DESC
        })
    
    # Sort by check number
    checks_list.sort(key=lambda x: int(x['check_number']))
    
    # Add sorted checks to data
    for check in checks_list:
        data.append({
            "Check number": check['check_number'],
            "date": check['date'],
            "batch": check['batch'],
            "code": check['code'],
            "amount": check['amount'],
            "description": check['description']
        })
        print(f"   💰 Check {check['check_number']}: ${check['amount']}")

    # --- FIXED "OTHER WITHDRAWALS" EXTRACTION ---
    print("🔍 Searching for 'Other withdrawals' section...")
    
    # Look for the section after Totalchecks
    section_pattern = r"Totalchecks.*?(Otherwithdrawals,debitsandservicecharges.*?Totalotherwithdrawals,debitsandservicecharges)"
    section_match = re.search(section_pattern, text, re.IGNORECASE | re.DOTALL)
    
    if section_match:
        section_text = section_match.group(1)  # Get the Other withdrawals section
        print(f"✅ Found 'Other withdrawals' section after Totalchecks! Length: {len(section_text)} chars")
        
        # FIX: Add space before amounts that are stuck to customer IDs
        section_text = re.sub(r'(\d{10})(\d{1,3},\d{3}\.\d{2})', r'\1 \2', section_text)
        
        # FIX: Better amount pattern to catch all amounts including ones without commas
        # Look for any number with exactly 2 decimal places
        amount_pattern = r'(\d{1,3}(?:,\d{3})*\.\d{2})'
        amounts = re.findall(amount_pattern, section_text)
        
        # Filter valid amounts - include smaller amounts too
        valid_amounts = []
        for amount in amounts:
            clean_amount = amount.replace(',', '')
            amount_float = float(clean_amount)
            # Include all amounts from $1.00 up to $1,000,000.00
            if amount_float >= 1.0 and amount_float <= 1000000.0:
                valid_amounts.append(amount)
        
        print(f"📊 Found {len(valid_amounts)} valid amounts in other withdrawals section")
        
        for amount in valid_amounts:
            clean_amount = amount.replace(',', '')
            data.append({
                "Check number": "9999",
                "date": month_end_date,
                "batch": HARDCODED_BATCH,
                "code": HARDCODED_CODE,
                "amount": clean_amount,
                "description": HARDCODED_DESC
            })
            print(f"   💰 Other withdrawal: ${clean_amount}")
    else:
        print("❌ No 'Other withdrawals' section found after Totalchecks")

    return data

def debug_text_extraction(text, filename):
    """Save extracted text for debugging"""
    debug_folder = "debug_texts"
    os.makedirs(debug_folder, exist_ok=True)
    
    debug_file = os.path.join(debug_folder, f"{os.path.splitext(filename)[0]}.txt")
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"🔍 Debug text saved: {debug_file}")

# --- MAIN PROCESSING LOOP ---
print("📄 Starting extraction...")
processed_files = 0

for file in os.listdir(input_folder):
    if file.lower().endswith(".pdf"):
        pdf_path = os.path.join(input_folder, file)
        print(f"\n🔍 Processing {file}...")

        text = extract_text_from_pdf(pdf_path)
        
        if not text.strip():
            print(f"❌ No text extracted from {file}")
            continue
            
        # Debug: save extracted text
        debug_text_extraction(text, file)
        
        # Get appropriate month-end date
        month_end_date = get_month_end_date(text, file)
        print(f"📅 Using month-end date: {month_end_date}")
        
        extracted_data = extract_checks_and_other(text, month_end_date)

        if not extracted_data:
            print(f"⚠️ No data extracted from {file}")
            # Create empty CSV with correct columns
            df = pd.DataFrame(columns=["Check number", "date", "batch", "code", "amount", "description"])
        else:
            df = pd.DataFrame(extracted_data)
            final_columns = ["Check number", "date", "batch", "code", "amount", "description"]
            df = df[final_columns]
            print(f"✅ Extracted {len(df)} total transactions")
            print(f"   - Checks: {len([x for x in extracted_data if x['Check number'] != '9999'])}")
            print(f"   - Other: {len([x for x in extracted_data if x['Check number'] == '9999'])}")

        output_file = os.path.join(output_folder, f"{os.path.splitext(file)[0]}.csv")
        
        # Save CSV without headers
        df.to_csv(output_file, index=False, header=False)
        print(f"💾 Saved: {output_file} (without headers)")
        
        processed_files += 1

print(f"\n✨ Extraction complete. Processed {processed_files} files.")