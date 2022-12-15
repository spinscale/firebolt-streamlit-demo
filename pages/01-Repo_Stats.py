import streamlit as st
import pandas as pd
import altair as alt
from firebolt_connection import get_firebolt_connection
from datetime import date

st.set_page_config(layout="wide", page_title="Repo Info", page_icon="firebolt-logo.png")


def load_repo_data(repo):
  connection = get_firebolt_connection()
  cursor = connection.cursor()

  # repo details
  cursor.execute("""
    SELECT count(*)
    FROM gharchive
    WHERE repo_name='%s' AND event_type='IssueCommentEvent';
  """ % repo)
  total_number_of_issue_comments = cursor.fetchone()[0]

  cursor.execute("""
    SELECT max(issues_event_number)
    FROM gharchive
    WHERE repo_name='%s' AND event_type='IssuesEvent';
  """ % repo)
  total_number_of_issues = cursor.fetchone()[0]

  cursor.execute("""
    SELECT count(*) cnt , actor_login
    FROM gharchive
    WHERE repo_name='%s' AND event_type='IssueCommentEvent'
    GROUP BY actor_login
    ORDER BY cnt DESC
    LIMIT 30;
  """ % repo)
  top_commenters = cursor.fetchall()

  cursor.execute("""
    SELECT count(*) cnt , actor_login
    FROM gharchive
    WHERE repo_name='%s' AND event_type='PushEvent'
    GROUP BY actor_login
    ORDER BY cnt DESC
    LIMIT 30;
  """ % repo)
  top_committers = cursor.fetchall()

  # events over time
  cursor.execute("""
    SELECT TO_DATE(CONCAT(EXTRACT(YEAR from created_at), '-', LPAD(TO_TEXT(EXTRACT(MONTH from created_at)), 2, '0'), '-01')) as truncated_date, count(*) AS cnt
    FROM gharchive
    WHERE repo_name = '%s'
    GROUP BY truncated_date
    ORDER BY truncated_date ASC;
  """ % repo)
  events_over_time = cursor.fetchall()

  connection.close()

  return {
    'total_number_of_issue_comments': total_number_of_issue_comments,
    'total_number_of_issues': total_number_of_issues,
    'top_commenters': top_commenters,
    'top_committers': top_committers,
    'events_over_time': events_over_time,
  }

st.title("Repository info")

col1, col2 = st.columns(2)
text_input = col1.text_input("Name of repository", value="elastic/elasticsearch", key="repo", help="Name of the repository to look at in form of org/repo")

with st.spinner('Fetching data and rendering...'):
  data = load_repo_data(text_input)

st.header("Repo details")
col1, col2 = st.columns(2)
col1.metric("Issues & PRs", "{:,}".format(data["total_number_of_issues"]))
col2.metric("Issue Comments since 2015", "{:,}".format(data["total_number_of_issue_comments"]))

st.header("Events over time")
events_over_time = pd.DataFrame(data["events_over_time"], columns=['Date', 'Count'])
st.area_chart(events_over_time, x='Date', y='Count')

st.header("Top Commiters (across all branches)")
top_committers = pd.DataFrame(data["top_committers"], columns=['Count', 'Committer'])
# special colorization for the bots
c = alt.Chart(top_committers).mark_bar().encode(
    y=alt.Y('Committer',sort=None),
    x=alt.X('Count', axis=alt.Axis(tickCount=10)),
    color=alt.condition((alt.datum.Commenter=='elasticmachine') | (alt.datum.Commenter=='elasticsearchmachine'),
          alt.value('#F72A2F'),
          alt.value('steelblue')))
st.altair_chart(c, use_container_width=True)

st.header("Top Commenters")
top_commenters = pd.DataFrame(data["top_commenters"], columns=['Count', 'Commenter'])
# special colorization for the bots
c = alt.Chart(top_commenters).mark_bar().encode(
    y=alt.Y('Commenter',sort=None),
    x=alt.X('Count', axis=alt.Axis(tickCount=10)),
    color=alt.condition((alt.datum.Commenter=='elasticmachine') | (alt.datum.Commenter=='elasticsearchmachine'),
          alt.value('#F72A2F'),
          alt.value('steelblue')))
st.altair_chart(c, use_container_width=True)
