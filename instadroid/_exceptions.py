class NoInternetConnectionException(Exception):
    """
    Exception raised when there is no internet connection.
    """

    def __init__(self):
        self.message = "There is no internet connection."
        super().__init__(self.message)

class ClosedWebdriverException(Exception):
    """
    Exception raised when trying to use a webdriver but it has been closed.
    """

    def __init__(self):
        self.message = "The webdriver you want to use has been closed."
        super().__init__(self.message)

class IncorrectCredentialsException(Exception):
    """
    Exception raised when credentials are incorrect.
    """

    def __init__(self):
        self.message = "The username and/or password are incorrect."
        super().__init__(self.message)


class BlockedAccountException(Exception):
    """
    Exception raised when the account is blocked.
    """

    def __init__(self):
        self.message = "The account has been blocked due to a detected unusual login attempt."
        super().__init__(self.message)


class IncorrectLinkException(Exception):
    """
    Exception raised when link-related issues occur.

    Attributes
    ----------
        message : str
            explanation of the error
    """

    def __init__(self, message="The page does not exist."):
        self.message = message
        super().__init__(self.message)

class TryCountExceeded(Exception):
    """
    Exception raised when a function has failed multiple times in a row.
    """

    def __init__(self):
        self.message = "The function has failed multiple times in a row."
        super().__init__(self.message)

class ReplyNotFoundException(Exception):
    """
    Exception raised when a reply to a comment is not found.
    """

    def __init__(self, message="This reply does not exist under the current comment."):
        self.message = message
        super().__init__(self.message)

class CommentNotSharedByUserException(Exception):
    """
    Exception raised when a comment was not published by the user, but the user is trying to delete it.
    """

    def __init__(self):
        self.message = "This comment was not shared by the user : it is impossible to delete it."
        super().__init__(self.message)

class LimitedCommentsException(Exception):
    """
    Exception raised when trying to comment on a post where the comments have been restricted.
    """

    def __init__(self):
        self.message = "Comments on this post have been restricted."
        super().__init__(self.message)
        