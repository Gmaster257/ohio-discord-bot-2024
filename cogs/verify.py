import core.records as records
import config
import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio

import random
import smtplib
from email.mime.text import MIMEText


class VerifyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.role_map = {
            'participant': config.discord_participant_role_id,
            'mentor': config.discord_mentor_role_id,
            'judge': config.discord_judge_role_id,
            'verified': config.discord_verified_role_id
        }
        self.logger.info(f'VerifyCog initialized with {bot.user}')

    def generate_random_code(n: int) -> str:
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
    
    async def assign_user_roles(self, user: discord.Member, roles: list) -> None:
        """
        Assigns specified roles to the user based on provided role names.

        Args:
            user (discord.Member): The Discord user to whom the roles will be assigned.
            roles (list): A list of role names (e.g., "participant", "mentor", "judge") that the user should be assigned
        """
        
        for role_name in roles:
            if role_name in self.role_map:
                role = discord.utils.get(user.guild.roles, id=self.role_map[role_name])
                if role:
                    await user.add_roles(role)
                else:
                    self.logger.info(f"Role '{role_name}' not found in the server.")
            else:
                self.logger.warning(f"Invalid role name '{role_name}' provided.")

    async def send_verification_email(self, recipient: str, CODE: str, username: str) -> bool:
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
                self.logger.info(f'Verification email sent to {recipient}.')
            return True
        except Exception as e:
            self.logger.error(f"ERROR: Message not to {recipient} not sent. ERROR: {e}")
            return False
    
    @app_commands.command(name='verify', description="Verify your Discord account for this Event")
    @app_commands.describe(email_or_code="Your registered email or verification code")
    async def verify(self, interaction: discord.Interaction, email_or_code: str):
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
            interaction (discord.Interaction): The interaction.
            email_or_code (str): String containing either a email address or code
        """
        self.logger.info(f"Verification attempt by {interaction.user.name} (ID: {interaction.user.id}) with input: {email_or_code}")

        user = interaction.user
        email = email_or_code

        # ------------------ Handle if a code is entered (all digits) --------------------------------
        if (email.isdigit()):
            code = email

            # Check that code is valid
            if not records.code_exists(code):
                await interaction.response.send_message(
                    content="Your Verification Code is either not valid or has expired. Please request a new one.",
                    ephemeral=True)
                return
                
            # Retrieve Message ID or Verification message
            user_id = records.get_value_from_code(code)

            # Check that user_id matches user entering the code
            if user_id != user.id:
                await interaction.response.send_message(
                    content=f"The code you entered is not associated with your discord account. Please request a new one by entering the email you registered with.",
                    ephemeral=True)
                return

            """ Happy Case """

            email = records.get_email_from_reg(user.id)

            # Add user to verified database
            records.add_verified_user(user.id, email, user.name)

            # Assign user with all given roles
            roles = records.get_roles(email)
            roles.append('verified')
            await self.assign_user_roles(user, roles)
            
            ## Send the user a message that they have been verified and the next steps
            await interaction.response.send_message(
                content=f"Welcome {records.get_first_name(email)}! \nYou have been verified. Please check the {self.bot.get_guild(config.discord_guild_id).get_channel(config.discord_start_here_channel_id).mention} channel for next steps.",
                ephemeral=True)
            return
        # -----------------------------------------------------------------------------------------

        #Confirm user is registered
        if not records.registered_user_exists(email):
            await interaction.response.send_message(
                content=f"There are no user's registered with the email: `<{email}>`. \nPlease verify using the correct email, reregister at {config.contact_registration_link}, or contact administration.",
                ephemeral=True)
            return
        
        #Check if user is already verified
        if records.verified_user_exists(user.id):
            first_name = records.get_first_name(records.get_verified_email(user.id))
            await interaction.response.send_message(
                content=f"Welcome, {first_name}! You are already verified.",
                ephemeral=True)
            return

        # Check if email is in verified DB
        if records.verified_email_exists(email):
            await interaction.response.send_message(
                content=f"A User with that email address is already verified. \nPlease reregister with a different email address at {config.contact_registration_link}",
                ephemeral=True)
            return

        """ Happy Case: Send user an email with a one-time code """

        # Add user_id to registered user
        records.update_reg_discord_id(email, user.id)

        # Remove any codes from same user so only newest link will work
        records.remove_user_codes(user.id)

        # Send Verification Info to web for update
        CODE = self.generate_random_code(6)
        while records.code_exists(CODE):
            CODE = self.generate_random_code(6)

        if(await self.send_verification_email(email, CODE, user.name)):
            # add code to verification codes and send message
            records.add_code(CODE, user.id)
            await interaction.response.send_message(
                content=f"Check your inbox for an email from `<{config.email_address}>` with a verification link. Please check your email and enter the code in this format \n `/verify (code)`",
                ephemeral=True)
        else:
            await interaction.response.send_message(
                content="Failed to send verification email. Please contact an organizer for assistance.",
                ephemeral=True)
            self.logger.error(f'Failed to send verification email for `{interaction.command}`')

        ## Wait for timeout then delete verification code
        await asyncio.sleep(config.email_code_expiration_time)
        records.remove_code(CODE)

    @app_commands.command(name='overify', description="Manually verify a user and assign roles")
    @app_commands.describe(
        member="The Discord user to verify", 
        email="Email address of the user", 
        role="Role to assign")
    @app_commands.checks.has_role(config.discord_organizer_role_id)
    @app_commands.choices(role=[
        app_commands.Choice(name='Participant', value='participant'),
        app_commands.Choice(name='Mentor', value='mentor'),
        app_commands.Choice(name='Judge', value='judge'),
        app_commands.Choice(name='Mentor/Judge', value='mentor, judge')
    ])    
    async def overify(self, interaction: discord.Interaction, member: discord.Member, email: str, role: app_commands.Choice[str]):
        """
        Manually verifies a Discord account for the event, allowing organizers to assign roles and verify users.

        If the user doesn't exist, add them to the database and assign roles.
        If the user exists, update role and updata database.
        Args:
            ctxt (discord.Interaction): The Context of the Interaction.
            flags (registerFlag): Flag that contains registrant information (user, email, and role)
            
        Requires:
            - User is an admin
        
        Ensures:
            - User gains assigned role
            - Database is updated accordingly (i.e., if user doesn't exist, add them with role, if they do exist, update role)
        """
        self.logger.info(f"Overification attempt by {interaction.user.name} (ID: {interaction.user.id}) for {member.name} (ID: {member.id}) with email: {email} and role: {role.value}")

        admin_user = interaction.user

        user = member
        email = email
        role_names : list = role.strip().split(',')

        # Ensure user is an organizer
        organizer_role = interaction.guild.get_role(config.discord_organizer_role_id)
        if not organizer_role in admin_user.roles:
            await interaction.response.send_message(
                content=f"You do not have permission to run this command",
                ephemeral=True)
            return

        # If User is not registered, add a registered user with no data
        if not records.registered_user_exists(email):
            records.add_registered_user(email, [role], {})

        # Check if user is already verified
        if records.verified_user_exists(user.id):
            verified_email = records.get_verified_email(user.id)

            #Check if user has role specified, else add it
            if role in records.get_roles(verified_email):
                await interaction.response.send_message(
                    content=f"`<{user.name}>` is verified and already has the role `<{role}>`.",
                    ephemeral=True)
                return

            # Assign user the role
            await self.assign_user_roles(user, role_names)
        
            # Update user in database
            roles = records.get_roles(verified_email)
            if not (role in roles):
                roles.append(role)
                records.reassign_roles(email, roles)
            
            await interaction.response.send_message(
                content=f"`<{user.name}>` is already verified but has been given the role `<{role}>`.",
                ephemeral=True)
            return
        
        # Add user to verified database
        records.add_verified_user(user.id, email, user.name)

        await self.assign_user_roles(user, [role, 'verified'])

        await interaction.response.send_message(
            content=f"`<{user.name}>` has been verified and given the role `<{role}>`.",
            ephemeral=True)
        self.logger.info(f"O-verified {member.name} with email: {email} and role: {role.value}")

async def setup(bot) -> None:
    await bot.add_cog(VerifyCog(bot))
