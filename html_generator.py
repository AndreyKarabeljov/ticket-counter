import datetime
import os

import config
from eventim_client import SECTOR_ORDER

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
                <span class="elementor-progress-percentage"></span>
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
SOLD_SECTORS = []


def _get_time():
    now = datetime.datetime.now()
    return now.strftime("%H:%M %d/%m/%Y")


def _update_bindings(template, bindings):
    result = []
    for line in template:
        for key, value in bindings.items():
            if key in line:
                line = line.replace(key, value)
        result.append(line)

    return result


def _process_sold_sector_template(sector_results):
    result = ""

    for r in sector_results:
        if r["name"] in SOLD_SECTORS:
            bindings = {
            "{{t}}": "{}, продадени {} от {}".format(r["name"], r["total"], r["total"])
            }
            result = result + (_update_bindings([SOLD_SECTOR_HTML], bindings)[0])

    return result


def _process_sector_template(sector_results):
    result = ""

    for r in sector_results:
        if r["total"] == r["sold"]:
            bindings = {
            "{{t}}": "{}, оставащи  {}".format(r["name"], r["available"])
            }
            result = result + (_update_bindings([SOLD_SECTOR_HTML], bindings)[0])
            continue

        bindings = {
            "{{t}}": "{}, оставащи {}".format(r["name"], r["available"]),
            "{{t.p}}": str(int(r["sold"] * 100 / r["total"]))
        }
        result = result + (_update_bindings([SECTOR_HTML], bindings)[0])

    return result


def _get_income(sector_results):
    income = 0
    for s in sector_results:
        price = 10 if s["name"] in SECTOR_ORDER[:2] else 10
        income = (s["sold"] * price) + income

        if s["name"] in SOLD_SECTORS and s["total"] != s["sold"]:
            income = (s["total"] * price) + income

    print("Total income: " + str(income))

    return income


def _get_total_sold(sector_results):
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
    bindings["{{total.all}}"] = "{:,.0f}".format(total_reserved + total_available)
    bindings["{{total.income}}"] = "{:,.0f}".format(_get_income(sector_results))
    bindings["{{current.sold}}"] = "{:,.0f}".format(total_reserved)
    bindings["{{total.sold}}"] = "{:,.0f}".format(_get_total_sold(sector_results))
    bindings["{{total.available}}"] = "{:,.0f}".format(total_available)
    bindings["{{date}}"] = _get_time()
    bindings["{{title}}"] = config.title
    bindings["{{subtitle}}"] = config.subtitle
    bindings["{{link_url}}"] = config.link_url
    bindings["{{link_image}}"] = config.link_image
    #bindings["{{sold_sectors}}"] = process_sold_sector_template(sector_results)
    bindings["{{sectors}}"] = _process_sector_template(sector_results)

    result = _update_bindings(template, bindings)

    index_file = os.path.join(site_dir, "index.html")
    with open(index_file, 'w') as file:
        file.writelines(result)
