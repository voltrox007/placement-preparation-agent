# Knowledge and retrieval

## Storage split

RAG: approved educational passages and resource descriptions. SQLite: student facts, role requirements, plans, scores, attempts, provenance. Private catalog: answer keys/rubrics, excluded from tutoring retrieval. LLM: wording, evidence interpretation, bounded feedback—not authoritative student facts or unsupported technical claims.

## Corpus

Start with approximately 20–40 reviewed sources, 15–25 skills, 40–60 reviewed assessment questions, and 10–15 activities/exercises. Use original notes or permitted material; record permitted use and link rather than copying commercial courses. These are implementation targets, not content that already exists.

## Ingestion

Register source → parse headings/pages → remove boilerplate → topic-aware chunk → hash → embed changed chunks → candidate index version → retrieval checks → activate → retire obsolete chunks. Failed ingestion must not replace the active corpus.

Initial chunks: roughly 400–700 tokens with modest overlap; preserve complete small code examples and contextual warnings. Tune with evaluation.

Metadata: chunk/document/corpus IDs and versions; title/URL/heading/page; skills; language; technology version; reviewed_at; active status; hash; access classification; embedding version/dimensions.

## Runtime

Application constructs one authorized query, filters active approved content, runs hybrid keyword/vector retrieval, deduplicates, and supplies approximately 4–6 passages in one Foundry request. No agentic query expansion or repeated retrieval loop by default. Query embedding is separately metered and cached where safe.

The model returns citation IDs only. Code resolves trusted titles/URLs and rejects absent citations. A valid citation ID is not proof of claim support: the evaluation dataset checks that separately. No relevant evidence means an explicit limitation; never invented sources.

Cache by normalized query/filter/corpus/embedding version. Re-embed only changed chunks. For learning resource recommendations, deterministic catalog lookup is sufficient and avoids AI calls.

## Freshness

Tag version-specific material, review changing technologies more frequently, exclude retired content, and make conflicts explicit. Keep student/private repository data out of the educational index.

## Technology decision

Azure AI Search gives explicit, testable keyword/vector retrieval. Semantic ranking is optional after measured benefit. Foundry IQ is deferred because the MVP has one curated corpus and no need for multi-source agentic retrieval. A local retrieval contingency requires a documented plan change; it is not silently substituted for the reference architecture.
