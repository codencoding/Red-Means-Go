<p align="center">
    <b style="font-size: 45px;">Red Means Go</b><br>
    <img width="614" height="345" src="https://raw.githubusercontent.com/codencoding/Red-Means-Go/gh-pages/images/site-logo.png">
</p>

## Abstract
YouTube has become a significant source of income for many content creators, and they are always looking for the best way to grow their channel. When a YouTube video gets more views, the Content Creator makes more money. The purpose of our project is to analyze the significance of the various features of a YouTube preview thumbnail that can contribute to a video’s success. We believe that there are features in YouTube thumbnails that can be extracted and used to identify what makes a video more appealing to potential viewers. 

## Introduction
Our research question is what YouTube thumbnail features, if any, have an effect on the amount of views that the video gets. Our hypothesis is that the more popular videos will likely have more provocative thumbnails that grab that attention of viewers. We believe that popular thumbnails will have more contrast, brightness, engaging subject matter, or just general attractiveness to potential viewers. 
We used YouTube’s Data API (v3) to create a data set that’s sourced from a YouTube search for “Fortnite”. We scrape the first 200 query results, and then scrape the first 100 videos from each unique channel, resulting in around 10,000 videos. Then we create a gamut of statistics from the metadata to best assess how well the video is doing according to YouTube. Because our data is from YouTube, which is an ever changing ecosystem, our results are only indicative of the data we scraped on April 16th, 2020. The thumbnails were created by YouTube content creators and/ or their thumbnail designers, while video metadata was provided by YouTube.
We think our analysis is an interesting investigation because YouTube is a very prominent cultural influence, and so being able to better attract a larger audience would be of general interest to anyone pursuing a YouTube-based career. Because of the recent monetization of YouTube on a large scale, more and more people are trying to make a living off of YouTube. We hope that our results will help give any potential YouTuber insight into what features are most relevant in a thumbnail. In addition, as avid YouTube viewers, we have an intuition that thumbnails play a factor in YouTube’s recommendation algorithm. We hoped to learn more about this rather vague recommendation system and figure out what factors help in a video’s success, if any.

## Methods
The features we will use to address our question are a combination of metadata and image features. For the metadata features, we use the view count of the YouTube video as well as a z-scored view count, calculated by taking fortnite videos from the same channel within the same month, that way we can compare channel to channel through the z-scores. For our image features, we are using image brightness, saturation, hue, unique_rgb_ratio (number of unique rgb values divided by the number of pixels), and the number of faces present (using DeepFace). For our metadata features, we used the YouTube Data API (v3) to get our metadata such as views. For the image features, we used the skimage library to extract image brightness, saturation, hue, and rgb values. For face recognition, we used DeepFace from DLib. We  computed our own extracted features such as unique_rgb_ratio and z-score views. 
The analytical techniques we are using are as follows. For initial eda, we computed the correlation between each image feature column and the z_views column. This way we can see if there is any correlation between a specific image feature and the amount of views the video got (relative to similar videos from the same channel). For a deeper analysis, we wanted to combine images features to see if a certain combination of image features would attract more viewers. To do this, we first tried feeding all image feature columns into a random forest regressor and gradient boosted regressor. Then we plotted the predicted values vs. the real values to see any patterns in the predictions. We also multiplied sets of two/three/four features together to make higher level features, then trained a linear regression model with these features. We also looked at the predictions for this model to see any patterns in the predictions. We did not use a neural net to generate features for regression as the generated high level features are not clear enough to make a distinction between which image features have impact on the video views.

## Results
The results of our deep dive into how image features of thumbnails relate to video views are that there is no strong correlation between our thumbnail image features and video views. To show this, we’ve selected a couple visualizations to help see these results.

<p align="center">
    <img width="614" height="345" src="https://raw.githubusercontent.com/codencoding/Red-Means-Go/gh-pages/images/fig1.png">
</p>

<p align="center">
    <small> Figure (1): Random Forest Regression on the z-score for video views </small>
</p>

<p align="center">
    <img width="614" height="345" src="https://raw.githubusercontent.com/codencoding/Red-Means-Go/gh-pages/images/fig2.png">
</p>

<p align="center">
    <small> Figure (2): Gradient Boosted Regression on the z-score for video views </small>
</p>

lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff 

<p align="center">
    <img width="614" height="345" src="https://raw.githubusercontent.com/codencoding/Red-Means-Go/gh-pages/images/fig3.png">
</p>

<p align="center">
    <small> Figure (3): Thumbnail image statistics </small>
</p>

lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff lorem ipsum text stuff 

## Discussion
For all models, the predictions scored worse than predicting the mean for all values, indicating no such patterns exists, alluding to a lack of correlation between our image features and video views. The score for each model is either negative or very close to 0. According to SKLearn’s documentation, a score of 0 would be achieved by predicting the mean of the target column for all values. Because our models scored around 0 while trained on thumbnail features, we cannot say that there is any significant correlation between our thumbnail features and video views. We think this result is likely due to the relative importance of the thumbnail to the content of the video. We additionally looked at the correlation of the individual image features and video views, and found no significant correlation.

Since there are so many aspects that go into whether someone watches the video such as title, thumbnail, video duration, and most importantly, the contents of the video, it makes sense that there would not be a strong correlation between thumbnail image features and video views. It is also worth noting that these results are specifically for Fortnite Gaming videos uploaded in March/April 2020, and our image features were relatively basic. If the scope of this project was larger, we could look at more genres and more videos per genre, along with more advanced image features. We still think that video thumbnails affect video views, but we lack the quantifiable results to say so. 

With the growth of social media platforms such as YouTube, the job title of ‘content creator’ has become a more common and financially viable occupation. As such, our work on YouTube thumbnails will help creators put numbers to the trends they inherently sense in the ever changing YouTube thumbnail meta, allowing them to make changes to their thumbnails with less guesswork and backed with more relevant data. Besides the impact on those creating thumbnails, our work also explores how audiences of specific genres of videos react to different types of thumbnails because thumbnails are the front cover of a video and holds the potential to attract millions of users who aren’t already followers.

Our approach takes advantage of the digital format as we were able to scrape and process mass amounts of data which wouldn’t have been easy to do manually which enabled us to acquire and work with a substantially larger dataset. Since we parameterized our work, it is very flexible and can be configured to analyze different genres of Youtube videos which could be useful for a Youtuber as it would provide them with a snapshot of the current YouTube thumbnail meta and act as a soft guide when they are making their own.
We could expand our project scope in the future by looking at other video games in the YouTube Gaming category or even other YouTube categories (such as make-up videos or VLOGS). Another direction is creating a live thumbnail meta analysis. We suspect that certain features in thumbnails rise and fall in popularity similar to fashion, so having a live trend analysis of thumbnails could prove useful. For instance, if faces in the thumbnail start becoming less popular, YouTubers might want to stay away from putting their face on a thumbnail. However, they might use the thumbnail meta analysis as a way to go against the meta which would make their thumbnails stick out. 

## References
Louise Myers 2019, accessed April 6, 2020, 

[https://louisem.com/198803/how-to-youtube-thumbnails](https://louisem.com/198803/how-to-youtube-thumbnails)

EmpLemon 2020, accessed May 4, 2020,

[https://www.youtube.com/watch?v=-6-i75wDIBE](https://www.youtube.com/watch?v=-6-i75wDIBE)
