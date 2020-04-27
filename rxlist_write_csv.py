import csv
import json
from rxlist_collect_links import write_file
import pandas



field_names = ['Drug name', 'Components', 'Forms', 'First paragraph forms', 'Therapeutic indications', 
               'Dosage (Posology) and method of administration', 'Contraindications',
               'Special warnings and precautions for use', 'Interaction with other medicinal products and other forms of interaction',
               'Undesirable effects', 'Overdose', 'Pharmacodynamic properties', 'Special precautions for disposal and other handling',
               'Date of revision of the text'
]

FILENAMES_FOR_REC = {
    'rxlist_r_data_json.json': 'rxlist_results_r.csv',
    'rxlist_q_data_json.json': 'rxlist_results_q.csv',
    'rxlist_v_data_json.json': 'rxlist_results_v.csv',
}
def letter_gen():
    for i in range(97,123):
        yield chr(i)

def csv_to_excel(letter):
    csv_fname = f'rxlist_results_{letter}.csv'
    xlsx_fname = f'rxlist_results_{letter}.xlsx'
    csv_file = pandas.read_csv(csv_fname)
    csv_file.to_excel(xlsx_fname, index=None, header=True)


def from_json_to_csv_multi():
    letters = letter_gen()
    for letter in letters:
        json_fname = f'rxlist_{letter}_data_json.json'
        csv_fname = f'rxlist_results_{letter}.csv'
        with open(json_fname) as f:
            drugs_lst = json.load(f)
        with open(csv_fname, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=field_names)
            writer.writeheader()
            for drug_dict in drugs_lst:
                writer.writerow(drug_dict)
        csv_to_excel(letter)    



def from_json_to_csv():
    for key, value in FILENAMES_FOR_REC.items():
        with open(key) as f:
            drugs_lst = json.load(f)
        with open(value, 'w') as f:
            writer = csv.DictWriter(f, fieldnames=field_names)
            writer.writeheader()
            for drug_dict in drugs_lst:
                writer.writerow(drug_dict)
        
    '''
    with open('rxlist_q_data_json.json') as f:
        drugs_lst = json.load(f)
    with open('rxlist_results_q.csv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        for drug_dict in drugs_lst:
            writer.writerow(drug_dict)
    '''
def links_starting_of(letter):
    with open('rxlist_links_dict_nodoubles.json') as f:
        all_links = json.load(f)
    links = all_links[letter]
    return links

def main():
    from_json_to_csv_multi()

def rewrite_list_of_forms():
    new_list = []
    with open('list_of_forms.json') as f:
        forms = json.load(f)
    with open('forms2.txt') as f:
        for line in f:
            new_list.append(line)
    forms.extend(new_list)
    count = 0
    for form in forms:
        forms[count] = form.lower().strip()
        count += 1
    forms = list(set(forms))
    write_file(forms, fname='forms.json')
          

if __name__ == "__main__":
    main()
    #rewrite_list_of_forms()
    #links = links_starting_of('q')
    #write_file(links, fname='q_links.json')



FORMS_LIST = [
    "dental cone",
    "enema",
    "infusion",
    "paste",
    "injection",
    "transdermal system",
    "tablet",
    "oxymel",
    "single-dose delivery system",
    "nasal drops",
    "powder",
    "capsule",
    "syrup",
    "inhaler",
    "lozenge",
    "ointment",
    "pressurized dispenser",
    "irrigation solution",
    "nebulizer",
    "aerosol spray",
    "extract",
    "pessary",
    "collodion",
    "rectal suspension enema",
    "liniment",
    "liquid preparation",
    "aromatic water",
    "paint",
    "oral solution",
    "suspension",
    "ophthalmic solution",
    "nasal spray",
    "ophthalmic emulsion",
    "granule",
    "spirit",
    "patch",
    "ear drops",
    "tincture",
    "rectal suppositories",
    "inhalation solution",
    "gel",
    "pastille",
    "aerosol",
    "dusting powder",
    "eye drops",
    "poultice",
    "injectable gel",
    "lotions",
    "suppository",
    "atomizer",
    "cream",
    "cloth",
    "vaccine",
    "lyophilizate"
]

SMALL_FORMS_LIST = [
    "aerosol",
    "aerosol spray",
    "aromatic water",
    "atomizer",
    "capsule",
    "collodion",
    "dental cone",
    "dusting powder",
    "ear drops",
    "eye drops",
    "granule",
    "inhalation solution",
    "injectable gel",
    "irrigation solution",
    "liniment",
    "liquid preparation",
    "nasal drops",
    "nasal spray",
    "ointment",
    "ophthalmic emulsion",
    "ophthalmic solution",
    "oral solution",
    "pastille",
    "patch",
    "pessary",
    "powder",
    "pressurized dispenser",
    "rectal suppositories",
    "rectal suspension enema",
    "single-dose delivery system",
    "spirit",
    "suppository",
    "tablet",
    "tincture",
    "transdermal system"
]