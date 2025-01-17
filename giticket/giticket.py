# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import argparse
import io
import re
import subprocess
import sys

import six

underscore_split_mode = 'underscore_split'
regex_match_mode = 'regex_match'


def update_commit_message(filename, regex, mode, format_string, ticket_number_regex):
    with io.open(filename, 'r+') as fd:
        contents = fd.readlines()
        commit_msg = contents[0].rstrip('\r\n')
        # Check if we can grab ticket info from branch name.
        branch = get_branch_name()


        tickets = re.findall(regex, branch)
        tickets = [ticket for ticket in tickets if ticket != ""]
        ticket_number = ""
        tickets_length = sum([len(ticket) for ticket in tickets]) + len(tickets) * 2
        # Bail if commit message already contains tickets
        if all(ticket in commit_msg[:tickets_length] for ticket in tickets):
            print(f"Commit message already contains tickets in the first {tickets_length} characters.")
            return 1

        if tickets:
            if mode == underscore_split_mode:
                tickets = [branch.split(six.text_type('_'))[0]]
            tickets = [t.strip() for t in tickets]
                
            if ticket_number_regex:
                ticket_number = re.findall(ticket_number_regex, tickets[0])
                if not ticket_number:
                    print("Could not find ticket number in branch name.")
                    return 1
                ticket_number = ticket_number[0]
                tickets[0] = re.sub(ticket_number_regex, '', tickets[0])
                    
 
            new_commit_msg = format_string.format(
                ticket=tickets[0], 
                tickets=', '.join(tickets),
                commit_msg=commit_msg,
                ticket_number= ticket_number
            )

            contents[0] = six.text_type(new_commit_msg + "\n")
            fd.seek(0)
            fd.writelines(contents)
            fd.truncate()
            return 0
        print("Found no tickets in the branch name.")
        return 1


def get_branch_name():
    # Only git support for right now.
    return subprocess.check_output(
        [
            'git',
            'rev-parse',
            '--abbrev-ref',
            'HEAD',
        ],
    ).decode('UTF-8')


def main(argv=None):
    """This hook saves developers time by prepending ticket numbers to commit-msgs.
    For this to work the following two conditions must be met:

        - The ticket format regex specified must match.
        - The branch name format must be <ticket number>_<rest of the branch name>
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='+')
    parser.add_argument('--regex')
    parser.add_argument('--format')
    parser.add_argument('--mode', nargs='?', const=underscore_split_mode,
                        default=underscore_split_mode,
                        choices=[underscore_split_mode, regex_match_mode])
    parser.add_argument('--ticket_number', nargs="?", default=None)
    args = parser.parse_args(argv)
    regex = args.regex or r'[A-Z]+-\d+'  # noqa
    format_string = args.format or '{ticket} {commit_msg}' # noqa
    return update_commit_message(args.filenames[0], regex, args.mode, format_string, args.ticket_number)


if __name__ == '__main__':
    sys.exit(main())
