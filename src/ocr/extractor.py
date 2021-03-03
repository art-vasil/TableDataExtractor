import os
import glob
import ntpath
import json
import numpy as np
import cv2
import pandas as pd

from pdf2image import convert_from_path
from src.aws.textract_tool import AWSTextractor
from settings import Y_BIND_THRESH, COLUMN_NUM_LIMIT, START_PAGE_NUM, JSON_DIR, OUTPUT_DIR, SAMPLE_PAGE_NUM


class InfoExtractor:
    def __init__(self):
        self.aws_textractor = AWSTextractor()
        self.table_data = {}
        self.template = {}
        self.row_id = 1
        self.main_cols = 0
        self.col_thresh = 0
        self.__initialize()

    def __initialize(self):
        for col_num in range(COLUMN_NUM_LIMIT):
            self.table_data[col_num + 1] = []

    @staticmethod
    def bind_y_close_data(raw_data):
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
        else:
            bind_y_close = []

        return bind_y_close

    def get_initial_raw_data(self, image_path, page_num, file_name):
        if os.path.exists(os.path.join(JSON_DIR, f"{file_name}_{page_num}.json")):
            with open(os.path.join(JSON_DIR, f"{file_name}_{page_num}.json")) as f:
                raw_data = json.load(f)
        else:
            raw_data = self.aws_textractor.extract_ocr_local(frame_path=image_path, page_num=page_num,
                                                             file_name=file_name)

        return raw_data

    def get_info_one_page(self, image_path, page_num, file_name, output_file_path):
        raw_data = self.get_initial_raw_data(image_path=image_path, page_num=page_num, file_name=file_name)
        bind_y_close = self.bind_y_close_data(raw_data=raw_data)

        for b_y_data in bind_y_close:
            if len(b_y_data) == 1:
                continue
            sorted_x_data = sorted(b_y_data, key=lambda k: k["Geometry"]["BoundingBox"]["Left"])
            tmp_table_data = [[str(self.row_id)]]
            if len(sorted_x_data) >= self.main_cols:
                for s_x_data in sorted_x_data:
                    tmp_table_data.append([s_x_data["Text"]])
            else:
                for col_idx in self.template.keys():
                    col_ret = False
                    for s_x_data in sorted_x_data:
                        if abs(s_x_data["Geometry"]["BoundingBox"]["Left"] - self.template[col_idx]) <= self.col_thresh:
                            if tmp_table_data[-1][0] == s_x_data["Text"]:
                                continue
                            col_ret = True
                            tmp_table_data.append([s_x_data["Text"]])
                            break
                    if not col_ret:
                        tmp_table_data.append([""])
            pd.DataFrame(tmp_table_data).T.to_csv(output_file_path, header=False, index=False, mode="a")
            self.row_id += 1

        return

    def extract_template(self, image_path, page_num, file_name):
        init_data = self.get_initial_raw_data(image_path=image_path, page_num=page_num, file_name=file_name)
        y_line_data = self.bind_y_close_data(raw_data=init_data)
        column_info = {}
        for y_l_data in y_line_data:
            line_cols = len(y_l_data)
            if line_cols in list(column_info.keys()):
                column_info[line_cols]["count"] += 1
                column_info[line_cols]["lines"].append(y_l_data)
            else:
                column_info[line_cols] = {"count": 1, "lines": [y_l_data]}

        self.main_cols = max(column_info, key=lambda k: column_info[k]["count"])
        for col_idx in range(self.main_cols):
            self.template[col_idx] = 0
        for main_col_line in column_info[self.main_cols]["lines"]:
            sorted_x_line = sorted(main_col_line, key=lambda k: k["Geometry"]["BoundingBox"]["Left"])
            for col_idx in range(self.main_cols):
                self.template[col_idx] += sorted_x_line[col_idx]["Geometry"]["BoundingBox"]["Left"]
        for col_idx in range(self.main_cols):
            self.template[col_idx] /= len(column_info[self.main_cols]["lines"])
        col_diff = []
        for temp_idx in self.template.keys():
            if temp_idx < len(list(self.template.keys())) - 1:
                col_diff.append(self.template[temp_idx + 1] - self.template[temp_idx])

        self.col_thresh = min(col_diff)

        return

    def process_one_pdf_file(self, file_path):
        file_name = ntpath.basename(file_path).replace(".pdf", "")
        output_file_path = os.path.join(OUTPUT_DIR, f"{file_name}.csv")
        pdf_frames = [np.array(page) for page in convert_from_path(file_path, 200)]

        tmp_image_path = os.path.join(JSON_DIR, "tmp.jpg")
        cv2.imwrite(tmp_image_path, pdf_frames[SAMPLE_PAGE_NUM - 1])
        self.extract_template(image_path=tmp_image_path, file_name=file_name, page_num=SAMPLE_PAGE_NUM)

        for page_idx, p_frame in enumerate(pdf_frames):
            if page_idx < START_PAGE_NUM - 1:
                continue
            print(f"[INFO] {file_name}, Processing Page {page_idx + 1}...")
            cv2.imwrite(tmp_image_path, p_frame)
            self.get_info_one_page(image_path=tmp_image_path, file_name=file_name, page_num=page_idx + 1,
                                   output_file_path=output_file_path)
        print(f"[INFO] Saved result of {file_name} pdf file into {output_file_path}")

        return

    def run(self, dir_path):
        files = glob.glob(os.path.join(dir_path, "*.pdf"))
        for f_path in files:
            self.process_one_pdf_file(file_path=f_path)

        return


if __name__ == '__main__':
    InfoExtractor().process_one_pdf_file(file_path="")
