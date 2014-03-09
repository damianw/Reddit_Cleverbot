#!/usr/bin/env python2

import math
import time
import random
from threading import Thread
import praw
from praw import Reddit
from cleverbot import Cleverbot
from collections import deque
from copy import copy

USERAGENT = "Reddit_Cleverbot/1.0"
SUMMON = '/u/Reddit_Cleverbot'

class Reddit_Cleverbot:

  def __init__(self, username, password, subreddit='all', useragent=USERAGENT):
    self.username = username
    self.password = password
    self.useragent = useragent
    self.subreddit = subreddit
    self.reddit = Reddit(useragent)
    self.reddit.login(username, password)
    self.stopped = True
    self.thread = None
    self.done = set()
    self.conversations = dict()

  def random_hot_comment(self):
    sub = self.reddit.get_subreddit(self.subreddit)
    hot = [post for post in sub.get_hot(limit=25)]
    post = random.choice(hot)
    comments = praw.helpers.flatten_tree(post.comments)
    # filter the comments to remove already-replied ones
    comments = [comment for comment in comments if comment not in self.done and isinstance(comment, praw.objects.Comment)]
    return random.choice(comments[0:100])

  def random_comment(self):
    comments = self.reddit.get_comments(self.subreddit)
    # filter the comments to remove already-replied ones
    comments = [comment for comment in comments if comment not in self.done]
    return random.choice(comments)

  def get_summoned_comments(self):
    comments = self.reddit.get_comments(self.subreddit)
    children = [comment for comment in comments 
      if comment not in self.done and SUMMON in comment.body]
    # print "--> " + str(len(children)) + " summons found!"
    return [self.reddit.get_info(thing_id=comment.parent_id) for comment in children]

  def reply(self, comment):
    if self.reddit.get_info(thing_id=comment.parent_id).author.name == self.username:
      # TODO: handle a threaded conversation over restarts. will need a DB. ugh
      pass
    if comment.parent_id in self.conversations:
      cleverbot = self.conversations[comment.parent_id]
    else:
      cleverbot = Cleverbot()
    response = cleverbot.ask(comment.body)
    post = comment.reply(response)
    self.done.add(comment.id)
    self.conversations[post.id] = copy(cleverbot)

  def reply_unread(self, interval):
    for item in self.reddit.get_unread():
      if item.parent_id not in self.conversations:
        print "Could not find conversation! Ignoring for now."
        pass
      self.reply(item)
      item.mark_as_read()
      time.sleep(interval)

  def reply_to_summons(self):
    summons = self.get_summoned_comments()
    for comment in summons:
      self.reply(comment)

  def _run_random(self, interval):
    while not self.stopped:
      self.reply_unread(interval)
      self.reply(self.random_hot_comment())
      time.sleep(interval)

  def run_random(self, interval):
    self.stopped = False
    self.thread = Thread(target=self._run_random, args=(interval,))
    self.thread.start()

  def stop(self):
    self.stopped = True
    #self.thread.join()