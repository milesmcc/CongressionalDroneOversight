import sys
import json
import datetime
import re
import unicodecsv as csv

def match(record):
    """
    Determine whether or not a record matches the search and should be included.
    """
    try:
        text = record["statement"].lower()
        title = record["title"]
        
        if title in ignored_titles:
            return False
        #date = datetime.datetime.strptime(record["date"], "%Y-%m-%d")
        #bio = record["bio"]
        #party = "Unknown"
        #name = record["speaker"]
        #if bio is not Null:
        #    if "party" in bio:
        #        party = bio['party']
        #    if "first_name" in bio and "last_name" in bio:
        #        name = bio["first_name"] + " " + bio["last_name"]

        # special logic

        # [!] match border unless Pakistan or Afghanistan is present
        if "border" in text:
            if not ("pakistan" in text or "afghan" in text):
                return False

        # [!] remove "american soil"  unless "foreign" or "somalia" or "afghanistan" or "pakistan" or "yemen" present
        if "american soil" in text:
            if not ("foreign" in text or "somalia" in text or "afghanistan" in text or "pakistan" in text or "yemen" in text):
                return False

        # general terms
        required = [
            re.compile("drone|uav|unmanned aerial vehicle")
        ]
        disallowed = [
            re.compile("(commerc|amazon|bezos|homeland security|dhs|faa|federal aviation administration|police|secret service|pipeline|survey)")
                        # NOT ON PAKISTAN BORDER - FIX
        ]
        for term in required:
            if not term.search(text):
                return False
        for term in disallowed:
            if term.search(text):
                return False

        return True
    except Exception as e:
        print e

output_columns = {
    "bio_columns": [
        "first_name",
        "last_name",
        "party",
        "sex",
        "state"
    ],
    "record_columns": [
        "date",
        "statement",
        "title"
    ],
    "order": [
        "date",
        "title",
        "first_name",
        "last_name",
        "party",
        "sex",
        "state",
        "statement"
    ]
}

def generate_row(record):
    row = []
    for column in output_columns['order']:
        value = "Unknown"
        if column in output_columns["bio_columns"]:
            if record['bio'] is not None:
                if column in record['bio']:
                    value = record['bio'][column]
        if column in output_columns['record_columns']:
            if column in record:
                value = record[column]
        row.append(value)
    return row

if len(sys.argv) < 3:
    print "Usage: <Annotated CGRecord (JSON) location> <output (JSON) location> [csv location]"
    sys.exit(0)

cgrecord_location = sys.argv[1]
output_location = sys.argv[2]
csv_location = None
if len(sys.argv) > 3:
    csv_location = sys.argv[3]

print "Loading annotated congressional record (this may take awhile)..."
records = []
with open(cgrecord_location, "r") as infile:
    records = json.load(infile)
print "Loaded {} records from the annotated congressional record!".format(str(len(records)))
print "Performing search..."
matched = []
for record in records:
    if match(record):
        matched.append(record)
print "Search completed... found {} matched records ({}% matched).".format(str(len(matched)), str((len(matched)+0.0)*100/len(records)))
print "Compiling output..."
output = []
for record in matched:
    trimmed_record = {}
    # try:
    if "bio" in record:
        for column in output_columns["bio_columns"]:
            if record["bio"] is not None and column in record["bio"]:
                trimmed_record[column] = record["bio"][column]
            else:
                trimmed_record[column] = "Unknown"
    for column in output_columns["record_columns"]:
        if column in record:
            trimmed_record[column] = record[column]
        else:
            trimmed_record[column] = "Unknown"
    output.append(trimmed_record)
    # except Exception as e:
    #     print e
    #     print "(moving on)"
print "Output compiled ({}/{} matched records included)".format(str(len(output)), str(len(matched)))
print "Writing JSON..."
with open(output_location, "w") as jsonout:
    json.dump(output, jsonout, indent=4)
if csv_location is not None:
    print "Writing CSV..."
    with open(csv_location, "w") as csvfile:
        writer = csv.writer(csvfile, encoding="utf-8")
        writer.writerow(output_columns["order"])
        for match in matched:
            writer.writerow(generate_row(match))
print "Done!"
