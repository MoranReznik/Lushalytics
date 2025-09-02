import plotly.graph_objects as go
from .DatePlottingSuper import DatePlotter
import pandas as pd 

class DateLinePlotter(DatePlotter):

    def __init__(self, df, title):

        super().__init__(df, title)
        

    def add_scatter_trace(self, fig, df, x_name, y_name, name, color, hover_text):
        fig.add_trace(go.Scatter(
            x=df[x_name],
            y=df[y_name],
            mode='lines+markers',
            line=dict(color=color, width=4),
            marker=dict(size=10),  
            line_shape='spline',
            name=name.replace("_", " "),
            hovertext=hover_text,
            hovertemplate='%{hovertext}<extra></extra>'
        ))

    def _create_trace_tooltip(self, trace_df, granularity, trace_name, value_col, other_cols_to_include=None):
        """Generates a formatted hover tooltip for a specific trace."""

        trace_df = trace_df.copy()
        trace_df['period_start'] = pd.to_datetime(trace_df['period_start'])
        trace_df['period_end'] = pd.to_datetime(trace_df['period_end'])

        if granularity != 'daily':
            date_part = trace_df['period_start'].dt.strftime('%b %d') + ' → ' + trace_df['period_end'].dt.strftime('%b %d, %Y')
        else:
            date_part = trace_df['period_start'].dt.strftime('%b %d, %Y')
            
        trace_name_title = self.convert_str_2_title(trace_name)
        value_formatted = trace_df[value_col].round(2).apply(lambda x: f"{x:,.2f}" if isinstance(x, float) else f"{x:,}")
        hover_text = date_part + '<br>' + trace_name_title + ': ' + value_formatted.astype(str)
        
        if other_cols_to_include:
            for col in other_cols_to_include:
                if col in trace_df.columns:
                    col_title = self.convert_str_2_title(col)
                    col_val = trace_df[col].round(2).apply(lambda x: f"{x:,.2f}" if isinstance(x, float) else f"{x:,}")
                    hover_text = hover_text + '<br>' + col_title + ': ' + col_val.astype(str)

        return hover_text

    def test_parameters_for_complience(
        self,
        aggregator,
        segment_col,
        target_col,
        count_col,
        period_aggregator=None,
        count_period_aggregator=None
    ):
        valid = {'avg', 'sum', 'weighted_avg', None}
        if aggregator not in valid:
            raise ValueError("aggregator must be 'avg', 'sum', 'weighted_avg' or None")
        if period_aggregator not in valid:
            raise ValueError("period_aggregator must be 'avg', 'sum', or 'weighted_avg'")
        valid_cnt = {'sum', 'mean', None}
        if count_period_aggregator not in valid_cnt:
            raise ValueError("count_period_aggregator must be 'sum', 'mean', or None")
        if segment_col and isinstance(target_col, list) and len(target_col) > 1:
            raise ValueError("Cannot add multiple target columns when segmentation is used.")
        if aggregator == 'weighted_avg':
            if isinstance(target_col, str) and not isinstance(count_col, str):
                raise ValueError("count_col must be a string for a single target")
            if isinstance(target_col, list):
                ok = isinstance(count_col, list) and len(count_col) == len(target_col)
                if not ok:
                    raise ValueError("count_col list must match target_col list length")
    
    def plot(
        self,
        date_col,
        target_col,
        filters=None,
        segment_col=None,
        aggregator=None,
        period_aggregator=None,
        count_col=None,
        count_period_aggregator='mean',
        granularity='daily',
        incomplete_drop=False,
        days_back=30,
        figsize=[700, 271],
        y_range=None
    ):

        target_cols = [target_col] if isinstance(target_col, str) else target_col
        # We need the list of count columns for tooltip generation later
        all_count_cols = []
        if isinstance(count_col, str):
            all_count_cols = [count_col]*len(target_cols)
        elif isinstance(count_col, list):
            all_count_cols = count_col

        self.test_parameters_for_complience(
            aggregator, segment_col, target_cols, all_count_cols,
            period_aggregator, count_period_aggregator
        )

        super().apply_filters(filters)
        super().trim_to_date_range(days_back, date_col)

        group_cols = [date_col] + ([segment_col] if segment_col else [])

        if aggregator == 'sum':
            agg_dict = {col: 'sum' for col in target_cols}
            agg_dict.update({col: 'sum' for col in all_count_cols})
            agg_df = self.df.groupby(group_cols, as_index=False).agg(agg_dict)
        elif aggregator == 'avg':
            agg_dict = {col: 'mean' for col in target_cols}
            if all_count_cols:
                agg_dict.update({col: 'sum' for col in all_count_cols})
            agg_df = self.df.groupby(group_cols, as_index=False).agg(agg_dict)
        elif aggregator == 'weighted_avg':
            cc_list = count_col if isinstance(count_col, list) else [count_col] * len(target_cols)
            for tc, cc in zip(target_cols, cc_list):
                denom = self.df.groupby(group_cols)[cc].transform('sum')
                self.df[f'{tc}_w'] = self.df[tc] * self.df[cc] / denom
            agg_dict = {f'{tc}_w': 'sum' for tc in target_cols}
            agg_dict.update({cc: 'sum' for cc in set(all_count_cols)})
            agg_df = self.df.groupby(group_cols, as_index=False).agg(agg_dict)
            agg_df.rename(columns={f'{tc}_w': tc for tc in target_cols}, inplace=True)
        self.df = agg_df

        super().convert_to_date_granularity(date_col, granularity)

        if incomplete_drop and granularity in ['weekly', 'monthly']:
            super().drop_incomplete_last_period_if_requested(date_col)
        
        group_cols = ['period_start','period_end'] + ([segment_col] if segment_col else [])
        if granularity != 'daily':
            if period_aggregator == 'sum':
                agg_df = self.df.groupby(group_cols, as_index=False).agg(
                    {col: 'sum' for col in target_cols}
                )
            elif period_aggregator == 'avg':
                agg_dict = {col: 'mean' for col in target_cols}
                if all_count_cols:
                    agg_dict.update({col: 'sum' for col in all_count_cols})
                agg_df = self.df.groupby(group_cols, as_index=False).agg(agg_dict)
            elif period_aggregator == 'weighted_avg':
                cc_list = count_col if isinstance(count_col, list) else [count_col] * len(target_cols)
                for tc, cc in zip(target_cols, cc_list):
                    denom = self.df.groupby(group_cols)[cc].transform('sum')
                    self.df[f'{tc}_w'] = self.df[tc] * self.df[cc] / denom
                agg_dict = {f'{tc}_w': 'sum' for tc in target_cols}
                agg_choice = count_period_aggregator or 'mean'
                agg_dict.update({cc: agg_choice for cc in set(all_count_cols)})
                agg_df = self.df.groupby(group_cols, as_index=False).agg(agg_dict)
                agg_df.rename(columns={f'{tc}_w': tc for tc in target_cols}, inplace=True)

        agg_df[date_col] = agg_df['period_start']
        agg_df = agg_df.sort_values(date_col)
        self._test = agg_df
        
        fig = go.Figure()
        
        if segment_col:
            
            sorted_segments = sorted(agg_df[segment_col].unique())
            
            for segment, color in zip(sorted_segments, self.colors):
                seg_data = agg_df[agg_df[segment_col] == segment].copy()
                
                hover_text = self._create_trace_tooltip(
                    trace_df=seg_data,
                    granularity=granularity,
                    trace_name=str(segment),
                    value_col=target_cols[0],
                    other_cols_to_include=all_count_cols
                )
                self.add_scatter_trace(fig, seg_data, date_col, target_cols[0], str(segment), color, hover_text)
        else:

            for i, tc in enumerate(sorted(target_cols)):
                color = self.colors[i % len(self.colors)]
                
                current_count_col_for_tooltip = []
                if aggregator in ['weighted_avg', 'avg']:
                    if isinstance(count_col, str):
                        # Case 1: A single, shared count_col string. Apply to all traces.
                        current_count_col_for_tooltip = [count_col]
                    elif isinstance(count_col, list) and len(count_col) > i:
                        # Case 2: A list of count_cols. Apply the corresponding one.
                        current_count_col_for_tooltip = [count_col[i]]

                hover_text = self._create_trace_tooltip(
                    trace_df=agg_df,
                    granularity=granularity,
                    trace_name=str(tc),
                    value_col=tc,
                    other_cols_to_include=current_count_col_for_tooltip
                )
                self.add_scatter_trace(fig, agg_df, date_col, tc, str(tc), color, hover_text)
                
        fig.update_layout(
            font=dict(family="Poppins-Medium, sans-serif"),
            plot_bgcolor="white", 
            title=self.title_dict,
            yaxis=self.axis_dict,
            margin=dict(l=self.n+10, r=0, t=self.n, b=self.n),
            legend=self.legend_dict,
            legend_title=self.convert_str_2_title(segment_col),
            hoverlabel=dict(align="left"),
            width=figsize[0],
            height=figsize[1]
        )

        if y_range is not None:
            fig.update_yaxes(range=y_range)
        
        if len(fig.data) > 0 and (agg_df.shape[0] / len(fig.data)) < 10:
            fig.update_layout(
                        xaxis={**self.axis_dict, 
                               "tickformat": "%b %d",
                               'tickvals': agg_df[date_col].unique(),
                               'ticktext': pd.to_datetime(agg_df[date_col].unique()).strftime("%b %d")},
                    )
        else:
            fig.update_layout(
                        xaxis={**self.axis_dict, 
                               "tickformat": "%b %d"}
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
            start = pd.to_datetime(agg_df['period_start']).dt.strftime('%Y-%m-%d')
            end = pd.to_datetime(agg_df['period_end']).dt.strftime('%Y-%m-%d')
            agg_df['hover_text'] = start + ' → ' + end
        else:
            agg_df['hover_text'] = pd.to_datetime(agg_df['period_start']).dt.strftime('%Y-%m-%d')

        for c in [x for x in agg_df.columns if x not in [date_col, 'hover_text', 'period_end', 'period_start']]:
            c_title = self.convert_str_2_title(c)
            val = agg_df[c].round(2).apply(lambda x: "{:,}".format(x)) if agg_df[c].dtype in ['float64', 'int64'] else agg_df[c].astype(str)
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
             figsize=[700, 271]
             ):
        
        # Apply filters
        self.apply_filters(filters)

        self.trim_to_date_range(days_back, date_col)
        
        target_cols = [actual_col,pred_col]

        self.convert_to_date_granularity(date_col ,granularity)
        
        # Drop incomplete last period if requested
        if incomplete_drop and granularity in ['weekly', 'monthly']:
            self.drop_incomplete_last_period_if_requested(date_col)

        group_cols = ['period_start','period_end']

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
            start = pd.to_datetime(agg_df['period_start']).dt.strftime('%Y-%m-%d')
            end = pd.to_datetime(agg_df['period_end']).dt.strftime('%Y-%m-%d')
            agg_df['hover_text'] = start + ' → ' + end
        else:
            agg_df['hover_text'] = pd.to_datetime(agg_df['period_start']).dt.strftime('%Y-%m-%d')

        for c in [x for x in agg_df.columns if x not in [date_col, 'hover_text', 'period_end', 'period_start']]:
            c_title = self.convert_str_2_title(c)
            val = agg_df[c].round(2).apply(lambda x: "{:,}".format(x)) if agg_df[c].dtype in ['float64', 'int64'] else agg_df[c].astype(str)
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
                 figsize=[600, 271],
                 y_range=None):
        
        # Apply filters
        self.apply_filters(filters)

        self.trim_to_date_range(days_back, date_col)
        
        self.convert_to_date_granularity(date_col ,granularity)
        
        # Drop incomplete last period if requested
        if incomplete_drop and granularity in ['weekly', 'monthly']:
            self.drop_incomplete_last_period_if_requested(date_col)
            
        group_cols = ['period_start','period_end'] + ([segment_col] if segment_col else [])
        
        data_grouped = self.df.groupby(group_cols)[target_col].sum().reset_index()
        if segment_col:
            data_grouped[segment_col] = data_grouped[segment_col].astype(str)
        
        if part_of_whole == True:
            data_grouped[f'total_{target_col}'] = data_grouped.groupby('period_start')[target_col].transform('sum')
            data_grouped[f'{target_col}_percentage'] = data_grouped[target_col] / data_grouped[f'total_{target_col}'] * 100

        data_grouped = self.compile_hover_tooltip(data_grouped, date_col, granularity)
        
        # Convert period back to a suitable date representation for plotting
        # We'll use the start of the period for the x-axis
        data_grouped[date_col] = data_grouped['period_start']
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
        if y_range is not None:
            fig.update_yaxes(range=y_range)
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
    
class LegendPlotter:
    def __init__(self, labels):
        self.labels = sorted(labels)
        self.colors = ["#ae37ff", "#ab8bff", "#bbc6e2",
                       "#8fb3e0", "#98c8d9", "#92e4c3",
                       "#91de73", "#bdf07f", "#e5f993"]
        if len(self.labels) > len(self.colors):
            raise ValueError(f"Too many labels: max {len(self.colors)}, got {len(self.labels)}.")
        self.color_map = {str(lbl): self.colors[i] for i, lbl in enumerate(self.labels)}
        self.legend_dict = dict(orientation="h", x=0.5, y=1,
                                xanchor="center", yanchor="top",
                                font=dict(size=12), borderwidth=0)

    def get_legend_figure(self):
        fig = go.Figure()
        for lbl in self.labels:
            fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers',
                                     name=str(lbl),
                                     marker=dict(color=self.color_map[str(lbl)], size=10)))
        fig.update_layout(legend=self.legend_dict, height=20,
                          margin=dict(l=0, r=0, t=0, b=0, pad=0),
                          xaxis=dict(visible=False), yaxis=dict(visible=False),
                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        return fig

