import re

import feedgenerator
import pytz
import tweepy
from flask import Blueprint

from twootfeed import param, twitter_api

twitter_bp = Blueprint('twitter', __name__)


@twitter_bp.route('/<query_feed>', methods=['GET'])
@twitter_bp.route('/tweets/<query_feed>', methods=['GET'])
def tweetfeed(query_feed):
    """ generate a rss feed from parsed twitter search """

    if twitter_api:
        tweet = {}
        buffered = []

        for i in tweepy.Cursor(twitter_api.search,
                               q=query_feed,
                               tweet_mode='extended').items():
            try:
                i.full_text
            except Exception:
                break
            else:
                try:
                    retweeted_status = i.retweeted_status

                except Exception:
                    retweeted_status = False

                if not retweeted_status:  # only the original tweets

                    tweet['text'] = i.full_text
                    tweet['screen_name'] = i.user.screen_name
                    tweet['profile_image_url'] = i.user.profile_image_url_https
                    tweet['user_name'] = i.user.name
                    tweet['user_url'] = i.user.url
                    tweet['id_str'] = i.id_str
                    tweet['created_at'] = i.created_at
                    tweet['source'] = i.source
                    tweet['retweets'] = i.retweet_count
                    tweet['favorites'] = i.favorite_count
                    tweet['tweet_url'] = 'https://twitter.com/' + tweet[
                        'user_name'] + '/status/' + tweet['id_str']

                    tweet['htmltext'] = '<blockquote><div><img src="' + tweet[
                        'profile_image_url'] + \
                        '" alt="' + tweet['screen_name'] + \
                        '" />   <strong>' + tweet['user_name'] + \
                        ': </strong>' + tweet['text'] + \
                        '<br><i>Source: ' + tweet[
                            'source'] + '</i>'

                    user_mentionslist = i.entities.get('user_mentions')
                    for j in user_mentionslist:
                        if j != '':
                            tweet['htmltext'] = re.sub(
                                ('@' + j.get('screen_name')),
                                ('<a href="https://twitter.com/'
                                 + j.get('screen_name')
                                 + '" target="_blank">@'
                                 + j.get('screen_name') + '</a>'),
                                tweet['htmltext'])

                    hashtaglist = i.entities.get('hashtags')
                    for j in hashtaglist:
                        if j != '':
                            tweet['htmltext'] = re.sub(
                                ('#' + j.get('text')),
                                ('<a href="https://twitter.com/hashtag/'
                                 + j.get('text')
                                 + '?src=hash" target="_blank">#'
                                 + j.get('text') + '</a>'),
                                tweet['htmltext']
                            )

                    urllist = i.entities.get('urls')
                    for j in urllist:
                        if j != '':
                            tweet['htmltext'] = re.sub(
                                (j.get('url')),
                                ('<a href="'
                                 + j.get('expanded_url')
                                 + '" target="_blank">'
                                 + j.get('display_url')
                                 + '</a>'),
                                tweet['htmltext'])
                    try:
                        medialist = i.extended_entities.get('media')
                    except AttributeError:
                        pass
                    else:
                        if medialist is not None:
                            tweet['htmltext'] = tweet['htmltext'] + '<br> '
                            for j in medialist:
                                if j != '':
                                    if j.get('type') == 'photo':
                                        tweet['htmltext'] = re.sub(
                                            j.get('url'), '',
                                            tweet['htmltext']
                                        )
                                        tweet['htmltext'] = tweet['htmltext'] \
                                            + '<a href="' \
                                            + j.get('media_url_https')\
                                            + '" target="_blank"> ' \
                                              '<img src="' \
                                            + j.get('media_url_https') \
                                            + ':thumb' + '"> ' \
                                            + '</a>'

                    location = i.place
                    if location is not None:
                        tweet['htmltext'] = tweet['htmltext'] \
                                            + '<br><i>Location: ' \
                                            + location.full_name + '</i>'

                    tweet['htmltext'] = tweet['htmltext'] + '<br> ♻ : ' + str(
                        tweet['retweets']) + ', ' + '♥ : ' + str(
                        tweet['favorites']) + '</div></blockquote>'

                    buffered.append(tweet.copy())

        utc = pytz.utc
        f = feedgenerator.Rss201rev2Feed(
            title=param['twitter']['title'] + '"' + query_feed + '"',
            link=param['twitter']['link'] + query_feed,
            description=param['twitter']['description'],
            language=param['feed']['language'],
            author_name=param['feed']['author_name'],
            feed_url=param['feed']['feed_url'])

        for tweet in buffered:
            f.add_item(
                title=tweet['screen_name']
                + ' ('
                + tweet['user_name'] + '): '
                + tweet['text'],
                link=tweet['tweet_url'],
                pubdate=utc.localize(tweet['created_at']).astimezone(
                    pytz.timezone(param['feed']['timezone'])),
                description=tweet['htmltext'])

        xml = f.writeString('UTF-8')
    else:
        xml = 'error - Twitter parameters not defined'

    return xml
