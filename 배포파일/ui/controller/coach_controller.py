from ui.view.coach_view import CoachView
from ui.controller.pregame_controller import PregameController


def run_full_app():
    view = CoachView()
    PregameController(view)
    view.mainloop() 