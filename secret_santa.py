#!/usr/bin/env python3
import yaml
# sudo pip install pyyaml
import re
import random
import smtplib
import datetime
import pytz
import time
import socket
import sys
import argparse
import os

REQRD = (
    'SMTP_SERVER',
    'SMTP_PORT',
    'USERNAME',
    'PASSWORD',
    'TIMEZONE',
    'PARTICIPANTS',
    'DONT-PAIR',
    'FROM',
    'SUBJECT',
    'MESSAGE',
)

HEADER = """Date: {date}
Content-Type: text/plain; charset="utf-8"
Message-Id: {message_id}
From: {frm}
To: {to}
Subject: {subject}

"""
class Person:
    def __init__(self, name, email, invalid_matches):
        self.name = name
        self.email = email
        self.invalid_matches = invalid_matches

    def __str__(self):
        return "%s <%s>" % (self.name, self.email)

class Pair:
    def __init__(self, giver, reciever):
        self.giver = giver
        self.reciever = reciever

    def __str__(self):
        return "%s ---> %s" % (self.giver.name, self.reciever.name)

def parse_yaml(yaml_path):
    return yaml.safe_load(open(yaml_path))

def choose_reciever(giver, recievers):
    choice = random.choice(recievers)
    if choice.name in giver.invalid_matches or giver.name == choice.name:
        if len(recievers) is 1:
            raise Exception('Only one reciever left, try again')
        return choose_reciever(giver, recievers)
    else:
        return choice

def create_pairs(g, r, attempt_limit=50, attempt_number = 1):
    givers = g[:]
    recievers = r[:]
    pairs = []
    attempts = attempt_number
    for giver in givers:
        try:
            reciever = choose_reciever(giver, recievers)
            recievers.remove(reciever)
            pairs.append(Pair(giver, reciever))
            for pair in pairs:
                for o_pair in pairs:
                    if pair.giver == o_pair.reciever and pair.reciever == o_pair.giver:
                        raise Exception('Pair collision')
        except:
            attempts += 1
            print(f'Collision, attempt number {attempts}')
            if attempts <= attempt_limit:
                return create_pairs(g, r, attempt_limit, attempts)
            else:
                print(f'Tried {attempts-1} times to generate pairs but failed.')
    return pairs

def new_pair(participants, attempt_limit):
    givers = participants[:]
    good_circle = False
    attempt = 1

    # first, generate a copy of the givers and 'rotate' them
    # one position counter-clockwise. Then run through and
    # check the matches to see if any are invalid. If any are,
    # randomize the list and try again, up to a maximum.

    while not good_circle and attempt <= attempt_limit:
        attempt += 1
        good_circle = True
        random.shuffle(givers)
        recievers = givers[:]
        recievers.append(recievers.pop(recievers.index(recievers[0])))
        i = -1
        for giver in givers:
            i += 1
            if recievers[i].name in giver.invalid_matches:
                good_circle = False
            if not good_circle:
                break
    if not good_circle and attempt > attempt_limit:
        raise('Failed to find good pairing')
    pairs = []
    i = 0
    while i < len(givers):
        pairs.append(Pair(givers[i], recievers[i]))
        i += 1

    return pairs


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    parser = argparse.ArgumentParser(description = 'A script to automatically generate and send secret santa pairings.')
    parser.add_argument('-c', '--yaml-path', help = 'Path to config yaml file.', default = 'config.yml')
    parser.add_argument('-s', '--send', help = 'Send the generated pairings. Default is to show test pairings and not send them.', action = 'store_true')
    parser.add_argument('-a', '--attempts', help = 'Number of times to try to find a suitable pairing. Default 50', default = 50, action = 'store', type = int)
    parser.add_argument('--no-save-pairs', help = 'Don\'t save pairings for later reference.', action = 'store_true')
    parser.add_argument('--algorithm', choices = ['loop', 'non-loop'], help = 'Which pairing algorithm you want to use. \'loop\' always generates one big loop of givers to recievers, but may be slower than \'non-loop\', which randomly pairs and can generate several independent chains. Default loop.', default = 'loop')

    if len(sys.argv) == 1:
        parser.print_help(sys.stdout)
        return 0

    args = parser.parse_args()
    algorithm = args.algorithm
    yaml_path = args.yaml_path
    send = args.send
    max_attempts = args.attempts
    no_save_pairs = args.no_save_pairs

    try:
        config = parse_yaml(yaml_path)
    except FileNotFoundError:
        print('Couldn\'t find your config file. Use --yaml-path to point to it')
        sys.exit(1)

    for key in REQRD:
        if key not in config.keys():
            raise Exception(
                'Required parameter %s not in yaml config file!' % (key,))

        participants = config['PARTICIPANTS']
        dont_pair = config['DONT-PAIR']
        if len(participants) < 2:
            raise Exception('Not enough participants specified.')

    givers = []
    for person in participants:
        name, email = re.match(r'([^<]*)<([^>]*)>', person).groups()
        name = name.strip()
        invalid_matches = []
        if dont_pair:
            for pair in dont_pair:
                names = [n.strip() for n in pair.split(',')]
                if name in names:
                    # is part of this pair
                    for member in names:
                        if name != member:
                            invalid_matches.append(member)
        person = Person(name, email, invalid_matches)
        givers.append(person)

    recievers = givers[:]
    if algorithm == 'non-loop':
        pairs = create_pairs(givers, recievers)
    else:
        try:
            pairs = new_pair(givers, max_attempts)
        except:
            print('No good pairing found.\nTry increasing the number of attempts, or relaxing pairing requirements.')
            return(5)
    if not send:
        test_string = """
Test pairings:

%s

To send out emails with new pairings,
call with the --send argument:

$ python secret_santa.py --send

        """ % ("\n".join([str(p) for p in pairs]))
        print(test_string)

    if send:
        server = smtplib.SMTP(config['SMTP_SERVER'], config['SMTP_PORT'])
        server.starttls()
        server.login(config['USERNAME'], config['PASSWORD'])
    for pair in pairs:
        zone = pytz.timezone(config['TIMEZONE'])
        now = zone.localize(datetime.datetime.now())
        date = now.strftime('%a, %d %b %Y %T %Z') # Sun, 21 Dec 2008 06:25:23 +0000
        message_id = '<%s@%s>' % (str(time.time())+str(random.random()), socket.gethostname())
        frm = config['FROM']
        to = pair.giver.email
        subject = config['SUBJECT'].format(santa=pair.giver.name, santee=pair.reciever.name)
        body = (HEADER+config['MESSAGE']).format(
            date=date,
            message_id=message_id,
            frm=frm,
            to=to,
            subject=subject,
            santa=pair.giver.name,
            santee=pair.reciever.name,
        )
        if send:
            result = server.sendmail(frm, [to], body)
            print("Emailed %s <%s>" % (pair.giver.name, to))

        if send and not no_save_pairs:
            with open('pairings_secret.txt', 'w') as outfile:
                for pair in pairs:
                    outfile.write(str(pair) + '\n')

    if send:
        server.quit()


if __name__ == "__main__":
    sys.exit(main())
