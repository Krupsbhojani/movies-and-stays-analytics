# Loads sample_airbnb into Azure Cosmos DB for MongoDB as two collections: listings and reviews
# usage: python load_to_azure.py --source "<atlas uri or path to listingsAndReviews.json>" [--review-cap 50]
import os, sys, time, argparse
from decimal import Decimal
from bson import Decimal128, json_util
from pymongo import MongoClient, ASCENDING, InsertOne
from pymongo.errors import BulkWriteError
from dotenv import load_dotenv

# approximate USD rates for Feb 2019, when Airbnb data was scraped
USD = {"US": 1.0, "CA": 0.75, "ES": 1.13, "PT": 1.13, "AU": 0.71, "HK": 0.1274, "CN": 0.1274, "BR": 0.268, "TR": 0.188}

# Decimal128 to float, since floats chart cleanly and every Cosmos tier supports them
def num(v):
    if isinstance(v, Decimal128): return float(v.to_decimal())
    if isinstance(v, (Decimal, int, float)): return float(v)
    try: return float(v)
    except (TypeError, ValueError): return None

# reshape one raw document into a lean listing doc plus its review docs
def transform(d, cap):
    a, h, cc = d.get("address", {}), d.get("host", {}), d.get("address", {}).get("country_code", "US")
    rate = USD.get(cc, 1.0)
    price = num(d.get("price"))
    amen = [x for x in d.get("amenities", []) if not x.startswith("translation missing")]  # drop broken labels
    listing = {
        "_id": d["_id"], "name": d.get("name"), "property_type": d.get("property_type"), "room_type": d.get("room_type"),
        "accommodates": d.get("accommodates"), "bedrooms": d.get("bedrooms"), "beds": d.get("beds"), "bathrooms": num(d.get("bathrooms")),
        "minimum_nights": num(d.get("minimum_nights")), "cancellation_policy": d.get("cancellation_policy"),
        "price_local": price, "currency_rate_usd": rate, "price_usd": round(price * rate, 2) if price else None,
        "cleaning_fee_usd": round(num(d.get("cleaning_fee")) * rate, 2) if d.get("cleaning_fee") is not None else None,
        "amenities": amen, "amenity_count": len(amen),
        "number_of_reviews": d.get("number_of_reviews", 0), "first_review": d.get("first_review"), "last_review": d.get("last_review"),
        "availability_365": d.get("availability", {}).get("availability_365"),
        "review_scores": {k.replace("review_scores_", ""): v for k, v in d.get("review_scores", {}).items()},
        "host": {"id": h.get("host_id"), "is_superhost": h.get("host_is_superhost", False), "listings_count": h.get("host_total_listings_count"),
                 "response_rate": h.get("host_response_rate"), "response_time": h.get("host_response_time"),
                 "identity_verified": h.get("host_identity_verified", False)},
        "address": {"market": a.get("market") or "Other", "country": a.get("country"), "country_code": cc,
                    "suburb": a.get("suburb"), "location": a.get("location", {}).get("coordinates")},
    }
    # newest reviews first, optionally capped to save RU on small Cosmos tiers
    revs = sorted(d.get("reviews", []), key=lambda r: r["date"], reverse=True)[:cap] if cap else d.get("reviews", [])
    reviews = [{"_id": r["_id"], "listing_id": d["_id"], "market": listing["address"]["market"], "room_type": d.get("room_type"),
                "date": r["date"], "reviewer_id": r.get("reviewer_id"), "comments": (r.get("comments") or "")[:1000]} for r in revs]
    return listing, reviews

# read either from a Mongo/Atlas source or from the mongoexport JSON file
def read_source(src):
    if src.startswith("mongodb"):
        yield from MongoClient(src)["sample_airbnb"]["listingsAndReviews"].find()
    else:
        with open(src, encoding="utf-8") as f:
            for line in f:
                if line.strip(): yield json_util.loads(line)

# bulk insert in batches, backing off when Cosmos returns 16500 (request rate too large)
def write(coll, docs, batch=200):
    for i in range(0, len(docs), batch):
        chunk = docs[i:i + batch]
        for attempt in range(8):
            try:
                coll.bulk_write([InsertOne(x) for x in chunk], ordered=False); break
            except BulkWriteError as e:
                errs = e.details.get("writeErrors", [])
                if all(x["code"] == 11000 for x in errs): break  # duplicates from a re-run are fine
                chunk = [chunk[x["index"]] for x in errs if x["code"] != 11000]
                time.sleep(2 ** attempt * 0.5)
        print(f"  {coll.name}: {min(i + batch, len(docs))}/{len(docs)}", end="\r")
    print()

def main():
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, help="source Mongo URI or path to listingsAndReviews.json")
    p.add_argument("--target", default=os.getenv("MONGO_URI"), help="Azure connection string (default: MONGO_URI in .env)")
    p.add_argument("--db", default=os.getenv("MONGO_DB", "airbnb_analytics"))
    p.add_argument("--review-cap", type=int, default=0, help="max reviews kept per listing, 0 keeps all")
    p.add_argument("--drop", action="store_true", help="drop existing collections first")
    args = p.parse_args()
    if not args.target: sys.exit("set MONGO_URI in .env or pass --target")

    db = MongoClient(args.target, retryWrites=False)[args.db]
    if args.drop: db.listings.drop(); db.reviews.drop()

    listings, reviews = [], []
    for d in read_source(args.source):
        l, r = transform(d, args.review_cap)
        listings.append(l); reviews.extend(r)
    print(f"prepared {len(listings)} listings and {len(reviews)} reviews")

    write(db.listings, listings)
    write(db.reviews, reviews, batch=500)

    # indexes for the dashboard filters and joins
    for f in ["address.market", "room_type", "property_type", "price_usd", "host.is_superhost"]:
        db.listings.create_index([(f, ASCENDING)])
    for f in ["listing_id", "market", "date"]:
        db.reviews.create_index([(f, ASCENDING)])
    print(f"done: listings={db.listings.count_documents({})}, reviews={db.reviews.count_documents({})}")

if __name__ == "__main__":
    main()
