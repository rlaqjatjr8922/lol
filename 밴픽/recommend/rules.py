def basic_rules(data):
    # 간단한 예시 추천 로직
    if not data["ally_picks"]:
        return ["Ahri", "Garen", "Lux"]
    return ["CounterPick1", "CounterPick2"]
