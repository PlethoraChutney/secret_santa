Intro
=====
I stole this entire repo from https://github.com/underbluewaters/secret-santa.

I did this before I knew about forking and I'm too lazy to go do it
properly, sorry. Anyway, I've also made a few changes to the algorithm used
to pick pairs. Instead of going through and randomly pairing people, this
method generates a single "loop", then checks to make sure that no pair
is forbidden by the requirements in config. If there is a pair, it
(stupdily) randomizes again. Since there's no guarantee you'll ever converge,
you can manually adjust the number of attempts you'll make to get a good loop.

If you prefer the old algorithm, which can generate independent chains, you can
choose it with the `--algorithm` option. The old method is probably more likely
to converge if you have highly restrictive pairing preferences.

Here's the original readme:

**secret-santa** can help you manage a list of secret santa participants by
randomly assigning pairings and sending emails. It can avoid pairing
couples to their significant other, and allows custom email messages to be
specified.

Dependencies
------------

pytz
pyyaml

Usage
-----

Copy config.yml.template to config.yml and enter in the connection details
for your outgoing mail server. Modify the participants and couples lists and
the email message if you wish.

    cd secret-santa/
    cp config.yml.template config.yml

Here is the example configuration unchanged:

    # Required to connect to your outgoing mail server. Example for using gmail:
    # gmail
    SMTP_SERVER: smtp.gmail.com
    SMTP_PORT: 587
    USERNAME: you@gmail.com
    PASSWORD: "you're-password"

    TIMEZONE: 'US/Pacific'

    PARTICIPANTS:
      - Chad <chad@somewhere.net>
      - Jen <jen@gmail.net>
      - Bill <Bill@somedomain.net>
      - Sharon <Sharon@hi.org>

    # Warning -- if you mess this up you could get an infinite loop
    DONT-PAIR:
      - Chad, Jen    # Chad and Jen are married
      - Chad, Bill   # Chad and Bill are best friends
      - Bill, Sharon

    # From address should be the organizer in case participants have any questions
    FROM: You <you@gmail.net>

    # Both SUBJECT and MESSAGE can include variable substitution for the
    # "santa" and "santee"
    SUBJECT: Your secret santa recipient is {santee}
    MESSAGE:
      Dear {santa},

      This year you are {santee}'s Secret Santa!. Ho Ho Ho!

      The maximum spending limit is 50.00


      This message was automagically generated from a computer.

      Nothing could possibly go wrong...

      http://github.com/underbluewaters/secret-santa

Once configured, call secret-santa:

    python secret_santa.py path/to/config.yml

Calling secret-santa without arguments will output a test pairing of
participants.

        Test pairings:

        Chad ---> Bill
        Jen ---> Sharon
        Bill ---> Chad
        Sharon ---> Jen

        To send out emails with new pairings,
        call with the --send argument:

            $ python secret_santa.py --send

To send the emails, call using the `--send` argument

    python secret_santa.py --send
