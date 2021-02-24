from src.ocr.extractor import InfoExtractor
from settings import FILE_PATH


if __name__ == '__main__':
    InfoExtractor().run(file_path=FILE_PATH)
