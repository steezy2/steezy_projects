from datetime import datetime
import xlsxwriter
from typing import Tuple

import xlsxwriter.worksheet


categories = [
    "gas/electric",
    "utilities",
    "auto",
    "groceries",
    "dining out",
    "entertainment",
    "amazon",
    "tolls",
    "travel",
    "health care",
    "personal care",
    "home care",
    "subscription services",
    "other",
]


category_map_name = {
    "gas/electric": ["fuel", "petrol", "diesel"],
    "utilities": ["electricity", "water", "gas", "internet", "phone", "trash"],
    "auto": ["vehicle insurance", "auto insurance", "auto repair", "auto parts", "auto registration"],
    "groceries": ["food", "supermarket", "grocery store"],
    "dining out": ["restaurants", "eating out", "takeout"],
    "entertainment": ["movies", "concerts", "amusement parks"],
    "amazon": ["online shopping", "e-commerce"],
    "tolls": ["tolls"],
    "travel": ["vacation", "trips", "flights"],
    "health care": ["medical", "doctor", "hospital"],
    "personal care": ["beauty", "hygiene", "wellness"],
    "home care": ["home repairs", "home tools"],
    "subscription services": ["memberships", "monthly fees"],
    "other": ["miscellaneous", "various", "uncategorized"],
}


category_map_statement = {
    "gas/electric": [
        "fuel",
        "loaf n jug",
        "phillips 66",
        "qt",
        "town pump",
        "circle k",
        "7-eleven",
        "conoco",
        "chargepoint",
        "sinclair",
        "shell",
        "rocket 6546",
        "exxon",
        "stop 4 gas",
        "coalmine gas",
        "maverik",
        "food and gas",
        "electrify amer",
        "evgateway"
    ],
    "utilities": [
        "spectrum mobile",
        "summit utilities",
        "core electric",
        "mountain view wast",
        "spectrum",
        "neteo",
    ],
    "auto": [
        "t5",
        "bachman",
        "geico",
        "co motor vehicle",
        "allstate",
        "big o tires",
        "big d",
        "napa",
        "stevinson chev",
        "audi denver",
        "alpine buick",
    ],
    "groceries": [
        "king soopers",
        "safeway",
        "wine and liquor",
        "nakedwines.com",
        "wine and spir",
        "wine spirits",
        "wholefds",
        "liquors",
        "trader joe",
        "sprouts",
        "liquor",
        "friends supermarket",
    ],
    "dining out": [
        "one barrel",
        "jack's bar",
        "food court",
        "washingtons",
        "cannonball",
        "boulder dushanbe",
        "greenfields pool",
        "domino's",
        "restaurant",
        "pho kitchen",
        "the barrel",
        "nepal cafe",
        "rock cut brewing",
        "starbuck",
        "canteen",
        "the boot grill",
        "sanun thai",
        "cajun grill",
        "nayax",
        " bar ",
        "cafe",
        "brewery",
        "oskar blues",
        "jack's slopeside",
        "tavern",
        "fish house",
        "pho",
        "sushi",
        "brewing",
        "ramen",
        "food truck",
        "511 rose",
        "still whiskey",
        "cow eatery",
        "coffee",
        "resta",
        "subway",
        "taco bell",
        "einstein bros",
        "snowpack taproom",
        "los 3 garcia's",
        "bbq",
        "potbelly",
        "long table",
        "elizabeth marriott",
        "lynn's whistle stop",
        "modern market",
        "mezza mediterranean",
        "mile high hamburger",
        "william oliver's",
        "dr proctors lounge",
        "linglon",
        "meadery",
        "the g wagon",
        "lobster roll",
        "olive and finch",
        "tony p's",
        "tabletop",
        "lucky bird",
        "saloon",
        "burndown",
        "mcdonald's",
        "snooze ft",
        "resolute brew",
        "beard papa",
        "empire dairy",
        "fellow traveler",
        "denver sweet",
        "westwoods res",
        "gque",
        "sit n bull",
        "tacos",
        "opa grill",
        "brioche doree",
        "mamatte lille",
        "choco delight",
        "groot melkhuis",
        "billy brunch",
        "food and wine",
        "calzedonia",
        "snarfs",
        "qdoba",
        "edgewater inn",
    ],
    "entertainment": [
        "stubhub",
        "cottonwood hot springs",
        "marquis theater",
        "fanexpo",
        "arthur murray dance",
        "goodrec.com",
        "the ritz carlton",
        "imax",
        "ice castles",
        "colorado mountain school",
        "axs.com",
        "steam purchase",
        "meow wolf",
        "red rocks amphith",
        "gothic theatre",
        "google *whiteout",
        "the plug las",
        "alamo aspen grove retail",
        "recreation.gov",
        "washington, llc",
        "microsoft*xbox",
        "denver new years",
        "the nightfall",
        "larimer co dept",
        "evolve st2410",
        "ikon pass",
        "the bulldog",
        "pindustry",
    ],
    "amazon": ["amzn", "amazon"],
    "tolls": ["express tolls"],
    "travel": [
        "vueling air",
        "public works-prkg",
        "public parking",
        "fillia dublin",
        "frontier a",
        "rtd englewood",
        "alexis park resort",
        "aerling",
        "amtrak",
        "newrest travel",
        "united",
        "lime",
        "vueling",
        "gare orly",
        "rtd",
    ],
    "health care": ["naturalcycles", "west ranch dental"],
    "personal care": [
        "dollar tree",
        "walgreens",
        "wm supercenter",
        "wal-mart",
        "target",
        "rei",
        "arc thrift",
        "joann stores",
        "disguises",
        "petsmart",
        "sally beauty",
        "sierra",
        "goat yog",
        "golden poppy",
        "pine junction country",
        "ross stores",
        "inner me consignment",
        "ls unleashed energy",
        "integrative heal",
        "k up lille",
    ],
    "home care": [
        "the home depot",
        "living water pump",
        "altitude electric",
        "lantzs ",
        " ace ",
        "brad co plumbing"
    ],
    "subscription services": [
        "chuze fitness",
        "netflix.com",
        "microsoft*realms",
        "microsoft*store",
    ],
    "other": [],
}



def create_pie_chart(workbook: xlsxwriter.Workbook, worksheet: xlsxwriter.worksheet.Worksheet, sheetname: str):
    # Create a pie chart object.
    chart = workbook.add_chart({'type': 'pie'})

    # Add a series to the chart.
    chart.add_series({
        'name':       'Budget Pie',
        'categories': f"={sheetname}!$A$1:$A$13",
        'values':     f"={sheetname}!$B$1:$B$13",
        'data_labels': {'value': True, 'category': True, 'percentage': True},
    })

    # Insert the chart into the worksheet.
    worksheet.insert_chart('C20', chart, {'x_scale': 2, 'y_scale': 2})

class Category:
    def __init__(
        self, name: str, othernames: list[str], search: list[str], total: float
    ):
        self.name: str = name
        self.othernames: list[str] = othernames
        self.search: list[str] = search
        self.total: float = total
        self.transactions: list[str] = []

    def __str__(self):
        return f"Category(name={self.name}, total={self.total})"

    def searching(self, name) -> bool:
        for searchitem in self.search:
            if searchitem in name:
                return True

        return False

    def searching_test(self, name) -> Tuple[bool, str]:
        for searchitem in self.search:
            if searchitem in name:
                return True, searchitem

        return False, None


class BudgetEntry:
    def __init__(self, data, year=2025):
        self.name = str(data["name"]).lower()
        self.cents = float(data["cents"])
        self.dollar = self.cents / 100
        try:
            self.date = datetime.strptime(f"{data['date']}/{year}", "%m/%d/%Y")
        except ValueError:
            self.date = datetime.strptime(f"01/01/1900", "%m/%d/%Y")
        self.category = None

    def __str__(self):
        return f"{
            self.name}: ${
            '{:.2f}'.format(
                self.dollar)} date:{
                self.date.strftime('%m/%d/%Y')}"

    def print_category(self):
        print(f"category:{self.category}\n")

    def assign_category(self, category: Category):
        self.category = category


class Categories:
    categories: dict[str, Category] = {}

    def __init__(self):
        for name in categories:
            self.categories[name] = Category(
                name, category_map_name[name], category_map_statement[name], float(0)
            )

    def __str__(self):
        return f"Categories(categories={self.categories})"

    def search(self, name) -> Category:
        for category in self.categories.values():
            if category.searching(name):
                return category

        return self.categories["other"]

    def search_test(self, name) -> Tuple[Category, str]:
        for category in self.categories.values():
            outbool, outstring = category.searching_test(name)
            if outbool:
                return category, outstring

        return self.categories["other"], None

    def addToTotal(self, budgetEntry: BudgetEntry):
        if budgetEntry.category:
            self.categories[budgetEntry.category.name].total += budgetEntry.dollar
            self.categories[budgetEntry.category.name].transactions.append(
                budgetEntry.__str__()
            )
        else:
            self.categories["other"].total += budgetEntry.dollar
            self.categories["other"].transactions.append(budgetEntry.__str__())

    def print_outfile_budget(self, filename: str):
        total_amount = float(0)
        with open(filename, "w") as f:
            for category in self.categories.values():
                print(
                    f"{
                        category.name}: ${
                        '{:.2f}'.format(
                            category.total)}\n transactions: {
                        category.transactions}"
                )
                f.write(
                    f"{
                        category.name}: ${
                        '{:.2f}'.format(
                            category.total)}\n transactions: {
                        category.transactions}\n"
                )
                total_amount += category.total

            formatted_total = "{:.2f}".format(total_amount)
            print(f"Total statement: ${formatted_total}\n\n\n")
            print(
                "_________________________________________________________________________________________\n\n"
            )
            f.write(f"Total statement: ${formatted_total}\n")

    def print_to_excel(self, filename: str):
        workbook = xlsxwriter.Workbook(filename)
        sheetname = filename.split("\\")[-1]

        worksheet = workbook.add_worksheet(sheetname[:-5])
        money_format = workbook.add_format({'num_format': '$#,##0.00'})

        row = 0
        col = 0
        total = 0
        for category in self.categories.values():
            total += category.total
            worksheet.write(row, col, category.name)
            worksheet.write(row, col + 1, category.total, money_format)
            worksheet.write(row, col + 2, "transactions:")
            num = 3
            for transaction in category.transactions:
                worksheet.write(row, col + num, transaction)
                num += 1
            row += 1
        
        worksheet.write(row + 2, 0, "Total")
        worksheet.write(row + 2, 1, total)

        create_pie_chart(workbook, worksheet, sheetname[:-5])
        worksheet.autofit()


        workbook.close()




teststring = "vueling airlufnl9s barcelona"

categories_test = Categories()
out1, out2 = categories_test.search_test(teststring)
print(out1, out2)
