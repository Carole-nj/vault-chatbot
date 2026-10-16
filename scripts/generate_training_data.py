"""Generate the labelled training dataset (CSV) for the Vault Electronics intent classifier.

Seed phrasings are expanded with polite prefixes/suffixes and light typo noise.
IMPORTANT: this gives a strong starting set, but real accuracy comes from adding real
customer enquiries (WhatsApp, email, phone notes) to data/seed_extra.csv and retraining.
"""
import csv
import random
import re
from pathlib import Path

random.seed(42)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "training_data.csv"
EXTRA = ROOT / "data" / "seed_extra.csv"  # optional: columns text,intent
TARGET_PER_INTENT = 135

SEEDS = {
    "greeting": ["hi", "hello", "hey there", "good morning", "good afternoon", "good evening", "hello vault", "hi there", "anyone there", "hey", "habari", "jambo"],
    "goodbye": ["bye", "goodbye", "see you later", "that is all for now", "talk to you later", "i am leaving now", "have a nice day", "ok bye", "cheers bye", "i have to go"],
    "thanks": ["thanks", "thank you", "thank you so much", "thanks a lot", "much appreciated", "great thanks for the help", "asante", "that was helpful thanks", "awesome thank you", "perfect thanks"],
    "about_company": ["tell me about vault electronics", "who are you", "what does your company do", "when was vault electronics established", "how long have you been in business", "what services do you offer", "tell me about your company", "what is vault electronics", "how many years of experience do you have", "what do you specialise in", "who is vault electronics", "what is your company background"],
    "location": ["where is your office in nairobi", "where are you located", "what is your address", "do you have an office in nanyuki", "where is the karen road office", "how do i get to your office", "can i visit your showroom", "which town are you in", "directions to your office", "where can i find you", "do you have a physical shop", "your location please"],
    "contact": ["what is your phone number", "how can i contact you", "give me your contact details", "i want to talk to someone", "can i speak to a sales person", "what is your whatsapp number", "how do i reach your team", "i need a human agent", "call me back", "do you have an email address", "customer care number", "how do i get in touch with sales"],
    "working_hours": ["what are your working hours", "when are you open", "are you open on saturday", "what time do you close", "do you work on weekends", "opening hours please", "are you open today", "what time do you open", "business hours", "are you open on public holidays", "when can i call your office"],
    "uae_presence": ["do you operate in the uae", "are you in dubai", "do you have an office in the uae", "can you serve clients in abu dhabi", "do you install in the united arab emirates", "uae contact number", "do you do projects outside kenya", "is there a vault electronics in dubai", "do you work in the emirates", "do you ship to the uae"],
    "clients": ["who are your clients", "which schools have you worked with", "do you have client references", "have you worked with peponi house", "do you work with durham international school", "have you done projects for ilri", "can you show me past projects", "which organisations use your products", "do you have any testimonials", "who have you installed for before", "do you serve churches", "do you work with government agencies"],
    "pricing": ["what is the price of the vtouch panel", "how much is a 75 inch interactive panel", "how much does cctv cost", "what are your prices", "price list please", "how much is an 86 inch panel", "cost of video conferencing system", "how much for digital signage", "what does a smart classroom cost", "how much is a digital kiosk", "price of 65 inch interactive flat panel", "how much do you charge", "what is the cost of a digital podium", "is it expensive", "give me the price"],
    "demo_request": ["can i get a demo for video conferencing", "i would like a free demo", "can you demonstrate the interactive panel", "book a demo", "do you offer free demos", "i want to see the product in action", "can i test the panel before buying", "arrange a demo at our school", "schedule a product demonstration", "can you bring a demo unit to our office", "request a demo", "demo of digital signage"],
    "consultation": ["i need a consultation", "can someone advise me on what to buy", "i need help choosing a solution", "can i book a consultation", "do you do site visits", "can an engineer visit our premises", "we need advice on av for our boardroom", "i want expert advice", "can you assess our building", "free consultation please", "site survey request"],
    "special_offers": ["do you have any special offers", "any discounts available", "are there promotions", "current deals please", "do you offer bulk discounts", "any offers on interactive panels", "do you have a sale", "is there a discount for schools", "what offers are running now", "any promo this month"],
    "interactive_flat_panels": ["do you have a 75 inch interactive panel", "tell me about interactive flat panels", "what sizes of interactive panels do you have", "do you sell 86 inch panels", "i need a 65 inch interactive display", "what is the specs of your interactive panel", "which interactive boards do you sell", "do you have smart boards", "interactive whiteboard for my classroom", "touch screen display for teaching", "which brands of interactive panels do you stock", "tell me about the vtouch panel"],
    "video_conferencing": ["do you have video conferencing systems", "i need a video conferencing setup for my boardroom", "what video conference equipment do you sell", "zoom room setup", "teams meeting room solution", "video call equipment for meeting room", "conference camera and microphone", "do you install video conferencing", "hybrid meeting room solutions", "conference room av setup", "tell me about your video conferencing"],
    "smart_classrooms": ["do you serve schools in nanyuki", "tell me about smart classrooms", "i want to make my classroom digital", "smart classroom solution for my school", "what do you offer for schools", "edtech solutions for schools", "digital learning equipment for classrooms", "do you equip schools", "technology for teaching", "how can you help our school go digital", "classroom technology packages"],
    "digital_signage": ["do you do digital signage", "i need digital signage for my shop", "advertising display screens", "digital notice board for office", "menu board screens", "tell me about digital signage solutions", "screens for displaying adverts", "digital display for reception", "video wall for lobby", "digital signage for church", "how does digital signage work"],
    "cctv_security": ["do you install cctv", "how long does cctv installation take", "i need security cameras", "cctv system for my business", "do you sell surveillance cameras", "security camera installation", "i want cctv for my school", "tell me about your security systems", "ip cameras for my premises", "do you offer cctv maintenance", "home cctv package", "how many cameras do i need"],
    "digital_kiosks": ["do you sell digital kiosks", "tell me about digital kiosks", "self service kiosk", "information kiosk for my office", "touch kiosk for visitors", "wayfinding kiosk", "interactive kiosk for reception", "what kiosks do you have", "kiosk for a school", "kiosk for a shopping mall"],
    "digital_podiums": ["do you have digital podiums", "tell me about smart lecterns", "digital podium for lecture hall", "smart podium for auditorium", "what is a digital podium", "podium with built in screen", "lectern with touch display", "podium for conference room", "do you sell smart podiums", "digital lectern for church"],
    "structured_cabling": ["do you do structured cabling", "network cabling for my office", "av integration services", "can you do cat6 cabling", "system integration for building", "cabling for new office", "network points installation", "do you do fibre cabling", "av and network integration", "tidy up cabling in server room"],
    "smart_workspaces": ["tell me about smart workspaces", "modern office technology solutions", "meeting room booking and display", "collaboration tools for our office", "make my office smart", "wireless presentation system for meeting rooms", "huddle room technology", "smart office av setup", "workspace collaboration displays", "hybrid workspace solutions"],
    "installation": ["how long does installation take", "do you install the products", "installation services", "how long will it take to install the panel", "do you mount the screens on the wall", "who will install the equipment", "installation timeline", "do you offer free installation", "can you install in nanyuki", "how many days to set up a classroom", "is installation included", "installation cost"],
    "maintenance_support": ["do you offer after sales support", "my system is not working", "i need technical support", "do you provide maintenance", "who do i call for repairs", "my panel has a problem", "system maintenance contract", "support after installation", "how do i report a fault", "do you service what you install", "customer support number", "my cctv stopped working"],
    "warranty": ["what is the warranty", "how long is the warranty on panels", "warranty terms", "is there a guarantee on products", "what does your warranty cover", "do the products come with a warranty", "warranty period for cctv", "how long is the guarantee", "what happens if the panel fails under warranty", "is warranty included in price"],
    "website_navigation": ["where can i find your products on the website", "how do i see all categories", "where is the contact page", "show me your products page", "where do i find offers on your website", "link to your website", "how do i navigate your site", "where can i download the catalogue", "which page has product details", "take me to the products page"],
    "quote_request": ["i need a quotation", "how do i request a quote", "send me a quote", "can i get a quotation for 10 panels", "quote for cctv installation", "request a quotation for a smart classroom", "i would like a formal quote", "prepare a quote for our school", "how do i get a quotation", "quote for video conferencing room"],
    "project_management": ["do you manage projects", "tell me about your project management", "who will manage our installation project", "do you handle the whole project", "end to end project delivery", "do you do turnkey projects", "project management services", "can you handle design supply and installation", "do you provide a project manager", "how do you manage large installations"],
}

PREFIXES = ["", "", "", "hi ", "hello ", "hey ", "please ", "good morning ", "i wanted to ask ", "quick question ", "i would like to know ", "excuse me "]
SUFFIXES = ["", "", "", "", " please", " thanks", " asap", " today", " if possible"]


def typo(text: str) -> str:
    words = text.split()
    cands = [i for i, w in enumerate(words) if len(w) > 4]
    if not cands:
        return text
    i = random.choice(cands)
    w = words[i]
    p = random.randrange(1, len(w) - 1)
    kind = random.choice(["drop", "swap", "dup"])
    if kind == "drop":
        w = w[:p] + w[p + 1:]
    elif kind == "swap":
        w = w[:p] + w[p + 1] + w[p] + w[p + 2:]
    else:
        w = w[:p] + w[p] + w[p:]
    words[i] = w
    return " ".join(words)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def main():
    rows, seen = [], set()
    for intent, phrases in SEEDS.items():
        local = set()
        for p in phrases:  # always keep the clean seeds
            local.add(norm(p))
        attempts = 0
        while len(local) < TARGET_PER_INTENT and attempts < 20000:
            attempts += 1
            t = random.choice(PREFIXES) + random.choice(phrases) + random.choice(SUFFIXES)
            if random.random() < 0.2:
                t = typo(t)
            local.add(norm(t))
        for t in sorted(local):
            if t not in seen:
                seen.add(t)
                rows.append((t, intent))
    if EXTRA.exists():
        with open(EXTRA, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                t = norm(r["text"])
                if t and t not in seen and r["intent"] in SEEDS:
                    seen.add(t)
                    rows.append((t, r["intent"]))
    random.shuffle(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["text", "intent"])
        w.writerows(rows)
    print(f"Wrote {len(rows)} examples across {len(SEEDS)} intents -> {OUT}")


if __name__ == "__main__":
    main()
