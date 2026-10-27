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
YT = "https://www.youtube.com/@weirdprofessoruniversity"
TT = "https://www.tiktok.com/@weirdscienceprofessor"
IG = "https://www.instagram.com/weirdprofessoruniversity/"
IG_REELS = {"DyRHnBbYyZo": "https://www.instagram.com/reel/DeciC0bxgVF/"}
LOGO = "https://yt3.googleusercontent.com/-61qrc1KAk86H9EYhTvGIaIeQizxZhHso1X87l-x0fBHDOijWlBgYHQu3AfL5fsnu4N6y1HwJXI=s900-c-k-c0x00ffffff-no-rj"
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

# ---------- shared pieces ----------
NAV = ('<header class="top"><a class="brand" href="/">Weird Professor University</a>'
       '<nav aria-label="Main"><a href="/myths/">Myths</a><a href="/professor/">The Professor</a>'
       '<a href="/books-and-kits/">Books and kits</a><a href="/#about">About</a></nav><button type="button" id="theme-toggle" class="theme-toggle" aria-label="Toggle dark mode" aria-pressed="false">Dark mode</button></header>')
FOLLOW = ('<section class="follow" aria-label="Follow our work"><h2>Follow the next fact check</h2>'
          '<p>More Professor myths, animated stories and checked sources.</p><div class="cta">'
          '<a class="btn" href="%s">Follow on YouTube</a><a class="btn ghost" href="%s">Follow on TikTok</a>'
          '<a class="btn ghost" href="%s">Follow on Instagram</a></div></section>') % (YT, TT, IG)
FOOT = FOLLOW + ('<footer><p>Weird Professor University &middot; <a href="/myths/">All myths</a> &middot; '
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
         '<link rel="stylesheet" href="/style.css?v=20261019-design">', '<script src="/theme.js"></script>']
    if ld:
        h.append('<script type="application/ld+json">%s</script>' % json.dumps(ld, indent=1, ensure_ascii=False).replace("</", "<\\/"))
    h.append("</head><body>")
    return "\n".join(h)

def thumb(ep): return "https://i.ytimg.com/vi/%s/hqdefault.jpg" % ep["id"]
def page_url(ep): return "/myths/%s/" % ep["slug"]
def day(ep): return ep["published"][:10]

def video_ld(ep):
    v = {"@context": "https://schema.org", "@type": "VideoObject", "name": ep["title"],
         "description": ep.get("answer") or ep.get("description") or ep["title"],
         "thumbnailUrl": [thumb(ep)], "uploadDate": ep["published"],
         "embedUrl": "https://www.youtube.com/embed/" + ep["id"],
         "url": SITE + page_url(ep)}
    if ep.get("duration"): v["duration"] = ep["duration"]
    return v

def card(ep):
    # Owner-approved 27 Oct 2026: hide only the Toilets upload card; retain its record/page.
    if ep["id"] == "NtQlVsxAaoQ":
        return ""
    blurb = ("Myth: " + ep["myth"]) if ep.get("myth") else ep.get("description", "")
    return ('<article class="ep"><a class="thumb %s" href="%s"><img src="%s" alt="" loading="lazy" width="480" height="360"></a>'
            '<h3><a href="%s">%s</a></h3><p>%s</p>'
            '<a class="btn ghost" href="%s">Read the fact check</a></article>') % (
        ("landscape" if ep.get("format") == "landscape" else ""), page_url(ep), thumb(ep), page_url(ep), E(ep["title"]), E(blurb), page_url(ep))

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
    p += ('<section class="home-intro"><div class="intro-mascot"><img src="%s" width="64" height="64" alt="The Weird Professor"><p class="kicker">The Professor is in.</p></div>'
          '<h1>Confidently wrong.<br>Fact checked.</h1><p class="lead">A weird science myth. One wildly wrong professor. Then the real answer.</p></section>') % LOGO
    p += ('<section id="latest" class="latest-section"><p class="kicker">Latest episode · %s</p><div class="latest-feature"><a class="latest-art" href="%s"><img src="%s" alt="" width="480" height="360"></a>'
          '<div><h2>%s</h2><div class="cta"><a class="btn" href="https://www.youtube.com/watch?v=%s">Watch the latest myth</a><a class="text-action" href="%s">Read the fact check →</a></div></div></div></section>') % (E(day(latest)), page_url(latest), thumb(latest), E(latest["title"]), latest["id"], page_url(latest))
    p += '<section id="episodes"><h2>Episodes</h2><div class="grid">%s</div><p class="more"><a class="btn ghost" href="/myths/">See every myth</a></p></section>' % "".join(card(e) for e in shown)
    p += ('<section id="characters"><h2>Characters</h2><div class="chars">'
          '<a class="char" href="/professor/"><img src="%s" width="120" height="120" alt="" loading="lazy"><div><h3>The Weird Professor</h3><p>Your host. Manic, certain and always ready with a theory.</p></div></a>'
          '<div class="char"><div class="fc" aria-hidden="true">FACT<br>CHECK</div><div><h3>Fact Check</h3><p>The bar that cuts in with the sourced answer.</p></div></div>'
          '</div><p class="muted">More characters are on the way.</p></section>') % LOGO
    p += ('<section id="about"><h2>About</h2>'
          '<p>Dreadful Science is a series of short animated episodes. Each one takes a gross, strange or frightening claim, lets the Weird Professor run with it, then corrects him with a sourced answer. Sources are listed on every myth page and in every video description.</p>'
          '<p>Episodes are made with AI. The characters are fiction. The facts are checked.</p></section>')
    p += SIGNUP
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
    p += '<div class="frame solo %s"><iframe src="https://www.youtube-nocookie.com/embed/%s" title="%s" loading="lazy" allow="accelerometer; encrypted-media; picture-in-picture" allowfullscreen></iframe></div>' % (("landscape" if ep.get("format") == "landscape" else ""), ep["id"], E(t))
    p += '<div class="box wrong"><h2>The Professor says</h2><p>%s</p></div>' % E(ep.get("myth") or "The Professor gets this one gloriously wrong.")
    p += '<div class="box right"><h2>Fact Check</h2><p>%s</p></div>' % E(ep.get("answer") or "Fact Check has the real, sourced answer in the video.")
    if ep.get("source_links"):
        p += '<div class="box src"><h2>Sources</h2><ul>%s</ul></div>' % "".join('<li><a href="%s" rel="noopener">%s</a></li>' % (E(u), E(n)) for n, u in ep["source_links"])
    elif ep.get("sources"):
        p += '<div class="box src"><h2>Sources</h2><p>%s</p></div>' % E(ep["sources"])
    p += '<div class="cta"><a class="btn" href="https://www.youtube.com/watch?v=%s">Watch on YouTube</a><a class="btn ghost" href="%s">Follow on TikTok</a>%s</div>' % (ep["id"], TT, ('<a class="btn ghost" href="%s">Watch on Instagram</a>' % IG_REELS[ep["id"]]) if ep["id"] in IG_REELS else "")
    p += '<p class="muted">Made with AI. The characters are fiction. The facts are checked.</p>'
    p += SIGNUP
    links = []
    if nxt: links.append('<a href="%s">&larr; Newer: %s</a>' % (page_url(nxt), E(nxt["title"])))
    if prev: links.append('<a href="%s">Older: %s &rarr;</a>' % (page_url(prev), E(prev["title"])))
    if links: p += '<nav class="pn" aria-label="More myths">%s</nav>' % "".join(links)
    p += "</article></main>" + FOOT + "</body></html>\n"
    return p

def build_index(eps):
    desc = "Every Professor myth, with the sourced Fact Check answer."
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": "All myths",
          "url": SITE + "/myths/", "description": desc}
    p = head("All myths | Weird Professor University", desc, "/myths/", ld=ld) + NAV + "<main>"
    p += '<section class="box right"><h2><a href="/myths/clocks-back-body-clock/">Clocks back. Body clock reset?</a></h2><p>Read the checked explanation and official sources.</p></section>'
    p += '<section><h1 class="pagetitle">All myths</h1><p class="lead">Every Professor claim, with the sourced answer.</p><div class="grid">%s</div></section>' % "".join(card(e) for e in eps)
    return p + "</main>" + FOOT + "</body></html>\n"

def build_professor(eps):
    desc = "Meet the Weird Professor: the manic, confident myth-making host of Dreadful Science. Fact Check sets him straight."
    ld = {"@context": "https://schema.org", "@type": "ProfilePage", "mainEntity": {
        "@type": "Person", "name": "The Weird Professor", "description": desc, "image": LOGO,
        "sameAs": [YT, TT]}}
    p = head("The Weird Professor | Meet the host of Weird Professor University", desc, "/professor/", ld=ld) + NAV + "<main>"
    p += ('<section class="hero"><div class="hero-text"><p class="kicker">Character</p><h1>The Weird Professor</h1>'
          '<p class="lead">Wild teal hair, round glasses and total certainty. He has a theory about everything. Fact Check tests his claims.</p>'
          '<p>Each episode he explains a myth like he invented it. Then Fact Check cuts in with the real answer and the sources. He never learns.</p>'
          '<div class="cta"><a class="btn" href="/myths/">See his mistakes</a><a class="btn ghost" href="%s">Watch on YouTube</a></div></div>'
          '<img class="hero-img" src="%s" width="600" height="600" alt="The Weird Professor, a 3D cartoon scientist with wild teal hair, round black glasses and a white lab coat"></section>') % (YT, LOGO)
    p += ('<section><h2>Fact Check</h2><div class="char"><div class="fc" aria-hidden="true">FACT<br>CHECK</div>'
          '<div><h3>The correction bar</h3><p>Every claim ends with a sourced answer. Links to the sources are on every myth page.</p></div></div></section>')
    p += '<section><h2>His latest mistakes</h2><div class="grid">%s</div></section>' % "".join(card(e) for e in eps[:3])
    p += '<section><h2>More characters</h2><p class="muted">New faces are on the way. Follow on <a href="%s">YouTube</a> or <a href="%s">TikTok</a> to meet them first.</p></section>' % (YT, TT)
    return p + "</main>" + FOOT + "</body></html>\n"

def build_404():
    p = head("Page not found | Weird Professor University", "That page does not exist.", "/404.html", noindex=True) + NAV
    p += '<main><section><h1 class="pagetitle">Wrong again.</h1><p class="lead">The Professor says this page exists. Fact Check says it does not.</p><div class="cta"><a class="btn" href="/">Back home</a><a class="btn ghost" href="/myths/">All myths</a></div></section></main>'
    return p + FOOT + "</body></html>\n"


def build_books():
    p = head("Books and kits | Weird Professor University", "Science books and an anatomy model for curious readers. Optional further reading, with affiliate disclosures.", "/books-and-kits/")
    p += "<style>" + '.preview{background:#fff5d8;border:1px solid #d3bd56;border-radius:12px;padding:16px;margin:24px 0}.books{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}.book{background:var(--card);padding:22px;border-radius:18px;min-width:0}.book img{width:100%;height:270px;object-fit:contain;background:#fff;border-radius:10px}.book .author{color:var(--mute);margin:4px 0 12px}.book h2{font-size:28px;margin:16px 0 4px}.book .tagline{color:var(--pink);font-weight:700}.book .note{font-size:14px}.pending{display:block;border:1px solid var(--rule);border-radius:999px;padding:10px 14px;color:var(--mute);font-size:14px;text-align:center}.disclosure{font-weight:600}.intro{max-width:760px}main{padding-bottom:40px}.book .note{min-height:65px}@media(max-width:650px){.books{grid-template-columns:minmax(0,1fr)}.book img{height:240px}.book .note{min-height:0}}' + "</style>" + NAV
    p += '<main><section class="intro"><p class="kicker">The Professor\'s reading shelf</p><h1>Books and kits</h1><p class="lead">Curiosity is excellent. Confidence without checking is my department. Here are books and a model for the checking part.</p><p class="disclosure">As an Amazon Associate I earn from qualifying purchases.</p><p>Based on publisher and manufacturer information, not hands-on tests. Optional reading, not evidence for our fact checks.</p></section><section class="books"><article class="book"><img alt="What If? 2 cover or product image" loading="lazy" src="https://www.hachette.co.uk/wp-content/uploads/2022/03/hbg-title-what-if2-3-94.jpg"/><h2>1. What If? 2</h2><p class="author">Randall Munroe</p><p class="tagline">Absurd questions, serious science.</p><p>Could you cool the planet by opening every freezer? I have a theory. Fortunately, this book does the maths.</p><p class="note">For readers who enjoy strange thought experiments. Not a guide to trying them.</p><a class="pending" href="https://www.amazon.co.uk/What-Additional-Scientific-Hypothetical-Questions/dp/147368062X?tag=weirdprofesso-21" rel="sponsored nofollow noopener" target="_blank">View on Amazon UK (ad) (paid link)</a></article><article class="book"><img alt="How Science Works cover or product image" loading="lazy" src="https://dk.com/cdn/shop/files/getfile_537a8568-18f1-486e-a40f-de1bfe1b7f4a.jpg?v=1757440873"/><h2>2. How Science Works</h2><p class="author">DK</p><p class="tagline">Start with the picture.</p><p>Atoms, forces, living things, space. A visual guide for when my explanation has become mostly waving.</p><p class="note">Illustrated introductions to core science, with updated topics including AI and quantum computing.</p><span class="pending">Pending: exact 2025 edition not found. No Amazon link.</span></article><article class="book"><img alt="How Technology Works cover or product image" loading="lazy" src="https://dk.com/cdn/shop/files/getfile_1b196d5e-3452-4bad-805d-80554d0105bb.jpg?v=1759672489"/><h2>3. How Technology Works</h2><p class="author">DK</p><p class="tagline">For the curious tinkerer.</p><p>Zips, engines, computers. Find out what the parts actually do before declaring the whole thing powered by tiny robots.</p><p class="note">An illustrated look inside everyday devices and the principles behind them.</p><a class="pending" href="https://www.amazon.co.uk/dp/0241356288?tag=weirdprofesso-21" rel="sponsored nofollow noopener" target="_blank">View on Amazon UK (ad) (paid link)</a></article><article class="book"><img alt="The Body: A Guide for Occupants cover or product image" loading="lazy" src="https://cdn.penguin.co.uk/dam-assets/books/9780552779906/9780552779906-jacket-large.jpg"/><h2>4. The Body: A Guide for Occupants</h2><p class="author">Bill Bryson</p><p class="tagline">You live in one. Read the manual.</p><p>A tour of the extraordinary machinery under your skin. No razor blades, swallowed gum experiments or other Professor behaviour required.</p><p class="note">Popular science about the body and how it works. Not medical advice.</p><a class="pending" href="https://www.amazon.co.uk/dp/0552779903?tag=weirdprofesso-21" rel="sponsored nofollow noopener" target="_blank">View on Amazon UK (ad) (paid link)</a></article><article class="book"><img alt="Immune cover or product image" loading="lazy" src="https://www.hachette.co.uk/wp-content/uploads/2021/03/hbg-title-immune-245.jpg"/><h2>5. Immune</h2><p class="author">Philipp Dettmer</p><p class="tagline">The microscopic defence department.</p><p>Viruses, bacteria, antibodies and a very busy immune system. Consider this the longer answer after our wet-hair myth.</p><p class="note">An illustrated introduction to the immune system. Not a diagnosis or treatment guide.</p><a class="pending" href="https://www.amazon.co.uk/Immune-Kurzgesagt-gorgeously-illustrated-immune/dp/1529360684?tag=weirdprofesso-21" rel="sponsored nofollow noopener" target="_blank">View on Amazon UK (ad) (paid link)</a></article><article class="book"><img alt="The Science of Animals cover or product image" loading="lazy" src="https://cdn2.penguin.com.au/covers/400/9780241346785.jpg"/><h2>6. The Science of Animals</h2><p class="author">DK</p><p class="tagline">Beyond the three-second myth.</p><p>How animals sense, move, communicate and survive. A better use of your eyes than assuming the bat has none.</p><p class="note">Photography-led zoology, organised around body parts and how they work.</p><a class="pending" href="https://www.amazon.co.uk/Science-Animals-Inside-their-Secret/dp/0241346789?tag=weirdprofesso-21" rel="sponsored nofollow noopener" target="_blank">View on Amazon UK (ad) (paid link)</a></article><article class="book"><img alt="Human Body Anatomy Model cover or product image" loading="lazy" src="https://www.thamesandkosmos.co.uk/wp-content/uploads/2020/04/Website-product-image-low-res-template-2025-08-12T090524.839-min-600x600.jpg.webp"/><h2>7. Human Body Anatomy Model</h2><p class="author">Thames &amp; Kosmos / Nature Discovery</p><p class="tagline">A body you can put back together.</p><p>Build the torso and fit its organs into place. At last, a laboratory activity where losing your brain is a tidy-up problem.</p><p class="note">Manufacturer age: 8+. Small parts: choking hazard, not suitable for under 3s. Keep the instructions. This is a model, not a medical tool.</p><a class="pending" href="https://www.amazon.co.uk/Thames-Kosmos-Discovery-Anatomy-Educational/dp/B0CJN2KWJV?tag=weirdprofesso-21" rel="sponsored nofollow noopener" target="_blank">View on Amazon UK (ad) (paid link)</a></article></section><section><h2>A note from Fact Check</h2><p>Follow a kit\'s age guidance and instructions. Never copy a dangerous stunt from an animated episode. Our science pages are education, not medical advice.</p><p class="muted">Publisher and manufacturer information checked 15 October 2026. Amazon links checked by the site owner. Prices and availability are shown on Amazon and can change. Product images belong to their publishers or manufacturers.</p></section></main>'
    return p + FOOT + "</body></html>\n"

def build_sitemap(eps):
    latest = day(eps[0])
    urls = [("/", latest), ("/myths/", latest), ("/professor/", latest), ("/books-and-kits/", "2026-10-15")] + [(page_url(e), day(e)) for e in eps]
    body = "".join("<url><loc>%s%s</loc><lastmod>%s</lastmod></url>" % (SITE, u, d) for u, d in urls)
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>\n' % body

def write(path, text):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
    open(full, "w", encoding="utf-8").write(text)


# Curated fact-check text and source links (verified Oct 13 2026). Applied over episodes.json.
EXTRA = {
 "sk820mQJXIM": {"myth": "A night race must be cool enough to keep the driver from overheating.", "answer": "Night does not remove the heat and humidity. Sweat cools the body when it evaporates; high humidity makes it feel hotter (heat index). Formula 1 describes Singapore as a night race with a hot cockpit, little cooling airflow and drivers working in fireproof overalls and a helmet. Those conditions can still put a heavy heat load on a driver.", "source_links": [["National Weather Service: Heat index and sweat evaporation", "https://www.weather.gov/ama/heatindex"], ["Formula 1: How drivers prepare for Singapore", "https://www.formula1.com/en/latest/article/surviving-and-thriving-in-singapore-how-drivers-prepare-for-the-toughest.5WK0nvwo8wQWmpT4LZgFJB"]]},
 "mLgBaP5NirM": {"myth": "The tongue has separate zones that can each taste only one flavour.", "answer": "There are five basic tastes: sweet, sour, bitter, salty and umami. Different types of taste cells are scattered throughout the tongue rather than confined to exclusive taste zones. Sensitivity can vary between regions, but the familiar taste map is misleading. Flavour also depends on smell, texture and temperature.", "source_links": [["NIH/NIDCD: Taste Disorders", "https://www.nidcd.nih.gov/health/taste-disorders"], ["Harvard Health: The myth of tongue and taste", "https://www.health.harvard.edu/diet-and-nutrition/the-myth-of-tongue-and-taste"]]},
 "x4RDUeQ_z18": {"myth": "Carrots give you superhuman night vision.", "answer": "Carrots contain beta-carotene, which the body can convert into vitamin A. Vitamin A helps normal vision in dim light. Adequate vitamin A supports eye health, but it cannot give night-vision superpowers. Deficiency can cause night blindness; treating a deficiency is different from boosting normal vision.", "source_links": [["NHS: Vitamin A", "https://www.nhs.uk/conditions/vitamins-and-minerals/vitamin-a/"], ["Harvard Nutrition Source: Vitamin A", "https://nutritionsource.hsph.harvard.edu/vitamin-a/"]]},
 "r6oXqGYx-Y8": {"source_links": [["Live Science: Do goldfish really have a 3-second memory?", "https://www.livescience.com/goldfish-memory.html"]]},
 "hm7paKmi7TE": {"source_links": [["Mayo Clinic: Does shaved hair grow back thicker?", "https://www.mayoclinic.org/healthy-lifestyle/adult-health/expert-answers/hair-removal/faq-20058427"]]},
 "NVF6kUCAdhg": {"source_links": [["Scientific American: Do People Only Use 10 Percent of Their Brains?", "https://www.scientificamerican.com/article/do-people-only-use-10-percent-of-their-brains/"]]},
 "GjGkIfn5I2k": {"source_links": [["US National Weather Service: Lightning Myths", "https://www.weather.gov/safety/lightning-myths"]]},
 "0zclC4hWPQ4": {"answer": "In a laboratory study, simulated gastric juice corroded razor blades over time. After 24 hours the blades weighed 63% of their original weight. This does not make swallowing metal safe: sharp objects can cause serious injury. Never try it. A lab corrosion result is not a safe way to remove a swallowed object.", "source_links": [["Li et al., 1997: In vitro effects of simulated gastric juice on swallowed metal objects (PubMed)", "https://pubmed.ncbi.nlm.nih.gov/9283866/"]]},
 "1mYke4OsLow": {"format": "landscape", "myth": "Wet hair causes colds; sugar makes children hyper; knuckle cracking causes arthritis; bulls hate red; the Great Wall is easy to see from space.", "answer": "Wet hair does not cause a cold: viruses do. A 1995 JAMA meta-analysis found no overall effect of sugar on children's behaviour or cognition, while noting that a small effect or effects in subsets of children cannot be ruled out. Knuckle-cracking studies have not found higher arthritis rates; Donald Unger's one-person experiment was a memorable example, not proof on its own. Movement, not a special hatred of red, draws a bull's attention. NASA says the Great Wall is not visible from the Moon and is difficult or impossible to see unaided from Earth orbit.", "source_links": [["Mayo Clinic: Myths about catching a cold", "https://newsnetwork.mayoclinic.org/discussion/mayo-clinic-q-and-a-myths-about-catching-a-cold/"], ["Wolraich, Wilson and White, JAMA 1995: Sugar meta-analysis", "https://jamanetwork.com/journals/jama/article-abstract/391812"], ["Scientific American: Crack Research", "https://www.scientificamerican.com/article/crack-research/"], ["Live Science: Why Do Bulls Charge When They See Red?", "https://www.livescience.com/33700-bulls-charge-red.html"], ["NASA: Great Wall", "https://www.nasa.gov/image-article/great-wall/"]]},
 "xKAbWN8G-NY": {"format": "landscape", "myth": "We use only 10% of our brains; shaving thickens hair; goldfish remember for three seconds; lightning never strikes twice; gum stays in the stomach for seven years.", "answer": "Over a day we use virtually every part of the brain, not just 10%. Shaving does not change hair thickness, colour or growth rate: a blunt tip can feel coarser. Goldfish can learn and retain information far longer than three seconds, including for months. Lightning can strike the same place repeatedly, especially tall isolated objects. Swallowed gum usually passes through relatively intact rather than staying for seven years, though large amounts combined with constipation can rarely cause a blockage in children.", "source_links": [["Scientific American: The 10% brain myth", "https://www.scientificamerican.com/article/do-people-only-use-10-percent-of-their-brains/"], ["Mayo Clinic: Shaving and hair thickness", "https://www.mayoclinic.org/healthy-lifestyle/adult-health/expert-answers/hair-removal/faq-20058427"], ["Live Science: Goldfish memory", "https://www.livescience.com/goldfish-memory.html"], ["The Guardian: Plymouth feeding-lever research", "https://www.theguardian.com/uk/2003/oct/01/highereducation.science"], ["US National Weather Service: Lightning Myths", "https://www.weather.gov/safety/lightning-myths"], ["Live Science: Repeated Empire State Building strikes", "https://www.livescience.com/13704-empire-state-building-lightning-strike.html"], ["Mayo Clinic: Swallowing gum", "https://www.mayoclinic.org/diseases-conditions/indigestion/expert-answers/digestive-system/faq-20058446"]]},

 "K13pEc5kgU4": {"myth": "Swallowed gum stays in your stomach for seven years.", "answer": "It does not. Your body cannot digest chewing gum, but swallowed gum moves relatively intact through your digestive system and passes out in your stool. Very rarely, large amounts of swallowed gum combined with constipation have blocked intestines in children. Do not make swallowing gum a habit.", "source_links": [["Mayo Clinic: Swallowing gum: Is it harmful?", "https://www.mayoclinic.org/diseases-conditions/indigestion/expert-answers/digestive-system/faq-20058446"]]},
 "DyRHnBbYyZo": {
  "myth": "Sugar makes kids hyper.",
  "answer": "It does not. A 1995 JAMA meta-analysis pooled 23 blinded, placebo-controlled studies and found that sugar does not affect children's behaviour or thinking. Parents who expect a sugar rush tend to see one, which is expectation. The authors note a small effect, or an effect in some subsets of children, can't be ruled out.",
  "source_links": [["Wolraich, Wilson and White, JAMA 1995: The Effect of Sugar on Behavior or Cognition in Children (meta-analysis)", "https://jamanetwork.com/journals/jama/article-abstract/391812"]]},
 "zVBzxKlpXZw": {
  "myth": "Cracking your knuckles gives you arthritis.",
  "answer": "It probably doesn't. Studies comparing habitual knuckle-crackers with non-crackers found no higher rate of hand arthritis. There is a catch: chronic cracking may reduce grip strength, and a couple of injuries have been reported.",
  "source_links": [["Harvard Health: Does cracking knuckles cause arthritis?", "https://www.health.harvard.edu/pain/does-cracking-knuckles-cause-arthritis"]]},
 "TWELor9a07U": {
  "myth": "Bats are blind.",
  "answer": "They are not. All bats have working eyes and can see. Vision varies by species, and some bats see better than people in the dark. Many bats use echolocation and sight together.",
  "source_links": [["Bat Conservation International: Blind as a Bat? No Such Thing", "https://www.batcon.org/blind-as-a-bat-no-such-thing/"],
                   ["USGS: Are bats blind?", "https://www.usgs.gov/faqs/are-bats-blind"],
                   ["Current Biology: Bats: Vision or echolocation, why not both?", "https://www.cell.com/current-biology/fulltext/S0960-9822(22)00313-X"]]},
}

RETIRED_IDS = {"3BWzKtDIhsA", "vgp-p5f3Exo", "wcW6tSFLh5A"}  # public availability checks 20 Oct 2026; reason unconfirmed


def main():
    data = json.load(open(os.path.join(OUT, "episodes.json")))
    known = {x["id"]: x for x in data}
    try:
        feed = load_feed()
    except Exception as ex:
        print("feed fetch unavailable, retaining known episodes:", ex); feed = []
    if not known and not feed:
        print("No episode data available"); return
    for f in feed:
        if f["id"] in known:
            k = known[f["id"]]
            k.setdefault("title", f["title"]); k.setdefault("published", f["published"])
            if not k.get("sources") and f["sources"]: k["sources"] = f["sources"]
        else:
            known[f["id"]] = {"id": f["id"], "title": f["title"], "published": f["published"], "sources": f["sources"]}
    for k_, v_ in EXTRA.items():
        if k_ in known: known[k_].update(v_)
    # Explicit exclusion list: IDs excluded from active lists after public availability checks
    # (oembed / watch page unavailable); the reason is unconfirmed (not claimed private or removed).
    # Nothing is inferred from the feed. Records stay in episodes.json; pages stay live with noindex
    # and are left out of lists, sitemap and llms.txt. Remove an ID from RETIRED_IDS to restore it.
    for k in known.values():
        if k["id"] in RETIRED_IDS: k["retired"] = True
        else: k.pop("retired", None); k.pop("missing_runs", None)
    all_eps = sorted(known.values(), key=lambda x: x["published"], reverse=True)
    eps = [x for x in all_eps if not x.get("retired")]
    retired = [x for x in all_eps if x.get("retired")]
    if not eps:
        raise SystemExit("no publishable episodes; leaving site unchanged")
    used = set()
    for e in all_eps:
        s = e.get("slug") or slugify(e["title"])
        while s in used: s += "-2"
        used.add(s); e["slug"] = s
    write("episodes.json", json.dumps(all_eps, indent=1, ensure_ascii=False))
    write("index.html", build_home(eps))
    write("myths/index.html", build_index(eps))
    write("professor/index.html", build_professor(eps))
    write("404.html", build_404())
    write("books-and-kits/index.html", build_books())
    write("sitemap.xml", build_sitemap(eps))
    write("robots.txt", "User-agent: *\nAllow: /\n\nSitemap: " + SITE + "/sitemap.xml\n")
    llms = "# Weird Professor University\n\n> Animated science myth-busting by The Weird Professor, with sourced fact checks.\n\nThe characters and animated stories are fiction. Source links and factual qualifications are on each episode page.\n\n## Main pages\n\n- [Home](" + SITE + "/)\n- [All myths](" + SITE + "/myths/)\n- [The Professor](" + SITE + "/professor/)\n\n## Follow\n\n- [YouTube](" + YT + ")\n- [TikTok](" + TT + ")\n- [Instagram](" + IG + ")\n\n## Fact checks\n\n"
    llms += "".join("- [" + e["title"] + "](" + SITE + page_url(e) + "): " + e.get("answer", "") + "\n" for e in eps)
    write("llms.txt", llms)
    for i, e in enumerate(eps):
        write("myths/%s/index.html" % e["slug"], build_myth(e, eps[i + 1] if i + 1 < len(eps) else None, eps[i - 1] if i else None))
    for e in retired:  # keep the page reachable but out of search, lists and sitemap
        write("myths/%s/index.html" % e["slug"], build_myth(e, None, None).replace("index, follow, max-image-preview:large", "noindex, nofollow", 1))
    print("episodes:", len(eps), "retired:", len(retired), "latest:", day(eps[0]))

if __name__ == "__main__":
    # Keep layout fixes with the generator and refresh cached styles.
    style_path = os.path.join(OUT, "style.css")
    css = open(style_path, encoding="utf-8").read()
    if "/* Audit navigation wrap */" not in css:
        write("style.css", css + "\n/* Audit navigation wrap */\n.pn a{white-space:normal;overflow-wrap:anywhere}\n")
    main()
