import pandas as pd
from datetime import datetime, timedelta

class DatePlotter():

    def __init__(self, df, title):

        self.df = df.copy()
        
        self.title_dict = dict(
                    text=title.title(),
                    font=dict(color="#AE37FF"),
                    x=0
                )
        
        self.n = 35
        
        self.colors = [
            "#ae37ff", "#ab8bff", "#bbc6e2",
            "#8fb3e0", "#98c8d9", "#92e4c3",
            "#91de73", "#bdf07f", "#e5f993"
        ]

        self.axis_dict = dict(
                showline=True, 
                linewidth=2, 
                linecolor='rgba(0, 0, 0, 0.2)', 
                mirror=False, 
                title=None, 
                automargin=False,
                tickfont=dict(size=9)
            )
        self.legend_dict = dict(
                orientation="h",  # Horizontal legend
                yanchor="top",    # Align legend closer to the top of its container
                y=-0.15,          # Adjust position to reduce the gap
                xanchor="center",
                x=0.5,
                font=dict(size=12)
            )
        
    def apply_filters(self, filters):
        df = self.df
        if filters:
            for col, values in filters.items():
                df = df[df[col].isin(values)]
        self.df = df

    def trim_to_date_range(self, days_back, date_col):
        self.df[date_col] = pd.to_datetime(self.df[date_col])
        start_date = datetime.now() - timedelta(days=days_back)
        end_date = datetime.now()
        self.df = self.df[(self.df[date_col] >= start_date) & (self.df[date_col] <= end_date)]

    def convert_to_date_granularity(self, date_col, granularity):
        if granularity == 'daily':
            self.df['period_start'] = self.df[date_col].dt.floor('D')
            self.df['period_end'] = self.df['period_start']
        elif granularity == 'weekly':
            self.df['period_start'] = self.df[date_col].dt.to_period('W').dt.start_time.dt.floor('D')
            self.df['period_end'] = self.df[date_col].dt.to_period('W').dt.end_time.dt.floor('D')
        elif granularity == 'monthly':
            self.df['period_start'] = self.df[date_col].dt.to_period('M').dt.start_time.dt.floor('D')
            self.df['period_end'] = self.df[date_col].dt.to_period('M').dt.end_time.dt.floor('D')
        else:
            raise ValueError("granularity must be one of 'daily', 'weekly', or 'monthly'.")

    def drop_incomplete_last_period_if_requested(self, date_col):
        
        self.df['period_end'] = pd.to_datetime(self.df['period_end']).dt.date
        self.df[date_col] = pd.to_datetime(self.df[date_col]).dt.date
        
        self.df['period_end'] = pd.to_datetime(self.df['period_end']).dt.date
        self.df[date_col] = pd.to_datetime(self.df[date_col]).dt.date
        
        max_period = self.df['period_end'].max()
        max_date = self.df[date_col].max()
        if max_date < max_period:
            self.df = self.df[self.df['period_end'] != max_period]
    
    # This helper function is now in DateLinePlotter, as it's used there.
    def convert_str_2_title(self, s):
        if s is None:
            return ""
        return s.replace('_',' ').title()