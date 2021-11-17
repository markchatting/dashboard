from __future__ import print_function
from googleapiclient.discovery import build
from google.oauth2 import service_account
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import dash

mapbox_access_token = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'keys.json'

creds = None
creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# The ID spreadsheet.
SAMPLE_SPREADSHEET_ID = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

service = build('sheets', 'v4', credentials=creds)

# Call the Sheets API
sheet = service.spreadsheets()
result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range='Sheet1!A1:BI3000').execute()
values = result.get('values', [])
print(values)

# Turn sheet into dataframe
df = pd.DataFrame(values, columns=values[0])
df['year'].astype(str)

# Subset out the year 2021 to do operations on single year data for figs
this_year = df[df['year'] == '2021']
this_year['date'] = pd.to_datetime(this_year['nest date'])
this_year.sort_values(by='date')
this_year['color'] = np.where(this_year.action == 'Nest', 'green', 'red')

per = this_year.replace(np.nan, '', regex=True)

tagged = per[per['new.tag'] != '']

all_counts = this_year.groupby(['action', 'Location']).agg('count').reset_index()
all_nests = all_counts[all_counts['action'] == 'Nest']
neonates = this_year.groupby(['new.tag']).agg('count').reset_index()
reclutch = this_year.groupby(['reclutch']).agg('count').reset_index()
remigrants = this_year.groupby(['remigrant']).agg('count').reset_index()

period_counts = per.groupby(['action', 'Location']).agg('count').reset_index()
nest_counts = period_counts[period_counts['action'] == 'Nest']
fca_counts = period_counts[period_counts['action'] == 'FCA']
fcu_counts = period_counts[period_counts['action'] == 'FCU']

# Pie chart, where the slices will be ordered and plotted counter-clockwise:
labels = all_nests['Location']
sizes = all_nests['nest date']

# Calculate cuimulative totals (nests and false crawls) for the current year
cum_count = this_year.groupby(['action', 'date']).agg('count').reset_index()
nest_cum_count = cum_count[cum_count['action'] == 'Nest']
nest_cum_count

Date = nest_cum_count['date']
nest_freq = nest_cum_count['nest date']

cum_tot = []
nest_arr = np.array(nest_freq)
for i in range(0, (len(nest_freq) - 1)):
    cum_tot.append(sum(nest_arr[0:i]))
    i += 1

cum_date = Date[1:len(Date)]


fig = make_subplots(
    rows = 4, cols = 6,
    specs=[
            [    {"type": "scattermapbox", 'rowspan':4, 'colspan':3}, None, None, {"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"} ],
            [    None, None, None,               {"type": "bar", "colspan":3}, None, None],
            [    None, None, None,              {"type": "bar", "colspan":3}, None, None],
            [    None, None, None,               {"type": "scatter", "colspan":3}, None, None],
          ]
)

fig.add_trace(
    go.Scattermapbox(
                     lon = this_year['lon'],
                     lat = this_year['lat'],
                     mode='markers',
                     marker={'color' : this_year['color']},
                     unselected={'marker' : {'opacity':1}},
                     selected={'marker' : {'opacity':0.5, 'size':25}},
                     hoverinfo='text',
                     hovertext=this_year['action']
     ),

    row=1, col=1
)


fig.add_trace(
    go.Indicator(
        mode="number",
        value=sum(all_nests['nest date']),
        title="Total Nests",
    ),
    row=1, col=4
)

fig.add_trace(
    go.Indicator(
        mode="number",
        value=(len(neonates) - 1),
        title="Neonates Tagged",
    ),
    row=1, col=5
)

fig.add_trace(
    go.Indicator(
        mode="number",
        value=(len(remigrants) - 1),
        title="Re-captures",
    ),
    row=1, col=6
)

fig.add_trace(
    go.Indicator(
        mode="number",
        value=(len(remigrants) - 1),
        title="Re-captures",
    ),
    row=1, col=6
)

fig.add_trace(
    go.Bar(
        x=all_nests['Location'].tolist(),
        y=all_nests['nest date'].tolist(),
        name= "Nests per site",
        marker=dict(color="Yellow"),
        showlegend=False,
    ),
    row=2, col=4
)

fig.add_trace(
    go.Bar(
        x=cum_date,
        y=nest_freq,
        name= "Nest Frequency",
        marker=dict(color="Green"),
        showlegend=False,
    ),
    row=3, col=4
)

fig.add_trace(
    go.Scatter(
        x=cum_date,
        y=cum_tot,
        mode='lines',
        name= "Cumulative Nests",
        marker=dict(color="Red"),
        showlegend=False,
    ),
    row=4, col=4
)

fig.update_layout(
    template='plotly_dark',
    title="Project title (Last Updated: " + str(np.array(this_year["nest date"])[-1]) + ').',
    autosize=True,
    hovermode='closest',
    showlegend=False,
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=dict(
            lat=25.8,
            lon=51.5
        ),
        pitch=0,
        zoom=8.5,
        style='light'
    ),
)


fig.write_html('Project title.html', auto_open=True)
