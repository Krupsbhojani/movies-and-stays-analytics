# DSA508 Big Data Platforms & Analytics: Problems 1 and 2

**Live dashboard:** https://rental-market-board.streamlit.app
```
problem1/
  problem1_mflix_analysis.ipynb    EDA, trends, text analysis, topic modeling (with outputs)
  problem1_mflix_analysis.html     same notebook as a read-only page
  requirements.txt
problem2/
  load_to_azure.py                 loads sample_airbnb into Azure Cosmos DB for MongoDB
  app.py                           Streamlit entry point (run this); switches between the two pages
  landscape.py                     Board page: the whole dashboard, including the 3D hex map, on one 16:9 screen
  detailed.py                      Detailed page: scrolling board with market pulse tiles, 3D map and value picks
  common.py                        shared theme, filters and MongoDB queries
  .streamlit/config.toml           light theme used by the board
  NARRATIVE.md                     purpose, analytical value, decision support
  .env.example                     connection settings template
  requirements.txt
```

