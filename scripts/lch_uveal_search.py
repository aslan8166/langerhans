#!/usr/bin/env python3
"""Reproducible metadata search for uveal/choroidal/intraocular LCH review.

Queries freely accessible APIs, optionally imports manual exports from subscription
bibliographic databases, deduplicates records, flags likely relevant/excluded
records, and writes PRISMA-oriented outputs.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
MANUAL = ROOT / "data" / "manual_exports"

DISEASE_TERMS = [
    '"Langerhans cell histiocytosis"', '"Langerhans-cell histiocytosis"',
    '"histiocytosis X"', '"Letterer-Siwe"', '"Hand-Schuller-Christian"',
    '"Hand Schuller Christian"', '"eosinophilic granuloma"', '"Langerhans cell granulomatosis"',
]
OCULAR_TERMS = [
    "uveal", "uvea", "choroid", "choroidal", "iris", '"ciliary body"',
    "ciliochoroidal", "intraocular", '"posterior segment"', "retina", "retinal",
    "retinochoroidopathy", "uveitis", "hyphema", "hypopyon",
    '"exudative retinal detachment"', '"serous retinal detachment"',
    '"choroidal mass"', '"choroidal infiltration"',
]
INCLUSION_FLAG_TERMS = [
    "choroid", "choroidal", "uveal", "uvea", "iris", "ciliary body",
    "ciliochoroidal", "intraocular", "posterior segment", "retina", "retinal",
    "retinochoroidopathy", "uveitis", "hyphema", "hypopyon",
    "exudative retinal detachment", "serous retinal detachment",
]
EXCLUSION_FLAG_TERMS = [
    "orbit", "orbital", "eyelid", "conjunctiva", "conjunctival", "lacrimal",
    "periorbital", "choroid plexus", "choroid-plexus",
]
SEED_TITLES = [
    "Choroidal Neovascular Membrane Formation and Retinochoroidopathy in a Patient with Systemic Langerhans Cell Histiocytosis: A Case Report and Review of the Literature",
    "Langerhans Cell Histiocytosis of the Uvea with a Ciliochoroidal Mass: A Case Report of Management with Systemic Therapy",
]
USER_AGENT = "lch-uveal-systematic-review/1.0 (mailto:example@example.com)"


def api_get_json(url: str, *, timeout: int = 40, retries: int = 2) -> dict[str, Any]:
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            print(f"WARN JSON request failed {e.code}: {url}")
            return {}
        except Exception as e:
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            print(f"WARN JSON request failed {e}: {url}")
            return {}
    return {}


def api_get_text(url: str, *, timeout: int = 40, retries: int = 2) -> str:
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            print(f"WARN text request failed {e}: {url}")
            return ""
    return ""


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = " ".join(clean_text(v) for v in value)
    return re.sub(r"\s+", " ", html.unescape(str(value))).strip()


def normalize_doi(doi: str) -> str:
    doi = clean_text(doi).lower()
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", doi)
    return doi.strip().strip(" .")


def normalize_title(title: str) -> str:
    title = clean_text(title).lower()
    title = re.sub(r"<[^>]+>", " ", title)
    title = re.sub(r"[^a-z0-9]+", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def extract_year(*values: Any) -> str:
    for value in values:
        m = re.search(r"(19|20)\d{2}", clean_text(value))
        if m:
            return m.group(0)
    return ""


def disease_query_plain() -> str:
    return " OR ".join(DISEASE_TERMS)


def ocular_query_plain() -> str:
    return " OR ".join(OCULAR_TERMS)


def combined_query_plain() -> str:
    return f"({disease_query_plain()}) AND ({ocular_query_plain()})"


def pubmed_query() -> str:
    disease = " OR ".join(f"{t}[Title/Abstract]" for t in DISEASE_TERMS)
    ocular = " OR ".join(f"{t}[Title/Abstract]" for t in OCULAR_TERMS)
    return f"({disease}) AND ({ocular})"


@dataclass
class Record:
    title: str = ""
    authors: str = ""
    year: str = ""
    journal: str = ""
    doi: str = ""
    pmid: str = ""
    pmcid: str = ""
    abstract: str = ""
    url: str = ""
    source: str = ""
    source_id: str = ""
    database_origins: str = ""
    citation_context: str = "direct_search"
    matched_inclusion_terms: str = ""
    matched_exclusion_terms: str = ""
    relevance_flag: str = ""
    exclusion_flag: str = ""
    dedupe_key: str = ""
    duplicate_of: str = ""
    notes: str = ""

    def finalize(self) -> "Record":
        self.title = clean_text(self.title)
        self.authors = clean_text(self.authors)
        self.year = extract_year(self.year)
        self.journal = clean_text(self.journal)
        self.doi = normalize_doi(self.doi)
        self.pmid = clean_text(self.pmid)
        self.pmcid = clean_text(self.pmcid)
        self.abstract = clean_text(self.abstract)
        self.url = clean_text(self.url)
        self.source = clean_text(self.source)
        self.source_id = clean_text(self.source_id)
        self.database_origins = self.database_origins or self.source
        return self


def flag_record(rec: Record) -> Record:
    blob = normalize_title(" ".join([rec.title, rec.abstract, rec.journal]))
    def present(term: str) -> bool:
        norm = normalize_title(term)
        return norm in blob
    inc = [t for t in INCLUSION_FLAG_TERMS if present(t)]
    exc = [t for t in EXCLUSION_FLAG_TERMS if present(t)]
    rec.matched_inclusion_terms = "; ".join(inc)
    rec.matched_exclusion_terms = "; ".join(exc)
    rec.relevance_flag = "likely_relevant" if inc else "unclear_no_intraocular_term_in_title_abstract"
    rec.exclusion_flag = "possible_exclusion" if exc else ""
    if inc and exc:
        rec.notes = "Contains both intraocular and exclusion-location terms; needs human screening."
    elif exc and not inc:
        rec.notes = "Likely isolated orbital/adnexal/CNS-choroid-plexus result; title/abstract exclusion only."
    return rec


def fetch_pubmed() -> list[Record]:
    term = urllib.parse.quote(pubmed_query())
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmax=500&retmode=json&term={term}"
    ids = api_get_json(url).get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    xml = api_get_text("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?" + urllib.parse.urlencode({"db":"pubmed","retmode":"xml","id": ",".join(ids)}))
    records: list[Record] = []
    root = ET.fromstring(xml) if xml else ET.Element("root")
    for article in root.findall(".//PubmedArticle"):
        med = article.find("./MedlineCitation")
        art = article.find("./MedlineCitation/Article")
        if med is None or art is None:
            continue
        pmid = clean_text(med.findtext("PMID"))
        title = "".join(art.findtext("ArticleTitle") or "")
        abstract = " ".join(clean_text(x.text) for x in art.findall(".//AbstractText"))
        journal = art.findtext("./Journal/Title") or art.findtext("./Journal/ISOAbbreviation") or ""
        year = art.findtext("./Journal/JournalIssue/PubDate/Year") or art.findtext("./Journal/JournalIssue/PubDate/MedlineDate") or ""
        authors = []
        for au in art.findall("./AuthorList/Author"):
            last = au.findtext("LastName") or ""
            fore = au.findtext("ForeName") or au.findtext("Initials") or ""
            coll = au.findtext("CollectiveName") or ""
            authors.append(clean_text(coll or f"{last} {fore}"))
        doi = ""
        for aid in article.findall(".//ArticleId"):
            if aid.attrib.get("IdType") == "doi": doi = aid.text or doi
        records.append(flag_record(Record(title=title, authors="; ".join(authors), year=year, journal=journal, doi=doi, pmid=pmid, url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", source="PubMed", source_id=pmid).finalize()))
    return records


def fetch_europepmc() -> list[Record]:
    q = combined_query_plain()
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urllib.parse.urlencode({"query": q, "format":"json", "pageSize":"1000", "resultType":"core"})
    data = api_get_json(url)
    records = []
    for item in data.get("resultList", {}).get("result", []):
        authors = item.get("authorString", "")
        pmcid = item.get("pmcid", "")
        pmid = item.get("pmid", "")
        url2 = item.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("url", "") if isinstance(item.get("fullTextUrlList"), dict) else ""
        if not url2:
            url2 = f"https://europepmc.org/article/{item.get('source','')}/{item.get('id','')}"
        records.append(flag_record(Record(title=item.get("title",""), authors=authors, year=item.get("pubYear",""), journal=item.get("journalTitle",""), doi=item.get("doi",""), pmid=pmid, pmcid=pmcid, abstract=item.get("abstractText",""), url=url2, source="Europe PMC", source_id=item.get("id","")).finalize()))
    return records


def fetch_crossref() -> list[Record]:
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode({"query.bibliographic": combined_query_plain(), "rows":"200", "select":"DOI,title,author,published-print,published-online,container-title,URL,abstract"})
    data = api_get_json(url)
    records = []
    for item in data.get("message", {}).get("items", []):
        authors = []
        for au in item.get("author", []) or []:
            authors.append(clean_text(f"{au.get('family','')} {au.get('given','')}"))
        year = ""
        for key in ("published-print", "published-online", "published"):
            parts = item.get(key, {}).get("date-parts", [])
            if parts and parts[0]:
                year = str(parts[0][0]); break
        records.append(flag_record(Record(title=clean_text(item.get("title", [""])), authors="; ".join(authors), year=year, journal=clean_text(item.get("container-title", [""])), doi=item.get("DOI",""), abstract=item.get("abstract",""), url=item.get("URL",""), source="CrossRef", source_id=item.get("DOI","")).finalize()))
    return records


def fetch_openalex_search() -> list[Record]:
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode({"search": combined_query_plain(), "per-page":"200", "mailto":"example@example.com"})
    data = api_get_json(url)
    return [openalex_to_record(item, "OpenAlex", "direct_search") for item in data.get("results", [])]


def inverted_index_to_text(idx: Any) -> str:
    if not isinstance(idx, dict):
        return ""
    words = []
    for word, positions in idx.items():
        for pos in positions:
            words.append((pos, word))
    return " ".join(word for _, word in sorted(words))


def openalex_to_record(item: dict[str, Any], source: str, context: str) -> Record:
    authors = []
    for au in item.get("authorships", []) or []:
        if au.get("author", {}).get("display_name"):
            authors.append(au["author"]["display_name"])
    doi = item.get("doi") or ""
    ids = item.get("ids", {}) or {}
    doi = doi or ids.get("doi", "")
    pmid = ids.get("pmid", "").rstrip("/").split("/")[-1] if ids.get("pmid") else ""
    journal = (item.get("primary_location") or {}).get("source", {}) or {}
    rec = Record(title=item.get("title", ""), authors="; ".join(authors), year=str(item.get("publication_year") or ""), journal=journal.get("display_name", ""), doi=doi, pmid=pmid, abstract=inverted_index_to_text(item.get("abstract_inverted_index")), url=item.get("id", ""), source=source, source_id=item.get("id", ""), citation_context=context).finalize()
    return flag_record(rec)


def semantic_to_record(item: dict[str, Any], context: str = "direct_search") -> Record:
    ext = item.get("externalIds", {}) or {}
    authors = "; ".join(a.get("name", "") for a in item.get("authors", []) or [])
    url = item.get("url") or (f"https://www.semanticscholar.org/paper/{item.get('paperId')}" if item.get("paperId") else "")
    rec = Record(title=item.get("title", ""), authors=authors, year=str(item.get("year") or ""), journal=item.get("venue", ""), doi=ext.get("DOI", ""), pmid=ext.get("PubMed", ""), pmcid=ext.get("PubMedCentral", ""), abstract=item.get("abstract", ""), url=url, source="Semantic Scholar", source_id=item.get("paperId", ""), citation_context=context).finalize()
    return flag_record(rec)


def fetch_semantic_search() -> list[Record]:
    url = "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode({"query": combined_query_plain(), "limit":"100", "fields":"title,abstract,year,authors,externalIds,url,venue,publicationDate"})
    data = api_get_json(url)
    return [semantic_to_record(item) for item in data.get("data", [])]


def openalex_search_title(title: str) -> dict[str, Any] | None:
    data = api_get_json("https://api.openalex.org/works?" + urllib.parse.urlencode({"search": title, "per-page":"5", "mailto":"example@example.com"}))
    norm = normalize_title(title)
    best = None; best_score = 0.0
    for item in data.get("results", []):
        score = SequenceMatcher(None, norm, normalize_title(item.get("title", ""))).ratio()
        if score > best_score:
            best, best_score = item, score
    return best if best_score >= 0.75 else None


def fetch_openalex_by_id(openalex_url: str) -> dict[str, Any] | None:
    if not openalex_url:
        return None
    return api_get_json(openalex_url + "?" + urllib.parse.urlencode({"mailto":"example@example.com"}))


def fetch_citation_chasing_openalex(limit_cited_by: int = 200) -> list[Record]:
    records = []
    seen_ids: set[str] = set()
    for title in SEED_TITLES:
        seed = openalex_search_title(title)
        if not seed:
            print(f"WARN OpenAlex seed not found: {title}")
            continue
        seed_id = seed.get("id", "")
        records.append(openalex_to_record(seed, "OpenAlex", "seed_record"))
        seen_ids.add(seed_id)
        for ref_id in seed.get("referenced_works", []) or []:
            if ref_id in seen_ids:
                continue
            seen_ids.add(ref_id)
            item = fetch_openalex_by_id(ref_id)
            if item:
                records.append(openalex_to_record(item, "OpenAlex", f"backward_from_seed:{seed_id}"))
        cited_url = seed.get("cited_by_api_url")
        if cited_url:
            data = api_get_json(cited_url + "&" + urllib.parse.urlencode({"per-page": str(min(limit_cited_by, 200)), "mailto":"example@example.com"}))
            for item in data.get("results", []):
                if item.get("id") not in seen_ids:
                    seen_ids.add(item.get("id", ""))
                    records.append(openalex_to_record(item, "OpenAlex", f"forward_from_seed:{seed_id}"))
    return records


def fetch_semantic_title(title: str) -> dict[str, Any] | None:
    data = api_get_json("https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode({"query": title, "limit":"5", "fields":"title,abstract,year,authors,externalIds,url,venue,references,citations"}))
    norm = normalize_title(title); best = None; best_score = 0
    for item in data.get("data", []):
        score = SequenceMatcher(None, norm, normalize_title(item.get("title", ""))).ratio()
        if score > best_score:
            best, best_score = item, score
    return best if best_score >= 0.75 else None


def fetch_citation_chasing_semantic() -> list[Record]:
    records = []
    for title in SEED_TITLES:
        seed = fetch_semantic_title(title)
        if not seed:
            print(f"WARN Semantic Scholar seed not found or API unavailable: {title}")
            continue
        records.append(semantic_to_record(seed, "seed_record"))
        for ref in seed.get("references", []) or []:
            if ref:
                records.append(semantic_to_record(ref, f"backward_from_seed:{seed.get('paperId','')}"))
        for cit in seed.get("citations", []) or []:
            if cit:
                records.append(semantic_to_record(cit, f"forward_from_seed:{seed.get('paperId','')}"))
    return records


def parse_ris(path: Path, source: str) -> list[Record]:
    records = []
    current: dict[str, list[str]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if len(line) < 6 or line[2:6] != "  - ":
            continue
        tag, value = line[:2], line[6:].strip()
        if tag == "TY":
            current = {tag: [value]}
        elif tag == "ER":
            records.append(ris_record_to_record(current, source, path.name))
            current = {}
        else:
            current.setdefault(tag, []).append(value)
    return [flag_record(r.finalize()) for r in records if r.title]


def ris_record_to_record(r: dict[str, list[str]], source: str, filename: str) -> Record:
    return Record(title=clean_text(r.get("TI", r.get("T1", [""]))), authors="; ".join(r.get("AU", [])), year=extract_year(*(r.get("PY", []) + r.get("Y1", []))), journal=clean_text(r.get("JO", r.get("JF", r.get("T2", [""])))), doi=clean_text(r.get("DO", [""])), pmid=clean_text(r.get("PM", [""])), abstract=clean_text(r.get("AB", [""])), url=clean_text(r.get("UR", [""])), source=source, source_id=filename, citation_context="manual_export")


def parse_bibtex(path: Path, source: str) -> list[Record]:
    text = path.read_text(encoding="utf-8", errors="replace")
    entries = re.split(r"\n@", "\n" + text)
    records = []
    for entry in entries:
        if not entry.strip():
            continue
        fields = {m.group(1).lower(): m.group(2).strip().strip("{}\"") for m in re.finditer(r"(\w+)\s*=\s*[\{\"](.*?)[\}\"]\s*,?\n", entry, re.S)}
        rec = Record(title=fields.get("title", ""), authors=fields.get("author", "").replace(" and ", "; "), year=fields.get("year", ""), journal=fields.get("journal", fields.get("booktitle", "")), doi=fields.get("doi", ""), pmid=fields.get("pmid", ""), abstract=fields.get("abstract", ""), url=fields.get("url", ""), source=source, source_id=path.name, citation_context="manual_export").finalize()
        if rec.title:
            records.append(flag_record(rec))
    return records


def parse_csv(path: Path, source: str) -> list[Record]:
    records = []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lower = {k.lower().strip(): v for k, v in row.items() if k}
            def pick(*keys: str) -> str:
                for key in keys:
                    if lower.get(key): return lower[key]
                return ""
            rec = Record(title=pick("title", "article title", "document title"), authors=pick("authors", "author", "au"), year=pick("year", "publication year"), journal=pick("source title", "journal", "publication name", "journal title"), doi=pick("doi"), pmid=pick("pmid", "pubmed id"), abstract=pick("abstract", "description"), url=pick("url", "link"), source=source, source_id=path.name, citation_context="manual_export").finalize()
            if rec.title:
                records.append(flag_record(rec))
    return records


def import_manual_exports() -> list[Record]:
    records = []
    if not MANUAL.exists():
        return records
    for path in MANUAL.iterdir():
        if path.is_dir():
            continue
        source = path.stem.split("_")[0].replace("-", " ").title()
        if path.suffix.lower() == ".ris":
            records.extend(parse_ris(path, source))
        elif path.suffix.lower() in (".bib", ".bibtex"):
            records.extend(parse_bibtex(path, source))
        elif path.suffix.lower() == ".csv":
            records.extend(parse_csv(path, source))
    return records


def record_key(rec: Record) -> str:
    if rec.doi: return "doi:" + rec.doi
    if rec.pmid: return "pmid:" + rec.pmid
    return "titleyear:" + normalize_title(rec.title)[:120] + ":" + rec.year


def dedupe(records: list[Record]) -> tuple[list[Record], list[Record]]:
    unique: list[Record] = []
    dupes: list[Record] = []
    key_index: dict[str, Record] = {}
    for rec in records:
        rec.dedupe_key = record_key(rec)
        exact_key = rec.dedupe_key
        master = key_index.get(exact_key)
        if master is None and not (rec.doi or rec.pmid):
            nt = normalize_title(rec.title)
            for existing in unique:
                if rec.year and existing.year and rec.year != existing.year:
                    continue
                if SequenceMatcher(None, nt, normalize_title(existing.title)).ratio() >= 0.92:
                    master = existing
                    break
        if master:
            origins = set(filter(None, master.database_origins.split("; "))) | {rec.source}
            master.database_origins = "; ".join(sorted(origins))
            if not master.abstract and rec.abstract: master.abstract = rec.abstract
            if not master.doi and rec.doi: master.doi = rec.doi
            if not master.pmid and rec.pmid: master.pmid = rec.pmid
            if not master.url and rec.url: master.url = rec.url
            master.citation_context = "; ".join(sorted(set(filter(None, master.citation_context.split("; ") + [rec.citation_context]))))
            rec.duplicate_of = master.dedupe_key
            dupes.append(rec)
        else:
            unique.append(rec)
            key_index[exact_key] = rec
    return unique, dupes


def write_csv(path: Path, records: Iterable[Record]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(asdict(Record()).keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for rec in records:
            writer.writerow(asdict(rec))


def escape_bib(s: str) -> str:
    return s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def write_bibtex(path: Path, records: Iterable[Record]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for i, rec in enumerate(records, 1):
            key_author = re.sub(r"[^A-Za-z0-9]", "", (rec.authors.split(";")[0] or "LCH"))[:20] or "LCH"
            key = f"{key_author}{rec.year or 'noyear'}_{i}"
            f.write(f"@article{{{key},\n")
            for field, value in [("title", rec.title), ("author", rec.authors.replace("; ", " and ")), ("year", rec.year), ("journal", rec.journal), ("doi", rec.doi), ("pmid", rec.pmid), ("url", rec.url), ("abstract", rec.abstract)]:
                if value:
                    f.write(f"  {field} = {{{escape_bib(value)}}},\n")
            f.write("}\n\n")


def write_ris(path: Path, records: Iterable[Record]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write("TY  - JOUR\n")
            if rec.title: f.write(f"TI  - {rec.title}\n")
            for au in filter(None, [a.strip() for a in rec.authors.split(";")]): f.write(f"AU  - {au}\n")
            if rec.year: f.write(f"PY  - {rec.year}\n")
            if rec.journal: f.write(f"JO  - {rec.journal}\n")
            if rec.doi: f.write(f"DO  - {rec.doi}\n")
            if rec.pmid: f.write(f"PM  - {rec.pmid}\n")
            if rec.abstract: f.write(f"AB  - {rec.abstract}\n")
            if rec.url: f.write(f"UR  - {rec.url}\n")
            f.write("ER  - \n\n")


def write_prisma_counts(raw: list[Record], deduped: list[Record], candidates: list[Record], excluded: list[Record], fulltext: list[Record], dupes: list[Record]) -> None:
    origins: dict[str, int] = {}
    for r in raw:
        origins[r.source] = origins.get(r.source, 0) + 1
    lines = ["# PRISMA-ready search counts", "", "Generated by `scripts/lch_uveal_search.py`.", "", "## Identification", ""]
    lines += [f"- Records identified from {src}: {n}" for src, n in sorted(origins.items())]
    lines += [f"- Total raw records: {len(raw)}", f"- Duplicate records removed automatically: {len(dupes)}", f"- Records after deduplication: {len(deduped)}", "", "## Screening flags", "", f"- Records with at least one intraocular/uveal relevance term: {len(candidates)}", f"- Records flagged as likely title/abstract exclusions because they had exclusion-location terms and no intraocular relevance term: {len(excluded)}", f"- Records retained for human full-text screening by automated rules: {len(fulltext)}", "", "## Notes", "", "These counts are automation outputs for PRISMA bookkeeping. Human reviewers should finalize title/abstract and full-text exclusions with reasons."]
    (RESULTS / "prisma_counts.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_strategy() -> None:
    text = f"""# Search strategy: uveal/choroidal/intraocular Langerhans cell histiocytosis

## Review question
Case report plus updated systematic review of true uveal/choroidal/intraocular involvement in Langerhans cell histiocytosis (LCH), including historical disease names. Isolated orbital, eyelid, conjunctival, lacrimal, periorbital, and CNS choroid plexus records are excluded unless true intraocular/uveal involvement is present.

## Core concepts
- Disease terms: {', '.join(DISEASE_TERMS)}
- Ocular/intraocular terms: {', '.join(OCULAR_TERMS)}
- Automated relevance flag terms: {', '.join(INCLUSION_FLAG_TERMS)}
- Automated possible-exclusion terms: {', '.join(EXCLUSION_FLAG_TERMS)}

## PubMed/MEDLINE API search
Run by `scripts/lch_uveal_search.py` using NCBI E-utilities.

```text
{pubmed_query()}
```

## Europe PMC API search
Run by `scripts/lch_uveal_search.py` using Europe PMC REST.

```text
{combined_query_plain()}
```

## CrossRef supplementary metadata search
CrossRef is used as a supplementary metadata source, not as a replacement for Embase/Scopus/Web of Science.

```text
{combined_query_plain()}
```

## OpenAlex supplementary metadata and citation-discovery search
OpenAlex is used for supplementary metadata and backward/forward citation chasing from the two seed articles.

```text
{combined_query_plain()}
```

Seed articles for citation chasing:
1. Thanos et al. 2012, "{SEED_TITLES[0]}"
2. Ghassemi et al. 2023, "{SEED_TITLES[1]}"

## Semantic Scholar supplementary metadata and citation-discovery search
Semantic Scholar is used for supplementary metadata and citation discovery where the public API is available.

```text
{combined_query_plain()}
```

## Embase manual search string
Run in Embase.com or Ovid Embase. Export all records as RIS, CSV, or BibTeX to `data/manual_exports/` with a filename beginning `embase_`.

### Embase.com example
```text
('langerhans cell histiocytosis':ti,ab,kw OR 'langerhans-cell histiocytosis':ti,ab,kw OR 'histiocytosis x':ti,ab,kw OR 'letterer siwe':ti,ab,kw OR 'hand schuller christian':ti,ab,kw OR 'hand-schuller-christian':ti,ab,kw OR 'eosinophilic granuloma':ti,ab,kw OR 'langerhans cell granulomatosis':ti,ab,kw)
AND
(uveal:ti,ab,kw OR uvea:ti,ab,kw OR choroid:ti,ab,kw OR choroidal:ti,ab,kw OR iris:ti,ab,kw OR 'ciliary body':ti,ab,kw OR ciliochoroidal:ti,ab,kw OR intraocular:ti,ab,kw OR 'posterior segment':ti,ab,kw OR retina:ti,ab,kw OR retinal:ti,ab,kw OR retinochoroidopathy:ti,ab,kw OR uveitis:ti,ab,kw OR hyphema:ti,ab,kw OR hypopyon:ti,ab,kw OR 'exudative retinal detachment':ti,ab,kw OR 'serous retinal detachment':ti,ab,kw OR 'choroidal mass':ti,ab,kw OR 'choroidal infiltration':ti,ab,kw)
```

### Ovid Embase example
```text
((langerhans cell histiocytosis or langerhans-cell histiocytosis or histiocytosis x or letterer siwe or hand schuller christian or hand-schuller-christian or eosinophilic granuloma or langerhans cell granulomatosis).ti,ab,kw.)
AND
((uveal or uvea or choroid or choroidal or iris or ciliary body or ciliochoroidal or intraocular or posterior segment or retina or retinal or retinochoroidopathy or uveitis or hyphema or hypopyon or exudative retinal detachment or serous retinal detachment or choroidal mass or choroidal infiltration).ti,ab,kw.)
```

## Scopus manual search string
Run in Scopus Advanced Search. Export all records as RIS, CSV, or BibTeX to `data/manual_exports/` with a filename beginning `scopus_`.

```text
TITLE-ABS-KEY("Langerhans cell histiocytosis" OR "Langerhans-cell histiocytosis" OR "histiocytosis X" OR "Letterer-Siwe" OR "Hand-Schuller-Christian" OR "Hand Schuller Christian" OR "eosinophilic granuloma" OR "Langerhans cell granulomatosis")
AND
TITLE-ABS-KEY(uveal OR uvea OR choroid OR choroidal OR iris OR "ciliary body" OR ciliochoroidal OR intraocular OR "posterior segment" OR retina OR retinal OR retinochoroidopathy OR uveitis OR hyphema OR hypopyon OR "exudative retinal detachment" OR "serous retinal detachment" OR "choroidal mass" OR "choroidal infiltration")
```

## Web of Science Core Collection manual search string
Run in Web of Science Core Collection Advanced Search. Export all records as RIS, CSV, or BibTeX to `data/manual_exports/` with a filename beginning `wos_`.

```text
TS=("Langerhans cell histiocytosis" OR "Langerhans-cell histiocytosis" OR "histiocytosis X" OR "Letterer-Siwe" OR "Hand-Schuller-Christian" OR "Hand Schuller Christian" OR "eosinophilic granuloma" OR "Langerhans cell granulomatosis")
AND
TS=(uveal OR uvea OR choroid OR choroidal OR iris OR "ciliary body" OR ciliochoroidal OR intraocular OR "posterior segment" OR retina OR retinal OR retinochoroidopathy OR uveitis OR hyphema OR hypopyon OR "exudative retinal detachment" OR "serous retinal detachment" OR "choroidal mass" OR "choroidal infiltration")
```

## Google Scholar manual search
Google Scholar does not provide a reliable public API for systematic export. Run several smaller searches, screen the first reproducible result window used by the review team (for example first 200 sorted by relevance and first 200 sorted by date if feasible), and export citations manually or via a citation manager to `data/manual_exports/`.

Suggested queries:
```text
"Langerhans cell histiocytosis" choroidal OR uveal OR intraocular
"histiocytosis X" choroid OR choroidal OR uvea OR intraocular
"Hand-Schuller-Christian" choroid OR uvea OR retina
"Letterer-Siwe" choroid OR uvea OR retina
"eosinophilic granuloma" choroid OR uvea OR intraocular
```

## Manual export/import workflow
1. Export Embase, Scopus, Web of Science, and Google Scholar records in RIS, CSV, or BibTeX format.
2. Place files in `data/manual_exports/` with source-identifying prefixes such as `embase_2026-05-30.ris`, `scopus_2026-05-30.csv`, `wos_2026-05-30.bib`, or `googlescholar_2026-05-30.ris`.
3. Re-run:

```bash
python scripts/lch_uveal_search.py
```

The script merges manual exports with API-derived records, deduplicates by DOI, PMID, normalized title similarity, and year, and regenerates all CSV/RIS/BibTeX outputs plus PRISMA counts.
"""
    (RESULTS / "search_strategy.md").write_text(text, encoding="utf-8")


def write_table_template() -> None:
    columns = ["Author/year", "age", "sex", "known LCH before ocular finding", "ocular presentation", "exact site", "mass vs diffuse infiltration", "laterality", "systemic involvement", "biopsy site", "histopathology/IHC", "imaging", "treatment", "ocular response", "final visual acuity", "systemic outcome", "follow-up duration"]
    with (RESULTS / "final_table_template.csv").open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(columns)
    md = "# Final evidence table template\n\n| " + " | ".join(columns) + " |\n|" + "|".join(["---"] * len(columns)) + "|\n"
    (RESULTS / "final_table_template.md").write_text(md, encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    RESULTS.mkdir(exist_ok=True)
    raw: list[Record] = []
    sources = [
        ("PubMed", fetch_pubmed),
        ("Europe PMC", fetch_europepmc),
        ("CrossRef", fetch_crossref),
        ("OpenAlex", fetch_openalex_search),
        ("Semantic Scholar", fetch_semantic_search),
        ("OpenAlex citation chasing", fetch_citation_chasing_openalex),
        ("Semantic Scholar citation chasing", fetch_citation_chasing_semantic),
        ("manual exports", import_manual_exports),
    ]
    for name, func in sources:
        if args.no_api and name != "manual exports":
            continue
        print(f"Fetching {name}...")
        try:
            got = func()
            print(f"  {len(got)} records")
            raw.extend(got)
            time.sleep(0.2)
        except Exception as e:
            print(f"WARN source failed {name}: {e}")
    raw = [flag_record(r.finalize()) for r in raw if r.title]
    deduped, dupes = dedupe(raw)
    candidates = [r for r in deduped if r.matched_inclusion_terms]
    excluded = [r for r in deduped if r.matched_exclusion_terms and not r.matched_inclusion_terms]
    fulltext = [r for r in deduped if r.matched_inclusion_terms]

    write_csv(RESULTS / "search_results_raw.csv", raw)
    write_csv(RESULTS / "search_results_deduplicated.csv", deduped)
    write_csv(RESULTS / "screening_candidates.csv", candidates)
    write_csv(RESULTS / "excluded_by_title_abstract.csv", excluded)
    write_csv(RESULTS / "included_for_full_text_screening.csv", fulltext)
    write_csv(RESULTS / "duplicates_removed.csv", dupes)
    write_bibtex(RESULTS / "search_results_deduplicated.bib", deduped)
    write_ris(RESULTS / "search_results_deduplicated.ris", deduped)
    write_prisma_counts(raw, deduped, candidates, excluded, fulltext, dupes)
    write_strategy()
    write_table_template()
    print(f"Wrote outputs to {RESULTS}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--no-api", action="store_true", help="Only import manual exports and regenerate outputs.")
    run(p.parse_args())


if __name__ == "__main__":
    main()
