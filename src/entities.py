"""
Entity definitions for the Local Wikipedia RAG Assistant.
Contains 20 famous people and 20 famous places with their Wikipedia URLs.
"""

# 10 required people + 10 additional people = 20 total
PEOPLE = [
    # --- Required 10 ---
    {"name": "Albert Einstein", "url": "https://en.wikipedia.org/wiki/Albert_Einstein"},
    {"name": "Marie Curie", "url": "https://en.wikipedia.org/wiki/Marie_Curie"},
    {"name": "Leonardo da Vinci", "url": "https://en.wikipedia.org/wiki/Leonardo_da_Vinci"},
    {"name": "William Shakespeare", "url": "https://en.wikipedia.org/wiki/William_Shakespeare"},
    {"name": "Ada Lovelace", "url": "https://en.wikipedia.org/wiki/Ada_Lovelace"},
    {"name": "Nikola Tesla", "url": "https://en.wikipedia.org/wiki/Nikola_Tesla"},
    {"name": "Lionel Messi", "url": "https://en.wikipedia.org/wiki/Lionel_Messi"},
    {"name": "Cristiano Ronaldo", "url": "https://en.wikipedia.org/wiki/Cristiano_Ronaldo"},
    {"name": "Taylor Swift", "url": "https://en.wikipedia.org/wiki/Taylor_Swift"},
    {"name": "Frida Kahlo", "url": "https://en.wikipedia.org/wiki/Frida_Kahlo"},
    # --- Additional 10 ---
    {"name": "Isaac Newton", "url": "https://en.wikipedia.org/wiki/Isaac_Newton"},
    {"name": "Cleopatra", "url": "https://en.wikipedia.org/wiki/Cleopatra"},
    {"name": "Mahatma Gandhi", "url": "https://en.wikipedia.org/wiki/Mahatma_Gandhi"},
    {"name": "Martin Luther King Jr.", "url": "https://en.wikipedia.org/wiki/Martin_Luther_King_Jr."},
    {"name": "Napoleon Bonaparte", "url": "https://en.wikipedia.org/wiki/Napoleon"},
    {"name": "Mozart", "url": "https://en.wikipedia.org/wiki/Wolfgang_Amadeus_Mozart"},
    {"name": "Aristotle", "url": "https://en.wikipedia.org/wiki/Aristotle"},
    {"name": "Charles Darwin", "url": "https://en.wikipedia.org/wiki/Charles_Darwin"},
    {"name": "Nelson Mandela", "url": "https://en.wikipedia.org/wiki/Nelson_Mandela"},
    {"name": "Amelia Earhart", "url": "https://en.wikipedia.org/wiki/Amelia_Earhart"},
]

# 10 required places + 10 additional places = 20 total
PLACES = [
    # --- Required 10 ---
    {"name": "Eiffel Tower", "url": "https://en.wikipedia.org/wiki/Eiffel_Tower"},
    {"name": "Great Wall of China", "url": "https://en.wikipedia.org/wiki/Great_Wall_of_China"},
    {"name": "Taj Mahal", "url": "https://en.wikipedia.org/wiki/Taj_Mahal"},
    {"name": "Grand Canyon", "url": "https://en.wikipedia.org/wiki/Grand_Canyon"},
    {"name": "Machu Picchu", "url": "https://en.wikipedia.org/wiki/Machu_Picchu"},
    {"name": "Colosseum", "url": "https://en.wikipedia.org/wiki/Colosseum"},
    {"name": "Hagia Sophia", "url": "https://en.wikipedia.org/wiki/Hagia_Sophia"},
    {"name": "Statue of Liberty", "url": "https://en.wikipedia.org/wiki/Statue_of_Liberty"},
    {"name": "Pyramids of Giza", "url": "https://en.wikipedia.org/wiki/Great_Pyramid_of_Giza"},
    {"name": "Mount Everest", "url": "https://en.wikipedia.org/wiki/Mount_Everest"},
    # --- Additional 10 ---
    {"name": "Stonehenge", "url": "https://en.wikipedia.org/wiki/Stonehenge"},
    {"name": "Petra", "url": "https://en.wikipedia.org/wiki/Petra"},
    {"name": "Angkor Wat", "url": "https://en.wikipedia.org/wiki/Angkor_Wat"},
    {"name": "Christ the Redeemer", "url": "https://en.wikipedia.org/wiki/Christ_the_Redeemer_(statue)"},
    {"name": "Great Barrier Reef", "url": "https://en.wikipedia.org/wiki/Great_Barrier_Reef"},
    {"name": "Niagara Falls", "url": "https://en.wikipedia.org/wiki/Niagara_Falls"},
    {"name": "Chichen Itza", "url": "https://en.wikipedia.org/wiki/Chichen_Itza"},
    {"name": "Acropolis of Athens", "url": "https://en.wikipedia.org/wiki/Acropolis_of_Athens"},
    {"name": "Mount Fuji", "url": "https://en.wikipedia.org/wiki/Mount_Fuji"},
    {"name": "Victoria Falls", "url": "https://en.wikipedia.org/wiki/Victoria_Falls"},
]


def get_all_entities():
    """Return all entities with their type annotation."""
    entities = []
    for person in PEOPLE:
        entities.append({**person, "type": "person"})
    for place in PLACES:
        entities.append({**place, "type": "place"})
    return entities
