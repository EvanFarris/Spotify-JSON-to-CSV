import time
import sys
import json
import csv
import os

if len(sys.argv) == 1:
    sys.exit()

#Grab all the json files in the directory given, if none, exit
path = sys.argv[1]
files = [f for f in os.listdir(path) if f.endswith(".json") and f.startswith("endsong_")]
if len(files) == 0:
    sys.exit()

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
#{spotify_url, [fullyPlayedCount, songEndedEarlyCount, firstPlayed, lastPlayed, timePlayed]}
songTemporalDict = {}
#{spotify_url, [track_name,artist_name]}
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
                total_seconds += obj["ms_played"]
                
                if obj["reason_end"] == "trackdone":
                    songTemporal[0] += 1
                    total_played_count += 1
                else:
                    songTemporal[1] += 1
                    skipped_song_count += 1
                
                if objDate < songTemporal[2]:
                    songTemporal[2] = objDate
                    if objDate < overall_first_played:
                        overall_first_played = objDate
                if objDate > songTemporal[3]:
                    songTemporal[3] = objDate
                    if objDate > overall_last_played:
                        overall_last_played = objDate

                songTemporalDict.update({obj["spotify_track_uri"] : songTemporal})
            except:
                loopBroken = True
                break
    cliF.close()

#Sort the dictionary by the total songs completed column in descending order
songTemporalDict = sorted(songTemporalDict.items(), key = lambda item: item[1][0], reverse = True)
f = open(outputfn, "a", encoding="utf-8", newline="")
#Use csv.writer to properly write output to file
csvWriter = csv.writer(f)
csvWriter.writerow(["Song name", "Artist", "Number of Times Completed", "Number of times ended early", "Total number of plays", "Total Minutes listened", "first_played", "last_played", "Spotify uri"])
csvWriter.writerow(["All", "Various", total_played_count, skipped_song_count, total_played_count + skipped_song_count + null_song_count, int(total_seconds / 60000), overall_first_played, overall_last_played, "n/a"])
for songUri, temporalSongData in songTemporalDict:
    csvWriter.writerow([songPermanentDict[songUri][0], songPermanentDict[songUri][1], temporalSongData[0], temporalSongData[1], temporalSongData[0] + temporalSongData[1], int(temporalSongData[4] / 60000), temporalSongData[2], temporalSongData[3], songUri])
f.close()

print("Completed! Check Working Directory for output")