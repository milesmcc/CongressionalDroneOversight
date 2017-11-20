import sys
import json
import datetime
import re
import unicodecsv as csv
from dateutil.parser import parse
from tqdm import tqdm

if len(sys.argv) < 3:
    print "Usage: <annotated CGRecord (JSON) location> <output location>"
    sys.exit(0)

cgrecord_location = sys.argv[1]
out_location = sys.argv[2]


print "Loading annotated congressional record (this may take awhile)..."
records = []
with open(cgrecord_location, "r") as infile:
    records = json.load(infile)
print "Loaded {} records from the annotated congressional record!".format(str(len(records)))
print "Performing analysis..."

unassociated = []

trivial = 0

trivial_speakers = ["the speaker pro tempore", "the speaker pro tempore (during the vote)", "recorder", "the speaker", "the vice president", "the president", "the presiding officer", "the president pro tempore", "the vice president pro tempore"]

for record in tqdm(records, desc="analyze"):
    if 'bio' not in record or record['bio'] is None:
        unassociated.append(record)
        if record['speaker'].lower() in trivial_speakers:
            trivial += 1

print "Unassociated: " + str(len(unassociated)) + " (" + str(100.* float(len(unassociated)) / float(len(records))) + "%)"
print "Trivial: " + str(trivial) + " (" + str(100.* float(trivial) / float(len(records))) + "%)"


with open(out_location, "w") as out:
    json.dump({
        "unassociated": unassociated,
    }, out, indent=4)

print "(Results written to `"+out_location+"`.)"
