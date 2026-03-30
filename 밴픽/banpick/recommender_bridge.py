def should_run_recommend(snapshot):
    return (
        snapshot.state.phase == "pick"
        and snapshot.state.is_my_turn
    )


def build_recommend_input(snapshot):
    return {
        "ally_picks": [x.name for x in snapshot.ally_picks if x.name],
        "enemy_picks": [x.name for x in snapshot.enemy_picks if x.name],
        "ally_bans": [x.name for x in snapshot.ally_bans if x.name],
        "enemy_bans": [x.name for x in snapshot.enemy_bans if x.name],
        "hover_pick": snapshot.hover_pick.name if snapshot.hover_pick else "",
    }