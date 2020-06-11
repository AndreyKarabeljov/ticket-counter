import datetime
import json
import os
import re
import subprocess
from time import sleep

import requests

current_dir = os.path.dirname(os.path.realpath(__file__))
site_dir = os.path.join(current_dir, "..", "levski")

SECTOR_HTML = """
<div class="elementor-element elementor-element-c58cad0 elementor-widget elementor-widget-progress"
    data-id="c58cad0" data-element_type="widget"
    data-widget_type="progress.default">
    <div class="elementor-widget-container">
        <span class="elementor-title">{{t}}</span>

        <div class="elementor-progress-wrapper progress-info" role="progressbar"
            aria-valuemin="0" aria-valuemax="100" aria-valuenow="10"
            aria-valuetext="">
            <div class="elementor-progress-bar" data-max="{{t.p}}"
                style="width: {{t.p}}%;">
                <span class="elementor-progress-text"></span>
                <span class="elementor-progress-percentage">{{t.p}}%</span>
            </div>
        </div>
    </div>
</div>
"""

SOLD_SECTOR_HTML = """
<div class="elementor-element elementor-element-c58cad0 elementor-widget elementor-widget-progress"
    data-id="c58cad0" data-element_type="widget"
    data-widget_type="progress.default">
    <div class="elementor-widget-container">
        <span class="elementor-title">{{t}}</span>

        <div class="elementor-progress-wrapper progress-success"
            role="progressbar" aria-valuemin="0" aria-valuemax="100"
            aria-valuenow="100" aria-valuetext="100">
            <div class="elementor-progress-bar" data-max="100"
                style="width: 100%;">
                <span class="elementor-progress-text"></span>
                <span class="elementor-progress-percentage">100%</span>
            </div>
        </div>
    </div>
</div>
"""

SECTOR_ORDER = [
    "ВИП",
    "Скайбокс*",
    "Сектор А",
    "Сектор Б",
    "Сектор В",
    "Сектор Г"
]
SOLD_SECTORS = []

EXCLUDE_BLOCKS = {
    " Блок 20",
    " Блок 20.",
    " Блок 23",
    " Блок 7",
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

SPECIAL_TICKETS = "БЪДИ С ОТБОРА!"

def get_token():
    url = "https://www.eventim.bg/bg/bileti/levski-ludogorec-sofia-vivacom-arena-georgi-asparuhov-1192163/performance.html"
    r = requests.get(url)
    tokenPattern = '''"authToken":"(.*?)"'''
    match = re.search(tokenPattern, r.text)
    return match.groups(0)

def get_data_from_url():
    token = get_token()
    print(token)
    headers = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
        'Content-Type': 'application/json',
        'Origin': 'https://www.eventim.bg',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://www.eventim.bg/bg/bileti/levski-ludogorec-sofia-vivacom-arena-georgi-asparuhov-1192163/performance.html',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    params = (
        ('smcVersion', 'v5.2'),
        ('version', 'v5.2.2-1'),
        ('cType', 'TDLREST'),
        ('cId', '1101'),
        ('evId', '1192163'),
        ('key', ''),
        ('a_ts', '1590686109529'),
        ('a_SystemID', '17'),
        ('a_TDLToken',
         token),
        ('a_PromotionID', '0'),
        ('fun', 'json'),
        ('areaId', '0'),
    )

    r = requests.get('https://api.eventim.com/seatmap/api/SeatMapHandler', headers=headers, params=params)
    return r.json()


def get_data_from_file():
    with open(os.path.join(current_dir, "sample-data.json")) as json_file:
        return json.load(json_file)


def get_sector_results():
    def populate_sector(sector_name, available, reserved):
        sector_name = "Сектор А" if sector_name == "STRABAG" else sector_name
        sector_name = "ВИП" if sector_name == "STRABAG VIP" else sector_name

        if sector_name not in sectors:
            return

        sectors[sector_name][0] += reserved
        sectors[sector_name][1] += available

    data = get_data_from_file()
    sectors = {
        "Скайбокс*": [0, 0],
        "ВИП": [0, 0],
        "Сектор А": [0, 0],
        "Сектор Б": [0, 0],
        "Сектор В": [0, 0],
        "Сектор Г": [0, 0]
    }

    for block in data["blocks"]:
        sector_name = block["name"].split(",")[0]
        block_name = block["name"].split(",")[1] if len(block["name"].split(",")) > 1 else ""

        if block_name in EXCLUDE_BLOCKS:
            continue

        if sector_name == SPECIAL_TICKETS:
            print(block["graphics"][0]["pcBlock"])
            print(block["graphics"][1]["pcBlock"])
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

        if block_name.startswith(" Box"):
            sector_name = "Скайбокс*"
            reserved = 0 if len(block["graphics"][0]["pcBlock"]) > 0 else 17
            available = 17 - reserved

        populate_sector(sector_name, available, reserved)

    total_reserved = 0
    total_available = 0

    sector_results = []
    for sector_name in SECTOR_ORDER:
        counts = sectors[sector_name]
        total_reserved += counts[0]
        total_available += counts[1]
        total = counts[0] + counts[1]
        print("{}, Продадени: {}, Свободни: {}, Общо:{}".format(sector_name, counts[0], counts[1], total))
        print("{}%".format(int(counts[0] * 100 / (counts[0] + counts[1]))))

        sector_results.append(
            {
                "name": sector_name,
                "sold": counts[0],
                "available": counts[1],
                "total": total
            }
        )

    print("Общо Продадени: {} ({}% от капацитета), Свободни: {}, Общо:{}".format(
        total_reserved,
        int(total_reserved * 100 / (total_reserved + total_available)),
        total_available,
        total_reserved + total_available))

    return total_reserved, total_available, sector_results

def getTime():
    now = datetime.datetime.now()
    return now.strftime("%H:%M %d/%m/%Y")

def update_bindings(template, bindings):
    result = []
    for line in template:
        for key, value in bindings.items():
            if key in line:
                line = line.replace(key, value)
        result.append(line)

    return result

def process_sold_sector_template(sector_results):
    result = ""

    for r in sector_results:
        if r["name"] in SOLD_SECTORS:
            bindings = {
            "{{t}}": "{}, продадени {} от {}".format(r["name"], r["total"], r["total"])
            }
            result = result + (update_bindings([SOLD_SECTOR_HTML], bindings)[0])

    return result

def process_sector_template(sector_results):
    result = ""

    for r in sector_results:
        if r["total"] == r["sold"]:
            bindings = {
            "{{t}}": "{}, продадени {} от {}".format(r["name"], r["sold"], r["total"])
            }
            result = result + (update_bindings([SOLD_SECTOR_HTML], bindings)[0])
            continue

        bindings = {
            "{{t}}": "{}, продадени {} от {}".format(r["name"], r["sold"], r["total"]),
            "{{t.p}}": str(int(r["sold"] * 100 / r["total"]))
        }
        result = result + (update_bindings([SECTOR_HTML], bindings)[0])

    return result

def get_income(sector_results):
    income = 0
    for s in sector_results:
        price = 10 if s["name"] in SECTOR_ORDER[:2] else 10
        income = (s["sold"] * price) + income

        if s["name"] in SOLD_SECTORS and s["total"] != s["sold"]:
            income = (s["total"] * price) + income

    print("Total income: " + str(income))

    return income

def get_total_sold(sector_results):
    sold = 0
    for s in sector_results:
        sold = sold + s["sold"]

        if s["name"] in SOLD_SECTORS and s["total"] != s["sold"]:
            sold = s["total"] + sold

    return sold

def process_html_template(total_reserved, total_available, sector_results):
    template_file = os.path.join(site_dir, "template.html")
    with open(template_file) as file:
        template = file.readlines()

    bindings = dict()
    bindings["{{total.all}}"] = str(total_reserved + total_available)
    bindings["{{total.income}}"] = "{:,.0f}".format(get_income(sector_results))
    bindings["{{current.sold}}"] = "{:,.0f}".format(total_reserved)
    bindings["{{total.sold}}"] = "{:,.0f}".format(get_total_sold(sector_results))
    bindings["{{total.available}}"] = "{:,.0f}".format(total_available)
    bindings["{{date}}"] = getTime()
    #bindings["{{sold_sectors}}"] = process_sold_sector_template(sector_results)
    bindings["{{sectors}}"] = process_sector_template(sector_results)

    result = update_bindings(template, bindings)

    index_file = os.path.join(site_dir, "index.html")
    with open(index_file, 'w') as file:
        file.writelines(result)

def commit():
    working_directory = site_dir
    os.chdir(working_directory)
    proc = subprocess.Popen(["git", "add", "index.html"], stdout=subprocess.PIPE)
    result = [x.decode('utf-8').rstrip('\n') for x in proc.stdout.readlines()]
    for l in result:
        print(l)

    proc = subprocess.Popen(["git", "commit", "-m", "stats"], stdout=subprocess.PIPE)
    result = [x.decode('utf-8').rstrip('\n') for x in proc.stdout.readlines()]
    for l in result:
        print(l)

    proc = subprocess.Popen(["git", "push"], stdout=subprocess.PIPE)
    result = [x.decode('utf-8').rstrip('\n') for x in proc.stdout.readlines()]
    for l in result:
        print(l)

def process():
    total_reserved, total_available, sector_results = get_sector_results()
    process_html_template(total_reserved, total_available, sector_results)
    commit()

#process()
for i in range(1, 1000):
    process()
    sleep(60 * 10)
