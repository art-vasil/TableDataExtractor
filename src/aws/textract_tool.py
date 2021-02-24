import boto3
import configparser
import time
import os
import json

from utils.file_tool import save_file
from settings import CONFIG_FILE, JSON_DIR


class AWSTextractor:
    def __init__(self):
        params = configparser.ConfigParser()
        params.read(CONFIG_FILE)
        self.textract = boto3.client('textract', region_name=params.get("DEFAULT", "region_name"),
                                     aws_access_key_id=params.get("DEFAULT", "access_key_id"),
                                     aws_secret_access_key=params.get("DEFAULT", "secret_access_key"))
        self.job_id = None

    @staticmethod
    def extract_invoice_no_json(invoice_info):
        invoice_no = ""
        bounding_left = 0
        bounding_right = 0
        bounding_top = 0
        bounding_bottom = 0
        for i, item in enumerate(invoice_info):
            if "Invoice" in item["Text"]:
                invoice_no = invoice_info[i + 1]["Text"]
                bounding_left = item["Geometry"]["BoundingBox"]["Left"] + item["Geometry"]["BoundingBox"]["Width"]
                bounding_right = item["Geometry"]["BoundingBox"]["Left"] + 3 * item["Geometry"]["BoundingBox"]["Width"]
                bounding_top = item["Geometry"]["BoundingBox"]["Top"] - 0.002
                bounding_bottom = \
                    item["Geometry"]["BoundingBox"]["Top"] + item["Geometry"]["BoundingBox"]["Height"] + 0.002
                break

        for item in invoice_info:
            item_left = item["Geometry"]["BoundingBox"]["Left"]
            item_top = item["Geometry"]["BoundingBox"]["Top"]
            if bounding_left <= item_left <= bounding_right and bounding_top <= item_top <= bounding_bottom:
                invoice_no = item["Text"]
                break

        return invoice_no

    def start_job(self, s3_bucket_name, object_name):
        response = self.textract.start_document_text_detection(
            DocumentLocation={'S3Object': {'Bucket': s3_bucket_name, 'Name': object_name}})

        return response["JobId"]

    def is_job_complete(self):
        time.sleep(5)
        response = self.textract.get_document_text_detection(JobId=self.job_id)
        status = response["JobStatus"]
        print(f"[INFO] Job status: {status}")

        while status == "IN_PROGRESS":
            time.sleep(5)
            response = self.textract.get_document_text_detection(JobId=self.job_id)
            status = response["JobStatus"]
            print(f"[INFO] Job status: {status}")

        return status

    def get_job_results(self):

        pages = []

        time.sleep(5)

        response = self.textract.get_document_text_detection(JobId=self.job_id)

        pages.append(response)
        print(f"[INFO] Result set page received: {len(pages)}")
        next_token = None
        if 'NextToken' in response:
            next_token = response['NextToken']

        while next_token:
            time.sleep(5)

            response = self.textract.get_document_text_detection(JobId=self.job_id, NextToken=next_token)

            pages.append(response)
            print(f"[INFO] Result set page received: {len(pages)}")
            next_token = None
            if 'NextToken' in response:
                next_token = response['NextToken']

        return pages

    def extract_invoice_no_pdf(self, pdf_name, s3_bucket_name):
        response = []

        self.job_id = self.start_job(s3_bucket_name=s3_bucket_name, object_name=pdf_name)
        print(f"[INFO] Started job with id: {self.job_id}")
        if self.is_job_complete():
            response = self.get_job_results()
        invoice_info = response[0]["Blocks"][1:]

        invoice_no = self.extract_invoice_no_json(invoice_info=invoice_info)

        return invoice_no

    def extract_invoice_no_frame(self, image_path):
        with open(image_path, 'rb') as document:
            image_bytes = bytearray(document.read())

        response = self.textract.detect_document_text(Document={'Bytes': image_bytes})
        invoice_info = response["Blocks"][1:]

        invoice_no = self.extract_invoice_no_json(invoice_info=invoice_info)

        return invoice_no

    def extract_ocr_local(self, frame_path, page_num, file_name):

        # Read document content
        with open(frame_path, 'rb') as document:
            image_bytes = bytearray(document.read())

        # Call Amazon Textract
        response = self.textract.detect_document_text(Document={'Bytes': image_bytes})
        json_file_path = os.path.join(JSON_DIR, f"{file_name}_{page_num}.json")
        save_file(filename=json_file_path, content=json.dumps(response, indent=4), method="w")

        return response


if __name__ == '__main__':
    AWSTextractor().extract_ocr_local(frame_path="/media/main/Data/Task/AWSOCR/test1.jpg")
