#!/usr/bin/env python3
"""Build the whole site from the YouTube channel feed. Free, no API key.

episodes.json is the record (old episodes survive the feed's 15-item window,
hand-written fields like myth/answer/slug are kept). Each run:
  - merges new videos from the feed and drops ones that left it (private/deleted)
  - writes index.html, /myths/, /myths/<slug>/, /professor/, 404.html, sitemap.xml
"""
import json, re, html, urllib.request, os, sys
import xml.etree.ElementTree as ET

CHANNEL = "UCaWE1M-HA8Rt6kZ6zmuHtdA"
FEED = "https://www.youtube.com/feeds/videos.xml?channel_id=" + CHANNEL
SITE = "https://weirdprofessoruniversity.com"
OUT = os.environ.get("SITE_OUT", ".")
SHOW = 12
YT = "https://www.youtube.com/@WeirdScienceProfessor"
TT = "https://www.tiktok.com/@weirdscienceprofessor"
IG = "https://www.instagram.com/weirdprofessoruniversity/"
IG_REELS = {"DyRHnBbYyZo": "https://www.instagram.com/reel/DeciC0bxgVF/"}
PATCH_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id=UC4PbWZpyk-1IX5HIBejFytg"
PATCH_YT = "https://www.youtube.com/@PatchTheMachine"
PATCH_TT = "https://www.tiktok.com/@patchthemachine"
PATCH_IMG = "https://yt3.googleusercontent.com/mnnzj75qElrpmVF_cGCGKd4xmBNFYV_0-_C1IMsrFYxps_39R2ihGEWreIGWY0zdYhJVVTkQ=s900-c-k-c0x00ffffff-no-rj"
LOGO = "https://yt3.googleusercontent.com/TfglslinqWTSdNONIyty7-Q0QOw-lytamex1bjZW9ej1w6FfMUSovXofqbcGPiXQVwI46Hu65w=s900-c-k-c0x00ffffff-no-rj"
NS = {"a": "http://www.w3.org/2005/Atom", "m": "http://search.yahoo.com/mrss/",
      "y": "http://www.youtube.com/xml/schemas/2015"}
E = lambda s: html.escape(s or "", quote=True)

def short_title(t):
    return re.sub(r"\.\s*Here's the (proof|catch)\.?$", "", t.strip())

def slugify(t):
    s = re.sub(r"[^a-z0-9]+", "-", short_title(t).lower()).strip("-")
    return s[:60].strip("-") or "episode"

def sources_from(desc):
    m = re.search(r"Sources?:\s*(.+?)(?:\n\s*\n|\n#|$)", desc or "", re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip().rstrip(".") if m else ""

def load_feed():
    raw = urllib.request.urlopen(urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
    out = []
    for e in ET.fromstring(raw).findall("a:entry", NS):
        d = e.find(".//m:description", NS)
        out.append({"id": e.find("y:videoId", NS).text,
                    "title": short_title(e.find("a:title", NS).text),
                    "published": e.find("a:published", NS).text,
                    "sources": sources_from(d.text if d is not None else "")})
    return out

def load_patch():
    try:
        raw = urllib.request.urlopen(urllib.request.Request(PATCH_FEED, headers={"User-Agent": "Mozilla/5.0"}), timeout=30).read()
        return [{"id": e.find("y:videoId", NS).text, "title": e.find("a:title", NS).text}
                for e in ET.fromstring(raw).findall("a:entry", NS)][:3]
    except Exception as ex:
        print("patch feed failed:", ex); return []

# ---------- shared pieces ----------
NAV = ('<header class="top"><a class="brand" href="/">Weird Professor University</a>'
       '<nav aria-label="Main"><a href="/myths/">Myths</a><a href="/professor/">The Professor</a><a href="/patch/">Patch</a>'
       '<a href="/#about">About</a></nav><button type="button" id="theme-toggle" class="theme-toggle" aria-label="Toggle dark mode" aria-pressed="false">Dark mode</button></header>')
FOOT = ('<footer><p>Weird Professor University &middot; <a href="/myths/">All myths</a> &middot; '
        '<a href="%s">YouTube</a> &middot; <a href="%s">TikTok</a> &middot; <a href="%s">Instagram</a></p>'
        '<p class="muted">Made with AI. The characters are fiction. The facts are checked.</p></footer>') % (YT, TT, IG)


SIGNUP = ('<section class="signup" id="join"><h2>Get the next myth first</h2>'
          '<p>One email when a new episode drops. No spam. Unsubscribe any time.</p>'
          "<script async data-uid='987fba3d3f' src='https://weird-professor-university.kit.com/987fba3d3f/index.js'></script>"
          '<p class="muted small">We use your email only to send new-episode emails. Unsubscribe from any email. Email is handled by Kit.</p></section>')

def head(title, desc, path, image=LOGO, ld=None, noindex=False, wide=False):
    url = SITE + path
    robots = "noindex, nofollow" if noindex else "index, follow, max-image-preview:large"
    card = "summary_large_image" if image != LOGO else "summary"
    h = ['<!doctype html>\n<html lang="en"><head>\n<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
         "<title>%s</title>" % E(title),
         '<meta name="description" content="%s">' % E(desc),
         '<link rel="canonical" href="%s">' % url,
         '<meta name="robots" content="%s">' % robots,
         '<meta name="theme-color" content="#fffdf7">',
         '<meta property="og:type" content="website"><meta property="og:site_name" content="Weird Professor University">',
         '<meta property="og:title" content="%s"><meta property="og:description" content="%s">' % (E(title), E(desc)),
         '<meta property="og:url" content="%s"><meta property="og:image" content="%s">' % (url, image),
         '<meta name="twitter:card" content="%s"><meta name="twitter:title" content="%s">' % (card, E(title)),
         '<meta name="twitter:description" content="%s"><meta name="twitter:image" content="%s">' % (E(desc), image),
         '<link rel="icon" href="%s">' % LOGO,
         '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
         '<link href="https://fonts.googleapis.com/css2?family=Lilita+One&display=swap" rel="stylesheet">',
         '<link rel="stylesheet" href="/style.css">', '<script src="/theme.js"></script>']
    if ld:
        h.append('<script type="application/ld+json">%s</script>' % json.dumps(ld, indent=1, ensure_ascii=False).replace("</", "<\\/"))
    h.append("</head><body>")
    return "\n".join(h)

def thumb(ep): return "https://i.ytimg.com/vi/%s/hqdefault.jpg" % ep["id"]
def page_url(ep): return "/myths/%s/" % ep["slug"]
def day(ep): return ep["published"][:10]

def video_ld(ep):
    v = {"@context": "https://schema.org", "@type": "VideoObject", "name": ep["title"],
         "description": ep.get("myth") or ep.get("description") or ep["title"],
         "thumbnailUrl": [thumb(ep)], "uploadDate": ep["published"],
         "embedUrl": "https://www.youtube.com/embed/" + ep["id"],
         "contentUrl": "https://www.youtube.com/shorts/" + ep["id"]}
    if ep.get("duration"): v["duration"] = ep["duration"]
    return v

def card(ep):
    blurb = ep.get("myth") or ep.get("description") or ""
    return ('<article class="ep"><a class="thumb" href="%s"><img src="%s" alt="" loading="lazy" width="480" height="360"></a>'
            '<h3><a href="%s">%s</a></h3><p>%s</p>'
            '<a class="btn ghost" href="%s">Read the fact check</a></article>') % (
        page_url(ep), thumb(ep), page_url(ep), E(ep["title"]), E(blurb), page_url(ep))

# ---------- pages ----------
def build_home(eps):
    shown = eps[:SHOW]; latest = eps[0]
    desc = ("The Weird Professor is confidently wrong about weird science. Fact Check has the real answer. "
            "Animated Shorts that bust everyday science myths, with sources.")
    title = "Weird Professor University | Animated science myths, Fact Checked"
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "Weird Professor University",
           "alternateName": "Dreadful Science", "url": SITE + "/", "description": desc},
          {"@context": "https://schema.org", "@type": "Organization", "name": "Weird Professor University",
           "url": SITE + "/", "logo": LOGO, "sameAs": [YT, TT, IG]}] + [video_ld(e) for e in shown]
    p = head(title, desc, "/", ld=ld)
    p += NAV + '<main id="top">'
    p += ('<section class="hero"><div class="hero-text"><p class="kicker">Dreadful Science</p>'
          '<h1>Weird Professor University</h1>'
          '<p class="lead">Confidently wrong about weird science. A manic professor gets everyday myths gloriously wrong. Then Fact Check interrupts with the real answer. New animated Shorts every day.</p>'
          '<div class="cta"><a class="btn" href="%s">Watch on YouTube</a><a class="btn ghost" href="%s">Follow on TikTok</a><a class="btn ghost" href="%s">Follow on Instagram</a></div></div>'
          '<img class="hero-img" src="%s" width="600" height="600" alt="The Weird Professor, a cartoon scientist with wild teal hair and yellow goggles, pointing at you"></section>') % (YT, TT, IG, LOGO)
    p += SIGNUP
    p += ('<section id="latest"><h2>Latest myth</h2><a class="latest" href="%s"><img src="%s" alt="" width="480" height="360">'
          '<div><p class="kicker">%s</p><h3>%s</h3><p>%s</p><span class="btn">Read the fact check</span></div></a></section>') % (
        page_url(latest), thumb(latest), E(day(latest)), E(latest["title"]), E(latest.get("myth") or latest.get("description") or ""))
    p += '<section id="episodes"><h2>Episodes</h2><div class="grid">%s</div><p class="more"><a class="btn ghost" href="/myths/">See every myth</a></p></section>' % "".join(card(e) for e in shown)
    p += ('<section id="characters"><h2>Characters</h2><div class="chars">'
          '<a class="char" href="/professor/"><img src="%s" width="120" height="120" alt="" loading="lazy"><div><h3>The Weird Professor</h3><p>Your host. Manic, certain and wrong about everything.</p></div></a>'
          '<div class="char"><div class="fc" aria-hidden="true">FACT<br>CHECK</div><div><h3>Fact Check</h3><p>The bar that cuts in with the sourced answer.</p></div></div>'
          '<a class="char" href="/patch/"><img src="%s" width="120" height="120" alt="" loading="lazy"><div><h3>Patch</h3><p>The lab&#39;s repair robot. Tests everything for real, fails honestly.</p></div></a>'
          '</div><p class="muted">More characters are on the way.</p></section>') % (LOGO, PATCH_IMG)
    p += ('<section id="about"><h2>About</h2>'
          '<p>Dreadful Science is a series of short animated episodes. Each one takes a gross, strange or frightening claim, lets the Weird Professor run with it, then corrects him with a sourced answer. Sources are listed on every myth page and in every video description.</p>'
          '<p>Episodes are made with AI. The characters are fiction. The facts are checked.</p></section>')
    p += "</main>" + FOOT + "</body></html>\n"
    return p

def build_myth(ep, prev, nxt):
    t = ep["title"]
    desc = (ep.get("answer") or ep.get("description") or t)
    desc = (desc[:157] + "...") if len(desc) > 160 else desc
    path = page_url(ep)
    ld = [video_ld(ep),
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
              {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
              {"@type": "ListItem", "position": 2, "name": "Myths", "item": SITE + "/myths/"},
              {"@type": "ListItem", "position": 3, "name": t, "item": SITE + path}]}]
    p = head(t + " | Weird Professor University", desc, path, image=thumb(ep), ld=ld) + NAV + "<main>"
    p += '<article class="myth"><p class="kicker"><a href="/myths/">Myths</a> &middot; %s</p><h1>%s</h1>' % (E(day(ep)), E(t))
    p += '<div class="frame solo"><iframe src="https://www.youtube-nocookie.com/embed/%s" title="%s" loading="lazy" allow="accelerometer; encrypted-media; picture-in-picture" allowfullscreen></iframe></div>' % (ep["id"], E(t))
    p += '<div class="box wrong"><h2>The Professor says</h2><p>%s</p></div>' % E(ep.get("myth") or "The Professor gets this one gloriously wrong.")
    p += '<div class="box right"><h2>Fact Check</h2><p>%s</p></div>' % E(ep.get("answer") or "Fact Check has the real, sourced answer in the video.")
    if ep.get("source_links"):
        p += '<div class="box src"><h2>Sources</h2><ul>%s</ul></div>' % "".join('<li><a href="%s" rel="noopener">%s</a></li>' % (E(u), E(n)) for n, u in ep["source_links"])
    elif ep.get("sources"):
        p += '<div class="box src"><h2>Sources</h2><p>%s</p></div>' % E(ep["sources"])
    p += '<div class="cta"><a class="btn" href="https://www.youtube.com/shorts/%s">Watch on YouTube</a><a class="btn ghost" href="%s">Follow on TikTok</a>%s</div>' % (ep["id"], TT, ('<a class="btn ghost" href="%s">Watch on Instagram</a>' % IG_REELS[ep["id"]]) if ep["id"] in IG_REELS else "")
    p += '<p class="muted">Made with AI. The characters are fiction. The facts are checked.</p>'
    p += SIGNUP
    links = []
    if nxt: links.append('<a href="%s">&larr; Newer: %s</a>' % (page_url(nxt), E(nxt["title"])))
    if prev: links.append('<a href="%s">Older: %s &rarr;</a>' % (page_url(prev), E(prev["title"])))
    if links: p += '<nav class="pn" aria-label="More myths">%s</nav>' % "".join(links)
    p += "</article></main>" + FOOT + "</body></html>\n"
    return p

def build_index(eps):
    desc = "Every myth the Weird Professor has gotten wrong, with the sourced Fact Check answer."
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "All myths",
          "url": SITE + "/myths/", "description": desc}
    p = head("All myths | Weird Professor University", desc, "/myths/", ld=ld) + NAV + "<main>"
    p += '<section><h1 class="pagetitle">All myths</h1><p class="lead">Every claim the Professor got wrong, with the sourced answer.</p><div class="grid">%s</div></section>' % "".join(card(e) for e in eps)
    return p + "</main>" + FOOT + "</body></html>\n"

def build_professor(eps):
    desc = "Meet the Weird Professor: the manic, confident, always wrong host of Dreadful Science. Fact Check sets him straight."
    ld = {"@context": "https://schema.org", "@type": "ProfilePage", "mainEntity": {
        "@type": "Person", "name": "The Weird Professor", "description": desc, "image": LOGO,
        "sameAs": [YT, TT]}}
    p = head("The Weird Professor | Meet the host of Weird Professor University", desc, "/professor/", ld=ld) + NAV + "<main>"
    p += ('<section class="hero"><div class="hero-text"><p class="kicker">Character</p><h1>The Weird Professor</h1>'
          '<p class="lead">Wild teal hair, yellow goggles and total certainty. He has a theory about everything, and it is wrong every time.</p>'
          '<p>Each episode he explains a myth like he invented it. Then Fact Check cuts in with the real answer and the sources. He never learns.</p>'
          '<div class="cta"><a class="btn" href="/myths/">See his mistakes</a><a class="btn ghost" href="%s">Watch on YouTube</a></div></div>'
          '<img class="hero-img" src="%s" width="600" height="600" alt="The Weird Professor, a cartoon scientist with wild teal hair and yellow goggles"></section>') % (YT, LOGO)
    p += ('<section><h2>Fact Check</h2><div class="char"><div class="fc" aria-hidden="true">FACT<br>CHECK</div>'
          '<div><h3>The correction bar</h3><p>Every claim ends with a sourced answer. Names of the sources are on every myth page.</p></div></div></section>')
    p += '<section><h2>His latest mistakes</h2><div class="grid">%s</div></section>' % "".join(card(e) for e in eps[:3])
    p += '<section><h2>More characters</h2><p>Meet <a href="/patch/">Patch</a>, the lab&#39;s repair robot.</p><p class="muted">New faces are on the way. Follow on <a href="%s">YouTube</a> or <a href="%s">TikTok</a> to meet them first.</p></section>' % (YT, TT)
    return p + "</main>" + FOOT + "</body></html>\n"

def build_patch(pe):
    desc = "Patch is the Weird Professor University's repair robot. One real test per episode, failures left in. Watch Patch on YouTube and TikTok."
    ld = {"@context": "https://schema.org", "@type": "ProfilePage", "mainEntity": {
        "@type": "Person", "name": "Patch", "description": desc, "image": PATCH_IMG, "sameAs": [PATCH_YT, PATCH_TT]}}
    p = head("Patch | The lab's repair robot | Weird Professor University", desc, "/patch/", image=PATCH_IMG, ld=ld) + NAV + "<main>"
    p += ('<section class="hero"><div class="hero-text"><p class="kicker">Character</p><h1>Patch</h1>'
          '<p class="lead">The university lab&#39;s repair robot. Small, unfinished and very determined.</p>'
          '<p>While the Professor gets science wrong on purpose, Patch runs real tests and logs what actually happened, failures included. The robot and his world are fiction. The experiments and results are real.</p>'
          '<div class="cta"><a class="btn" href="%s">Watch Patch on YouTube</a><a class="btn ghost" href="%s">Follow on TikTok</a></div></div>'
          '<img class="hero-img" src="%s" width="600" height="600" alt="Patch, a small repair robot"></section>') % (PATCH_YT, PATCH_TT, PATCH_IMG)
    if pe:
        p += '<section><h2>Latest from Patch</h2><div class="grid">%s</div></section>' % "".join(
            ('<article class="ep"><a class="thumb" href="https://www.youtube.com/shorts/%s"><img src="https://i.ytimg.com/vi/%s/hqdefault.jpg" alt="" loading="lazy" width="480" height="360"></a>'
             '<h3><a href="https://www.youtube.com/shorts/%s">%s</a></h3></article>') % (x["id"], x["id"], x["id"], E(x["title"])) for x in pe)
    p += '<section><p class="muted">Patch has his own channel. This is his home at the university.</p></section>'
    return p + "</main>" + FOOT + "</body></html>\n"

def build_404():
    p = head("Page not found | Weird Professor University", "That page does not exist.", "/404.html", noindex=True) + NAV
    p += '<main><section><h1 class="pagetitle">Wrong again.</h1><p class="lead">The Professor says this page exists. Fact Check says it does not.</p><div class="cta"><a class="btn" href="/">Back home</a><a class="btn ghost" href="/myths/">All myths</a></div></section></main>'
    return p + FOOT + "</body></html>\n"

def build_sitemap(eps):
    latest = day(eps[0])
    urls = [("/", latest), ("/myths/", latest), ("/professor/", latest), ("/patch/", latest)] + [(page_url(e), day(e)) for e in eps]
    body = "".join("<url><loc>%s%s</loc><lastmod>%s</lastmod></url>" % (SITE, u, d) for u, d in urls)
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>\n' % body

def write(path, text):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
    open(full, "w", encoding="utf-8").write(text)


# Curated fact-check text and source links (verified Oct 13 2026). Applied over episodes.json.
EXTRA = {
 "DyRHnBbYyZo": {
  "myth": "Sugar makes kids hyper.",
  "answer": "It does not. A 1995 JAMA meta-analysis pooled 23 blinded, placebo-controlled studies and found that sugar does not affect children's behaviour or thinking. Parents who expect a sugar rush tend to see one, which is expectation. The authors note a small effect, or an effect in some subsets of children, can't be ruled out.",
  "source_links": [["Wolraich, Wilson and White, JAMA 1995: The Effect of Sugar on Behavior or Cognition in Children (meta-analysis)", "https://jamanetwork.com/journals/jama/article-abstract/391812"]]},
 "zVBzxKlpXZw": {
  "myth": "Cracking your knuckles gives you arthritis.",
  "answer": "It probably doesn't. Studies comparing habitual knuckle-crackers with non-crackers found no higher rate of hand arthritis. The pop is bubbles bursting in the joint fluid. There is a catch: chronic cracking may reduce grip strength, and a couple of injuries have been reported.",
  "source_links": [["Harvard Health: Does cracking knuckles cause arthritis?", "https://www.health.harvard.edu/pain/does-cracking-knuckles-cause-arthritis"]]},
 "TWELor9a07U": {
  "myth": "Bats are blind.",
  "answer": "They are not. All bats have working eyes and can see. Vision varies by species, and some bats see better than people in the dark. Many bats use echolocation and sight together.",
  "source_links": [["Bat Conservation International: Blind as a Bat? No Such Thing", "https://www.batcon.org/blind-as-a-bat-no-such-thing/"],
                   ["USGS: Are bats blind?", "https://www.usgs.gov/faqs/are-bats-blind"],
                   ["Current Biology: Bats: Vision or echolocation, why not both?", "https://www.cell.com/current-biology/fulltext/S0960-9822(22)00313-X"]]},
}

def main():
    data = json.load(open(os.path.join(OUT, "episodes.json")))
    known = {x["id"]: x for x in data}
    try:
        feed = load_feed()
    except Exception as ex:
        print("feed fetch failed, leaving site unchanged:", ex); return
    if not feed:
        print("empty feed, leaving site unchanged"); return
    if len(feed) < 15:
        ids = {f["id"] for f in feed}
        known = {k: v for k, v in known.items() if k in ids}
    for f in feed:
        if f["id"] in known:
            k = known[f["id"]]
            k.setdefault("title", f["title"]); k.setdefault("published", f["published"])
            if not k.get("sources") and f["sources"]: k["sources"] = f["sources"]
        else:
            known[f["id"]] = {"id": f["id"], "title": f["title"], "published": f["published"], "sources": f["sources"]}
    for k_, v_ in EXTRA.items():
        if k_ in known: known[k_].update(v_)
    eps = sorted(known.values(), key=lambda x: x["published"], reverse=True)
    used = set()
    for e in eps:
        s = e.get("slug") or slugify(e["title"])
        while s in used: s += "-2"
        used.add(s); e["slug"] = s
    write("episodes.json", json.dumps(eps, indent=1, ensure_ascii=False))
    write("index.html", build_home(eps))
    write("myths/index.html", build_index(eps))
    write("professor/index.html", build_professor(eps))
    write("patch/index.html", build_patch(load_patch()))
    write("404.html", build_404())
    write("sitemap.xml", build_sitemap(eps))
    for i, e in enumerate(eps):
        write("myths/%s/index.html" % e["slug"], build_myth(e, eps[i + 1] if i + 1 < len(eps) else None, eps[i - 1] if i else None))
    print("episodes:", len(eps), "latest:", day(eps[0]))

if __name__ == "__main__":
    main()
