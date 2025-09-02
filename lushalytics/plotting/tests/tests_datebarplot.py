import pandas as pd
import numpy as np
from datetime import datetime
from lushalytics.plotting.DatePlotingClasses import DateBarPlotter

import plotly.io as pio
pio.renderers.default = "browser"

labels = ['A', 'B','D','E','F','G','C','X','Z']

# Toy dataset
np.random.seed(0)
date_range = pd.date_range(end=datetime.today(), periods=90)
data = {
    'date': np.random.choice(date_range, 500),
    'category': np.random.choice(labels, 500),
    'value_1': np.random.normal(1900, 100, 500),
    'value_2': np.random.normal(200, 20, 500),
    'count_1': np.random.randint(1, 10, 500),
    'count_2': np.random.randint(1, 20, 500),
}
df = pd.DataFrame(data)

plotter2 = DateBarPlotter(df.copy(), "Daily Value 1")
f2 = plotter2.plot(
    date_col="date",
    target_col="value_1",
    granularity="daily"
)
f2.show()

plotter3 = DateBarPlotter(df.copy(), "Weekly Share of Value 2 by Category")
f3 = plotter3.plot(
    date_col="date",
    target_col="value_2",
    segment_col="category",
    part_of_whole=True,
    granularity="weekly",
    days_back=90
)
f3.show()

plotter4 = DateBarPlotter(df.copy(), "Monthly Count 1 for A & B")
f4 = plotter4.plot(
    date_col="date",
    target_col="count_1",
    filters={"category": ["A", "B"]},
    granularity="monthly"
)
f4.show()

plotter5 = DateBarPlotter(df.copy(), "Daily Value 1 (Last 14 Days)")
f5 = plotter5.plot(
    date_col="date",
    target_col="value_1",
    days_back=14,
    y_range=[1500, 2300]
)
f5.show()