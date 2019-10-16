from textblob import TextBlob
from textblob.exceptions import NotTranslated
from types import SimpleNamespace
from math import ceil
from re import search,sub
from os.path import isfile
from sys import argv

formatos = (('<i>{}</i>', 'i'), ('<b>{}</b>', 'b'), ('<u>{}</u>', 'u'), ('^\W{}', 'l'))
endStrs = ('.', '?', '!', '...', '"', ':','-')
outputFile = 'out.srt'


def translate(text):
    t = TextBlob(text)
    if t.detect_language() == 'es': return t
    try:
        t = t.translate(from_lang='en', to='es').string
    except NotTranslated:
        t = sub('["#$%&\\\(\)\*+-/:;<=>@\[\]^_`\{|\}~]','',t)
        t = t.translate(from_lang='en', to='es').string
    return t


def chop(it, chunks):
    chunkSize = ceil(len(it) / chunks)
    return [' '.join(it[x:x + chunkSize]) for x in range(0, len(it), chunkSize)]


def detectFormat(line):
    text = line.rawText
    for f in formatos:
        if search(f[0].format('.+'), text):
            text = search(''.join(('(?<=', f[0].format(').+(?='), ')')), text).group()
            line.format = f[1]
            break
    else:
        line.format = 'n'
    line.text = text.strip()
    return line


def fillFormat(line):
    if line.format == 'l':
        leadingChar = search('^\W', line.rawText).group()
        line.text = leadingChar + ' ' + line.text
    elif line.format == 'n':
        return line
    else:
        for f in formatos:
            if line.format == f[1]:
                line.text = f[0].format(line.text)
    return line


def clean(subtitle):
    temp = []
    for chunk in subtitle:
        chunk = chunk.split('\n')
        try:
            chunk[2] = ' '.join(chunk[2:])
        except:
            continue
        temp.append('\n'.join(chunk[:3]))
    return temp


def loadSrt(path,file):
    with open(path+file, 'r',encoding='utf-8') as srt:
        subtitle = srt.read().split('\n\n')
        subtitle = clean(subtitle)
        subLines = [SimpleNamespace(**x) for x in
                  [dict(zip(('id', 'timeStamp', 'rawText'), (x.split('\n')))) for x in subtitle]]
    for line in subLines:
        line = detectFormat(line)
    return subLines


def saveSrt(path,file):
    with open(path+file,'w',encoding='utf-8') as srt:
        while True:
            line = (yield)
            srt.write('\n'.join((line.id, line.timeStamp, line.text)) + '\n\n')


def getFile():
    while True:
        if len(argv) > 1: file = argv[1]
        else: file = input('File path :> ')
        if isfile(file): break
        else: print('File does not exist.')
    flist = file.replace('\\','/').split('/')
    path,file = '/'.join(flist[:-1]),flist[-1]
    if not path: path = './'
    else: path += '/'
    return path,file


def main():
    path,subFile = getFile()
    subtitle = loadSrt(path,subFile)
    saveToSrt = saveSrt(path,outputFile)
    saveToSrt.send(None)
    totalLines = len(subtitle)
    index,offset = 0,1

    while index <= totalLines:
        for line in subtitle[index:]:
            if line.text[0].isupper() and not line.text.isupper():
                if any(map(line.text.endswith, endStrs)):
                    line.text = translate(line.text)
                    saveToSrt.send(line)
                    offset = 0
                    break
                else:
                    text = line.text
                    while True:
                        nextLine = subtitle[index + offset]
                        if not nextLine.text[0].isupper() and not nextLine.text.isupper():
                            text += ' ' + nextLine.text
                            if any(map(nextLine.text.endswith, endStrs)):
                                break
                            else:
                                offset += 1
                        elif nextLine.text[0].isupper():
                            offset = 0
                            break
                    text = translate(text)
                    for i, t in enumerate(chop(text.split(' '), offset + 1)):
                        line = subtitle[index + i]
                        line.text = t
                        line = fillFormat(subtitle[index + i])
                        saveToSrt.send(line)
                    break
        status = '{}/{}\r'.format(index,totalLines)
        print(status,end=status)
        index = index + offset + 1
        offset = 1

main()