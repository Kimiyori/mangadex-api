

import asyncio
import random

from uuid import UUID

from mangadex import ApiMethod, ApiWrapper


class MangaDex:
    """
    Class for manga part of api
    """


    @classmethod
    async def create(cls,
                 username: str,
                 email: str,
                 password: str):
        self = MangaDex()
        self.session = await ApiWrapper.create(username, email, password)
        self.api: ApiMethod = await self.session.get_api()
        self.list_params: list[str] = ['authors', 'artists', 'includedTags', 'excludedTags', 'status', 'originalLanguage',
                                       'excludedOriginalLanguage', 'availableTranslatedLanguage', 'publicationDemographic', 
                                       'ids', 'contentRating', 'includes', 'ids','manga','locales','uploaders']
        return self

    async def _validate_params(self, **kwargs):
        """
        Method for check params, given as args. It changes list params for api requirements. 
        For example: 'artists' becomes 'artists[]'
        """
        def _check_key(key):
            if key in self.list_params:
                return f'{key}[]' if key[-2:] != '[]' else key
            else:
                return key
        data = {_check_key(key): value for key, value in kwargs.items()}
        return data

    # GET methods

    async def get_list(self, **kwargs):
        """
        get manga list with given arguments. Full list arguments given in https://api.mangadex.org/swagger.html#/Manga/get-search-manga
        """
        data = await self._validate_params(**kwargs)
        return await self.api.manga.GET(**data)

    async def get_manga_id(self, id: UUID, **kwargs):
        """
        get instance specific title with given uuid
        :params uuid id: pass title uuid
        """
        return await self.api.manga(id).GET(**kwargs)

    async def get_random_manga(self):
        """
        get random title
        """
        return await self.api.manga.random.GET()

    async def get_tag_list(self):
        """
        get tag list
        """
        return await self.api.manga.tag.GET()

    async def get_reading_status_id(self, id: UUID):
        """
        get logged user reading status given title 
        """
        return await self.api.manga(id).status.GET()

    async def get_list_reading_status_for_user(self):
        """
        return list all user titles and their reading status for given user
        """
        return await self.api.manga.status.GET()

    async def get_manga_relation(self, id: UUID):
        """
        return relation for given manga
        """
        return await self.api.manga(id).relation.GET()

    async def get_manga_follow(self, limit: int = 10, offset: int = 0):
        """
        return titles that logged user follows

        :params int limit: max 100

        :params int offset: int
        """
        return await self.api.user.follows.manga.GET(limit=limit, offset=offset)

    async def title_search(self, title: str):
        """
        search manga with title name
        """
        return await self.api.manga.GET(title=title)

    async def get_random_title_from_user_list(self, reading_status: str = None, title_status: str = None):
        """get random title from your list
        ":params str reading_status: the type of your reading status of the ешеду you want to randomly select.
                                    You can skip this value or choose between the following options:[reading, on_hold, plan_to_read, dropped, re_reading, completed]
         :params str title_status: status of the title that you want to pick.
                                    You can skip this value or choose between the following options:[ongoing,hiatus,completed,cancelled]
         """
        author_state = await self.get_list_reading_status_for_user()
        if reading_status:
            author_state = [key for key in author_state['statuses'].keys(
            ) if author_state['statuses'][key] == reading_status]
        else:
            author_state = [key for key in author_state['statuses'].keys()]
        list_titles = []
        offset = 0
        while True:
            titles = await self.get_manga_follow(limit=100, offset=offset)
            if titles['data']:
                if title_status:
                    list_titles.extend([title['id'] for title in titles['data']
                                        if title['attributes']['status'] == title_status])
                else:
                    list_titles.extend([title['id']
                                       for title in titles['data']])
                offset = offset+100
            else:
                break

        intersection = set(list_titles) & set(author_state)
        title = random.choice(list(intersection))
        result=await self.get_manga_id(title)
        return result['data']['attributes']['title']

    async def get_logged_user_custom_lists(self):
        """
        return all logged user custom lists
        """
        return await self.api.user.list.GET()

    async def get_custom_list_user(self, id: UUID):
        """
        return all custom lists of user with given id
        """
        return await self.api.user(id).list.GET()

    async def get_custom_list_id(self, id: UUID):
        """
        return user custom list with given id
        """
        return await self.api.list(id).GET()

    async def get_authors(self, **kwargs):
        """
        Return list of authors. Possible arguments:

        :params int limit: default 10,max=100

        :params int offset: itt's just an offset :|

        :params Optional[list]UUID] ids[]: pass list of authors

        :params str name: name of author
        """
        data = await self._validate_params(**kwargs)
        return await self.api.author.GET(**data)

    async def get_author(self, id: UUID):
        """
        Return author
        """
        return await self.api.author(id).GET()
    
    async def get_covers(self,**kwargs):
        """
        Return covers. Possible arguments given in https://api.mangadex.org/swagger.html#/Cover/get-cover
        """
        data = await self._validate_params(**kwargs)
        return await self.api.cover.GET(**data)
    
    async def get_cover_id(self,id:UUID):
        return await self.api.cover(id).GET()
    
    async def get_chapter(self,**kwargs):
        """
        return chapter info. 
        """
        data = await self._validate_params(**kwargs)
        return await self.api.chapter.GET(**data)
    
    async def get_chapter_id(self,**kwargs):
        """
        return chapter info. 
        """
        return await self.api.chapter(id).GET(**kwargs)

    # PUT METHODS

    async def update_list_demographic(self, id: UUID, demographic: str):
        """
        put all user titles with given demographic into user custom list with given id
        """
        list = await self.get_custom_list_id(id)
        version = list['data']['attributes']['version']
        list_titles = []
        offset = 0
        while True:
            titles = await self.get_manga_follow(limit=100, offset=offset)
            if titles['data']:
                list_titles.extend([title['id'] for title in titles['data']
                                   if title['attributes']['publicationDemographic'] == demographic])
                offset = offset+100
            else:
                break
        print(titles)
        response = await self.api.list(id).PUT(manga=list_titles, version=version)
        return response

    # POST METHODS

    async def update_manga_status(self, id: UUID, status: str):
        """
        Update reading status for given manga

        status must have one of following options:[reading, on_hold, plan_to_read, dropped, re_reading, completed]
        """
        return await self.api.manga(id).status.GET(status=status)

    # DELETE METHODS

    async def unfollow_manga(self, id: UUID):
        return await self.api.manga(id).follow.DELETE()

