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
            "#ae37ff",
            "#ab8bff",
            "#bbc6e2",
            "#8fb3e0",
            '#98c8d9',
            '#92e4c3',
            '#91de73'
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
                y=-0.15,           # Adjust position to reduce the gap
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

    def convert_to_date_granularity(self, date_col ,granularity):
        if granularity == 'daily':
            self.df['period_start'] = self.df[date_col].dt.floor('D')
            self.df['period_end'] = self.df['period_start']
        elif granularity == 'weekly':
            self.df['period_start'] = self.df[date_col].dt.to_period('W').dt.start_time
            self.df['period_end'] = self.df[date_col].dt.to_period('W').dt.end_time
        elif granularity == 'monthly':
            self.df['period_start'] = self.df[date_col].dt.to_period('M').dt.start_time
            self.df['period_end'] = self.df[date_col].dt.to_period('M').dt.end_time
        else:
            raise ValueError("granularity must be one of 'daily', 'weekly', or 'monthly'.")

        # Combine the start and end into a single range string
        self.df['period'] = self.df['period_start'].dt.strftime('%Y-%m-%d') + '/' + self.df['period_end'].dt.strftime('%Y-%m-%d')

    def drop_incomplete_last_period_if_requested(self, date_col):
        
        max_period = self.df['period_end'].max()
        max_date = self.df[date_col].max()
        if max_date < max_period:
            self.df= self.df[self.df['period_end'] != max_period]

    def compile_hover_tooltip(self, agg_df, date_col, granularity):
        
        if granularity != 'daily':
            start = agg_df['period'].astype(str).str.split('/').str[0]
            end = agg_df['period'].astype(str).str.split('/').str[1]
            agg_df['hover_text'] = start + ' → ' + end
        else:
            agg_df['hover_text'] = agg_df['period'].astype(str).str.split('/').str[0]
            
        for c in [x for x in agg_df.columns if x not in [date_col,'hover_text','period','period_start']]:
            c_title = self.convert_str_2_title(c)
            if agg_df[c].dtype in ['float64', 'int64']:
                val = agg_df[c].round(2).apply(lambda x: "{:,}".format(x))
            else:
                val = agg_df[c].astype(str)
            agg_df['hover_text'] = agg_df['hover_text'] + '<br>' + c_title + ': ' + val

        return agg_df