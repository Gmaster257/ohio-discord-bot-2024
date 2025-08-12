import sqlite3
import os
import json

_DATABASE_FILE = 'records.db'

"""
Registrant Scheme {
    EMAIL: TEXT*,
    IS_PARTICIPANT: BOOLEAN,
    IS_JUDGE: BOOLEAN,
    IS_MENTOR, BOOLEAN,
    DISCORD_ID: TEXT (Used during email verification, ties email to user_id before adding to verification table)
}

Data Scheme {
    email: TEXT REFERENCES {_REG_RESPONSES_TABLE_NAME}(email),
    first_name: TEXT,
    last_name: TEXT,
    university: TEXT,
    class_time: TEXT,
    major: TEXT,
    grad_year: INTEGER,
    company: TEXT,
    job_title: TEXT,
    ... (other fields as needed)
}

Verified Scheme {
    DISCORD_ID: INTEGER* PRIMARY KEY,
    EMAIL: TEXT*,
    TEAM_ID: INTEGER REFERENCES {_TEAM_TABLE_NAME}(id)
    USERNAME: TEXT*
}

- Channels is a JSON object that can have a variable number of channels, 
  Channel Keys are (TEXT, VOICE, CATEGORY*)

Team Scheme {
    ID: INTEGER PRIMARY KEY AUTOINCREMENT,
    NAME: TEXT UNIQUE,
    CHANNELS: TEXT* (JSON parsed) {
        CATEGORY: INTEGER*,
        TEXT: INTEGER,
        VOICE: INTEGER
    }
}

Code Scheme {
    CODE: TEXT* PRIMARY KEY
    USER_ID: INTEGER*
}
"""

_REG_RESPONSES_TABLE_NAME = 'registration'
_REG_DATA_TABLE_NAME = 'data'
_VERIFIED_TABLE_NAME = 'verified'
_TEAM_TABLE_NAME = 'teams'
_CODE_TABLE_NAME = 'codes'


def _initialize_db(cursor: sqlite3.Cursor):

    # Registration form responses
    cursor.execute(
        f"""CREATE TABLE {_REG_RESPONSES_TABLE_NAME} ( 
            email TEXT NOT NULL, 
            is_participant BOOLEAN NOT NULL,
            is_judge BOOLEAN NOT NULL,
            is_mentor BOOLEAN NOT NULL,
            discord_id INTEGER
            )
        """)

    # Table for registrant/user data
    cursor.execute(
        f"""CREATE TABLE {_REG_DATA_TABLE_NAME} (
            email TEXT NOT NULL REFERENCES {_REG_RESPONSES_TABLE_NAME}(email),
            first_name TEXT,
            last_name TEXT,
            university TEXT,
            class_team TEXT,
            major TEXT,
            grad_year TEXT,
            company TEXT,
            job_title TEXT
            )
        """)

    # Verified users
    cursor.execute(
        f"""CREATE TABLE {_VERIFIED_TABLE_NAME} ( 
            discord_id INTEGER UNIQUE PRIMARY KEY, 
            team_id REFERENCES {_TEAM_TABLE_NAME}(id), 
            email TEXT UNIQUE NOT NULL, 
            username TEXT UNIQUE NOT NULL
            )
        """)

    # Teams
    cursor.execute(
        f"""CREATE TABLE {_TEAM_TABLE_NAME} ( 
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT UNIQUE NOT NULL, 
            channels TEXT
            )
        """)
    
    # Verification Codes
    cursor.execute(
        f"""CREATE TABLE {_CODE_TABLE_NAME} (
            code TEXT PRIMARY KEY NOT NULL,
            value INTEGER NOT NULL
            )
        """)
    

# ---------- Register Data into Database ------------------------------------------------------------ DONE

def add_registered_user(email: str, roles: list, data: dict):
   
    #Check if user is not verified
    if verified_email_exists(email):
        print(f"The email ({email}) is already verified. Registered user is not added")
        return

    #Check if user with that email already registerd and remove it
    if registered_user_exists(email):
        remove_registered_user(email)
    
    #Extract the roles from the provided role list
    is_participant = True if 'participant' in roles else False
    is_judge = True if 'judge' in roles else False
    is_mentor = True if 'mentor' in roles else False

    #Add user data to the data table
    add_user_data(email, data)

    #Add Registered user back with newest form submission information
    cursor.execute(
        f'INSERT INTO {_REG_RESPONSES_TABLE_NAME} (email, is_participant, is_judge, is_mentor)'
        + ' VALUES (?, ?, ?, ?)',
        (email, is_participant, is_judge, is_mentor)
    )

def add_user_data(email: str, data: dict):

    #Define an empty data dictionary
    user_data = {
        'first_name': None,
        'last_name': None,
        'university': None,
        'class_team': None,
        'major': None,
        'grad_year': None,
        'company': None,
        'job_title': None
    }

    #Extract data from the dictionary
    for attribute in data:
        try:
            user_data[attribute] = data[attribute]
        except KeyError:
            pass

    #Insert user data into the database
    cursor.execute(
        f'INSERT INTO {_REG_DATA_TABLE_NAME} (email, first_name, last_name, university, class_team, '
        + 'major, grad_year, company, job_title)'
        + ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (email, user_data['first_name'], user_data['last_name'], user_data['university'], user_data['class_team'],
         user_data['major'], user_data['grad_year'], user_data['company'], user_data['job_title'])
    )

def add_verified_user(discord_id: int, email: str, username: str):
    cursor.execute(
        f'INSERT INTO {_VERIFIED_TABLE_NAME} (discord_id, email, username) VALUES (?, ?, ?)',
        (discord_id, email, username)
    )

def create_team(team_name: str, channels: dict) -> int:
    channels_text = json.dumps(channels)
    cursor.execute(
        f'INSERT INTO {_TEAM_TABLE_NAME} (name, channels) VALUES (?,?)',
        (team_name,channels_text)
    )
    return cursor.lastrowid

# ------------ Remove Entries from Tables -------------------------------------------------------------------------- DONE

def remove_registered_user(email: str):
    cursor.execute(
        f'DELETE FROM {_REG_RESPONSES_TABLE_NAME} WHERE email = ?',
        (email,)
    )
    remove_user_data(email)

def remove_user_data(email: str):
    cursor.execute(
        f'DELETE FROM {_REG_DATA_TABLE_NAME} WHERE email = ?',
        (email,)
    )

def remove_verified_user(discord_id: int):
    cursor.execute(
        f'DELETE FROM {_VERIFIED_TABLE_NAME} WHERE discord_id = ?',
        (discord_id,)
    )

def remove_team(team_id: int):
    cursor.execute(
        f'DELETE FROM {_TEAM_TABLE_NAME} WHERE id = ?',
        (team_id,)
    )

# ------------ Retrieve Individual Entry ------------------------------------------------------------------------ DONE

def get_registered_user(email: str) -> dict:
    cursor.execute(
        f'SELECT * FROM {_REG_RESPONSES_TABLE_NAME} WHERE email = ?',
        (email,)
    )
    data_tuple = cursor.fetchone()
    if data_tuple is None:
        return None

    # Convert data string to dictionary
    data = {
        'email': data_tuple[0],
        'is_participant': data_tuple[1],
        'is_judge': data_tuple[2],
        'is_mentor': data_tuple[3],
        'discord_id': data_tuple[4]
    }

    return data

def get_user_data(email: str) -> dict:
    cursor.execute(
        f'SELECT * FROM {_REG_DATA_TABLE_NAME} WHERE email = ?',
        (email,)
    )
    data_tuple = cursor.fetchone()
    if data_tuple is None:
        return None
    
    # Convert data string to dictionary
    data = {
        'email': data_tuple[0],
        'first_name': data_tuple[1],
        'last_name': data_tuple[2],
        'university': data_tuple[3],
        'class_team': data_tuple[4],
        'major': data_tuple[5],
        'grad_year': data_tuple[6],
        'company': data_tuple[7],
        'job_title': data_tuple[8]
    }

    return data

def get_verified_user(discord_id: int) -> dict:
    cursor.execute(
        f'SELECT * FROM {_VERIFIED_TABLE_NAME} WHERE discord_id = ?',
        (discord_id,)
    )
    data_tuple = cursor.fetchone()
    if data_tuple is None:
        return None

    # Convert data string to dictionary
    data = {
        'discord_id': data_tuple[0],
        'team_id': data_tuple[1],
        'email': data_tuple[2],
        'username': data_tuple[3],
    }

    return data

def get_team(team_id: int) -> dict:
    cursor.execute(
        f'SELECT * FROM {_TEAM_TABLE_NAME} WHERE id = ?',
        (team_id,)
    )
    data_tuple = cursor.fetchone()
    if data_tuple is None:
        return None

    # Convert data string to dictionary
    data = {
        'id': data_tuple[0],
        'name': data_tuple[1],
        'channels': json.loads(data_tuple[2])
    }


    return data


# -------------- Check if entry exists ----------------------------------------------------------------------- DONE

def registered_user_exists(email: str) -> bool:
    cursor.execute(
        f'SELECT * FROM {_REG_RESPONSES_TABLE_NAME} WHERE email = ?',
        (email,)
    )
    return cursor.fetchone() is not None

def user_data_exists(email: str) -> bool:
    cursor.execute(
        f'SELECT * FROM {_REG_DATA_TABLE_NAME} WHERE email = ?',
        (email,)
    )
    return cursor.fetchone() is not None

def verified_user_exists(discord_id: int) -> bool:
    cursor.execute(
        f'SELECT * FROM {_VERIFIED_TABLE_NAME} WHERE discord_id = ?',
        (discord_id,)
    )
    return cursor.fetchone() is not None

def team_exists(team_id: int) -> bool:
    cursor.execute(
        f'SELECT * FROM {_TEAM_TABLE_NAME} WHERE id = ?',
        (team_id,)
    )
    return cursor.fetchone() is not None

# ------- Registered User Methods ----------------------------------------------------------------------------

def get_roles(email: str) -> list:
    cursor.execute(
        f'SELECT is_participant, is_judge, is_mentor FROM {_REG_RESPONSES_TABLE_NAME} WHERE email = ?',
        (email,)
    )
    row = cursor.fetchone()
    roles = []
    if row[0]: roles.append('participant')
    if row[1]: roles.append('judge')
    if row[2]: roles.append('mentor')
    return roles

def reassign_roles(email: str, roles: list):
    #Extract the roles from the provided role list
    is_participant = True if 'participant' in roles else False
    is_judge = True if 'judge' in roles else False
    is_mentor = True if 'mentor' in roles else False

    cursor.execute(
        f'UPDATE {_REG_RESPONSES_TABLE_NAME} SET is_participant=?, is_judge=?, is_mentor=? WHERE email=?',
        (is_participant, is_judge, is_mentor, email)
    )

def get_first_name(email: str) -> str:
    if not has_first_name(email):
        return "Hackathon Registrant"
    else:
        return get_registered_user(email)['data']['first_name']

def has_first_name(email:str) -> bool:
    userData = get_registered_user(email)
    return 'first_name' in userData['data']

def update_reg_discord_id(email:str, discord_id:int):
    cursor.execute(f"UPDATE {_REG_RESPONSES_TABLE_NAME} SET discord_id=:discord_id where email=:email", {
        'discord_id':discord_id,
        'email': email
    })

def get_email_from_reg(discord_id: int) -> str:
    return cursor.execute(f"SELECT email FROM {_REG_RESPONSES_TABLE_NAME} WHERE discord_id=:discord_id", {
        'discord_id': discord_id
    }).fetchone()[0]

# ------- Verified User Methods ----------------------------------------------------------------------------

def get_verified_discord_id(email: str) -> int:
    return cursor.execute(
        f"SELECT discord_id FROM {_VERIFIED_TABLE_NAME} WHERE email=:email", {'email': email}).fetchone()[0]

def get_verified_email(discord_id: int) -> str:
    return cursor.execute(
        f"SELECT email FROM {_VERIFIED_TABLE_NAME} WHERE discord_id=:discord_id", {'discord_id': discord_id}).fetchone()[0]

def verified_email_exists(email: str) -> bool:
    return cursor.execute(f"SELECT * from {_VERIFIED_TABLE_NAME} WHERE email=:email", {
        'email': email
    }).fetchone() is not None

def user_is_participant(user_id: int) -> bool:
    roles = get_roles(get_verified_email(user_id))
    return 'participant' in roles


# ----------- Team Methods ---------------------------------------------------------------------------- 

def add_channel(team_id, channel):
    channels = get_channels(team_id)
    channels.append(channel)

    cursor.execute(f"UPDATE {_TEAM_TABLE_NAME} SET channels=:channels WHERE id=:team_id", {
        'team_id': team_id,
        'channels': channels
    })

def get_channels(team_id):
    channels_text = cursor.execute(
        f"SELECT channels FROM {_TEAM_TABLE_NAME} WHERE id=:team_id", {
            'team_id': team_id})
    return json.loads(channels_text)

def drop_team(discord_id: int):
    cursor.execute(
        f'UPDATE {_VERIFIED_TABLE_NAME} SET team_id=NULL WHERE discord_id=:discord_id', {
            'discord_id': discord_id})

def join_team(team_id: int, discord_id: int):
    cursor.execute(
        f'UPDATE {_VERIFIED_TABLE_NAME} SET team_id=:team_id WHERE discord_id=:discord_id', {
            'discord_id': discord_id, 'team_id': team_id})

def get_team_size(team_id: int) -> int:
    return cursor.execute(
        f'SELECT COUNT(*) FROM {_VERIFIED_TABLE_NAME} WHERE team_id=:team_id', {
            'team_id': team_id}).fetchone()[0]

def get_number_of_teams() -> int:
    return cursor.execute(f"SELECT COUNT(*) FROM {_TEAM_TABLE_NAME}").fetchone()[0]

def get_max_team_id() -> int:
    max_id = cursor.execute(f'SELECT MAX(id) FROM {_TEAM_TABLE_NAME}').fetchone()[0]
    return max_id if max_id is not None else 0

def is_member_on_team(discord_id: int) -> bool:
    cursor.execute(f"SELECT team_id FROM {_VERIFIED_TABLE_NAME} WHERE discord_id=:discord_id", {'discord_id': discord_id})
    user_team_id = cursor.fetchone()[0]
    return user_team_id is not None

def get_user_team_id(discord_id: int) -> int:
    return cursor.execute(f"SELECT team_id FROM {_VERIFIED_TABLE_NAME} WHERE discord_id=:discord_id", 
                          {'discord_id': discord_id}).fetchone()[0]

def get_team_id(team_name: str) -> int:
    return cursor.execute(f"SELECT id FROM {_TEAM_TABLE_NAME} WHERE name=:team_name", {'team_name': team_name}).fetchone()[0]

def get_team_members(team_id: int) -> list:
    cursor.execute(f'SELECT discord_id FROM {_VERIFIED_TABLE_NAME} WHERE team_id=:team_id', {'team_id': team_id})
    members = cursor.fetchall()
    return members

def team_name_exists(team_name: int) -> bool:
    cursor.execute(f"SELECT * FROM {_TEAM_TABLE_NAME} WHERE name=:team_name", {
        'team_name': team_name
    })
    return cursor.fetchone() is not None

def update_channels(team_id: int, channels: list):
    channels_text = json.dumps(channels)
    cursor.execute(f"UPDATE {_TEAM_TABLE_NAME} SET channels=:channels WHERE id=:team_id", {
        'channels': channels_text,
        'team_id': team_id
    })

# ----------- Verification Code Methods ----------------------------------------------------------------------

def add_code(code: str, value: int):
    cursor.execute(f"INSERT INTO {_CODE_TABLE_NAME} (code, value) VALUES (:code, :value)", {
        'code': code,
        'value': value
    })

def code_exists(code: str) -> bool:
    return cursor.execute(f"SELECT * FROM {_CODE_TABLE_NAME} WHERE code=:code", {'code': code}).fetchone() is not None

def get_value_from_code(code: str) -> int:
    return cursor.execute(f"SELECT value FROM {_CODE_TABLE_NAME} WHERE code=:code", {'code': code}).fetchone()[0]

def remove_code(code: str):
    cursor.execute(f"DELETE FROM {_CODE_TABLE_NAME} WHERE code=:code", {'code': code})

def remove_user_codes(discord_id: int):
    cursor.execute(f"DELETE FROM {_CODE_TABLE_NAME} WHERE value=:discord_id",{
        'discord_id': discord_id
    })

# ----------- Connect to Database ----------------------------------------------------------------------------

# Check if db file exists
_db_file_exists = os.path.isfile(_DATABASE_FILE)

# Connecting creates the file if not there
_connection = sqlite3.connect(_DATABASE_FILE, isolation_level=None)
cursor = _connection.cursor()

# Initialize tables if database is new
if not _db_file_exists:
    _initialize_db(cursor)




