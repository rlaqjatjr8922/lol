def ease_in_out(t):
    return t * t * (3 - 2 * t)


def update_swap_animation(progress, speed, is_animating):
    if not is_animating:
        return progress, is_animating

    progress += speed
    if progress >= 1.0:
        progress = 1.0
        is_animating = False

    return progress, is_animating