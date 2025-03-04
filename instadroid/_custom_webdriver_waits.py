from selenium.webdriver.common.by import By
from typing import List, Tuple, Union

import datetime
import selenium


class ElementsHaveUpdated:
    """
    An expectation for checking that the elements have been updated after a scroll.

    Attributes
    ----------
        locator : Tuple[str, str]
            used to find the elements
        previous_elements : list
            previously found elements   
    """

    def __init__(self, 
                 locator: Tuple[str, str], 
                 previous_elements: list) -> None:
        """
        Initializes an instance of the class ElementsHaveUpdated, called within WebDriverWait.

        Args
        ----
            locator : Tuple[str, str]
                used to find the elements
            previous_elements : list
                previously found elements
        """
        self.locator = locator
        self.previous_elements = previous_elements

    def __call__(self, 
                 driver: selenium.webdriver.Chrome) \
                    -> Union[selenium.webdriver.remote.webelement.WebElement, bool]:
        """
        Makes an instance of ElementsHaveUpdated callable.

        Args
        ----
            driver : selenium.webdriver.Chrome
                automated browser controlled by Selenium

        Returns
        -------
            Union[selenium.webdriver.remote.webelement.WebElement, bool] : \
                the WebElements if they have been updated, False if not
        """
        # find elements
        elements = driver.find_elements(*self.locator)
        # check if newly found elements are different from previously found elements
        if elements != self.previous_elements:
            # if so, return elements
            return elements
        else:
            return False
        

class CommentHasBeenPosted:
    """
    An expectation for checking that a comment has been posted (i.e. is present in th DOM), by going through 
    all comments and comparing all of them to the posted comment until it is found in the DOM.

    Attributes
    ----------
        locator : Tuple[str, str]
            used to find the elements
        username : str
            username of user who shared the comment    
        datetime : datetime.datetime
            when the comment was submitted 
        text : str
            text of the comment
    """

    def __init__(self, 
                 locator: Tuple[str, str], 
                 username: str, 
                 datetime: datetime.datetime, 
                 text: str) -> None:
        """
        Initializes an instance of the class CommentHasBeenPosted, called within WebDriverWait.

        Args
        ----
            locator : Tuple[str, str]
                used to find the elements
            username : str
                username of user who commented    
            datetime : datetime.datetime
                when the comment was submitted 
            text : str
                text of the comment
        """
        self.locator = locator
        self.username = username
        self.datetime = datetime
        self.text = text

    def __call__(self, 
                 driver: selenium.webdriver.Chrome) \
                    -> Union[List[selenium.webdriver.remote.webelement.WebElement], bool]:
        """
        Makes an instance of CommentHasBeenPosted callable.

        Args
        ----
            driver : selenium.webdriver.Chrome
                automated browser controlled by Selenium

        Returns
        -------
            Union[List[selenium.webdriver.remote.webelement.WebElement], bool] : \
                the list of WebElements if they were found, False if not
        """
        # find all comments on page
        comments = driver.find_elements(*self.locator)
        for i_comment in comments:
            # find datetime from ith comment element
            datetime_selector = ".//time"
            datetime_elmt = i_comment.find_element(By.XPATH, 
                                                   datetime_selector)
            datetime_attrbt = datetime_elmt.get_attribute("datetime")
            # convert datetime to datetime.datetime then back to string
            datetime_attrbt = datetime.datetime.strptime(datetime_attrbt, "%Y-%m-%dT%H:%M:%S.%fZ")
            datetime_attrbt = datetime_attrbt.strftime("%d/%m/%Y, %H:%M:%S")
            # find publisher from ith comment element
            publisher_selector = ".//time" + "/.."*3 + "//a[not(time)]"
            publisher = i_comment.find_element(By.XPATH, 
                                               publisher_selector)
            publisher = publisher.text
            # find text from ith comment element
            text_selector = ".//span[@style='----base-line-clamp-line-height: 18px; --lineHeight: 18px;'][not(a/time)][not(span)]"
            text = i_comment.find_element(By.XPATH, 
                                          text_selector)
            text = text.text
            # get posted comment's datetime - 1 sec
            self_datetime_1sec_subsracted = datetime.datetime.strptime(self.datetime, "%d/%m/%Y, %H:%M:%S")
            self_datetime_1sec_subsracted = self_datetime_1sec_subsracted - datetime.timedelta(seconds=1)
            self_datetime_1sec_subsracted = self_datetime_1sec_subsracted.strftime("%d/%m/%Y, %H:%M:%S")
            # get posted comment's datetime + 1 sec
            self_datetime_1sec_added = datetime.datetime.strptime(self.datetime, "%d/%m/%Y, %H:%M:%S")
            self_datetime_1sec_added = self_datetime_1sec_added + datetime.timedelta(seconds=1)
            self_datetime_1sec_added = self_datetime_1sec_added.strftime("%d/%m/%Y, %H:%M:%S")
            # check if ith comment datetime in [posted comment's datetime - 1 sec, posted comment's datetime + 1 sec] 
            # time interval and that its text corresponds to the posted comment's text 
            # and that its username corresponds to the posted comment's username
            if (datetime_attrbt in [self_datetime_1sec_subsracted, self.datetime, self_datetime_1sec_added]) \
                and (publisher == self.username) and (text == self.text):
                # if all these conditions are met, we are assuming ith comment is the element representing the posted comment
                return i_comment
        else:
            return False
        
class InputBarHasCleared:
    """
    An expectation for checking that the input bar has cleared after a comment has been submitted.
    """

    def __call__(self, 
                 driver: selenium.webdriver.Chrome) \
                    -> Union[selenium.webdriver.remote.webelement.WebElement, bool]:
        """
        Makes an instance of InputBarHasCleared callable.

        Args
        ----
            driver : selenium.webdriver.Chrome
                automated browser controlled by Selenium

        Returns
        -------
            Union[selenium.webdriver.remote.webelement.WebElement, bool] : the input bar WebElement once it has cleared
        """
        # find comment input
        comment_input_selector = "textarea[class]"
        comment_input = driver.find_element(By.CSS_SELECTOR, comment_input_selector)
        # check if it is cleared
        if comment_input.get_attribute("value") == "":
            return comment_input
        else:
            return False
        