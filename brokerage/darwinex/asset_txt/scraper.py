import json
from bs4 import BeautifulSoup

with open("assets.json", "r") as f:
    assets = json.load(f)

with open("commodities.txt") as f:
    contents = f.read()

soup = BeautifulSoup(contents, "html.parser")

cont = soup.find(id="commodities-content")
rows = cont.find_all("tr")

tickers = []
for r in rows:
    code = str(r).split("</td>")[0].split("<td>")[1]
    tickers.append(code)

assets["commodities"] = tickers

with open("assets.json", "w") as f:
    json.dump(assets, f, indent=4)

