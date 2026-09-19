import json
from mal_api import get_json

POOL_SIZE = 4000
PAGE_LIMIT = 500   # the maximum the ranking endpoint allows per request
FIELDS = ("mean,num_list_users,num_scoring_users,alternative_titles,"
          "media_type,nsfw,start_date,genres")
KEEP_TYPES = {"tv", "movie", "ona"}

pool = []
offset = 0
while offset < POOL_SIZE:
    params = {"ranking_type": "bypopularity", "limit": PAGE_LIMIT,
              "offset": offset, "fields": FIELDS}
    page = get_json("/anime/ranking", params=params)
    for item in page["data"]:
        a = item["node"]
        if (a.get("mean") is None or a.get("nsfw") != "white" or a.get("media_type") not in KEEP_TYPES):
            continue
        pool.append({
            "id": a["id"],
            "title": a["alternative_titles"].get("en") or a["title"],
            "image": a.get("main_picture", {}).get("large"),
            "score": a["mean"],
            "members": a["num_list_users"],
            "scored_by": a["num_scoring_users"],
            "type": a.get("media_type"),
            "year": (a.get("start_date") or "")[:4],
            "genres": [g["name"] for g in a.get("genres", [])],
        })
    print(f"offset {offset}: pool now {len(pool)}")
    offset += PAGE_LIMIT

with open("pool.json", "w", encoding="utf-8") as f:
    json.dump(pool, f, ensure_ascii=False, indent=1)
print("Saved", len(pool), "anime to pool.json")
