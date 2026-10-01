"""
Module providing tools and routings for easy data plotting for simple
visual verifications.
"""
from typing import Any

import dearpygui.dearpygui as dpg
import os

import multiprocessing
import pandas as pd
import numpy as np


multiprocessing.set_start_method('spawn', force=True)


GAP_FILL_MARKERS_FILL_COLOR = [255, 0, 0, 255]
GAP_FILL_MARKERS_OUTLINE_COLOR = [20, 0, 0, 255]
HIGHLIGHT_COLOR = [255, 255, 255, 255]

item_pairs = {}
active_pair = None

DEFAULT_THEME = dpg.theme()
HIGHLIGHT_THEME = dpg.theme()


class Plot:
    """A basic DearPyGUI data plotter.
    """

    markers = ["━", "■"]

    def __init__(self, title: str) -> None:
        self.data = []

        dpg.create_context()

        dpg.add_window(width=600, height=400, tag="main_window")
        dpg.add_group(tag="window_group", parent="main_window",
                      horizontal=True)

        # First in the group to be left side.
        # self.legend = Legend("Legend", "window_group")

        # Second in the group to be right side.
        dpg.add_plot(label=title, parent="window_group",
                     height=-1, width=-1, tag="plot")
        dpg.add_plot_legend(parent="plot")

        dpg.add_plot_axis(dpg.mvXAxis, tag="x_axis", parent="plot", time=True)
        dpg.add_plot_axis(dpg.mvYAxis, tag="y_axis", parent="plot")

        # Define global theme,
        dpg.add_theme(tag="default_theme")

        with dpg.theme_component(dpg.mvText, parent="default_theme"): # type: ignore
            dpg.add_theme_color(dpg.mvThemeCol_Text, (180, 180, 180, 255))

        dpg.bind_item_theme("plot", "default_theme")

        # Define highlight theme for hovered data.
        dpg.add_theme(tag="highlight_theme")

        with dpg.theme_component(dpg.mvText, parent="highlight_theme"): # type: ignore
            dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 215, 0, 255))
            dpg.add_theme_color(dpg.mvPlotCol_Line, (255, 215, 0, 255))

        self._callback = None
        self.__counter = 0

    @property
    def _counter(self) -> int:
        self.__counter += 1
        return self.__counter

    def to_datetime(self, x: list | np.ndarray | pd.Index | np.datetime64) -> list:
        x = np.array(x)
        return (x.astype("datetime64[us]")
                 .astype("int64") / 1e6).tolist()

    def add_line(self, x_data: list | pd.Index | np.datetime64,
                 y_data: list | np.ndarray | pd.Series, title: str,
                 color: tuple | None = None,
                 weight: int | None = None):

        x_data = self.to_datetime(x_data)
        y_data = list(y_data)

        # Add line to plot.
        dpg.add_line_series(x_data, y_data,
                            parent="y_axis", tag=title, label=title)

        
        if any([color, weight]):
            theme = dpg.add_theme(tag=title+"theme")
        
            if color is not None:
                with dpg.theme_component(dpg.mvLineSeries, parent=theme): # type: ignore
                    dpg.add_theme_color(
                        dpg.mvPlotCol_Line,
                        color,
                        category=dpg.mvThemeCat_Plots
                    )

            if weight is not None:
                with dpg.theme_component(dpg.mvLineSeries, parent=theme): # type: ignore
                    dpg.add_theme_style(
                        dpg.mvPlotStyleVar_LineWeight,
                        weight,
                        category=dpg.mvThemeCat_Plots
                    )

            dpg.bind_item_theme(title, theme)

    def add_scatter(self, x_data, y_data, title,
                    fill_color = None,
                    outline_color = None,
                    outline_weight = None,
                    size = None):
        x_data = self.to_datetime(x_data)
        y_data = list(y_data)
        # Add line to plot.
        dpg.add_scatter_series(x_data, y_data, parent="y_axis", tag=title,
                               label=title)

        if any([fill_color, outline_weight, outline_color]):
            theme = dpg.add_theme(tag=title+"theme")

            if fill_color is not None:
                with dpg.theme_component(dpg.mvScatterSeries, parent=theme): # type: ignore
                    dpg.add_theme_color(
                        dpg.mvPlotCol_MarkerFill,
                        fill_color,
                        category=dpg.mvThemeCat_Plots
                    )
            if outline_color is not None:
                with dpg.theme_component(dpg.mvScatterSeries, parent=theme): # type: ignore
                    dpg.add_theme_color(
                        dpg.mvPlotCol_MarkerOutline,
                        outline_color,
                        category=dpg.mvThemeCat_Plots
                    )
            if outline_weight is not None:
                with dpg.theme_component(dpg.mvScatterSeries, parent=theme): # type: ignore
                    dpg.add_theme_style(
                        dpg.mvPlotStyleVar_MarkerWeight, 
                        outline_weight, 
                        category=dpg.mvThemeCat_Plots
                    )

            if size is not None:
                with dpg.theme_component(dpg.mvScatterSeries, parent=theme): # type: ignore
                    dpg.add_theme_style(
                        dpg.mvPlotStyleVar_MarkerSize, 
                        size, 
                        category=dpg.mvThemeCat_Plots
                    )
        
            dpg.bind_item_theme(title, theme)

    def show(self):
        dpg.create_viewport(title=os.environ.get("app-name") or "window",
                            width=600, height=400, resizable=True)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()

        dpg.destroy_context()


class PlotterMP(Plot):
    """Phantom wrapper of a real plotter implementation. Communication API
    for a plotter running in another process.
    """
    def __init__(self, title: str) -> None:
        self._q = multiprocessing.Queue()
        self.process = multiprocessing.Process(target=self._process,
                                               args=(title, self._q))
        self.process.start()

    @staticmethod
    def _process(title, queue):
        plotter = Plot(title=title)
        action = None
        while action != 'show':
            action, args = queue.get()
            getattr(plotter, action)(*args)

    def add_line(self, x_data: list | pd.Index | np.datetime64,
                 y_data: list | np.ndarray[tuple[Any, ...], np.dtype[Any]] | pd.Series,
                 title: str, color: tuple | None = None, weight: int | None = None):
        self._q.put(("add_line", (x_data, y_data, title, color, weight)))

    def add_scatter(self, x_data, y_data, title, fill_color=None, outline_color=None, outline_weight=None, size=None):
        self._q.put(("add_scatter", (x_data, y_data, title, fill_color, outline_color, outline_weight)))

    def show(self):
        self._q.put(("show", tuple()))


class Legend:
    """Instantiate inside a plot context.
    """

    def __init__(self, title: str, parent: int | str) -> None:
        # Vertical legend card.
        # Horizontal == On side of plot.
        dpg.add_child_window(width=120, height=-1, tag='legend_window',
                             parent=parent, label=title)
        dpg.add_text(title, color=(200, 200, 200, 255),
                     parent="legend_window", )
        dpg.add_separator(parent="legend_window")
        dpg.add_theme(tag="legend_theme")
        dpg.add_theme_component(dpg.mvThemeCol_ChildBg,
                                parent="legend_theme",
                                tag="background_component")
        dpg.add_theme_color(dpg.mvThemeCol_ChildBg,
                            (80, 80, 80, 255),
                            parent="background_component")
        dpg.add_theme_color(dpg.mvThemeCol_Border,
                            (80, 100, 130, 255),
                            parent="background_component")
        dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 6.0,
                            parent="background_component")

        # Bind the theme to the legend child window.
        dpg.bind_item_theme("legend_window", "legend_theme")

        # Internal counter.
        self._entry_id = 0

    def add_entry(self, name, marker, color):
        with dpg.group(parent="legend_window", horizontal=True,
                       tag=f"legend_{name}"): # type: ignore
            dpg.add_text(marker, color=color, )
            dpg.add_text(name, color=(200, 200, 200, 255))
