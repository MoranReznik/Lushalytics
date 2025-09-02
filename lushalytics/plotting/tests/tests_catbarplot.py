import pandas as pd
import numpy as np
from lushalytics.plotting.CategoricalBarPlot import CatBarPlot
from plotly.subplots import make_subplots

import plotly.io as pio
pio.renderers.default = "browser"

figsize = (800, 400)

df = pd.DataFrame({
    "category": ["A","A","B","B","B","C","D","D"],
    "value":    [10,  5,  23,  2,  5,  15,  7,  3],
    "count":    [ 5,  3,   2,  1,  4,   2,  1,  3],
    "filter_col_1": ["a","a","a","b","b","b","b","b"],
    "filter_col_2": ["c","c","d","d","c","c","a","b"]
})

TEST_CREATION_TITLE_FIGSIZE = False
TEST_SORTING = False
TEST_VERICALITY = False
TEST_FILTERS = False
TEST_AGGREGATION = False
TEST_SEGMENTATION = True


if TEST_CREATION_TITLE_FIGSIZE:
    bar_plot = CatBarPlot(df, title="Test Plot")
    f = bar_plot.plot("category", "value", figsize=figsize, agg="sum")
    f.show()

if TEST_SORTING:
    custom_order = ["C", "A", "D", "B"]
    bar_plot = CatBarPlot(df, title="Sorting Tests")
    combos = [
        ("value", False, "value | normal"),
        ("value", True,  "value | reverse"),
        ("label", False, "label | normal"),
        ("label", True,  "label | reverse"),
        (custom_order, False, "custom | normal"),
        (custom_order, True,  "custom | reverse"),
    ]
    fig = make_subplots(rows=len(combos), cols=1, vertical_spacing=0.08,
                        subplot_titles=[c[2] for c in combos])
    for i, (sorting, reverse, _) in enumerate(combos, 1):
        f = bar_plot.plot("category", "value", sorting=sorting, reverse=reverse, agg="sum")
        fig.add_trace(f.data[0], row=i, col=1)
    fig.show()

if TEST_VERICALITY:
    bar_plot = CatBarPlot(df, title="Verticality Tests")
    combos = [
        (None, False, "h | no sorting"),
        ("value", False, "h | sort=value"),
        ("label", True, "h | sort=label, reverse"),
    ]
    fig = make_subplots(rows=len(combos), cols=1, vertical_spacing=0.08,
                        subplot_titles=[c[2] for c in combos])
    for i, (sorting, reverse, _) in enumerate(combos, 1):
        f = bar_plot.plot("category", "value", sorting=sorting, reverse=reverse,
                          figsize=figsize, orientation="h", agg="sum")
        fig.add_trace(f.data[0], row=i, col=1)
    fig.show()

if TEST_FILTERS:
    bar_plot = CatBarPlot(df, title="Filter Tests")
    combos = [
        ({"filter_col_1": ["a"]}, "filter_col_1 ∈ [a]"),
        ({"filter_col_2": ["c"]}, "filter_col_2 ∈ [c]"),
        ({"filter_col_1": ["a", "b"]}, "filter_col_1 ∈ [a,b]"),
        ({"category": ["A","C"]}, "category ∈ [A,C]"),
        ({"value": [23,7]}, "value ∈ [23,7]"),
        ({"category": ["B"], "filter_col_2": ["d"]}, "category ∈ [B], filter_col_2 ∈ [d]"),
    ]
    fig = make_subplots(rows=len(combos), cols=1, vertical_spacing=0.08,
                        subplot_titles=[c[1] for c in combos])
    for i, (filters, _) in enumerate(combos, 1):
        f = bar_plot.plot("category", "value", filters=filters, figsize=figsize,
                          orientation="v", agg="sum")
        fig.add_trace(f.data[0], row=i, col=1)
    fig.show()

if TEST_AGGREGATION:
    bar_plot = CatBarPlot(df, title="Aggregation Tests")
    combos = [
        ("sum",           None, "agg=sum"),
        ("mean",          None, "agg=mean"),
        ("max",           None, "agg=max"),
        ("count",         None, "agg=count"),
        ("wmean:count",   None, "agg=wmean:count"),
        ("wmean:count", {"filter_col_1":["b"]}, "agg=wmean:count | col1=b"),
    ]
    fig = make_subplots(rows=len(combos), cols=1, vertical_spacing=0.08,
                        subplot_titles=[c[2] for c in combos])
    for i, (agg, filters, _) in enumerate(combos, 1):
        f = bar_plot.plot("category", "value", agg=agg, filters=filters,
                          figsize=figsize, orientation="v", sorting="value")
        fig.add_trace(f.data[0], row=i, col=1)
    fig.show()

if TEST_SEGMENTATION:
    bar_plot = CatBarPlot(df, title="Segmentation Tests")

    combos = [
        dict(segment="filter_col_1", agg="sum",         sorting="value", reverse=False, orientation="v",
             filters=None, subtitle="STACK • seg=filter_col_1 | sum | v", segment_mode="stack"),
        dict(segment="filter_col_2", agg="sum",         sorting="label", reverse=True,  orientation="h",
             filters=None, subtitle="STACK • seg=filter_col_2 | sort=label, reverse | h", segment_mode="stack"),
        dict(segment="filter_col_1", agg="wmean:count", sorting="value", reverse=False, orientation="v",
             filters={"category": ["A","B","D"]}, subtitle="STACK • seg=filter_col_1 | wmean:count | A,B,D", segment_mode="stack"),
        dict(segment="filter_col_1", agg="sum",         sorting="value", reverse=False, orientation="v",
             filters=None, subtitle="GROUP • seg=filter_col_1 | sum | v", segment_mode="group"),
        dict(segment="filter_col_2", agg="sum",         sorting="label", reverse=True,  orientation="h",
             filters=None, subtitle="GROUP • seg=filter_col_2 | sort=label, reverse | h", segment_mode="group"),
        dict(segment="filter_col_1", agg="wmean:count", sorting="value", reverse=False, orientation="v",
             filters={"category": ["A","B","D"]}, subtitle="GROUP • seg=filter_col_1 | wmean:count | A,B,D", segment_mode="group"),
    ]

    combos_stack = [c for c in combos if c["segment_mode"] == "stack"]
    combos_group = [c for c in combos if c["segment_mode"] == "group"]

    fig_stack = make_subplots(
        rows=len(combos_stack), cols=1, vertical_spacing=0.08,
        subplot_titles=[c["subtitle"] for c in combos_stack]
    )
    for i, c in enumerate(combos_stack, 1):
        f = bar_plot.plot(
            "category", "value",
            agg=c["agg"], sorting=c["sorting"], reverse=c["reverse"],
            figsize=figsize, orientation=c["orientation"], filters=c["filters"],
            segment=c["segment"], segment_mode=c["segment_mode"]
        )
        for tr in f.data: fig_stack.add_trace(tr, row=i, col=1)
    fig_stack.update_layout(barmode="stack")
    fig_stack.show()

    fig_group = make_subplots(
        rows=len(combos_group), cols=1, vertical_spacing=0.08,
        subplot_titles=[c["subtitle"] for c in combos_group]
    )
    for i, c in enumerate(combos_group, 1):
        f = bar_plot.plot(
            "category", "value",
            agg=c["agg"], sorting=c["sorting"], reverse=c["reverse"],
            figsize=figsize, orientation=c["orientation"], filters=c["filters"],
            segment=c["segment"], segment_mode=c["segment_mode"]
        )
        for tr in f.data: fig_group.add_trace(tr, row=i, col=1)
    fig_group.update_layout(barmode="group")
    fig_group.show()