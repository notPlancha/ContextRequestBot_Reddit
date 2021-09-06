import praw
from praw.models import Message
import threading
import time
from datetime import datetime

# this program is provided "as is"

user_agent = ""
client_id = ""
client_secret = ""
username = ""
password = ""
subredditName = ""
messageToUser_Subject = ""
messageToUser_Description = ""
messageToProvideContext = ""  # insert here one {} where the context will be
moderator_username = ""
"""
here is to whom the bot will send the approval request,
it's used here because I can't trust modmail discussions and its relation with inbox
Unfortonately this code is only loaded to only one mod to approve,
but that can be fixed by transforming into a list and looping when this is called
"""
hoursToWait = 6  # The higher the number the more ram it'll be needed

reddit = praw.Reddit(
    user_agent=user_agent,
    client_id=client_id,
    client_secret=client_secret,
    username=username,
    password=password,
)
subreddit = reddit.subreddit(subredditName)
submissions = []


class submissionC:
    def __init__(self, submission, contextProvided=None):
        self.submission = submission
        self.contextProvided = contextProvided
        if hasattr(submission, "created_utc"):
            self.timeout = submission.created_utc + 3600 * hoursToWait
        else:
            self.timeout = datetime.utcnow() + 3600 * hoursToWait
        if len(submissions) == 0:
            self.id = 0
        else:
            self.id = submissions[-1].id + 1

    def sendMessage(self):
        if hasattr(self.submission, "author") and hasattr(self.submission, "url"):
            subreddit.modmail.create(
                messageToUser_Subject, messageToUser_Description, self.submission.author
            )
            return True
        else:
            return False


def getSubmissionFromAuthor(author):
    for i in range(len(submissions)):
        if i.submisison.author.name == author:
            return i
    return None


def getSubmissionFromId(id):
    for i in range(len(submissions)):
        if i.id == id:
            return i
    return None


def detectSubsmissions():
    for submission in subreddit.stream.submissions():
        freeMem()
        if hasattr(subreddit, "user_is_moderator") and subreddit.user_is_moderator:
            sub = submissionC(submission)
            if sub.sendMessage():
                submissions.append(sub)


def detectDms():
    for message in reddit.inbox.stream():
        if isinstance(message, Message):
            subIndex = getSubmissionFromAuthor(message.author.name)
            if subIndex is None:
                for moderator in subreddit.moderator():
                    if message.author.name == moderator.name:
                        mes = message.body
                        if "approve" in mes:
                            try:
                                id = int(mes.split()[-1])
                            except ValueError:
                                message.reply("There was an error approving, try again")
                                break
                            index = getSubmissionFromId(id)
                            if index is None:
                                message.reply("Unknown Id, couldnt accept")
                            else:
                                sub = submissions[index]
                                comm = sub.submission.reply(
                                    messageToProvideContext.format(sub.contextProvided)
                                )
                                comm.mod.distinguish(sticky=True)
                                message.reply("Context accepted")
                                del submissions[index]
                            break
                        elif "deny" in mes:
                            try:
                                id = int(mes.split()[-1])
                            except ValueError:
                                message.reply("There was an error denying, try again")
                                break
                            index = getSubmissionFromId(id)
                            if index is None:
                                message.reply("Unknown Id, couldnt deny")
                            else:
                                del submissions[index]
                                message.reply("Context Denied")
                            break
            else:
                sub = submissions[subIndex]
                if message.body.strip() != "":
                    sub.contextProvided = message.body
                    sub.timeout = datetime.utcnow() + 3600 * hoursToWait
                    reddit.redditor(moderator_username).message(
                        "Approval request #" + str(sub.id),
                        f'User {sub.submission.author} sent this context in regards to [this submission]({sub.submission.url}): "{sub.context}". If you want to approve or deny this context reply to this message with either "approve {sub.id}" or "deny {sub.id}"(without quotes)',
                    )
                    message.reply("Thank you, you're context was sent for approval")


def freeMem():
    while True:
        now = datetime.utcnow()
        global submissions
        submissions = [i for i in submissions if i.timeout >= now]
        time.sleep(300)  # 5 min


t1 = threading.Thread(target=detectSubsmissions)
t2 = threading.Thread(target=detectDms)
t3 = threading.Thread(target=freeMem)
t1.start()
t2.start()
t3.start()
t1.join()
t2.join()
t3.join()
# this code can get confused if a user submits more than 1 time in the time limit
