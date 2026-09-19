from mal_api import get_json

params = {
    "ranking_type": "bypopularity",
    "limit": 10,
    "fields": "mean,num_list_users,num_scoring_users,alternative_titles,media_type",
}
page = get_json("/anime/ranking", params=params)
for item in page["data"]:
    a = item["node"]
    title = a["alternative_titles"].get("en") or a["title"]
    print(a["id"], title, a["mean"], a["num_list_users"])
print(page["paging"])
