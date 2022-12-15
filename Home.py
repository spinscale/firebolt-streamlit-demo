import streamlit as st
import pandas as pd
import altair as alt
from humanize import naturaldelta
from firebolt_connection import get_firebolt_connection
from datetime import date

# page config
st.set_page_config(layout="wide", page_title="Firebolt GitHub Archive Demo", page_icon="firebolt-logo.png")

@st.experimental_singleton(show_spinner=False)
def load_github_archive_data(date_filter):
  connection = get_firebolt_connection()
  cursor = connection.cursor()

  # parameter parsing
  date_from = date_filter[0]
  date_to   = date_filter[1]
  ts_filter = "DATE_TRUNC('DAY', created_at) >= (DATE '%s') AND DATE_TRUNC('DAY', created_at) <= (DATE '%s')" % (date_from, date_to)

  cursor.execute("SELECT COUNT(*) FROM gharchive WHERE %s; " % ts_filter)
  total_events = cursor.fetchone()[0]

  cursor.execute("SELECT count(distinct(repo_name)) FROM gharchive WHERE %s;" % (ts_filter))
  total_repos = cursor.fetchone()[0]

  cursor.execute("SELECT count(distinct(actor_login)) FROM gharchive WHERE %s;" % (ts_filter))
  total_users = cursor.fetchone()[0]

  truncate_unit = 'MONTH'
  delta_days = (date_to-date_from).days
  if delta_days < 183:
    truncate_unit = 'DAY'

  cursor.execute("""
    SELECT DATE_TRUNC('%s', created_at) AS truncated_date, count(*) AS cnt
    FROM gharchive
    WHERE %s
    GROUP BY truncated_date
    ORDER BY truncated_date ASC;
  """ % (truncate_unit, ts_filter))
  events_per_time = cursor.fetchall()

  cursor.execute("""
    SELECT event_type, count(*) as total 
    FROM gharchive 
    WHERE %s
    GROUP BY event_type 
    ORDER BY total DESC;
  """ % ts_filter)
  count_per_event_type = cursor.fetchall()

  connection.close()

  return {
    'total_events': total_events,
    'total_repos': total_repos,
    'total_users': total_users,
    'events_per_time' : events_per_time,
    'events_per_type': count_per_event_type,
  }

st.title("GitHub Archive Data")

col1, col2 = st.columns([2,1], gap='large')
start_date = date(2015, 1, 1)
today = date.today()
col1.slider(
  "Select start/end dates for widgets below",
  min_value=start_date,
  max_value=today,
  value=(start_date, today),
  format="YYYY-MM-DD",
  key="date_from_to")

col1, col2, col3 = st.columns(3)
col1.write("Start: %s" % st.session_state['date_from_to'][0])
col2.write("End: %s" % st.session_state['date_from_to'][1])
col3.write("Duration: %s" % naturaldelta(st.session_state['date_from_to'][1]-st.session_state['date_from_to'][0]))

with st.spinner('Fetching data and rendering...'):
  data = load_github_archive_data(st.session_state['date_from_to'])

col1, col2, col3 = st.columns(3)
col1.metric("Total Events", "{:,}".format(data["total_events"]))
col2.metric("Total repos", "{:,}".format(data["total_repos"]))
col3.metric("Total users",  "{:,}".format(data["total_users"]))

st.header("Events")
events_per_year = pd.DataFrame(data["events_per_time"], columns=['Time', 'Count'])
st.area_chart(data=events_per_year, x='Time', y='Count')

st.header("Events per type")
events_per_type = pd.DataFrame(data["events_per_type"], columns=['Type', 'Count'])
st.bar_chart(data=events_per_type, x='Type', y='Count')
