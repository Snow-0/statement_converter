import os
import re
import pandas as pd
from PyPDF2 import PdfReader
from datetime import datetime
import logging

# 📂 Configuration - Using input_pdfs folder for PDFs
CONFIG = {
    "input_folder": "input_pdfs",  # Using input_pdfs folder
    "output_folder": "monthly_csvs", 
    "debug_folder": "debug_texts",
    
    # Default values for CSV output
    "default_batch": "O01",
    "default_code": "5040",
    "default_desc": "Other Debit",
    "fees_check_number": "9999",
    # Removed hardcoded default_date - will be generated dynamically
    
    # Special check cases to handle problematic patterns
    "special_check_cases": [
        {
            "check_no": "113",
            "pattern": r'113\s*\^\s*\d{2}/\d{2}\s*\$?([\d,]+\.\d{2})[A-Z]',
            "description": "Check stuck to DEPOSITS text"
        },
        {
            "check_no": "171", 
            "pattern": r'Total Checks Paid.*?171\s*\^\s*\d{2}/\d{2}\s+([\d,]+\.\d{2})',
            "description": "Check after Total Checks Paid"
        },
        {
            "check_no": "173",
            "pattern": r'173\s*\*\s*\^\s*\d{2}/\d{2}\s+([\d,]+\.\d{2})',
            "description": "Check with asterisk format"
        }
    ],
    
    # False positive checks to skip
    "false_positive_checks": ["2171"],
    
    # Fee threshold
    "fee_threshold": 1.00
}

class ChaseStatementProcessor:
    def __init__(self, config):
        self.config = config
        self.setup_directories()
        self.setup_logging()
        # Generate month end dates dynamically for current year
        self.config["month_end_dates"] = self.generate_month_end_dates()
    
    def generate_month_end_dates(self):
        """Generate month-end dates dynamically for the current year"""
        current_year = datetime.now().year
        year_suffix = str(current_year)[-2:]  # Get last 2 digits of year
        
        month_end_dates = {
            "01": f"0131{year_suffix}",  # January 31
            "02": f"0228{year_suffix}",  # February 28 (non-leap year)
            "03": f"0331{year_suffix}",  # March 31
            "04": f"0430{year_suffix}",  # April 30
            "05": f"0531{year_suffix}",  # May 31
            "06": f"0630{year_suffix}",  # June 30
            "07": f"0731{year_suffix}",  # July 31
            "08": f"0831{year_suffix}",  # August 31
            "09": f"0930{year_suffix}",  # September 30
            "10": f"1031{year_suffix}",  # October 31
            "11": f"1130{year_suffix}",  # November 30
            "12": f"1231{year_suffix}",  # December 31
        }
        
        # Handle leap year for February
        if current_year % 4 == 0 and (current_year % 100 != 0 or current_year % 400 == 0):
            month_end_dates["02"] = f"0229{year_suffix}"  # February 29 for leap year
        
        print(f"📅 Generated month-end dates for year: {current_year}")
        return month_end_dates
    
    def setup_directories(self):
        """Create necessary directories"""
        for folder in [self.config["input_folder"], 
                      self.config["output_folder"], 
                      self.config["debug_folder"]]:
            os.makedirs(folder, exist_ok=True)
    
    def setup_logging(self):
        """Setup logging configuration - removed file handler"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()  # Only console output, no file
            ]
        )
        self.logger = logging.getLogger(__name__)

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file - improved to handle page breaks"""
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    # Add page separator to help with pattern matching across pages
                    text += "\n" + page_text + "\n---PAGE_BREAK---\n"
            return text
        except Exception as e:
            self.logger.error(f"Error reading PDF {pdf_path}: {e}")
            return ""

    def get_month_end_date(self, text, filename):
        """Extract month from statement and return appropriate month-end date - FIXED"""
        print("🔍 Determining statement month...")
        
        # Look for the specific pattern in your debug text: "January 01, 2025 throughJanuary 31, 2025"
        statement_patterns = [
            # Your specific format: "January 01, 2025 throughJanuary 31, 2025"
            r'(\w+)\s+\d{1,2},\s+\d{4}\s+through\s*(\w+)\s+\d{1,2},\s+\d{4}',
            r'(\w+)\s+\d{1,2},\s+\d{4}\s+through\s+(\w+)\s+\d{1,2},\s+\d{4}',
            r'(\w+)\s+\d{1,2},\s+\d{4}\s+to\s+(\w+)\s+\d{1,2},\s+\d{4}',
            r'Statement Period:\s*(\w+)\s+\d{1,2},\s+\d{4}\s+through\s*(\w+)\s+\d{1,2},\s+\d{4}',
        ]
        
        month_names = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12',
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
            'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }
        
        for pattern in statement_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    start_month_name = match[0].lower()
                    end_month_name = match[1].lower()
                    
                    if start_month_name in month_names and end_month_name in month_names:
                        month = month_names[end_month_name]  # Use the end month
                        # Extract year from the pattern
                        year_match = re.search(r'through\s*\w+\s+\d{1,2},\s+(\d{4})', text, re.IGNORECASE)
                        if year_match:
                            year_suffix = year_match.group(1)[-2:]
                        else:
                            # Fallback: look for any 4-digit year in the same area
                            year_match = re.search(r'(\d{4})', text[max(0, text.find(match[0])-50):text.find(match[0])+100])
                            year_suffix = year_match.group(1)[-2:] if year_match else str(datetime.now().year)[-2:]
                        
                        if month in self.config["month_end_dates"]:
                            month_end_date = self.config["month_end_dates"][month]
                            month_end_date = month_end_date[:4] + year_suffix
                            print(f"📅 Found statement period: {match[0]} {match[1]} -> {month_end_date}")
                            return month_end_date
        
        # Try to find month in filename
        print("🔍 Looking for month in filename...")
        month_match = re.search(r'(\d{2})[/\-]?(\d{2})[/\-]?(\d{2,4})', filename)
        if month_match:
            month = month_match.group(1)  # Get MM from filename
            year = month_match.group(3)  # Get YY or YYYY from filename
            if len(year) == 2:
                year_suffix = year
            else:
                year_suffix = year[-2:]
                
            if month in self.config["month_end_dates"]:
                month_end_date = self.config["month_end_dates"][month]
                month_end_date = month_end_date[:4] + year_suffix
                print(f"📅 Using month from filename: {month_end_date}")
                return month_end_date
        
        # Last resort: use current month instead of hardcoded December
        current_month = datetime.now().strftime('%m')
        current_year_suffix = datetime.now().strftime('%y')
        month_end_date = self.config["month_end_dates"][current_month]
        month_end_date = month_end_date[:4] + current_year_suffix
        print(f"⚠️  Could not determine month, using current month: {month_end_date}")
        return month_end_date

    def extract_chase_checks(self, text, month_end_date):
        """Extract check numbers and amounts from ALL pages - fixed for boundary issues"""
        data = []
        
        print("🔍 Searching for Chase checks table across all pages...")
        
        # Remove page break markers first
        clean_text = text.replace('---PAGE_BREAK---', '')
        
        # FIXED: Handle cases where check numbers get stuck to amounts or other text
        check_patterns = [
            # Pattern 1: Standard format "114 ^ 12/05 1,094.05"
            r'(\d{3,4})\s+\^\s+\d{2}/\d{2}\s+([\d,]+\.\d{2})',
            # Pattern 2: Handle check numbers with asterisk like "138 * ^ 12/23 29.00"
            r'(\d{3,4})\s+\*\s*\^\s+\d{2}/\d{2}\s+([\d,]+\.\d{2})',
            # Pattern 3: Handle check numbers with double dates like "165 * ^ 12/19 12/19 85.00"
            r'(\d{3,4})\s+\*\s*\^\s+\d{2}/\d{2}\s+\d{2}/\d{2}\s+([\d,]+\.\d{2})',
            # Pattern 4: Handle check numbers stuck to amounts like "113^" or "171^"
            r'(\d{3,4})\s*\^',
        ]
        
        all_checks = []
        
        # First try: Standard pattern
        pattern1 = re.compile(check_patterns[0])
        checks1 = pattern1.findall(clean_text)
        if checks1:
            print(f"📊 Found {len(checks1)} checks with standard pattern")
            all_checks.extend(checks1)
        
        # Second try: Asterisk pattern
        pattern2 = re.compile(check_patterns[1])
        checks2 = pattern2.findall(clean_text)
        if checks2:
            print(f"📊 Found {len(checks2)} checks with asterisk pattern")
            all_checks.extend(checks2)
        
        # Third try: Double date pattern
        pattern3 = re.compile(check_patterns[2])
        checks3 = pattern3.findall(clean_text)
        if checks3:
            print(f"📊 Found {len(checks3)} checks with double date pattern")
            all_checks.extend(checks3)
        
        # Fourth try: Find check numbers with ^ symbol
        pattern4 = re.compile(r'(\d{3,4})\s*\^')
        check_markers = pattern4.findall(clean_text)
        print(f"🔍 Found {len(check_markers)} check markers (^)")
        
        # For each check marker, find the corresponding amount
        lines = clean_text.split('\n')
        for i, line in enumerate(lines):
            # Look for check number patterns in the line
            check_match = re.search(r'(\d{3,4})\s*\^', line)
            if check_match:
                check_no = check_match.group(1)
                
                # Skip if we already have this check number
                if check_no in [c[0] for c in all_checks]:
                    continue
                
                # Look for amount in various positions
                amount_found = None
                
                # Method 1: Look for amount in the same line after check number
                amount_after_check = re.search(r'\^\s*\d{2}/\d{2}\s+([\d,]+\.\d{2})', line)
                if amount_after_check:
                    amount_found = amount_after_check.group(1)
                
                # Method 2: Look for amount with double dates
                if not amount_found:
                    amount_double_date = re.search(r'\^\s*\d{2}/\d{2}\s+\d{2}/\d{2}\s+([\d,]+\.\d{2})', line)
                    if amount_double_date:
                        amount_found = amount_double_date.group(1)
                
                # Method 3: Look for amount later in the same line
                if not amount_found:
                    amount_in_line = re.search(r'(\d{1,3}(?:,\d{3})*\.\d{2})', line[line.find('^') + 1:])
                    if amount_in_line:
                        amount_found = amount_in_line.group(1)
                
                # Method 4: Look for amount in next line
                if not amount_found and i + 1 < len(lines):
                    amount_next_line = re.search(r'(\d{1,3}(?:,\d{3})*\.\d{2})', lines[i + 1])
                    if amount_next_line:
                        amount_found = amount_next_line.group(1)
                
                if amount_found:
                    # Validate amount is reasonable
                    clean_amount = amount_found.replace(',', '')
                    try:
                        amount_float = float(clean_amount)
                        if 1.0 <= amount_float <= 50000.0:  # Reasonable check amount range
                            all_checks.append((check_no, amount_found))
                            print(f"   ✅ Found check {check_no}: ${clean_amount}")
                    except ValueError:
                        continue
        
        # SPECIAL FIX: Handle special cases from config
        print("🔍 Checking for special case checks...")
        for special_case in self.config["special_check_cases"]:
            check_no = special_case["check_no"]
            pattern = special_case["pattern"]
            description = special_case["description"]
            
            special_match = re.search(pattern, clean_text)
            if special_match and check_no not in [c[0] for c in all_checks]:
                amount = special_match.group(1)
                all_checks.append((check_no, amount))
                print(f"   ✅ Found special case check {check_no} ({description}): ${amount}")
        
        # Remove duplicates by check number and validate amounts
        unique_checks = {}
        for check_no, amount in all_checks:
            clean_amount = amount.replace(',', '')
            try:
                amount_float = float(clean_amount)
                if 1.0 <= amount_float <= 50000.0:  # Reasonable check amount range
                    # Skip false positive checks from config
                    if check_no in self.config["false_positive_checks"]:
                        print(f"   ⚠️  Skipping false positive check {check_no}")
                        continue
                    if check_no not in unique_checks:
                        unique_checks[check_no] = clean_amount
            except ValueError:
                continue
        
        print(f"📊 Total unique checks found: {len(unique_checks)}")
        
        # Sort by check number for better reporting
        sorted_checks = sorted(unique_checks.items(), key=lambda x: int(x[0]))
        
        for check_no, amount in sorted_checks:
            data.append({
                "Check number": check_no,
                "date": month_end_date,
                "batch": self.config["default_batch"],
                "code": self.config["default_code"],
                "amount": amount,
                "description": self.config["default_desc"]
            })
            print(f"   💰 Check {check_no}: ${amount}")
        
        return data

    def extract_chase_electronic_withdrawals(self, text, month_end_date):
        """Extract electronic withdrawals WITH DESCRIPTIONS - FIXED FOR MISSING TRANSACTIONS"""
        data = []
        
        print("🔍 Searching for electronic withdrawals with descriptions...")
        
        clean_text = text.replace('---PAGE_BREAK---', '')
        
        # Strategy: Extract complete transactions with descriptions to avoid duplicates
        electronic_transactions = []
        
        # Find the start of electronic withdrawals section
        start_marker = "* All of your recent checks may not be on this statement, either because they haven't cleared yet or they were listed on"
        marker_index = clean_text.find(start_marker)
        
        if marker_index != -1:
            # Extract the ENTIRE electronic withdrawals section
            electronic_section = clean_text[marker_index + len(start_marker):]
            print("✅ Found electronic withdrawals section")
            
            # Split into lines and process in order
            lines = electronic_section.split('\n')
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Look for transaction start patterns
                transaction_found = False
                amount = None
                
                # Pattern 1: Online Payment with date
                if re.match(r'\d{2}/\d{2}\s+\d{2}/\d{2}\s+Online Payment', line):
                    # Extract amount and description
                    amount_match = re.search(r'([\d,]+\.\d{2})$', line)
                    if amount_match:
                        amount = amount_match.group(1)
                        transaction_found = True
                        print(f"   💳 Online Payment: ${amount}")
                
                # Pattern 2: Online Transfer with date
                elif re.match(r'\d{2}/\d{2}\s+\d{2}/\d{2}\s+Online Transfer', line):
                    amount_match = re.search(r'([\d,]+\.\d{2})$', line)
                    if amount_match:
                        amount = amount_match.group(1)
                        transaction_found = True
                        print(f"   💳 Online Transfer: ${amount}")
                
                # Pattern 3: Online ACH Payment with date
                elif re.match(r'\d{2}/\d{2}\s+\d{2}/\d{2}\s+Online ACH Payment', line):
                    amount_match = re.search(r'([\d,]+\.\d{2})$', line)
                    if amount_match:
                        amount = amount_match.group(1)
                        transaction_found = True
                        print(f"   💳 Online ACH Payment: ${amount}")
                
                # Pattern 4: Look for any line with amount at the end (catch missing transactions)
                elif re.search(r'[\d,]+\.\d{2}$', line) and any(keyword in line for keyword in ['Online', 'Transfer', 'ACH', 'Payment']):
                    amount_match = re.search(r'([\d,]+\.\d{2})$', line)
                    if amount_match:
                        amount = amount_match.group(1)
                        transaction_found = True
                        print(f"   💳 Electronic Transaction: ${amount}")
                
                # Pattern 5: Orig CO transactions (electronic transfers)
                elif 'Orig CO Name:' in line:
                    # This is a multi-line transaction, collect the full transaction
                    transaction_lines = [line]
                    
                    # Look ahead for the next few lines to capture the full transaction
                    for j in range(1, 6):  # Check next 5 lines
                        if i + j < len(lines):
                            next_line = lines[i + j].strip()
                            transaction_lines.append(next_line)
                            
                            # Look for Tc amount in the collected lines
                            combined_text = ' '.join(transaction_lines)
                            tc_match = re.search(r'Trn:\s*\d+T[cC]([\d,]+\.\d{2})', combined_text)
                            if not tc_match:
                                tc_match = re.search(r'Tm:\s*\d+T[cC]([\d,]+\.\d{2})', combined_text)
                            
                            if tc_match:
                                amount = tc_match.group(1)
                                transaction_found = True
                                print(f"   💳 Electronic Transfer: ${amount}")
                                break
                    
                    # Skip the lines we just processed
                    if transaction_found:
                        i += len(transaction_lines) - 1
                
                # If we found a transaction, add it to the list
                if transaction_found and amount:
                    clean_amount = amount.replace(',', '')
                    try:
                        amount_float = float(clean_amount)
                        if 10.0 <= amount_float <= 100000.0:
                            # Use the original amount string to preserve formatting
                            electronic_transactions.append(amount)
                    except ValueError:
                        pass
                
                i += 1
            
            print(f"🔍 Found {len(electronic_transactions)} unique electronic transactions")
            
        else:
            print("❌ Could not find electronic withdrawals starting marker")
            return data
        
        # Add transactions to data - ALWAYS USE "Other Debit" as description
        for amount in electronic_transactions:
            data.append({
                "Check number": self.config["fees_check_number"],
                "date": month_end_date,
                "batch": self.config["default_batch"],
                "code": self.config["default_code"],
                "amount": amount,
                "description": self.config["default_desc"]  # Always use "Other Debit"
            })
        
        return data

    def extract_chase_fees(self, text, month_end_date):
        """Extract ALL fee amounts - ONLY FEES OVER $1"""
        data = []
        
        print(f"🔍 Searching for fees over ${self.config['fee_threshold']}...")
        
        clean_text = text.replace('---PAGE_BREAK---', '')
        
        # Look for ALL fee amounts mentioned - ONLY WITH DATES AND OVER threshold
        fee_transactions = []
        
        # Process each line individually and look for specific fee patterns WITH DATES
        lines = clean_text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Look for Domestic Incoming Wire Fee WITH DATE
            if 'Domestic Incoming Wire Fee' in line and re.search(r'\d{2}/\d{2}', line):
                # Extract amount with or without dollar sign
                amount_match = re.search(r'Domestic Incoming Wire Fee\s*\$?(\d+\.\d{2})', line)
                if amount_match:
                    amount = amount_match.group(1)
                    # Check if amount is over threshold
                    if float(amount) > self.config["fee_threshold"]:
                        fee_transactions.append(amount)
                        print(f"   💸 Found Domestic Incoming Wire Fee: ${amount}")
            
            # Look for Monthly Service Fee WITH DATE
            elif 'Monthly Service Fee' in line and re.search(r'\d{2}/\d{2}', line):
                amount_match = re.search(r'Monthly Service Fee\s*\$?(\d+\.\d{2})', line)
                if amount_match:
                    amount = amount_match.group(1)
                    # Check if amount is over threshold
                    if float(amount) > self.config["fee_threshold"]:
                        fee_transactions.append(amount)
                        print(f"   💸 Found Monthly Service Fee: ${amount}")
            
            # Look for any other fees WITH DATES
            elif 'Fee' in line and re.search(r'\d{2}/\d{2}', line):
                # Extract any amount that looks like a fee
                amount_matches = re.findall(r'\$?(\d+\.\d{2})(?:\s|$)', line)
                for amount in amount_matches:
                    try:
                        amount_float = float(amount)
                        # Only include fees over threshold and in reasonable fee range
                        if self.config["fee_threshold"] < amount_float <= 100.0:
                            fee_transactions.append(amount)
                            print(f"   💸 Found other fee with date: ${amount} in line: {line}")
                    except ValueError:
                        continue
        
        print(f"📊 Found {len(fee_transactions)} fee transactions over ${self.config['fee_threshold']}")
        
        for amount in fee_transactions:
            data.append({
                "Check number": self.config["fees_check_number"],
                "date": month_end_date,
                "batch": self.config["default_batch"],
                "code": self.config["default_code"],
                "amount": amount,
                "description": "Bank Fee"
            })
        
        return data

    def debug_text_extraction(self, text, filename):
        """Save extracted text for debugging"""
        debug_file = os.path.join(self.config["debug_folder"], f"{os.path.splitext(filename)[0]}.txt")
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"🔍 Debug text saved: {debug_file}")

    def process_all_pdfs(self):
        """Main processing function for all PDFs in the input_pdfs folder"""
        print("🏦 Starting Chase statement extraction...")
        print(f"📁 Looking for PDF files in: {os.path.abspath(self.config['input_folder'])}")
        
        processed_files = 0
        pdf_files = []

        # Find all PDF files in input_pdfs directory
        for file in os.listdir(self.config["input_folder"]):
            if file.lower().endswith(".pdf"):
                pdf_files.append(file)
        
        if not pdf_files:
            print(f"❌ No PDF files found in the '{self.config['input_folder']}' folder!")
            print(f"💡 Please make sure your PDF files are in: {os.path.abspath(self.config['input_folder'])}")
            return 0

        print(f"📄 Found {len(pdf_files)} PDF file(s) to process")

        for file in pdf_files:
            pdf_path = os.path.join(self.config["input_folder"], file)
            print(f"\n🔍 Processing {file}...")

            text = self.extract_text_from_pdf(pdf_path)
            
            if not text.strip():
                print(f"❌ No text extracted from {file}")
                continue
                
            # Debug: save extracted text
            self.debug_text_extraction(text, file)
            
            # Get appropriate month-end date
            month_end_date = self.get_month_end_date(text, file)
            print(f"📅 Using month-end date: {month_end_date}")
            
            # Extract data from all sections
            checks_data = self.extract_chase_checks(text, month_end_date)
            electronic_data = self.extract_chase_electronic_withdrawals(text, month_end_date)
            fees_data = self.extract_chase_fees(text, month_end_date)
            
            # Combine all data
            all_data = checks_data + electronic_data + fees_data

            if not all_data:
                print(f"⚠️ No data extracted from {file}")
                # Create empty CSV with correct columns
                df = pd.DataFrame(columns=["Check number", "date", "batch", "code", "amount", "description"])
            else:
                df = pd.DataFrame(all_data)
                final_columns = ["Check number", "date", "batch", "code", "amount", "description"]
                df = df[final_columns]
                print(f"✅ Extracted {len(df)} total transactions")
                print(f"   - Checks: {len(checks_data)}")
                print(f"   - Electronic Withdrawals: {len(electronic_data)}")
                print(f"   - Fees: {len(fees_data)}")

            output_file = os.path.join(self.config["output_folder"], f"{os.path.splitext(file)[0]}.csv")
            
            # Save CSV without headers
            df.to_csv(output_file, index=False, header=False)
            print(f"💾 Saved: {output_file} (without headers)")
            
            processed_files += 1

        print(f"\n✨ Extraction complete. Processed {processed_files} files.")
        return processed_files

# --- MAIN EXECUTION ---
# if __name__ == "__main__":
#     processor = ChaseStatementProcessor(CONFIG)
#     processor.process_all_pdfs()