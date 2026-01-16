from multiprocessing import Process
import ocrmypdf
import os


input_folder = "input_pdfs"


# copy and pasted from ocrmypdf docs
def ocrmypdf_process(statement):
    ocrmypdf.ocr(statement, statement)


def run_ocr(statement):
    p = Process(target=ocrmypdf_process, args=(statement,))
    p.start()
    p.join()


def main():
    print("📄 Adding OCR..")
    processed_files = 0

    for file in os.listdir(input_folder):
        pdf_path = os.path.join(input_folder, file)

        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_folder, file)
            print(f"\n🔍 Processing {file}...")
            run_ocr()
