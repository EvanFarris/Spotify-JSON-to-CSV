import time
import sys
import json
import csv
import os
import pandas as pd

if len(sys.argv) < 5:
    print("\nFormat: python spotifyjsontocsv.py <criteria> <mininum number of criteria> <Ratio completed> <path_to_directory> <Optional_Spotify_uri_only file>")
    print("\nPossible criteria: completion/ended_early/total/listentime")
    print("\nRatio criteria: Shows songs you've completed more than the minimum percent of times\n Ex: python spotifyjsontocsv.py total 20 .75 C:\\directory_with_spotify_data C:\\output_12345.txt")
    print("\nThis would give you all the songs that you have played more than 20 times, completed 75% of the time\nAnd sorted by total number of plays in descending order, ignoring uris that are in output_12345.txt ")
    sys.exit()

#Grab all the json files in the directory given, if none, exit
criteriaArg = sys.argv[1]
min = int(sys.argv[2])
minRatio = float(sys.argv[3])
path = sys.argv[4]
comparisonFile = None
comparisonArr = []
if len(sys.argv) == 6:
    comparisonFile = sys.argv[5]

files = [f for f in os.listdir(path) if f.endswith(".json") and f.startswith("endsong_")]
if len(files) == 0:
    print("No files found in" + path)
    sys.exit()
if min < 0:
    print("Min out of bounds")
    sys.exit()
if minRatio > 1.0 or minRatio < 0.0:
    print("minRatio out of bounds")
    sys.exit()
if criteriaArg == "completion":
    criteria = 0
elif criteriaArg == "ended_early":
    criteria = 1
elif criteriaArg == "listenTime":
    criteria = 4
elif criteriaArg == "total":
    criteria = 5

#Setup the output file name
ts = str(int(time.time()))
outputfn = "output_" + ts + ".csv"

#Overall stat tracking
null_song_count = 0
total_played_count = 0
skipped_song_count = 0
total_seconds = 0
maxDate = "9999-12-31"
minDate = "1900-01-01"
overall_first_played = maxDate
overall_last_played = minDate
###Dictionaries to hold data
#{spotify_uri, [fullyPlayedCount, songEndedEarlyCount, firstPlayed, lastPlayed, timePlayed]}
songTemporalDict = {}
#{spotify_uri, [track_name,artist_name]}
songPermanentDict = {}
loopBroken = False
#Load song information from each file into the dictionaries/counters
for fileName in files:
    print("Processing " + fileName + "...")
    if(loopBroken == True):
        print("Error processing file, exiting")
        sys.exit()
    ###Change the line below iff path given isn't structured like C:\dir_a\dir_b\dir_c Where all the json files are stored in dir_c###
    cliF = open(path + "\\"+ fileName, "r", encoding="utf-8")
    ###                                           ###
    arr = json.load(cliF)
    
    for obj in arr:
        if not "master_metadata_album_artist_name" in obj or not "master_metadata_track_name" in obj or not "spotify_track_uri" in obj or not "reason_end" in obj or not "ms_played" in obj:
            loopBroken = True
            break
    
        if obj["master_metadata_track_name"] is None:
            null_song_count += 1
        else:
            try:
                objDate = obj["ts"][:10]
                if obj["spotify_track_uri"] in songTemporalDict:
                    songTemporal = songTemporalDict[obj["spotify_track_uri"]]
                else:
                    songTemporal = [0,0,maxDate,minDate, 0]
                    songPermanentDict.update({obj["spotify_track_uri"] : [obj["master_metadata_track_name"], obj["master_metadata_album_artist_name"]] })
                
                songTemporal[4] += obj["ms_played"]
                
                if obj["reason_end"] == "trackdone":
                    songTemporal[0] += 1
                else:
                    songTemporal[1] += 1

                if objDate < songTemporal[2]:
                    songTemporal[2] = objDate
                if objDate > songTemporal[3]:
                    songTemporal[3] = objDate

                songTemporalDict.update({obj["spotify_track_uri"] : songTemporal})
            except:
                loopBroken = True
                break
    cliF.close()

#Sort the dictionary by criteria given
if criteria <= 4:
    songTemporalDict = sorted(songTemporalDict.items(), key = lambda item: item[1][criteria], reverse = True)
else:
    songTemporalDict = sorted(songTemporalDict.items(), key = lambda item: item[1][0] + item[1][1], reverse = True)

if not comparisonFile is None:
    f = open(comparisonFile, "r")
    comparisonArr = json.load(f)
    f.close()

#Have to get totals before 
for songUri, temporalSongData in songTemporalDict:
    if criteria <= 4 and temporalSongData[criteria] < min or criteria == 5 and temporalSongData[0] + temporalSongData[1] < min :
        break
    if not comparisonArr is None and songUri in comparisonArr:
        continue
    if float(temporalSongData[0] / (temporalSongData[0] + temporalSongData[1])) > minRatio:
        total_played_count += temporalSongData[0]
        skipped_song_count += temporalSongData[1]
        total_seconds += temporalSongData[4]
        if temporalSongData[2] < overall_first_played:
            overall_first_played = temporalSongData[2]
        if temporalSongData[3] > overall_last_played:
            overall_last_played = temporalSongData[3]
            
f = open(outputfn, "a", encoding="utf-8", newline="")
#Use csv.writer to properly write output to file
csvWriter = csv.writer(f)
csvWriter.writerow(["Song name", "Artist", "Number of Times Completed", "Number of times ended early", "Total number of plays", "Total Minutes listened", "first_played", "last_played", "Spotify uri"])
csvWriter.writerow(["All", "Various", total_played_count, skipped_song_count, total_played_count + skipped_song_count, int(total_seconds / 60000), overall_first_played, overall_last_played, "Sorted by " + criteriaArg + " | Min needed: " + str(min) + " | Min ratio: " + str(minRatio) + " | Skipped: " + str(skipped_song_count)])
uriArray = []


for songUri, temporalSongData in songTemporalDict:
    if criteria <= 4 and temporalSongData[criteria] < min or criteria == 5 and temporalSongData[0] + temporalSongData[1] < min:
        break
    if not comparisonArr is None and songUri in comparisonArr:
        continue
    if float(temporalSongData[0] / (temporalSongData[0] + temporalSongData[1])) > minRatio:
        csvWriter.writerow([songPermanentDict[songUri][0], songPermanentDict[songUri][1], temporalSongData[0], temporalSongData[1], temporalSongData[0] + temporalSongData[1], int(temporalSongData[4] / 60000), temporalSongData[2], temporalSongData[3], songUri])
        uriArray.append(songUri)

f.close()

f = open("uri_only_" + ts + ".txt", "a")
json.dump(uriArray,f)
f.close()


print("Completed! Check Working Directory for output")