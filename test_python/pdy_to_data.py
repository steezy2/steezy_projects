from typing import List, Dict, Tuple
import pymupdf
import pandas
import xlsxwriter
import re


def read_pdf_into_dicts(name: str) -> Tuple[List[Dict], List[Dict]]:
    """Read a pdf and return a list of transaction dictionaries"""
    doc = pymupdf.open(name)
    end_strings = ["Transactions continued on next page", "TOTAL FEES FOR THIS PERIOD", "TOTAL INTEREST FOR THIS PERIOD"]
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

    print(f"transactions: {transactions}") # useful for debugging

    trans_obj_list = []
    inverse_trans_list = []
    # filter transactions into list of dicts
    for idx, trans in enumerate(transactions):
        reference_match = re.search(r"\d\d\d\d\d\d\d\S{10}", trans)
        amount_match = re.search(r"\.\d\d$", trans)
        print(amount_match)

        if reference_match:
            name_to_add = transactions[idx + 1]
            date_to_add = transactions[idx - 2]

        if amount_match:
            if "-" not in amount_match.string:
                print(trans)
                if "X" in trans:
                    print("X found")
                    print(trans)
                    break
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
    # print(trans_obj_list)
    return trans_obj_list, inverse_trans_list

def read_csv_into_dicts(name: str) -> Tuple[List[Dict], List[Dict]]:
    """Read a csv and return a list of transaction dictionaries"""
    df = pandas.read_csv(name)
    return df.to_dict('records')

if __name__ == "__main__":
    pdf_name = input("Please enter the statement pdf name without the .pdf: ")
    trans_list, inverse_list = read_pdf_into_dicts(f"{pdf_name}.pdf")
    df = pandas.DataFrame(trans_list)
    values = df.values.tolist()
    workbook = xlsxwriter.Workbook("statement_calc.xlsx")
    worksheet = workbook.add_worksheet(pdf_name)
    data = read_csv_into_dicts(f"{pdf_name}.csv")
    data = [dict(row) for row in data]
    print("testing")
    print(data)
    print("other data")
    print(values)

    row = 1
    col = 0
    for idx, line in enumerate(values):
        a, b, c = line
        worksheet.write(row, col, a)
        worksheet.write(row, col + 1, b)
        worksheet.write(row, col + 2, c)
        for data_idx, el in enumerate(data):
            desc_str: str = str(el["Description"]).lower()
            desc_str = desc_str.replace(" ", "")
            other_desc: str = str(a.lower())[:-2]
            other_desc = other_desc.replace(" ", "")
            amount : int= round(el["Amount"]*100)
            other_amount : int = round(b)
            if other_desc in desc_str:
                if "Bethany" in el["Cardholder"] and amount == other_amount:
                    worksheet.write(row, col + 3, "b")
                    data.pop(data_idx)
                    break
                if "Arnaud" in el["Cardholder"] and amount == other_amount:
                    worksheet.write(row, col + 3, "a")
                    data.pop(data_idx)
                    break
        row += 1

    # set column names
    worksheet.write(0, 0, "Transaction Name")
    worksheet.write(0, 1, "Amount in cents")
    worksheet.write(0, 2, "Post Date")
    worksheet.write(0, 6, f"Bethany owes in dollars")
    worksheet.write(1, 6, f'=SUMIF(D1:D{row}, "b", B1:B{row})/100')
    worksheet.write(0, 7, f"Arnaud owes in dollars")
    worksheet.write(1, 7, f'=SUMIF(D1:D{row}, "a", B1:B{row})/100')
    worksheet.write(0, 8, f"Total SUM in dollars")
    worksheet.write(1, 8, f"=SUM(B1:B{row})/100")
    worksheet.write(0, 9, f"Rewards from card")
    worksheet.write(1, 9, f"=I2*0.03")
    worksheet.write(4, 6, f"Please put any adjustments below here")
    worksheet.autofit()

    workbook.close()