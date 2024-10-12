import os
import discord
from discord.ext import commands
import data
import config



#Init Bot Settings
intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)
   
#---------------------Constants----------------------

MAX_TEAM_SIZE = 4
TEAM_FORMATION_TIMEOUT = 60

# --------------------Helper Methods-------------------



# ---------------------Classes-------------------------

#Retrieves Member username (Can be used for adding members)
class userFlag(commands.FlagConverter):
    member: discord.Member = commands.flag(description='The User being selected')

#Retrieves Email
class emailFlag(commands.FlagConverter):
    email: str = commands.flag(description = 'Email Address used to Register')

#Retrieves Team Name
class teamNameFlag(commands.FlagConverter):
    teamName: str = commands.flag(description = "Name of your team")

#Details to register user to database (Expected to be called by Qualtrics Workflow)
class registerFlag(commands.FlagConverter):
    email: str = commands.flag(description="User Email Address")
    username: str = commands.flag(description="Discord Username")
    role: str = commands.flag(description="User Role")

#-------------------"/" Command Methods-----------------------------
#Init DB's


#Test Greet Command
@bot.tree.command(description="test command")
async def greet(ctxt, name: str):
    await ctxt.send(f'Hi {name}, how\'s your day going? ')

'''
* @requires 
    - Email entered is in database
    - Discord Username matches the user whose email was entered
    - User is not already verified (check role)
* @ensures
    - User gains "verified" role
    - User in database is updated to verified
'''
@bot.hybrid_command(description="Verify your Discord account for this Event")
async def verify(Context, flags: emailFlag): #TODO
    username = Context.author
    email = flags.email

    #Search Database for user with matching email
    
    # TODO Replace {email_in_db} with response from data.py if email is in the database or not
    email_in_db = None

    # if email not registered
    if not email_in_db:
        await Context.send(content="You have not registered your email yet. Go to https://hack.osu.edu/hack12/ to register or contact administration.")
        return
        
    #If user exists, check if discord username exists

    # TODO replace associated_username with repsonse from data.py that gets username given email
    associated_username = None # something like {data.get_username(email)}

    #username not associated with email
    if associated_username != username:
        await Context.send(content="Your Discord username does not match the email provided. Please contact administration.")
        return
    
    # username associated with email and email in db
    
    # TODO do stuff here in data.py here to set user as verified
    await Context.send(content="You have been verified")
    
    
'''
* @requires
    - User sending command is admin (check role)
* @ensures
    - User gains assigned role
    - Database is updated accordingly 
        (if user doesn't exist, add them will role, if they do exist, update role)
'''
@bot.command()
async def overify(Context, flags: registerFlag):  #TODO
    admin_username = Context.author
    user = flags.username
    email = flags.email

    #Search Database for user with matching email

    #If user exists, check if discord username exists

    # else, respond saying either email not found or discord username doesn't match and to contact administration

'''
Useful method to check if someone is verified
''' 
async def check_verified(interaction: discord.Interaction, member: discord.Member = None):
    if member is None:
        member = interaction.user  # Default to the user who invoked the command

    # Check all roles in the guild
    roles = interaction.guild.roles

    # Find the verified role
    verified_role = discord.utils.get(roles, name='Verified')

    if verified_role in member.roles:
        return True
    else:
        return False

'''Useful Methods for creating text and voice channels'''
async def create_text_channel(interaction: discord.Interaction, channel_name: str):
    guild = interaction.guild

    # Check if the channel already exists
    existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
    if existing_channel:
        await interaction.response.send_message(f"Channel '{channel_name}' already exists!")
        return f"Channel '{channel_name}' already exists!", False  # Indicate failure to create

    # Create the text channel
    new_channel = await guild.create_text_channel(name=channel_name)
    return f"Channel '{new_channel.name}' has been created!", True # Indicates success

async def create_voice_channel(interaction: discord.Interaction, channel_name: str):
    guild = interaction.guild

    # Check if the channel already exists
    existing_channel = discord.utils.get(guild.voice_channels, name=channel_name)
    if existing_channel:
        return f"Voice channel '{channel_name}' already exists!", False

    # Create the voice channel
    new_channel = await guild.create_voice_channel(name=channel_name)
    return f"Voice channel '{new_channel.name}' has been created!", True
'''-------------------------------------------------------------------------------'''

'''
* @requires 
    - Cannot already be in a team
    - Must be Verified
    - Team cannot already exist

* @ensures
    - Team is added to database
    - Format is [Team Token, Team Name, Members...]
    - Discord Channels are created
    - User gets role updated
'''
@bot.tree.command(name='createteam', description='Create a team')
async def createteam(
    interaction: discord.Interaction,
    teamname: str
):
    user = interaction.user

    if (check_verified):
        # TODO: check if they are in a team using db methods
        # TODO: check if team already exists using db methods
        await create_text_channel(interaction, teamname)
        await create_voice_channel(interaction, teamname)
        await interaction.response.send_message(f'{teamname} has been created')
    else:
        await interaction.response.send_message(f'You are not verified')

'''
* @requires
    - User calling command is in the team or an admin
* @ensures
    - Team is removed from Databse
    - Discord Channels are removed
    - Roles are removed from Users
'''
@bot.command() #TODO
async def deleteTeam(ctxt):
    pass
    
'''
* @requires
    - Member is in the server
    - Member is not currently in a team
    - Member is Verified
* @ensures
    - Member is added to team in db
    - Member is given the team role
    - Send message to team channel
'''
@bot.tree.command(name='addmember', description='Add a member to your team')
async def addmember(
    interaction: discord.Interaction,
    member: discord.Member # only allow people in server to be selected
):
    user = interaction.user

    # TODO: check if user is in team using db methods
    # TODO: check what team user is in using db methods
    teamName = None
    # TODO: add user to team using db methods
    await interaction.response.send_message(f'{member} has been added to team {teamName} by {user.display_name}')

'''
* @requires
    - Member is in a team
* @ensures
    - Member is removed from team db
    - Member has team role removed
    - Send message to team channel
'''
@bot.command() #TODO
async def leaveTeam(ctxt):
    pass

'''
* @requires
    - Must be an admin
    - Must provide 2 arguments for (previous name, new name)
* @ensures
    - Team name is altered in db
    - Role name is changed
    - Users are assigned the new role
    - Channel names are changed
'''
@bot.command() #TODO
async def renameTeam(ctxt):
    pass


#When the bot is ready, this automatically runs
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user}')


def start():
    bot.run(config.discord_token)
