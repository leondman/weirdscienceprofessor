#!/usr/bin/env python3
"""Refresh the episode list from the YouTube channel feed. Free, no API key.
Keeps episodes.json as the record (so old episodes survive after the feed's
15-item window), then rewrites the episode grid and VideoObject schema in
index.html and the sitemap lastmod."""
import json, re, html, urllib.request, datetime
import xml.etree.ElementTree as ET

CHANNEL = "UCaWE1M-HA8Rt6kZ6zmuHtdA"
FEED = "https://www.youtube.com/feeds/videos.xml?channel_id=" + CHANNEL
SHOW = 12
NS = {"a": "http://www.w3.org/2005/Atom", "m": "http://search.yahoo.com/mrss/",
      "y": "http://www.youtube.com/xml/schemas/2015"}
START, END = "<!--EPISODES:START-->", "<!--EPISODES:END-->"

def short_title(t):
    return re.sub(r"\.\s*Here's the (proof|catch)\.?$", "", t.strip())

def blurb(desc):
    m = re.search(r"Source:\s*([^,(:\n]+)", desc or "")
    src = m.group(1).strip().rstrip(".") if m else None
    base = "The Professor gets it wrong. Fact Check has the real answer."
    return base + (" Source: " + src + "." if src else "")

def load_feed():
    req = urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0"})
    root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
    out = []
    for e in root.findall("a:entry", NS):
        vid = e.find("y:videoId", NS).text
        out.append({
            "id": vid,
            "title": short_title(e.find("a:title", NS).text),
            "published": e.find("a:published", NS).text,
            "description": blurb(e.find(".//m:description", NS).text),
        })
    return out

def main():
    data = json.load(open("episodes.json"))
    known = {x["id"]: x for x in data}
    try:
        feed = load_feed()
    except Exception as ex:
        print("feed fetch failed, leaving site unchanged:", ex)
        return
    if not feed:
        print("empty feed, leaving site unchanged")
        return
    if len(feed) < 15:
        feed_ids = {f["id"] for f in feed}
        known = {k: v for k, v in known.items() if k in feed_ids}
    for f in feed:
        if f["id"] in known:
            # keep hand-written text, refresh nothing but missing fields
            for k in ("title", "published"):
                known[f["id"]].setdefault(k, f[k])
        else:
            known[f["id"]] = f
    eps = sorted(known.values(), key=lambda x: x["published"], reverse=True)
    json.dump(eps, open("episodes.json", "w"), indent=1, ensure_ascii=False)
    shown = eps[:SHOW]
    total = len(eps)

    cards = []
    for i, ep in enumerate(shown):
        n = total - i
        t = html.escape(ep["title"], quote=True).replace("&#x27;", "&#x27;")
        d = html.escape(ep["description"], quote=True)
        cards.append(
            '<article class="ep" id="ep%d">\n'
            '<div class="frame"><iframe src="https://www.youtube-nocookie.com/embed/%s" title="%s" loading="lazy" allow="accelerometer; encrypted-media; picture-in-picture" allowfullscreen></iframe></div>\n'
            '<h3>%s</h3><p>%s</p>\n'
            '<a class="btn ghost" href="https://www.youtube.com/shorts/%s">Watch on YouTube</a></article>'
            % (n, ep["id"], t, t, d, ep["id"]))
    grid = START + '<div class="grid">' + "".join(cards) + "</div>" + END

    page = open("index.html", encoding="utf-8").read()
    if START in page:
        page = re.sub(re.escape(START) + ".*?" + re.escape(END), lambda m: grid, page, flags=re.S)
    else:
        page = re.sub(r'<div class="grid">.*?</div></section>\n?<section id="characters">',
                      lambda m: grid + '</section>\n<section id="characters">', page, count=1, flags=re.S)

    m = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', page, re.S)
    ld = [x for x in json.loads(m.group(2)) if x.get("@type") != "VideoObject"]
    for ep in shown:
        v = {"@context": "https://schema.org", "@type": "VideoObject",
             "name": ep["title"], "description": ep["description"],
             "thumbnailUrl": ["https://i.ytimg.com/vi/%s/hqdefault.jpg" % ep["id"]],
             "uploadDate": ep["published"],
             "embedUrl": "https://www.youtube.com/embed/" + ep["id"],
             "contentUrl": "https://www.youtube.com/shorts/" + ep["id"]}
        if ep.get("duration"):
            v["duration"] = ep["duration"]
        ld.append(v)
    page = page[:m.start(2)] + json.dumps(ld, indent=1, ensure_ascii=False) + page[m.end(2):]
    open("index.html", "w", encoding="utf-8").write(page)

    latest = eps[0]["published"][:10]
    sm = open("sitemap.xml").read()
    sm = re.sub(r"<lastmod>.*?</lastmod>", "<lastmod>%s</lastmod>" % latest, sm)
    open("sitemap.xml", "w").write(sm)
    print("episodes:", total, "latest:", latest)

if __name__ == "__main__":
    main()
