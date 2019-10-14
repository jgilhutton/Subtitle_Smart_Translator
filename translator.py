from textblob import TextBlob
from types import SimpleNamespace
from math import ceil
from re import search

formatos = (('<i>{}</i>', 'i'), ('<b>{}</b>', 'b'), ('<u>{}</u>', 'u'), ('^\W{}', 'l'))
endStrs = ('.', '?', '!', '...', '"',':')


def chop(it, chunks):
    chunkSize = ceil(len(it) / chunks)
    return [' '.join(it[x:x + chunkSize]) for x in range(0, len(it), chunkSize)]


def detectFormat(line):
    text = line.text
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
        line.text = '# ' + line.text
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
        chunk[2] = ' '.join(chunk[2:])
        temp.append('\n'.join(chunk[:3]))
    return temp

with open('sub.srt', 'r') as sub:
    subtitle = sub.read().split('\n\n')
    subtitle = clean(subtitle)
    lineas = [SimpleNamespace(**x) for x in [dict(zip(('id', 'timeStamp', 'text'), (x.split('\n')))) for x in subtitle]]

for linea in lineas:
    linea = detectFormat(linea)

index = 0
offset = 1
while index <= len(lineas):
    for linea in lineas[index:]:
        if linea.text[0].isupper() and not linea.text.isupper():
            if any(map(linea.text.endswith, endStrs)):
                text = TextBlob(linea.text)
                linea.text = text.translate(from_lang='en',to='es').string
                offset = 0
                break
            else:
                text = linea.text
                while True:
                    nextLine = lineas[index + offset]
                    if not nextLine.text[0].isupper() and not nextLine.text.isupper():
                        text += ' ' + nextLine.text
                        if any(map(nextLine.text.endswith, endStrs)):
                            break
                        else:
                            offset += 1
                    elif nextLine.text[0].isupper():
                        break
                text = TextBlob(text)
                text = text.translate(from_lang='en',to='es').string
                for i, t in enumerate(chop(text.split(' '), offset + 1)):
                    lineas[index + i].text = t
                    lineas[index + i] = fillFormat(lineas[index + i])
                break
    index = index + offset + 1
    offset = 1

with open('out.srt', 'w', encoding='utf-8') as outFile:
    for linea in lineas:
        outFile.write('\n'.join((linea.id, linea.timeStamp, linea.text)) + '\n\n')
