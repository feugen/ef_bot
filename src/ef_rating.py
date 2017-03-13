import random
import src.ef_functions as ef_functions
from apiclient import errors


class Rating:

    def __init__(self):

        # Hilfsfunktion instance
        self.inst_helpfct = ef_functions.Hilfsfunktionen_yt()

    def youtube_video_manual(self, yt_handle, yt_video_id, yt_rating="like", thread_name=None):

        # Since this function is primitive and is always in a loop of other functions,
        # we have to delay the response time to simulate a human. So call a
        # time_function here from ef_functions. Don't do this in other auto functions,
        # since you will get 2 delays.

        if self.inst_helpfct.time_function():

            yt_statistics = self.inst_helpfct.video_statistics_by_video_id(yt_handle, yt_video_id)
            # ViewCount should be at least 5 times higher than likeCount to prevent detection

            if int(yt_statistics['likeCount']) != 0:
                ratio = int(yt_statistics['viewCount']) / int(yt_statistics['likeCount'])
            else:
                ratio = int(yt_statistics['viewCount'])

            # The purpose is to avoid None in output
            if thread_name is None:
                thread_name = ''
            else:
                thread_name += ': '

            if ratio > 5:
                # get current rating
                rating_result = yt_handle.videos().getRating(id=yt_video_id).execute()

                # If not rated yet, than rate the video, but prevent to try to rate a video twice.
                if rating_result['items'][0]['rating'] == 'none':
                    try:
                        yt_handle.videos().rate(id=yt_video_id, rating=yt_rating).execute()
                    except errors.HttpError as e:
                        print(self.inst_helpfct.timestamp() + thread_name +
                              'An HTTP error {0} occurred:{1}'.format(e.resp.status, e.content))
                    else:
                        print(self.inst_helpfct.timestamp() + thread_name + 'Rating::youtube_video_manual: Video '
                              + yt_video_id + ' rated: ' + yt_rating)

                elif rating_result['items'][0]['rating'] == 'like' and rating_result['items'][0]['rating'] != yt_rating:
                    try:
                        yt_handle.videos().rate(id=yt_video_id, rating=yt_rating).execute()
                    except errors.HttpError as e:
                        print(self.inst_helpfct.timestamp() + thread_name + 'An HTTP error {0} occurred:{1}'
                              .format(e.resp.status, e.content))
                    else:
                        print(self.inst_helpfct.timestamp() + thread_name + 'Rating::youtube_video_manual: Video '
                              + yt_video_id + ' rated: ' + yt_rating)

                elif rating_result['items'][0]['rating'] == 'dislike' and \
                                rating_result['items'][0]['rating'] != yt_rating:
                    try:
                        yt_handle.videos().rate(id=yt_video_id, rating=yt_rating).execute()
                    except errors.HttpError as e:
                        print(self.inst_helpfct.timestamp() + thread_name + 'An HTTP error {0} occurred:{1}'
                              .format(e.resp.status, e.content))
                    else:
                        print(self.inst_helpfct.timestamp() + thread_name + 'Rating::youtube_video_manual: Video '
                              + yt_video_id + ' rated: ' + yt_rating)
                else:
                    print(self.inst_helpfct.timestamp() + thread_name + 'Rating::youtube_video_manual:'
                                                                             " Videorating for " + yt_video_id +
                          " already exist or not possible")
            else:
                print(self.inst_helpfct.timestamp() + thread_name + "Rating::youtube_video_manual:"
                            "Attention, Viewcount devided by LikeCount is less than 5, its {0} for the video {1}."
                                                                         " Video was not rated".format(ratio, yt_video_id))
        return True

    def youtube_video_auto(self, yt_handle, thread_name=None):

        # Get a video list from DB
        video_list = self.inst_helpfct.get_video_list_from_sqlite()

        # Create a reason list
        reason = []
        for i in video_list:
            reason.append(i[1])

        # Now get the video list and reason for each video
        # and pass the proper arguments to youtube_video_manual
        n = 0
        while n < len(video_list):

            video_link = video_list[n][0]
            # video_link = entry[0]
            video_id = self.inst_helpfct.get_yt_video_id_from_link(video_link)
            rating = reason[n]

            rating_string = None

            if rating == 1 or None:
                rating_string = 'like'
            if rating == 0:
                rating_string = 'dislike'

            self.youtube_video_manual(yt_handle, video_id, rating_string, thread_name)
            n += 1

        return 0

    def youtube_channel_auto(self, yt_handle, video_list_by_channel, channel_list_by_id, thread_name):

        # Create a reason list
        reason = []
        for i in channel_list_by_id:
            reason.append(i[1])

        # Now get the video list and reason for each channel and pass the proper arguments to youtube_video_manual
        n = 0
        while n < len(video_list_by_channel):

            channel_list = video_list_by_channel[n]
            channel_reason = reason[n]

            for video_id in channel_list:
                # Get the correct rating properties and run the rating function
                if channel_reason == 1:
                    # 95% of all videos are rated up, and 5 not rated
                    if random.randint(0, 99) < 5:
                        yt_rating = "none"
                    else:
                        yt_rating = "like"
                elif channel_reason == 0:
                    # 90% of all videos are rated down, and 5 not rated
                    if random.randint(0, 99) > 9:
                        yt_rating = "dislike"
                    else:
                        yt_rating = "none"
                elif channel_reason is None:
                    rating_list = ['dislike', 'like', 'like', 'none', 'none']
                    yt_rating = rating_list[random.randint(0, 4)]
                else:
                    rating_list = ['dislike', 'like', 'like', 'none', 'none', 'none', 'none']
                    yt_rating = rating_list[random.randint(0, 6)]
                # The manual rating function (youtube_video_manual) is calling a delay function, so the loop is slow
                self.youtube_video_manual(yt_handle, video_id, yt_rating, thread_name)
            n += 1