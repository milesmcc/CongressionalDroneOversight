import os
from lxml import etree
import json
from StringIO import StringIO

dates = {}

def escape( q ):
    q = q.replace("&", "&amp;")
    q = q.replace("<greek-m>", "")
    #q = q.replace("<High School", "less than High School")
    return q

rootDir = '.'
for dirName, subdirList, fileList in os.walk(rootDir):
    for f in fileList:
        if f.startswith("CREC") and f.endswith(".xml"):
            print "found: " + dirName + "/" + f
            data = ""
            with open(dirName + "/" + f, "r") as infile:
                data = escape(infile.read())
                #print data
            parser = etree.XMLParser(recover=True)
            tree = etree.parse(StringIO(data), parser)
            day = tree.find("day").text
            month = tree.find("month").text
            year = tree.find("year").text
            date = "-".join([year, month, day])
            document_title = tree.find("document_title").text
            congress = tree.find("congress").text
            titles = [z.text for z in tree.findall("title")]
            location_mappings = {}
            for i in range(len(titles)):
                title = titles[i]
                if title.startswith("HON. "):
                    titles[i] = title[5:]
                    if len(titles) > i + 1:
                        titles[i] += " " + titles[i+1]
            spoken = []
            speakers = {}
            for speaking in tree.findall("speaking"):
                try:
                    text = speaking.text.replace("\n", "")
                    speaker = speaking.get("name")
                    speaker_sex = "?"
                    try:
                        speaker = speaker.split(' of ')[0]
                        if speaker.startswith("Mr. "):
                            speaker_sex = "male"
                            speaker = speaker[4:]
                        if speaker.startswith("Ms. "):
                            speaker_sex = "female"
                            speaker = speaker[4:]
                        if speaker.startswith("Dr. "):
                            speaker_sex = "?"
                            speaker = speaker[4:]
                        for title in titles:
                            if speaker in title:
                                speaker = title
                        if speaker not in speakers:
                            speakers[speaker] = {
                                "name": speaker,
                                "sex": speaker_sex
                            }
                    except:
                        print text
                    spoken.append({
                        "speaker": speaker,
                        "text": text
                    })
                except Exception as e:
                    print "[errored]"
                    print e
            if date not in dates:
                dates[date] = {
                    "speakers": {},
                    "records": []
                }
            for speaker in speakers:
                dates[date]['speakers'][speaker] = speakers[speaker]
            dates[date]['records'].append({
                "title": document_title,
                "congress": congress,
                "spoken": spoken
            })
with open("congressional_record.json", "w") as outfile:
    print "Writing..."
    json.dump(dates, outfile, indent=4)
    print "Done!"
print "Finished."
