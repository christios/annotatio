#!/usr/bin/env python3
from flask import Flask, request, render_template, jsonify, abort
import json
import methods
import os

with open('./config.json', encoding='utf8') as f:
    config = json.load(f)

USER = config['current_annotator']
ANNOTATORS = [annotator.strip() for annotator in config["annotators"]]
CORPUS_INDEXES = config["annotators"][USER]
NUMBER_OF_TOKENS = 0
NUMBER_OF_TOKENS_TAXONOMY = 0

gulf_tag_examples = {}
coda_examples = {}
msa_tag_examples = {}
search_previous_annotations = False

app = Flask(__name__)
# app.run(debug=True)

def setup_environment():
    repo_dir = os.path.join(os.getcwd(), f'annotations')
    global gulf_tag_examples, coda_examples, msa_tag_examples
    with open('./annotations/examples/gulf_tag_examples.json', encoding='utf8') as f_gulf, \
            open('./annotations/examples/coda_examples.json', encoding='utf8') as f_coda, \
            open('./annotations/examples/msa_tag_examples.json', encoding='utf8') as f_msa:
        gulf_tag_examples = json.load(f_gulf)
        coda_examples = json.load(f_coda)
        msa_tag_examples = json.load(f_msa)
    annotator_file_path = os.path.join(repo_dir, f'annotations_{USER.lower()}.json')
    if not os.path.exists(annotator_file_path):
        with open(annotator_file_path, 'w', encoding='utf8') as f:
            print([], file=f)
    texts = methods.get_single_annotations_file(assigned_corpus_indexes=CORPUS_INDEXES)
    global NUMBER_OF_TOKENS, NUMBER_OF_TOKENS_TAXONOMY
    NUMBER_OF_TOKENS = len(CORPUS_INDEXES) * len([token for sent in texts for token in sent.strip().split()])
    with open(f"./annotations/annotations_{USER.lower()}.json", 'r', encoding='utf8') as fq:
        dataaz = json.load(fq)
    NUMBER_OF_TOKENS_TAXONOMY = sum(
        1 for d in dataaz for token in d['taxonomy'] if token != 'equal')
    return texts


@app.route('/')
def index():
    repo_dir = os.path.join(os.getcwd(), f'annotations')
    annotators = [a for a in ANNOTATORS if a != USER] + ['All', 'All But Me']
    annotators.insert(0, 'Me')
    global search_previous_annotations
    search_previous_annotations = False
    if not os.path.exists(repo_dir):
        auth_key = config['password']
        texts = setup_environment(auth_key)
        return render_template('index.html',
                               phrases=texts,
                               annotated_indexes=checkIfAnnotatedPhrases(texts),
                               annotators=annotators,
                               filtered=False)
    else:
        texts = setup_environment()
        return render_template('index.html',
                               phrases=texts,
                               annotated_indexes=checkIfAnnotatedPhrases(texts),
                               annotators=annotators,
                               filtered=False)

@app.route('/filteredRes')
def filtered_index():
    filtered = parseFilteredText()
    annotators = [a for a in ANNOTATORS if a != USER] + ['All', 'All But Me']
    annotators.insert(0, 'Me')
    global search_previous_annotations
    search_previous_annotations = False
    return render_template('index.html',
                           phrases=filtered,
                           annotated_indexes=['me' for _ in range(len(filtered))],
                           annotators=annotators,
                           filtered=True)


def parseFilteredText():
    filtered_testsite_array = []
    
    with open(f"./annotations/annotations_{USER.lower()}.json", 'r', encoding='utf8') as fq:
        try:
            dataaz = json.load(fq)
            for d in dataaz:
                taxonomy = d["taxonomy"]
                for token_tags in taxonomy:
                    if 'NONE' in token_tags:
                        filtered_testsite_array.append(d["original"])
                        continue
                    else:
                        continue
        except:
            dataaz = []
    return list(dict.fromkeys(filtered_testsite_array))

def getCounts(dataaz):
    global NUMBER_OF_TOKENS, NUMBER_OF_TOKENS_TAXONOMY
    completed_morphology_tokens = sum(
        1 for d in dataaz for token in d['segments'] if token[0]['pos'] != 'NONE')
    completed_taxonomy_tags = sum(
        1 for d in dataaz for token in d['taxonomy'] if token != 'equal' and token[0] != 'NONE')
    counts = f'{completed_taxonomy_tags:,} / {NUMBER_OF_TOKENS_TAXONOMY:,}  |  {completed_taxonomy_tags/NUMBER_OF_TOKENS_TAXONOMY:.1%}' + \
        ' — ' + \
        f'{completed_morphology_tokens:,} / {NUMBER_OF_TOKENS:,}  |  {completed_morphology_tokens/NUMBER_OF_TOKENS:.1%}'
    return counts

@app.route('/getdata/<toSend>', methods=['GET','POST'])
def data_get(toSend):
    
    if request.method == 'POST': 
        print(request.get_text())
        return 'OK', 200
    
    else: 
        with open(f"./annotations/annotations_{USER.lower()}.json", 'r', encoding='utf8') as fq:
            dataaz = json.load(fq)
            print(f'{methods.bcolors.OKGREEN}{methods.bcolors.BOLD}Length of the {methods.bcolors.OKBLUE}annotations_{USER.lower()}.json {methods.bcolors.OKGREEN}file:{methods.bcolors.ENDC}', len(dataaz))
            newData = json.loads(toSend)
            if not newData.get("delete") and not methods.is_well_formed([newData]):
                return "invalid annotation"
            for d in dataaz:
                if(d["original"] == newData["original"]):
                    print(f'{methods.bcolors.OKGREEN}{methods.bcolors.BOLD}Removing sentence:{methods.bcolors.ENDC}')
                    dataaz.remove(d)
                    break
            if not search_previous_annotations:
                if not newData.get("delete"):
                    print(f'{methods.bcolors.OKGREEN}{methods.bcolors.BOLD}Replacing old sentence with:{methods.bcolors.ENDC}')
                    dataaz.append(newData)
            else:
                texts = methods.get_single_annotations_file(assigned_corpus_indexes=CORPUS_INDEXES)
                if newData["original"] not in texts:
                    return "different annotator"
                else:
                    if not newData.get("delete"):
                        print(f'{methods.bcolors.OKGREEN}{methods.bcolors.BOLD}Replacing old sentence with:{methods.bcolors.ENDC}')
                        dataaz.append(newData)
            print(f'{methods.bcolors.OKGREEN}{methods.bcolors.BOLD}Length of the {methods.bcolors.OKBLUE}annotations_{USER.lower()}.json {methods.bcolors.OKGREEN}file:{methods.bcolors.ENDC}', len(dataaz))
            
            is_well_formed = methods.is_well_formed(dataaz)
            if is_well_formed:
                print(f'{methods.bcolors.OKGREEN}{methods.bcolors.BOLD}WELL FORMED{methods.bcolors.ENDC}: OK')
            else:
                print(f'{methods.bcolors.WARNING}{methods.bcolors.BOLD}WELL FORMED{methods.bcolors.ENDC}: NOT OK')
                return "file not well formed"
            
            with open(f"./annotations/annotations_{USER.lower()}.json", 'w', encoding='utf8') as f:
                json.dump(dataaz, f, ensure_ascii = False)
                return getCounts(dataaz)

@app.route('/getAnnotationStatus/<obj>', methods=['GET','POST'])
def annotation_get(obj):
    
    if request.method == 'POST': 
        print(request.get_text())
        return 'OK', 200
    
    else: 
        obj = json.loads(obj)
        print(f'{methods.bcolors.OKGREEN}{methods.bcolors.BOLD}Getting sentence:{methods.bcolors.ENDC}', obj["original"])
        if(checkIfAnnotated(obj)):
            return "annotated"
        else:
            return "notAnnotated"

@app.route('/getPreviousAnnotations/<obj>', methods=['GET','POST'])
def previous_annotation_get(obj):
    
    if request.method == 'POST': 
        print(request.get_text())
        return 'OK', 200
    
    else: 
        obj = json.loads(obj)
        print(f'{methods.bcolors.OKGREEN}{methods.bcolors.BOLD}Getting sentence:{methods.bcolors.ENDC}', obj['original'])
        try:
            dataaz = methods.get_merged_json(repo_dir=os.path.join(os.getcwd(), f'annotations'))
            if search_previous_annotations:
                dataaz = dataaz[obj["annotator"] if obj["annotator"] != 'me' else USER.lower()]
            else:
                dataaz = dataaz[USER.lower()]
            
            for d in dataaz:
                if d["original"] == obj["original"]:
                    return json.dumps(d)
        except:
            dataaz = []

def checkIfAnnotated(obj):
    try:
        dataaz = methods.get_merged_json(repo_dir=os.path.join(os.getcwd(), f'annotations'))
        if search_previous_annotations:
            dataaz = dataaz[obj["annotator"] if obj["annotator"] != 'me' else USER.lower()]
        else:
            dataaz = dataaz[USER.lower()]
        print(f'{methods.bcolors.OKGREEN}{methods.bcolors.BOLD}Length of the {methods.bcolors.OKBLUE}annotations_{USER.lower()}.json {methods.bcolors.OKGREEN}file:{methods.bcolors.ENDC}', len(dataaz))
        sentences = [d["original"] for d in dataaz]
        if obj["original"] in sentences:
            return True
        else:
            return False
    except:
        dataaz = {}            

def checkIfAnnotatedPhrases(phrases):
    try:
        dataaz = methods.get_merged_json(repo_dir=os.path.join(os.getcwd(), f'annotations'))
        if not search_previous_annotations:
            dataaz = [d["original"] for d in dataaz[USER.lower()]]
        else:
            dataaz = [d["original"] for annotator in dataaz for d in dataaz[annotator]]
        return ["annotated" if p.strip() in dataaz else "notAnnotated" for p in phrases]
    except:
        dataaz = {}

@app.route('/getSearch/<data>', methods=['GET','POST'])
def get_search(data):
    if request.method == 'POST': 
        print(request.get_text())
        return 'OK', 200
    else: 
        new_data = json.loads(data)
        print(f'{methods.bcolors.OKGREEN}{methods.bcolors.BOLD}Example Search Query:')
        print(f'{methods.bcolors.OKCYAN}{methods.bcolors.BOLD}' +
              json.dumps(new_data, indent=2, sort_keys=True) + f'{methods.bcolors.ENDC}')
        json_response = methods.search_bar_examples(new_data["search_txt0"], gulf_tag_examples, msa_tag_examples, coda_examples, (new_data["search_txt1"], new_data["search_txt2"], new_data["search_txt3"]))
        print(f'{methods.bcolors.OKGREEN}{methods.bcolors.BOLD}Length of the response:{methods.bcolors.ENDC}', len(json_response))
        if(new_data["search_txt3"] == "CODA Examples"):
            return json.dumps(json_response)
        else:
            return json_response


@app.route('/getSearchPreviousAnnotations/<data>', methods=['GET', 'POST'])
def get_search_previous_annotations(data):
    if request.method == 'POST':  
        dataaz = methods.get_merged_json(repo_dir=os.path.join(os.getcwd(), f'annotations'))
        new_data = request.form
        filtered = methods.search_bar_previous_annotations(new_data["search_txt4"], dataaz, (
            new_data["search_txt5"], new_data["search_txt6"], new_data["search_txt7"], new_data["search_txt8"]))
        annotated_indexes = ['me' if f[0] == USER.lower() else f[0] for f in filtered]
        filtered = [f[1] for f in filtered]
        print(f'{methods.bcolors.OKGREEN}{methods.bcolors.BOLD}Length of the filtered response:{methods.bcolors.ENDC}', len(
            filtered))
        annotators = [a for a in ANNOTATORS if a != USER] + ['All', 'All But Me']
        annotators.insert(0, 'Me')
        global search_previous_annotations
        search_previous_annotations = True
        return render_template('index.html',
                               phrases=filtered,
                               annotated_indexes=annotated_indexes,
                               annotators=annotators,
                               filtered=True)
    else:  
        print(request.get_text())
        return 'OK', 200
        

@app.route('/sync')
def sync():
    methods.sync_annotations(
        repo_dir=os.path.join(os.getcwd(), f'annotations'),
        annotator_name=USER.lower())
    return 'OK', 200


@app.route('/getCount')
def get_count():
    with open(f"./annotations/annotations_{USER.lower()}.json", 'r', encoding='utf8') as fq:
        dataaz = json.load(fq)
        return getCounts(dataaz)

if __name__ == '__main__':
    # methods.get_annotated_sentences(os.path.join(
    #     os.getcwd(), f'annotations'), config["annotators"])
    import logging
    logging.basicConfig(filename='error.log', level=logging.DEBUG)
    app.run(host='0.0.0.0')
