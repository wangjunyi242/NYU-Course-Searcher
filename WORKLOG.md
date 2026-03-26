2026-02-12T00:00:00+00:00 Added 01_scrape_courses CLI wrapper; now appends scrape counts to WORKLOG at runtime.
2026-02-12T16:31:29.501121+00:00 scrape_all_courses subjects=657 failed=0 parsed=0 upserted=0 db_total=0
2026-02-12T00:00:00+00:00 Updated subject parser to handle courseblock detail spans and numeric subject codes.
2026-02-12T16:37:36.430433+00:00 scrape_all_courses subjects=5 failed=0 parsed=86 upserted=86 db_total=86
2026-02-12T16:38:18.106563+00:00 scrape_all_courses subjects=5 failed=0 parsed=86 upserted=86 db_total=86
2026-02-12T16:44:54.846197+00:00 scrape_all_courses subjects=657 failed=0 parsed=17122 upserted=17122 db_total=17122
2026-02-12T17:08:00.960797+00:00 build_embeddings count=10 dim=768 model=nomic-ai/nomic-embed-text-v1.5 elapsed_sec=107.2
2026-02-12T17:40:31.567309+00:00 build_embeddings count=17122 dim=768 model=nomic-ai/nomic-embed-text-v1.5 elapsed_sec=646.4
2026-02-12T18:36:17.285597+00:00 build_faiss count=17122 dim=768 elapsed_sec=0.3
