import os

from utils.file_tool import make_directory_if_not_exists

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = make_directory_if_not_exists(os.path.join(CUR_DIR, 'output'))
JSON_DIR = make_directory_if_not_exists(os.path.join(CUR_DIR, 'aws_json'))

CONFIG_FILE = os.path.join(CUR_DIR, 'config.cfg')

Y_BIND_THRESH = 0.01

COLUMN_NUM_LIMIT = 6
START_PAGE_NUM = 7
SAMPLE_PAGE_NUM = 12

DIR_PATH = ""
