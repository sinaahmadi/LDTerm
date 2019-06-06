# -*- coding: utf-8 -*-
"""
Created on Mon May  13 16:45:08 2019
 @author: Sina Ahmadi - Patricia Martín Chozas  .

"""
import requests
from random import randint

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
# Extract altLabel
# =========================================
# Given a JSON file, extract altLabel and create a dicitonary {article_URL:[altLabel, ...]}
def extract_altLabel(labels):
    altLabels = dict()
    for item in labels['results']['bindings']:
        article = item['article']['value']
        if 'altLabel' in item.keys():
            altLabel = item['altLabel']['value']
        else:
            altLabel = ""
        if article not in altLabels:
            altLabels[article] = [altLabel]
        else:
            altLabels[article].append(altLabel)
    return altLabels
# =========================================
# Extract naTerm
# =========================================
# Given a JSON file, extract altLabel and create a dicitonary {article_URL:[altLabel, ...]}

def extract_naTerm(terms):
    naTerms = dict()
    for item in terms['results']['bindings']:
        article = item['article']['value']
        if 'naTerm' in item.keys():
            naTerm = item['naTerm']['value']
        else:
            naTerm = ""
        if article not in naTerms:
            naTerms[article] = [naTerm]
        else:
            naTerms[article].append(naTerm)
    return naTerms
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
      FILTER(?lang in ('es', 'de', 'nl'))  
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
      FILTER(?lang in ('es', 'de', 'nl'))  
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
    Wikidata_dataset = dict()
    subjects = {"policy": "Q1156854", "leave of absence": "Q13561011", "sources of law": "Q846882", "rights policy": "Q2135597", "comparative law": "Q741338", "sociology of law ": "Q847034",
                "legal doctrine": "Q1192543", "area of law": "Q1756157", "law": "Q7748", "legal science": "Q382995",
                "social issue": "Q1920219", "jurisprudence": "Q4932206", "rule": "Q1151067", "Economy": "Q159810",
                "Economics": "Q8134", "labour law": "Q628967", "human action": "Q451967", "legal concept": "Q2135465"}
    ""

    print(term)
    query = retrieve_query.replace("TERM", term).replace("LANG", lang)
    r = requests.get(url, params={'format': 'json', 'query': query})
    data = r.json()

    if len(data['results']['bindings']) != 0:
        item_id = data['results']['bindings'][0]['item']['value'].split("/")[-1]

        retrieved_subjects = dict()
        for subject in subjects:
            query = class_checker.replace("WDTMID", item_id).replace("SUBJECT", subjects[subject])
            r = requests.get(url, params={'format': 'json', 'query': query})
            data = r.json()
            if data['boolean'] == True:
                retrieved_subjects[subjects[subject]] = data['boolean']
                # Quit the loop if a subject found
                break

        if True in retrieved_subjects.values():
            query = original_query.replace("WDTMID", item_id)
            r = requests.get(url, params={'format': 'json', 'query': query})
            data = r.json()
            # print(query)

            query = altLabel_query.replace("WDTMID", item_id)
            r = requests.get(url, params={'format': 'json', 'query': query})
            altLabel_response = r.json()
            altLabel_dict = extract_altLabel(altLabel_response)

            #patricia tries to retrieve naTerm
            query = naTerm_query.replace("WDTMID", item_id)
            r = requests.get(url, params={'format': 'json', 'query': query})
            naTerm_response = r.json()
            naTerm_dict = extract_naTerm(naTerm_response)
                           
            # Extract data
            retrieved = list()
            for item in data['results']['bindings']:
                article = item['article']['value']
                lang = item['lang']['value']
                name = item['name']['value']
                if "desc" in item.keys():
                    desc = item['desc']['value']
                else:
                    desc = ""
                retrieved.append({"article": article, "lang": lang, "name": name, "desc": desc, "altLabel": altLabel_dict[article], "naTerm": naTerm_dict[article]})

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
        skos:altLabel CONCAT2 .
"""

br_template = """
        skos:broader <https://www.wikidata.org/wiki/WDBRTMID>; 
"""

naTerm_template = """
        skos:narrower <https://www.wikidata.org/wiki/WDNRTMID> .
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
# he quitado el zip. no faltaría un return?
# =========================================
def skos_converter(entry, wiki_data):
    name_lang, desc_lang, altLabel_lang, naTerm_lang = list(), list(), list(), list()
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
                naTerm = ntrm
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
        if len(body):
            body = body[:-2] + "."

    if ", ":
        narrow_terms = naTerm_template.replace("WDNRTMID", naTerm)
    else:
        narrow_terms = ""
        if len(body):
            body = body[:-2] + "."

    return header + body + alternative_labels + narrow_terms
# =========================================
# main
# =========================================
## List of words
source_language = "english"
source_file_dir = "original_datasets/6term.csv"
source_file = open(source_file_dir, "r")
terms = [t for t in source_file.read().split("\n")][0:10]
# print(terms)

# Giving an ID to each term and saving the dict in a csv file
TERM_ID_MAP = dict()
a = open('scterm_dict.csv','w+')
for t in terms:
    TERM_ID_MAP[t] = sctmid_creator()
    a.write(t+ ', '+ TERM_ID_MAP[t] + '\n')
a.close()

output_file_name = "populated_datasets/results.rdf"
not_found_file_name = "populated_datasets/not_found.txt"

# Creating the output file and writing the prefixes
with open(output_file_name, "a") as output_file:
    output_file.write(prefixes_templates)
    output_file.write("\n\n")

not_found = list()
for entry in terms:
    retrieved_data = wikidata_retriever(entry, lang=source_language[0:2])
    # print(retrieved_data)
    if len(retrieved_data):
        skos_text = skos_converter(entry, retrieved_data)
        with open(output_file_name, "a") as output_file:
          output_file.write(skos_text)
          output_file.write("\n\n")
    else:
        not_found.append(entry)

# Writing those words which could not be found
with open(not_found_file_name, "w") as output_file:
    output_file.write("\n".join(not_found))








