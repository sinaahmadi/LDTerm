# -*- coding: utf-8 -*-
"""
Created on Mon May  13 16:45:08 2019
 @author: Sina Ahmadi - Patricia Martín Chozas  .

"""
import requests
from random import randint
import os
import requests
import json
# header for Wikidata queries
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
# =========================================
# Clean text by removing noisy characters
# =========================================
def clean_text(text):
    return text.replace("\n", "")
# =========================================
# Creation of numeric ID for source terms
# =========================================
def sctmid_creator():
    numb = randint(1000000, 9999999)

    SCTMID = "LT" + str(numb)
    return SCTMID
# =========================================
# Given a term, get the synonyms from different languages on ConcetpNet
# =========================================
def get_conceptNet_synonyms(term, lang="en"):
    synonyms = dict()
    obj = requests.get("http://api.conceptnet.io/query?start=/c/%s/%s&rel=/r/Synonym&limit=1000"%(lang, term)).json()
    for edge_index in range(len(obj['edges'])):
        syn_lang = obj['edges'][edge_index]["end"]["language"]
        if syn_lang not in synonyms:
            synonyms[syn_lang] = [obj['edges'][edge_index]["end"]["label"]]
        else:
            synonyms[syn_lang].append(obj['edges'][edge_index]["end"]["label"])
    return synonyms

def inducer(T, A, S):
    # Gets T, the list of preferred labels and A, the list of alternative labels
    # Using synonyms of T, S, it induces the semantic relationship that exists between T and A. 
    # S is a dictionary of word as term and dictionary {lang: synonyms} as values.
    semantic_relationship = None

    if len(A) and len(T):
        invalid = False
        if len(T) == len(A):
            case_check = list()
            for t in T:
                if t in A:
                    case_check.append(True)
                else:
                    # check if the language exists
                    if lang in S[t]:
                        print(S[t][lang])
                        if True in [True for s_t in S[t][lang] if s_t in A]:
                            case_check.append(True)
                        else:
                            case_check.append(False)
                    else:
                        invalid = True

            if case_check.count(True) < len(T):
                semantic_relationship = "related"
            if not invalid and False not in case_check: 
                semantic_relationship = "synonymy"

        elif len(T) < len(A):
            case_check = list()
            for t in T:
                print(S[t][lang])
                if t in A:
                    case_check.append(True)
                else:
                    # check if the language exists
                    if lang in S[t]:
                        if True in [True for s_t in S[t][lang] if s_t in A]:
                            case_check.append(True)
                        else:
                            case_check.append(False)
                    else:
                        case_check.append(False)

            # print(case_check)
            if False not in case_check:
                semantic_relationship = "narrower"

        elif len(T) > len(A):
            case_check = True
            for a in A:
                # Find all the synonyms of the existing terms
                syns = list()
                for term_syn in S.values():
                    if lang in term_syn:
                        syns = syns + term_syn[lang]
                    else:
                        pass

                syns = list(set(syns))
                if len(syns):
                    if not (a in T or True in [True for s_t in syns if a in s_t]):
                        case_check = False
                else:
                    invalid = True

            if not invalid and case_check:
                semantic_relationship = "broader"

        else:
            pass

    return semantic_relationship
# =========================================
# Extract multiLabel
# =========================================
# Given a JSON file, extract multiple values for one entry and create a dicitonary {article_URL:[altLabel, ...]}
# altLabel or naTerm
def extract_multiLabel(labels, key):
    multiLabels = dict()
    for item in labels['results']['bindings']:
        article = item['article']['value']
        if key in item.keys():
            label = item[key]['value']
        else:
            label = ""
        if article not in multiLabels:
            multiLabels[article] = [label]
        else:
            multiLabels[article].append(label)
    return multiLabels
# =========================================
# Retrieving from Wikidata
# =========================================
def wikidata_retriever(term, lang):
    url = 'https://query.wikidata.org/sparql'
    retrieve_query = """
      SELECT * {
       ?item rdfs:label "TERM"@LANG.
      }
    """

    class_checker = """
      ask {
        wd:WDTMID (wdt:P361|wdt:P279|wdt:P31)+ wd:SUBJECT .
      }
    """

    original_query = """
    SELECT DISTINCT ?article ?lang ?name ?desc WHERE {
      ?article schema:about wd:WDTMID;
               schema:inLanguage ?lang;
               schema:name ?name.
      FILTER(?lang in ('es', 'de', 'nl', 'en'))  
      OPTIONAL {
        wd:WDTMID schema:description ?desc.
        FILTER (lang(?name) = lang(?desc))
      }
    }ORDER BY ?lang
    """

    altLabel_query = """
    SELECT DISTINCT ?article ?altLabel WHERE {
      ?article schema:about wd:WDTMID;
               schema:inLanguage ?lang;
               schema:name ?name.
      FILTER(?lang in ('es', 'de', 'nl', 'en'))  
      OPTIONAL {
        wd:WDTMID skos:altLabel ?altLabel.
        FILTER (lang(?name) = lang(?altLabel))
      }
    }ORDER BY ?lang
    """

    naTerm_query = """
    SELECT DISTINCT ?article ?naTerm WHERE {
      ?article schema:about wd:WDTMID;
               schema:inLanguage ?lang;
               schema:name ?name.
      FILTER(?lang in ('es', 'de', 'nl'))  
      OPTIONAL {
        ?naTerm wdt:P279 wd:WDTMID;
      }
    }ORDER BY ?lang
    
    """

    brTerm_query="""
    SELECT DISTINCT ?article ?brTerm WHERE {
      ?article schema:about wd:WDTMID;
               schema:inLanguage ?lang;
               schema:name ?name.
      FILTER(?lang in ('es', 'de', 'nl'))  
      OPTIONAL {
        wd:WDTMID wdt:P279 ?brTerm;          
      }
    }ORDER BY ?lang
    """
    Wikidata_dataset = dict()
    subjects = {"legal instrument": "Q1428955", "common law": "Q30216", "statutory law": "Q7766927", "statute": "Q820655", "legislation": "Q49371", "code of law": "Q922203", "economic value": "Q868257", "employee benefit": "Q678774", "quality": "Q1207505", "political philosophy": "Q179805", "social status": "Q189970", "work": "Q6958747", "job": "Q192581", "philosophy of law": "Q126842", "policy": "Q1156854", "leave of absence": "Q13561011", "sources of law": "Q846882", "rights policy": "Q2135597", "comparative law": "Q741338", "sociology of law ": "Q847034",
                "legal doctrine": "Q1192543", "area of law": "Q1756157", "law": "Q7748", "legal science": "Q382995",
                "social issue": "Q1920219", "jurisprudence": "Q4932206", "rule": "Q1151067", "Economy": "Q159810",
                "Economics": "Q8134", "labour law": "Q628967", "human action": "Q451967", "legal concept": "Q2135465"}
    ""

    print(term)
    query = retrieve_query.replace("TERM", term).replace("LANG", lang)
    SRCTERM = "\"" + term + "\"" + "@" + lang
    #print(SRCTERM) We have to save this in the skos as well
    r = requests.get(url, params={'format': 'json', 'query': query}, headers=headers)
    data = r.json()

    if len(data['results']['bindings']) != 0:
        item_id = data['results']['bindings'][0]['item']['value'].split("/")[-1]

        retrieved_subjects = dict()
        for subject in subjects:
            query = class_checker.replace("WDTMID", item_id).replace("SUBJECT", subjects[subject])
            r = requests.get(url, params={'format': 'json', 'query': query}, headers=headers)
            data = r.json()
            if data['boolean'] == True:
                retrieved_subjects[subjects[subject]] = data['boolean']
                # Quit the loop if a subject found
                break

        if True in retrieved_subjects.values():
            query = original_query.replace("WDTMID", item_id)
            r = requests.get(url, params={'format': 'json', 'query': query}, headers=headers)
            data = r.json()
            # print(data)

            # Alternative labels
            query = altLabel_query.replace("WDTMID", item_id)
            r = requests.get(url, params={'format': 'json', 'query': query}, headers=headers)
            altLabel_response = r.json()
            altLabel_dict = extract_multiLabel(altLabel_response, "altLabel")
            # print(altLabel_dict)

            # Narrower terms
            query = naTerm_query.replace("WDTMID", item_id)
            r = requests.get(url, params={'format': 'json', 'query': query}, headers=headers)
            naTerm_response = r.json()
            naTerm_dict = extract_multiLabel(naTerm_response, "naTerm")
            # print(naTerm_dict)

            # Broader terms
            query = brTerm_query.replace("WDTMID", item_id)
            r = requests.get(url, params={'format': 'json', 'query': query}, headers=headers)
            brTerm_response = r.json()
            brTerm_dict = extract_multiLabel(brTerm_response, "brTerm")
            # print(brTerm_dict)         

            # Extract data
            retrieved = list()
            for item in data['results']['bindings']:
                article = item['article']['value']
                lang = item['lang']['value']
                name = item['name']['value']
                altL, naTeL, brTeL = "", "", ""
                if "desc" in item.keys():
                    desc = item['desc']['value']
                else:
                    desc = ""
                if article in altLabel_dict.keys():
                    altL = altLabel_dict[article]
                if article in naTerm_dict.keys():
                    naTeL = naTerm_dict[article]
                if article in brTerm_dict.keys():
                    brTeL = brTerm_dict[article]
                retrieved.append({"article": article, "lang": lang, "name": name, "desc": desc, 
                    "altLabel": altL, "naTerm": naTeL, "brTerm": brTeL})

            subj = list(retrieved_subjects.keys())[list(retrieved_subjects.values()).index(True)]
            retrieved_data = {"WDTMID": item_id, "SBJCT": subj, "translations": retrieved}
        else:
            retrieved_data = {}
    else:
        retrieved_data = {}

    return retrieved_data
# =========================================
# SKOS template
# =========================================
prefixes_templates = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix iso639: <http://lexvo.org/id/iso639-1/> .
@prefix wd: <http://www.wikidata.org/entity/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#>.
@prefix : <#> .
"""
concept_template = """
    <http://lkg.lynx-project.eu/kos/labourlaw_terms/SCTMID> a skos:Concept ;
        skos:closeMatch <https://www.wikidata.org/wiki/WDTMID> ;
        skos:prefLabel CONCAT ;
"""

desc_template = """
        skos:description CONCAT1;
"""

alt_template = """
        skos:altLabel CONCAT2 ;
"""

br_template = """
        skos:broader WDBRTMID ; 
"""

naTerm_template = """
        skos:narrower WDNRTMID ;
"""
re_template = """
        skos:related <https://www.wikidata.org/wiki/WDRLTMID>; 
"""

brconcept_temp = """
    <http://lkg.lynx-project.eu/kos/labourlaw/LTBRTMID> a skos:Concept .
    skos:exactMatch <https://www.wikidata.org/wiki/WDBRTMID> .
"""

brconceptlab_temp = """
        skos:prefLabel CONCAT3 ;
"""

nrconcept_temp = """
    <http://lkg.lynx-project.eu/kos/labourlaw/LTNRTMID> a skos:Concept .
        skos:exactMatch <https://www.wikidata.org/wiki/WDNRTMID> .
"""
nrconceptlab_temp = """
        skos:prefLabel CONCAT4 ;
"""

reconcept_temp = """
    <http://lkg.lynx-project.eu/kos/labourlaw/LTRLTMID> a skos:Concept .
        skos:exactMatch <https://www.wikidata.org/wiki/WDRLTMID> .
"""
reconceptlab_temp = """
        skos:prefLabel CONCAT5 ;
"""

# =========================================
# Creation of SKOS model with the collected Wikidata_dataset
# he quitado el zip. no faltaría un return?  naTerm_lang
# =========================================
def skos_converter(entry, wiki_data):
    name_lang, desc_lang, altLabel_lang, narrower_terms, broader_terms = list(), list(), list(), list(), list()
    translations = wiki_data["translations"]
    for i in translations:
        name_lang.append( "\"" + i["name"] + "\"" + "@" + i["lang"] )
        if i["desc"]:
            dl = "\"" + i["desc"] + "\"" + "@" + i["lang"]
            if dl not in desc_lang:
                desc_lang.append(dl)

        if i["altLabel"]:
            for lbl in i["altLabel"]:
                if len(lbl):
                    ll = "\"" + lbl + "\"" + "@" + i["lang"]
                    if ll not in altLabel_lang:
                        altLabel_lang.append(ll)

        if i["naTerm"]:
            for ntrm in i["naTerm"]:
                ntrm = "<" + ntrm + ">"
                if len(ntrm) and ntrm not in narrower_terms:
                        narrower_terms.append(ntrm)

        if i["brTerm"]:
            for btrm in i["brTerm"]:
                btrm = "<" + btrm + ">"
                if len(btrm) and btrm not in broader_terms:
                        broader_terms.append(btrm)

    header = concept_template.replace("CONCAT", ", ".join(name_lang)).replace("WDTMID", 
        wiki_data["WDTMID"]).replace("SCTMID", TERM_ID_MAP[entry])

    if ", ".join(desc_lang):
        body = desc_template.replace("CONCAT1", ", ".join(desc_lang))
    else:
        body = ""

    if ", ".join(altLabel_lang):
        alternative_labels = alt_template.replace("CONCAT2", ", ".join(altLabel_lang))
    else:
        alternative_labels = ""

    # remove empty elements (NEXT STEP)
    if ", ".join(narrower_terms):
        narrower_concepts = naTerm_template.replace("WDNRTMID", ", ".join(narrower_terms))
    else:
        narrower_concepts = ""

    if ", ".join(broader_terms):
        broader_concepts = br_template.replace("WDBRTMID", ", ".join(broader_terms))
    else:
        broader_concepts = ""

    return str(header + body + alternative_labels + narrower_concepts + broader_concepts)[:-3] + "."
# =========================================
# main
# =========================================xx
## List of words
source_language = "english"
source_file_dir = "original_datasets/100term.csv"
source_file = open(source_file_dir, "r")
terms = [t for t in source_file.read().split("\n")][0:10]
# print(terms)

term_id_file_dir = 'scterm_dict.csv'
TERM_ID_MAP = dict()
# Check if ID-term file exists
if os.path.isfile(term_id_file_dir):
    id_term = open(term_id_file_dir,'r').read().split("\n")
    TERM_ID_MAP = {t.split(", ")[0]: t.split(", ")[1] for t in id_term}
# otherwise create a new one
else:
    a = open('scterm_dict.csv','w+')
    for t in terms:
        TERM_ID_MAP[t] = sctmid_creator()
        a.write(t+ ', '+ TERM_ID_MAP[t] + '\n')
    a.close()
# ================
if False:
    output_file_name = "populated_datasets/results.rdf"
    not_found_file_name = "populated_datasets/not_found.txt"

    # # Creating the output file and writing the prefixes
    # with open(output_file_name, "a") as output_file:
    #     output_file.write(prefixes_templates)
    #     output_file.write("\n\n")

    not_found = list()
    for entry in terms[1:2]:
        retrieved_data = wikidata_retriever(entry, lang=source_language[0:2])
        print(retrieved_data)
        # if len(retrieved_data):
        #     skos_text = skos_converter(entry, retrieved_data)
        #     with open(output_file_name, "a") as output_file:
        #       output_file.write(skos_text)
        #       output_file.write("\n\n")
        # else:
        #     not_found.append(entry)

    # Writing those words which could not be found
    # with open(not_found_file_name, "w") as output_file:
    #     output_file.write("\n".join(not_found))
# ================
# with open("example.json", 'r') as f:
#     example = json.load(f)

# for trans in example["translations"]:
#     for key, value in trans.items():
#         print(key, value)
# print(example.keys())
# synonyms = get_conceptNet_synonyms("en", "discrimination")
# print(synonyms)

lang = "en"
T = "employment agreement".split()
S = dict()
for t in T:
    if t not in S:
        S[t] = get_conceptNet_synonyms(t)

print(S)
# test
# A = "employment contract".split()
# # S = {"employement":["job", "position", "work"], "agreement":["contract", "compromise", "binding"]}
# print("T:", T, "A: ", A)
# print(inducer(T, A, S))

# A = "rental contract".split()
# print("T:", T, "A: ", A)
# print(inducer(T, A, S))

# A = "temporary work contract".split()
# print("T:", T, "A: ", A)
# print(inducer(T, A, S))

# A = "contract".split()
# print("T:", T, "A: ", A)
# print(inducer(T, A, S))

# ================
# Ignore category
# Remove duplicates




