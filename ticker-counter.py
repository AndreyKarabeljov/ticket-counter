import datetime
import json
import math

import requests

EXCLUDE_BLOCKS = {
    " Блок 20",
    " Блок 20.",
    " Блок 23",
    # " Блок 25",
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


def get_data_from_url():
    headers = {
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
        'Content-Type': 'application/json',
        'Origin': 'https://www.eventim.bg',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://www.eventim.bg/bg/bileti/106-godini-lubov-sofia-vivacom-arena-georgi-asparuhov-1198691/performance.html',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    params = (
        ('smcVersion', 'v5.2'),
        ('version', 'v5.2.2-1'),
        ('cType', 'TDLREST'),
        ('cId', '1101'),
        ('evId', '1198691'),
        ('key', ''),
        ('a_ts', '1589637445194'),
        ('a_SystemID', '17'),
        ('a_TDLToken',
         'AEE2A0652F6B6B6B5F6B6B6B530B8573636B626B9928E0A84D25AD6EE860DD093B39D7D82CC786ABDA345C59C222918D0B28316304BD620ED8B471938162E3AB3F6F771FD72FEC58'),
        ('a_PromotionID', '0'),
        ('fun', 'json'),
        ('areaId', '0'),
    )

    r = requests.get('https://api.eventim.com/seatmap/api/SeatMapHandler', headers=headers, params=params)
    return r.json()


def get_data_from_file():
    with open("/Users/akarabelyov/Library/Preferences/PyCharm2018.3/scratches/scratch.json") as json_file:
        return json.load(json_file)


data = get_data_from_url()
sectors = {
    "Сектор А": [0, 0],
    "Сектор Б": [0, 0],
    "Сектор В": [0, 0],
    "Сектор Г": [0, 0]
}

sectors_template_id = {
    "Сектор А": "a",
    "Сектор Б": "b",
    "Сектор В": "v",
    "Сектор Г": "g"
}

def populate_sector(sector_name, available, reserved):
    sector_name = "Сектор А" if sector_name == "STRABAG" or sector_name == "STRABAG VIP" else sector_name
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
    # rows = block["r"]

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
bindings = {}
for sector_name, counts in sorted(sectors.items()):
    total_reserved += counts[0]
    total_available += counts[1]
    total = counts[0] + counts[1]
    print("{}, Продадени: {}, Свободни: {}, Общо:{}".format(sector_name, counts[0], counts[1], total))
    print("{}%".format(math.ceil(counts[0] * 100 / (counts[0] + counts[1]))))

    template_id = sectors_template_id[sector_name]
    bindings["{{{{{}}}}}".format(template_id)] = "{}, продадени {} от {}".format(sector_name, counts[0], total)
    bindings["{{{{{}.p}}}}".format(template_id)] =  str(math.ceil(counts[0] * 100 / total))

total = total_reserved + total_available
print("Общо Продадени: {} ({}% от капацитета), Свободни: {}, Общо:{}".format(
    total_reserved,
    math.ceil(total_reserved * 100 / total),
    total_available,
    total))

bindings["{{total.all}}"] = str(total)
bindings["{{total.sold}}"] = str(total_reserved)
bindings["{{total.available}}"] = str(total_available)

def getTime():
    now = datetime.datetime.now()
    return now.strftime("%H:%M %d/%m/%Y")
bindings["{{date}}"] = getTime()

def publish():
    template_file = "/Users/akarabelyov/Downloads/www.levski.com/www.levski.com/levski/template.html"
    with open(template_file) as file:
        template = file.readlines()

    result = []
    for line in template:
        for key, value in bindings.items():
            if key in line:
                line = line.replace(key, value)
        result.append(line)

    index_file = "/Users/akarabelyov/Downloads/www.levski.com/www.levski.com/levski/index.html"
    with open(index_file, 'w') as file:
        file.writelines(result)
