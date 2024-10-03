import configparser

#Init Vars
config_data = configparser.ConfigParser()
CONFIG_FILENAME = 'config.ini'

# Required configuration entries in _CONFIG_FILENAME, a list of tuples of
# (section: str, option: str)
_REQUIRED_CONFIG_ENTRIES = [
    ('discord', 'guild_id'),
    ('discord', 'token'),
    ('discord', 'start_here_channel_id'),
    ('discord', 'ask_an_organizer_channel_id'),
    ('discord', 'organizer_role_id'),
    ('discord', 'participant_role_id'),
    ('discord', 'mentor_role_id'),
    ('discord', 'judge_role_id'),
    ('discord', 'team_assigned_role_id'),
    ('discord', 'all_access_pass_role_id'),
    ('discord', 'verified_role_id'),
    ('contact', 'registration_link'),
    ('contact', 'organizer_email'),
    ('web', 'port'),
    ('web', 'api_key'),
]

#Import Data from CONFIG_FILENAME into _config
try:
    config_data.read(CONFIG_FILENAME)
except configparser.Error:
    print("ERROR: Error reading config file")
    exit(1)


#Check that all required entries are present
for entry in _REQUIRED_CONFIG_ENTRIES:
    entry_value = config_data.get(entry[0], entry[1])
    if entry_value is None:
        print(
            f'ERROR: Missing required config entry "{entry[1]}" in section "{entry[0]}"')
        exit(1)


#Declare relevant variables to be retrieved
discord_guild_id = int(config_data['discord']['guild_id'])
discord_token = config_data['discord']['token']
discord_start_here_channel_id = int(config_data['discord']['start_here_channel_id'])
discord_ask_an_organizer_channel_id = int(config_data['discord']['ask_an_organizer_channel_id'])
discord_organizer_role_id = int(config_data['discord']['organizer_role_id'])
discord_participant_role_id = int(config_data['discord']['participant_role_id'])
discord_mentor_role_id = int(config_data['discord']['mentor_role_id'])
discord_judge_role_id = int(config_data['discord']['judge_role_id'])
discord_team_assigned_role_id = int(config_data['discord']['team_assigned_role_id'])
discord_all_access_pass_role_id = int(config_data['discord']['all_access_pass_role_id'])
discord_verified_role_id = int(config_data['discord']['verified_role_id'])
contact_registration_link = config_data['contact']['registration_link']
contact_organizer_email = config_data['contact']['organizer_email']
web_port = int(config_data['web']['port'])
web_api_key = config_data['web']['api_key']