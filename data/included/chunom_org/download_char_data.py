import csv
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

HTML_URL = "https://www.chunom.org/pages/standard/"
TSV_URL = "https://www.chunom.org/pages/standard-list/?max=2000&download=1"


def parse_cell_0(cell):
    # get rid of trailing period and space, then convert to int
    char_id = int(next(cell.children).strip()[:-1])
    prons = cell.find("a").text
    prons = prons.split(", ")
    return char_id, prons


def parse_cell_1(cell):
    # "Phonetic Loan"
    loan1 = bool(cell.find(class_="loan1"))
    # "Phonetic Loan (but rare, phonetic, or similar)"
    loan2 = bool(cell.find(class_="loan2"))
    char = cell.find("a").text
    return char, loan1, loan2


def parse_cell_2(cell):
    definition = cell.text

    return definition


def parse_cell_3(cell):
    freq_score = cell.text

    return freq_score


def parse_cell_4(cell: Tag):
    gray_variants = ""
    black_variants = ""
    for span in cell.find_all("span", recursive=False):
        anchors = span.find_all("a", recursive=False)
        # page address is "/pages/𢫘/", etc.
        chars = "".join(a["href"][-2] for a in anchors)
        # TODO: what is this supposed to indicate?
        if "opacity" in span.get("style", ""):
            gray_variants += chars
        else:
            black_variants += chars
    return black_variants, gray_variants


def fetch_char_data():
    page = requests.get(HTML_URL)
    soup = BeautifulSoup(page.content, "html.parser")
    table = soup.find(id="std-table")
    rows = table.find_all("tr")
    all_char_data = []
    # skip header row
    for r in rows[1:]:
        cells = r.find_all("td")

        id_, prons = parse_cell_0(cells[0])
        char, loan1, loan2 = parse_cell_1(cells[1])
        definition = parse_cell_2(cells[2])
        freq_score = parse_cell_3(cells[3])
        black_variants, gray_variants = parse_cell_4(cells[4])

        char_data = {
            "id": id_,
            "prons": "|".join(prons),
            "loan1": loan1,
            "loan2": loan2,
            "char": char,
            "definition": definition,
            "freq_score": freq_score,
            "black_variants": black_variants,
            "gray_variants": gray_variants,
        }
        all_char_data.append(char_data)
    return all_char_data


def main(out_file):
    data = fetch_char_data()
    keys = data[0].keys()
    with open(out_file, "w", newline="") as f:
        dict_writer = csv.DictWriter(f, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)


if __name__ == "__main__":
    current_dir = Path(__file__).parent
    main(current_dir / "char_data.csv")
