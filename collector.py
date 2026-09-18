# sme-voice-cebu / harvester.py — async, read-only SME harvester (Philippines)
import asyncio, os, json, aiohttp
SUBREDDITS = ["Philippines", "Cebu", "smallbusiness", "digitalnomad"]
KEYWORDS = ["bir", "rehistro", "puhunan", "dti", "ingredient cost",
 "tourism season", "delivery", "rent"]
UA = "python:sme-voice-cebu:v0.9 (by /u/LiezlFajardoSME)"
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API = "https://oauth.reddit.com"
async def token(sess):
 auth = aiohttp.BasicAuth(os.environ["REDDIT_CLIENT_ID"],
 os.environ["REDDIT_CLIENT_SECRET"])
 async with sess.post(TOKEN_URL, auth=auth,
 data={"grant_type": "client_credentials"},
 headers={"User-Agent": UA}) as r:
 return (await r.json())["access_token"]
async def get(sess, path, headers):
 for attempt in range(4): # exponential backoff on 429/5xx
 async with sess.get(API + path, headers=headers) as r:
 if r.status == 200:
 return await r.json()
 await asyncio.sleep(2 ** attempt * 3)
 return None
async def main():
 async with aiohttp.ClientSession() as s:
 tk = await token(s)
 h = {"User-Agent": UA, "Authorization": f"Bearer {tk}"}
 out = open("harvest.jsonl", "a")
 for sub in SUBREDDITS: # GET only; no write scopes
 data = await get(s, f"/r/{sub}/new?limit=100", h)
 if not data: continue
 for c in data.get("data", {}).get("children", []):
 d = c["data"]
 text = (d["title"] + " " + d.get("selftext", "")).lower()
 if any(k in text for k in KEYWORDS):
 out.write(json.dumps({"id": d["id"], "sub": sub,
 "ts": d["created_utc"],
 "author_hash": hash(d["author"]) % 10**12,
 "snippet": text[:300]}) + "\n")
 await asyncio.sleep(3) # ~20 QPM ceiling
 out.close()
if __name__ == "__main__":
 asyncio.run(main()) # twice weekly via cron; ~430 calls/week total
