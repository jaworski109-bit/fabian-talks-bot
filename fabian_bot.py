import re
import json
from pathlib import Path
from datetime import datetime
import feedparser

BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "output"
OUTPUT.mkdir(exist_ok=True)

with open(BASE / "config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

CONFLICT_WORDS = {"war", "attack", "missile", "strike", "threat", "blockade", "navy", "iran", "israel"}
MONEY_WORDS = {"oil", "fuel", "prices", "shipping", "trade", "market", "gulf", "hormuz", "strait of hormuz"}
BIG_COUNTRY_WORDS = {"usa", "iran", "china", "russia", "israel", "eu", "america"}
URGENCY_WORDS = {"breaking", "urgent", "now", "today", "latest", "warning", "threat"}
STOPWORDS = {"the", "a", "an", "and", "of", "in", "to", "for", "on", "with"}

def clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def tokenize(text: str):
    return re.findall(r"[a-zA-Z0-9\-']+", text.lower())

def contains_phrase(text: str, phrase: str) -> bool:
    return phrase.lower() in text.lower()

def score_item(title: str, summary: str):
    text = f"{title} {summary}".lower()
    words = set(tokenize(text))
    w = CONFIG["weights"]
    score = 0
    reasons = []

    conflict_hits = len(words & CONFLICT_WORDS)
    if conflict_hits:
        score += conflict_hits * w["conflict"]
        reasons.append("konflikt/eskalacja")

    money_hits = len(words & MONEY_WORDS)
    if money_hits:
        score += money_hits * w["money_impact"]
        reasons.append("wpływ na ceny/handel")

    country_hits = len(words & BIG_COUNTRY_WORDS)
    if country_hits:
        score += country_hits * w["big_country"]
        reasons.append("duże państwa/geopolityka")

    urgency_hits = len(words & URGENCY_WORDS)
    if urgency_hits:
        score += urgency_hits * w["urgency"]
        reasons.append("pilność/tempo")

    short_title_bonus = 2 if len(title.split()) <= 12 else 0
    score += short_title_bonus
    if short_title_bonus:
        reasons.append("czytelny tytuł")

    if contains_phrase(text, "strait of hormuz") or contains_phrase(text, "hormuz"):
        score += 8
        reasons.append("silny trigger Ormuz")

    if contains_phrase(text, "oil") or contains_phrase(text, "fuel") or contains_phrase(text, "prices"):
        score += 6
        reasons.append("mocny trigger portfel/paliwo")

    return score, reasons

def pick_thumbnail(title: str, summary: str) -> str:
    text = f"{title} {summary}".lower()
    if "hormuz" in text and ("oil" in text or "fuel" in text or "prices" in text):
        return "PALIWO WYSTRZELI?"
    if "hormuz" in text:
        return "ORMUZ ZAPŁONIE?"
    if "iran" in text and "usa" in text:
        return "USA KONTRA IRAN"
    if "oil" in text or "fuel" in text:
        return "CENY PÓJDĄ W GÓRĘ?"
    return "ŚWIAT WCHODZI W CHAOS?"

def build_reel_text(title: str, summary: str) -> str:
    thumb = pick_thumbnail(title, summary)
    if thumb == "PALIWO WYSTRZELI?":
        return (
            "USA i Iran znowu grają Ormuzem.\n"
            "👉 Przez tę cieśninę idzie ogromna część światowej ropy.\n"
            "👉 Jedna decyzja… i ceny mogą ruszyć w górę.\n\n"
            "To nie jest daleki konflikt.\n\n"
            "👉 To jest Twoja stacja paliw.\n"
            "👉 Twój rachunek.\n"
            "👉 Twój portfel.\n\n"
            "Pytanie nie brzmi czy.\n"
            "Pytanie brzmi — kiedy to poczujesz."
        )
    if "ORMUZ" in thumb:
        return (
            "Ormuz znowu wraca na pierwszy plan.\n"
            "Statki, sankcje i nerwy między mocarstwami rosną.\n"
            "A kiedy ten punkt zapalny się rusza,\n"
            "świat zaczyna płacić za handel, transport i paliwa.\n\n"
            "To nie jest tylko geopolityka.\n"
            "To jest koszt życia."
        )
    return (
        "Na świecie znowu rośnie napięcie.\n"
        "Ale najważniejsze pytanie brzmi jedno:\n"
        "czy za chwilę zapłacisz za to wyższą ceną życia?\n\n"
        "Bo największe kryzysy zaczynają się daleko,\n"
        "a kończą w Twoim portfelu."
    )

def build_post_text(title: str, summary: str) -> str:
    return (
        f"{clean(title)}\n\n"
        f"{clean(summary)}\n\n"
        "Tu nie chodzi już tylko o politykę. "
        "Jeśli napięcie wokół tego tematu wzrośnie, rynek może przerzucić koszt na paliwo, transport i ceny. "
        "I właśnie dlatego to jest temat dla zwykłego człowieka, a nie tylko dla ekspertów.\n\n"
        "Myślisz, że to realne zagrożenie dla cen… czy tylko straszenie rynków?"
    )

def build_follow_hook() -> str:
    return "Obserwuj Fabian Talks — bo tu zobaczysz konsekwencje, zanim poczujesz je na rachunku."

def fetch_items():
    items = []
    keywords = [k.lower() for k in CONFIG["keywords"]]
    for feed_url in CONFIG["feeds"]:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:20]:
            title = clean(getattr(entry, "title", ""))
            summary = clean(getattr(entry, "summary", ""))
            link = getattr(entry, "link", "")
            hay = f"{title} {summary}".lower()
            if any(k in hay for k in keywords):
                score, reasons = score_item(title, summary)
                items.append({
                    "title": title,
                    "summary": summary[:700],
                    "link": link,
                    "score": score,
                    "reasons": reasons,
                    "thumbnail": pick_thumbnail(title, summary),
                    "reel_text": build_reel_text(title, summary),
                    "post_text": build_post_text(title, summary),
                    "follow_hook": build_follow_hook(),
                    "hashtags": CONFIG["default_hashtags"],
                })
    dedup = {}
    for item in items:
        key = re.sub(r"[^a-z0-9]+", " ", item["title"].lower()).strip()
        if key not in dedup or item["score"] > dedup[key]["score"]:
            dedup[key] = item
    return sorted(dedup.values(), key=lambda x: x["score"], reverse=True)

def save_outputs(top_items):
    json_path = OUTPUT / "top_topics.json"
    md_path = OUTPUT / "top_topics.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "topics": top_items[:3]
        }, f, ensure_ascii=False, indent=2)

    lines = [f"# Fabian Talks — top tematy ({datetime.now().strftime('%Y-%m-%d %H:%M')})", ""]
    for i, item in enumerate(top_items[:3], 1):
        lines += [
            f"## {i}. {item['thumbnail']}",
            f"**Score:** {item['score']}",
            f"**Powody:** {', '.join(item['reasons'])}",
            f"**Tytuł źródła:** {item['title']}",
            f"**Link:** {item['link']}",
            "",
            "### Tekst na rolkę",
            item['reel_text'],
            "",
            "### Tekst pod post",
            item['post_text'],
            "",
            f"### Hook follow\n{item['follow_hook']}",
            "",
            f"### Hashtagi\n{' '.join(item['hashtags'])}",
            "",
            "---",
            ""
        ]
    md_path.write_text("\n".join(lines), encoding="utf-8")

def main():
    items = fetch_items()
    save_outputs(items)
    print(f"Zapisano {min(3, len(items))} top tematów do folderu output/")

if __name__ == "__main__":
    main()