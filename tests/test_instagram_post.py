from instadroid import InstagramPost

from datetime import datetime as dt
from dotenv import load_dotenv
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.color import Color
from selenium.webdriver.support.ui import WebDriverWait
from typing import Dict, Generator, Tuple, Union

import _pytest
import json
import os
import pytest
import re
import selenium


# load environment variables from .env file
load_dotenv()

# access variables and set username and password
username = os.getenv("INSTAGRAM_USERNAME")
password = os.getenv("INSTAGRAM_PASSWORD")
user_creds=(username, password)


class TestInstagramPostLogIn:
    """
    Tests exceptions that are raised when log in is not successful.
    """

    # URL of post to reach
    post_url = "https://www.instagram.com/p/C9zsEnZOc2j/"

    # credentials of a blocked account
    blocked_username = os.getenv("INSTAGRAM_USERNAME")
    blocked_password = os.getenv("INSTAGRAM_PASSWORD")
    
    @pytest.mark.parametrize("driver, user_creds, expected_exception", [
        (None, None, "TypeError"), # both driver and user_creds set to None
        (None, ("username", "password", "useless string"), "TypeError"), # user_creds parameter has three strings instead of two
        (None, ("username", 1), "TypeError"), # user_creds has one element of incorrect type
        (None, (1, "password"), "TypeError"), # user_creds has one element of incorrect type
        (None, ("incorrect_username", "incorrect_password"), "IncorrectCredentialsException"), # incorrect credentials
        # account not blocked anymore so wait for it or another one to get blocked
        # (None, (blocked_username, blocked_password), "BlockedAccountException") # credentials belong to a blocked account
    ])
    def test_log_in(self, 
                    driver: Union[selenium.webdriver.Chrome, None], 
                    user_creds: Union[Tuple[str, str], None], 
                    expected_exception: str) -> None:
        """
        Parametrized test to test expected exceptions raised when logging in.

        Args
        ---- 
            driver : Union[selenium.webdriver.Chrome, None]
                Automated browser controlled by Selenium
            user_creds : Union[Tuple[str, str], None] 
                User's credentials
            expected_exception : str
                Expected exception raised
        """
        try:
            # try logging in with test parameters
            InstagramPost(post_url=self.post_url,
                          driver=driver, 
                          user_creds=user_creds,
                          headless_browser=False)
            # exception should be raised so if successful log in, test fails
            assert False
        except Exception as e:
            # assert exception raised matches expected exception
            assert type(e).__name__ == expected_exception, \
                f"Expected exception '{expected_exception}', but got '{type(e).__name__}'"


class TestInstagramPostWebScraping:
    """
    Tests post web scraping methods.
    """

    # load expected post data
    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data", 
        "expected_post_data.json")
    with open(file_path, "r", encoding="utf-8") as f:
        expected_data = json.load(f)

    # get all post URLs
    post_urls = expected_data.keys()

    @pytest.fixture(scope="class")
    def instagram_post_without_initial_driver(self) -> Generator[InstagramPost, None, None]:
        """
        Initializes the test class by building an InstagramPost instance out of credentials.

        Yields
        ------
            InstagramPost : an instance of the class for testing
        """
        post_url = "https://www.instagram.com/p/C9zsEnZOc2j/"
        post = InstagramPost(post_url=post_url, 
                             user_creds=user_creds,
                             headless_browser=False)
        # close post at the end of class tests
        yield post
        post.close()

    @pytest.fixture(scope="class", params=post_urls)
    def instagram_post(self, 
                       request: _pytest.fixtures.FixtureRequest, 
                       instagram_post_without_initial_driver: InstagramPost) -> InstagramPost:
        """
        Initializes the test class by building as many InstagramPost instances, out of a 
        Selenium chrome webdriver instance, as there are URLs in post_urls parameter.

        Args
        ----
            request : _pytest.fixtures.FixtureRequest
                Object allowing to access fixture parameters
            instagram_post_without_initial_driver : InstagramPost
                Base InstagramPost instance created out of credentials

        Returns
        ------- 
            InstagramPost : an InstagramPost instance created out of the base InstagramPost instance's webdriver
        """
        # get post_url parameter
        post_url = request.param
        # create InstagramPost instance out of credentials 
        driver = instagram_post_without_initial_driver.driver
        # create InstagramPost instance out of Selenium chrome webdriver 
        # (to avoid having multiple webdrivers opened : instagram_post_without_initial_driver 
        # fixture will open one webdriver and instagram_post fixture will use this webdriver 
        # on its multiple InstagramPost instances) 
        post = InstagramPost(post_url=post_url, 
                             driver=driver)
        return post
    
    def test_get_post_user(self, 
                           instagram_post: InstagramPost) -> None:
        """
        Tests whether the username(s) that is scraped is correct.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # get parametrized fixture's current InstagramPost's URL
        post_url = instagram_post.url
        # get expected username
        expected_post_user = self.expected_data[post_url]["user"]
        # get scraped username
        post_user = instagram_post.user
        if isinstance(post_user, list):
            # sort both lists if more than one scraped usernames
            post_user.sort()
            expected_post_user.sort()
            # assert that both lenths are equal
            assert len(post_user) == len(expected_post_user), \
                f"Expected len(users) '{len(expected_post_user)}', but got '{len(post_user)}'"
            for actual, expected in zip(post_user, expected_post_user):
                # assert that all actual and expected usernames match
                assert actual == expected, \
                    f"Expected user '{actual}', but got '{expected}'"
        else:
            # assert that actual and expected username match if not list (i.e. is string)
            assert post_user == expected_post_user, \
                f"Expected user '{expected_post_user}', but got '{post_user}'"

    def test_get_post_datetime(self, 
                               instagram_post: InstagramPost) -> None:
        """
        Tests whether the datetime that is scraped is correct.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # get parametrized fixture's current InstagramPost's URL
        post_url = instagram_post.url
        # get expected datetime
        expected_post_datetime = self.expected_data[post_url]["datetime"]
        # get scraped datetime
        post_datetime = instagram_post.datetime
        # assert that actual and expected datetime match
        assert post_datetime == expected_post_datetime, \
            f"Expected datetime '{expected_post_datetime}', but got '{post_datetime}'"

    def test_get_post_type(self, 
                           instagram_post: InstagramPost) -> None:
        """
        Tests whether the type of post that is deduced is correct.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # get parametrized fixture's current InstagramPost's URL
        post_url = instagram_post.url
        # get expected type
        expected_post_type = self.expected_data[post_url]["type"]
        # get deduced type
        post_type = instagram_post.type
        # assert that actual and expected types match
        assert post_type == expected_post_type, \
            f"Expected type '{expected_post_type}', but got '{post_type}'"

    def test_get_post_caption(self, 
                              instagram_post: InstagramPost) -> None:
        """
        Tests whether the caption that is scraped is correct.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # get parametrized fixture's current InstagramPost's URL
        post_url = instagram_post.url
        # get expected caption
        expected_post_caption = self.expected_data[post_url]["caption"]
        # get scraped caption
        post_caption = instagram_post.caption
        # assert that actual and expected captions match
        assert post_caption == expected_post_caption, \
            f"Expected caption '{expected_post_caption}', but got '{post_caption}'"

    def test_get_post_likes_count(self, 
                                  instagram_post: InstagramPost) -> None:
        """
        Tests whether the likes count that is scraped is correct.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # get parametrized fixture's current InstagramPost's URL
        post_url = instagram_post.url
        # get expected likes count
        expected_post_likes_count = self.expected_data[post_url]["likes count"]
        # get scraped likes count
        post_likes_count = instagram_post.likes_count
        # assert that actual and expected likes counts match
        assert post_likes_count == expected_post_likes_count, \
            f"Expected likes count '{expected_post_likes_count}', but got '{post_likes_count}'"

    def test_get_post_location(self, 
                               instagram_post: InstagramPost) -> None:
        """
        Tests whether the location that is scraped is correct.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # get parametrized fixture's current InstagramPost's URL
        post_url = instagram_post.url
        # get expected location
        expected_post_location = self.expected_data[post_url]["location"]
        # get scraped location
        post_location = instagram_post.location
        # assert that actual and expected locations match
        assert post_location == expected_post_location, \
            f"Expected location '{expected_post_location}', but got '{post_location}'"

    def test_get_post_audio(self, 
                            instagram_post: InstagramPost) -> None:
        """
        Tests whether the audio that is scraped is correct.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # get parametrized fixture's current InstagramPost's URL
        post_url = instagram_post.url
        # get expected audio
        expected_post_audio = self.expected_data[post_url]["audio"]
        # get scraped audio
        post_audio = instagram_post.audio
        # assert that actual and expected audios match
        assert post_audio == expected_post_audio, \
            f"Expected audio '{expected_post_audio}', but got '{post_audio}'"

    def test_get_post_media_count(self, 
                                  instagram_post: InstagramPost) -> None:
        """
        Tests whether the media count that is deduced is correct.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # get parametrized fixture's current InstagramPost's URL
        post_url = instagram_post.url
        # get expected media count
        expected_post_media_count = self.expected_data[post_url]["media count"]
        # get deduced media count
        post_media_count = instagram_post.media_count
        # assert that actual and expected media counts match
        assert post_media_count == expected_post_media_count, \
            f"Expected media count '{expected_post_media_count}', but got '{post_media_count}'"

    def test_get_post_likes_list(self, 
                                 instagram_post: InstagramPost) -> None:
        """
        Tests whether the scraped likes list is correct.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # get parametrized fixture's current InstagramPost's URL
        post_url = instagram_post.url
        # get expected likes list
        expected_post_likes_list = self.expected_data[post_url]["likes list"]
        # get scraped likes list
        post_likes_list = instagram_post.get_likes()
        # assert that each scraped username in list is in expected list
        if expected_post_likes_list:  
            for actual in post_likes_list:
                assert actual in expected_post_likes_list, \
                    f"'{actual}' not in expected likes list'"
        # if expected likes list empty, assert actual list is also empty
        else:
            assert post_likes_list == expected_post_likes_list, \
                f"Expected likes list '{expected_post_likes_list}', but got '{post_likes_list}'"
            
    def test_get_post_comments(self, 
                               instagram_post: InstagramPost) -> None:
        """
        Tests whether the scraped comment data is correct.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # get parametrized fixture's current InstagramPost's URL
        post_url = instagram_post.url
        # get expected comment data
        expected_post_comments = self.expected_data[post_url]["comments"]
        # get scraped comment data
        post_comments = instagram_post.get_comments()
        # assert expected comment count is equal to scraped comment count
        assert len(expected_post_comments.keys()) == len(post_comments.keys()), \
            f"Expected length '{len(expected_post_comments.keys())}', but got '{len(post_comments.keys())}'"
        for comment_url in expected_post_comments.keys():
            # assert expected comment in scraped comment
            assert comment_url in post_comments.keys(), \
                f"Expected url '{comment_url}' to be in comments, but is not'"
            for key in expected_post_comments[comment_url].keys():
                if key != "replies":
                    # assert that every expected comment's data matches scraped comment's data
                    assert expected_post_comments[comment_url][key] == post_comments[comment_url][key], \
                        f"Expected {key} '{expected_post_comments[comment_url][key]}' for {comment_url}, but got '{post_comments[comment_url][key]}'"
                else:
                    if expected_post_comments[comment_url][key]:
                        # assert that each comment has as many expected replies as scraped replies
                        assert len(expected_post_comments[comment_url][key]) == len(post_comments[comment_url][key]), \
                            f"Expected {len(expected_post_comments[comment_url][key])} replies, but got {len(post_comments[comment_url][key])}"
                    for expected, actual in zip(expected_post_comments[comment_url][key], post_comments[comment_url][key]):
                        # assert that every expected reply's data matches scraped reply's data
                        for reply_key in expected.keys():
                            assert expected[reply_key] == actual[reply_key], \
                                f"Expected {reply_key} '{expected[reply_key]}' in {comment_url} replies, but got '{actual[reply_key]}'"


class TestInstagramPostWebAutomation:
    """
    Tests post web automation methods.
    """

    @pytest.fixture(scope="class")
    def instagram_post(self) -> Generator[InstagramPost, None, None]:
        """
        Initializes the test class by building an InstagramPost instance out of credentials.

        Yields
        ------
            InstagramPost : an instance of the class for testing
        """
        post_url = "https://www.instagram.com/p/DC7MHx9S_1R/"
        post = InstagramPost(post_url=post_url, 
                             user_creds=user_creds,
                             headless_browser=False)
        yield post
        # close post at the end of class tests
        post.close()

    def __get_like_button_color(self, 
                                instagram_post: InstagramPost) -> None:
        """
        Finds a post's like button current color.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # selector for when post has not been liked
        like_button_selector = "//*[@aria-label='Like'][@height='24']"
        # selector for when post has already been liked
        unlike_button_selector = "//*[@aria-label='Unlike'][@height='24']"
        # find button
        button_selector = f"{like_button_selector}|{unlike_button_selector}"
        button = WebDriverWait(instagram_post.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, button_selector)))
        button_color = Color.from_string(button.value_of_css_property("fill"))
        return button_color

    def test_like_post(self, 
                       instagram_post: InstagramPost) -> None:
        """
        Tests whether the like_post() method actually likes the post.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # add a like to the post
        instagram_post.like_post()
        # find like button color
        button_color = self.__get_like_button_color(instagram_post)
        # assert that color is equal to following rgba color (i.e. color of button when post is liked)
        expected_button_color = Color.from_string("rgba(255, 48, 64, 1)")
        assert button_color == expected_button_color, \
            f"Expected '{expected_button_color}', but got '{button_color}'"

    def test_unlike_post(self, 
                         instagram_post: InstagramPost) -> None:
        """
        Tests whether the unlike_post() method actually unlikes the post.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # remove like from the post
        instagram_post.unlike_post()
        # find like button color
        button_color = self.__get_like_button_color(instagram_post)
        # assert that color is equal to following rgba color (i.e. color of button when post is not liked)
        expected_button_color1 = Color.from_string("rgba(142, 142, 142, 1)")
        expected_button_color2 = Color.from_string("rgba(38, 38, 38, 1)")
        assert button_color in (expected_button_color1, expected_button_color2), \
            f"Expected '{expected_button_color1}' or '{expected_button_color2}', but got '{button_color}'"

    def __find_comment(self, 
                       instagram_post: InstagramPost,
                       comment_url: str, 
                       levels: int) -> selenium.webdriver.remote.webelement.WebElement:
        """
        Finds comment element that corresponds to a specific URL.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
            comment_url : str
                URL of a comment
            levels : int
                Number of levels to get parent element from comment element

        Returns
        -------
            selenium.webdriver.remote.webelement.WebElement : the comment WebElement that has comment_url as its href
        """
        # find comment element corresponding to comment_url
        comment_url = comment_url.replace("https://www.instagram.com", "")
        comment_selector = f"//a[@href='{comment_url}']" + "/.."*levels
        comment = WebDriverWait(instagram_post.driver, 30).until(
            EC.visibility_of_element_located((By.XPATH, comment_selector)))
        # move mouse to comment element
        ActionChains(instagram_post.driver).move_to_element(comment).perform()
        return comment
    
    def __get_comment_like_button_color(self, 
                                        comment: selenium.webdriver.remote.webelement.WebElement) \
                                            -> selenium.webdriver.support.color.Color:
        """
        Finds the like (or unlike) button color of the comment.

        Args
        ----
            comment : selenium.webdriver.remote.webelement.WebElement
                the WebElement representing the comment

        Returns
        -------
            selenium.webdriver.support.color.Color : the color of the WebElement \
                representing the like (or unlike) button of the comment.
        """
        # selector for when comment has not been liked
        like_button_selector = ".//*[@aria-label='Like']"
        # selector for when comment has already been liked
        unlike_button_selector = ".//*[@aria-label='Unlike']"
        # find button
        button_selector = f"{like_button_selector}|{unlike_button_selector}"
        button = WebDriverWait(comment, 30).until(
            EC.element_to_be_clickable((By.XPATH, button_selector)))
        # get color of button
        button_color = Color.from_string(button.value_of_css_property("fill"))
        return button_color
    
    def test_like_comment(self, 
                          instagram_post: InstagramPost) -> None:
        """
        Tests whether the like_comment() method actually likes a comment.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # URL of comment
        comment_url = instagram_post.url + "c/17914151177995757/"
        # add like to comment
        instagram_post.like_comment(comment_url)
        # get comment element corresponding to comment_url (get 5th parent element)
        comment = self.__find_comment(instagram_post, comment_url, 5)
        # find like or unlike button's color
        button_color = self.__get_comment_like_button_color(comment)
        # assert that color is equal to following rgba color (i.e. color of button when post is liked)
        expected_button_color = Color.from_string("rgba(255, 48, 64, 1)")
        assert button_color == expected_button_color, \
            f"Expected '{expected_button_color}', but got '{button_color}'"

    def test_unlike_comment(self, 
                            instagram_post: InstagramPost) -> None:
        """
        Tests whether the unlike_comment() method actually removes a like from a comment.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # URL of comment
        comment_url = instagram_post.url + "c/17914151177995757/"
        # remove like from comment
        instagram_post.unlike_comment(comment_url)
        # get comment element corresponding to comment_url (get 5th parent element)
        comment = self.__find_comment(instagram_post, comment_url, 5)
        # find like or unlike button's color
        button_color = self.__get_comment_like_button_color(comment)
        # assert that color is equal to following rgba color (i.e. color of button when post is not liked)
        expected_button_color1 = Color.from_string("rgba(142, 142, 142, 1)")
        expected_button_color2 = Color.from_string("rgba(38, 38, 38, 1)")
        assert button_color in (expected_button_color1, expected_button_color2), \
            f"Expected '{expected_button_color1}' or '{expected_button_color2}', but got '{button_color}'"

    def __get_comment_data(self, 
                           comment: selenium.webdriver.remote.webelement.WebElement) -> Tuple[str, Dict[str, str]]:
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
        publisher_selector = ".//a[not(time)][not(img)]"
        publisher = comment.find_element(By.XPATH, 
                                         publisher_selector)
        publisher = publisher.text
        # find text from comment element
        text_selector = ".//div/span[text()]"
        text = comment.find_element(By.XPATH, 
                                    text_selector)
        text = text.text
        # find likes count from comment element if it has likes (set to 0 if not)
        try:
            likes_count_selector = ".//button//span[contains(text(), 'like')]"
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
    
    def test_add_delete_comment(self, 
                                instagram_post: InstagramPost) -> None:
        """
        Tests whether the add_comment() and delete_comment() methods respectively add and remove a comment.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # testing add_comment()
        # text to comment
        comment_text = "✨"
        # add comment and get expected comment data
        expected_comment_url, expected_comment_data = instagram_post.add_comment(comment_text)
        # get comment page
        instagram_post.driver.get(expected_comment_url)
        # scrape comment data corresponding to posted comment
        comment = self.__find_comment(instagram_post, expected_comment_url, 5)
        comment_url, comment_data = self.__get_comment_data(comment)
        # assert expected and scraped data match
        for key in expected_comment_data.keys():
            assert expected_comment_data[key] == comment_data[key], \
                f"Add_comment() failed : Expected {key} '{expected_comment_data[key]}', but got '{comment_data[key]}'"
        # testing delete_comment()
        # delete comment that was just posted
        instagram_post.delete_comment(comment_url)
        # get post page and refresh page
        instagram_post.driver.get(instagram_post.url)
        instagram_post.driver.refresh()
        # wait until comments are visible
        comments_selector = "//a/time[@datetime]" + "/.."*9 + "/parent::div"
        WebDriverWait(instagram_post.driver, 30).until(
            EC.visibility_of_all_elements_located((By.XPATH, comments_selector)))
        try:
            # find comment element corresponding to comment_url
            comment_url = comment_url.replace("https://www.instagram.com", "")
            comment_selector = f"//a[@href='{comment_url}']" + "/.."
            instagram_post.driver.find_element(By.XPATH, 
                                               comment_selector)
            assert False, \
                f"Delete_comment() failed : {comment_url} did not get deleted"
        except NoSuchElementException:
            assert True

    def __get_last_reply(self, 
                         instagram_post: InstagramPost, 
                         comment_url: str) -> Tuple[str, str]:
        """
        Finds the last reply of a comment.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
            comment_url : str
                URL of a comment

        Returns
        -------
            Tuple[str, str] : the last reply's username and text
        """
        # get comment element corresponding to comment_url (get 8th parent element)
        comment = self.__find_comment(instagram_post, comment_url, 8)
        try:
            # find "view_replies" button if it exists
            view_replies_selector = ".//button//span[contains(text(), 'View replies ')]"
            view_replies = comment.find_element(By.XPATH, 
                                                view_replies_selector)
        except NoSuchElementException:
            # if it does not exist : error
            assert False, \
                "Add_reply() failed : Reply did not get posted"
        # click view replies button as long as there is one, to show all replies
        while True:
            view_replies.click()
            try:
                view_replies = comment.find_element(By.XPATH, 
                                                    view_replies_selector)
            except NoSuchElementException:
                break
        # find comment's replies
        replies_selector = ".//span[contains(text(), ' replies')]" + "/.."*5 + "/ul/div"
        try:
            # simple .find_element to ensure comment really has replies 
            # (to prevent "show more replies" button clicked but no replies)
            comment.find_element(By.XPATH, 
                                 replies_selector)
        except NoSuchElementException:
            # if it does not exist : error
            assert False, \
                "Add_reply() failed : Reply did not get posted"
        # find comment replies
        replies = WebDriverWait(comment, 30).until(
            EC.visibility_of_all_elements_located((By.XPATH, replies_selector)))
        # get last reply
        last_reply = replies[-1]
        # scrape last reply's username
        reply_username_selector = ".//h3"
        reply_username = last_reply.find_element(By.XPATH, 
                                                 reply_username_selector)
        last_reply_username = reply_username.text
        # scrape last reply's text
        text_selector = ".//h3" + "/.." + "/div/span[@dir='auto']"
        text = last_reply.find_element(By.XPATH, 
                                       text_selector)
        last_reply_text = text.text
        return last_reply_username, last_reply_text

    def test_add_delete_reply(self, 
                              instagram_post: InstagramPost) -> None:
        """
        Tests whether the add_reply() and delete_reply() methods respectively add and remove a reply to a comment.

        Args
        ---- 
            instagram_post : InstagramPost
                InstagramPost instance provided by the fixture
        """
        # URL of comment
        comment_url = instagram_post.url + "c/17914151177995757/"
        # username of user who posted comment
        username_to_reply_to = "@lilbibby_"
        # text to reply
        reply_text = "✨"
        # testing add_reply()
        # reply to comment
        instagram_post.add_reply(comment_url, reply_text)
        # refresh page
        instagram_post.driver.refresh()
        # get comment last reply
        reply_text = f"{username_to_reply_to} {reply_text}"
        last_reply_username, last_reply_text = self.__get_last_reply(instagram_post, comment_url)
        # assert last reply's username and text match user's username and posted reply's text
        if (last_reply_username != username) or (last_reply_text != reply_text):
            assert False, \
                "Add_reply() failed : Reply did not get posted"
        # testing delete_reply()
        # delete reply that was just posted
        instagram_post.delete_reply(comment_url, reply_text)
        # refresh page
        instagram_post.driver.refresh()
        # get comment last reply
        last_reply_username, last_reply_text = self.__get_last_reply(instagram_post, comment_url)
        # assert last reply's username and text don't match user's username and posted reply's text 
        # (i.e. would mean reply did not get deleted)
        if (last_reply_username == username) and (last_reply_text == reply_text):
            # refresh page one more time
            instagram_post.driver.refresh()
            # get comment last reply
            last_reply_username, last_reply_text = self.__get_last_reply(instagram_post, comment_url)
            # assert last reply's username and text don't match user's username and posted reply's text 
            if (last_reply_username == username) and (last_reply_text == reply_text):
                assert False, \
                    "Delete_reply() failed : Reply did not get deleted"