import csv
import json
from rxlist_collect_links import write_file

field_names = ['Drug name', 'Components', 'Forms', 'Therapeutic indications', 'Dosage (Posology) and method of administration', 'Contraindications',
               'Special warnings and precautions for use', 'Interaction with other medicinal products and other forms of interaction',
               'Undesirable effects', 'Overdose', 'Pharmacodynamic properties', 'Date of revision of the text'
]
q_links = [
        "https://www.rxlist.com/qutenza-drug.htm",
        "https://www.rxlist.com/quadracel-drug.htm",
        "https://www.rxlist.com/qoliana-drug.htm",
        "https://www.rxlist.com/doral-drug.htm",
        "https://www.rxlist.com/qmiiz-odt-drug.htm",
        "https://www.rxlist.com/qualaquin-drug.htm",
        "https://www.rxlist.com/quinidine-gluconate-drug.htm",
        "https://www.rxlist.com/seroquel-drug.htm",
        "https://www.rxlist.com/quillichew-er-drug.htm",
        "https://www.rxlist.com/quinidine-injection-drug.htm",
        "https://www.rxlist.com/qtern-drug.htm",
        "https://www.rxlist.com/seroquel-xr-drug.htm",
        "https://www.rxlist.com/quelicin-drug.htm",
        "https://www.rxlist.com/qbrexza-drug.htm",
        "https://www.rxlist.com/quinidex-drug.htm",
        "https://www.rxlist.com/qudexy-xr-drug.htm",
        "https://www.rxlist.com/accupril-drug.htm",
        "https://www.rxlist.com/qternmet-xr-drug.htm",
        "https://www.rxlist.com/quixin-drug.htm",
        "https://www.rxlist.com/qvar-redihaler-drug.htm",
        "https://www.rxlist.com/gardasil-drug.htm",
        "https://www.rxlist.com/quartette-drug.htm",
        "https://www.rxlist.com/quadramet-drug.htm",
        "https://www.rxlist.com/qnasl-drug.htm",
        "https://www.rxlist.com/qsymia-drug.htm",
        "https://www.rxlist.com/accuretic-drug.htm",
        "https://www.rxlist.com/qvar-drug.htm",
        "https://www.rxlist.com/synercid-drug.htm",
        "https://www.rxlist.com/questran-drug.htm",
        "https://www.rxlist.com/qbrelis-drug.htm",
        "https://www.rxlist.com/quasense-drug.htm",
        "https://www.rxlist.com/quinidine-sulfate-drug.htm",
        "https://www.rxlist.com/quillivant-xr-drug.htm",
        "https://www.rxlist.com/quzyttir-drug.htm"
    ]


def from_json_to_csv():
    with open('rxlist_q_data_json.json') as f:
        drugs_lst = json.load(f)
    with open('rxlist_results_q.csv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        for drug_dict in drugs_lst:
            writer.writerow(drug_dict)

def links_starting_of(letter):
    with open('rxlist_links_dict_nodoubles.json') as f:
        all_links = json.load(f)
    links = all_links[letter]
    return links

def main():
    from_json_to_csv()

if __name__ == "__main__":
    main()

    #links = links_starting_of('q')
    #write_file(links, fname='q_links.json')
