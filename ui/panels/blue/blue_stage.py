def trigger_swap_to_stage2(state):
    state.progress = 0.0
    state.is_animating = True
    state.mode = "original"
    state.animation_target_mode = "swapped"


def trigger_swap_to_stage3(state):
    state.progress = 0.0
    state.is_animating = True
    state.mode = "swapped"
    state.animation_target_mode = "original"


def sync_stage_layout(state, stage):
    state.is_animating = False

    if stage in (0, 1, 4):
        state.progress = 0.0
        state.mode = "original"
        state.animation_target_mode = "original"
    elif stage == 2:
        state.progress = 1.0
        state.mode = "swapped"
        state.animation_target_mode = "swapped"
    elif stage == 3:
        state.progress = 0.0
        state.mode = "original"
        state.animation_target_mode = "original"
