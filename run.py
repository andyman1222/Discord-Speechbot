import discord
import json
import traceback
from discord.ext import commands
import re
import random
from random import randint
import os
import string
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import ctypes, sys
from threading import Thread
import threading
from socketserver import ThreadingMixIn
import socket
import copy

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


sys.setrecursionlimit(2000)
intents = discord.Intents(messages=True, members=True, guilds=True)
bot = commands.Bot(command_prefix='$',intents=intents)

fileLock = threading.Lock()
dataLock = threading.Lock()

graphsG = {}

authorsG = {}

authorG = {}

letterGraphsG = {}

wordGraphG = {}

fileName = "graph.json"
fileAuthors = "authors.json"
lettersName = "lettersGraph.json"

#http server

serverPort = 12222

class Handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        try:
            query = urlparse(self.path).query
            query_components = dict(qc.split("=") for qc in query.split("&"))
            g = query_components["guild_id"]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("<html><head><title>Bot add success</title></head>", "utf-8"))
            #self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
            self.wfile.write(bytes("<body>", "utf-8"))
            self.wfile.write(bytes("<p>The bot was added to your server.</p>", "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))
            #print("New server joining: ", g)
            #too lazy to figure out httpserver printing
        except:
            #print("Invalid GET")
            pass
        #sys.stdout.flush()

#loads the word and letter graphs from file
def loadFile():
    global graphsG
    global letterGraphsG
    global fileLock
    global dataLock
    #dataLock.acquire()
    fileLock.acquire()
    try:
        saveFile = open(fileName, "r")
        saveFileW = open(lettersName, "r")
        authorSaveFile = open(fileAuthors, "r")
    except:
        saveFile = open(fileName, "w+")
        saveFileW = open(lettersName, "w+")
        authorSaveFile = open(fileAuthors, "w+")
    try:
        graphsG = json.load(saveFile)
        letterGraphsG = json.load(saveFileW)
        authorsG = json.load(authorSaveFile)
    except Exception as e:
        print(e)
        print("Using previous graps!")
        #graphsG = {}
        #letterGraphsG = {}
    saveFile.close()
    saveFileW.close()
    #dataLock.release()
    fileLock.release()

#save all 3 graphs and update the global graphs
#releases lock
def saveFile(guild, graph, letterGraph, author):
    global graphsG
    global authorsG
    global letterGraphsG
    global fileLock
    global dataLock

    loadFile()

    #dataLock.acquire()
    fileLock.acquire()

    graphsG[guild] = graph
    authorsG[guild] = author
    letterGraphsG[guild] = letterGraph

    saveFile = open(fileName, "w")
    authorSaveFile = open(fileAuthors, "w")
    saveFileW = open(lettersName, "w")

    json.dump(graphsG, saveFile)
    json.dump(authorsG, authorSaveFile)
    json.dump(letterGraphsG, saveFileW)

    saveFile.truncate()
    saveFile.close()
    authorSaveFile.truncate()
    authorSaveFile.close()
    saveFileW.truncate()
    saveFileW.close()
    
    fileLock.release()
    #dataLock.release()

#Create a deep copy of the global graphs for the specified message
#acquires lock
def generateGraph(message):
    loadFile()
    global graphsG
    global authorsG
    #G
    global letterGraphsG
    global dataLock
    _id=hex(message.channel.guild.id)
  
    dataLock.acquire()
    if(_id not in graphsG):
        graphsG[_id] = {}
        graph = graphsG[_id]
        graph['L'] = {}
        graph['L']['M'] = []
        graph['L']['C'] = []
        graph['L']['S'] = ""
        graph['C'] = []
        graph['W'] = {}
    graph = graphsG[_id]
        
    if(_id not in letterGraphsG):
        letterGraphsG[_id] = {}
    letterGraph = letterGraphsG[_id]
        

    if(_id not in authorsG):
        authorsG[_id] = {}
    author = authorsG[_id]
    

    if("null" in graph.keys()):
        graph[None] = graph['W']["null"].copy()
        del graph['W']["null"]
        if not "\n" in graph[None].keys():
            graph[None]["\n"] = []

    if("null" in letterGraph.keys()):
        letterGraph[None] = letterGraph["null"].copy()
        del letterGraph["null"]
        if not "\n" in letterGraph[None].keys():
            letterGraph[None]["\n"] = []

    r = (graph, letterGraph, author)
    #dataLock.release()
    return r

#saves a new word into a letter graph
#word: word to save
#graph: letter graph to save word to
#returns: graph, with word added appropriately
#important: does not acquire dataLock (uses only local vars)
def saveWord(word, graph):
    wordL = re.sub('[^A-Za-z]', '', word).lower()
    wordL = wordL + ' ;'
    if len(wordL) == 0:
        return
    prevLtr = None
    ltr = wordL[0]
    #print(wordL)
    if not 'W' in graph:
        graph['W'] = {}
    i = 0
    while i < len(wordL) - 1:
        if i != 0:
            if wordL[i-1] != ";":
                prevLtr = wordL[i-1]
            else:
                prevLtr = ""
            if not prevLtr in graph['W']:
                graph['W'][prevLtr] = {}
            targetGraphW = graph['W'][prevLtr]
        else:
            if not "" in graph['W']:
                graph['W'][""] = {}
            targetGraphW = graph['W'][""]
        if not ltr in targetGraphW:
            targetGraphW[ltr] = {}
            targetGraphW[ltr]['X'] = {}
            targetGraphW[ltr]['W'] = 0
        targetGraphW[ltr]['W'] = targetGraphW[ltr]['W']+1

        if (wordL[i+1] != ";" and wordL[i+1] in targetGraphW[ltr]):
            targetGraphW[ltr]['X'][wordL[i + 1]]['W'] = targetGraphW[ltr]['X'][wordL[i + 1]]['W'] + 1
        elif (wordL[i+1] == ";" and "" in targetGraphW[ltr]):
            targetGraphW[ltr]['X'][""]['W'] = targetGraphW[ltr]['X'][""]['W'] + 1
        elif(wordL[i + 1] in targetGraphW[ltr]):
            targetGraphW[ltr]['X'][wordL[i + 1]]['W'] = targetGraphW[ltr]['X'][wordL[i + 1]]['W'] + 1

        elif prevLtr != " ":

            if wordL[i+1] != ";":
                targetGraphW[ltr]['X'][wordL[i + 1]] = {}
                targetGraphW[ltr]['X'][wordL[i + 1]]['W'] = 1
            else:
                targetGraphW[ltr]['X'][""] = {}
                targetGraphW[ltr]['X'][""]['W'] = 1

        i = i + 1
        if wordL[i] != ";":
            ltr = wordL[i]
        else:
            ltr = ""
    return graph

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(activity=discord.Streaming(url="http://quantonium.net", name="" + str(os.path.getsize('graph.json')) + " bytes of sentence data"))

commandsList = ["$help", "$speak", "$randomspeak", "$randomspeaknonsense", "$speaknonsense", "$clear", "$check", "$sentencesearch", "$wordcount", "$channelstats", "$userstats", "$generateword", "$generatenonsenseword", "$randomword", "$randomnonsenseword"]

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    graphData = generateGraph(message)
    graph = graphData[0]
    wordGraph = graphData[1]
    author = graphData[2]

    channelId = hex(message.channel.id)
    authorId = hex(message.author.id)
    msgId = hex(message.id)
    guildId = hex(message.guild.id)

    i = 0

    # removed anything that would be surrounding bodies of text, as this would complicate things later. Note: didn't remove *, _, ||, or <> to either make things more interesting
    words = message.clean_content.replace('\n', " \n ").replace("! ", "! \n ").replace(
        "? ", "? \n ").replace("; ", "; \n ").replace('\"', " \" ").split(' ')
    l = len(words) - 1
    while i < l:
        if not (words[i] is None):
            if words[i].lower() == '\n':
                words.insert(i+1, None)
            # street addresses should be included but theres so many abbreviations i didnt bother
            elif (words[i].lower().endswith('.')) and (not any(ext in words[i].lower() for ext in {"mr.", "ms.", "mrs." "e.g.", "cf.", "i.e.", "v.", "viz.", "etc.", "sc.", 'al.', "ca."})):
                words.insert(i+1, '\n')
        i = i+1
        l = len(words) - 1
    word = None
    words.append("\n")
    words.append(None)
    if(words[0] != None):
        word = words[0].lower()
    if word != None and not word in commandsList:
        if (not authorId in author):
            author[authorId] = {}
            author[authorId]['C'] = 0
        if(not channelId in author[authorId]):
            author[authorId][channelId] = 0
        author[authorId]['C'] += 1
        author[authorId][channelId] += 1

        if(not channelId in graph['C']):
            graph['C'].append(channelId)
        index = graph['C'].index(channelId)

        i = 0
        prevWord = ""
        while i < len(words) - 1:
            saveWord(word, wordGraph)
            if i != 0:
                if words[i-1] != None:
                    prevWord = words[i-1].lower()
                else:
                    prevWord = ""
                if not prevWord in graph['W']:
                    graph['W'][prevWord] = {}
                targetGraph = graph['W'][prevWord]
            else:
                if not "" in graph['W']:
                    graph['W'][""] = {}
                targetGraph = graph['W'][""]
            if not word in targetGraph:
                targetGraph[word] = {}
                targetGraph[word]['X'] = {}
                targetGraph[word]['W'] = 0
            targetGraph[word]['W'] = targetGraph[word]['W']+1

            if (words[i+1] != None and words[i+1].lower() in targetGraph[word]):
                targetGraph[word]['X'][words[i + 1].lower()]['C'] = index
                targetGraph[word]['X'][words[i + 1].lower()]['M'] = msgId
                targetGraph[word]['X'][words[i + 1].lower()]['W'] = targetGraph[word]['X'][words[i + 1].lower()]['W'] + 1
            elif (words[i+1] == None and "" in targetGraph[word]):
                targetGraph[word]['X'][""]['C'] = index
                targetGraph[word]['X'][""]['M'] = msgId
                targetGraph[word]['X'][""]['W'] = targetGraph[word]['X'][""]['W'] + 1
            elif(words[i + 1] in targetGraph[word]):
                targetGraph[word]['X'][words[i + 1]]['C'] = index
                targetGraph[word]['X'][words[i + 1]]['M'] = msgId
                targetGraph[word]['X'][words[i + 1]]['W'] = targetGraph[word]['X'][words[i + 1]]['W'] + 1

            elif prevWord != "\n":

                if words[i+1] != None:
                    targetGraph[word]['X'][words[i + 1].lower()] = {}
                    targetGraph[word]['X'][words[i + 1].lower()]['W'] = 1
                    targetGraph[word]['X'][words[i + 1].lower()]['C'] = index
                    targetGraph[word]['X'][words[i + 1].lower()]['M'] = msgId
                else:
                    targetGraph[word]['X'][""] = {}
                    targetGraph[word]['X'][""]['W'] = 1
                    targetGraph[word]['X'][""]['C'] = index
                    targetGraph[word]['X'][""]['M'] = msgId

            i = i + 1
            if words[i] != None:
                word = words[i].lower()
            else:
                word = ""
        saveFile(guildId, graph, wordGraph, author)
    dataLock.release()
    await bot.change_presence(activity=discord.Streaming(url="http://quantonium.net", name="" + str(os.path.getsize('graph.json')) + " bytes of sentence data"))
    await bot.process_commands(message)


@bot.command(pass_context=True)
async def clear(ctx, *args):
    if not ctx.message.author.permissions_in(ctx.guild.id).administrator:
        await ctx.send("You don't have permission to do this.")
    else:
        graphData = generateGraph(ctx.message)
        graph = graphData[0]
        wordGraph = graphData[1]
        author = graphData[2]

        saveFile(hex(ctx.guild.id), graph, wordGraph, author)
        await ctx.send("Memory on this server has been cleared!")

maxLength = 50

bot.remove_command("help")
@bot.command(pass_context=True)
async def help(ctx, *args):
    await ctx.send(".\nI'm a speech bot that tries to learn to speak based on messages in your channel!" + 
        "\n\nTell me to speak: `$speak <word>`\nRandomly speak: `$randomspeak [min length]`\nCheck if you can use a word: `$check <word>`" + 
        "\nTell me to speak without coherency: `$speaknonsense <word>`\nTell me DIY: `$randomspeaknonsense [min length]`\n" + 
        "See the roots of my logic: `$sentencesearch`\nClear my memory (admins only): `$clear`\n\n" + 
        "**NEW!!**\nGenerate a random word: `$generateword <letter(s)>  [min length]`\nGenerate a random word, starting with any letter: `$randomword [min length]`\n" + 
        "Generate a random word that makes less sense: `$generatenonsenseword <letter(s)>  [length]` or `$randomnonsenseword [min length]`\n\n**Extra/Coming Soon(tm):**" + 
        "\n ~~See stats for the server: `$serverstats <max count>`~~\n~~See stats for user(s): `$userstats <user 1> <user 2>...`~~" + 
        "\n~~See stats per channel(s): `$channelstats <channel 1> <channel 2>...`~~")


maxSentence = 100


class WordDoesntExist(Exception):
    """Unknown word"""
    pass


class badWordChar(Exception):
    """Unknown word"""
    pass

class badLength(Exception):
    """bad length"""
    pass


# one check to find a weighted value for next word.

maxMessageLength = 2000 #discord's text limit

def findWeightedValue(prevKey, key, graph, origMsg, saveSentence = True, graphMetadata = True, dividingStr = " ", length=0):
    #print(prevKey)
    #print(key)
    #print()

    if key == "":
        return ""
    # if key not in graph, check other prevKey for the same value before terminating, only  if prevKey is None (or "null" in file). This means that it can start from anywhere if only given one word.
    if prevKey == "" or prevKey == None:
        #print("Choosing a random key")
        randomList = []
        for x in graph['W'].keys():
            #print(x)
            if str(key).lower() in graph['W'][x]:
                randomList.append(x)
        if len(randomList) == 0:
            return ""
        else:
            #print("Choosing a random start point")
            index = randint(0, len(randomList)-1)
            values = graph['W'][randomList[index]][str(key).lower()]
    # if prevKey not in graph, terminate. This only happens if the graph has been set up improperly, or the bot has never seen such a combo with 2 words
    elif not str(prevKey).lower() in graph['W']:
        #print("prevKey doesn't exist! Either I never saw this word, or something else went wrong")
        raise WordDoesntExist
    elif str(key).lower() in graph['W'][str(prevKey).lower()]:
        #print("Continuing the sentence...")
        values = graph['W'][str(prevKey).lower()][str(key).lower()]
    else:
        return ""

    totalWeight = 0
    valuesToChooseFrom = []
    valueBounds = []
    valueChannel = []
    valueSentence = []
    for val in values['X']:
        valuesToChooseFrom.append(val)
        totalWeight = totalWeight + values['X'][val]['W']
        valueBounds.append(totalWeight)
        if graphMetadata:
            valueSentence.append(int(values['X'][val]['M'],16))
            valueChannel.append(int(graph['C'][values['X'][val]['C']],16))

    if totalWeight != 0:
        totalWeight = randint(0, totalWeight)
        i = 0
        while(valueBounds[i] < totalWeight and i < len(valueBounds)):
            i += 1
        if valuesToChooseFrom[i] != "" and saveSentence:
            graph['L']['S'] = graph['L']['S'] + dividingStr + valuesToChooseFrom[i]
            graph['L']['M'].append(valueSentence[i])
            graph['L']['C'].append(valueChannel[i])
        if length + len(valuesToChooseFrom[i] + dividingStr) > maxMessageLength:
            return ""
        return valuesToChooseFrom[i] + dividingStr + findWeightedValue(key, valuesToChooseFrom[i], graph, origMsg, saveSentence, graphMetadata, dividingStr, length + len(valuesToChooseFrom[i] + dividingStr))

    return ""

# only one iteration to find weighted value, for less coherency


def findWeightedValue2(key, graph, origMsg, saveSentence = True, graphMetadata = True, dividingStr = " ", length=0):
    #print(key)
    #print()

    if key == "" or key == None:
        return ""
    # if key not in graph, check other prevKey for the same value before terminating, only  if prevKey is None (or "null" in file). This means that it can start from anywhere if only given one word.
    randomList = []
    for x in graph['W'].keys():
        if str(key).lower() in graph['W'][x]:
            randomList.append(x)
    if len(randomList) == 0:
        return ""
    else:
        #print("Choosing a random start point")
        index = randint(0, len(randomList)-1)
        values = graph['W'][randomList[index]][str(key).lower()]

    totalWeight = 0
    valuesToChooseFrom = []
    valueBounds = []
    valueChannel = []
    valueSentence = []
    for val in values['X']:
        valuesToChooseFrom.append(val)
        totalWeight = totalWeight + values['X'][val]['W']
        valueBounds.append(totalWeight)
        if graphMetadata:
            valueSentence.append(int(values['X'][val]['M'],16))
            valueChannel.append(int(graph['C'][values['X'][val]['C']],16))

    if totalWeight != 0:
        totalWeight = randint(0, totalWeight)
        i = 0
        while(valueBounds[i] < totalWeight and i < len(valueBounds)):
            i += 1
        if valuesToChooseFrom[i] != ""  and saveSentence:
            graph['L']['S'] = graph['L']['S'] + dividingStr + valuesToChooseFrom[i]
            graph['L']['M'].append(valueSentence[i])
            graph['L']['C'].append(valueChannel[i])
            
        if length + len(valuesToChooseFrom[i] + dividingStr) > maxMessageLength:
            return ""
        return valuesToChooseFrom[i] + dividingStr + findWeightedValue2(valuesToChooseFrom[i], graph, origMsg, saveSentence, graphMetadata, dividingStr, length + len(valuesToChooseFrom[i] + dividingStr))

    return ""


@bot.command(pass_context=True)
async def speak(ctx, *args):
    if len(args) == 0:
        await ctx.send("Usage: $speak <words>")
        return
    graphData = generateGraph(ctx)
    graph = graphData[0]
    wordGraph = graphData[1]
    author = graphData[2]
    graph['L']['S'] = ""
    graph['L']['M'].clear()
    graph['L']['C'].clear()
    start = args[len(args)-1]
    prevWord = None
    await ctx.send("Making sentence, please wait...")
    try:
        sentence = ""
        i = 0
        while i < len(args)-1:
            sentence += args[i] + " "
            prevWord = args[i]
            i += 1
        sentence = sentence + start + " " + findWeightedValue(prevWord, start, graph, ctx, True, True, " ", len(sentence + start + " "))
        graph['L']['S'] = sentence.replace("\n", "")
        if len(sentence.replace("\n", "")) == 0:
            raise WordDoesntExist
        saveFile(hex(ctx.guild.id), graph, wordGraph, author)
        await ctx.send(sentence.replace("\n", ""))
    except WordDoesntExist:
        await ctx.send("Gee... I've never heard of that word or combination of words before.\n(I look back 2 words in order to make my sentences the most gramatically correct as possible, so I might not know how to continue off your sentence.)")
        
    except badWordChar:
        await ctx.send("Gee... I get upset with the word \"null\" and escape characters, or I just got confused some other way.\n(If you want to start with nothing, use $randomspeak.)")
        
    except Exception as e:
        await ctx.send("Something else went wrong, try again.")
        print(e)
        
    finally:
        dataLock.release()


@bot.command(pass_context=True)
async def check(ctx, *args):
    if len(args) == 0:
        await ctx.send("Usage: $check <word>")
        return
    graphData = generateGraph(ctx)
    graph = graphData[0]
    wordGraph = graphData[1]
    author = graphData[2]
    start = args[len(args)-1]
    prevWord = None
    await ctx.send("Checking, please wait...")
    try:
        sentence = ""
        i = 0
        while i < len(args)-1:
            sentence += args[i] + " "
            prevWord = args[i]
            i += 1
        argsString = sentence + args[i]
        sentence = sentence + " " + start + " " + findWeightedValue(prevWord, start, graph, ctx, False, False, " ", len(sentence + start + " "))
        if len(sentence.replace("\n", "")) == 0:
            raise WordDoesntExist
        await ctx.send("I have seen that word/combination of words! Feel free to use it with `$speak " + argsString + "`.")
    except WordDoesntExist:
        await ctx.send("Gee... I've never heard of that word or combination of words before.\n(I look back 2 words in order to make my sentences the most gramatically correct as possible, so I might not know how to continue off your sentence.)")
        
    except badWordChar:
        await ctx.send("Gee... I get upset with the word \"null\" and escape characters, or I just got confused some other way.\n(If you want to start with nothing, use $randomspeak.)")
        
    except Exception as e:
        await ctx.send("Something else went wrong, try again.")
        print(e)
        
    finally:
        dataLock.release()

@bot.command(pass_context=True)
async def wordcount(ctx, *args):
    if len(args) == 0:
        await ctx.send("Usage: $wordcount <word>")
        return
    graphData = generateGraph(ctx)
    graph = graphData[0]
    wordGraph = graphData[1]
    author = graphData[2]
    start = args[len(args)-1]
    await ctx.send("Checking, please wait...")
    if start in graph:
        c = 0
        for w in graph[start]:
            c+=graph[start][w]['W']
        await ctx.send("The word " + start + " has been used `" + str(c) + "` times.")
    else:    
        await ctx.send("Gee... I've never heard of that word before.")
    dataLock.release()

@bot.command(pass_context=True)
async def randomspeak(ctx, *args):
    loops = -1
    if len(args) != 0:
        loops = int(args[0])
        if not loops > 0:
            loops = -1
    graphData = generateGraph(ctx)
    graph = graphData[0]
    wordGraph = graphData[1]
    author = graphData[2]
    graph['L']['S'] = ""
    graph['L']['M'].clear()
    graph['L']['C'].clear()
    await ctx.send("Making sentence, please wait...")
    try:
        if int(loops) > maxLength:
            raise badLength
        sentence = ""
        while True:
            randomList = []
            for x in graph['W'][""].keys():
                randomList.append(x)
            index = randint(0, len(randomList)-1)
            nextword = randomList[index]
            sentence = sentence + " " + nextword + " " + findWeightedValue(None, nextword, graph, ctx, True, True, " ", len(sentence +" " + nextword + " "))
            if(len(sentence.replace(" ", '')) > 0):
                while(sentence[-1] == ' ' or sentence[-1] == '.'):
                    sentence = sentence[:-1]
                sentence = sentence + "."
                if len(sentence.split(' ')) > loops:
                    break
        graph['L']['S'] = sentence.replace("\n", "")
        saveFile(hex(ctx.guild.id), graph, wordGraph, author)
        await ctx.send(sentence.replace("\n", ""))
    except WordDoesntExist:
        await ctx.send("Gee... something's wrong. I can't seem to find my own words!")
        
    except badWordChar:
        await ctx.send("Gee... I'm stumbling upon \"null\" and escape characters, or I just got confused some other way!")
        
    except badLength:
        await ctx.send("Length cannot exceed " + str(maxLength) + "!")
    except Exception as e:
        await ctx.send("Something else went wrong, try again.")
        print(e)
        
    finally:
        dataLock.release()


@bot.command(pass_context=True)
async def speaknonsense(ctx, *args):
    if len(args) == 0:
        await ctx.send("Usage: $speaknonsense <word>")
        return
    graphData = generateGraph(ctx)
    graph = graphData[0]
    wordGraph = graphData[1]
    author = graphData[2]
    graph['L']['S'] = ""
    graph['L']['M'].clear()
    graph['L']['C'].clear()
    start = args[len(args)-1]
    await ctx.send("Making sentence, please wait...")
    try:
        sentence = ""
        i = 0
        while i < len(args)-1:
            sentence += args[i] + " "
            i += 1
        sentence = sentence + start + " " + findWeightedValue2(start, graph, ctx, True, True, " ", len(sentence + start + " "))
        if len(sentence.replace("\n", "")) == 0:
            raise WordDoesntExist
        graph['L']['S'] = sentence.replace("\n", "")
        saveFile(hex(ctx.guild.id), graph, wordGraph, author)
        await ctx.send(sentence.replace("\n", ""))
    except WordDoesntExist:
        await ctx.send("Gee... I've never heard of that word or combination of words before.\n(I look back 2 words in order to make my sentences the most gramatically correct as possible, so I might not know how to continue off your sentence.)")
        
    except badWordChar:
        await ctx.send("Gee... I get upset with the word \"null\" and escape characters, or I just got confused some other way.\n(If you want to start with nothing, use $randomspeak.)")
        
    except Exception as e:
        await ctx.send("Something else went wrong, try again.")
        print(e)
        
    finally:
        dataLock.release()


@bot.command(pass_context=True)
async def randomspeaknonsense(ctx, *args):
    loops = -1
    if len(args) != 0:
        loops = int(args[0])
        if not loops > 0:
            loops = -1
    graphData = generateGraph(ctx)
    graph = graphData[0]
    wordGraph = graphData[1]
    author = graphData[2]
    graph['L']['S'] = ""
    graph['L']['M'].clear()
    graph['L']['C'].clear()
    await ctx.send("Making sentence, please wait...")
    try:
        if int(loops) > maxLength:
            raise badLength
        sentence = ""
        while True:
            randomList = []
            for x in graph['W'][""].keys():
                randomList.append(x)
            index = randint(0, len(randomList)-1)
            nextword = randomList[index]
            sentence = sentence + " " + nextword + " " + findWeightedValue2(nextword, graph, ctx, True, True, " ", len(sentence + " " + nextword + " "))
            if(len(sentence.replace(" ", '')) > 0):
                while(sentence[-1] == ' '):
                    sentence = sentence[:-1]
                sentence = sentence + "."
                #print("currnet sentence: " + sentence)
                if len(sentence.split(' ')) > loops:
                    break
        graph['L']['S'] = sentence.replace("\n", "")
        saveFile(hex(ctx.guild.id), graph, wordGraph, author)
        await ctx.send(sentence.replace("\n", ""))
    except WordDoesntExist:
        await ctx.send("Gee... something's wrong. I can't seem to find my own words!")
        
    except badWordChar:
        await ctx.send("Gee... I'm stumbling upon \"null\" and escape characters, or I just got confused some other way!")
        
    except badLength:
        await ctx.send("Length cannot exceed " + str(maxLength) + "!")
    except Exception as e:
        await ctx.send("Something else went wrong, try again.")
        print(e)
    finally:
        dataLock.release()
        


@bot.command(pass_context=True)
async def sentencesearch(ctx, *args):
    graphData = generateGraph(ctx)
    graph = graphData[0]
    wordGraph = graphData[1]
    author = graphData[2]
    await ctx.send("Finding sources for the sentence `" + graph['L']['S'] + "`...")
    madeSen = graph['L']['S'].split(" ")
    out = ""
    i = 0
    prevMsg = -1
    prevChannel = -1
    channels = graph['L']['C']
    messages = graph['L']['M']
    finalOut = ""
    tmp = set()
    for index in channels:
        channel = channels[i]
        message = messages[i]
        try:
            currentSen = await ctx.message.guild.get_channel(channel).fetch_message(message)
            out = currentSen.clean_content.replace("\n", "\n> ")
            if(index not in tmp):
                finalOut = finalOut +  "\n> "+ out + "\noriginal: <https://discordapp.com/channels/" + str(ctx.message.channel.guild.id) + "/" + str(channel) + "/" + str(message) + ">\n"
                tmp.add(index)
            i+=1
            
        except Exception as e:
            
            if(index not in tmp):
                finalOut = finalOut + "\n*An original source message could not be retrieved*\n"
                print(e)
                print("if it's NoneType then there's probably a nonexistent channel or deleted message")
                tmp.add(index)
            continue
    await ctx.send(finalOut)
    dataLock.release()



@bot.command(pass_context=True)
async def generateword(ctx, *args):
    
    if len(args) == 0:
        await ctx.send("Usage: $generateword <letters> [length]")
        return
    graphData = generateGraph(ctx)
    graph = graphData[0]
    wordGraph = graphData[1]
    author = graphData[2]
    prevLtr = None
    await ctx.send("Making word, please wait...")
    try:
        length = 0
        word = args[0]
        start = word[len(word)-1]
        if len(args) > 1:
            length = int(args[1])
        if len(word) > 1:
            prevLtr = word[len(word)-2]
        if (length <= len(word) and length > 0) or length > maxLength:
            raise badLength
        else:
            length = length-len(word)
        while True:
            word = word + findWeightedValue(prevLtr, start, wordGraph, ctx, False, False, "", len(word))
            length -= 1
            if length < 0:
                break
        if len(word.replace(" ;", "")) == 0:
            raise WordDoesntExist
        await ctx.send(word.replace(" ;", ""))
    except WordDoesntExist:
        await ctx.send("Gee... I've never seen that character(s) before! Be sure you are using a-z and I have seen them on this server before.")
        
    except badWordChar:
        await ctx.send("Gee... I get upset with \"null\" and escape characters, or I just got confused some other way.\n(If you want to start with nothing, use $randomword.)")
        
    except badLength:
        await ctx.send("Length must be at least one greater than the number of characters initially inputted! Length cannot exceed " + str(maxLength) + " as well!")
    except Exception as e:
        await ctx.send("Something else went wrong, try again.")
        print(e)
    finally:
        dataLock.release()
        

@bot.command(pass_context=True)
async def randomword(ctx, *args):
    
    loops = -1
    if len(args) != 0:
        loops = int(args[0])
        if not loops > 0:
            loops = -1
    graphData = generateGraph(ctx)
    graph = graphData[0]
    wordGraph = graphData[1]
    author = graphData[2]
    await ctx.send("Making word, please wait...")
    try:
        if int(loops) > maxLength:
            raise badLength
        word = ""
        while True:
            randomList = []
            for x in wordGraph['W'][""].keys():
                randomList.append(x)
            index = randint(0, len(randomList)-1)
            nextletter = randomList[index]
            
            word = word + nextletter + findWeightedValue(None, nextletter, wordGraph, ctx, False, False, "", len(word + nextletter))
            if len(word.replace(" ;", "")) > 0:
                if len(word) > loops:
                    break
        await ctx.send(word.replace(" ;", ""))
    except WordDoesntExist:
        await ctx.send("Gee... something's wrong. I can't seem to find my own letters! Try again.")
        
    except badWordChar:
        await ctx.send("Gee... I'm stumbling upon \"null\" and escape characters, or I just got confused some other way!")
        
    except badLength:
        await ctx.send("Length cannot exceed " + str(maxLength) + "!")
    except Exception as e:
        await ctx.send("Something else went wrong, try again.")
        print(e)
    finally:
        dataLock.release()
        

@bot.command(pass_context=True)
async def generatenonsenseword(ctx, *args):
    
    if len(args) == 0:
        await ctx.send("Usage: $generatenonsenseword <letter(s)> [min length]")
        return
    graphData = generateGraph(ctx)
    graph = graphData[0]
    wordGraph = graphData[1]
    author = graphData[2]
    await ctx.send("Making word, please wait...")
    try:
        length = 0
        word = args[0]
        start = word[len(word)-1]
        if len(args) > 1:
            length = int(args[1])
        if (length <= len(word) and length > 0) or length > maxLength:
            raise badLength
        else:
            length = length-len(word)
        while True:
            word = word + start + findWeightedValue2(start, wordGraph, ctx, False, False, "", len(word + start))
            length -= 1
            if length < 0:
                break
        if len(word.replace(" ;", "")) == 0:
            raise WordDoesntExist
        await ctx.send(word.replace(" ;", ""))
    except WordDoesntExist:
        await ctx.send("Gee... I've never seen that character(s) before! Be sure you are using a-z and I have seen them on this server before.")
        
    except badWordChar:
        await ctx.send("Gee... I get upset with \"null\" and escape characters, or I just got confused some other way.\n(If you want to start with nothing, use $randomword.)")
        
    except badLength:
        await ctx.send("Length must be at least one greater than the number of characters initially inputted! Length cannot exceed " + str(maxLength) + " as well!")
    except Exception as e:
        await ctx.send("Something else went wrong, try again.")
        print(e)
    finally:
        dataLock.release()
        

@bot.command(pass_context=True)
async def randomnonsenseword(ctx, *args):
    
    loops = -1
    if len(args) != 0:
        loops = int(args[0])
        if not loops > 0:
            loops = -1
    graphData = generateGraph(ctx)
    graph = graphData[0]
    wordGraph = graphData[1]
    author = graphData[2]
    await ctx.send("Making word, please wait...")
    try:
        if int(loops) > maxLength:
            raise badLength
        word = ""
        while True:
            randomList = []
            for x in wordGraph['W'][""].keys():
                randomList.append(x)
            index = randint(0, len(randomList)-1)
            nextletter = randomList[index]
            
            word = word + nextletter + findWeightedValue2(nextletter, wordGraph, ctx, False, False, "", len(word + nextletter))
            #print("currnet sentence: " + sentence)
            if len(word.replace(" ;", "")) > 0:
                if len(word) > loops:
                    break
        await ctx.send(word.replace(" ;", ""))
    except WordDoesntExist:
        await ctx.send("Gee... something's wrong. I can't seem to find my own letters!")
        
    except badWordChar:
        await ctx.send("Gee... I'm stumbling upon \"null\" and escape characters, or I just got confused some other way!")
        
    except badLength:
        await ctx.send("Length cannot exceed " + str(maxLength) + "!")
    except Exception as e:
        await ctx.send("Something else went wrong, try again.")
        print(e)
    finally:
        dataLock.release()
        

#@bot.command(pass_context=True)
#async def userstats(ctx, *args):

#if (is_admin()):
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    #address_family = socket.AF_INET6

def serve(ip):
    print("Server started http://%s:%s" % (ip, serverPort))
    webServer = ThreadingHTTPServer((ip, serverPort), Handler)
    webServer.serve_forever()

if __name__ == "__main__":        
    
    t1=Thread(target=serve,args=['0.0.0.0']).start()
    #t2=Thread(target=serve,args=['::']).start()
    try:
        token = open("key.txt", "r").read()
        bot.run(token)
        
    except KeyboardInterrupt:
        pass
    print("Server stopped.")
    sys.exit()

    
#else:
    # Re-run the program with admin rights
#    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)


# U: url
# M: message
# S: sentences/sentence
# L: lastSentence
# N: lastSentenceN
# X: nextWords
# W: weight
# S: lastSavedSentence
# C: count
# A: author
