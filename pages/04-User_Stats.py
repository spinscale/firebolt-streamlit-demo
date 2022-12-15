import re
import streamlit as st
import pandas as pd
import altair as alt
from firebolt_connection import get_firebolt_connection
from datetime import date

st.set_page_config(layout="wide", page_title="User Info", page_icon="firebolt-logo.png")


def load_user_data(user):
  connection = get_firebolt_connection()
  cursor = connection.cursor()

  # user details
  cursor.execute("""
    SELECT count(*)
    FROM gharchive
    WHERE actor_login='%s';
  """ % user)
  total_events = cursor.fetchone()[0]

  # activity over time
  cursor.execute("""
    SELECT EXTRACT(YEAR FROM created_at) as year, count(*)
    FROM gharchive
    WHERE actor_login='%s'
    GROUP BY year
    ORDER by year ASC;
  """ % user)
  events_per_year = cursor.fetchall()

  # different types of events
  cursor.execute("""
    SELECT event_type, count(*) AS cnt
    FROM gharchive
    WHERE actor_login='%s'
    GROUP by event_type
    ORDER BY cnt DESC;
  """ % user)
  event_types = cursor.fetchall()

  # number of different repos worked on
  cursor.execute("""
    SELECT count(distinct(repo_name)) FROM gharchive WHERE actor_login = '%s';
  """ % user)
  number_of_different_repos_worked_on = cursor.fetchone()[0]

  # issue with the most comments
  cursor.execute("""
    SELECT html_url, max(issue_comment_event_issue_comments) as comment_count
    FROM gharchive
    WHERE actor_login = '%s' and event_type = 'IssueCommentEvent'
    GROUP BY html_url
    ORDER BY comment_count DESC
    LIMIT 1;
  """ % user)
  issue_with_most_comments = cursor.fetchone()


  # top issue with the most comments

  connection.close()

  return {
          'events_per_year' : events_per_year,
          'total_events': total_events, # this could also be calculated via events_per_year
          'number_of_different_repos_worked_on': number_of_different_repos_worked_on,
          'event_types': event_types,
          'issue_with_most_comments': issue_with_most_comments,
  }

st.title("User info")

col1, col2 = st.columns(2)
text_input = col1.text_input("User", value="aymeric-dispa", key="user", help="Name of the user to look at")

with st.spinner('Fetching data and rendering...'):
  data = load_user_data(text_input)

st.header("User details")
col1, col2 = st.columns(2)
col1.metric("Total events", data["total_events"])
col2.metric("Different repos worked on", data["number_of_different_repos_worked_on"])
#st.metric("Most worked repo", data["most_worked_on_repo"])

if data["issue_with_most_comments"]:
    issue_name = re.sub('^https://github.com/', '', data["issue_with_most_comments"][0])
    comment_count = data["issue_with_most_comments"][1]
    st.write("###### Most commented issue (%s comments)\n\n[%s](%s)" % (comment_count, issue_name, data["issue_with_most_comments"][0]))


st.header("Events over time")
events_per_year = pd.DataFrame(data["events_per_year"], columns=['Year', 'Count'])
st.bar_chart(events_per_year, x='Year', y='Count')
st.dataframe(data=events_per_year)
