## fix the boa so that it will work with multiple files when you drag it in 
## have a flag system to choose in the cmd line 
## use the main.py file for this

from boa import main_boa
from chase import ChaseStatementProcessor
from truist import main_truist
from ocr import run_ocr


def convert(bank_type):
    if bank_type == "boa":
        main_boa()
    elif bank_type == "truist":
        main_truist()
    elif bank_type == "chase":
        processor = ChaseStatementProcessor(CONFIG)
        processor.process_all_pdfs()
    else:
        print("Please enter a valid bank!")



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description = "Convert a PDF Bank Statement into a csv file for Su Liu CPA") 

    parser = argparse.ArgumentParser(
        description="Bank statement converter",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "-c", "--convert",
        metavar="Convert Bank",
        required=True,
        choices=["boa", "truist", "chase"],
        help=(
            "Convert PDF bank statement to CSV\n"
            "Current banks to convert:\n"
            "  - Bank of America (boa)\n"
            "  - Truist Bank (truist)\n"
            "  - Chase Bank (chase)"
        )
    )

    parser.add_argument(
    "-ocr", 
    "--ocr",
    metavar="OCR",
    required=False,
    help=("Add a OCR layer to a scanned PDF. Likely to be less accurate (untested)")

    )


    args = parser.parse_args()

    convert(args.convert)
    if args.ocr == "ocr":
        run_ocr()


