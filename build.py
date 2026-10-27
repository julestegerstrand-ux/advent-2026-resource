#!/usr/bin/env python3
"""Builds index.html from template.html and the Word files in "New England Advent 2026".
Run:  python3 build.py   (needs pandoc and Pillow)"""
import os, re, json, subprocess, urllib.parse
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "New England Advent 2026")
M1 = os.path.join(SRC, "Module 1_Advent Year B")
M2 = os.path.join(SRC, "Module 2_General resources")
os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)

def url(path):
    return urllib.parse.quote(os.path.relpath(path, ROOT).replace(os.sep, "/"))

def html_of(path):
    return subprocess.run(["pandoc", "-t", "html", "--wrap=none", path], capture_output=True, text=True, check=True).stdout

def clean(h, title=None):
    h = h.replace("Links to an external site.", "")
    # drop leading helper lines and a repeated page title
    while True:
        m = re.match(r"\s*<p>(.*?)</p>\s*", h, re.S)
        if not m:
            break
        t = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if re.match(r"^(MODULE \d|Page \d|M\d\.)", t) or (title and t.lower() == title.lower()):
            h = h[m.end():]
        else:
            break
    h = re.sub(r"<p>\s*\(NEED[^<]*</p>", "", h)
    h = re.sub(r"<p>(&nbsp;|\s| )*</p>", "", h)
    # YouTube links and iframes become embedded videos
    def vid(i): return f'<div class="video"><iframe src="https://www.youtube.com/embed/{i}" title="Video" allowfullscreen></iframe></div>'
    h = re.sub(r"<p>\s*<a href=\"https?://youtu\.be/([\w-]+)[^\"]*\">[^<]*</a>\s*</p>", lambda m: vid(m.group(1)), h)
    h = re.sub(r"<p>\s*&lt;iframe[^>]*youtube\.com/embed/([\w-]+)[^>]*&gt;.*?</p>", lambda m: vid(m.group(1)), h, flags=re.S)
    h = re.sub(r"<iframe[^>]*youtube\.com/embed/([\w-]+)[^>]*></iframe>", lambda m: vid(m.group(1)), h)
    h = h.replace('<div class="video"><div class="video">', '<div class="video">').replace("</iframe></div></div>", "</iframe></div>")
    # links into the old Canvas site will not work here
    h = re.sub(r'<a href="https://pdlearn\.instructure\.com[^"]*">([^<]*)</a>', r'<span class="muted">\1 (link to be added)</span>', h)
    return h

def thumb(src, dst, w):
    im = Image.open(src).convert("RGB")
    im.thumbnail((w, w * 2))
    im.save(os.path.join(ROOT, "assets", dst), quality=82)
    return "assets/" + dst

im = Image.open(os.path.join(gdir0 := os.path.join(M2, "M2.1.Advent Series Graphics", "Prepare Way Images"), "preparethewaybg.jpg")).convert("RGB")
im.crop((0, 40, 3840, 1520)).resize((1800, 694)).save(os.path.join(ROOT, "assets", "banner.jpg"), quality=84)

P = {}
P["how"] = clean(html_of(os.path.join(M1, "M1.How to Use This Resource.docx")), "How to Use This Resource")
P["intro"] = clean(html_of(os.path.join(M1, "M1. Introduction to Season pf Advent.docx")), "Introduction to Advent")
P["psalm"] = clean(html_of(os.path.join(M1, "M1. The Weekly Psalm.docx")), "The Weekly Psalm")
P["smallgroup"] = clean(html_of(os.path.join(ROOT, "M1. Small Group Resources.docx")), "Small Group Resources")
P["welcome"] = '<div class="draft">This page is ready for the welcome message.</div>'

# Meet the Authors: each table becomes a card with the headshot
au = os.path.join(M1, "M1. Meet the Authors")
heads = [thumb(os.path.join(au, f), n, 300) for f, n in [
    ("John W. Nielson cropped small.jpg", "nielson.jpg"), ("Julene Headshot 2025.jpg", "julene.jpg"),
    ("Mat Thomas Headshot.png", "thomas.jpg"), ("David Young Headshot.JPG", "young.jpg")]]
h = clean(html_of(os.path.join(au, "M1. Neet the Authors.docx")), "Meet the Authors")
tabs = re.findall(r"<table>.*?</table>", h, re.S)
for i, t in enumerate(tabs):
    cells = [c for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", t, re.S) if re.sub(r"<[^>]+>|\s", "", c)]
    who = "".join(cells)
    who = re.sub(r"[\U0001F4E7\U0001F310\U0001F4F0]️?", "", who)
    h = h.replace(t, f'<div class="author"><img src="{heads[i]}" alt=""><div>{who}</div></div>')
P["authors"] = h

# General resources
gdir = os.path.join(M2, "M2.1.Advent Series Graphics", "Prepare Way Images")
g1 = thumb(os.path.join(gdir, "preparethewaycover.jpg"), "prepare-cover.jpg", 900)
g2 = thumb(os.path.join(gdir, "preparethewaybg.jpg"), "prepare-bg.jpg", 900)
def fig(img, orig, cap):
    return f'<figure><img src="{img}" alt="{cap}"><figcaption><a href="{url(orig)}" download>Download the full size image</a></figcaption></figure>'
P["graphics"] = '<p>Graphics for the Prepare the Way Advent series.</p><div class="gallery">' + \
    fig(g1, os.path.join(gdir, "preparethewaycover.jpg"), "Prepare the Way cover") + \
    fig(g2, os.path.join(gdir, "preparethewaybg.jpg"), "Prepare the Way background") + "</div>"

sd = os.path.join(M2, "M2.2.Advent Sermon Series")
pdf = os.path.join(sd, "Prepare the Way Sermon Series Overview.pdf")
sh = html_of(os.path.join(sd, "M2.2.Sample Sermon Series Overview.docx"))
sh = re.sub(r'<a href="https://pdlearn[^"]*">[^<]*</a>', f'<a href="{url(pdf)}">HERE</a>', sh)
sh = clean(sh, "Sample Sermon Series Overview")
P["sermon"] = sh
P["calendar"] = clean(html_of(os.path.join(M2, "M2.3, Seasons of the Christian Church Year.docx")), "Introduction to the Christian Calendar")
P["calendar"] += '<p><a href="https://youtu.be/EjWE9GRhfmI" target="_blank" rel="noopener">Watch on YouTube</a></p>'
P["colors"] = clean(html_of(os.path.join(M2, "M2.4. Colors and Visuals for Advent.docx")), "Colors and Visuals for Advent")
P["wreath"] = clean(html_of(os.path.join(M2, "M2.5. The Advent Wreath.docx")), "The Advent Wreath")
P["wreath"] = '<p><span class="muted">John\'s video on the Advent Wreath (to be added)</span></p>' + P["wreath"]
_wr = "New%20England%20Advent%202026/Module%202_General%20resources/Prepare%20the%20Way%20Advent%20Wreath%20Readings.pdf"
P["wreath"] = P["wreath"].replace('<p><span class="muted">Prepare the Way Advent Wreath Readings (link to be added)</span></p>', '')
P["wreath"] = P["wreath"].replace('<span class="muted">Download Prepare the Way Advent Wreath Readings (link to be added)</span>', '<a href="%s" target="_blank" rel="noopener">Download Prepare the Way Advent Wreath Readings (PDF)</a>' % _wr)
P["wreath"] = P["wreath"].replace('<span class="muted">Family Guide to the Advent Wreath (link to be added)</span>', '<a href="https://www.focusonthefamily.com/parenting/celebrating-advent-as-a-family-parents-guide-to-meaningful-christmas-traditions/" target="_blank" rel="noopener">Family Guide to the Advent Wreath (Focus on the Family)</a>')
P["music"] = '<p>A list of Advent songs for worship and personal use.</p><a class="btn" href="https://www.thegospelcoalition.org/article/advent-playlist-2023/" target="_blank" rel="noopener">Open the Advent Songs List (The Gospel Coalition)</a>'
cp = os.path.join(M2, "M2.7.Prepare the Way Children's Scope and Sequence.pdf")
P["children"] = f'<p>The scope and sequence for the children\'s lessons in the Prepare the Way series.</p><a class="btn" href="{url(cp)}">Open the Children\'s Scope and Sequence (PDF)</a>'

cdir = os.path.join(ROOT, "content")
if os.path.isdir(cdir):
    for fn in sorted(os.listdir(cdir)):
        if fn.endswith(".html"):
            P["c_" + fn[:-5]] = open(os.path.join(cdir, fn), encoding="utf-8").read()

def better_video(h):
    def fix(m):
        vid = m.group(1)
        return ('<iframe src="https://www.youtube-nocookie.com/embed/%s?rel=0&amp;cc_load_policy=1&amp;playsinline=1" ' % vid)
    h = re.sub(r'<iframe src="https://www\.youtube\.com/embed/([\w-]+)"\s*', fix, h)
    h = re.sub(r'(<iframe src="https://www\.youtube-nocookie\.com/embed/[^"]+" )(?![^>]*loading=)', r'\1loading="lazy" referrerpolicy="strict-origin-when-cross-origin" ', h)
    return h

for k in list(P):
    P[k] = better_video(P[k])
P["intro"] = P["intro"].replace('title="Video"', 'title="Introduction to Advent video"')
P["calendar"] = P["calendar"].replace('title="Video"', 'title="Introduction to the Christian Calendar video"')

t = open(os.path.join(ROOT, "template.html"), encoding="utf-8").read()
t = t.replace("/*PAGES*/", "var P=" + json.dumps(P, ensure_ascii=False).replace("</", "<\\/") + ";")
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("built", len(t), "bytes;", len(P), "pages")
