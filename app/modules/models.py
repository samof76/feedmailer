from google.appengine.ext import db
from google.appengine.api import users

import datetime

from tools import calcNextDigestDateTime

class UserPrefs(db.Model):
    user = db.UserProperty(required=True)
    email = db.StringProperty(required=True)
        
    date_joined = db.DateTimeProperty(auto_now_add=True)    
    date_lastlogin = db.DateTimeProperty(auto_now_add=True)    
    emails_received = db.IntegerProperty(default=0)
    emails_last = db.DateTimeProperty()    

    # If true, all feeds will be combined into one digest,
    # if false every feed is delivered in a separate email.
    combined_digest = db.BooleanProperty(default=True)

    # if items are ready to be sent by email
    # ~ user.feeditem_set.count() > 0
    _items_ready = db.BooleanProperty(default=False)
    
    # Next scheduled email sending. see tools.updateUserNextDigest 
    _digest_next = db.DateTimeProperty(default=datetime.datetime.now())
    
def getUserPrefs(user):
    """Get or create user preference object"""
    if user:
        q = db.GqlQuery("SELECT * FROM UserPrefs WHERE user = :1", user)
        prefs = q.get()
        if not prefs:
            prefs = UserPrefs(user=user, email=user.email())
            prefs.put()
        return prefs

class UserDigestInterval(db.Model):
    """One user can have multiple interval groups. Multiple feeds can
    use the same interval group which, when updated, affects all feeds"""
    user = db.UserProperty(required=True)    
    title = db.StringProperty(required=True)
    
    digest_days = db.IntegerProperty(default=0)
    digest_time = db.TimeProperty(default=datetime.time(12, 0))

def getUserDigestIntervals(user):
    """Get or create digest interval object"""
    if user:
        q = db.GqlQuery("SELECT * FROM UserDigestInterval WHERE user = :1", user)
        d = q.get()
        if not d:
            d = UserDigestInterval(user=user, title="Standard")
            d.put()
        return d

class Feed(db.Model):
    user = db.UserProperty(required=True)
    title = db.StringProperty(required=True)
    link_web = db.StringProperty(required=True)
    link_rss = db.StringProperty(required=True)
    #link_hub = db.StringProperty(default=None) # pubsubhubbub link
    
    date_added = db.DateProperty(auto_now_add=True)
    date_last_crawled = db.DateTimeProperty(auto_now_add=True)
    emails_sent = db.IntegerProperty(default=0)
    
    # digest timing can either be a group or a custom setting.
    # if digest_group == None: use custom settings, 
    # else: use group and overwrite custom settings with group settings 
    #      (needed for querying feeds that need to send emails)
    digest_group = db.ReferenceProperty(UserDigestInterval)
    
    # bitfild of days to send digest (Mo=1, Tue=2, Wed=4, ...) or 0=instant
    digest_days = db.IntegerProperty(default=0) 
    digest_time = db.TimeProperty(default=datetime.time(12, 0))

    # if user switches to instant and back, restore previous settings
    last_custom_digest_days = db.IntegerProperty(default=127)
    
    # Next scheduled email sending. see tools.updateUserNextDigest
    _digest_next = db.DateTimeProperty(default=datetime.datetime.now())

    # A list of 10 recent item links for feed crawler to know which items
    # in the feed are new. Helps in case a blogger changes or removes stories 
    _recent_items = db.StringListProperty()

    #def _update_digest_next(self):
    #    self._digest_next = calcNextDigestDateTime(self.digest_days, self.digest_time)
    #    self.save()
        
class FeedItem(db.Model):
    """Feed item waiting to be sent to the user on next delivery interval"""
    feed = db.ReferenceProperty(Feed, required=True)
    user = db.UserProperty(required=True)
    title = db.StringProperty(required=True)
    link = db.StringProperty(required=True)
        
    date_added = db.DateTimeProperty(auto_now_add=True)
