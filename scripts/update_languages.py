"""Generate a language card from public, non-fork GitHub repositories."""
import json
import os
from collections import Counter
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

OWNER = os.environ.get("PROFILE_OWNER", "FeuValente")

def api(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-languages"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    with urlopen(Request("https://api.github.com" + path, headers=headers), timeout=30) as response:
        return json.load(response)

def collect():
    totals = Counter()
    count = 0
    page = 1
    while True:
        repos = api(f"/users/{OWNER}/repos?type=owner&per_page=100&page={page}")
        if not repos:
            break
        for repo in repos:
            if repo["fork"] or repo.get("private") or repo["name"].lower() == OWNER.lower():
                continue
            totals.update(api(f'/repos/{repo["full_name"]}/languages'))
            count += 1
        page += 1
    return totals, count

def render(totals, count):
    total = sum(totals.values())
    rows = totals.most_common(7)
    colors = ["#72f5b0", "#5dd9ed", "#b6a2ff", "#f1d778", "#ffad87", "#f38cb8", "#98b5cf"]
    height = 138 + 42 * max(len(rows), 1)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="{height}" viewBox="0 0 720 {height}" role="img" aria-labelledby="title desc">',
             '<title id="title">Linguagens em movimento</title>',
             f'<desc id="desc">Distribuição por bytes de código em {count} repositórios públicos próprios, sem forks.</desc>',
             f'<rect width="720" height="{height}" rx="16" fill="#0d1518"/>',
             '<g font-family="Segoe UI,Arial,sans-serif">',
             '<text x="30" y="42" font-size="22" font-weight="700" fill="#edf6f1">Linguagens em movimento</text>',
             f'<text x="30" y="67" font-size="12" fill="#a7bfb3">{count} repositórios públicos · bytes de código · sem forks</text>']
    for i, (name, size) in enumerate(rows):
        y = 105 + i * 42
        pct = size / total * 100
        parts += [f'<text x="30" y="{y}" font-size="14" fill="#edf6f1">{escape(name)}</text>',
                  f'<rect x="165" y="{y - 11}" width="450" height="12" rx="6" fill="#22322c"/>',
                  f'<rect x="165" y="{y - 11}" width="{450 * pct / 100:.2f}" height="12" rx="6" fill="{colors[i]}"/>',
                  f'<text x="686" y="{y}" text-anchor="end" font-size="13" fill="#b9cdc2">{pct:.1f}%</text>']
    if not rows:
        parts += ['<text x="30" y="110" font-size="14" fill="#b9cdc2">Ainda sem código público para calcular.</text>']
    stamp = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    parts += [f'<text x="30" y="{height - 24}" font-size="11" fill="#8ea99b">Atualizado em {stamp} (UTC) · Top 7 · percentual sobre todas as linguagens</text>', '</g></svg>']
    return "\n".join(parts) + "\n"

if __name__ == "__main__":
    totals, count = collect()
    output = Path("assets/languages.svg")
    output.parent.mkdir(exist_ok=True)
    output.write_text(render(totals, count), encoding="utf-8")

