import xlsxwriter

# Create a workbook and add a worksheet.
workbook = xlsxwriter.Workbook('pie_chart.xlsx')
worksheet = workbook.add_worksheet()

# Data for the chart.
headings = ['Category', 'Values']
data = [
    ['A', 'B', 'C', 'D'],
    [10, 40, 50, 20]
]

# Write the data to the worksheet.
worksheet.write_row('A1', headings)
worksheet.write_column('A2', data[0])
worksheet.write_column('B2', data[1])

# Create a pie chart object.
chart = workbook.add_chart({'type': 'pie'})

# Add a series to the chart.
chart.add_series({
    'name':       'Pie Chart',
    'categories': '=Sheet1!$A$2:$A$5',
    'values':     '=Sheet1!$B$2:$B$5',
})

# Insert the chart into the worksheet.
worksheet.insert_chart('C2', chart)

workbook.close()