import core.records as records
import config
import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio

MAX_TEAM_SIZE = 4
TEAM_FORMATION_TIMEOUT = 120

class TeamsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.logger.info(f'TeamsCog initialized with {bot.user}')
    
    async def remove_roles(self, user: discord.Member, roles: list): 
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

    async def delete_team_channels(self, team_id: int):
        """
        Deletes all channels and role associateed with a team, and removes the team from database

        Args:
            team_id (int): The unique ID of the team to delete.
            
        Requires:
            team_id exists and associated with a team
        """
        # Get all channels from database
        guild = self.bot.get_guild(config.discord_guild_id)
        channels = records.get_team_channels

        #Delete all channels and role

        # TODO: this needs to be changed in accordance with database
        for channel in channels:
            if(channel == 'role'):
                await guild.get_role(channels[channel]).delete()
            else:
                await guild.get_channel(channels[channel]).delete()

        # Remove team from database
        records.remove_team(team_id)

    async def handle_team_formation_timeout(self, ctxt: discord.Interaction, team_id: int):
        """
        Handles the timeout of team formation when team doesn't meet minimum size requirement
        
        If team has fewer than two members when timeout, this function will:
            1. remove team assigned role from all current members of team.
            2. remove team association from members in database
            3. delete team associated channels
            4. sends message explaining timeout and team re-creation process

        Args:
            interaction (discord.Interaction): The interaction.
            team_id (int): The unique ID of the team
        """
        if records.team_exists(team_id) and records.get_team_size(team_id) <= 1:
            # Remove Role and team_id from each user on team
            for member in records.get_team_members(team_id):
                await self.remove_roles(ctxt.guild.get_member(member[0]), [ctxt.guild.get_role(config.discord_team_assigned_role_id)])
                records.drop_team(member[0])
                
            # Remove all Channels
            await self.delete_team_channels(team_id)
            await ctxt.send(ephemeral=True,
                            content=f'Team formation timed out. Teams must have at least two members {round(TEAM_FORMATION_TIMEOUT/60)} minutes after creation to be saved. You must re-create your team and use the `/addmember` command to add members to your team within one minute of using the `/createteam` command.')
    
    @app_commands.command(name='createteam', description="Create a new team for this event")
    @app_commands.checks.has_any_role(config.discord_verified_role_id, 'Verified')
    @app_commands.describe(team_name='Name of your team')
    async def create_team(self, interaction: discord.Interaction, team_name: str):
        """
        Creates a new team, assigning user to team and creating necessary roles and channels

        Args:
            interaction (discord.Interaction): The interaction.
            team_name (str): The name of the team to be created 
            
        Requires:
            - cannot already be in team
            - user has to be verified and participant
        """
        self.logger.info(f'Attempting to create team: {team_name} by {interaction.user}')

        # Retrieve Context
        user = interaction.user
        # Check that user is verified
        if not records.verified_user_exists(user.id):
            await interaction.response.send_message(
                content="You are not verified! Please verify yourself with the /verify command",
                ephemeral= True)
            return

        # Check that user is not in another team
        if records.is_member_on_team(user.id):
            await interaction.response.send_message(
                content="You are already on a team. You can leave with the /leaveteam command",
                ephemeral=True)
            return

        # Check that team doesn't already exist
        if records.team_name_exists(team_name):
            await interaction.response.send_message(
                content="That team name is already in use. Please chose a different name",
                ephemeral=True)
            return

        # Create Team Role create channel permissions
        team_role = await interaction.guild.create_role(name=team_name)

        # Sets up permissions:
        #   - all_access_pass role -> can view channel
        #   - @everyone -> cannot view channel
        #   - team_role -> can view channel
        category_channel_perms = {
            interaction.guild.get_role(config.discord_all_access_pass_role_id): discord.PermissionOverwrite(view_channel=True),
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),  
            team_role: discord.PermissionOverwrite(view_channel=True),               
        } 
        voice_channel_perms={
            team_role: discord.PermissionOverwrite(connect=True, view_channel=True, speak=True),
            interaction.guild.get_role(config.discord_all_access_pass_role_id): discord.PermissionOverwrite(connect=True, view_channel=True, speak=True),
            interaction.guild.default_role:  discord.PermissionOverwrite(view_channel=False)
        }
        try:
            # Create Channels
            category_channel = await interaction.guild.create_category_channel(f"Team ## - {team_name}", overwrites=category_channel_perms)
            text_channel = await category_channel.create_text_channel(f"{team_name.replace(' ','-')}-text") # Inherit perms from Category
            voice_channel = await category_channel.create_voice_channel(f"{team_name.replace(' ','-')}-voice", overwrites=voice_channel_perms)
            self.logger.info(f'Created team channels: {text_channel.name}, {voice_channel.name} in category {category_channel.name}')
        except discord.Forbidden:
            await interaction.response.send_message(
                content="An error occurred while creating the team channels. Please contact a server admin.",
                ephemeral=True)
            self.logger.error("Forbidden error while creating team channels. Check bot permissions.")
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(
                content=f"An error occurred while creating the team channels. Please contact a server admin.",
                ephemeral=True)
            self.logger.error(f"HTTPException while creating team channels: {e}")
            return
        
        # Create Team and Channels in Database
        team_id = records.create_team(team_name, team_role.id)
        records.add_channel(category_channel.id, team_id, 'category')
        records.add_channel(text_channel.id, team_id, 'text')
        records.add_channel(voice_channel.id, team_id, 'voice')
        records.join_team(team_id, user.id) # Add user to team

        # Assign role to user and send confirmation message
        await category_channel.edit(name=f"Team {team_id} - {team_name}")
        await user.add_roles(team_role)
        await user.add_roles(interaction.guild.get_role(config.discord_team_assigned_role_id))
        await interaction.response.send_message(
            content=f'Team creation succeeded. {team_role.mention} created. Make sure to add members to your team using the `/addmember` command. Teams with fewer than 2 members will be deleted after {round(TEAM_FORMATION_TIMEOUT/60)} minutes.',
            ephemeral=True)
    
        self.logger.info(f'Team {team_name} created with ID {team_id} by {interaction.user}')
        # Wait for team timeout
        await asyncio.sleep(TEAM_FORMATION_TIMEOUT)
        await self.handle_team_formation_timeout(interaction, team_id)

    @app_commands.command(name='leaveteam', description="Leave your current team")
    @app_commands.checks.has_role(config.discord_team_assigned_role_id)
    async def leave_team(self, interaction: discord.Interaction):
        """
        Command for a user to leave their current team. 
        The user will:
            - be removed from the team
            - have team roles removed
        
        Team channel will be notified of departure. If no members are left, the team will be fully deleted.
        
        Args:
            interaction (discord.Interaction): The Context of the Interaction.

        Requires:
            - user to be in a team
        """
        # Check that iser is on a team
        user = interaction.user
        if not records.is_member_on_team(user.id):
            await interaction.response.send_message(
                content="You cannot leave a team since you are not assigned to one!",
                ephemeral=True)
            return

        team_id = records.get_user_team_id(user.id)
        role_id = records.get_team_role_id

        team_assigned_role = interaction.guild.get_role(config.discord_team_assigned_role_id)
        team_role = interaction.guild.get_role(role_id)
        team_text_channel = interaction.guild.get_channel(records.get_team_text_channel_id(team_id))

        # Remove user from team in Database
        records.drop_team(user.id)

        # Remove role from user
        await self.remove_roles(user, [team_role, team_assigned_role])
        
        # Send message back confirming removal
        await interaction.response.send_message(
            content=f"You have successfully been removed from the team {team_role.mention}",
            ephemeral=True)
        await team_text_channel.send(content=f'{user.mention} has left the team.')
        self.logger.info(f'{interaction.user} has left team {team_id} ({team_role.name})')

        # Delete team if no one is left
        if records.get_team_size(team_id) == 0:
            await self.delete_team_channels(team_id)
            self.logger.info(f'Team {team_id} ({team_role.name}) deleted due to no members left.')

    @app_commands.command(name='addmember', description="Add a member to your team")
    @app_commands.describe(member='Member to add to team')
    @app_commands.checks.has_role(config.discord_participant_role_id)
    @app_commands.checks.has_role(config.discord_verified_role_id)
    async def add_member(self, interaction: discord.Interaction, member: discord.Member):
        """
        Adds a specified member to the team of the user who invokes the command.

        Args:
            interaction (discord.Interaction): The Context of the Interaction.
            member (discord.Member): Member to be added to team

        Requires:
            - Member is currently in the server
            - Member to be added is not currently in a team
            - Member is verified and a participant
        
        Ensures:
            - Member is added to team in db
            - Member is given the team role
            - Notify team of new member
        """
        team_user = interaction.user # User who invoked the command
        added_user = member # The user to be added to the taem

        # Check that team_user is in a team
        if not records.is_member_on_team(team_user.id):
            await interaction.response.send_message(
                content='Failed to add team member. You are not currently in a team. You must be in a team to add a team member. Please use `/createteam` to create a team or have another participant use `/addmember` to add you to their team',
                ephemeral=True)
            return
        
        # Check that team is not full
        team_id = records.get_user_team_id(team_user.id)
        if records.get_team_size(team_id) >= MAX_TEAM_SIZE:
            await interaction.response.send_message(
                content=f'Failed to add team member. There is no space in your team. Teams can have a maximum of {MAX_TEAM_SIZE} members.',
                ephemeral=True)
            return

        # Check that added_user is verified and a participant
        if not (records.verified_user_exists(added_user.id) and records.user_is_participant(added_user.id)):
            await interaction.response.send_message(
                content=f'Failed to add team member. `@{added_user.name}` is not a verified participant. All team members must be verified participants.',
                ephemeral=True)
            return
        
        # Check that added_user is not on a team
        if records.is_member_on_team(added_user.id):
            await interaction.response.send_message(
                content=f'Failed to add team member. {added_user.mention} is already in a team. To join your team, they must leave their current team.',
                ephemeral=True)
            return
        
        # Add the member to the team
        records.join_team(team_id, added_user.id)

        # Retrieve the team text channel and role
        text_channel = interaction.guild.get_channel(records.get_team_text_channel_id)
        team_role = interaction.guild.get_role(records.get_team_role_id)

        # Assign added user team and team_assigned role
        await added_user.add_roles(team_role)
        await added_user.add_roles(interaction.guild.get_role(config.discord_team_assigned_role_id))
        
        # Send confirmation message to team_user
        await interaction.send(
            content=f'Team member added successfully. {added_user.mention} has been added to {team_role.mention}.',
            ephemeral=True)
        
        # Notify team in team text channel of new member
        await text_channel.send(content=f'{added_user.mention} has been added to the team by {team_user.mention}.')
        self.logger.info(f'{added_user} has been added to team {team_id} ({team_role.name}) by {team_user}')

    @app_commands.command(name='renameteam', description="Renames a team")
    @app_commands.describe(
        team_role="Select your team",
        new_name="New name of team"
    )
    async def rename_team(self, interaction: discord.Interaction, team_role: discord.Role, new_name: str):
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
        # TODO: implement
        pass

    @app_commands.command(name='deleteteam', description="Remove Team (Organizers only)") 
    @app_commands.checks.has_any_role(config.discord_organizer_role_id)
    async def delete_team(self, interaction: discord.Interaction, team_role: discord.Role, reason: str):
        """
        Delete a team and its associated data from the event.

        Args:
            interaction (discord.Interaction): The Interaction
            team_role: The role of the team to be removed
            reason: The reason for team removal

        Requires:
            - User calling command is in the team or an admin
        
        Ensures:
            - Team is removed from database
            - Team discord channels are removed
            - Team roles are removed from users
        """
        # Retrieve team role, name, and ID
        user = interaction.user
        team_name = team_role.name
        team_id = records.get_team_id(team_name)

        # Retrieve team members
        members = records.get_team_members(team_id)

        # Ensure user is an organizer
        organizer_role = interaction.guild.get_role(config.discord_organizer_role_id)
        if not organizer_role in user.roles:
            await interaction.response.send_message(
                content=f"You do not have permission to run this command",
                ephemeral=True)
            return

        # Remove roles from users and drop members from team
        for member in members:
            curr_user = interaction.guild.get_member(member[0])
            await self.remove_roles(curr_user, [team_role, interaction.guild.get_role(config.discord_team_assigned_role_id)])
            records.drop_team(curr_user.id)

        # Delete team channels and db
        await self.delete_team_channels(team_id)

        # Notify team and admin about removal.
        await interaction.response.send_message(
            content=f"The team `<{team_name}>` has been removed and the members have been notified",
            ephemeral=True)
        
        for member in members:
            await interaction.guild.get_member(member[0]).send(
                content=f"Your team has been removed from the event. \nReason: `{reason}`. \nYou may create a new team but continued failure to comply may result in being permanently removed")
        self.logger.info(f'Team {team_id} - {team_name} has been removed from the event. \n Reason: `{reason}')

async def setup(bot) -> None:
    await bot.add_cog(TeamsCog(bot))
