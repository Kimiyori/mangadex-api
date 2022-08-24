# MangaDex API

This is a simple Python implementation of the [Mangadex API](https://api.mangadex.org/swagger.html). 

It uses only simple commands, because the main purpose of creating this API was that the possibilities of using lists of users were very limited.

# How use it:

```
from manga import MangaDex
session=MangaDex(username, email, password)
#get manga list
response=session.get_list()
#get random title based on title and reading status
response=session.get_random_title_from_user_list(reading_status='plan_to_read',title_status='completed')

```
