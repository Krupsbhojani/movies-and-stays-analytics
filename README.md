# DSA508 Big Data Platforms & Analytics: Problems 1 and 2

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

## Step 1: MongoDB Atlas with the sample data (Problem 1 source)

1. Sign up at mongodb.com/cloud/atlas/register and create a free **M0** cluster (any region).
2. **Database Access**: add a database user with a password.
3. **Network Access**: add your current IP address. Use 0.0.0.0/0 only for testing.
4. On the cluster card, open the **...** menu and choose **Load Sample Dataset**. It takes a few minutes and creates `sample_mflix`, `sample_airbnb` and others.
5. Choose **Connect > Drivers > Python** and copy the connection string. It looks like `mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/`.

## Step 2: Run Problem 1

```bash
cd problem1
pip install -r requirements.txt
export MONGO_URI="mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/"   # Windows: set MONGO_URI=...
jupyter notebook problem1_mflix_analysis.ipynb
```
Run all cells (about one minute). The saved outputs came from a slightly older copy of `sample_mflix`, so your counts may differ a little from the ones quoted in the text, but the patterns are the same. Re-read the numbers in the markdown cells against your own outputs before submitting.

## Step 3: Azure Cosmos DB for MongoDB (Problem 2 target)

The **vCore** option with the free tier is the easiest choice: it has no request-unit throttling and costs nothing. Newer portal versions may list it as **Azure DocumentDB**.

1. In the Azure portal (an Azure for Students subscription works), go to **Create a resource > Azure Cosmos DB > Azure Cosmos DB for MongoDB > vCore cluster**.
2. Tick **Free tier**, choose a region, and set an admin username and password.
3. **Networking**: choose public access, then **Add current client IP**.
4. After deployment, open **Settings > Connection strings**, copy the string, and fill in your username and password.

If you use the **RU-based** account type instead, enable the free tier (1000 RU/s) and copy the primary connection string from **Settings > Connection String**. The loader backs off automatically when it gets throttled, but pass `--review-cap 30` to keep the load to a few minutes.

## Step 4: Load the data and run the dashboard

```bash
cd problem2
pip install -r requirements.txt
cp .env.example .env            # then paste your Azure connection string into MONGO_URI
python load_to_azure.py --source "mongodb+srv://<atlas connection string>" --drop
streamlit run app.py
```
The loader reads `sample_airbnb` from Atlas, reshapes it into the `listings` and `reviews` collections, writes them to Azure and creates the indexes. You can also pass the path to a `listingsAndReviews.json` export as `--source`. The dashboard opens at http://localhost:8501 on the landscape **Board** page, which is sized for a 1920x1080 screen (use a full-screen browser window, or zoom out slightly on a smaller laptop). Switch to **Detailed** at the top for the market pulse tiles and the value picks table.

For the "database connection" part of the submission, include `.env.example` (never the real `.env` with your password) and a screenshot of the Azure Data Explorer showing the `airbnb_analytics` database with its two collections.
