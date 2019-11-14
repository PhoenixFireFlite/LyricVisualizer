import requests
import re
import string
import time
import numpy as np
import matplotlib.pyplot as plt
import json

geniusIdUrl = 'http://www.genius.com/songs/'
geniusNameUrl = 'https://genius.com/'
geniusSongSearchUrl = 'https://genius.com/api/search/song?page=1&q={0}'

# You might need to run "pip install Pillow" for saving to work!

def getSongByInteractiveQuery(query):
    rawJson = requests.get(geniusSongSearchUrl.format(str(query).replace(' ','+'))).content
    parsedJson = json.loads(rawJson)
    apiHits = parsedJson['response']['sections'][0]['hits']

    if len(apiHits) == 0:
        print('No songs found using query: "{}"'.format(query))
        return None

    print('Found the following song matches for "{0}":'.format(query))
    i = 0
    for x in apiHits:
        print('  {0}: {1}'.format(str(i), x['result']['full_title']))
        i += 1

    maxIndex = i - 1

    inputChoice = int(input('Which song would you like to visualize? '))
    correctedChoiceIndex = min(maxIndex, inputChoice)

    return int(apiHits[correctedChoiceIndex]['result']['id']), apiHits[correctedChoiceIndex]['result']['full_title']

def getSongIdByQuery(query, choiceIndex):
    rawJson = requests.get('https://genius.com/api/search/song?page=1&q={0}'.format(str(query).replace(' ','+'))).content
    parsedJson = json.loads(rawJson)
    apiHits = parsedJson['response']['sections'][0]['hits']

    if len(apiHits) == 0:
        print('No songs found using query: "{}"'.format(query))
        return None

    print('Found the following song matches for "{0}":'.format(query))
    i = 0
    for x in apiHits:
        print('  {0}: {1}'.format(str(i), x['result']['full_title']))
        i += 1

    maxIndex = i-1
    correctedChoiceIndex = min(maxIndex,choiceIndex)

    print('Choosing song {0}: {1}'.format(correctedChoiceIndex, apiHits[correctedChoiceIndex]['result']['full_title']))

    return int(apiHits[correctedChoiceIndex]['result']['id'])

def getLyricsByQuery(query):
    return getLyrics(getSongIdByQuery(query))

def getLyrics(apiId):
    songUrl = geniusIdUrl + str(apiId)
    response = None
    tries = 0
    while response is None:
        try:
            response = requests.get(songUrl)
        except Exception as x:
            time.sleep(2)
            tries += 1
            print('Retrying: ' + str(tries), flush=True)

    if response.status_code != 200:
        return None

    content = response.content

    unprocessed_lyrics = str(re.findall(r'<div class=\"lyrics\">.*?<p>(.*?)</p>', str(content))[0])
    unprocessed_lyrics = re.sub(r'(<a.*?href=.*?>)', '', unprocessed_lyrics)
    unprocessed_lyrics = re.sub(r'(\[Verse.*?\])', '', unprocessed_lyrics)
    unprocessed_lyrics = re.sub(r'(\[Intro.*?\])', '', unprocessed_lyrics)
    unprocessed_lyrics = re.sub(r'(\[Hook.*?\])', '', unprocessed_lyrics)
    unprocessed_lyrics = re.sub(r'(\[Chorus.*?\])', '', unprocessed_lyrics)
    unprocessed_lyrics = re.sub(r'(\[Pre.*?\])', '', unprocessed_lyrics)
    unprocessed_lyrics = re.sub(r'(\[Outro.*?\])', '', unprocessed_lyrics)
    unprocessed_lyrics = re.sub(r'<.*?>', '', unprocessed_lyrics)
    unprocessed_lyrics = re.sub(r'\(.*?\)', '', unprocessed_lyrics) # optional: can be cool if removed
    unprocessed_lyrics = unprocessed_lyrics.replace('\\n\\n', ' ').replace('\\n', ' ').replace('</a>', '').replace(
        '\\\'', '\'').strip()
    unprocessed_lyrics = re.sub(r'( +)', ' ', unprocessed_lyrics)

    return unprocessed_lyrics

def getLyricMatrixByQuery(query, choiceIndex):
    return getLyricMatrix(getSongIdByQuery(query, choiceIndex))

def getLyricMatrix(apiId, removeSingleWordRepeats=True):
    lyrics = getLyrics(apiId)
    if lyrics is None:
        return

    lyrics = lyrics.lower()
    lyrics = (re.compile('[%s]' % re.escape(string.punctuation))).sub('', lyrics)
    lyrics = lyrics.split(' ')

    lyricLength = len(lyrics)
    lyricMap = []

    index = 0
    usedWords = {}

    for word in lyrics:
        if word in usedWords:
            wordIndex = usedWords[word]
        else:
            index += 1
            wordIndex = index
            usedWords[word] = index

        lyricMap.append(wordIndex)

    mat = np.zeros((lyricLength, lyricLength))

    for x in range(lyricLength):
        for y in range(lyricLength):
            if lyricMap[x] == lyricMap[y]:
                mat[x][y] = lyricMap[x]

    if removeSingleWordRepeats:
        for x in range(lyricLength):
            for y in range(lyricLength):
                if mat[x][y] != 0:
                    if x > 0 and y > 0 and mat[x - 1][y - 1] == 0 and \
                            ((x < lyricLength - 1 and y < lyricLength - 1 and mat[x + 1][y + 1] == 0) or
                             (x == lyricLength - 1 and (x == lyricLength - 1 or y == lyricLength - 1))):
                        mat[x][y] = 0

    return mat

def slugify(value):
    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf-8')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    value = re.sub('[-\s]+', '-', value)

    return value

def saveLyricMatrix(lyricMatrix, cmap=plt.cm.hsv, backgroundColor='#181718', saveName='tempSave.png'):
    if lyricMatrix is None: return

    npArray = lyricMatrix
    lyricLength = len(lyricMatrix)
    plt.xlim([0, lyricLength])
    plt.ylim([0, lyricLength])
    cmap.set_under(color=backgroundColor)
    # plt.imshow(npArray, cmap=cmap, vmin=0.1)
    plt.imsave(saveName, np.rot90(npArray), cmap=cmap, vmin=0.0000001)
    print('File saved as {}'.format(saveName))
    # plt.show()


removeSingleWordRepeats = True

if __name__ == "__main__":
    while True:
        queryInput = input('\nInput a query for your song choice: ')
        songId, songName = getSongByInteractiveQuery(queryInput)
        if songId is None: continue
        lyricMatrix = getLyricMatrix(songId, removeSingleWordRepeats)
        fileName = "lyricMatrices/"+slugify(songName)+('_RSWR' if removeSingleWordRepeats else '')+".png"
        saveLyricMatrix(lyricMatrix, cmap=plt.cm.hsv, backgroundColor='#181818', saveName=fileName)

