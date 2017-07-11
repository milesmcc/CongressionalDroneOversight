"""
Beware: this is Spaghetti code
"""

import sys
import json
import datetime
import unicodedata
import md5

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii

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
        standard_name = remove_accents(legislator["name"]["last"].lower())
        if datetime.datetime.strptime(legislator["terms"][-1]["end"], "%Y-%m-%d").date() >= earliest:
            if standard_name not in legislators:
                legislators[standard_name] = []
            legislators[standard_name].append({
                "first_name": legislator["name"]["first"],
                "last_name": legislator["name"]["last"],
                "party": legislator["terms"][-1]["party"], # caveat: could have switched // this is very rare, though
                "sex": legislator["bio"]["gender"], # the API says gender but they mean sex
                "state": states[legislator["terms"][-1]["state"].upper()].upper(),
                "govtrack": legislator["id"]["govtrack"],
                "periods": [
                    {
                        "start": datetime.datetime.strptime(term["start"], "%Y-%m-%d").date(),
                        "end": datetime.datetime.strptime(term["end"], "%Y-%m-%d").date()
                    } for term in legislator["terms"]
                ]
            })

def get_next_election_date(date, periods):
    try:
        for term in periods:
            if term["start"] <= date and term["end"] >= date:
                return term["end"]
    except e:
        print "[!!]" + str(e)


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
                if speaker["sex"] == "female" or speaker["name"].startswith("Mrs. ") or speaker["name"].startswith("Ms. ") or speaker["name"].startswith("Miss. "):
                    speaker_sex = "f"
                if speaker["sex"] == "male" or speaker["name"].startswith("Mr. "):
                    speaker_sex = "m"
                speaker_last_normalized = remove_accents(speaker_last.strip().lower().replace(")","").replace("(", ""))
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
                    # print speeked
                    try:
                        legislator_full = value["speakers"][speeked["speaker"]]
                        # print legislator_full
                        if 'bio' in legislator_full and legislator_full['bio'] is not None:
                            legislator = prep_legislator_for_json(legislator_full['bio'])
                            try:
                                legislator["term_ends"] = "Unknown"
                                legislator["days_until_term_ends"] = "Unknown"
                                if "periods" in legislator_full['bio']:
                                    legislator["term_ends"] = get_next_election_date(date, legislator_full['bio']["periods"])
                                    legislator["days_until_term_ends"] = (legislator["term_ends"] - date)
                                    legislator["term_ends"] = str(legislator["term_ends"])
                                    legislator["days_until_term_ends"] = legislator["days_until_term_ends"].days
                            except Exception as e:
                                print "[!] " + str(e)
                            bio_found_count += 1
                        else:
                            legislator = None
                    except Exception as e:
                        print e
                        print "(moving on...)"
                    md5sum = md5.md5()
                    md5sum.update(str(date))
                    md5sum.update(speeked["text"])
                    md5sum.update(doctitle)
                    md5sum.update(speeked["speaker"])
                    statements.append({
                        "statement": speeked["text"],
                        "speaker": speeked["speaker"],
                        "bio": legislator,
                        "date": str(date),
                        "title": doctitle,
                        "id": md5sum.hexdigest()
                    })
    print "Processing complete!"
    print "{}/{} statements have biographies associated with them ({}%).".format(bio_found_count, len(statements), (bio_found_count+0.0)/len(statements)*100)
    outloc = "annotated_congressional_record.json"
    print "Writing to disk as `{}`".format(outloc)
    with open(outloc, "w") as out:
        json.dump(statements, out, indent=4)
    print "Done!"
