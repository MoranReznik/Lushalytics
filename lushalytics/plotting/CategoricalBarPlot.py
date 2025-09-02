import plotly.graph_objects as go
import pandas as pd

class CatBarPlot:
    def __init__(self, df, title=""):
        self.df = df.copy()
        self.title = title
        self.colors = ["#ae37ff","#ab8bff","#bbc6e2","#8fb3e0","#98c8d9","#92e4c3","#91de73","#bdf07f","#e5f993"]
        self.title_dict = dict(text=title.title(), font=dict(color="#AE37FF"), x=0)
        self.margins = dict(l=45, r=0, t=35, b=35)

    def _apply_filters(self, df, filters):
        if filters is None: 
            return df
        if not isinstance(filters, dict):
            raise ValueError("filters must be a dict of {col: list_of_values}.")
        for col, values in filters.items():
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame.")
            df = df[df[col].isin(values)]
        return df

    def _apply_sorting(self, df, sorting, reverse):
        if isinstance(sorting, list):
            custom = [str(x) for x in sorting]
            if set(df["label"]) != set(custom):
                raise ValueError("Custom order must match labels exactly.")
            order = {k: i for i, k in enumerate(custom)}
            df = df.assign(_o=df["label"].map(order)).sort_values("_o").drop(columns="_o")
        elif sorting == "value":
            df = df.sort_values("value", ascending=False)
        elif sorting == "label":
            df = df.sort_values("label", ascending=True)
        elif sorting is not None:
            raise ValueError("sorting must be 'value', 'label', a list, or None.")
        if reverse: df = df.iloc[::-1].reset_index(drop=True)
        return df
    
    def _make_trace_with_oriantation(self, df, orientation):
        if orientation == "v":
            return go.Bar(x=df["label"], y=df["value"], marker_color=self.colors[0], showlegend=False)
        if orientation == "h":
            return go.Bar(x=df["value"], y=df["label"], marker_color=self.colors[0], showlegend=False, orientation="h")
        raise ValueError("orientation must be 'v' or 'h'.")

    def _make_stacked_traces(self, df, labels_order, orientation):
        segs = pd.Index(df["segment"].astype(str).unique())
        traces = []
        for i, s in enumerate(segs):
            sub = df[df["segment"] == s]
            sub = sub.set_index("label").reindex(labels_order, fill_value=0).reset_index()
            if orientation == "v":
                tr = go.Bar(name=str(s), x=sub["label"], y=sub["value"], marker_color=self.colors[i % len(self.colors)], showlegend=True)
            else:
                tr = go.Bar(name=str(s), x=sub["value"], y=sub["label"], marker_color=self.colors[i % len(self.colors)], showlegend=True, orientation="h")
            traces.append(tr)
        return traces

    def _apply_aggregation(self, df, agg="sum"):
        group_cols = ["label"] + (["segment"] if "segment" in df.columns else [])
        if isinstance(agg, str) and agg.startswith(("wmean:","weighted_mean:")):
            tmp = df.assign(_w=df['wc'], _wv=df["value"]*df['wc'])
            out = tmp.groupby(group_cols, as_index=False)[["_wv","_w"]].sum()
            out["value"] = out["_wv"] / out["_w"]
            return out[group_cols + ["value"]]
        out = df.groupby(group_cols, as_index=False)["value"].agg(agg)
        out.columns = group_cols + ["value"]
        return out
    
    def _build_template(self, df, label_col, value_col, agg, segment):
        out = pd.DataFrame({"label": df[label_col].astype(str), "value": df[value_col].values})
        if segment is not None:
            if segment not in df.columns: 
                raise ValueError(f"Column '{segment}' not found in DataFrame.")
            out["segment"] = df[segment].astype(str).values
        if isinstance(agg, str) and agg.startswith(("wmean:","weighted_mean:")):
            wc_col = agg.split(":", 1)[1]
            if wc_col not in df.columns:
                raise ValueError(f"Weighted mean column '{wc_col}' not found in DataFrame.")
            out["wc"] = df[wc_col].values
        return out

    def plot(self, label_col, value_col, agg=None, sorting=None, reverse=False, figsize=(None, None), orientation="v", filters=None, segment=None):
        df = self.df.copy()
        df = self._apply_filters(df, filters)
        df = self._build_template(df, label_col, value_col, agg, segment)
        df = self._apply_aggregation(df, agg)
        if segment is None:
            df = self._apply_sorting(df, sorting, reverse)
            trace = self._make_trace_with_oriantation(df, orientation)
            fig = go.Figure(trace)
            fig.update_layout(title=self.title_dict, margin=self.margins, width=figsize[0], height=figsize[1])
            return fig
        totals = df.groupby("label", as_index=False)["value"].sum()
        totals = self._apply_sorting(totals, sorting, reverse)
        labels_order = totals["label"].tolist()
        traces = self._make_stacked_traces(df, labels_order, orientation)
        fig = go.Figure(traces)
        fig.update_layout(barmode="stack", title=self.title_dict, margin=self.margins, width=figsize[0], height=figsize[1])
        return fig
