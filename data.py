import sqlite3
import os

"""
Goals

Make a class that connects to the DB and has an interface for methods like
add_registered_user
create_team
remove_team
leave_team
getUser

"""
_DATABASE_FILE = 'records.db'

_PARTICIPANT_REG_RESPONSES_TABLE_NAME = 'participant_reg_responses'
_MENTOR_REG_RESPONSES_TABLE_NAME = 'mentor_reg_responses'
_JUDGE_REG_RESPONSES_TABLE_NAME = 'judge_reg_responses'

_PARTICIPANT_TABLE_NAME = 'participants'
_MENTOR_TABLE_NAME = 'mentors'
_JUDGE_TABLE_NAME = 'judges'

_TEAM_TABLE_NAME = 'teams'


def _initialize_db(cursor: sqlite3.Cursor):
    # Registration form responses
    cursor.execute(
        f'CREATE TABLE {_PARTICIPANT_REG_RESPONSES_TABLE_NAME} ( email TEXT NOT NULL, discord_username TEXT NOT NULL )')
    cursor.execute(
        f'CREATE TABLE {_MENTOR_REG_RESPONSES_TABLE_NAME} ( email TEXT NOT NULL, discord_username TEXT NOT NULL )')
    cursor.execute(
        f'CREATE TABLE {_JUDGE_REG_RESPONSES_TABLE_NAME} ( email TEXT NOT NULL, discord_username TEXT NOT NULL )')

    # Verified users
    cursor.execute(
        f'CREATE TABLE {_PARTICIPANT_TABLE_NAME} ( discord_id INTEGER PRIMARY KEY, email TEXT OT NULL, team_id REFERENCES {_TEAM_TABLE_NAME}(id) )')
    cursor.execute(
        f'CREATE TABLE {_MENTOR_TABLE_NAME} ( discord_id INTEGER PRIMARY KEY, email TEXT NOT NULL )')
    cursor.execute(
        f'CREATE TABLE {_JUDGE_TABLE_NAME} ( discord_id INTEGER PRIMARY KEY, email TEXT NOT NULL )')

    # Teams
    cursor.execute(f'CREATE TABLE {_TEAM_TABLE_NAME} ( id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, category_channel_id INTEGER NOT NULL, text_channel_id INTEGER NOT NULL, voice_channel_id INTEGER NOT NULL, role_id INTEGER NOT NULL )')