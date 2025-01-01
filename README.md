# Lushalytics

**Lushalytics** is a set of tools designed for quick, convenient, and beautiful data analysis. It provides intuitive plotting wrappers and utility functions to simplify exploratory analysis and dashboard creation.

---

## Features

### **Plotting**
Lushalytics offers several opinionated wrappers around Plotly to create interactive, aesthetically pleasing charts with ease. These tools provide Tableau-like exploration options, enabling:

- **Segmentation**: Group and compare data across categories.
- **Multi-Metric Tracking**: Monitor several metrics in a single plot.
- **Time Range Control**: Specify how many days back from today to include in your data.
- **Filtering**: Refine the data displayed using custom filters.
- **Time Granularity Control**: Switch between daily, weekly, and monthly views.
- **Aggregation Options**: Choose how metrics are aggregated (e.g., sum, average).
- **Informative Hover Tooltips**: Access detailed, contextual data on hover.

These features are designed to integrate seamlessly into dashboards built with tools like **Streamlit** or **Dash**.

#### Supported Chart Types:
- **Line Chart**: Visualize trends over time.
- **Bar Chart**: Compare metrics across categories or time periods.

---

### **Utils**
Lushalytics includes quality-of-life utilities to simplify common data formatting tasks. Currently, it offers a **number formatting** function that can:

- **Round Numbers**: Adjust precision to suit your needs.
- **Add Commas**: Improve readability with thousands separators.
- **Add Suffixes of Magnitude**: Represent large numbers with appropriate suffixes (e.g., `K`, `M`, `B`).

Example conversions:
- `123456.789` → `123,456.7`
- `123456.789` → `123.4K`

---

## Installation

Install Lushalytics via pip:

```bash
pip install lushalytics