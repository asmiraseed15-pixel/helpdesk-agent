import re

TAMIL = re.compile(r"[\u0B80-\u0BFF]")

# Common romanized-Tamil words. A message with 1+ of these (and no Tamil script) is Tanglish.
TANGLISH_WORDS = {
    "enna", "illa", "illai", "aagala", "aagudhu", "aaguthu", "pannunga", "pannu",
    "panna", "venum", "venam", "vendam", "irukku", "iruku", "seri", "sari", "nalla",
    "romba", "epdi", "eppadi", "yaen", "yen", "ennaku", "enaku", "naan", "nan",
    "ungal", "unga", "kudunga", "sollunga", "sollu", "vandhuchu", "vandhudhu",
    "pogala", "poguthu", "work-a", "aachu", "aagiduchu", "mudiyala", "mudiyadhu",
    "irukka", "kaattu", "paarunga", "thirumba", "podunga", "maathunga", "ah",
    "la", "ku", "kku", "nu", "na", "enga", "ethuku", "yethuku", "ippo", "ipo",
}

def detect(text: str) -> str:
    """Return 'ta' (Tamil script), 'tanglish' or 'en'."""
    if TAMIL.search(text):
        return "ta"
    words = re.findall(r"[a-zA-Z\-]+", text.lower())
    hits = sum(1 for w in words if w in TANGLISH_WORDS)
    if hits >= 1 and (hits >= 2 or len(words) <= 4):
        return "tanglish"
    return "en"

T = {
    "greeting": {
        "en": "Hi! I'm your IT helpdesk assistant. What problem are you facing? Pick one below or just type it.",
        "tanglish": "Hi! Naan ungal IT helpdesk assistant. Enna problem? Keezha select pannunga illa type pannunga.",
        "ta": "வணக்கம்! நான் உங்கள் IT helpdesk உதவியாளர். என்ன பிரச்சனை? கீழே தேர்வு செய்யுங்கள் அல்லது டைப் செய்யுங்கள்.",
    },
    "resolved": {
        "en": "Glad it's working now! Anything else I can help you with?",
        "tanglish": "Super, work aagiduchu! Vera edhaavadhu help venumaa?",
        "ta": "மகிழ்ச்சி, இப்போது வேலை செய்கிறது! வேறு ஏதாவது உதவி வேண்டுமா?",
    },
    "ticket_created": {
        "en": "Ticket #{id} created: {title}. Our IT team will contact you soon.",
        "tanglish": "Ticket #{id} create aagiduchu: {title}. IT team seekiram contact pannuvaanga.",
        "ta": "Ticket #{id} உருவாக்கப்பட்டது: {title}. IT குழு விரைவில் தொடர்பு கொள்ளும்.",
    },
    "ticket_status": {
        "en": "Ticket #{id} ({title}) is currently: {status}.",
        "tanglish": "Ticket #{id} ({title}) ippo status: {status}.",
        "ta": "Ticket #{id} ({title}) இப்போதைய நிலை: {status}.",
    },
    "ticket_missing": {
        "en": "I couldn't find ticket #{id}. Please check the number.",
        "tanglish": "Ticket #{id} kidaikkala. Number-a thirumba check pannunga.",
        "ta": "Ticket #{id} கிடைக்கவில்லை. எண்ணைச் சரிபார்க்கவும்.",
    },
}

def t(key: str, lang: str, **kw) -> str:
    return T[key][lang].format(**kw)
