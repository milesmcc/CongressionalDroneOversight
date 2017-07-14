"""
Beware: this is Spaghetti code
"""

import sys
import json
import datetime
from datetime import timedelta
import unicodedata
import md5
import math

def decode_dw_row(row):
    # decodes row such as:
    #  114   29774  71  24  CALIFOR    100  0  1   CAPPS         -0.389   -0.227      -81.84920   1077     26    0.927
    # format: congress, icpsr, state code, district number (0 if senate or president), state name, party code (100=dem, 200=republican), occupancy, office attainment type, name, 1st dimension coord, 2nd dimension coord, log likelyhood, # of votes, # of classification errors, geometric mean probability
    elements = [element.strip() for element in row.split("  ") if element.strip() != ""]
    if len(elements) == 16:
        del elements[9]
    if len(elements) != 15:
        print "error: != 15 elements in a row! {}".format(len(elements))
        print row
        raise Exception("!= 15 elements in row")
    return {
        "congress": elements[0],
        "icpsr": elements[1],
        "state_code": elements[2],
        "district_number": elements[3],
        "state": remove_accents(elements[4].lower()),
        "party_code": int(elements[5]),
        "occupancy": elements[6],
        "office_attainment_type": elements[7],
        "last_name": remove_accents(elements[8].split(" ")[0].lower()),
        "dim_1": float(elements[9]),
        "dim_2": float(elements[10]),
        "log_likelyhood": float(elements[11]),
        "votes": int(elements[12]),
        "classification_errors": float(elements[13]),
        "geometric_mean_probability": float(elements[14])
    }

def load_dw_nominate_scores(filepath, mincongress):
    # Return all DW-NOMINATE scores in the file located at filepath
    # in the following format:
    # scores[last name][congress][state] = data
    scores = {}
    with open(filepath, "r") as data:
        for line in data.readlines():
            score = decode_dw_row(line)
            if int(score["congress"]) < mincongress:
                continue
            if score["last_name"] not in scores:
                scores[score["last_name"]] = {}
            if score["state"] not in scores[score["last_name"]]:
                scores[score["last_name"]][score["state"]] = {}
            scores[score["last_name"]][score["state"]][score["congress"]] = score
    return scores

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', unicode(input_str))
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

def get_congress(time):
    time = time - timedelta(days=3)
    year = time.year
    return int(math.ceil(0.5*year - 894))

def in_range(periods, date):
    for period in periods:
        if date >= period["start"] and date <= period["end"]:
            return True
    return False

def parse_legislator_file_into_legislators(f):
    global legislators
    data = json.load(f)
    for legislator in data:
        standard_name = remove_accents(legislator["name"]["last"].lower())
        if datetime.datetime.strptime(legislator["terms"][-1]["end"], "%Y-%m-%d").date() >= earliest:
            periods = [ {
                "start": datetime.datetime.strptime(term["start"], "%Y-%m-%d").date(),
                "end": datetime.datetime.strptime(term["end"], "%Y-%m-%d").date()
            } for term in legislator["terms"] ]
            names = [standard_name]
            if "-" in standard_name:
                names.extend(standard_name.split("-"))
            if " " in standard_name:
                names.extend(standard_name.split(" "))
            if standard_name not in names:
                names.append(standard_name)
            for name in names:
                if name not in legislators:
                    legislators[name] = []
                nickname = legislator['name']['first']
                if "nickname" in legislator['name']:
                    nickname = legislator["name"]["nickname"]
                legislators[name].append({
                    "first_name": legislator["name"]["first"].replace("-", "").replace(" ", ""),
                    "last_name": legislator["name"]["last"].replace("-", "").replace(" ", ""),
                    "nickname": nickname.replace("-", "").replace(" ", ""),
                    "party": legislator["terms"][-1]["party"], # caveat: could have switched // this is very rare, though
                    "sex": legislator["bio"]["gender"], # the API says gender but they mean sex
                    "state": states[legislator["terms"][-1]["state"].upper()].upper(),
                    "govtrack": legislator["id"]["govtrack"],
                    "periods": periods
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
    print "Getting DW-NOMINATE data..."
    scores = load_dw_nominate_scores("data/DW-NOMINATE.txt", 105)
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
        print statements
        biosa = 0
        nominatesa = 0
        totalnum = 0
        nttotal = 0
        trivial = ["The PRESIDING OFFICER", "The ACTING PRESIDENT pro tempore", "The CHAIR", "The SPEAKER", "The PRESIDENT pro tempore", "The PRESIDENT", "The CHAIRMAN", "The CHAIRMAN pro tempore" "The ACTING PRESIDENT pro tempore", "The Acting CHAIR", "The SPEAKER pro tempore (during the vote)", "The SPEAKER pro tempore", "recorder", ]
        for key, value in cg.iteritems():
            date = datetime.datetime.strptime(key, "%Y-%B-%d").date()
            print "..." + str(date) + " ({} records, {} speakers)".format(len(value["records"]), len(value["speakers"]))
            for speaker in value["speakers"].itervalues():
                speaker_names = speaker["name"].split(" of ")[0].lower().replace(", jr.", "").replace(" ii", "").replace("iii", "").split(" ")
                speaker_state = "?"
                if len(speaker["name"].split(" of ")) > 1:
                    speaker_state = speaker["name"].split(" of ")[1]
                speaker_last = speaker_names[-1].strip()
                speaker_first = speaker_names[0].strip()
                if speaker_first == speaker_last:
                    speaker_first = "?"
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
                    tlpossibles = len(legislators[speaker_last_normalized])
                    for legislator in legislators[speaker_last_normalized]:
                        # print speaker_last_normalized
                        if legislator["sex"].upper() == speaker_sex.upper() or legislator["sex"] == "?" or speaker_sex == "?":
                            # print "sex match"
                            # print legislator["state"]
                            # print speaker_state
                            if legislator["state"] == "?" or speaker_state == "?" or legislator["state"].upper().strip() == speaker_state.upper().strip():
                                # print "state match"
                                if speaker_first == "?" or speaker_first == "the" or speaker_first.strip() == "" or remove_accents(legislator["first_name"].upper().strip()) == remove_accents(speaker_first.upper().strip()) or remove_accents(legislator["nickname"].upper().strip()) == remove_accents(speaker_first.upper().strip()) or tlpossibles == 1:
                                    if in_range(legislator["periods"], date):
                                        possibles += 1
                                        speaker['bio'] = legislator
                                        congress = get_congress(date)
                                        extrapolated = False
                                        if congress > 114:
                                            congress = 114
                                            extrapolated = True
                                        nominate_data = None
                                        congress += 1
                                        while nominate_data is None and not (congress < 100):
                                            try:
                                                congress -= 1
                                                nominate_data = scores[speaker_last_normalized[:11]][legislator["state"].lower()[:7]][str(congress)]
                                            except KeyError:
                                                pass
                                            # couldn't find NOMINATE data...
                                        speaker['dwnominate'] = nominate_data
                    if possibles > 1:
                        speaker['bio'] = None # we must be very conservative and careful!
                        speaker['dwnominate'] = None
            for record in value["records"]:
                doctitle = record["title"]
                for speeked in record["spoken"]:
                    dwnominate = None
                    # print speeked
                    try:
                        legislator_full = value["speakers"][speeked["speaker"]]
                        if "dwnominate" in legislator_full:
                            dwnominate = legislator_full["dwnominate"] # passalong code
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
                    totalnum += 1
                    if dwnominate is not None:
                        nominatesa += 1
                    if legislator is not None:
                        biosa += 1
                    if speeked['speaker'] not in trivial:
                        nttotal += 1
                        # if legislator is None:
                        #     print speeked["speaker"]
                    statements.append({
                        "statement": speeked["text"],
                        "speaker": speeked["speaker"],
                        "bio": legislator,
                        "nominate": dwnominate,
                        "date": str(date),
                        "title": doctitle,
                        "id": md5sum.hexdigest()
                    })
    print "Processing complete!"
    print "{}/{} statements have biographies associated with them ({}% all, {}% nontrivial).".format(biosa, totalnum, (biosa+0.0)/totalnum*100, (biosa+0.0)/nttotal*100)
    print "{}/{} statements have nominate data associated with them ({}%).".format(nominatesa, totalnum, (nominatesa+0.0)/totalnum*100)
    outloc = "annotated_congressional_record.json"
    print "Writing to disk as `{}`".format(outloc)
    with open(outloc, "w") as out:
        json.dump(statements, out, indent=4)
    print "Done!"
