import pandas as pd
import mysql.connector

def parse_rating(rating_str):
    if isinstance(rating_str, str):
        if "One" in rating_str:
            return 1.0
        elif "Two" in rating_str:
            return 2.0
        elif "Three" in rating_str:
            return 3.0
        elif "Four" in rating_str:
            return 4.0
        elif "All" in rating_str:
            return 5.0
    return None

df = pd.read_csv("hotels.csv", encoding="ISO-8859-1")
df.columns = df.columns.str.strip()


df = df[df['countyName'].str.strip().str.lower() == 'czech republic']

print("Broj hotela iz Czech Republic:", len(df))

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="dbubanj",
    database="hotelmatch"
)
cursor = conn.cursor()

for _, row in df.iterrows():
    hotel_rating = parse_rating(row['HotelRating'])
    row = row.where(pd.notnull(row), None)

    sql = """
        INSERT IGNORE INTO hotels (
            countyCode, countyName, cityCode, cityName,
            HotelCode, HotelName, HotelRating, Address,
            Attractions, Description, FaxNumber, HotelFacilities,
            Map, PhoneNumber, PinCode, HotelWebsiteUrl
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        row['countyCode'], row['countyName'], row['cityCode'], row['cityName'],
        row['HotelCode'], row['HotelName'], hotel_rating, row['Address'],
        row['Attractions'], row['Description'], row['FaxNumber'], row['HotelFacilities'],
        row['Map'], row['PhoneNumber'], row['PinCode'], row['HotelWebsiteUrl']
    )

    try:
        cursor.execute(sql, values)
    except Exception as e:
        print(f"Greška za {row.get('HotelCode', 'N/A')}: {e}")

conn.commit()
cursor.close()
conn.close()
print("Unos za Czech Republic završen.")
