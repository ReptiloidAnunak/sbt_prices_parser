from rapidfuzz import process, fuzz


def normalize(s: str) -> str:
    return s.upper().replace("X", "").replace("  ", " ").strip()

def match_product(name, choices, threshold=85):
    name_n = normalize(name)

    match = process.extractOne(
        name_n,
        choices,
        scorer=fuzz.token_sort_ratio
    )

    if not match:
        return None

    best_match, score, idx = match

    if score < threshold:
        return None

    return {
        "input": name,
        "matched": best_match,
        "score": score
    }