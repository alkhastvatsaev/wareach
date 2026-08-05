"""French consumer / buyer discovery seeds — Phase 2 (no Firecrawl)."""


def fr_consumer_queries() -> list[dict]:
    queries: list[dict] = []
    seen: set[str] = set()

    def add(brand: str, query: str, priority: int = 200):
        if query in seen:
            return
        seen.add(query)
        queries.append({"brand": brand, "query": query, "priority": priority, "category": "consumer_fr"})

    rep_subs = "fashionreps OR repladies OR designerreps"
    for brand, terms in [
        ("hermes", ["hermes", "birkin", "kelly"]),
        ("louis_vuitton", ["louis vuitton", "LV", "neverfull"]),
        ("chanel", ["chanel", "CF bag"]),
        ("cartier", ["cartier", "love bracelet"]),
        ("van_cleef_arpels", ["van cleef", "alhambra", "VCA"]),
        ("dior", ["dior", "book tote"]),
        ("gucci", ["gucci"]),
    ]:
        for t in terms:
            add(brand, f"{t} france pandabuy {rep_subs}", 240)
            add(brand, f"{t} cssbuy shipping france", 225)
            add(brand, f"comment commander {t} yupoo france", 220)

    generics = [
        "guide yupoo français pandabuy",
        "réplique hermès france agent",
        "fausse cartier livraison france",
        "replique sac louis vuitton france douane",
        "van cleef réplique france telegram",
        "W2C france hermes fashionreps",
        "haul france fashionreps",
        "colissimo replica bag france",
        "douane france réplique sac",
        "premier achat pandabuy france",
        "repsfrench",
        "meilleur agent france 2025 replica",
        "telegram france replica luxury",
    ]
    for q in generics:
        add("multi", q, 235)

    return sorted(queries, key=lambda x: -x["priority"])
