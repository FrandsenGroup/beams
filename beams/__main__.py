"""
Entry point for the application.
"""

import multiprocessing

if __name__ == '__main__':
    multiprocessing.freeze_support()

    from app.beams import BEAMS
    app = BEAMS()
    app.run()

