"""Read one sheet of an .xlsx as a list of row tuples: openpyxl if importable, else
zipfile + XML (standard library)."""
from __future__ import annotations
import re, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}


def _col(ref: str) -> int:
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_sheet(path: Path, name: str) -> list[tuple]:
    try:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True)
        return [tuple(r) for r in wb[name].iter_rows(values_only=True)]
    except ImportError:
        pass
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
    wbx = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rmap = {r.get("Id"): r.get("Target") for r in rels}
    target = None
    for s in wbx.find("m:sheets", NS):
        if s.get("name") == name:
            target = rmap[s.get(f"{{{NS['r']}}}id")]
    target = target.lstrip("/")
    if not target.startswith("xl/"):
        target = "xl/" + target
    rows = []
    for row in ET.fromstring(z.read(target)).iter(f"{{{NS['m']}}}row"):
        vals = {}
        for c in row.findall("m:c", NS):
            v = c.find("m:v", NS)
            t = c.get("t")
            if t == "s" and v is not None:
                val = shared[int(v.text)]
            elif t == "inlineStr":
                val = "".join(x.text or "" for x in c.iter(f"{{{NS['m']}}}t"))
            else:
                val = v.text if v is not None else None
            vals[_col(c.get("r"))] = val
        rows.append(tuple(vals.get(i) for i in range(max(vals) + 1)) if vals else tuple())
    return rows
