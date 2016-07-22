"""Generates human-readable content from a threat model's JSON specification.

Examples:
    $ python docgen.py "threat model example.json"

Todos:
    * Unit tests
"""

import json
import sys

SUPPORTED_FORMATS = ['github-flavored-markdown']
DEBUG_PRINT = False

def _main():
    args = get_args()

    with open(args['json_filename'], 'r') as json_file:
        json_obj = json.load(json_file)

        if args['format'] == 'github-flavored-markdown':
            markdown = ("%s%s%s\n%s\n%s" %
                        (get_model_headers(json_obj), _get_table_headers(),
                         _get_table_body(json_obj),
                         get_countermeasures_list(json_obj),
                         get_criteria_list(json_obj)))
            with open(args['json_filename'] + ".md", 'w') as markdown_file:
                markdown_file.write(markdown)
        else:
            print_usage()

def get_model_headers(threat_model):
    """Returns name and description string for threat model in GFM format."""
    assert 'name' in threat_model
    assert 'description' in threat_model
    headers = "<!-- generated by docgen.py. See: https://github.com/OpenBitcoinPrivacyProject/threat-model-scoring-system -->\n"
    headers += "%s\n" % threat_model['name']
    headers += "=" * len(threat_model['name'])
    headers += "\n%s\n\n" % threat_model['description']
    return headers

def _get_table_headers():
    return ("Attackers | Attacks | Countermeasures | Criteria\n"
            "--- | --- | --- | ---\n")


def _get_table_body(threat_model):
    """Generates the GFM text of the table body.

    Each attacker may have multiple attacks, countermeasures, etc. and so
    in general each descriptor will only be included in the first row it
    applies to, followed by blank spaces for subsequent rows in the appropriate
    column.
    """
    table_body = ""
    assert 'attackers' in threat_model
    for attacker in threat_model['attackers']:
        attacker_name = attacker['name']
        dprint("attacker_name = %s" % attacker_name)

        if 'attacks' not in attacker:
            table_body += get_one_row(attacker_name)
            continue

        for attack in attacker['attacks']:
            attack_name = attack['name']

            dprint("attack_name = %s" % attack_name)

            if 'countermeasures' not in attack:
                table_body += get_one_row(attacker_name, attack_name)
                attacker_name = None #display name only one row per attacker
                continue

            for countermeasure in attack['countermeasures']:
                countermeasure_text = countermeasure['id']
                if 'description' in countermeasure:
                    countermeasure_text = countermeasure['description']

                dprint("countermeasure_text = %s" % countermeasure_text)

                if 'criteria-groups' not in countermeasure:
                    table_body += get_one_row(
                        attacker_name, attack_name, countermeasure_text)
                    attacker_name = None #display name only one row per attacker
                    attack_name = None #display name only one row per attack
                    continue

                for criteria_group in countermeasure['criteria-groups']:
                    table_body += _get_table_body_criteria_group_recurse(
                        threat_model, criteria_group, attacker_name,
                        attack_name, countermeasure_text)
                    attacker_name = None #display name only one row per attacker
                    attack_name = None #display name only one row per attack
                    countermeasure_text = None #display once per countermeasure

    return table_body

def _get_table_body_criteria_group_recurse(threat_model, criteria_group,
                                           attacker_name, attack_name,
                                           countermeasure_text,
                                           num_rows_printed=0):
    """A criteria-group may contain criteria and/or child criteria-groups."""
    body = ""

    dprint(("criteria_group='%s' attacker_name='%s' attack_name='%s' "
            "countermeasure_text='%s' num_rows_printed=%d") %
           (str(criteria_group), attacker_name, attack_name,
            countermeasure_text, num_rows_printed))

    if ('criteria' not in criteria_group and
            'criteria-groups' not in criteria_group and num_rows_printed == 0):
        #no actual criteria to be found under this countermeasure, so just
        #print everything else.
        return get_one_row(attacker_name, attack_name, countermeasure_text)

    if 'criteria' in criteria_group:
        for criterion in criteria_group['criteria']:
            criterion_text = criterion['id']
            #if 'description' in criterion:
            #    criterion_text = criterion['description']
            dprint("criterion_text=%s" % criterion_text)
            num_rows_printed += 1
            body += get_one_row(
                attacker_name, attack_name, countermeasure_text, criterion_text)
            attacker_name = None #display name only one row per attacker
            attack_name = None #display name only one row per attack
            countermeasure_text = None #display once per countermeasure

    if 'criteria-groups' in criteria_group:
        for criteria_group in criteria_group['criteria-groups']:
            body += _get_table_body_criteria_group_recurse(
                threat_model, criteria_group, attacker_name, attack_name,
                countermeasure_text, num_rows_printed)
            attacker_name = None #display name only one row per attacker
            attack_name = None #display name only one row per attack
            countermeasure_text = None #display once per countermeasure

    return body

def get_countermeasures_list(threat_model):
    """Returns GFM string representing the list of countermeasures."""
    counterm_section = ("## Countermeasures list\n\n"
                        "ID | Description\n"
                        "--- | ---\n")
    for counterm in threat_model['countermeasures']:
        counterm_section += ("%s | %s\n" %
                             (counterm['id'], counterm['description']))
    return counterm_section

def get_criteria_list(threat_model):
    """Returns GFM string representing the list of criteria."""
    criteria_section = ("## Criteria list\n\n"
                        "ID | Description\n"
                        "--- | ---\n")
    for criterion in threat_model['criteria']:
        criteria_section += ("%s | %s\n" %
                             (criterion['id'], criterion['description']))
    return criteria_section

def get_one_row(attacker_name=None, attack_name=None, countermeasure_text=None,
                criterion_text=None):
    """Get one row of the table based on the provided string values."""

    row = ""
    if attacker_name is None:
        row += "   "
    else:
        row += attacker_name
    row += " | "
    if attack_name is None:
        row += "   "
    else:
        row += attack_name
    row += " | "
    if countermeasure_text is None:
        row += "   "
    else:
        row += countermeasure_text
    row += " | "
    if criterion_text is None:
        row += "   "
    else:
        row += criterion_text
    row += "\n"
    return row

def get_args():
    """Reads command line arguments.
    Returns `dict`:
        * 'json_filename'
    """
    args = dict()

    args['format'] = 'github-flavored-markdown'

    args['json_filename'] = None
    if len(sys.argv) == 2:
        args['json_filename'] = str(sys.argv[1])
    else:
        print_usage()

    return args

def print_json(json_obj):
    """Prints the contents of the JSON object in pretty format to stdout."""
    print(json.dumps(json_obj, indent=4, sort_keys=True))

def print_usage():
    """Prints syntax for usage and exits the program."""
    print(("Usage:\n"
           "\tpython docgen.py threat-model-file.json"))
    sys.exit()

def dprint(data):
    """Print debug data, if enabled."""
    if DEBUG_PRINT:
        print "DEBUG: %s" % str(data)

if __name__ == '__main__':
    _main()
