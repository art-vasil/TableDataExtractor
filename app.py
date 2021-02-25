from src.ocr.extractor import InfoExtractor
from settings import DIR_PATH


if __name__ == '__main__':
    InfoExtractor().run(dir_path=DIR_PATH)
