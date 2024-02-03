import csv
from database.database import DatabaseManager
db_manager = DatabaseManager()

def insert_data_from_csv(db_manager):
    with open('blend_data.csv', mode='r') as infile:
        reader = csv.DictReader(infile)
        i = 1
        for row in reader:
            # Check for empty string and provide a default value of 0.0 if necessary
            try:
                kilos_to_produce = float(row['Kilos to Produce']) if row['Kilos to Produce'] else 0.0
            except Exception:
                kilos_to_produce = 0
            try:
                tablet_weight = float(row['Tablet weight']) if row['Tablet weight'] else 0.0
            except Exception:
                tablet_weight = 0
            try:
                tablets_amount = int(row['Tablets Amount']) if row['Tablets Amount'] else 0
            except Exception:
                tablets_amount = 0
            db_manager.insert_blend(
                code=row['Code'],
                product=row['PRODUCT'],
                tablets_amount=tablets_amount,
                kilos_to_produce=kilos_to_produce,
                tablet_size=row['Tablet Size'],
                tablet_weight=tablet_weight
            )
            print(f"[{i}] Inserted or updated information for {row['PRODUCT']}")
            i += 1
## Loads new Product Information into the database if there have been changes
## You need to 'run' this file individually
if __name__ == "__main__":
    print("This program updates all stored product data based on the contents of 'blend_data.csv'.")
    print("It is expected that you use a copy of the exact Product Information on our spreadsheets...")
    print("Type 'yes' if you're sure you want to continue (there are few fail-safes here if you've messed up!)")
    continue_opt = input("Are you sure? ")
    if continue_opt == "yes":
        insert_data_from_csv(db_manager)
    else:
        print("Exiting.")
        exit("User cancelled operation.")
