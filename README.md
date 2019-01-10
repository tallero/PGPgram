# PGPgram

[![Python 3.x Support](https://img.shields.io/pypi/pyversions/Django.svg)](https://python.org)
[![License: AGPL v3+](https://img.shields.io/badge/license-AGPL%20v3%2B-blue.svg)](http://www.gnu.org/licenses/agpl-3.0) 

![PGPgram example usage](https://raw.githubusercontent.com/tallero/PGPgram/master/screenshots/pgpgram-in-action.gif)

*PGPgram* is a [GPG](https://gnupg.org) encrypted backup/restore tool written in `python` using [TDLib](https://github.com/tdlib/td). It locally encrypts your files with GnuPG, before they get sent to telegram cloud.

## Motivation

I've come to hate telegram. At the beginning, they were like "we're gonna open source everything after some time, we care about privacy", then

- they've [never](https://twitter.com/ch3ckmat3/status/517144635466989568) [released](https://twitter.com/RebRied/status/555398577351315456) [the source](https://twitter.com/moxie/status/582276833082650625) [of the server](https://twitter.com/AlexeyMetz/status/583122792654213120) (over 5 years have passed),

- they didn't improve secret chats algorithm so that it could be the default way of sending messages without lacking features (going instead with a *curious*, to say the least [apology](https://telegra.ph/Why-Isnt-Telegram-End-to-End-Encrypted-by-Default-08-14) of unecrypted [remote storage](https://xkcd.com/908/), despite aknowledging the existence of credential recovery [schemes](https://postmarkapp.com/guides/password-reset-email-best-practices) secure at least as their [authentication](https://www.theverge.com/2017/9/18/16328172/sms-two-factor-authentication-hack-password-bitcoin);

- they didn't ported secret chats to [desktop](https://github.com/telegramdesktop/tdesktop/issues?utf8=%E2%9C%93&q=is%3Aissue+secret+chat+);

- they competed unfairly in respect to other opensource IM projects, locking in users with over the top [short to last](https://arstechnica.com/information-technology/2015/11/microsoft-drops-unlimited-onedrive-storage-after-people-use-it-for-unlimited-storage/) [features](https://telegram.org/blog/files-on-steroids) made possible by their huge dollar backing ([Durov](https://en.wikipedia.org/wiki/Pavel_Durov)), like [not specified storage quota size](https://www.reddit.com/r/Telegram/comments/7ujfqp/the_maximum_size_of_file_size_that_can_be_sent/) (heck, what do you think you are, Gmail in 2004?).

- their positions is not so much clear; regarding copyright infringements they put theirselves in a gray area; having strong opinions on the matter I am concerned that there exist loopholes in their statements.

So now telegram boasts itself as a privacy champion in the instant messaging space, although previous points tell us quite the opposite. Also, their press material is always very careful with words, so that their statements can easily lead uninformed users to think that their service is secure:
they don't mention that's as true as when you say that Skype is secure, not as when you say that *GNUpg is secure* and you should know [why](https://en.wikipedia.org/wiki/Security_through_obscurity).

## So why did I write PGPgram?
I wrote it as proof-of-concept to show that it could be easy to have (whatever) encryption implemented by default on telegram.
Not that counts anyway, because telegram API [terms of services](https://core.telegram.org/api/terms) indirectly prohibit use of encryption over its servers:

*it is forbidden to force users of other telegram clients to download your app to view CERTAIN messages and content sent using your app*,

which is indeed what an encrypted by default version of telegram would do, even by keeping retrocompatibility.

It should be noted notice that PGPgram does not violate that rule, since the contents it produce are not meant to be shared with other telegram users.

At the time of writing it would be just a matter of time to convert PGPgram to a full fledged telegram client, using other encryption schemes that preserve message sharing among devices, forward secrecy or secret group chats and bots.

## Installation

*PGPgram* is available through the [Python Package Index (PyPI)](https://pypi.org/). Pip is pre-installed if `python >= 3.4` has been downloaded from [python.org](https://python.org); if you're using a GNU/Linux distribution, you can find how to install it on this [page](https://packaging.python.org/guides/installing-using-linux-tools/#installing-pip-setuptools-wheel-with-linux-package-managers).

After setting up pip, you can install *PGPgram* by simply typing in your terminal

    # pip3 install pgpgram

## Usage

*PGPgram* install a command line utility with the same name, `pgpgram`, that can be used to `backup`, `restore`, `search` and `list` files. You can invoke command line help with `pgpgram --help` and get command options with

    pgpgram <command> --help

![PGPgram search](https://raw.githubusercontent.com/tallero/PGPgram/master/screenshots/pgpgram-search.gif)

The application requires `split`, `cat`, `dd`, `sha256sum` and `gpg` to be present on your system, so maybe macOS users will need to make some aliases. At the moment file deletion is not handled because I reached time limit for unpaid development.

## About

This program is licensed under [GNU Affero General Public License v3 or later](https://www.gnu.org/licenses/gpl-3.0.en.html) by [Pellegrino Prevete](http://prevete.ml).<br>
TDLib is licensed under the terms of the [Boost Software License](http://www.boost.org/LICENSE_1_0.txt).<br>
If you find this program useful, consider offering me a [beer](https://patreon.com/tallero), a new [computer](https://patreon.com/tallero) or a part time remote [job](mailto:pellegrinoprevete@gmail.com) to help me pay the bills.


