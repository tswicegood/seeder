Seeder
======
Seeder is a Django application for allowing retweeting important information.


Introduction
------------
We have a great message at [Water.org][water] that we try to get out.  This application
helps with that by allowing users to "donate" their status to us.  Once they're
authorized use using [Twitter's OAuth][twit-oauth], it pushes updates that are
generated through Django's admin out to those users.


Technology
----------
This uses the following applications:

 * [Django][Django] for the data storage
 * [python-twitter][python-twitter] for interaction with Twitter
 * [oauth-python-twitter][oauth-python-twitter] as a wrapper around Twitter's OAuth interface

This serves as a complete example of how to interact with Twitter's OAuth mechanism
using the various libraries that are available.

Installation
------------
Yet to be written

Usage
-----
Standard Django app usage.  The only thing this requires is some way to
automatically run commands so it can post to Twitter.

License
-------
This code is licensed under the [GPLv3][gpl].


[water]: http://water.org
[twit-oauth]: http://apiwiki.twitter.com/OAuth-FAQ
[Django]: http://www.djangoproject.com
[python-twitter]: http://code.google.com/p/python-twitter/
[oauth-python-twitter]: http://code.google.com/p/oauth-python-twitter/
[gpl]: http://www.gnu.org/licenses/gpl-3.0.html

