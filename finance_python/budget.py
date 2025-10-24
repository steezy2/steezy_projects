import pdy_to_data
from budget_data import *
from typing import Tuple
import pandas


def parsebudget(data, year) -> Tuple[list[BudgetEntry], Categories]:
    budgetArray: list[BudgetEntry] = []
    categories = Categories()
    for line in data:
        budget_entry = BudgetEntry(line, year)
        category = categories.search(budget_entry.name)
        budget_entry.assign_category(category)
        categories.addToTotal(budget_entry)
        budgetArray.append(budget_entry)

    return budgetArray, categories


def combine_xlsx_files(filenames: list[str], output_filename: str) -> None:
    # create a workbook
    output_workbook = xlsxwriter.Workbook(output_filename)
    money_format = output_workbook.add_format({'num_format': '$#,##0.00'})
    

    # loop over the files and add a sheet from each one to the output workbook
    for filename in filenames:
        workbook = pandas.read_excel(filename, sheet_name=None)
        for sheet_name, df in workbook.items():
            output_worksheet = output_workbook.add_worksheet(sheet_name)
            for row_num, row in df.iterrows():
                for col_num, val in enumerate(row):
                    out = str(val)
                    if out not in "nan":
                        if col_num == 1:
                            output_worksheet.write(row_num, col_num, val, money_format)
                        else:
                            output_worksheet.write(row_num, col_num, val)
                        create_pie_chart(output_workbook, output_worksheet, sheet_name)
                        output_worksheet.autofit()

            
        

    # close the output workbook
    output_workbook.close()


if __name__ == "__main__":
    import os

    file_dir = "oldstatements/"
    filenames = [
        f for f in os.listdir(file_dir) if os.path.isfile(os.path.join(file_dir, f))
    ]

    output_dir = "budget"
    excel_filenames = []
    for filename in filenames:
        filepath = file_dir + filename
        (output, _) = pdy_to_data.read_pdf_into_dicts(filepath)
        year_str = filename[:-4]
        year = int(year_str[-4:])

        budget_arr, budget_categories = parsebudget(output, year)

        print("\n\n__________________Final Categorized Budget:__________________\n")
        file_path = os.path.join(output_dir, filename[:-4])
        budget_categories.print_outfile_budget(f"{file_path}.txt")
        budget_categories.print_to_excel(f"{file_path}.xlsx")
        excel_filenames.append(f"{os.path.join(output_dir, filename[:-4])}.xlsx")

    combine_xlsx_files(excel_filenames, "combinedBudget.xlsx")
