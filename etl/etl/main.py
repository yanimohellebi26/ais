from etl.extract.AISDownloader import AISDownloader
from etl.utils.FileDownloader import *
def run_etl():
    aisd = AISDownloader()
    aisd.get_file(2024,1,13)


if __name__ == "__main__":
    run_etl()
