# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
@auhtor: Zlatko K. Minev
@date: 2020
"""

import matplotlib.pyplot as plt
from PyQt5.QtCore import QTimer

from ...._gui.utility._handle_qt_messages import catch_exception_slot_pyqt


class AnimatedText():
    def __init__(self, ax: plt.Axes, text: str, canvas, kw: dict = None,
                 anim_start=0.9,
                 anim_dt_ms=25,
                 anim_delta=-0.0005,
                 anim_stop=0,
                 anim_accel=-0.0005,
                 start=True,
                 loc=[0.5, 0.5]):

        self.canvas = canvas
        self.ax = ax
        self.anim_value = anim_start
        self.anim_delta = anim_delta
        self.anim_dt_ms = anim_dt_ms
        self.anim_stop = anim_stop
        self.anim_accel = anim_accel
        self.anim_veloc = 0

        # MPL text
        # Create the text
        kw = {**dict(fontsize=35, fontweight='bold', va='center', ha='center', alpha=anim_start,
                     transform=ax.transAxes, color='#00356B', zorder=200),
              **(kw if kw else {})}

        self.text = ax.text(*loc, text, **kw)

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_tick)

        if start:
            self.start()

    def start(self):
        self.timer.start(self.anim_dt_ms)

    def stop(self):
        self.timer.start()

    @catch_exception_slot_pyqt()
    def timer_tick(self):
        # Update anim position value
        self.anim_veloc += self.anim_accel  # acceleration on vellcoity update
        self.anim_value += self.anim_delta + self.anim_veloc  # update position
        # print(f'tick {self.anim_value}')

        if self.anim_value >= self.anim_stop:  # one sided
            self.text.set_alpha(self.anim_value)
            if self.text not in self.ax.texts:
                # if the axis is cleared and redrawn
                self.ax.texts.append(self.text)
            self.canvas.refresh()  # refresht the canvas

        else:
            self.timer.stop()
            self.timer.deleteLater()

            # Remove artist
            self.text.figure = self.ax.figure
            if self.text in self.ax.texts:
                self.ax.texts.remove(self.text)

            if self.text.axes:
                try:
                    # remove text from axis
                    self.text.remove()
                except ValueError as e:
                    # could raise ValueError: list.remove(x): x not in list
                    pass

            self.canvas.refresh()  # refresht the canvas
