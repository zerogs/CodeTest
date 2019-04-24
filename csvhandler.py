import csv


def csv_reader(file_obj):
    """
        Read a CSV file using csv.DictReader
        """
    reader = csv.DictReader(file_obj, delimiter=';')
    lst = []
    for line in reader:
        lst.append((line['last_name'], line['first_name'], line['patronymic']))

if __name__ == "__main__":
    with open("test.csv") as f_obj:
        csv_reader(f_obj)