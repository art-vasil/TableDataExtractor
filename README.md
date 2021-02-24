# TableDataExtractor

## Overview

This project is to extract the necessary table data from the scanned pdf document using AWS Textract.

## Structure

- src

    The main source code for OCR
    
- utils

    The source code to manage folders and files
    
- app

    The main execution file
    
- config

    AWS Textract key configuration
    
- requirements

    All the dependencies for this project
    
- settings

    Several settings including file path, column number and page number

## Installation

- Environment

    Python 3.6, Ubuntu 18.04, Windows 10

- Dependency Installation

    Please navigate to this project directory and run the following command in the terminal.
    ```
        pip3 install -r requirements.txt
    ```

## Execution

- Please set AWS Textract keys in config file.

- Please in settings file, set COLUMN_NUM variable with column number to extract, PAGE_NUM variable with the page number 
for starting extraction, and FILE_PATH variable with the full path of the pdf file to parse.

- Please run the following command in the terminal.

    ```
        python3 app.py
    ```

- Then the output file will be in output folder.