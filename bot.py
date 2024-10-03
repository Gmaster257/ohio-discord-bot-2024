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
    pass

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


#When the bot is ready, this automatically runs
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user}')


def start():
    bot.run(config.discord_token)
