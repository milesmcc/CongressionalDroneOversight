"""
Beware: this is Spaghetti code
"""

import sys
import json
import datetime

states = {
        'AK': 'Alaska',
        'AL': 'Alabama',
        'AR': 'Arkansas',
        'AS': 'American Samoa',
        'AZ': 'Arizona',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DC': 'District of Columbia',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'GU': 'Guam',
        'HI': 'Hawaii',
        'IA': 'Iowa',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'MA': 'Massachusetts',
        'MD': 'Maryland',
        'ME': 'Maine',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MO': 'Missouri',
        'MP': 'Northern Mariana Islands',
        'MS': 'Mississippi',
        'MT': 'Montana',
        'NA': 'National',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'NE': 'Nebraska',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NV': 'Nevada',
        'NY': 'New York',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'PR': 'Puerto Rico',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VA': 'Virginia',
        'VI': 'Virgin Islands',
        'VT': 'Vermont',
        'WA': 'Washington',
        'WI': 'Wisconsin',
        'WV': 'West Virginia',
        'WY': 'Wyoming'
}

# compile legislators
earliest = datetime.date(1999,12,28)

legislators = {}

def prep_legislator_for_json(legislator):
    if legislator is None:
        return None
    return {
        "first_name": legislator["first_name"],
        "last_name": legislator["last_name"],
        "party": legislator["party"],
        "state": legislator["state"],
        "govtrack": legislator["govtrack"],
        "sex": legislator["sex"],
    }

def parse_legislator_file_into_legislators(f):
    global legislators
    data = json.load(f)
    for legislator in data:
        if datetime.datetime.strptime(legislator["terms"][-1]["end"], "%Y-%m-%d").date() >= earliest:
            if legislator["name"]["last"].lower() not in legislators:
                legislators[legislator["name"]["last"].lower()] = []
            legislators[legislator["name"]["last"].lower()].append({
                "first_name": legislator["name"]["first"],
                "last_name": legislator["name"]["last"],
                "party": legislator["terms"][-1]["party"], # caveat: could have switched // this is very rare, though
                "sex": legislator["bio"]["gender"], # the API says gender but they mean sex
                "state": states[legislator["terms"][-1]["state"].upper()].upper(),
                "govtrack": legislator["id"]["govtrack"],
                "periods": [
                    {
                        "start": datetime.datetime.strptime(term["start"], "%Y-%m-%d").date(),
                        "end": datetime.datetime.strptime(term["start"], "%Y-%m-%d").date()
                    } for term in legislator["terms"]
                ]
            })


if len(sys.argv) != 2:
    print "Enter path to the congressional record file as the argument!"
else:
    print "Compiling legislators..."
    with open("data/legislators-current.json", "r") as lf:
        parse_legislator_file_into_legislators(lf)
    with open("data/legislators-historical.json", "r") as lf:
        parse_legislator_file_into_legislators(lf)
    print "Compiled!"
    overlap = 0
    total = 0
    for value in legislators.itervalues():
        total += len(value)
        if len(value) > 1:
            # print value
            # print len(value)
            # print "----"
            overlap += len(value)
    print "Name overlap: " + str(overlap)
    print "Total: " + str(total)
    print "-----"
    print "Loading the congressional record... (this may take a while)"
    statements = []
    bio_found_count = 0
    cg = None
    with open(sys.argv[1], "r") as cgrec:
        cg = json.load(cgrec)
    if not cg == None:
        print "Congressional record loaded!"
        print "Processing speakers and other elements..."
        for key, value in cg.iteritems():
            date = datetime.datetime.strptime(key, "%Y-%B-%d").date()
            print "..." + str(date) + " ({} records, {} speakers)".format(len(value["records"]), len(value["speakers"]))
            for speaker in value["speakers"].itervalues():
                speaker_names = speaker["name"].split(" of ")[0].split(" ")
                speaker_state = "?"
                if len(speaker["name"].split(" of ")) > 1:
                    speaker_state = speaker["name"].split(" of ")[1]
                speaker_last = speaker_names[-1].strip()
                speaker_first = speaker_names[0].strip()
                if speaker_first is "The":
                    speaker_first = speaker["name"]
                    speaker_last = speaker["name"] # weird behavior, but go with it.
                if len(speaker_names) == 1:
                    speaker_first = "?"
                speaker_sex = "?"
                if speaker["sex"] == "male":
                    speaker_sex = "m"
                if speaker["sex"] == "female":
                    speaker_sex = "f"
                speaker_last_normalized = speaker_last.strip().lower().replace(")","").replace("(", "")
                if speaker_last_normalized in legislators:
                    possibles = 0
                    for legislator in legislators[speaker_last_normalized]:
                        # print speaker_last_normalized
                        if legislator["sex"].upper() == speaker_sex.upper() or legislator["sex"] == "?" or speaker_sex == "?":
                            # print "sex match"
                            # print legislator["state"]
                            # print speaker_state
                            if legislator["state"] == "?" or speaker_state == "?" or legislator["state"].upper().strip() == speaker_state.upper().strip():
                                # print "state match"
                                possibles += 1
                                speaker['bio'] = legislator
                    if possibles > 1:
                        speaker['bio'] = None # we must be very conservative and careful!
            for record in value["records"]:
                doctitle = record["title"]
                for speeked in record["spoken"]:
                    legislator = None
                    try:
                        legislator = value["speakers"][speeked["speaker"]]
                        if 'bio' in legislator:
                            legislator = prep_legislator_for_json(legislator['bio'])
                            bio_found_count += 1
                        else:
                            legislator = None
                    except Exception as e:
                        print e
                        print "(moving on...)"
                    statements.append({
                        "statement": speeked["text"],
                        "speaker": speeked["speaker"],
                        "bio": legislator,
                        "date": str(date),
                        "title": doctitle
                    })
    print "Processing complete!"
    print "{}/{} statements have biographies associated with them ({}%).".format(bio_found_count, len(statements), (bio_found_count+0.0)/len(statements)*100)
    outloc = "annotated_congressional_record.json"
    print "Writing to disk as `{}`".format(outloc)
    with open(outloc, "w") as out:
        json.dump(statements, out, indent=4)
    print "Done!"