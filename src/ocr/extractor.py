import os
import ntpath
import json
import numpy as np
import cv2
import pandas as pd

from pdf2image import convert_from_path
from src.aws.textract_tool import AWSTextractor
from settings import Y_BIND_THRESH, COLUMN_NUM, PAGE_NUM, JSON_DIR, OUTPUT_DIR


class InfoExtractor:
    def __init__(self):
        self.aws_textractor = AWSTextractor()
        self.table_data = []

    def get_info_one_page(self, image_path, page_num, file_name):
        if os.path.exists(os.path.join(JSON_DIR, f"{file_name}_{page_num}.json")):
            with open(os.path.join(JSON_DIR, f"{file_name}_{page_num}.json")) as f:
                raw_data = json.load(f)
        else:
            raw_data = self.aws_textractor.extract_ocr_local(frame_path=image_path, page_num=page_num,
                                                             file_name=file_name)
        meta_data = []
        for res_data in raw_data["Blocks"][1:]:
            if res_data["BlockType"] == "LINE":
                meta_data.append(res_data)

        if meta_data:
            y_sorted_data = sorted(meta_data, key=lambda k: k["Geometry"]["BoundingBox"]["Top"])
            bind_y_close = []
            tmp_line = []
            init_value = y_sorted_data[0]["Geometry"]["BoundingBox"]["Top"]

            for r_data in y_sorted_data:
                if abs(init_value - r_data["Geometry"]["BoundingBox"]["Top"]) < Y_BIND_THRESH:
                    tmp_line.append(r_data)
                else:
                    bind_y_close.append(tmp_line[:])
                    tmp_line.clear()
                    tmp_line.append(r_data)
                    init_value = r_data["Geometry"]["BoundingBox"]["Top"]

            bind_y_close.append(tmp_line[:])
            for b_y_data in bind_y_close:
                if len(b_y_data) == COLUMN_NUM or len(b_y_data) == COLUMN_NUM - 1:
                    sorted_x_data = sorted(b_y_data, key=lambda k: k["Geometry"]["BoundingBox"]["Left"])
                    tmp_table_data = []
                    if len(b_y_data) == COLUMN_NUM - 1:
                        tmp_table_data.append('"')
                    for s_x_data in sorted_x_data:
                        tmp_table_data.append(s_x_data["Text"])
                    tmp_table_data.append(f"page{page_num}")
                    tmp_table_data.append(file_name)
                    self.table_data.append(tmp_table_data)

        return

    def run(self, file_path):
        file_name = ntpath.basename(file_path).replace(".pdf", "")
        output_file_path = os.path.join(OUTPUT_DIR, f"{file_name}_{COLUMN_NUM}.csv")
        pdf_frames = [np.array(page) for page in convert_from_path(file_path, 200)]

        tmp_image_path = os.path.join(JSON_DIR, "tmp.jpg")

        for page_idx, p_frame in enumerate(pdf_frames):
            if page_idx < PAGE_NUM - 1:
                continue
            print(f"[INFO] Processing Page {page_idx + 1}...")
            cv2.imwrite(tmp_image_path, p_frame)
            self.get_info_one_page(image_path=tmp_image_path, file_name=file_name, page_num=page_idx + 1)

        pd.DataFrame(self.table_data).to_csv(output_file_path, index=False, header=False, mode="w")
        print(f"[INFO] Saved result into {output_file_path}")

        return


if __name__ == '__main__':
    InfoExtractor().run(file_path="")
