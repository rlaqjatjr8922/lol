def resolve_my_team(is_blue_side=True):
    return "team1" if is_blue_side else "team2"


def apply_my_team_to_state(state, my_team):
    state.my_team = my_team
    state.is_my_turn = (state.current_team == my_team)
    return state