# Search strategy: uveal/choroidal/intraocular Langerhans cell histiocytosis

## Review question
Case report plus updated systematic review of true uveal/choroidal/intraocular involvement in Langerhans cell histiocytosis (LCH), including historical disease names. Isolated orbital, eyelid, conjunctival, lacrimal, periorbital, and CNS choroid plexus records are excluded unless true intraocular/uveal involvement is present.

## Core concepts
- Disease terms: "Langerhans cell histiocytosis", "Langerhans-cell histiocytosis", "histiocytosis X", "Letterer-Siwe", "Hand-Schuller-Christian", "Hand Schuller Christian", "eosinophilic granuloma", "Langerhans cell granulomatosis"
- Ocular/intraocular terms: uveal, uvea, choroid, choroidal, iris, "ciliary body", ciliochoroidal, intraocular, "posterior segment", retina, retinal, retinochoroidopathy, uveitis, hyphema, hypopyon, "exudative retinal detachment", "serous retinal detachment", "choroidal mass", "choroidal infiltration"
- Automated relevance flag terms: choroid, choroidal, uveal, uvea, iris, ciliary body, ciliochoroidal, intraocular, posterior segment, retina, retinal, retinochoroidopathy, uveitis, hyphema, hypopyon, exudative retinal detachment, serous retinal detachment
- Automated possible-exclusion terms: orbit, orbital, eyelid, conjunctiva, conjunctival, lacrimal, periorbital, choroid plexus, choroid-plexus

## PubMed/MEDLINE API search
Run by `scripts/lch_uveal_search.py` using NCBI E-utilities.

```text
("Langerhans cell histiocytosis"[Title/Abstract] OR "Langerhans-cell histiocytosis"[Title/Abstract] OR "histiocytosis X"[Title/Abstract] OR "Letterer-Siwe"[Title/Abstract] OR "Hand-Schuller-Christian"[Title/Abstract] OR "Hand Schuller Christian"[Title/Abstract] OR "eosinophilic granuloma"[Title/Abstract] OR "Langerhans cell granulomatosis"[Title/Abstract]) AND (uveal[Title/Abstract] OR uvea[Title/Abstract] OR choroid[Title/Abstract] OR choroidal[Title/Abstract] OR iris[Title/Abstract] OR "ciliary body"[Title/Abstract] OR ciliochoroidal[Title/Abstract] OR intraocular[Title/Abstract] OR "posterior segment"[Title/Abstract] OR retina[Title/Abstract] OR retinal[Title/Abstract] OR retinochoroidopathy[Title/Abstract] OR uveitis[Title/Abstract] OR hyphema[Title/Abstract] OR hypopyon[Title/Abstract] OR "exudative retinal detachment"[Title/Abstract] OR "serous retinal detachment"[Title/Abstract] OR "choroidal mass"[Title/Abstract] OR "choroidal infiltration"[Title/Abstract])
```

## Europe PMC API search
Run by `scripts/lch_uveal_search.py` using Europe PMC REST.

```text
("Langerhans cell histiocytosis" OR "Langerhans-cell histiocytosis" OR "histiocytosis X" OR "Letterer-Siwe" OR "Hand-Schuller-Christian" OR "Hand Schuller Christian" OR "eosinophilic granuloma" OR "Langerhans cell granulomatosis") AND (uveal OR uvea OR choroid OR choroidal OR iris OR "ciliary body" OR ciliochoroidal OR intraocular OR "posterior segment" OR retina OR retinal OR retinochoroidopathy OR uveitis OR hyphema OR hypopyon OR "exudative retinal detachment" OR "serous retinal detachment" OR "choroidal mass" OR "choroidal infiltration")
```

## CrossRef supplementary metadata search
CrossRef is used as a supplementary metadata source, not as a replacement for Embase/Scopus/Web of Science.

```text
("Langerhans cell histiocytosis" OR "Langerhans-cell histiocytosis" OR "histiocytosis X" OR "Letterer-Siwe" OR "Hand-Schuller-Christian" OR "Hand Schuller Christian" OR "eosinophilic granuloma" OR "Langerhans cell granulomatosis") AND (uveal OR uvea OR choroid OR choroidal OR iris OR "ciliary body" OR ciliochoroidal OR intraocular OR "posterior segment" OR retina OR retinal OR retinochoroidopathy OR uveitis OR hyphema OR hypopyon OR "exudative retinal detachment" OR "serous retinal detachment" OR "choroidal mass" OR "choroidal infiltration")
```

## OpenAlex supplementary metadata and citation-discovery search
OpenAlex is used for supplementary metadata and backward/forward citation chasing from the two seed articles.

```text
("Langerhans cell histiocytosis" OR "Langerhans-cell histiocytosis" OR "histiocytosis X" OR "Letterer-Siwe" OR "Hand-Schuller-Christian" OR "Hand Schuller Christian" OR "eosinophilic granuloma" OR "Langerhans cell granulomatosis") AND (uveal OR uvea OR choroid OR choroidal OR iris OR "ciliary body" OR ciliochoroidal OR intraocular OR "posterior segment" OR retina OR retinal OR retinochoroidopathy OR uveitis OR hyphema OR hypopyon OR "exudative retinal detachment" OR "serous retinal detachment" OR "choroidal mass" OR "choroidal infiltration")
```

Seed articles for citation chasing:
1. Thanos et al. 2012, "Choroidal Neovascular Membrane Formation and Retinochoroidopathy in a Patient with Systemic Langerhans Cell Histiocytosis: A Case Report and Review of the Literature"
2. Ghassemi et al. 2023, "Langerhans Cell Histiocytosis of the Uvea with a Ciliochoroidal Mass: A Case Report of Management with Systemic Therapy"

## Semantic Scholar supplementary metadata and citation-discovery search
Semantic Scholar is used for supplementary metadata and citation discovery where the public API is available.

```text
("Langerhans cell histiocytosis" OR "Langerhans-cell histiocytosis" OR "histiocytosis X" OR "Letterer-Siwe" OR "Hand-Schuller-Christian" OR "Hand Schuller Christian" OR "eosinophilic granuloma" OR "Langerhans cell granulomatosis") AND (uveal OR uvea OR choroid OR choroidal OR iris OR "ciliary body" OR ciliochoroidal OR intraocular OR "posterior segment" OR retina OR retinal OR retinochoroidopathy OR uveitis OR hyphema OR hypopyon OR "exudative retinal detachment" OR "serous retinal detachment" OR "choroidal mass" OR "choroidal infiltration")
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
