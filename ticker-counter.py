import requests


EXCLUDE_BLOCKS = {
    " Блок 20",
    " Блок 20.",
    " Блок 23",
    #" Блок 25",
    # " Блок 26",
}

# Exclude all the rows less or equals to the specified.
EXCLUDE_ROWS = {
    " Блок 15": 1,
    " Блок 16": 1,
    " Блок 17": 18,
    " Блок 18": 18,
    " Блок 19": 1,
}

URL = "https://api.eventim.com/seatmap/api/SeatMapHandler?smcVersion=v5.2&version=v5.2.2-1&cType=TDLREST&cId=1101&evId=1192163&key=&a_ts=1583880707473&a_SystemID=17&a_TDLToken=2F095E852F6B6B6B5F6B6B6B38A01D02636B626B057084165F4DD841B03D4D1239B1E57FA74CF4A02D8AC67AAE370A8EB069FD3184950205A62A8DB29F0B945242BFA0E2D09823EC&a_PromotionID=0&fun=json&areaId=0"

r = requests.get(URL)
data = r.json()

sectors = {
    "STRABAG" : [0, 0],
    "Сектор Б": [0, 0],
    "Сектор В": [0, 0],
    "Сектор Г": [0, 0]
}


def populate_sector(sector_name, available, reserved):
    if sector_name not in sectors:
        return

    sectors[sector_name][0] += reserved
    sectors[sector_name][1] += available


for block in data["blocks"]:
    sector_name = block["name"].split(",")[0]
    block_name = block["name"].split(",")[1] if len(block["name"].split(",")) > 1 else ""

    if block_name in EXCLUDE_BLOCKS:
        continue

    reserved = 0
    available = 0

    # Sort the rows by seat number so the lower rows to be the first.
    rows = sorted(block["r"], key=lambda r: r["g"][0]["s"][0])
    #rows = block["r"]

    for row_number, row in enumerate(rows):
        if EXCLUDE_ROWS.get(block_name) and EXCLUDE_ROWS.get(block_name) >= row_number + 1:
            continue

        for group in row["g"]:
            seatStatus = 0
            for seat in group["s"]:

                if len(seat) >= 4:
                    seatStatus = seat[3][0]

                if seatStatus == 1:
                    available += 1
                else:
                    reserved += 1

    populate_sector(sector_name, available, reserved)

total_reserved = 0
total_available = 0
for sector_name, counts in sorted(sectors.items()):
    sector_name = "Сектор А" if sector_name == "STRABAG" else sector_name
    total_reserved += counts[0]
    total_available += counts[1]
    print("{}, Продадени: {}, Свободни: {}, Общо:{}".format(sector_name, counts[0], counts[1], counts[0] + counts[1]))

print("Общо Продадени: {}, Свободни: {}, Общо:{}".format(total_reserved, total_available, total_reserved + total_available))

