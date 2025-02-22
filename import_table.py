"""
Imports the data from the CSV file generated by Qualtrics.
Any entires already in the database are ignored during the import.
"""
import sys
import csv
import records

# Be sure to check the Qualtrics forms for what these values should be.
JUDGE_ROLE_NUM = '1' # A string that represents the judge role in the volunteer form.
MENTOR_ROLE_NUM = '2' # A string that represents the mentor role in the volunteer form.

# Variable to keep track of stats for report at the end.
num_duplicates = 0
num_error = 0
num_unfinished = 0
num_entries = 0

with open(sys.argv[1], 'r') as csv_file:
    # Try to open the provided file name.
    try:
        reader = csv.DictReader(csv_file, delimiter=',')
    except:
        raise BaseException('Cannot read/import CSV file. Check format and resubmit.')

    # Verify that the file has all the attributes we need.
    attributes = set(reader.fieldnames)
    try:
        attributes.remove('Progress')
        attributes.remove('First Name')
        attributes.remove('Email')
    except:
        raise ValueError('CSV file missing required attributes. Check file contents and resubmit.')

    # Check if we are importing the participant or volunteer form.
    isParticipant = False
    try:
        attributes.remove('Roles')
    except:
        isParticipant = True

    # For each entry in the CSV file...
    for entry in reader:
        num_entries = num_entries + 1

        ### Collect data. ###
        # Check that the entry is for a completed response.
        if entry['Progress'] != '100':
            num_unfinished = num_unfinished + 1
            continue

        # Check for and store the entry's first name.
        if entry['First Name'] == '':
            num_error = num_error + 1
            continue
        first_name = entry['First Name']

        # Check for and store the entry's email.
        if entry['Email'] == '':
            num_error = num_error + 1
            continue
        email = entry['Email']

        # Check for a roles attribute.
        roles = []
        try:
            if entry['Roles'] == '':
                # If the roles attribute exists but is blank,
                # skip this entry.
                num_error = num_error + 1
                continue
            # Add appropriate roles for the volunteer form.
            if entry['Roles'].find(JUDGE_ROLE_NUM) != -1:
                roles.append('judge')
            if entry['Roles'].find(MENTOR_ROLE_NUM) != -1:
                roles.append('mentor')
        except KeyError:
            # If the roles attribute does not exist,
            # then we are importing the participant form.
            roles.append('participant')

        ### Add data to database. ###
        #TODO check if entry already exists
        #TODO add entry to DB

# There are essentially three header rows in the CSV file generated by Qualtrics.
# One header row is the actual header row, and the other two rows are treated as entries
# by the CSV reader. As such, subtract two from the relevant totals.
num_entries = num_entries - 2
num_unfinished = num_unfinished - 2

# Output statistics to help with any troubleshooting that may come up.
print(f'Finished importing {sys.argv[1]}')
print(f'Total number of entries processed: {num_entries}')
print(f'-----------------------------------------')
print(f'Number of entries added to database:', end=' ')
print(f'{num_entries - num_duplicates - num_error - num_unfinished} out of {num_entries}')
print(f'Number of duplicate entries: {num_duplicates} out of {num_entries}')
print(f'Number of entries with incomplete information: {num_error} out of {num_entries}')
print(f'Number of unfinished entries: {num_unfinished} out of {num_entries}')
