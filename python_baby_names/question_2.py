import os
import mixins
import pandas as pd
import settings

from bs4 import BeautifulSoup


NAMES_IN_REPORT = ["Ryan", "Ben", "Eugene"]
EXCEL_FILENAME = 'report.xlsx'
EXCEL_SHEETNAME = 'Great Report'


class Script(mixins.BabyNamesMixin):
    """
    This script details the rankings over the available years for specific
    baby names.
    """
    def __init__(self, names_in_report: list, excel_filename: str = '',
                 excel_sheetname: str = ''):
        self.names_in_report = names_in_report
        if not excel_filename:
            excel_filename = os.path.basename(__file__).replace('.py', '_report.xlsx')
            output_path = (
                os.path.dirname(os.path.abspath(__file__)) + '\\' + excel_filename)
        self.output_path = output_path
        self.excel_sheetname = excel_sheetname

    def execute_report(self):
        columns = ['Year'] + self.names_in_report
        male_df = pd.DataFrame(columns=columns)
        male_df.columns = pd.MultiIndex.from_tuples(
            zip(['Male Name Rankings Per Year', '', '', ''], male_df.columns))

        female_df = pd.DataFrame(columns=columns)
        female_df.columns = pd.MultiIndex.from_tuples(
            zip(['Female Name Rankings Per Year', '', '', ''], female_df.columns))

        filenames, available_years = self.get_filename_info()

        # Gather the data from the files.
        for index, filename in enumerate(filenames):
            html_file = open(f'{settings.RELATIVE_PATH}/{filename}', 'r')
            contents = html_file.read()
            soup = BeautifulSoup(contents, 'html.parser')

            year = available_years[index]
            self.validate_year(year, soup)
            table = self.get_table(soup)

            # Find all the rows in the table.
            # The first row is the header, so skip it.
            rows = table.find_all('tr', attrs={'align': 'right'})[1:]

            # The dictionary element's key will be the name.
            # The dictionary element's value will be the rank.
            male_names = {}
            female_names = {}
            for row in rows:
                # For most of the html files, the table rows are missing the
                # closing tr tags, so I am calling "next" until I get the correct
                # element.
                rank_el = row.next.next
                rank_num = int(str(rank_el))
                tag = rank_el.next
                male_name = tag.text.strip()
                male_names[male_name] = rank_num
                female_name = tag.next_sibling.text.strip()
                female_names[female_name] = rank_num

            # Example:
            # https://www.geeksforgeeks.org/how-to-add-one-row-in-an-existing-pd-dataframe/
            # Append a new row to the male's table.
            male_df.loc[len(male_df.index)] = \
                self.add_data_to_row(male_names, [year])

            # Append a new row to the female's table.
            female_df.loc[len(female_df.index)] = \
                self.add_data_to_row(female_names, [year])
            html_file.close()

        self.save_to_excel([male_df, female_df])

    def add_data_to_row(self, names: dict, new_row_data: list = []) -> list:
        for name in self.names_in_report:
            try:
                rank = names[name]
            except KeyError:
                rank = 'N/A'
            new_row_data.append(rank)
        return new_row_data

    def save_to_excel(self, dataframes):
        writer = pd.ExcelWriter(self.output_path, engine='xlsxwriter')
        row = 0
        for df in dataframes:
            df.to_excel(
                writer,
                sheet_name=self.excel_sheetname,
                startrow=row,
                startcol=0,
            )
            row = row + len(df.index) + 2
        writer.save()

Script(
    NAMES_IN_REPORT,
    excel_sheetname=EXCEL_SHEETNAME,
).execute_report()
