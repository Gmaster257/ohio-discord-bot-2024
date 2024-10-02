import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import data


#Load in Bot Key
load_dotenv()

#Init Bot Settings
intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)
   
#---------------------Constants----------------------

MAX_TEAM_SIZE = 4
TEAM_FORMATION_TIMEOUT = 60
TEAM_DATABASE = 'team.sqlite'
USER_DATABASE = 'user.sqlite'

# --------------------Helper Methods-------------------



# ---------------------Classes-------------------------

#Retrieves Member username (Can be used for adding members)
class userFlag(commands.FlagConverter):
    member: discord.Member = commands.flag(description='The member to ban')

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
* @ensures
    - User gains "verified" role
    - User in database is updated to verified
'''
@bot.command()
async def verify(Context, flags: emailFlag): #TODO
    username = Context.author
    email = flags.email

    #Search Database for user with matching email
    
    #If user exists, check if discord username exists

    # else, respond saying either email not found or discord username doesn't match and to contact administration
    
'''
* @requires
    - User sending command is admin
* @ensures
    - User gains assigned role
    - Database is updated accordingly
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
@bot.command() #TODO
async def createTeam(ctxt, *, args: str, flags: teamNameFlag):
    try:
        #Split arguments by space into a list of strings
        split_args = args.split()

        #ensure there are at least 5 elements in the list (1 team name + 4 emails)
        if len(split_args) < 5:
            await ctxt.send("You need to provide the team name followed by 4 email addresses.")
            return

        #get the last 4 elements as emails
        email1 = split_args[-4]
        email2 = split_args[-3]
        email3 = split_args[-2]
        email4 = split_args[-1]
        #join everything before the last 4 emails as the team name
        teamName = " ".join(split_args[:-4])
        # Insert these 5 variables into the sql database
        teamDB.execute('INSERT INTO teams VALUES (?,?,?,?,?)', (teamName, email1, email2, email3, email4))
        teamDB.commit()

        #send success message
        await ctxt.send(f'{teamName} was successfully registered! Happy hacking!')

    except Exception as e:
        #Catch any unexpected errors and log them
        await ctxt.send(f"An error occurred: {e}")

'''
* @requires
    - User calling command is in the team or an admin
* @ensures
    - Team is removed from Databse
    - Discord Channels are removed
    - Rolls are removed from Users
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
@bot.command(name='addmember', description='Add a member to your team.') # TODO
@commands.has_role('Verified')
async def addmember(ctxt):
    #Get the Role object for the Verified role.
    verified_role = discord.utils.find(lambda role: role.name == 'Verified', ctxt.guild.roles)
    if verified_role not in ctxt.author.roles:
        #If the caller of the command is not verified, they cannot use this command.
        await ctxt.send("I'm sorry, but you need to be verified to join a team."
                        + "Use the /verify command to get verified!")
        return
    await ctxt.send(f'{ctxt.author.display_name} has joined teamName!')

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

    userDB.execute('INSERT INTO users (name) VALUES (?)', (flags.emal))
    userDB.commit()

    #send success message
    await ctxt.send(f'Email: {flags.email} was successfully added')


#When the bot is ready, this automatically runs
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user}')

@bot.event
async def on_command_error(ctxt, error):
    if isinstance(error, commands.errors.CheckFailure):
        print(f'User {ctxt.author.display_name}', end=' ')
        print(f'attempted to run the {ctxt.command.name} command', end=' ')
        print(f'without having the {error.missing_role} role.')
    else:
        print(error)

#Get Bot Token and start running on server
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
bot.run(DISCORD_BOT_TOKEN)