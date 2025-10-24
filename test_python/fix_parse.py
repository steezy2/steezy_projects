import os
import pymupdf
from typing import List, Dict, Tuple
import pymupdf
import pandas
import xlsxwriter
import re

def read_pdf_into_dicts(name: str) -> Tuple[List[Dict], List[Dict]]:
    """Read a pdf and return a list of transaction dictionaries"""
    doc = pymupdf.open(name)
    end_strings = ["Transactions continued on next page", "TOTAL FEES FOR THIS PERIOD"]
    keep_going = False
    transactions = []

    # combine all text from all pages
    text = ""
    for page in doc:
        text += page.get_text()
    lines = text.splitlines()
    # filter out transaction data
    for line in lines:
        if keep_going:
            if any(s in line for s in end_strings):
                keep_going = False
            else:
                transactions.append(line)

        if "Transaction Description" in line:
            keep_going = True

    # print(f"transactions: {transactions}") # useful for debugging

    trans_obj_list = []
    inverse_trans_list = []
    # filter transactions into list of dicts
    for idx, trans in enumerate(transactions):
        reference_match = re.search(r"\d\d\d\d\d\d\d\S{10}", trans)
        amount_match = re.search(r"\.\d\d", trans)

        if reference_match:
            name_to_add = transactions[idx + 1]
            date_to_add = transactions[idx - 2]

        if amount_match:
            if "-" not in amount_match.string:
                cents_to_add = round(float(trans.replace(",", "")) * 100)
                trans_obj_list.append(
                    {"name": name_to_add, "cents": cents_to_add, "date": date_to_add}
                )
            else:
                cents_to_add = round(
                    float(trans.replace("-", "").replace(",", "")) * 100
                )
                inverse_trans_list.append(
                    {"name": name_to_add, "cents": cents_to_add, "date": date_to_add}
                )
    print(trans_obj_list)
    return trans_obj_list, inverse_trans_list


file_dir = "oldstatements/"
# filenames = [
#     f for f in os.listdir(file_dir) if os.path.isfile(os.path.join(file_dir, f))
# ]
# print(filenames)
filepath = file_dir + "dec2024.pdf"
read_pdf_into_dicts(filepath)
