from ._custom_webdriver_waits import CommentHasBeenPosted, ElementsHaveUpdated, InputBarHasCleared
from ._exceptions import ClosedWebdriverException, CommentNotSharedByUserException, \
    IncorrectLinkException, LimitedCommentsException, ReplyNotFoundException, TryCountExceeded
from ._instagram import Instagram

from datetime import datetime as dt
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.color import Color
from selenium.webdriver.support.ui import WebDriverWait
from typing import Dict, Tuple, Union
from urllib3.exceptions import MaxRetryError

import json
import pytz
import re
import selenium
import time


class InstagramPost(Instagram):
    """
    Simulates post interactions and scrapes its data.

    Can be used within a context manager, to allocate and release resources. 
    If used without, make sure to use .close() function to close the automated browser controlled by Selenium.

    Args
    ----
        post_url : str
            URL of the post
        driver : Union[selenium.webdriver.Chrome, None] (default value is None)
            automated browser controlled by Selenium
            (if None, user_creds has to be passed in)
        user_creds : Union[Tuple[str, str], None] (default value is None)
            user's credentials
            (if not None, must be of length 2 and have the username and password as its first and second values)
            (if None, driver has to be passed in)
        headless_browser : bool (default value is True)
            whether the webdriver is headless or not
    
    Attributes
    ----------
        driver : selenium.webdriver.Chrome
            automated browser controlled by Selenium
        url : str
            URL of the post
        user : Union[str, list]
            user(s) who shared the post
        datetime : str
            datetime at which the post was shared
        likes_count : Union[int, None]
            number of likes the post has received
        caption : str
            caption of the post
        type : str
            type of post (caroussel, reel or single image)
        media_count : int
            number of pictures or videos the post contains
        media_src : Union[str, list]
            link to each picture and video's source page 
        location : Union[str, None]
            geographical location of the post
        audio : Union[str, None]
            the song that was added to the post

    Methods
    -------
        get_likes()
            Scrapes the post's likes list to get usernames of people who liked the post.
        get_comments(max=None)
            Scrapes comments published under the post (returns a list of dictionaries).
        print_comments(max=None)
            Prints comments published under the post.
        like_post()
            Adds a like to the post.
        unlike_post()
            Removes user's like from the post.
        add_comment(comment_text)
            Adds a comment to the post.
        delete_comment(comment_url)
            Deletes a comment posted by user.
        like_comment(comment_url)
            Adds a like to a comment.
        unlike_comment(comment_url)
            Removes user's like from a comment.
        add_reply(comment_url, reply_text)
            Adds a reply to a comment under the post.
        delete_reply(comment_url, reply_text):
            Deletes a reply to a comment under the post.
        close()
            Closes the instance's webdriver.
    """
    
    def __init__(self, 
                 post_url: str, 
                 driver: Union[selenium.webdriver.Chrome, None] = None, 
                 user_creds: Union[Tuple[str, str], None] = None, 
                 headless_browser : bool = True) -> None:
        """
        Creates an instance of the class InstagramPost and sets its attributes.

        Args
        ----
            post_url : str
                URL of the post
            driver : Union[selenium.webdriver.Chrome, None] (default value is None)
                automated browser controlled by selenium
                (if None, user_creds has to be passed in)
            user_creds : Union[Tuple[str, str], None] (default value is None)
                user's credentials
                (if not None, must be of length 2 and have the username and password as its first and second values)
                (if None, driver has to be passed in)
            headless_browser : bool (default value is True)
                whether the webdriver is headless or not 
                (applicable only when new webdriver is instaciated : cannot change properties of already created webdriver)

        Raises
        ------
            TypeError
                If any of the arguments is not the correct type.
            NoInternetConnectionException
                If there is no internet connection
            IncorrectCredentialsException
                If the credentials user_creds are incorrect.
            BlockedAccountException
                If the account corresponding to user_creds is blocked.
        """
        # check that post_url argument is a string
        if (not isinstance(post_url, str)) or (post_url.replace(" ", "") == ""):
            raise TypeError("'post_url' argument must be a non-empty string.")
        # check that driver argument is either a selenium.webdriver.Chrome or is equal to None
        if (not isinstance(driver, selenium.webdriver.Chrome)) and (driver is not None):
            raise TypeError("'driver' argument must be a selenium.webdriver or equal to None.")
        # check that user_creds argument is either a tuple or is equal to None
        if (not isinstance(user_creds, tuple)) and (user_creds is not None):
            raise TypeError("'user_creds' argument must be a tuple or equal to None.")
        # check that user_creds argument contains two strings, if it's not None
        if user_creds is not None:
            if len(user_creds) != 2:
                raise TypeError("'user_creds' argument must be of length 2.")
            if any((not isinstance(value, str)) or \
                    (value.replace(" ", "") == "") for value in user_creds):
                raise TypeError("'user_creds' argument must only contain non-empty strings.")
        # check that user_creds and driver arguments are not both None
        if (user_creds is None) and (driver is None):
            raise TypeError("'user_creds' and 'driver' arguments can not both be equal to None.")
        # check that headless_browser argument is a bool
        if (not isinstance(headless_browser, bool)):
            raise TypeError("'headless_browser' argument must be a bool.")
        # open new webdriver to Instagram and log in, if driver does not already exist
        if not driver:
            self._initiate_instagram(user_creds, headless=headless_browser)
        else:
            self.driver = driver
        self.__user_creds = user_creds
        self.url = post_url
        try:
            # get post url if not already on page
            if self.driver.current_url != self.url:
                self.driver.get(self.url)
        except MaxRetryError:
            raise ClosedWebdriverException
        # check if log in was succesful
        self._check_logged_in()
        # check if link to post exists
        self.__check_link()
        # get user(s) who shared post
        self.user = self.__get_user()
        # get datetime at which post was shared
        self.datetime = self.__get_datetime()
        # get number of likes post has received       
        self.likes_count = self.__get_likes_count()
        # get geographical location of post
        self.location = self.__get_location()
        # get song that was added to post
        self.audio = self.__get_audio()
        # get link to each picture and video's source page 
        self.media_src = self.__get_media_src()
        # get number of pictures or videos post contains
        self.media_count = self.__get_media_count()
        # get type of post (caroussel, reel or single image)
        self.type = self.__get_type()
        # get post caption
        self.caption = self.__get_caption()

    def __repr__(self) -> str:
        """
        Creates the representation of the object.

        Returns
        -------
            str : the representation of the object 
        """
        representation = f"InstagramPost(post_url:\'{self.url}\', driver:{self.driver}, user_creds:{self.__user_creds})"
        return representation

    def __str__(self) -> str:
        """
        Indicates the way an instance should be printed.

        Returns
        -------
            str : the string printed when the print function is called on the instance
        """
        # store instance's attributes in dictionary
        post_data = {
            "URL": self.url,
            "user": self.user,
            "datetime": self.datetime,
            "type": self.type,
            "caption": self.caption,
            "likes count": self.likes_count,
            "location": self.location,
            "audio": self.audio,
            "media count": self.media_count,
            "media source": self.media_src
        }
        # convert dictionary to json, for better readability
        data_to_json = json.dumps(post_data, 
                                  indent=4)
        return data_to_json
    
    def __check_link(self) -> None:
        """
        Checks whether link exists and leads to a post.

        Raises
        ------
            IncorrectLinkException
                If page does not exist or not a post URL.
        """
        # selector for when page does not exist
        incorrect_link_selector = "//a[text()='Go back to Instagram.']"
        # selector for when page exists
        correct_link_selector = "//div[@role='button']"
        # find any of the elements above
        page_existence_selector = f"{incorrect_link_selector}|{correct_link_selector}"
        page_existence = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, page_existence_selector)))
        # if page does not exist, raise IncorrectLinkException
        if page_existence.tag_name == "a":
            raise IncorrectLinkException
        # if self.url not a post URL, raise IncorrectLinkException
        elif "https://www.instagram.com/p/" not in self.url:            
            raise IncorrectLinkException(f"The link {self.url} does not lead to a post.")

    def __get_header(self) -> selenium.webdriver.remote.webelement.WebElement:
        """
        Finds the header part of the post.

        Returns
        -------
            selenium.webdriver.remote.webelement.WebElement : the WebElement representing the top part
        """
        # find "more options" button
        more_options_button_selector = "[aria-label='More options']"       
        more_options_button = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, more_options_button_selector)))
        # get header part from "more options" button
        header_selector = "." + "/.."*6
        header = more_options_button.find_element(By.XPATH, 
                                                  header_selector)
        return header

    def __get_user(self) -> Union[str, list]:
        """
        Finds the user(s) who shared the post.

        Returns
        -------
            Union[str, list] : the user(s) who shared the post (str if only one, list if more than one)
        """
        # get header part of the post
        header = self.__get_header()
        # find usernames in header
        users_selector = ".//a[not(contains(@href, '/audio/'))][not(contains(@href, '/locations/'))][not(@style)]"
        users_elements = header.find_elements(By.XPATH, 
                                              users_selector)
        # get text attribute of each element
        users = [user.text for user in users_elements]
        # if more than 2 users, "Collaborators" window needs to be opened
        for user in users_elements:
            # find if "n others" button is present
            if " others" in user.text:
                # click "n others" button
                user.click()
                # find "Collaborators" window
                collaborators_window_selector = "//div[@role='heading']" + "/.."*5
                collaborators_window = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, collaborators_window_selector)))
                # find usernames in window
                users_selector = ".//div/a[not(img)]"
                users_elements = WebDriverWait(collaborators_window, 30).until(
                    EC.presence_of_all_elements_located((By.XPATH, users_selector)))
                # get text attribute of each element
                users = [user.text for user in users_elements]
                # find window's close button
                close_button_selector = "svg[aria-label='Close']"
                close_button = collaborators_window.find_element(By.CSS_SELECTOR, 
                                                                    close_button_selector)
                # click button
                close_button.click()
                break
        # if only one user found, only get the username instead of the username inside a list
        if len(users) == 1:
            users = users[0]
        return users

    def __get_location(self) -> Union[str, None]:
        """
        Finds the geographical location of the post.

        Returns
        -------
            Union[str, None] : the geographical location of the post (str if there is one, None if not)
        """
        # get header part of the post
        header = self.__get_header()
        try:
            # find location if it exists
            location_selector = ".//a[contains(@href, '/locations/')]"
            location = header.find_element(By.XPATH, 
                                           location_selector)
            return location.text
        except NoSuchElementException:
            # return None if it does not exist
            return None

    def __get_audio(self) -> Union[str, None]:
        """
        Finds the audio that was added to the post 
        (works only on reels as the audio is not displayed on the Instagram desktop version).

        Returns
        -------
            Union[str, None] : the song name of the audio that was added to the post (str if there is one, None if not)
        """
        # get header part of the post
        header = self.__get_header()
        try:
            # find song name if there is one
            location_selector = ".//a[contains(@href, '/audio/')]"
            location = header.find_element(By.XPATH, 
                                           location_selector)
            return location.text
        except NoSuchElementException:
            # return None if it does not exist
            return None
        
    def __get_likes_count(self) -> Union[int, None]:
        """
        Finds the number of likes the post has received.

        Returns
        -------
            Union[int, None] : how many time the post received a like (int if it has likes, None if not)
        """
        # selector for when post has likes and is carousel or single image post
        likes_selector = "//a[contains(@href, '/liked_by/')][span[text()]]"
        # selector for when post has likes and is a video
        views_selector = "//span[contains(text(), ' views')][span]"
        # selector for when post has no likes (sometimes not present when post has no likes)
        no_likes_selector = "//div[@role='button'][text()='like this']"
        # find any of the elements above  
        likes_count_selector = f"{likes_selector}|{views_selector}|{no_likes_selector}"
        try:
            likes_count = self.driver.find_element(By.XPATH, 
                                                   likes_count_selector)
        except NoSuchElementException:
            # if no element is present, then post has no like
            return 0
        # if likes count hidden, return None
        if likes_count.text == "others":
            return None
        else:
            # if post has no likes, return 0
            if likes_count.tag_name == "div":
                return 0
            else:
                # if post is a video, element displays number of views instead of likes count
                if "views" in likes_count.text:
                    # click 'views' button to display likes count
                    likes_count.click()
                    # find likes count
                    likes_selector = "." + "/.."*2 + "//div[contains(text(), ' likes')]"
                    likes_count = likes_count.find_element(By.XPATH, 
                                                           likes_selector)
                    # click 'views' button again to hide likes count
                    likes_count.click()
                # get text of element and extract digits
                likes_count = re.findall(r"[0-9]+", 
                                         likes_count.text)
                likes_count = int("".join(likes_count))
                return likes_count
        
    def __get_datetime(self) -> str:
        """
        Finds the datetime at which the post was shared.

        Returns
        -------
            str : what day and time the post was published
        """
        # find like or unlike button to get footer part of post
        like_button_selector = "//*[@aria-label='Like'][@height='24']"
        unlike_button_selector = "//*[@aria-label='Unlike'][@height='24']"
        button_selector = f"{like_button_selector}|{unlike_button_selector}"
        button = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, button_selector)))
        # find footer part from button element
        footer_selector = "." + "/.."*8
        footer = button.find_element(By.XPATH, 
                                     footer_selector)
        # find datetime from footer element
        datetime_selector = "time"
        datetime = footer.find_element(By.TAG_NAME, 
                                       datetime_selector)
        # get datetime attribute from datetime element
        datetime = datetime.get_attribute("datetime")
        # convert datetime to datetime.datetime then back to string
        datetime = dt.strptime(datetime, "%Y-%m-%dT%H:%M:%S.%fZ")
        datetime = datetime.strftime("%d/%m/%Y, %H:%M:%S")
        return datetime
    
    def __get_media_src(self) -> Union[str, list]:
        """
        Finds the link to each picture and video's source page, contained in the post.

        Returns
        -------
            Union[str, list] : the link to each video or video 
                (list if the post is a carousel, str if it has only one pic or video)
        """
        # find post window
        header = self.__get_header()
        post_selector = "." + "/.."*4
        post = header.find_element(By.XPATH, post_selector)
        media_src = set()
        while True:
            # selector for pictures 
            img_selector = ".//div[@style]/img[@style='object-fit: cover;']"
            # selector for videos 
            video_selector = ".//video"
            # find all the picture and video elements present in the post
            media_selector = f"{img_selector}|{video_selector}"
            media = post.find_elements(By.XPATH, 
                                       media_selector)
            try:
                # get each element's src attribute and add it to the media_src set
                media = [medium.get_attribute("src") for medium in media]
            except StaleElementReferenceException:
                # find media elements again if stale
                media = self.driver.find_elements(By.XPATH, 
                                                  media_selector)
                media = [medium.get_attribute("src") for medium in media]
            media_src.update(media)
            try:
                # if post is caroussel, find "next" button if there is one 
                next_button_selector = "[aria-label='Next']"
                next_button = self.driver.find_element(By.CSS_SELECTOR, 
                                                       next_button_selector)
                # wait until button is clickable
                WebDriverWait(self.driver, 30).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, next_button_selector)))
                # click button
                next_button.click()
            except NoSuchElementException:
                # break out of while loop if not caroussel or no more "next" button
                break
        # convert set to list
        media_src = list(media_src)
        # if only one video or picture, only get its source instead of it inside a list
        if len(media_src) == 1:
            media_src = media_src[0]
        return media_src
    
    def __get_media_count(self) -> int:
        """
        Finds how many pictures or videos the post contains.

        Returns
        -------
            int : how many pictures or videos the post has
        """
        if type(self.media_src) == str:
            # if only one picture/video, self.media_src is string (see self.__get_media_src method)
            return 1
        else:
            return len(self.media_src)
    
    def __get_type(self) -> str:
        """
        Finds the type of post (caroussel, reel or single image).

        Returns
        -------
            str : the type of post
        """
        if type(self.media_src) == str:
            # if only one picture/video, post is either a reel or a single image
            if self.media_src.startswith("blob:"):
                # if medium source url starts with "blob:", medium is reel
                return "reel"
            else:
                return "single image"
        else:
            # if multiple pictures and/or videos, post is caroussel
            return "caroussel"
        
    def __get_caption(self) -> Union[str, None]:
        """
        Finds the post caption.

        Returns
        -------
            Union[str, None] : the text that accompanies the post (or None if there is none)
        """
        # find caption element
        caption_selector = "//div/span[time]" + "/.."*2 + "/span"
        try:
            caption = self.driver.find_element(By.XPATH, 
                                               caption_selector)
            return caption.text
        except NoSuchElementException:
            # if no caption element, then post has no caption
            return None
    
    def get_likes(self) -> Union[list, None]:
        """
        Scrapes the post's likes list to get usernames of people who liked the post. 
        
        Returns
        -------
            Union[list, None] : the list of usernames (is None if unable to view the likes list)

        Raises
        ------
            TryCountExceeded
                If method failed 3 times.
        """
        TRY_COUNT = 3
        for _try in range(TRY_COUNT):
            try:
                # get post's page if not on it already
                self._get_self_page()
                # wait for page to be fully loaded 
                # (any method starting with a WebDriverWait would work)
                # to prevent using a WebDriverWait instead of find_elements in this method
                self.__get_datetime()
                # selector for when post has likes list 
                likes_selector = "//a[contains(@href, '/liked_by/')][span[text()]]"
                # selector for when post is a video (does not have likes list in this case)
                views_selector = "//span[contains(text(), ' views')][span]"
                # selector for when post has no likes
                no_likes_selector = "//div[@role='button'][text()='like this']"
                # find any of the elements above
                try:
                    likes_count_selector = f"{likes_selector}|{views_selector}|{no_likes_selector}"
                    likes_count = self.driver.find_element(By.XPATH, 
                                                        likes_count_selector) 
                except NoSuchElementException:
                    # if no element is present, then post has no like
                    return []
                if likes_count.tag_name == "a":
                    # if post has likes list, click "liked by" button to show likes window
                    self.driver.execute_script("arguments[0].click();", 
                                               likes_count)
                    # find likes window element
                    top_section_selector = "//h2"
                    frame_selector = top_section_selector + "/.."*2 + "//div[contains(@style, 'hidden auto')]"
                    frame = WebDriverWait(self.driver, 30).until(
                        EC.visibility_of_element_located((By.XPATH, frame_selector)))
                    self._save_screenshot("likes_window_opened") # take screenshot if test
                    # create set to only list unique usernames
                    likes = set()
                    # create list to compare previously found usernames and newly found usernames after scroll
                    usernames = []
                    while True:
                        # find usernames
                        usernames_selector = "./.." + "//a[not(@style)]"
                        # wait until usernames have updated after a scroll
                        # i.e. wait until previously found usernames and newly found 
                        # usernames are different to ensure elements are attached to the DOM
                        usernames = WebDriverWait(frame, 30).until(
                            ElementsHaveUpdated((By.XPATH, usernames_selector), usernames))
                        # update likes set with usernames' text attribute
                        likes.update([username.text for username in usernames])
                        # get number of pixels by which likes window's content is scrolled from its top edge, before the scroll
                        previous_height = self.driver.execute_script("return arguments[0].scrollTop;", 
                                                                    frame)
                        # scroll likes window, downwards, by 500 pixels 
                        self.driver.execute_script("arguments[0].scrollTop += 500;", 
                                                frame)
                        # get number of pixels by which likes window's content is scrolled from its top edge, after the scroll
                        current_height = self.driver.execute_script("return arguments[0].scrollTop;", 
                                                                    frame)
                        if previous_height == current_height:
                            # if no pixels were scrolled, i.e. bottom of window had been reached, break out of while loop
                            break
                    # find likes window's close button
                    close_button_selector = top_section_selector + "/.." + "//div[@role='button']"
                    close_button = self.driver.find_element(By.XPATH, 
                                                            close_button_selector)
                    # click close button
                    self.driver.execute_script("arguments[0].click();", 
                                            close_button)
                    # convert set to list due to personnal preference when printing
                    likes = list(likes)
                elif likes_count.tag_name == "div":
                    # if post has no likes, set likes to empty list
                    likes = []
                else:
                    # if post is video (does not have likes list in this case), 
                    # set likes to None to differentiate between having no likes and being unable to get likes list
                    likes = None
                return likes
            except TimeoutException:
                # find likes window's close button
                close_button_selector = top_section_selector + "/.." + "//div[@role='button']"
                close_button = self.driver.find_element(By.XPATH, 
                                                        close_button_selector)
                # click close button
                self.driver.execute_script("arguments[0].click();", 
                                        close_button)
        raise TryCountExceeded
    
    def __get_comment_data(self, 
                           comment: str) -> Tuple[str, Dict[str, str]]:
        """
        Scrapes data of a comment (publisher, datetime, text, likes count and URL).

        Args
        ----
            comment : selenium.webdriver.remote.webelement.WebElement
                WebElement representing the comment
        
        Returns
        -------
            Tuple[str, Dict[str, str]] : the comment's URL and a dict containing its data 
                (four string key-value pairs: datetime, url, publisher and text)
        """
        # find datetime from comment element
        datetime_selector = ".//time"
        datetime = comment.find_element(By.XPATH, 
                                        datetime_selector)
        datetime = datetime.get_attribute("datetime")
        # convert datetime to datetime.datetime then back to string
        datetime = dt.strptime(datetime, "%Y-%m-%dT%H:%M:%S.%fZ")
        datetime = datetime.strftime("%d/%m/%Y, %H:%M:%S")
        # find url from comment element
        url_selector = ".//time" + "/.."
        url = comment.find_element(By.XPATH, 
                                   url_selector)
        url = url.get_attribute("href")
        # find publisher from comment element
        publisher_selector = ".//time" + "/.."*3 + "//a[not(time)]"
        publisher = comment.find_element(By.XPATH, 
                                         publisher_selector)
        publisher = publisher.text
        # find text from comment element
        text_selector = ".//span[@style='----base-line-clamp-line-height: 18px; --lineHeight: 18px;'][not(a/time)][not(span)]"
        text = comment.find_element(By.XPATH, 
                                    text_selector)
        text = text.text
        # find likes count from comment element if it has likes (set to 0 if not)
        try:
            likes_count_selector = ".//div[@role='button']//span[contains(text(), 'like')]"
            likes_count = comment.find_element(By.XPATH, 
                                               likes_count_selector)
            likes_count = likes_count.text
            # extract digits from string
            likes_count = re.findall(r"[0-9]+", likes_count)
            likes_count = int("".join(likes_count))
        except NoSuchElementException:
            likes_count = 0
        # store scraped data in dictionary
        comment_data = {
            "username": publisher, 
            "text": text, 
            "datetime": datetime, 
            "likes count": likes_count
        }   
        return url, comment_data
    
    def get_comments(self, 
                     max: Union[int, None] = None) -> Dict[str, Dict]:
        """
        Scrapes comments published under the post.

        Args
        ----
            max : Union[int, None] (default value is None)
                Maximum number of comments to get
                (if not set, will scrape all the comments)

        Returns
        -------
            Dict[str, Dict] : a dictionary of dictionaries where each key-value pair represents a different comment
                Each value has its key as the comment's URL and follows the structure :
                    comment_URL : {
                        "username": comment_username, 
                        "text": comment_text, 
                        "datetime": comment_datetime,
                        "likes count": comment_likes_count,
                        "replies": [
                            {
                                "username": reply_username, 
                                "text": reply_text, 
                                "datetime": reply_datetime,
                                "likes count": reply_likes_count
                            },
                        ]
                    }

        Raises
        ------
            TypeError
                If max argument is not an integer or None.
        """
        # check that max argument is integer or NoneType
        if (not isinstance(max, int)) and (max is not None):
            raise TypeError("'max' argument must be None or an integer.")
        # get post's page
        self.driver.get(self.url)
        # create dict that will contain comments
        post_comments = dict()
        # find comment section of the post
        comments_selector = "//a/time[@datetime]" + "/.."*9 + "/parent::div"
        comment_section_selector = comments_selector + "/.."*3
        no_comments_selector = "//*[text()='No comments yet.']" # selector for when post has no comments
        comment_section_selector = f"{comment_section_selector}|{no_comments_selector}"
        comment_section = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, comment_section_selector)))
        self._save_screenshot("page_reached_for_comments") # take screenshot if test
        # flag to raise if max value has been reached
        max_reached = False
        if comment_section.tag_name == "div":
            # if comment section has comments, scroll it until max reached or bottom of page reached
            while True:
                # find comments
                comments = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_all_elements_located((By.XPATH, comments_selector)))
                for comment in comments:
                    # check if max has been reached (if max)
                    if max is not None:
                        if len(post_comments.keys()) >= max:
                            # raise max_reached flag
                            max_reached = True
                            # break out of for loop
                            break
                    # find current comment element to avoid changed DOM issues
                    current_comment_selector = "./div[not(ul)][not(@class)]"
                    current_comment = comment.find_element(By.XPATH, 
                                                           current_comment_selector)
                    # scrape comment data  
                    comment_url, comment_data = self.__get_comment_data(current_comment)
                    # create list that will contain comment's replies
                    comment_data["replies"] = []
                    # create list to compare previously found replies and newly found replies after scroll
                    replies = []
                    # check that current comment is not already in post_comments dict
                    if not comment_url in post_comments.keys():
                        # check if comment has replies
                        try:
                            # find "view_replies" button if it exists
                            view_replies_selector = ".//div[@role='button']//span[contains(text(), 'replies')]"
                            view_replies = comment.find_element(By.XPATH, 
                                                                view_replies_selector)
                            # set has_replies to True
                            has_replies = True
                        except NoSuchElementException:
                            # if it does not exist set has_replies to False
                            has_replies = False
                        if has_replies:
                            # scroll until "view_replies" button is visible
                            self.driver.execute_script("arguments[0].scrollIntoView();", 
                                                       view_replies)
                            # click "view_replies" button
                            self.driver.execute_script("arguments[0].click();", 
                                                       view_replies)
                            while True:
                                # selector for "show more replies" button
                                show_more_replies_selector = ".//span[text()='Show more replies']"
                                # selector for "hide all replies" button
                                hide_replies_selector = ".//span[text()='Hide all replies']"
                                # find any of the buttons, to ensure page has loaded 
                                button_selector = f"{show_more_replies_selector}|{hide_replies_selector}"
                                WebDriverWait(comment, 30).until(
                                    EC.presence_of_element_located((By.XPATH, button_selector)))
                                # find comment's replies
                                replies_selector = ".//span[contains(text(), ' replies')]" + "/.."*3 + "/ul/div"
                                try:
                                    # simple .find_element to ensure comment really has replies 
                                    # (to prevent "show more replies" button clicked but no replies)
                                    comment.find_element(By.XPATH, 
                                                         replies_selector)
                                except NoSuchElementException:
                                    # break out of while loop if comment has in reality no replies
                                    break
                                # wait until replies have updated after a scroll
                                # i.e. wait until previously found replies and newly found replies 
                                # are different to ensure elements are attached to the DOM
                                replies = WebDriverWait(comment, 30).until(
                                    ElementsHaveUpdated((By.XPATH, replies_selector), replies))
                                for reply in replies:
                                    # scrape each reply's comment data 
                                    reply_url, reply_data = self.__get_comment_data(reply)
                                    # add reply data to current comment's "replies" list
                                    comment_data["replies"].append(reply_data)
                                try:
                                    # find "show more replies" button if there is one
                                    show_more_replies = comment.find_element(By.XPATH, 
                                                                             show_more_replies_selector)
                                    # scroll until "show more replies" button is visible
                                    self.driver.execute_script("arguments[0].scrollIntoView();", 
                                                               show_more_replies)
                                    # ensure that "show more replies" is clickable
                                    WebDriverWait(comment, 30).until(
                                        EC.element_to_be_clickable((By.XPATH, show_more_replies_selector)))
                                    # click "show more replies" button
                                    self.driver.execute_script("arguments[0].click();", 
                                                               show_more_replies)
                                except NoSuchElementException:
                                    # if no "show more replies" button, then no more replies : break out of while loop 
                                    break
                        # add current comment's data (which contains its replies too) to post_comments dict
                        post_comments[comment_url] = comment_data
                # get number of pixels by which comment section's content is scrolled from its top edge, before the scroll
                previous_height = self.driver.execute_script("return arguments[0].scrollTop;", 
                                                             comment_section)
                # scroll comment section, downwards, by 300 pixels
                self.driver.execute_script("arguments[0].scrollTop += 300;", 
                                           comment_section)
                # get number of pixels by which comment section's content is scrolled from its top edge, after the scroll
                current_height = self.driver.execute_script("return arguments[0].scrollTop;", 
                                                            comment_section)
                if previous_height == current_height:
                    # if no pixels were scrolled, check if bottom of comment section has been reached
                    try:
                        # find loading symbol if it exists 
                        # (located at the bottom after scrolling to the bottom, appears until new content is loaded)
                        loading_selector = "[aria-label='Loading...']"
                        self.driver.find_element(By.CSS_SELECTOR, 
                                                 loading_selector)
                    except NoSuchElementException:
                        # if no loading symbol, then bottom of comment section has been reached : 
                        # break out of while loop because no more comments to scrape
                        break
                if max_reached:
                    # break out of while loop
                    break
        return post_comments
    
    def print_comments(self, 
                       max: Union[int, None] = None) -> None:
        """
        Prints comments published under the post.
        
        Uses .get_comments() method, but instead of returning a dictionary, 
        prints a JSON version of the dictionary for better readability.

        Args
        ----
            Union[int, None] (default value is None)
                Maximum number of comments to get
                (if not set, will print all the comments)

        Raises
        ------
            TypeError
                If max argument is not an integer or None.
        """
        # check that max argument is integer or NoneType
        if (not isinstance(max, int)) and (max is not None):
            raise TypeError("'max' argument must be None or an integer.")
        # scrape comments (either <=max, or all of them if max=None)
        comments = self.get_comments(max=max)
        # convert dictionary to JSON
        comments_to_json = json.dumps(comments, 
                                      indent=4)
        # print JSON version of the dictionary
        print(comments_to_json)
    
    def __get_like_button(self) -> selenium.webdriver.remote.webelement.WebElement:
        """
        Finds the like (or unlike) button element.

        Returns
        -------
            selenium.webdriver.remote.webelement.WebElement : the WebElement representing the like (or unlike) button
        """
        # selector for when post has not been liked
        like_button_selector = "//*[@aria-label='Like'][@height='24']"
        # selector for when post has already been liked
        unlike_button_selector = "//*[@aria-label='Unlike'][@height='24']"
        # find button
        button_selector = f"{like_button_selector}|{unlike_button_selector}"
        button = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, button_selector)))
        return button
    
    def like_post(self) -> None:
        """
        Adds a like to the post.
        """
        # get post's page if not on it already
        self._get_self_page()
        # find like or unlike button
        button = self.__get_like_button()
        try:
            # get button color
            previous_color = Color.from_string(button.value_of_css_property("fill")) 
        except StaleElementReferenceException:
            # if button is stale, find button element again
            button = self.__get_like_button()
            previous_color = Color.from_string(button.value_of_css_property("fill"))
        # check if post has not been liked already (if like: no need to like again)
        if button.get_attribute("aria-label") == "Like":
            # set timeout
            start_time = time.time()
            TIMEOUT = 30
            while True:
                # check if timeout passed
                if time.time() - start_time > TIMEOUT:
                    raise TimeoutException
                # find clickable element from button element
                clickable_button_selector = "." + "/.."*3
                clickable_button = button.find_element(By.XPATH, 
                                                       clickable_button_selector)
                # click button
                ActionChains(self.driver).move_to_element(clickable_button).click().perform()
                # check if fill color has changed, i.e. if like has been uploaded
                button = self.__get_like_button()
                try:
                    current_color = Color.from_string(button.value_of_css_property("fill"))
                except StaleElementReferenceException:
                    # if button is stale, find button element again
                    button = self.__get_like_button()
                    current_color = Color.from_string(button.value_of_css_property("fill"))
                if current_color != previous_color:
                    break
        # take screenshot if test
        self._save_screenshot("post_liked")

    def unlike_post(self) -> None:
        """
        Removes user's like from the post.
        """
        # get post's page if not on it already
        self._get_self_page()
        # find like or unlike button
        button = self.__get_like_button()
        try:
            # get button color
            previous_color = Color.from_string(button.value_of_css_property("fill"))
        except StaleElementReferenceException:
            # if button is stale, find button element again
            button = self.__get_like_button()
            previous_color = Color.from_string(button.value_of_css_property("fill"))
        # check if post has been liked (if no like: no need to unlike)
        if button.get_attribute("aria-label") == "Unlike":
            # set timeout
            start_time = time.time()
            TIMEOUT = 30
            while True:
                # check if timeout passed
                if time.time() - start_time > TIMEOUT:
                    raise TimeoutException
                # find clickable element from button element
                clickable_button_selector = "." + "/.."*3
                clickable_button = button.find_element(By.XPATH, 
                                                       clickable_button_selector)
                
                # click button
                ActionChains(self.driver).move_to_element(clickable_button).click().perform()
                # check if fill color has changed, i.e. if unlike has been uploaded
                button = self.__get_like_button()
                try:
                    current_color = Color.from_string(button.value_of_css_property("fill"))
                except StaleElementReferenceException:
                    # if button is stale, find button element again
                    button = self.__get_like_button()
                    current_color = Color.from_string(button.value_of_css_property("fill"))
                if current_color != previous_color:
                    break
        # take screenshot if test
        self._save_screenshot("post_unliked")
        
    def add_comment(self, 
                    comment_text: str) -> Tuple[str, Dict[str, str]]:
        """
        Adds a comment to the post.

        Args
        ----
            comment_text : str
                Text of comment

        Returns
        -------
            Tuple[str, Dict[str, str]] : the comment's URL (if the comment was shared successfully)
                and a dict containing its data (four string key-value pairs: datetime, url, publisher and text)
            
        Raises
        ------
            TypeError
                If comment_text argument is not a string or is empty.
            LimitedCommentsException
                If comments on this post have been limited.
        """
        # check that comment_text argument is a string
        if (not isinstance(comment_text, str)) or (comment_text.replace(" ", "") == ""):
            raise TypeError("'comment_text' argument must be a non-empty string.")
        # get post's page if not on it alreadyunlike_
        self._get_self_page()
        # selector for comment input bar
        comment_input_selector = "//textarea[@class]"
        # selector for when comments are limited
        comments_limited_selector = "//span[text()='Comments on this post have been limited.']"
        # find any of the elements above
        comment_input_selector = f"{comment_input_selector}|{comments_limited_selector}"
        comment_input = WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, comment_input_selector)))
        # check presence of comment input bar
        if comment_input.tag_name == "textarea":
            # get user's username, to later make sure comment has been posted
            user_username = self._get_user_username()
            # get current local time in UK, to later make sure comment has been posted
            # (comments' datetime value are set according to local time in UK)
            tz_London = pytz.timezone("Europe/London")
            comment_datetime = dt.now(tz_London)
            comment_datetime = comment_datetime.strftime("%d/%m/%Y, %H:%M:%S")
            try:
                # send comment_text and enter key to comment input bar
                comment_input.send_keys(comment_text + Keys.ENTER)
                # wait for text to be sent
                WebDriverWait(self.driver, 30).until(InputBarHasCleared())
                # take screenshot if test
                self._save_screenshot("comment_submitted")
            except StaleElementReferenceException:
                # if StaleElementReferenceException occurs, find comment input bar again
                comment_input = self.driver.find_element(By.XPATH, 
                                                         comment_input_selector)
                # send comment_text and enter key to comment input bar
                comment_input.send_keys(comment_text + Keys.ENTER)
                # wait for text to be sent
                WebDriverWait(self.driver, 30).until(InputBarHasCleared())
                # take screenshot if test
                self._save_screenshot("comment_submitted")
            # find all comments to compare to comment that was just shared
            comments_selector = "//a/time[@datetime]" + "/.."*9 + "/parent::div"
            # wait until presence of element representing comment that has just been posted
            # i.e. compare all comments found with the selector above, with the current comment 
            # that has just been shared (compare publisher's username, datetime and text)
            comment = WebDriverWait(self.driver, 30).until(
                CommentHasBeenPosted((By.XPATH, comments_selector), user_username, comment_datetime, comment_text))
            # get comment data and url
            comment_url, comment_data = self.__get_comment_data(comment)        
            return comment_url, comment_data
        else:
            # if limited comments, unable to add comment : raise LimitedCommentsException
            raise LimitedCommentsException

    def __find_comment(self, 
                       comment_url: str, 
                       levels: int) -> selenium.webdriver.remote.webelement.WebElement:
        """
        Finds comment element that corresponds to a specific URL.

        Args
        ----
            comment_url : str
                URL of a comment
            levels : int
                Number of levels to get parent element from comment element

        Returns
        -------
            selenium.webdriver.remote.webelement.WebElement : the comment WebElement that has comment_url as its href

        Raises
        ------
            IncorrectLinkException
                If comment_url is not under the post or does not lead to an existing comment.
        """
        # check if comment reached with comment_url is under current post (i.e. comment_url starts with self.url)
        if self.url not in comment_url:
            # raise IncorrectLinkException if not
            raise IncorrectLinkException("The comment you would like to reach is not under the current post.")
        # check if comment_url leads to a comment (i.e. comment_url contains "/c/")
        if "/c/" not in comment_url:
            # raise IncorrectLinkException if not
            raise IncorrectLinkException(f"The link {comment_url} does not lead to a comment.")
        # get comment URL
        # get driver's current page
        current_url = self.driver.current_url
        # get digits at the end of current_url if there are any
        ends_with_digits = re.findall(r"\d+$", current_url)
        if ends_with_digits:
            ends_with_digits = ends_with_digits[0]
            # check if URL ends with "?img_index={any digit or seq of digits}"
            # to check if driver on comment page
            if current_url.endswith(f"?img_index={ends_with_digits}"):
                current_url = current_url.replace(f"?img_index={ends_with_digits}", "")
        # get page if not already on it
        if current_url != comment_url:
            self.driver.get(comment_url)
            # wait until comments are shown for screenshot
            comments_selector = "//a/time[@datetime]" + "/.."*9 + "/parent::div"
            WebDriverWait(self.driver, 30).until(
                    EC.presence_of_all_elements_located((By.XPATH, comments_selector)))
            # take screenshot if test
            self._save_screenshot("comment_page_reached") 
        # check existence of comment_url
        # (if link to comment does not exist, self.driver.current_url will switch to self.url 
        # (+ "?img_index=1" if post is carousel) instead of being equal to comment_url)
        if self.driver.current_url.split("?")[0] != comment_url:
            # raise IncorrectLinkException if not
            raise IncorrectLinkException(f"The link {comment_url} does not lead to an existing comment.")
        # find comment element corresponding to comment_url
        comment_url = comment_url.replace("https://www.instagram.com", "")
        comment_selector = f"//a[@href='{comment_url}']" + "/.."*levels
        comment = WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, comment_selector)))
        # move mouse to comment element
        ActionChains(self.driver).move_to_element(comment).perform()
        return comment

    def delete_comment(self, 
                       comment_url: str) -> None:
        """
        Deletes a comment posted by user.

        Args
        ----
            comment_url : str
                URL of the comment to delete

        Raises
        ------
            TypeError
                If comment_url argument is not a string or is empty.
            IncorrectLinkException
                If comment_url is not under the post or does not lead to an existing comment.
        """
        # check that comment_url is string
        if (not isinstance(comment_url, str)) or (comment_url.replace(" ", "") == ""):
            raise TypeError("'comment_url' argument must be a non-empty string.")
        # get comment element corresponding to comment_url (get 3rd parent element)
        comment = self.__find_comment(comment_url, 3)
        # make sure comment was published by the user (otherwise unable to delete it)
        # find user's username
        user_username = self._get_user_username()
        # find comment's publisher
        comment_username_selector = ".//a[@href][not(*)]"
        comment_username = comment.find_element(By.XPATH, 
                                                comment_username_selector)
        comment_username = comment_username.text
        # compare the two usernames : if different then comment not by user and raise CommentNotSharedByUserException
        if user_username != comment_username:
            raise CommentNotSharedByUserException
        # find "Comment Options" button
        comment_options_button_selector = "[aria-label='Comment Options']"
        comment_options_button = comment.find_element(By.CSS_SELECTOR, 
                                                      comment_options_button_selector)
        # find clickable element from comment_options_button element
        comment_options_button_selector = "." + "/.."*3
        comment_options_button = comment_options_button.find_element(By.XPATH, 
                                                                     comment_options_button_selector)
        # click button
        comment_options_button.click()
        # find "Delete" button
        delete_button_selector = "//button[text()='Delete']"
        delete_button = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, delete_button_selector)))
        self._save_screenshot("comment_options_button_clicked") # take screenshot if test
        # click button
        delete_button.click()
        # wait until delete_button no longer attached to DOM
        WebDriverWait(self.driver, 30).until(EC.staleness_of(delete_button))
        # take screenshot if test
        self._save_screenshot("delete_comment_button_clicked")


    def __get_comment_like_button(self, 
                                  comment: selenium.webdriver.remote.webelement.WebElement) \
                                    -> selenium.webdriver.remote.webelement.WebElement:
        """
        Finds the like (or unlike) button element of the comment.

        Args
        ----
            comment : selenium.webdriver.remote.webelement.WebElement
                the WebElement representing the comment

        Returns
        -------
            selenium.webdriver.remote.webelement.WebElement : the WebElement representing \
                the like (or unlike) button of the comment.
        """
        # selector for when comment has not been liked
        like_button_selector = ".//*[@aria-label='Like']"
        # selector for when comment has already been liked
        unlike_button_selector = ".//*[@aria-label='Unlike']"
        # find button
        button_selector = f"{like_button_selector}|{unlike_button_selector}"
        button = WebDriverWait(comment, 30).until(
            EC.element_to_be_clickable((By.XPATH, button_selector)))
        return button

    def like_comment(self, 
                     comment_url: str) -> None:
        """
        Adds a like to a comment.

        Args
        ----
            comment_url : str
                URL of a comment
        
        Raises
        ------
            TypeError
                If comment_url argument is not a string or is empty.
            IncorrectLinkException
                If comment_url is not under the post or does not lead to an existing comment.
        """
        # check that comment_url is string
        if (not isinstance(comment_url, str)) or (comment_url.replace(" ", "") == ""):
            raise TypeError("'comment_url' argument must be a non-empty string.")
        # get comment element corresponding to comment_url (get 5th parent element)
        comment = self.__find_comment(comment_url, 5)
        # find like or unlike button
        button = self.__get_comment_like_button(comment)
        # get button color
        try:
            previous_color = Color.from_string(button.value_of_css_property("fill"))
        except StaleElementReferenceException:
            # if button is stale, find button element again
            button = self.__get_comment_like_button(comment)
            previous_color = Color.from_string(button.value_of_css_property("fill"))
        # check if post has not been liked already (if like: no need to like again)
        if button.get_attribute("aria-label") == "Like":
            # set timeout
            start_time = time.time()
            TIMEOUT = 30
            while True:
                # check if timeout passed
                if time.time() - start_time > TIMEOUT:
                    raise TimeoutException
                # find clickable element from button element
                clickable_button_selector = "." + "/.."*3
                clickable_button = button.find_element(By.XPATH, 
                                                       clickable_button_selector)
                
                # click button
                ActionChains(self.driver).move_to_element(clickable_button).click().perform()
                # check if fill color has changed, i.e. if like has been uploaded
                button = self.__get_comment_like_button(comment)
                # get button color
                try:
                    current_color = Color.from_string(button.value_of_css_property("fill"))
                except StaleElementReferenceException:
                    # if button is stale, find button element again
                    button = self.__get_comment_like_button(comment)
                    current_color = Color.from_string(button.value_of_css_property("fill"))
                if current_color != previous_color:
                    break
        # take screenshot if test
        self._save_screenshot("comment_liked")

    def unlike_comment(self, 
                       comment_url: str) -> None:
        """
        Removes user's like from a comment.

        Args
        ----
            comment_url : str
                URL of a comment
        
        Raises
        ------
            TypeError
                If comment_url argument is not a string or is empty.
            IncorrectLinkException
                If comment_url is not under the post or does not lead to an existing comment.
        """
        # check that comment_url is string
        if (not isinstance(comment_url, str)) or (comment_url.replace(" ", "") == ""):
            raise TypeError("'comment_url' argument must be a non-empty string.")
        # get comment element corresponding to comment_url (get 5th parent element)
        comment = self.__find_comment(comment_url, 5)
        # find like or unlike button
        button = self.__get_comment_like_button(comment)
        # get button color
        try:
            previous_color = Color.from_string(button.value_of_css_property("fill"))
        except StaleElementReferenceException:
            # if button is stale, find button element again
            button = self.__get_comment_like_button(comment)
            previous_color = Color.from_string(button.value_of_css_property("fill"))
        # check if post has not been liked already (if like: no need to like again)
        if button.get_attribute("aria-label") == "Unlike":
            # set timeout
            start_time = time.time()
            TIMEOUT = 30
            while True:
                # check if timeout passed
                if time.time() - start_time > TIMEOUT:
                    raise TimeoutException
                # find clickable element from button element
                clickable_button_selector = "." + "/.."*3
                clickable_button = button.find_element(By.XPATH, 
                                                       clickable_button_selector)
                
                # click button
                ActionChains(self.driver).move_to_element(clickable_button).click().perform()
                # check if fill color has changed, i.e. if like has been uploaded
                button = self.__get_comment_like_button(comment)
                # get button color
                try:
                    current_color = Color.from_string(button.value_of_css_property("fill"))
                except StaleElementReferenceException:
                    # if button is stale, find button element again
                    button = self.__get_comment_like_button(comment)
                    current_color = Color.from_string(button.value_of_css_property("fill"))
                if current_color != previous_color:
                    break
        # take screenshot if test
        self._save_screenshot("comment_unliked")

    def add_reply(self, 
                  comment_url: str, 
                  reply_text: str) -> None:
        """
        Adds a reply to a comment under the post.

        Args
        ----
            comment_url : str
                URL of a comment
            reply_text : str
                text of reply
        
        Raises
        ------
            TypeError
                If comment_url or reply_text arguments are not strings or are empty.
            LimitedCommentsException
                If comments on this post have been limited.
            IncorrectLinkException
                If comment_url is not under the post or does not lead to an existing comment.
        """
        # check that comment_url is string
        if (not isinstance(comment_url, str)) or (comment_url.replace(" ", "") == ""):
            raise TypeError("'comment_url' argument must be a non-empty string.")
        # check that reply_text is string
        if (not isinstance(reply_text, str)) or (reply_text.replace(" ", "") == ""):
            raise TypeError("'reply_text' argument must be a non-empty string.")
        # get comment element corresponding to comment_url (get 3rd parent element)
        comment = self.__find_comment(comment_url, 3)
        try:
            # find reply button from comment element
            reply_button_selector = "//span[text()='Reply']" + "/.."
            reply_button = comment.find_element(By.XPATH, 
                                                reply_button_selector)
            # click reply button
            reply_button.click()
            # find comment input bar 
            comment_input_selector = "textarea[class]"
            comment_input = self.driver.find_element(By.CSS_SELECTOR, 
                                                     comment_input_selector)
            self._save_screenshot("reply_button_clicked") # take screenshot if test
            # send reply_text and enter key to comment input bar
            comment_input.send_keys(reply_text + Keys.ENTER)
            # wait for text to be sent
            WebDriverWait(self.driver, 30).until(InputBarHasCleared())
            # take screenshot if test
            self._save_screenshot("reply_submitted")
        # if comments are limited, no reply button and no comment input bar
        except NoSuchElementException:
            # assure presence of "Comments on this post have been limited" message
            comments_limited_selector = "//span[text()='Comments on this post have been limited.']"
            self.driver.find_element(By.XPATH, 
                                     comments_limited_selector)
            # raise LimitedCommentsException if comments are indeed limited
            raise LimitedCommentsException
        
    def delete_reply(self, 
                     comment_url: str, 
                     reply_text: str) -> None:
        """
        Deletes a reply to a comment under the post.

        Args
        ----
            comment_url : str
                URL of a comment
            reply_text : str
                text of reply
        
        Raises
        ------
            TypeError
                If comment_url or reply_text arguments are not strings or are empty.
            ReplyNotFoundException
                If there is no reply under the comment corresponding to reply_text and user's username.
            IncorrectLinkException
                If comment_url is not under the post or does not lead to an existing comment.
        """
        # check that comment_url is string
        if (not isinstance(comment_url, str)) or (comment_url.replace(" ", "") == ""):
            raise TypeError("'comment_url' argument must be a non-empty string.")
        # check that reply_text is string
        if (not isinstance(reply_text, str)) or (reply_text.replace(" ", "") == ""):
            raise TypeError("'reply_text' argument must be a non-empty string.")
        # get comment element corresponding to comment_url (get 8th parent element)
        comment = self.__find_comment(comment_url, 8)
        # get user's username, to later compare reply's publisher with user
        user_username = self._get_user_username()
        view_replies = None
        # make sure that comment has replies
        try:
            # find "view_replies" button if it exists
            view_replies_selector = ".//button//span[contains(text(), 'View replies ')]"
            view_replies = comment.find_element(By.XPATH, 
                                                view_replies_selector)
        except NoSuchElementException:
            # check if replies are not already all shown
            try:
                # find "hide replies" button if it exist
                hide_replies_selector = ".//span[text()='Hide replies']"
                comment.find_element(By.XPATH, 
                                     hide_replies_selector)
            except NoSuchElementException:
                # if it does not exist raise NoRepliesException
                raise ReplyNotFoundException("This comment does not have any reply.")
        if view_replies:
            # click view replies button as long as there is one, to show all replies
            while True:
                view_replies.click()
                try:
                    view_replies = comment.find_element(By.XPATH, 
                                                        view_replies_selector)
                except NoSuchElementException:
                    break
        # take screenshot if test
        self._save_screenshot("comment_replies_displayed")
        # find comment's replies
        replies_selector = ".//span[contains(text(), ' replies')]" + "/.."*5 + "/ul/div"
        try:
            # simple .find_element to ensure comment really has replies 
            # (to prevent "show more replies" button clicked but no replies)
            comment.find_element(By.XPATH, 
                                 replies_selector)
        except NoSuchElementException:
            # raise NoRepliesException if comment has in reality no replies
            raise ReplyNotFoundException("This comment does not have any reply.")
        last_reply = None
        while True:
            # find comment replies
            replies = WebDriverWait(comment, 30).until(
                EC.visibility_of_all_elements_located((By.XPATH, replies_selector)))
            for reply in replies:
                # scrape each reply's username
                username_selector = ".//h3"
                username = reply.find_element(By.XPATH, 
                                              username_selector)
                username = username.text
                # scrape each reply's text
                text_selector = ".//h3" + "/.." + "/div/span[@dir='auto']"
                text = reply.find_element(By.XPATH, 
                                          text_selector)
                text = text.text
                if (username == user_username) and (text == reply_text):
                    # scroll to reply
                    self.driver.execute_script("arguments[0].scrollIntoView();", 
                                               reply)
                    # take screenshot if test
                    self._save_screenshot("reply_to_delete_found")
                    # move mouse to reply
                    ActionChains(self.driver).move_to_element(reply).perform()
                    # find "Comment Options" button
                    comment_options_button_selector = "[aria-label='Comment Options']"
                    comment_options_button = reply.find_element(By.CSS_SELECTOR, 
                                                                comment_options_button_selector)
                    # find clickable element from comment_options_button element
                    comment_options_button_selector = "." + "/.."*3
                    comment_options_button = comment_options_button.find_element(By.XPATH, 
                                                                                 comment_options_button_selector)
                    # click button
                    comment_options_button.click()
                    # find "Delete" button
                    delete_button_selector = "//button[text()='Delete']"
                    delete_button = WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, delete_button_selector)))
                    self._save_screenshot("comment_options_button_clicked") # take screenshot if test
                    # click button
                    delete_button.click()
                    # wait until delete_button no longer attached to DOM
                    WebDriverWait(self.driver, 30).until(EC.staleness_of(delete_button))
                    # take screenshot if test
                    self._save_screenshot("delete_reply_button_clicked")
                    # exit function
                    return
            if replies[-1] == last_reply:
                break
            last_reply = replies[-1]
            # scroll to last reply
            self.driver.execute_script("arguments[0].scrollIntoView();", 
                                       last_reply)
        # if end of function reached, means reply was not found
        raise ReplyNotFoundException
    