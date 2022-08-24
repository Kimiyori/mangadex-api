# MangaDex API

This is a simple Python implementation of the [Mangadex API](https://api.mangadex.org/swagger.html). 

It uses only simple commands, because the main purpose of creating this API was that the possibilities of using lists of users were very limited.

# How use it:

```
from manga import MangaDex
import asyncio

session=MangaDex(username, email, password)
async def fetch():
    client =  await MangaDex.create(username, email, password)
    try:
        #get manga list
        response =await client.get_list()
        
        #get random title based on title and reading status
        response=await client.get_random_title_from_user_list(reading_status='plan_to_read',title_status='completed')
    finally:
        await client.session.close()
        
asyncio.run(fetch())


#or use directly from wrapper
from mangadex import ApiWrapper
import asyncio

async def fetch():
    client =  await ApiWrapper.create(username, email, password)
    api = await client.get_api()
    try:
        lst = ['491bdbe0-0c83-42d5-8b20-3a651e65f70b']*100
        r=await asyncio.gather(*(asyncio.create_task(api.manga(id).GET()) for id in lst))
        ...
    finally:
        await client.close()
  
asyncio.run(fetch())
