# NYU Course Searcher

NYU Course Searcher is a local Streamlit app that helps students find NYU courses using semantic search.
Instead of only matching exact keywords, it compares meaning, so you can type natural phrases like
"intro to machine learning" or "creative writing workshop" and get relevant courses.

## What This App Does

- Scrapes course data from the NYU bulletin.
- Stores parsed course information in a local SQLite database.
- Builds text embeddings for each course using a Hugging Face model.
- Uses a FAISS index for fast semantic retrieval.
- Provides a simple web UI for searching, saving courses, and adding personal notes.

## Main Pages

- Search: Find courses semantically, save/unsave, and leave thumbs feedback.
- My Courses: View saved courses, filter them, and update personal notes.
- Admin Data: Run pipeline steps (scrape, embed, index) and view recent run summaries.

## Typical Flow

1. Run the pipeline scripts to prepare data.
2. Start the Streamlit app.
3. Sign in, search for courses, and save the ones you like.

## Local-Only Design

This app is intended for local use. Data, embeddings, and indexes are stored in local project folders.
No external backend service is required.
