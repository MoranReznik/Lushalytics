import plotly.graph_objects as go
from .DatePlottingSuper import DatePlotter

class DateLinePlotter(DatePlotter):
    """
    A class for creating a customizable line plot comparing metrics over time with hover functionality.
    
    Initialization Parameters:
    ---------------------------
    df : pandas.DataFrame
        The DataFrame containing the data to be used for plotting.
    title : str
        The title of the plot.
    
    plot() Method Parameters:
    --------------------------
    date_col : str
        The name of the column containing dates for the x-axis.
    target_col : str or list
        The name(s) of the column(s) representing the metric(s) to plot on the y-axis.
    filters : dict, optional, default=None
        A dictionary where keys are column names and values are lists of values to keep before plotting.
    segment_col : str, optional, default=None
        The name of the column to segment data into separate traces on the plot.
        if this is used, only a single meric should be passed as 'target+col'.
    aggregator : str, optional, default='avg'
        Aggregation method for the target metric. Options: 'avg', 'sum', or 'weighted_avg'.
    count_col : str, optional, default=None
        The name of the column used for weighting when aggregator='weighted_avg'.
    granularity : str, optional, default='daily'
        The time granularity for grouping data. Options: 'daily', 'weekly', or 'monthly'.
    incomplete_drop : bool, optional, default=False
        If True, removes data from the last incomplete period (e.g., an incomplete week or month).
    days_back : int, optional, default=30
        The number of days to include in the plot, starting from today.
    
    Usage:
    ------
    1. Initialize the class with a DataFrame and a plot title.
    2. Call the plot() method with the required columns and additional configuration options to generate the plot.
    
    Returns:
    --------
    A Plotly figure object representing the generated line plot.
    """
    def __init__(self, df, title):
        
        super().__init__(df, title)

    def add_scatter_trace(self, fig, df, x_name, y_name, name, color_idx):
            fig.add_trace(go.Scatter(
                x=df[x_name],
                y=df[y_name],
                mode='lines+markers',
                line=dict(color=self.colors[color_idx], width=4),  # Line color and width
                marker=dict(size=10),  
                line_shape='spline',
                name=name,
                text=df['hover_text'],
                hoverinfo='text'
            ))

    def test_parameters_for_complience(self, aggregator, segment_col, target_col, count_col):
        
        if (aggregator not in ['avg', 'sum', 'weighted_avg']) and aggregator:
            raise ValueError("Invalid aggregator. Choose from 'avg', 'sum', or 'weighted_avg'.")

        if segment_col and isinstance(target_col, list):
            raise ValueError("Cannot add multiple target columns when segmentation is used.")

        if aggregator == 'weighted_avg' and not count_col:
            raise ValueError("count_col must be provided for weighted_avg aggregator.")

    def convert_str_2_title(self, s):
        return s.replace('_',' ').title()
    
    def plot(self, 
             date_col, 
             target_col, 
             filters=None, 
             segment_col=None, 
             aggregator=None, 
             count_col=None, 
             granularity='daily', 
             incomplete_drop=False,
             days_back=30,
             figsize=[700, 271]):

        self.test_parameters_for_complience(aggregator, segment_col, target_col, count_col)
        
        super().apply_filters(filters)

        super().trim_to_date_range(days_back, date_col)

        super().convert_to_date_granularity(date_col ,granularity)
        
        target_cols = [target_col] if isinstance(target_col, str) else target_col

        # Drop incomplete last period if requested
        if incomplete_drop and granularity in ['weekly', 'monthly']:
            super().drop_incomplete_last_period_if_requested(date_col)

        group_cols = ['period','period_start'] + ([segment_col] if segment_col else [])
        
        # Aggregation
        if aggregator == 'sum':
            sum_per_date = self.df.groupby(
                                [date_col] + ([segment_col] if segment_col else []),
                                as_index=False
                            ).agg({
                                **{col: lambda x: x.sum(min_count=1) for col in target_cols},
                                'period': 'first',
                                'period_start': 'first'
                            })
            agg_df = sum_per_date.groupby(group_cols, as_index=False)[target_cols].mean()
        elif aggregator == 'avg':
            agg_df = self.df.groupby(group_cols, as_index=False).agg({
                        **{col: 'mean' for col in target_cols},
                        count_col: 'sum'
                    })
        elif aggregator == 'weighted_avg':
            self.df['weights'] = self.df[count_col] / self.df.groupby(group_cols)[count_col].transform(lambda x: x.sum(min_count=1))
            for tc in target_cols:
                self.df[tc + '_weighted'] = self.df[tc] * self.df['weights']
            weighted_cols = [tc + '_weighted' for tc in target_cols]
            agg_df = self.df.groupby(group_cols, as_index=False).agg({
                    **{col: lambda x: x.sum(min_count=1) for col in weighted_cols},
                    count_col: 'sum'
                })
            for tc in target_cols:
                agg_df[tc] = agg_df[tc + '_weighted']
                agg_df.drop(columns=tc + '_weighted', inplace=True)
        else:
            if granularity != 'daily':
                raise ValueError('must pick an aggregator when date granularity is not daily')
            else:
                agg_df = self.df

        # compile text for hover panel
        agg_df = self.compile_hover_tooltip(agg_df, date_col, granularity)

        # Convert period back to a suitable date representation for plotting
        # We'll use the start of the period for the x-axis
        agg_df[date_col] = agg_df['period_start']
        agg_df = agg_df.sort_values(date_col)
        agg_df.drop(columns='period', inplace=True)
        self._test = agg_df
        
        fig = go.Figure()
        if segment_col:
            for i, segment in enumerate(agg_df[segment_col].unique()):
                seg_data = agg_df[agg_df[segment_col] == segment]
                self.add_scatter_trace(fig, seg_data, date_col, target_cols[0], str(segment) ,i)
        else:
            for i, tc in enumerate(target_cols):
                self.add_scatter_trace(fig, agg_df, date_col, tc, str(tc), i)
                
        # Update layout
        fig.update_layout(
            barmode='stack',
            font=dict(family="Poppins-Medium, sans-serif"),
            plot_bgcolor="white", 
            title=self.title_dict,
            yaxis = self.axis_dict,
            margin = dict(l=self.n+10, r=0, t=self.n, b=self.n),
            legend = self.legend_dict,
            legend_title=segment_col,
            hoverlabel=dict(align="left"),
            width=figsize[0],
            height=figsize[1]
        )
        if (agg_df.shape[0] / len(fig.data)) < 10:
            fig.update_layout(
                        xaxis={**self.axis_dict, 
                               "tickformat": "%b %d",  # Adds month-day formatting to the x-axis
                               'tickvals': agg_df[date_col],  # Ensure these match the x-axis data
                               'ticktext': agg_df[date_col].dt.strftime("%b %d")},  # Format as 'Dec-14'
                    )
        else:
            fig.update_layout(
                        xaxis={**self.axis_dict, 
                               "tickformat": "%b %d"}  # Adds month-day formatting to the x-axis
                    )
        return fig
    
class ErrorDateLinePlotter(DatePlotter):
    """
    A function to create a line plot comparing daily predicted values to actual values of a specified metric. 
    (can be used for any pair of metrics, for the original use is for predicted versus actual).
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The DataFrame containing the data to be plotted. This parameter is mandatory.
    title : str
        The title of the plot. This parameter is mandatory.
    
    plot() method arguments:
    ------------------------
    date_col : str
        The column name containing dates for the x-axis. This parameter is mandatory.
    actual_col : str
        The column name containing actual values for the y-axis. This parameter is mandatory.
    pred_col : str
        The column name containing predicted values for the y-axis. This parameter is mandatory.
    count_col : str
        The column name containing sample sizes (e.g., counts for each date and dimension). Used to calculate a weighted average 
        and aggregate actual and predicted values for a single value per date. This parameter is mandatory.
    filters : dict, optional, default=None
        A dictionary where keys are column names and values are lists of values to keep before plotting.
    granularity : str, optional, default='daily'
        Specifies the time granularity of the plot. Possible values are 'daily', 'weekly', or 'monthly'.
    incomplete_drop : bool, optional, default=False
        If True, removes the latest time unit (e.g., the latest week if granularity='weekly') when it is incomplete. This prevents 
        outliers caused by partial data.
    days_back : int, optional, default=30
        The number of days to include in the plot, counting back from today.
    y_range : list, optional, default=[0, 100]
        Specifies the range of the y-axis.
    
    Returns:
    --------
    A line plot visualizing the difference between predicted and actual values over time.
    """
    
    def __init__(self, df, title):

        super().__init__(df, title)
        
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

    def assign_color(self, size):
        if size <= 1_000:
            return 'red'
        elif 1_001 <= size <= 10_000:
            return 'yellow'
        else:
            return 'green'

    def convert_str_2_title(self, s):
        return s.replace('_',' ').title()
        
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
    
    def plot(self, 
             date_col, 
             actual_col, 
             pred_col,
             count_col, 
             filters=None,
             granularity='daily', 
             incomplete_drop=False,
             days_back=30,
             y_range=[0,1],
             figsize=[700, 271]):
        
        # Apply filters
        self.apply_filters(filters)

        self.trim_to_date_range(days_back, date_col)
        
        target_cols = [actual_col,pred_col]

        self.convert_to_date_granularity(date_col ,granularity)
        
        # Drop incomplete last period if requested
        if incomplete_drop and granularity in ['weekly', 'monthly']:
            self.drop_incomplete_last_period_if_requested(date_col)

        group_cols = ['period','period_start']

        # Aggregation
        self.df['weights'] = self.df[count_col] / self.df.groupby(group_cols)[count_col].transform('sum')
        for tc in target_cols:
            self.df[tc + '_weighted'] = self.df[tc] * self.df['weights']
        weighted_cols = [tc + '_weighted' for tc in target_cols] + [count_col]
        agg_df = self.df.groupby(group_cols, as_index=False)[weighted_cols].sum()
        for tc in target_cols:
            agg_df[tc] = agg_df[tc + '_weighted']
            agg_df.drop(columns=tc + '_weighted', inplace=True)

        # compile text for hover panel
        agg_df = self.compile_hover_tooltip(agg_df, date_col, granularity)
        
        # Convert period back to a suitable date representation for plotting
        # We'll use the start of the period for the x-axis
        agg_df[date_col] = agg_df['period_start']
        agg_df.drop(columns='period', inplace=True)

        agg_df['color'] = agg_df['sample_size'].apply(self.assign_color)
        
        self._test = agg_df
        fig = go.Figure()

        # Add dashed lines for errors
        for i in range(len(agg_df)):
            fig.add_trace(go.Scatter(
                x=[agg_df[date_col].iloc[i], agg_df[date_col].iloc[i]],  # Ensure vertical line on the same date
                y=[agg_df[actual_col].iloc[i], agg_df[pred_col].iloc[i]],  # From actual to predicted value
                mode='lines',
                line=dict(dash='dot', color='#4d4d4d'),
                showlegend=False
            ))
            
        # Add the actual value line and markers
        fig.add_trace(go.Scatter(
            x=agg_df[date_col],
            y=agg_df[actual_col],
            mode='lines+markers',
            line=dict(color=self.colors[0], width=4),
            marker=dict(size=10),  
            line_shape='spline',
            text=agg_df['hover_text'],
            hoverinfo='text',
            showlegend=False
        ))
        
        # Add the predicted value markers
        fig.add_trace(go.Scatter(
            x=agg_df[date_col],
            y=agg_df[pred_col],
            mode='markers',
            line=dict(color=self.colors[1], width=4),
            marker=dict(size=10, color=agg_df['color'], line=dict(color='black', width=1)),
            text=agg_df['hover_text'],
            hoverinfo='text',
            showlegend=False
        ))
                
        # Update layout
        fig.update_layout(
            barmode='stack',
            font=dict(family="Poppins-Medium, sans-serif"),
            plot_bgcolor="white", 
            title=self.title_dict,
            yaxis = {**self.axis_dict, 'range':[y_range[0], y_range[1]]},
            margin = dict(l=self.n, r=self.n, t=self.n, b=self.n),
            legend = self.legend_dict,
            hoverlabel=dict(align="left"),
            width=figsize[0],
            height=figsize[1]
        )

        fig.add_trace(
            go.Scatter(
                x=[None], 
                y=[None], 
                mode='markers',
                marker=dict(size=10, color='red', line=dict(color='black', width=1)),
                name='≤ 1,000 sample size'
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[None], 
                y=[None], 
                mode='markers',
                marker=dict(size=10, color='yellow', line=dict(color='black', width=1)),
                name='1,001 – 10,000 sample size'
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[None], 
                y=[None], 
                mode='markers',
                marker=dict(size=10, color='green', line=dict(color='black', width=1)),
                name='> 10,000 sample size'
            )
        )

        if (agg_df.shape[0]) < 10:
            fig.update_layout(
                        xaxis={**self.axis_dict, 
                               "tickformat": "%b %d",  # Adds month-day formatting to the x-axis
                               'tickvals': agg_df[date_col],  # Ensure these match the x-axis data
                               'ticktext': agg_df[date_col].dt.strftime("%b %d")},  # Format as 'Dec-14'
                    )
        else:
            fig.update_layout(
                        xaxis={**self.axis_dict, 
                               "tickformat": "%b %d"}  # Adds month-day formatting to the x-axis
                    )
        return fig
    
class DateBarPlotter(DatePlotter):

    """
    A class for creating customizable bar plots comparing metrics over time, with hover functionality and optional segmentation.
    
    Initialization Parameters:
    ---------------------------
    df : pandas.DataFrame
        The DataFrame containing the data to be used for plotting.
    title : str
        The title of the plot.
    
    plot() Method Parameters:
    --------------------------
    date_col : str
        The name of the column containing dates for the x-axis.
    target_col : str
        The name of the column representing the metric to plot on the y-axis.
    filters : dict, optional, default=None
        A dictionary where keys are column names and values are lists of values to filter before plotting.
    segment_col : str, optional, default=None
        The name of the column to segment data into separate bars on the plot.
    part_of_whole : bool, optional, default=False
        If True, calculates and displays the target metric as a percentage of the total for each time period.
    granularity : str, optional, default='daily'
        The time granularity for grouping data. Options: 'daily', 'weekly', or 'monthly'.
    incomplete_drop : bool, optional, default=False
        If True, removes data from the last incomplete period (e.g., an incomplete week or month).
    days_back : int, optional, default=30
        The number of days to include in the plot, starting from today.
    
    Usage:
    ------
    1. Initialize the class with a DataFrame and a plot title.
    2. Call the plot() method with the required columns and additional configuration options to generate the plot.
    
    Returns:
    --------
    plotly.graph_objs.Figure
        A Plotly figure object representing the generated bar plot.
    """

    def __init__(self, df, title):

        super().__init__(df, title)

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

    def convert_str_2_title(self, s):
        return s.replace('_',' ').title()
    
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
        
    def plot(self, 
                 date_col, 
                 target_col, 
                 filters = None,
                 segment_col=None,
                 part_of_whole=False,
                 granularity='daily',
                 incomplete_drop=False,
                 days_back=30,
                 figsize=[600, 271]):
        
        # Apply filters
        self.apply_filters(filters)

        self.trim_to_date_range(days_back, date_col)
        
        self.convert_to_date_granularity(date_col ,granularity)
        
        # Drop incomplete last period if requested
        if incomplete_drop and granularity in ['weekly', 'monthly']:
            self.drop_incomplete_last_period_if_requested(date_col)
            
        group_cols = ['period','period_start'] + ([segment_col] if segment_col else [])
        
        data_grouped = self.df.groupby(group_cols)[target_col].sum().reset_index()
        if segment_col:
            data_grouped[segment_col] = data_grouped[segment_col].astype(str)
        
        if part_of_whole == True:
            data_grouped[f'total_{target_col}'] = data_grouped.groupby('period')[target_col].transform('sum')
            data_grouped[f'{target_col}_percentage'] = data_grouped[target_col] / data_grouped[f'total_{target_col}'] * 100

        data_grouped = self.compile_hover_tooltip(data_grouped, date_col, granularity)
        
        # Convert period back to a suitable date representation for plotting
        # We'll use the start of the period for the x-axis
        data_grouped[date_col] = data_grouped['period_start']
        data_grouped.drop(columns='period', inplace=True)
        self.test = data_grouped
        fig = go.Figure()
        
        if segment_col:
                for i, tier in enumerate(data_grouped[segment_col].unique()):
                    tier_data = data_grouped[data_grouped[segment_col] == tier]
                    fig.add_trace(go.Bar(
                        x=tier_data[date_col],
                        y=tier_data[f'{target_col}_percentage'] if part_of_whole else tier_data[target_col],
                        name=tier,
                        marker=dict(color=self.colors[i]),
                        text=tier_data['hover_text'],  # Filtered hover text for the current tier
                        hoverinfo='text',
                        textposition="none"
                    ))
        else:
            fig.add_trace(go.Bar(
                x=data_grouped[date_col],
                y=data_grouped[f'{target_col}_percentage'] if part_of_whole else data_grouped[target_col],
                marker=dict(color=self.colors[0]),
                text=data_grouped['hover_text'],
                hoverinfo='text',
                textposition="none"
            ))

        fig.update_layout(
            barmode='stack',
            font=dict(family="Poppins-Medium, sans-serif"),
            plot_bgcolor="white", 
            title=self.title_dict,
            yaxis = self.axis_dict,
            margin = dict(l=self.n, r=self.n, t=self.n, b=self.n),
            legend = self.legend_dict,
            legend_title=segment_col,
            hoverlabel=dict(align="left"),
            width=figsize[0],
            height=figsize[1]
        )

        if (data_grouped.shape[0] / len(fig.data)) < 10:
            fig.update_layout(
                        xaxis={**self.axis_dict, 
                               "tickformat": "%b %d",  # Adds month-day formatting to the x-axis
                               'tickvals': data_grouped[date_col],  # Ensure these match the x-axis data
                               'ticktext': data_grouped[date_col].dt.strftime("%b %d")},  # Format as 'Dec-14'
                    )
        else:
            fig.update_layout(
                        xaxis={**self.axis_dict, 
                               "tickformat": "%b %d"}  # Adds month-day formatting to the x-axis
                    )
                

        return fig