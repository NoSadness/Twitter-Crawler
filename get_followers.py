import tweepy
import time
import os
import sys
import json
import argparse
from twython import Twython
from math import ceil

FOLLOWING_DIR = 'following/twitter-users/'
TWEETS_DIR = 'following/tweets/'
MAX_FRIENDS = 200
FRIENDS_OF_FRIENDS_LIMIT = 200

if not os.path.exists(FOLLOWING_DIR):
    os.makedirs(FOLLOWING_DIR)

if not os.path.exists(TWEETS_DIR):
    os.makedirs(TWEETS_DIR)

enc = lambda x: x.encode('ascii', errors='ignore')

CONSUMER_KEY = '3IgaK6BNq36uotDhDYgl4LscA'
CONSUMER_SECRET = 'r8q2s1BrVKA5dVpts2FGIwPBV9OOhrCMZGhrif9UimJXreA4ca'

ACCESS_TOKEN = '821853490691657733-CfEYFgPTap4ebWow7g80ooEVkNHg5CT'
ACCESS_TOKEN_SECRET = 'wrBxLd2nrFn4fjtbYzhhAYE9BtZ7RS2E7AAkqvdEI6hZ9'

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

api = tweepy.API(auth)
twitter=Twython(CONSUMER_KEY,access_token=ACCESS_TOKEN)

def get_tweets(id):
    user = api.get_user(id)
    profile = user.description
    print(user.id)
    screen_name = user.screen_name
    
    tweets = []
    tweets_time = []

    #https://codeandculture.wordpress.com/2016/01/19/scraping-twitter-with-python/
    user_timeline=twitter.get_user_timeline(id=id,count=1) #get most recent tweet
    lis=user_timeline[0]['id']-1 #tweet id # for most recent tweet
    #only query as deep as necessary
    tweetsum= user_timeline[0]['user']['statuses_count']
    cycles = int(ceil(tweetsum / 200))
    if cycles>16:
        cycles=16 #API only allows depth of 3200 so no point trying deeper than 200*16
    time.sleep(60)
    for i in range(0, cycles): ## iterate through all tweets up to max of 3200
        incremental = twitter.get_user_timeline(id=id,
        count=200, include_retweets=True, max_id=lis)
        user_timeline.extend(incremental)
        lis=user_timeline[-1]['id']-1
        time.sleep(60) ## The API allows 15 calls per 15 minutes

    for tweet in user_timeline:
        tweets.append(tweet['text'])
        tweets_time.append(tweet['created_at'])
        print(tweet['text'].encode('utf-8'))
        print(tweet['created_at'].encode('utf-8'))

    tfname = os.path.join(TWEETS_DIR, str(id) + 'tweets' + '.json')
    
    with open(tfname, "w") as outfile:
        json.dump({'tweets':tweets, 'tweetstamp': tweets_time, 'user':screen_name,
                   'profile':profile}, outfile, indent = 4)

def get_friends_tweets(id):
    friends_ids = []
    c = tweepy.Cursor(api.friends_ids, id=id).items()
    while True:
        try:
            user = c.next();
            friends_ids.append(user)
        except tweepy.TweepError:
            time.sleep(60*15)
            continue
        except StopIteration:
            break

    for friend in friends_ids:
        get_tweets(friend)


    
def get_follower_ids(centre, max_depth=1, current_depth=0, taboo_list=[]):

    if current_depth == max_depth:
        return taboo_list

    if centre in taboo_list:
        # we've been here before
        return taboo_list
    else:
        taboo_list.append(centre)

    try:
        userfname = os.path.join(FOLLOWING_DIR, str(centre) + '.json')
        if not os.path.exists(userfname):
            print ('Retrieving user details for twitter id %s' % str(centre))
            while True:
                try:
                    user = api.get_user(centre)

                    d = {'name': user.name,
                         'screen_name': user.screen_name,
                         'id': user.id,
                         'friends_count': user.friends_count,
                         'followers_count': user.followers_count,
                         'followers_ids': user.followers_ids()}

                    with open(userfname, 'w') as outfile:
                        outfile.write(json.dumps(d, indent=1))

                    user = d
                    break
                except tweepy.TweepError as error:
                    print (type(error))

                    if str(error) == 'Not authorized.':
                        print ('Can''t access user data - not authorized.')
                        return taboo_list

                    if str(error) == 'User has been suspended.':
                        print ('User suspended.')
                        return taboo_list

                    errorObj = error[0][0]

                    print (errorObj)

                    if errorObj['message'] == 'Rate limit exceeded':
                        print ('Rate limited. Sleeping for 15 minutes.')
                        time.sleep(15 * 60 + 15)
                        continue

                    return taboo_list
        else:
            user = json.loads(open(userfname).read())

        screen_name = enc(user['screen_name'])
        fname = os.path.join(FOLLOWING_DIR, screen_name + '.csv')
        friendids = []

        if True:
            if not os.path.exists(fname):
                print ('No cached data for screen name "%s"' % screen_name)
                with open(fname, 'w') as outf:
                    params = (enc(user['name']), screen_name)
                    print ('Retrieving friends for user "%s" (%s)' % params)

                    # page over friends
                    c = tweepy.Cursor(api.friends, id=user['id']).items()

                    friend_count = 0
                    while True:
                        try:
                            friend = c.next()
                            friendids.append(friend.id)
                            params = (friend.id, enc(friend.screen_name), enc(friend.name))
                            outf.write('%s\t%s\t%s\n' % params)
                            friend_count += 1
                            if friend_count >= MAX_FRIENDS:
                                print ('Reached max no. of friends for "%s".' % friend.screen_name)
                                break
                        except tweepy.TweepError:
                            # hit rate limit, sleep for 15 minutes
                            print ('Rate limited. Sleeping for 15 minutes.')
                            time.sleep(15 * 60)
                            continue
                        except StopIteration:
                            break
            else:
                friendids = [int(line.strip().split('\t')[0]) for line in file(fname)]

            print ('Found %d friends for %s' % (len(friendids), screen_name))

            # get friends of friends
            cd = current_depth
            if cd+1 < max_depth:
                for fid in friendids[:FRIENDS_OF_FRIENDS_LIMIT]:
                    taboo_list = get_follower_ids(fid, max_depth=max_depth,
                        current_depth=cd+1, taboo_list=taboo_list)

            if cd+1 < max_depth and len(friendids) > FRIENDS_OF_FRIENDS_LIMIT:
                print ('Not all friends retrieved for %s.' % screen_name)

    except Exception as error:
        print ('Error retrieving followers for user id: ', centre)
        print (error)

        if os.path.exists(fname):
            os.remove(fname)
            print ('Removed file "%s".' % fname)

        sys.exit(1)

    return taboo_list

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--screen-name", required=True, help="Screen name of twitter user")
    ap.add_argument("-d", "--depth", required=True, type=int, help="How far to follow user network")
    args = vars(ap.parse_args())

    twitter_screenname = args['screen_name']
    depth = int(args['depth'])

    if depth < 1 or depth > 3:
        print ('Depth value %d is not valid. Valid range is 1-3.' % depth)
        sys.exit('Invalid depth argument.')

    print ('Max Depth: %d' % depth)
    matches = api.lookup_users(screen_names=[twitter_screenname])

    if len(matches) == 1:
        print (get_follower_ids(matches[0].id, max_depth=depth))
        print (get_tweets(matches[0].id))
        print (get_friends_tweets(matches[0].id))
    else:
        print ('Sorry, could not find twitter user with screen name: %s' % twitter_screenname)
