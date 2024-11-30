from multiprocessing import Process
import ocrmypdf


# copy and pasted from ocrmypdf docs
def ocrmypdf_process(statement):
    ocrmypdf.ocr(statement, statement)


def run_ocr(statement):
    p = Process(target=ocrmypdf_process, args=(statement,))
    p.start()
    p.join()
