# import os
import io
import records
import config
# import web

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import smtplib
from email.mime.text import MIMEText


#Init Bot Settings
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
# intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

#---------------------Constants----------------------

MAX_TEAM_SIZE = 4
TEAM_FORMATION_TIMEOUT = 120

# Maps role names to corresponding role IDs from configuration
role_map = {
    "participant": config.discord_participant_role_id,
    "mentor": config.discord_mentor_role_id,
    "judge": config.discord_judge_role_id,
    "verified": config.discord_verified_role_id
}

# --------------------Helper Methods-------------------
async def assign_user_roles(user, roles: list): 
    """
    Assigns specified roles to the user based on provided role names.

    Args:
        user (discord.Member): The Discord user to whom the roles will be assigned.
        roles (list): A list of role names (e.g., "participant", "mentor", "judge") that the user should be assigned
    """
    
    for role_name in roles:
        if role_name in role_map:
            role = discord.utils.get(user.guild.roles, id=role_map[role_name])
            if role:
                await user.add_roles(role)
            else:
                print(f"Role '{role_name}' not found in the server.")
        else:
            print(f"Invalid role name '{role_name}' provided.")

async def remove_roles(user: discord.Member, roles:list): 
    """
    Removes specified roles from a Discord user.

    Args:
        user (discord.Member): The Discord user whose roles will be modified.
        roles (list): A list of roles that should be removed from the user.
    """
    roles_set = set(roles)
    old_roles = user.roles
    new_roles = []

    # If role is not contained in the set of roles to remove
    for role in old_roles:
        if role not in roles_set:
            new_roles.append(role)

    # Update user with new roles
    await user.edit(roles=new_roles)

def generate_random_code(n):
    """
    Generates random string of specified length using uppercase letters, lowercase letters, and digits.

    Args:
        length (int): the length of random string to generate

    Requires:
        length (int) >= 0
        
    Returns:
        str: A random string of specified length, containing digits.
    """
    characters = '0123456789'
    return ''.join(random.choices(characters, k=n))    


async def handle_team_deletion(ctxt: discord.Interaction, team_id: int): 
    """
    Handles the timeout of team formation when team doesn't meet minimum size requirement
    
    If team has fewer than two members when timeout, this function will:
        1. remove team assigned role from all current members of team.
        2. remove team association from members in database
        3. delete team associated channels
        4. sends message explaining timeout and team re-creation process

    Args:
        ctxt (discord.Interaction): The Context of the Interaction.
        team_id (int): The unique ID of the team
    """
    if records.team_exists(team_id):
        # Remove Role and team_id from each user on team
        for member in records.get_team_members(team_id):
            await remove_roles(ctxt.guild.get_member(member[0]), [ctxt.guild.get_role(config.discord_team_assigned_role_id)])
            records.drop_team(member[0])
            
        # Remove all Channels
        await delete_team_channels(team_id)
        
async def send_verification_email(recipient, CODE, username): 
    """
    Sends verification email to recipientwith one-time use link for verifying Discord account
    
    Args:
        recipient (str): Email address of the users to send the verificatio link to.
        CODE (str): A randomly generated verification code used in verification link.
        username (str): The Discord username of the person requesting verification.
    
    Returns:
        bool: True if email was sent successfully, False if there was error.
        
    Raises:
        Exception: If there is an error with sending email, prints error message.
    
    """
    body = f"""Dear {records.get_first_name(recipient)},<br>
        To verify that your email is associated with the discord account: {username}, please enter the code below:<br><br>
        <h3>{CODE}</h3><br>
        If you didn’t attempt to verify your account, you can safely ignore this email.<br><br>
        This code will expire in {round(config.email_code_expiration_time/60)} minutes. If it has expired, please request a new verification email.<br><br>
        Thank you,<br>
        OHI/O Hackathon Team<br><br>
        If you have any issues or questions, please contact us at {config.contact_organizer_email} or message in the Ask an Organizer channel on discord
        """
    msg = MIMEText(body, 'html')
    msg['Subject'] = 'Verify your Discord Account'
    msg['From'] = config.email_address
    msg['To'] = recipient
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(config.email_address, config.email_password)
            smtp_server.sendmail(config.email_address, recipient, msg.as_string())

        return True
    except Exception as e:
        print(f"ERROR: Message not to {recipient} not sent. ERROR: {e}")
        return False

async def delete_team_channels(team_id: int):
    """
    Deletes all channels and role associateed with a team, and removes the team from database

    Args:
        team_id (int): The unique ID of the team to delete.
        
    Requires:
        team_id exists and associated with a team
    """
    # Get all channels and role from database
    guild = bot.get_guild(config.discord_guild_id)
    channels = records.get_channels_for_team(team_id)
    team = records.get_team(team_id)

    #Delete all channels and role
    for channel in channels:
        if channel == "category": continue # SKIP CATEGORY FOR HACK
        await guild.get_channel(channels[channel]).delete()
    await guild.get_role(team['role']).delete()

    # Remove team and channels from database
    records.remove_team(team_id)
    for channel in channels:
        records.remove_channel(channels[channel])

async def handle_permission_error(ctxt: discord.Interaction, error: discord.errors): 
    await ctxt.send(ephemeral=True,
                               content='You do not have permission to use this command.')


#-------------------"/" Command Methods-----------------------------

@bot.tree.command(description="Get all team IDs")
@commands.has_role(config.discord_organizer_role_id)
async def getteams(interaction):
    teams = records.get_all_team_ids()
    await interaction.response.send_message(ephemeral=True, content=f'Team IDs: {teams}')

@bot.tree.command(description="Preview messages to be sent to teams")
@commands.has_role(config.discord_organizer_role_id)
async def previewmessages(interaction):
    with open('send_messages.csv', 'r') as file:
        content = file.read()
        # csv in format of team_id,message
        # print content in format of sending to team_id: message
        messages = content.split('\n')
        preview = ""
        for line in messages[1:]:
            if line.strip() == "":
                continue
            team_id, message = line.split(',', 1)
            preview += f'To Team {team_id}:\n{message.replace("\\n", "\n")}\n\n'
        file = discord.File(io.StringIO(preview), filename="messages_preview.txt")
        await interaction.response.send_message(ephemeral=True, content="The message was too long, so here it is as a file:", file=file)

@bot.tree.command(description="Send messages to teams from CSV file")
@commands.has_role(config.discord_organizer_role_id)
async def sendmessages(interaction):
    guild = interaction.guild
    with open('send_messages.csv', 'r') as file:
        content = file.read()
        messages = content.split('\n')
        for line in messages[1:]:
            if line.strip() == "":
                continue
            team_id, message = line.split(',', 1)
            # get team text channel
            team_id_int = int(team_id)
            if not records.team_exists(team_id_int):
                continue
            channels = records.get_channels_for_team(team_id_int)
            team_role_id = records.get_team(team_id_int)['role']
            team_role = interaction.guild.get_role(team_role_id)
            # Prepend team role mention to message
            message = f'{team_role.mention}\n\n' + message
            text_channel_id = channels['text']
            text_channel = guild.get_channel(text_channel_id)
            if text_channel:
                await text_channel.send(content=message.replace('\\n', '\n'))
    await interaction.response.send_message(ephemeral=True, content='Messages sent to teams.')

#Test Greet Command - Anyone can run
@bot.tree.command(description="Recieve a random affirmation for encouragement")
async def affirm(ctxt): # TESTED
    affirmations = {
        "You're doing amazing—every line of code is one step closer to something great!",
        "Remember, the best solutions often come from the toughest challenges. Keep going!",
        "You belong here. Your ideas matter and are worth sharing.",
        "It's not about having all the answers; it's about asking the right questions. You're doing great!",
        "Every bug you squash is a step closer to innovation. Keep debugging!",
        "Your creativity is your superpower. Let it shine!",
        "It's okay to take breaks. Rest fuels brilliance.",
        "You’re capable of more than you realize—trust the process.",
        "Collaboration is key, and you're an invaluable part of your team!",
        "Progress, not perfection, is the goal. You're moving forward, and that's what counts.",
        "Hackathons are marathons, not sprints. Pace yourself and enjoy the journey!",
        "Remember, even the greatest projects started with a single idea. Keep building!",
        "You’re not alone; your teammates and community are here to support you.",
        "Every keystroke is an act of creativity. You're a digital artist!",
        "Challenges are opportunities in disguise. Embrace them and thrive!",
        "Your dedication inspires others. Keep up the amazing work!",
        "Celebrate small victories—they lead to big successes!",
        "Think outside the box. Your unique perspective is your advantage!",
        "You're making something out of nothing—that's incredible!",
        "No matter the outcome, you're learning, growing, and creating. That's a win!"
    }
    random_affirm = random.choice(list(affirmations))
    await ctxt.response.send_message(ephemeral=True, content=f'{random_affirm}')

@bot.hybrid_command(description="Verify your Discord account for this Event")
@app_commands.describe(email_or_code="Email Address used to Register / or / Verification Code")
async def verify(ctxt, email_or_code: str): #TESTED
    """
    Verifies a user's Discord account by linking it with their reg email

    This function:
    1. Checks if the email is registered
    2. Checks if user is already verified
    3. Checks if email is already associated with a verified account
    4. Associates the user's Discord ID with email if they are registered but not yet verified
    5. Sends a verification code via email and waits for user to confirm
    6. Removes expired verification codes after a specified timeout
    
    Args:
        ctxt (Context): The Context of the Interaction
        flags (emailFlag): Flag containing email address to be verified
    """
    
    user = ctxt.author
    email_or_code

    # ------------------ Handle if a code is entered (all digits) --------------------------------
    if (email_or_code.isdigit()):
        code = email_or_code

        # ------------- Do Validation Checks --------------------

        # Check that code is valid
        if not records.code_exists(code):
            await ctxt.send(ephemeral=True,
                            content="Your Verification Code is either not valid or has expired. Please request a new one.")
            return
            
        # Retrieve Message ID or Verification message
        user_id = records.get_value_from_code(code)

        # Check that user_id matches user entering the code
        if user_id != user.id:
            await ctxt.send(ephemeral=True,
                            content=f"The code you entered is not associated with your discord account. Please request a new one by entering the email you registered with.")
            return

        # ------------- Happy Case --------------------

        email = records.get_email_from_reg(user.id)

        # Add user to verified database
        records.add_verified_user(user.id, email, user.name)

        # Assign user with all given roles
        roles = records.get_roles(email)
        roles.append('verified')
        await assign_user_roles(user, roles)
        
        ## Send the user a message that they have been verified and the next steps
        await ctxt.send(ephemeral=True,
                        content=f"Welcome {records.get_first_name(email)}! \nYou have been verified. Please check the {bot.get_guild(config.discord_guild_id).get_channel(config.discord_start_here_channel_id).mention} channel for next steps.")
        return
    # -----------------------------------------------------------------------------------------
    
    email = email_or_code

    # ------------- Do Validation Checks --------------------

    #Check if user is already verified
    if records.verified_user_exists(user.id):
        first_name = records.get_first_name(records.get_verified_email(user.id))
        await ctxt.send(ephemeral=True,
                        content=f"Welcome, {first_name}! You are already verified.")
        return

    #Confirm user is registered
    if not records.registered_user_exists(email):
        await ctxt.send(ephemeral=True,
                        content=f"There are no user's registered with the email: `<{email}>`. \nPlease verify using the correct email, reregister at {config.contact_registration_link}, or contact administration.")
        return
    
    # Check if email is in verified DB
    if records.verified_email_exists(email):
        await ctxt.send(ephemeral=True,
                        content=f"A User with that email address is already verified. \nPlease reregister with a different email address at {config.contact_registration_link}")
        return

    # ------------- Happy Case --------------------

    # Add user_id to registered user
    records.update_reg_discord_id(email, user.id)

    # Remove any codes from same user so only newest link will work
    records.remove_user_codes(user.id)

    # Send Verification Info to web for update
    CODE = generate_random_code(6)
    while records.code_exists(CODE):
        CODE = generate_random_code(6)

    if(await send_verification_email(email, CODE, user.name)):
        # add code to verification codes and send message
        records.add_code(CODE, user.id)
        await ctxt.send(ephemeral=True,
                        content=f"Check your inbox for an email from `<{config.email_address}>` with a verification link. Please check your email and enter the code in this format \n `/verify <code>` to complete your verification. \n\n If you do not see the email within a few minutes, please check your spam/junk folder.")
    else:
        await ctxt.send(ephemeral=True,
                        content="Failed to send verification email. Please contact an organizer for assistance.")

    ## Wait for timeout then delete verification code
    await asyncio.sleep(config.email_code_expiration_time)
    records.remove_code(CODE)

@commands.has_role(config.discord_organizer_role_id)
@bot.hybrid_command(description="Manually verify a Discord account for this event (Organizers only)") 
@app_commands.describe(role="User Role: 'participant', 'mentor', or 'judge'")
async def overify(ctxt, member_to_promote: discord.Member, email_address: str, role: str): #TESTED
    """
    Manually verifies a Discord account for the event, allowing organizers to assign roles and verify users.

    If the user doesn't exist, add them to the database and assign roles.
    If the user exists, update role and updata database.
    Args:
        ctxt (discord.Interaction): The Context of the Interaction.
        flags (registerFlag): Flag that contains registrant information (user, email, and role)
        
    Requires:
        User is an admin
    """
    admin_user = ctxt.author
    email = email_address

    # ------------- Do Validation Checks --------------------

    # Ensure user is an organizer
    organizer_role = ctxt.guild.get_role(config.discord_organizer_role_id)
    if not organizer_role in admin_user.roles:
        await ctxt.send(ephemeral=True,
                        content=f"You do not have permission to run this command")
        return
    
    #Check if role is valid to be overified with
    if not (role in role_map):
        await ctxt.send(ephemeral=True,
                        content=f"`<{role}>` is not a valid role. \nPlease chose either `participant`, `mentor`, or `judge`")
        return

    # If User is not registered, add a registered user with no data
    if not records.registered_user_exists(email):
        records.add_registered_user(email, [role], {})

    # Check if user is already verified
    if records.verified_user_exists(member_to_promote.id):
        verified_email = records.get_verified_email(member_to_promote.id)

        #Check if user has role specified, else add it
        if role in records.get_roles(verified_email):
            await ctxt.send(ephemeral=True,
                            content=f"`<{member_to_promote.name}>` is verified and already has the role `<{role}>`.")
            return

        # Assign user the role
        await assign_user_roles(member_to_promote, [role])
    
        # Update user in database
        roles = records.get_roles(verified_email)
        if not (role in roles):
            roles.append(role)
            records.reassign_roles(email, roles)
        
        await ctxt.send(ephemeral=True,
                        content=f"`<{member_to_promote.name}>` is already verified but has been given the role `<{role}>`.")
        return
    
    # ------------- Happy Case --------------------

    # Add user to verified database
    records.add_verified_user(member_to_promote.id, email, member_to_promote.name)

    await assign_user_roles(member_to_promote, [role, 'verified'])

    await ctxt.send(ephemeral=True,
                    content=f"`<{member_to_promote.name}>` has been verified and given the role `<{role}>`.")
overify.error(handle_permission_error)

@bot.hybrid_command(description="Create a new team for this event")
@app_commands.describe(team_name="Name/Label for your Team")
async def createteam(ctxt, team_name: str, teammate_1: discord.Member, teammate_2: discord.Member = None, teammate_3: discord.Member = None): #TESTED
    """
    Creates a new team, assigning user to team and creating necessary roles and channels

    Args:
        ctxt (discord.Interaction): The Context of the Interaction.
        flags (teamNameFlag): The flags passed containing the team name and teammates users. 
        
    Requires:
        - cannot already be in team
        - user has to be verified and participant

        teamname: str = commands.flag(description = "Name of your team")
        teammate1: discord.Member = commands.flag(description="Username of Teammate")
        teammate2: discord.Member = None
        teammate3: discord.Member = None
        
    """

    # Retrieve Context
    user = ctxt.author

    # ------------- Do Validation Checks --------------------

    # Check that user is verified
    if not records.verified_user_exists(user.id):
        await ctxt.send(ephemeral=True,
                        content="You are not verified! Please verify yourself with the /verify command")
        return

    # Check that user is not in another team
    if records.is_member_on_team(user.id):
        await ctxt.send(ephemeral=True,
                        content="You are already on a team. You can leave with the /leaveteam command")
        return

    # Check that team doesn't already exist
    if records.team_name_exists(team_name):
        await ctxt.send(ephemeral=True,
                        content="That team name is already in use. Please chose a different name")
        return


    # ------------- Happy Case --------------------
    #     Sets up permissions:
    #   - all_access_pass role -> can view channel
    #   - @everyone -> cannot view channel
    #   - team_role -> can view channel

    # voice_channel_perms={
    #     team_role: discord.PermissionOverwrite(connect=True, view_channel=True, speak=True),
    #     ctxt.guild.get_role(config.discord_all_access_pass_role_id): discord.PermissionOverwrite(connect=True, view_channel=True, speak=True),
    #     ctxt.guild.default_role:  discord.PermissionOverwrite(view_channel=False)
    # }
    # voice_channel = await category_channel.create_voice_channel(f"{team_name.replace(' ','-')}-voice", overwrites=voice_channel_perms)

    # Create all channels and role for team internally

    team_role = await ctxt.guild.create_role(name=team_name)
    category_channel_perms = {
        ctxt.guild.get_role(config.discord_all_access_pass_role_id): discord.PermissionOverwrite(view_channel=True),
        ctxt.guild.default_role: discord.PermissionOverwrite(view_channel=False),  
        team_role: discord.PermissionOverwrite(view_channel=True)            
    } 
    text_channel_perms = {
        ctxt.guild.get_role(config.discord_all_access_pass_role_id): discord.PermissionOverwrite(view_channel=True),
        ctxt.guild.default_role: discord.PermissionOverwrite(view_channel=False),  
        team_role: discord.PermissionOverwrite(view_channel=True)  
    }

    channels_per_category = 50 # Max channels per category btw

    # Look at the previously made team (if exists) and 
    team_id = records.create_team(team_name, team_role.id)

    if (team_id - 1) % channels_per_category == 0: 
        # New category channel needs made
        category_channel = await ctxt.guild.create_category_channel(f"Teams {team_id} - {(team_id - 1) + channels_per_category}", overwrites=category_channel_perms)
        records.new_category(category_channel.id, (team_id - 1) + channels_per_category)
    else:
        # Use a previous team's category channel
        category_id = records.get_latest_category()
        category_channel = bot.get_channel(category_id)
    text_channel = await category_channel.create_text_channel(f"{team_id}-{team_name.replace(' ','-')}-text", overwrites=text_channel_perms) # Inherit perms from Category
    

    # Record Team and Channels in Database
    # records.add_channel(category_channel.id, team_id, 'category')
    records.add_channel(text_channel.id, team_id, 'text')
    # records.add_channel(voice_channel.id, team_id, 'voice')
    records.join_team(team_id, user.id) # Add author to team

    # Attempt to add users mentioned to team (Requires atleast 1 Sucesss)
    success = False
    if teammate_1: success = await addmember(ctxt, teammate_1) or success
    if teammate_2: success = await addmember(ctxt, teammate_2) or success
    if teammate_3: success = await addmember(ctxt, teammate_3) or success

    # Check if atleast one user was added to the team
    if not success:
        await handle_team_deletion(ctxt, team_id)
        await ctxt.send(ephemeral=True, content=f'Team creation failed - No teammates could be added. Choose a different teammate or reach out to them to fix their problem.')
        return

    # Assign role to user and send confirmation message
    # await category_channel.edit(name=f"Team {team_id} - {team_name}")
    await user.add_roles(team_role)
    await user.add_roles(ctxt.guild.get_role(config.discord_team_assigned_role_id))
    await ctxt.send(ephemeral=True,
                    content=f'Team creation succeeded. {team_role.mention} created. Make sure to add members to your team using the `/addmember` command. Teams with fewer than 2 members will be deleted after {round(TEAM_FORMATION_TIMEOUT/60)} minutes.')

@bot.hybrid_command(description="Leave your current team")
async def leaveteam(ctxt): #TESTED
    """
    Command for a user to leave their current team. 
    The user will:
        - be removed from the team
        - have team roles removed
    
    Team channel will be notified of departure. If not members are left, the team will be fully deleted.
    
    Args:
        ctxt (discord.Interaction): The Context of the Interaction.
    """

    user = ctxt.author

    # ------------- Do Validation Checks --------------------

    # Ensure user is on a team
    if not records.is_member_on_team(user.id):
        await ctxt.send(ephemeral=True, content="You cannot leave a team since you are not assigned to one!")
        return

    # ------------- Happy Case --------------------

    # Grab Team Relavent Info
    team_id = records.get_user_team_id(user.id)
    role_id = records.get_team(team_id)['role']
    team_assigned_role = ctxt.guild.get_role(config.discord_team_assigned_role_id)
    team_role = ctxt.guild.get_role(role_id)
    team_text_channel = ctxt.guild.get_channel(records.get_channels_for_team(team_id)['text'])

    # Remove user from team in Database
    records.drop_team(user.id)

    # Remove role from user
    await remove_roles(user, [team_role, team_assigned_role])
    
    # Send message back confirming removal
    await ctxt.send(ephemeral=True,
                    content=f"You have successfully been removed from the team {team_role.mention}")
    await team_text_channel.send(content=f'{user.mention} has left the team.')

    # Delete team if no one is left
    if records.get_team_size(team_id) == 0: await handle_team_deletion(ctxt, team_id)
        
@bot.hybrid_command(description="Add a member to your team")
@app_commands.describe(member="The member to add to your team") # This gives the description and autofill
async def addmember(ctxt, member: discord.Member): #TESTED
    """
    Adds a specified member to the team of the user who invokes the command.

    Args:
        ctxt (discord.Interaction): The Context of the Interaction.
        flags (userFlag): The user specified in the command input.
    """
    team_user = ctxt.author # User who invoked the command
    added_user = member # The user to be added to the taem

    # ------------- Do Validation Checks --------------------

    # Check that team_user is in a team
    if not records.is_member_on_team(team_user.id):
        await ctxt.send(ephemeral=True,
                        content='Failed to add team member. You are not currently in a team. You must be in a team to add a team member. Please use `/createteam` to create a team or have another participant use `/addmember` to add you to their team')
        return False # FAILURE
    
    # Check that team is not full
    team_id = records.get_user_team_id(team_user.id)
    if records.get_team_size(team_id) >= MAX_TEAM_SIZE:
        await ctxt.send(ephemeral=True,
                        content=f'Failed to add team member. There is no space in your team. Teams can have a maximum of {MAX_TEAM_SIZE} members.')
        return False # FAILURE

    # Check that added_user is verified and a participant
    if not (records.verified_user_exists(added_user.id) and records.user_is_participant(added_user.id)):
        await ctxt.send(ephemeral=True,
                        content=f'Failed to add team member. `@{added_user.name}` is not a verified participant. All team members must be verified participants.')
        return False # FAILURE
    
    # Check that added_user is not on a team
    if records.is_member_on_team(added_user.id):
        await ctxt.send(ephemeral=True,
                        content=f'Failed to add team member. {added_user.mention} is already in a team. To join your team, they must leave their current team.')
        return False # FAILURE
    
    # ------------- Happy Case --------------------

    # Add the member to the team
    records.join_team(team_id, added_user.id)

    # Retrieve the team text channel and role
    text_channel = ctxt.guild.get_channel(records.get_channels_for_team(team_id)['text'])
    team_role = ctxt.guild.get_role(records.get_team(team_id)['role'])

    # Assign added user team and team_assigned role
    await added_user.add_roles(team_role)
    await added_user.add_roles(ctxt.guild.get_role(config.discord_team_assigned_role_id))
    
    # Send confirmation message to team_user
    await ctxt.send(ephemeral=True,
                    content=f'Team member added successfully. {added_user.mention} has been added to {team_role.mention}.')
    
    # Notify team in team text channel of new member
    await text_channel.send(content=f'{added_user.mention} has been added to the team by {team_user.mention}.')

    return True # SUCCESS

@commands.has_role(config.discord_organizer_role_id)
@bot.hybrid_command(description="Remove Team (Organizers only)") 
async def deleteteam(ctxt, team_role: discord.Role, reason_for_removal: str): #TESTED
    """
    Delete a team and its associated data from the event.

    Args:
        ctxt (discord.Interaction): The Context of the Interaction
        flags (removeTeamFlag): Flags containing the 'team_role' and 'reason' for removal
    """
    # Retrieve team role, name, and ID
    user = ctxt.author
    team_name = team_role.name
    team_id = records.get_team_id(team_name)
    members = records.get_team_members(team_id)

    # ------------- Do Validation Checks --------------------

    # Ensure user is an organizer
    organizer_role = ctxt.guild.get_role(config.discord_organizer_role_id)
    if not organizer_role in user.roles:
        await ctxt.send(ephemeral=True,
                        content=f"You do not have permission to run this command")
        return

    # ------------- Happy Case --------------------

    # Remove roles from users and drop members from team
    for member in members:
        curr_user = ctxt.guild.get_member(member[0])
        await remove_roles(curr_user, [team_role, ctxt.guild.get_role(config.discord_team_assigned_role_id)])
        records.drop_team(curr_user.id)

    # Delete team channels and db
    await delete_team_channels(team_id)

    # Notify team and admin about removal.
    await ctxt.send(ephemeral=True,
                    content=f"The team `<{team_name}>` has been removed and the members have been notified")
    
    for member in members:
        await ctxt.guild.get_member(member[0]).send(
            content=f"Your team has been removed from the event. \nReason: `{reason_for_removal}`. \nYou may create a new team but continued failure to comply may result in being permanently removed")
deleteteam.error(handle_permission_error)

#When the bot is ready, this automatically runs
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.tree.sync()

def start():
    bot.run(config.discord_token)
# ------------------------------------------------------------------


