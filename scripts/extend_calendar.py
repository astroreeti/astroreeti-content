#!/usr/bin/env python3
"""Extend calendar.json with the Aug 26 -> Nov 25 2026 quarter.

Structure decided 2026-08-13 with Reeti:

  * Four standing themes own the weekdays, so followers learn the rhythm:
        Mon = marriage & love   Tue = career & business
        Wed = money (loss/gain) Thu = health
  * Friday morning is the recurring transit slot (TL). Its topic is
    deliberately generic -- the authoring session must verify real positions
    against drikpanchang.com on the day, never from memory.
  * Friday evening / Saturday morning / Sunday morning rotate through
    craft, myth-busting and cross-theme material.
  * Sunday evening finishes the Nakshatra Katha serial (12 episodes left
    after Krittika's catch-up on Aug 24) and then closes it with a finale.
  * Saturday has a morning slot ONLY -- an evening entry there can never fire.

  * LANGUAGE: from 2026-08-26 morning slots stay Hindi (Devanagari) and
    evening slots are authored in English. Slots before that date keep the
    Hindi-everywhere rule they were written under.

Guards are machine-readable so the authoring run cannot forget them:
    health-disclaimer   -> needs an explicit "astrology is not treatment,
                           see a doctor" slide
    no-wealth-guarantee -> needs an explicit "no yoga guarantees wealth" slide

Run from the repo root:  python3 scripts/extend_calendar.py
It is idempotent -- it rebuilds every day from START_DATE onward.
"""
import datetime
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAL = ROOT / "calendar.json"

START = datetime.date(2026, 8, 26)
END = datetime.date(2026, 11, 25)

# --------------------------------------------------------------------------
# Bridge days: the old calendar left Aug 22 missing entirely and Aug 23-25
# without morning entries. Fill them in the pre-switch language (Hindi both
# slots) so nothing has to be improvised.
# --------------------------------------------------------------------------
BRIDGE = {
    "2026-08-22": {  # Saturday - morning only
        "morning": ("RL", "marriage", "Joint families & married life — the 2nd house you marry into", None),
    },
    "2026-08-23": {
        "morning": ("RL", "career", "Government job yoga — what actually points to it, and what doesn't", None),
    },
    "2026-08-24": {
        "morning": ("RL", "money", "Where the money leaks — reading the 12th house of expenditure", "no-wealth-guarantee"),
    },
    "2026-08-25": {
        "morning": ("RL", "health", "Sleep, rest and the Moon — why the mind won't switch off", "health-disclaimer"),
    },
}

# --------------------------------------------------------------------------
# Topic banks. Morning = accessible/real-life (Hindi). Evening = technical
# deep-dive (English). Nothing here repeats a row already in topics.md.
# --------------------------------------------------------------------------

MARRIAGE_AM = [
    "Love marriage or arranged — which combinations lean which way (5th vs 7th)",
    "Why you keep attracting the same kind of partner — the 7th lord's dispositor",
    "Long-distance relationships — 7th lord in the 12th, 9th and what it asks of you",
    "Break-ups: what a chart shows about closure, and what it refuses to say",
    "Remarriage and second partnerships — the 9th house as the second 7th",
    "36/36 in guna milan and still fighting — what the score never measured",
    "Marriage after 30 — Saturn's timing is maturity, not punishment",
    "What the 7th house says about your partner's nature (not their name)",
    "The manglik panic — what the classical texts actually condition it on",
    "Commitment without a ceremony — 7th house vs 8th house bonds",
    "When two charts disagree about the timing of the same marriage",
    "In-laws and the married home — 4th from the 7th, read plainly",
    "Why we never predict separation or widowhood — the ethics line",
]

MARRIAGE_PM = [
    "Darakaraka: the Jaimini partner significator most readings skip",
    "Upapada Lagna and the 2nd from it — the classical marriage-durability method",
    "Timing marriage properly: Vimshottari dasha plus the Saturn/Jupiter double transit",
    "Venus combust — what it really does to relationship karma, degree by degree",
    "The 7th lord through all twelve houses: a working interpretation matrix",
    "Guna milan mechanics: what each of the eight kutas actually scores",
    "Rahu in the 7th and the 'foreign or unconventional partner' claim, tested",
    "D9 vs D7 vs D12 — which varga answers which family question",
    "Papakartari, maraka and the afflicted kalatra bhava — and what redeems it",
    "Bhrigu Bindu and event timing for relationship milestones",
    "Comparing two charts without guna milan — a practical synastry method",
    "The 8th house is marriage's real longevity house — here's why",
    "Vargottama, atmakaraka and the Navamsa beyond marriage prediction",
]

CAREER_AM = [
    "Job change timing — when a dasha shift is the one opening the door",
    "Freelance or salaried — which temperament your chart is built for",
    "Trouble with your boss — the Sun, the 10th lord and the 6th house",
    "Founders and the 3rd house — initiative, risk and self-effort",
    "A career break and the return — the 12th house read honestly",
    "Choosing a field from your single strongest planet",
    "Strong 10th house, stuck career — why the dasha decides the pace",
    "Working abroad vs working remotely from home — two different signatures",
    "Family business or your own path — the 4th house against the 10th",
    "Creative careers — the 3rd, the 5th, and Mercury with Venus",
    "Teaching, consulting, advising — Jupiter's professions",
    "Losing a job: what to actually look at, without the fear-mongering",
    "The quiet 6th house — service, competition and the work you do daily",
]

CAREER_PM = [
    "Dashamsha D10 done properly — lagna, 10th lord and Amatyakaraka together",
    "Amatyakaraka: the Jaimini career significator and how to use it",
    "Arudha Lagna — public perception versus the work you actually do",
    "Panchadha Maitri: five-fold planetary friendship and why results change",
    "Karyesha logic — Sun, Saturn and Mercury as the karma-control planets",
    "Ashtakavarga for career: reading bindus in the 10th house",
    "When D10 and Vimshottari contradict each other — resolution order",
    "Raja yogas that deliver versus raja yogas that stay on paper",
    "Saturn as karma karaka — slow, structural, and frequently misread",
    "Business partnerships: the 7th house and the 10th from the 7th",
    "Muhurta for launching an enterprise — what to actually check",
    "Mapping modern digital professions onto classical karakas",
    "Reading professional longevity: the 10th, its lord, and dasha sequence",
]

MONEY_AM = [
    "Income keeps rising, savings don't — a strong 11th with a weak 2nd",
    "Loans and EMIs — when borrowing is structurally fine, and when it isn't",
    "Inheritance and family money — the 8th house, read without drama",
    "The stock market and the 5th house — and why no yoga guarantees a profit",
    "Property as wealth or property as burden — the 4th house question",
    "Gold and savings instruments — Venus, Jupiter and what they signify",
    "Money inside a marriage — joint finances and the 2nd from the 7th",
    "Sudden financial loss — how to read it without spiralling",
    "Charity, giving and the 12th house paradox",
    "Enough money, constant money anxiety — the Moon and the 2nd house",
    "Side income streams — the 3rd house with the 11th",
    "Financial recovery after a bad stretch — spotting the dasha turn",
    "Lending money to family — the 2nd, 4th and 6th houses together",
    "Your first salary to your first investment — sequencing it by dasha",
]

MONEY_PM = [
    "Dhana yogas: the classical list and the strict conditions everyone drops",
    "Sorting shastra from folklore — Lakshmi yoga and the 'Kubera' claims",
    "The 11th house of labha — gains are not the same as free money",
    "Maraka houses doing double duty: the 2nd and 7th in wealth analysis",
    "The Hora chart D2 — the wealth varga almost nobody opens",
    "Ashtakavarga for wealth: bindus in the 2nd and 11th",
    "Debilitated planets that still produce money — the conditions that allow it",
    "Jupiter or Venus as the wealth significator — the actual difference",
    "Timing gains: the 11th lord's dasha against Jupiter's transit",
    "Vyaya analysis: the 12th lord through the houses, in order",
    "Kendra-trikona lords and the combinations that genuinely build wealth",
    "A strong chart that is still broke — when the dasha sequence is the story",
    "Reading a chart for financial risk tolerance rather than financial promise",
    "Why the classics tie wealth to the 2nd, 11th and 9th — and not to luck",
]

HEALTH_AM = [
    "The 6th house or the 8th — an episode versus something chronic",
    "Digestion, appetite and the fire element in a chart",
    "Stress and a restless mind — Mercury with the Moon",
    "Bones, joints and the territory Saturn governs",
    "Eyes and vision — the Sun, the Moon and the 2nd/12th houses",
    "Skin and what the Moon, Mars and Venus mix has to do with it",
    "Women's health and the Moon's cycle in the chart",
    "Children's health and the 5th house — a parent's honest guide",
    "Ageing parents' health — the 4th and 9th houses",
    "Injury-prone placements, handled responsibly and without alarm",
    "Recovery and convalescence — the 8th house's other, kinder face",
    "Preventive habits your chart makes easier to keep",
    "Energy through the day — Chandra bala and simple routine",
]

HEALTH_PM = [
    "The 6-8-12 dusthana axis in medical Jyotish — the classical frame",
    "Rogesha: the 6th lord and its dispositor, in reading order",
    "Shashtamsa D6 — the health varga and how to use it cautiously",
    "Kalapurusha: body parts mapped by sign, and the limits of that map",
    "Vata, pitta, kapha and the grahas — the Ayurvedic-Jyotish bridge",
    "Maraka versus arishta — why longevity claims are irresponsible",
    "Balarishta and childhood in the classics — historical context, modern caution",
    "Transits that correlate with low vitality — Sun and Moon strength",
    "Ashtakavarga and the 6th house — bindus as resilience, not diagnosis",
    "Remedies people ask for: what has scriptural basis and what does not",
    "The mind in classical texts — Moon, Mercury, and where Jyotish stops",
    "Chandra bala and daily wellbeing — a usable weekly method",
    "Why we never predict disease — the ethics of medical astrology",
]

# Friday evening: craft and technique, cross-theme.
CRAFT_PM = [
    "A repeatable seven-step order for reading any chart",
    "Bhava bala — how house strength is actually computed",
    "Shadbala without the maths phobia — what each of the six strengths means",
    "Retrogression: the classical position versus the modern one",
    "Combustion degrees, planet by planet — the table you should keep",
    "Special lagnas: Bhava, Hora and Ghati lagna in practice",
    "Argala and virodha argala — intervention and its blocking",
    "The eight Jaimini karakas, in order, with what each one governs",
    "Chara dasha or Vimshottari — when each one is the right tool",
    "Yogini and Ashtottari — the lesser dashas and their proper scope",
    "Sade sati read properly — structure, not seven and a half years of dread",
    "Jupiter's twelve-year cycle across the houses",
    "The Rahu-Ketu axis and its eighteen-month rhythm",
]

# Saturday morning (single post): myth-busting and practical literacy.
SATURDAY_AM = [
    "Myth: 'manglik means a doomed marriage' — what the texts really say",
    "Myth: 'Rahu is always bad' — placement, house and dasha decide",
    "How to establish an accurate birth time when nobody wrote it down",
    "Ayanamsa: why two apps show you two different charts",
    "Choosing an astrologer — the red flags worth walking away from",
    "Gemstones: what the classics prescribe and what the market invented",
    "Myth: 'a weak Moon means depression' — where astrology must stop",
    "Free chart tools — the settings you must check before trusting the output",
    "Panchang basics you can genuinely use every week",
    "Reading your own Vimshottari dasha timeline, start to finish",
    "Questions worth asking before you pay for any reading",
    "What astrology cannot answer — an honest list",
    "Building your own chart-reading checklist for the quarter",
]

# Sunday morning: cross-theme, accessible.
SUNDAY_AM = [
    "What makes a partnership last, chart-wise — beyond the wedding date",
    "A rich chart and a stable chart are not the same thing",
    "Doing work that suits your nature rather than your résumé",
    "Managing your energy by your Moon sign — a practical week",
    "Parents' approval and the marriage question — the 4th and 9th",
    "Mid-life direction change — reading it as a turn, not a failure",
    "Seasonal wellbeing and the transits behind it",
    "When friendship becomes love — what shifts in the chart's story",
    "Joint accounts and financial trust between partners",
    "Repairing a reputation after a professional setback",
    "Burnout where the 6th and 10th houses meet",
    "Money conversations with adult children — the 5th and 2nd",
    "Quarter recap: your four-house wellbeing checklist",
]

# Sunday evening: the remaining Nakshatra Katha serial, in strict order.
NAKSHATRA_PM = [
    "Vishakha — Indra and Agni, the twin-flamed goal you nearly reach",
    "Anuradha — Mitra, the friendship that survives distance",
    "Jyeshtha — Indra's elder pride, the protective eldest's burden",
    "Mula — Nirriti, the root that has to be pulled up to be seen",
    "Purva Ashadha — Apas, the waters that are never defeated",
    "Uttara Ashadha — the Vishvadevas and the victory that actually lasts",
    "Shravana — Vishnu's three steps, and the star that listens",
    "Dhanishta — the eight Vasus, wealth carried on rhythm",
    "Shatabhisha — Varuna's hundred healers and the veiled circle",
    "Purva Bhadrapada — Aja Ekapada, the one-footed fire",
    "Uttara Bhadrapada — Ahir Budhnya, the deep serpent's stillness",
    "Revati — Pushan, the shepherd who brings everyone home",
    "Nakshatra Katha finale — all 27 stars in one map, and how to use them",
]

TL_TOPIC = ("This week's transits — sign changes, retrogrades and the Moon's "
            "route (VERIFY every position against drikpanchang.com sidereal "
            "data on the authoring day; never write positions from memory)")

THEME_GUARD = {"money": "no-wealth-guarantee", "health": "health-disclaimer"}


class Bank:
    """A topic bank that refuses to repeat itself."""

    def __init__(self, name, items):
        self.name, self.items, self.i = name, items, 0

    def take(self):
        if self.i >= len(self.items):
            raise RuntimeError(
                f"topic bank '{self.name}' exhausted after {len(self.items)} "
                f"entries -- add more topics rather than letting it repeat"
            )
        item = self.items[self.i]
        self.i += 1
        return item


def build():
    cal = json.loads(CAL.read_text())
    days = [d for d in cal["days"] if d["date"] < START.isoformat()]

    # Patch the bridge days that the old calendar left half-empty.
    by_date = {d["date"]: d for d in days}
    for date, slots in BRIDGE.items():
        entry = by_date.get(date)
        if entry is None:
            entry = {"day": None, "date": date}
            days.append(entry)
        for run, (pillar, theme, topic, guard) in slots.items():
            if entry.get(run):
                continue  # never overwrite something already planned
            slot = {"pillar": pillar, "theme": theme, "topic": topic, "lang": "hi"}
            if guard:
                slot["guard"] = guard
            entry[run] = slot
    days.sort(key=lambda d: d["date"])

    banks = {
        ("marriage", "am"): Bank("marriage_am", MARRIAGE_AM),
        ("marriage", "pm"): Bank("marriage_pm", MARRIAGE_PM),
        ("career", "am"): Bank("career_am", CAREER_AM),
        ("career", "pm"): Bank("career_pm", CAREER_PM),
        ("money", "am"): Bank("money_am", MONEY_AM),
        ("money", "pm"): Bank("money_pm", MONEY_PM),
        ("health", "am"): Bank("health_am", HEALTH_AM),
        ("health", "pm"): Bank("health_pm", HEALTH_PM),
        ("craft", "pm"): Bank("craft_pm", CRAFT_PM),
        ("saturday", "am"): Bank("saturday_am", SATURDAY_AM),
        ("sunday", "am"): Bank("sunday_am", SUNDAY_AM),
        ("serial", "pm"): Bank("nakshatra_pm", NAKSHATRA_PM),
    }

    WEEKDAY_THEME = {0: "marriage", 1: "career", 2: "money", 3: "health"}

    def slot(pillar, theme, topic, run):
        s = {"pillar": pillar, "theme": theme, "topic": topic,
             "lang": "hi" if run == "am" else "en"}
        guard = THEME_GUARD.get(theme)
        if guard:
            s["guard"] = guard
        return s

    d = START
    while d <= END:
        wd = d.weekday()  # 0=Mon .. 6=Sun
        entry = {"day": None, "date": d.isoformat()}

        if wd in WEEKDAY_THEME:
            theme = WEEKDAY_THEME[wd]
            entry["morning"] = slot("RL", theme, banks[(theme, "am")].take(), "am")
            entry["evening"] = slot("DD", theme, banks[(theme, "pm")].take(), "pm")
        elif wd == 4:  # Friday
            entry["morning"] = {"pillar": "TL", "theme": "timely", "topic": TL_TOPIC,
                                "lang": "hi", "verify": "drikpanchang"}
            entry["evening"] = slot("DD", "craft", banks[("craft", "pm")].take(), "pm")
        elif wd == 5:  # Saturday - MORNING ONLY, never an evening entry
            entry["morning"] = slot("DD", "literacy", banks[("saturday", "am")].take(), "am")
        else:  # Sunday
            entry["morning"] = slot("RL", "crossover", banks[("sunday", "am")].take(), "am")
            entry["evening"] = slot("NK", "serial", banks[("serial", "pm")].take(), "pm")

        days.append(entry)
        d += datetime.timedelta(days=1)

    for n, e in enumerate(days, start=1):
        e["day"] = n

    cal["days"] = days
    cal["language_policy"] = {
        "effective": "2026-08-26",
        "morning": "hi",
        "evening": "en",
        "before_effective": "hi",
        "note": ("Morning slots are Hindi in Devanagari script (never "
                 "Latin-script Hinglish). Evening slots are English from "
                 "2026-08-26 onward; Jyotish terms may stay transliterated "
                 "(Navamsa, dasha, gochar) with a one-line gloss on first use."),
    }
    cal["themes"] = {
        "marriage": "Marriage & Love (Mon)",
        "career": "Career & Business (Tue)",
        "money": "Financial Loss & Gain (Wed)",
        "health": "Health (Thu)",
        "timely": "Transit slot (Fri am) - positions must be verified on the day",
        "craft": "Technique deep-dive (Fri pm)",
        "literacy": "Myth-busting / practical literacy (Sat am, single post)",
        "crossover": "Cross-theme accessible (Sun am)",
        "serial": "Nakshatra Katha serial (Sun pm)",
    }
    cal["note"] = (
        "Extended 2026-08-13 to cover 2026-08-26 -> 2026-11-25. Four standing "
        "themes own Mon-Thu; Friday morning is the verified transit slot; "
        "Saturday is a single morning post; Sunday evening finishes the "
        "27-episode Nakshatra Katha serial. Evening slots switch to English on "
        "2026-08-26. Regenerate with scripts/extend_calendar.py."
    )
    CAL.write_text(json.dumps(cal, ensure_ascii=False, indent=1) + "\n")

    used = {k: b.i for k, b in banks.items()}
    print(f"calendar.json: {len(days)} days, {days[0]['date']} -> {days[-1]['date']}")
    print("bank usage:", ", ".join(f"{k[0]}/{k[1]}={v}" for k, v in used.items()))


if __name__ == "__main__":
    build()
