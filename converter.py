# -*- coding: utf-8 -*-
import json
from random import randint

final_template = """
<http://lkg.lynx-project.eu/kos/labourlaw_terms/SCTMID> a skos:Concept ;
skos:prefLabel PREFLABEL ;
skos:inScheme <http://lkg.lynx-project.eu/kos/labourlaw_terms> ;
skos:altLabel ALTLABEL ;
skos:definition DESC ;
skos:closeMatch <https://www.wikidata.org/entity/EKBTMID> ;
EKBBRTMID
EKBNRTMID
EKBRLTMID .
"""

prefixes = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix iso639: <http://lexvo.org/id/iso639-1/> .
@prefix wd: <http://www.wikidata.org/entity/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix lynx: <http://lkg.lynx-project.eu/kos/labourlaw_terms/> .
@prefix : <#> .

<http://lkg.lynx-project.eu/kos/labourlaw_terms> a skos:ConceptScheme; 
    skos:prefLabel "LabourLaw Terms Scheme".

# ##########################################################
"""

def sctmid_creator():
    numb = randint(1000000, 9999999)

    SCTMID = "LT" + str(numb)
    return SCTMID

wiki_dir = "/Users/sina/My_GitHub/LDTerm/backup/July16/300_retrieved_wikidata.json"
concept_net = "/Users/sina/My_GitHub/LDTerm/backup/July16/300_induction_results.json"
scterm_dict = "/Users/sina/My_GitHub/LDTerm/backup/July16/scterm_dict.csv"
rdf_dataset = list()

with open(wiki_dir, 'r') as f:
    wiki = json.load(f)
with open(concept_net, 'r') as f:
    concept = json.load(f)
with open(scterm_dict, 'r') as f:
    scterm = { (i.split(", ")[0], "en"): i.split(", ")[1] for i in f.read().split("\n")}

for a, i in enumerate(wiki):
    PREFLABEL = list()
    ALTLABEL = list()
    desc = list()
    body = list()
    related, broader, narrower = list(), list(), list()
    for b, j in enumerate(i["translations"]):
        
        PREFLABEL.append( "\"TERM\"@LANG".replace("TERM", j["name"]).replace("LANG", j["lang"]) )
        if len(j["desc"]):
            desc.append("\"%s\"@%s"%(j["desc"], j["lang"]))

        for k, v in concept[a][b]["A"].items():

            sct = sctmid_creator()
            flag = True
            while flag:
                if (sct, concept[a][b]["lang"]) not in scterm:
                    scterm[ (sct, concept[a][b]["lang"]) ] = k
                    flag = False

            if v == "synonymy":
                # ALTLABEL.append("<http://lkg.lynx-project.eu/kos/labourlaw_terms/%s>"%sct)
                # body.append("<http://lkg.lynx-project.eu/kos/labourlaw_terms/%s> skos:prefLabel \"%s\"@%s ."%(sct, k, concept[a][b]["lang"]))
                ALTLABEL.append( "\"%s\"@%s"%(k, concept[a][b]["lang"] ))
            elif v == "related":
                related.append("lynx:%s"%sct)
                body.append("lynx:%s a skos:Concept;\n\tskos:inScheme <http://lkg.lynx-project.eu/kos/labourlaw_terms> ;\n\tskos:prefLabel \"%s\"@%s ."%(sct, k, concept[a][b]["lang"]))
                # related.append( "\"%s\"@%s"%(k, concept[a][b]["lang"] ))
            elif v == "narrower":
                narrower.append("lynx:%s"%sct)
                body.append("lynx:%s a skos:Concept;\n\tskos:inScheme <http://lkg.lynx-project.eu/kos/labourlaw_terms> ;\n\t skos:prefLabel \"%s\"@%s ."%(sct, k, concept[a][b]["lang"]))
                # narrower.append( "\"%s\"@%s"%(k, concept[a][b]["lang"] ))
            elif v == "broader":
                broader.append("lynx:%s"%sct)
                body.append("lynx:%s a skos:Concept;\n\tskos:inScheme <http://lkg.lynx-project.eu/kos/labourlaw_terms> ;\n\tskos:prefLabel \"%s\"@%s ."%(sct, k, concept[a][b]["lang"]))
                # broader.append( "\"%s\"@%s"%(k, concept[a][b]["lang"] ))

    # Not able to reteive alternative labels
    i_template = final_template.replace(
        "PREFLABEL", ", ".join(PREFLABEL)).replace("SCTMID", scterm[(i["Term"], "en")]).replace(
        "DESC", ", ".join(desc)).replace("EKBTMID", i["WDTMID"])
    if len(broader):
        i_template = i_template.replace("EKBBRTMID", "\t\n".join(["skos:broader " + i + " ;" for i in broader]))
    if len(narrower):
        i_template = i_template.replace("EKBNRTMID", "\t\n".join(["skos:narrower " + i + " ;" for i in narrower]))
    if len(related):
        i_template = i_template.replace("EKBRLTMID", "\t\n".join(["skos:related " + i + " ;" for i in related]))
    if len(ALTLABEL):
        i_template = i_template.replace("ALTLABEL", ", ".join(ALTLABEL))

    for rem in ["EKBBRTMID\n", "EKBNRTMID\n", "EKBRLTMID .\n", "skos:altLabel  ;", "skos:definition  ;", "skos:prefLabel  ;", "skos:altLabel ALTLABEL ;\n"]:
        i_template = i_template.replace(rem, "")

    i_template = i_template.replace("\n\n\n", "\n").replace("\n\n", "\n").replace("\"\"", "\"")
    # print(i_template)
    rdf_dataset.append(i_template + "\n" + "\n".join(body))

with open("/Users/sina/My_GitHub/LDTerm/backup/July16/rdf_dataset.ttl", "w") as rdf:
    rdf.write(prefixes + "\n".join(rdf_dataset).replace(" ;\n\n", " .\n\n").replace(";\n\n", " .\n\n").replace("; .", "."))

with open("/Users/sina/My_GitHub/LDTerm/backup/July16/scterm_dict_new.tsv", "w") as ff:
    ff.write("\n".join( [k[0] + "\t" + k[1] + "\t" + v for k, v in scterm.items()]) )

    # exit()        # for j in i:
    #     print(skos_converter(j))
    #     exit()

