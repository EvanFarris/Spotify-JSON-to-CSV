# Purpose

This script strips a user's song data requested from [Spotify's extended streaming history](https://spotify.com/us/account/privacy) and aggregates the data into two output files, one to look at with a spreadsheet visualizer, and the other to output the songs to [a Spotify playist](https://github.com/EvanFarris/CSV-to-Spotify-Playlist).

The first output file is of the form:
> output_*timestamp*.csv

Which can be thrown into any spreadsheet tool or program to see the results, or used for any other data visualization tool.
![Screenshot of the first three lines of the file using Google Sheets](i.imgur.com/D2R6cN0.png)
Data shown for each song:
	
	-The name of the song
	-The Artist of the song
	-The number of times you have played the song to completion
	-The number of times the song ended early
	-The total number of times yo have played the song (previous two bullet points combined)
	-The total length of time (in minutes) you have listened to the song
	-The first date you played the song
	-The last date you played the song
	-The Spotify URI for the song which you can copy/paste into spotify's search bar to find the song

The second output file is of the form:
> uri_only_*timestamp*.csv

This is meant to be used with [my other project](https://github.com/EvanFarris/CSV-to-Spotify-Playlist) which converts the file to a spotify playlist if one wanted to.

# Usage
This program only works with python 3.10+ because of the usage of match cases, but should work on both Windows/Linux os.
```
python3 spotifyjsontocsv.py -dir <path>
python3 spotifyjsontocsv.py -dir <path> -sort <sortType> -minCount <num> -maxCount <num> -minRatio < 0<=float<=1 > -maxRatio < 0<=float<=1 > -minDate <YYYY-MM-DD> -maxDate <YYYY-MM-DD> -ignoreFile <path> 
```
The first line above is the basic command, which includes every song entry given.
The second line above has all of the possible options that one can use
## Options

-dir is the full or relative path the directory containing endsong_*number*.json files, ex: C:\Users\Evan\Downloads\my_spotify_data

-sort is for the attribute you want the file to be sorted on. Possible values are: "completion" "total" "ended_early" and "listen_time" all relating to the previous list above. By default, the value is sorted on "total"

-minCount is the minimum value (based on the sort) needed to be on the sheet. The first example below needs at least 5 total plays to be on the list, while the second needs the song to have been played for at least 5 minutes.

```
-sort "total" -minCount 5
-sort "listen_time" -minCount 5
```

-maxCount is the maximum counterpart to minCount, an upper limit of values

-minRatio is a float between zero and one, which requires the ratio of  *Number of song completions* / *Total plays* to be at or above the ratio

-maxRatio is the maximum counterpart to maxCount, an upper limit to the ratio

-minDate is the minimum date that an entry needs to be processed. Format: YYYY-MM-DD

>-minDate 2019-01-01

-maxDate is the maximum counterpart of minDate.

-ignoreFile requires a path to a csv file generated by this program. Any songs listed in this file will be ignored in the new output files, used to exclude songs you've already looked at.

# Pitfalls
The biggest pitfall is that entries in the extended spotify history can be null. That is, there is no discernable data that can be used by this program, other than the number of times a null-filled entry has been given to you. This is an issue that only Spotify can fix, and it seemingly effects recent data; for my friends and I, valid entries stopped at 2022-10-14, even though we use it daily.

Total completion is based solely on the end_reason field in the original data being "trackdone". So no matter if you've listened to the entirety of the song, or only the last .1% of it, as long as the reason is "trackdone", it will be counted. 
This criteria was chosen as ms_played can be slightly off of the full length of the song, but still have "trackdone" for the end_reason.
Also while playing with the end_reason field, I discovered that Spotify doesn't have a public list of all possible fields, and while using my personal data, I found 12 options, and notably one was triggered only twice (As the reason only occurred on the web client, but not the desktop or mobile app). Overall, (slight exaggeration) 98% of the end_reason field fell into three categories, one being "trackdone" while the other two of which were an indicator that I manually changed the song.

Songs reuploaded, remixed, or uploaded as a solo release and included in another album by an artist are treated as separate songs. They have different spotify URLs, and making it based solely on track title would potentially miscredit artists/misrepresent the data, if a user happened to listen to multiple songs with the same title.

# Future work
I think some sort of tie-in / genre analysis with spotify's API could be done, but I think that would fit better into [the other project](https://github.com/EvanFarris/CSV-to-Spotify-Playlist), as it already interacts with Spotify's API, and is tied to being more of a web service.
