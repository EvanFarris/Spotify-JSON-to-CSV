import time
import sys
import json
import csv
import os
import pandas as pd

if len(sys.argv) == 1 or sys.argv[1] == "-help":
    print("\nFormat: python spotifyjsontocsv.py -dir <path to directory with spotify files> -minCount <number> -maxCount <number> -minRatio <0 <= float <= 1> -maxRatio <0 <= float <= 1 -ignoreFile <path>")
    print("\nPossible criteria: completion/ended_early/total/first_played/last_played/listen_time\n")
    print("\nRatio criteria: Shows songs you've completed more than the minimum percent of times\n")
    print("\nIf using first_played/last_played, date range is in the format 'YYYY-MM-DD'\n")
    sys.exit()
    
argCounter = 1
try:
    while argCounter + 1 < len(sys.argv):
        curArg = sys.argv[argCounter]
        match curArg:
            case "-dir":
                path = sys.argv[argCounter + 1]
            case "-sort":
                criteriaArg = sys.argv[argCounter + 1]
            case "-minCount":
                minCount = int(sys.argv[argCounter + 1])
            case "-maxCount":
                maxCount = int(sys.argv[argCounter + 1])
            case "-minRatio":
                minRatio = float(sys.argv[argCounter + 1])
            case "-maxRatio":
                maxRatio = float(sys.argv[argCounter + 1])
            case "-ignoreFile":
                comparisonFile = sys.argv[argCounter + 1]
            case _:
                print("Error in parsing command line arguments. Valid arguments: -dir -sort -minCount -maxCount -minRatio -maxRatio -ignoreFile")
                sys.exit()
        argCounter += 2
except:
    print("Error with one of the count or ratio fields. -minCount/-maxCount/-minRatio/-maxRatio must be a number.")
    

#We need at least a path specified to search for the input files
try:
    path
    #Grab all the json files in the directory given
    files = [f for f in os.listdir(path) if f.endswith(".json") and f.startswith("endsong_")]
except:
    print("No path specified")
    sys.exit()

#If no files found, exit.
if len(files) == 0:
    print("No files found in" + path)
    sys.exit()
#Initialize variables, give default values if value not entered.
try: minCount
except: minCount = 0
try: maxCount
except: maxCount = 9999999999
try: minRatio
except: minRatio = float(0)
try: maxRatio
except: maxRatio = float(1.0)
    
if minCount > maxCount:
    print("minCount is bigger than maxCount")
    sys.exit()
if minRatio > maxRatio:
    print("minRatio is bigger than maxRatio")
    sys.exit()

try: criteriaArg
except: criteriaArg = "total"
match criteriaArg:
    case "completion":
        criteria = 0
    case "ended_early":
        criteria = 1
    case "first_played":
        criteria = 2
    case "last_played":
        criteria = 3
    case "listen_time":
        criteria = 4
    case "total":
        criteria = 5
    case _:
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

#Fix path depending on os
if os.name == "nt":
    path += "\\"
elif os.name == "posix":
    path += "/"

#Load song information from each file into the dictionaries/counters
for fileName in files:
    if(loopBroken == True):
        print("Error processing file, exiting")
        sys.exit()
    print("Processing " + fileName + "...")

    try:
        cliF = open(path + fileName, "r", encoding="utf-8")
    except:
        print("Error opening file to read entries")
        sys.exit()

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

try: 
    comparisonFile
    f = open(comparisonFile, "r")
    comparisonArr = json.load(f)
    f.close()
except:
    comparisonArr = None
#Stackoverflow says you can't write specific rows using csv.writer without having to read the whole csv file and writing it out again.
#So we have to go through the dictionary early to get the aggregate data and write it at the top of the file. 
for songUri, temporalSongData in songTemporalDict:
    if criteria <= 4 and temporalSongData[criteria] < minCount or criteria == 5 and temporalSongData[0] + temporalSongData[1] < minCount:
        break
    if not comparisonArr is None and songUri in comparisonArr:
        continue
    ratio = float(temporalSongData[0] / (temporalSongData[0] + temporalSongData[1]))
    if ratio >= minRatio and ratio <= maxRatio and (criteria <= 4 and temporalSongData[criteria] <= maxCount or criteria == 5 and temporalSongData[0] + temporalSongData[1] <= maxCount):
        total_played_count += temporalSongData[0]
        skipped_song_count += temporalSongData[1]
        total_seconds += temporalSongData[4]
        if temporalSongData[2] < overall_first_played:
            overall_first_played = temporalSongData[2]
        if temporalSongData[3] > overall_last_played:
            overall_last_played = temporalSongData[3]
            
#Prep the output file with the headers
f = open(outputfn, "a", encoding="utf-8", newline="")
csvWriter = csv.writer(f)
csvWriter.writerow(["Song name", "Artist", "Number of Times Completed", "Number of times ended early", "Total number of plays", "Total Minutes listened", "first_played", "last_played", "Spotify uri"])
csvWriter.writerow(["All", "Various", total_played_count, skipped_song_count, total_played_count + skipped_song_count, int(total_seconds / 60000), overall_first_played, overall_last_played, "Sorted by " + criteriaArg + " | " + str(minCount) +" <= count <=" + str(maxCount) + " | " + str(minRatio) + " <= ratio <= "+ str(maxRatio) + " | Null song entries: " + str(null_song_count)])
#Array to hold all the spotify uris to output
uriArray = []

#Write all eligible songs to the file, and append spotify links to the array.
for songUri, temporalSongData in songTemporalDict:
    if criteria <= 4 and temporalSongData[criteria] < minCount or criteria == 5 and temporalSongData[0] + temporalSongData[1] < minCount:
        break
    if not comparisonArr is None and songUri in comparisonArr:
        continue
    ratio = float(temporalSongData[0] / (temporalSongData[0] + temporalSongData[1]))
    if ratio >= minRatio and ratio <= maxRatio and (criteria <= 4 and temporalSongData[criteria] <= maxCount or criteria == 5 and temporalSongData[0] + temporalSongData[1] <= maxCount):
        csvWriter.writerow([songPermanentDict[songUri][0], songPermanentDict[songUri][1], temporalSongData[0], temporalSongData[1], temporalSongData[0] + temporalSongData[1], int(temporalSongData[4] / 60000), temporalSongData[2], temporalSongData[3], songUri])
        uriArray.append(songUri)

f.close()

#Write array of spotify uris to new file.
f = open("uri_only_" + ts + ".txt", "a")
json.dump(uriArray,f)
f.close()

print("Completed! Check Working Directory for output")