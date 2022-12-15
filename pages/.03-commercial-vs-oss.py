import streamlit as st
import pandas as pd
import altair as alt
from firebolt_connection import get_firebolt_connection
from datetime import date

st.set_page_config(layout="wide", page_title="Weekends vs. Weekdays", page_icon="firebolt-logo.png")


@st.experimental_singleton(show_spinner=False)
def load_activity_data():
  connection = get_firebolt_connection()
  cursor = connection.cursor()

  # repo details
  cursor.execute("""
WITH repos AS (
SELECT repo_name FROM gharchive
  WHERE event_type = 'WatchEvent' and action='started'
  GROUP BY repo_name
  ORDER BY count(*) DESC
  LIMIT 1000
)
SELECT gharchive.repo_name,
  SUM(CASE WHEN TO_DAY_OF_WEEK(created_at) < 6 THEN 1 ELSE 0 END) AS weekday_commits,
  SUM(CASE WHEN TO_DAY_OF_WEEK(created_at) >= 6 THEN 1 ELSE 0 END) AS weekend_commits,
  SUM(CASE WHEN TO_DAY_OF_WEEK(created_at) < 6 THEN 1 ELSE 0 END)/(SUM(CASE WHEN TO_DAY_OF_WEEK(created_at) < 6 THEN 1 ELSE 0 END)+SUM(CASE WHEN TO_DAY_OF_WEEK(created_at) >= 6 THEN 1 ELSE 0 END)) AS weekday_commit_ratio
  FROM gharchive,repos
  WHERE event_type = 'PushEvent' AND gharchive.repo_name=repos.repo_name
  GROUP BY repo_name
  HAVING weekday_commits+weekend_commits > 10000
  ORDER BY weekday_commit_ratio DESC
  LIMIT 50;
  """)
  repos_with_most_work_weekdays = cursor.fetchall()

  cursor.execute("""
WITH repos AS (
SELECT repo_name FROM gharchive
  WHERE event_type = 'WatchEvent' and action='started'
  GROUP BY repo_name
  ORDER BY count(*) DESC
  LIMIT 1000
)
SELECT gharchive.repo_name,
  SUM(CASE WHEN TO_DAY_OF_WEEK(created_at) < 6 THEN 1 ELSE 0 END) AS weekday_commits,
  SUM(CASE WHEN TO_DAY_OF_WEEK(created_at) >= 6 THEN 1 ELSE 0 END) AS weekend_commits,
  SUM(CASE WHEN TO_DAY_OF_WEEK(created_at) >= 6 THEN 1 ELSE 0 END)/(SUM(CASE WHEN TO_DAY_OF_WEEK(created_at) < 6 THEN 1 ELSE 0 END)+SUM(CASE WHEN TO_DAY_OF_WEEK(created_at) >= 6 THEN 1 ELSE 0 END)) AS weekend_commit_ratio
  FROM gharchive,repos
  WHERE event_type = 'PushEvent' AND gharchive.repo_name=repos.repo_name
  GROUP BY repo_name
  HAVING weekday_commits+weekend_commits > 10000
  ORDER BY weekend_commit_ratio DESC
  LIMIT 50;  
  """)
  repos_with_most_work_weekends = cursor.fetchall()

  connection.close()

  return {
    'repos_with_most_work_weekdays': repos_with_most_work_weekdays,
    'repos_with_most_work_weekends': repos_with_most_work_weekends,
  }

st.title("Repos with weekend vs. weekday work")

with st.spinner('Fetching data and rendering...'):
  data = load_activity_data()

st.header("Repos with highest weekday activity")
st.subheader("by number of pushes, ratio weekday vs weekend")
st.dataframe(pd.DataFrame(data["repos_with_most_work_weekdays"]))

st.header("Repos with highest weekend activity")
st.subheader("by number of pushes, ratio weekend vs weekday")
st.dataframe(pd.DataFrame(data["repos_with_most_work_weekends"]))
