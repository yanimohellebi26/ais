from etl.extract.AISDownloader import AISDownloader
from etl.utils.FileDownloader import *
from dotenv import load_dotenv
from etl.utils.logger import Logger

load_dotenv()
Logger.info(f"System started with env {os.getenv("ENV")} ")

def run_etl():
    aisd = AISDownloader()
    aisd.get_file(2024,1,13)

if __name__ == "__main__":
    run_etl()