import os


'''
Goal:
    Create a cmd prompt-like interface to run prepregrammed commands

    How:
    - Listen for any input()
    - Tokenize input
    - Identify command
    - Run method
'''

SEPARATORS = " "
ROLES = {'participants', 'judge', 'mentor'}
command_history = []



def wait_for_input(prompt:str):
    return input(prompt)

def tokenize(line:str):

    #Create Set of Separators
    separators = set()
    for char in SEPARATORS:
        separators.add(char)

    #Create Queue for tokens
    tokens = []

    #Tokenize String
    position = 0
    while(position < len(line)):
        token = next_char_or_separator(line, position, separators)
        position = position + len(token)
        if not (token[0] in separators):
            tokens.append(token)
    
    return tokens


    
def next_char_or_separator(line:str, position:int, separators:set):
    
    #Loop through str and find next index
    index = position
    firstCharIsSeparator = line[position] in separators
    while(index < len(line) and (firstCharIsSeparator == (line[index] in separators))):
        index = index + 1
        
    return line[position:index]


def interpret_input_tokens(tokens:list):
    
    #Does user have a slash at the front of the command
    if (tokens[0][0] == '/'):
        #Distingish command, params, and data
        command = tokens[0]
        parameters = tokens[1:]

        #Identify Command
        for sent_command in COMMANDS:
            if sent_command[0] == command:
                sent_command[1](parameters)
        
    else:
        print("> Please enter a command with '/' | Type /help for commands")

        return


def start():
    while(True):
        input = wait_for_input("> ")
        
        tokens = tokenize(input)

        interpret_input_tokens(tokens)

def c_help(parameters):
    #Print a list of commands
    print("Commands: ")
    for command in COMMANDS:
        print(f'\t- {command[0]}')
    print("\nPlease type (/command) -help for more information")


def c_import_table(parameters):
    
    # Retrieve Location // roles // email-header // user_header
    location = parameters[0] #DIR
    roles = parameters[1][1:] # /jm or / p
    email_header = parameters[2] #Str
    user_header = parameters[3]

    #------- Test parameters --------

    #Try to open the file
    if(not os.path.isfile(location)):
        print("ERROR: File can not be found!")
        return


    if (len(roles) == 0):
        print("No roles specificied...")
    temp = []
    print(roles + "-" + len(roles))
    for char in roles:
        for role in ROLES:
            if (char == role[0]):
                temp.append(role)
    




## Tuple list of all commands and their corrosponding method
COMMANDS = [
    (
        "/help",
        c_help,
        " - Display a list of commands\n"
    ),
    (
        "/importTable", 
        c_import_table,
        """ Import a csv table of users into the registered db
              \t/importTable [location] /[roles] -e [email-header] -u [username-header]
              \t--------------------------------------
              \t[location] = Valid path to .csv file
              \t[roles] = /p - particpant || /m - mentor  || /j - judge || //jm - multiple
              \t[email_header] = CSV header name for Email
              \t[user_header] = CSV header name for Username
        """
    )]


start()