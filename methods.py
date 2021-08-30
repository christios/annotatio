from typing import Dict, List, Union, Tuple
from string import punctuation as punc
from collections import namedtuple
import re
import os
import json
import string

POS = str
ExampleFieldGulf = str # ['baseword', 'gloss', 'clitic', 'context']
ExampleFieldCODA = str  # ['raw', 'coda', 'context']
ExampleFieldMSA = str # ['segment', 'gloss', 'context']
SegmentType = str # ['baseword', 'enclitic', 'proclitic']
ExampleGulf = Dict[ExampleFieldGulf, str]
ExampleCODA = Dict[ExampleFieldCODA, str]
ExampleMSA = Dict[ExampleFieldMSA, str]
ExamplesQueryFilter = namedtuple('ExamplesQueryFilter', 'segment_type match_type resource')

ARABIC_LETTERS = "ءؤئابتثجحخدذرزسشصضطظعغفقكلمنهوىي"

def search_bar_examples(query: str,
                        gulf_tag_examples: Dict[SegmentType, Dict[POS, List[ExampleGulf]]],
                        msa_tag_examples: Dict[POS, List[ExampleMSA]],
                        coda_examples: List[ExampleCODA],
                        query_filter: Tuple[str] = ('Baseword', 'Approximate', 'Gulf Tags')
                        ) -> Union[Dict[POS, List[ExampleGulf]], List[ExampleCODA], Dict[POS, List[ExampleMSA]]]:
    """Function which allows to search for specific examples in a static JSON file using a filter.
    For the query filter:
        - In index 0, possible choices are 'Baseword', 'Enclitic', 'Proclitic'.
        - In index 1, possible choices are 'Approximate', 'Exact' (whether the match should be exact or not).
        - In index 2, possible choices are 'Gulf Tags', 'MSA Tags', 'CODA Examples'.

    Args:
        query (str): what the user will type in the search bar.
        gulf_tag_examples (Dict[SegmentType, Dict[POS, List[Dict[ExampleField, str]]]]): already parsed static JSON object sitting in memory for Gulf Arabic tagging examples
        msa_tag_examples (Dict[POS, List[Dict[ExampleField, str]]]): already parsed static JSON object sitting in memory for MSA tagging examples
        coda_examples (List[ExampleCODA]): already parsed static JSON object sitting in memory for CODA standardization examples
        query_filter (Optional[List[str]], optional): Should be drop down menus where the user specifies what he is searching for. Defaults to ('Baseword', 'Approximate', 'Gulf Tags').

    Returns:
        Union[Dict[POS, List[Union[ExampleGulf, ExampleMSA]]], List[ExampleCODA]]: Dictionary with a structure which depends on the value chosen for the resource type (index 2) in the query filter
    """
    query_filter = ExamplesQueryFilter(*query_filter)
    
    if 'Tags' in query_filter.resource:
        response: Dict[POS, List[Union[ExampleGulf, ExampleMSA]]] = {}
        if 'Gulf' in query_filter.resource:
            tag_examples: Dict[POS, List[ExampleGulf]] = gulf_tag_examples[query_filter.segment_type.lower()]
        elif 'MSA' in query_filter.resource:
            tag_examples: Dict[POS, List[ExampleMSA]] = msa_tag_examples

        is_pos = True if query.translate(
            str.maketrans('', '', punc)).isupper() else False
        is_arabic_str = True if query[0] in ARABIC_LETTERS else False
        is_gloss = True if [True for char in query if char.islower(
        ) and char not in ARABIC_LETTERS] else False

        if is_pos:
            query_pos, query_features = None, None
            if 'Gulf' in query_filter.resource:
                query_split = query.split(':')
                query_pos, query_features = query_split[0], set(query_split[1]) if len(query_split) == 2 else set()
            for k, v in tag_examples.items():
                k_pos, k_features = None, None
                if 'Gulf' in query_filter.resource and (query_pos or query_features):
                    k = k.split(':')
                    k_pos, k_features = k[0], set(k[1]) if len(k) == 2 else set()
                
                if not query_pos:
                    if query_filter.match_type == 'Approximate':
                        if query in k:
                            response[k] = v
                    elif query_filter.match_type == 'Exact':
                        if query == k:
                            response[k] = v
                else:
                    if query_filter.match_type == 'Approximate':
                        if query_pos in k_pos or bool(k_features.intersection(query_features)):
                            response[':'.join(k)] = v
                    elif query_filter.match_type == 'Exact':
                        if query_pos == k_pos and query_features == k_features:
                            response[':'.join(k)] = v

        elif is_arabic_str or is_gloss:
            if 'Gulf' in query_filter.resource:
                example_key = 'baseword' if query_filter.segment_type.lower() == 'baseword' else 'clitic'
                example_key = 'gloss' if is_gloss else example_key
            elif 'MSA' in query_filter.resource:
                example_key = 'segment'

            for k, v in tag_examples.items():
                v_: List[ExampleGulf] = []
                for example in v:
                    if query_filter.match_type == 'Approximate':
                        if query in example[example_key]:
                            v_.append(example)
                    elif query_filter.match_type == 'Exact':
                        if query == example[example_key]:
                            v_.append(example)
                if v_:
                    response[k] = v_
    
    elif query_filter.resource == 'CODA Examples':
        response: List[ExampleCODA] = []
        for example in coda_examples:
            if query_filter.match_type == 'Approximate':
                if query in example['raw'] or query in example['coda']:
                    response.append(example)
            elif query_filter.match_type == 'Exact':
                if query == example['raw'] or query == example['coda']:
                    response.append(example)
    
    return response

Annotator = str
Feature = str # ['raw', 'coda', 'segments']
AnnotationField = str  # ['text', 'verb_form', 'pos', 'lemma']
Segment = Dict[AnnotationField, str]
Annotation = Dict[Feature, Union[str, List[str], List[Segment]]]
FilteredAnnotation = namedtuple('FilteredAnnotation', 'annotator id annotation')
AnnotationsQueryFilter = namedtuple('AnnotationsQueryFilter', 'feature field match annotators')


def search_bar_previous_annotations(query: str,
                                    annotations_json: Dict[Annotator, List[Annotation]],
                                    query_filter: Tuple[str] = ('Raw', 'Text', 'Approximate', 'Christian')
                                    ) -> List[Annotation]:
    """Function which allows to search for previously done annotations the contents of which match the values of the filter.
    For the query filter:
        - In index 0, possible choices are 'Raw', 'CODA', 'Segments'.
        - In index 1, possible choices are 'Text', 'Verb Form', 'POS', 'Lemma'.
        - In index 2, possible choices are 'Approximate', 'Exact' (whether the match should be exact or not).
        - In index 3, possible choices are the names of the annotators, to be defined in a separate list.

    Args:
        query (str): what the user will type in the search bar.
        annotations_json (Dict[Annotator, List[Annotation]]): JSON file containing the already finished annotations
        query_filter (Tuple[str], optional): Should be dropdown menus where the user specifies what he is searching for. Defaults to ('Raw', 'Text', 'Approximate', 'Christian').

    Returns:
        List[Annotation]: List of annotations to show that we can scroll through.
    """
    with open('./config.json', encoding='utf8') as f:
        config = json.load(f)
    ANNOTATORS = [annotator for annotator in config["annotators"]]
    CURRENT_ANNOTATOR = config["current_annotator"]
    
    query_filter = AnnotationsQueryFilter(*query_filter)
    # Filtering by annotator
    annotators = ANNOTATORS
    annotators = [query_filter.annotators] if query_filter.annotators in ANNOTATORS else ANNOTATORS
    if query_filter.annotators.strip() == 'All But Me':
        annotators.remove(CURRENT_ANNOTATOR)
    elif query_filter.annotators.strip() == 'Me':
        annotators = [CURRENT_ANNOTATOR]
    elif query_filter.annotators.strip() == 'All':
        annotators = ANNOTATORS
        
    # Filtering by feature
    annotations_filtered: List[FilteredAnnotation] = []
    for annotator, annotations in annotations_json.items():
        if annotator in [a.lower() for a in annotators]:
            for i, annotation in enumerate(annotations):
                if query_filter.feature == 'Segments':
                    for token in annotation[query_filter.feature.lower()]:
                        for segment in token:
                            annotations_filtered.append(FilteredAnnotation(
                                annotator, i, segment[query_filter.field.lower()]))
                else:
                    annotations_filtered.append(FilteredAnnotation(
                        annotator, i, annotation['_'.join(query_filter.feature.lower().split())]))

    already_added = []
    response: List[Tuple[Annotator, Annotation]] = []
    query_pos, query_features = None, None
    if query_filter.field == 'POS':
        query_split = query.split(':')
        query_pos, query_features = query_split[0], set(query_split[1]) if len(query_split) == 2 else set()
    for annotation in annotations_filtered:
        k_pos, k_features = None, None
        if query_filter.field == 'POS' and (query_pos or query_features):
            k = annotation.annotation.split(':')
            k_pos, k_features = k[0], set(k[1]) if len(k) == 2 else set()
        
        if not (query_pos or query_features):
            if query_filter.match == 'Approximate':
                if isinstance(annotation.annotation, list):
                    condition = query in ' '.join(annotation.annotation)
                else:
                    condition = query in annotation.annotation
                if condition and \
                    (annotation.annotator, annotation.id) not in already_added:
                    response.append(
                        (annotation.annotator, annotations_json[annotation.annotator][annotation.id]['original']))
                    already_added.append((annotation.annotator, annotation.id))
            elif query_filter.match == 'Exact':
                if isinstance(annotation.annotation, list):
                    condition = query in annotation.annotation
                else:
                    condition = query == annotation.annotation
                if condition and \
                    (annotation.annotator, annotation.id) not in already_added:
                    response.append(
                        (annotation.annotator, annotations_json[annotation.annotator][annotation.id]['original']))
                    already_added.append((annotation.annotator, annotation.id))
        else:
            if (annotation.annotator, annotation.id) not in already_added:
                if query_filter.match == 'Approximate':
                    if query_pos in k_pos or bool(k_features.intersection(query_features)):
                        response.append(
                            (annotation.annotator, annotations_json[annotation.annotator][annotation.id]['original']))
                        already_added.append((annotation.annotator, annotation.id))
                elif query_filter.match == 'Exact':
                    if query_pos == k_pos and query_features == k_features:
                        response.append(
                            (annotation.annotator, annotations_json[annotation.annotator][annotation.id]['original']))
                        already_added.append((annotation.annotator, annotation.id))

    return response


COMMIT_MESSAGE = 'No message'

def clone_repo(repo_dir='/Users/chriscay/thesis/annotation_wiaam',
               username='christios',
               auth_key='',
               repo_name='annotated-shami-corpus',
               annotator_name='Wiaam') -> None:
    """This method is called once, when the annotator sets up their local application.
    What it does:
        - Clones a remote repository that I have already set up
        - Sets up a local branch in the annotator's name and its corresponding up-stream branch
    """
    annotations_name = f'{annotator_name}_annotations'
    annotator_file_path = os.path.join(repo_dir, f'annotations_{annotator_name}.json')

    if not os.path.exists(repo_dir):
        repo_url = f"https://{username}:{auth_key}@github.com/{username}/{repo_name}.git"
        repo = Repo.clone_from(repo_url, repo_dir)
    else:
        repo = Repo(repo_dir)
    
    remote_branches = repo.git.branch('-r').splitlines()
    remote_branches = [branch.strip()
                    for branch in remote_branches if re.match(r'\w+/\w+$', branch.strip(), re.M) and 'main' not in branch]
    if not bool([True for b in remote_branches if annotations_name in b]):
        annotations = repo.create_head(annotations_name)
        if not os.path.exists(annotator_file_path):
            with open(annotator_file_path, 'w', encoding='utf8') as f:
                print([], file=f)
        # Pushing empty annotations branch
        annotations.checkout()
        repo.git.add([annotator_file_path])
        repo.index.commit('Add empty annotations branch')
        repo.git.push('origin', annotations_name)
    else:
        repo.git.checkout(annotations_name)
        
    if not os.path.exists(annotator_file_path):
        with open(annotator_file_path, 'w', encoding='utf8') as f:
            print([], file=f)
    else:
        repo.git.add([annotator_file_path])
        repo.index.commit('Saving work without pushing to remote')

    
    repo.git.checkout('resources-inter-annotator')
    with open('./annotations/examples/gulf_tag_examples.json', encoding='utf8') as f_gulf, \
            open('./annotations/examples/coda_examples.json', encoding='utf8') as f_coda, \
            open('./annotations/examples/msa_tag_examples.json', encoding='utf8') as f_msa:
        gulf_tag_examples = json.load(f_gulf)
        coda_examples = json.load(f_coda)
        msa_tag_examples = json.load(f_msa)
    repo.git.checkout(annotations_name)
        
    return gulf_tag_examples, coda_examples, msa_tag_examples

def get_single_annotations_file(assigned_corpus_indexes):
    testsite_array = []
    for index in assigned_corpus_indexes:
        with open(f"./annotations/corpus/inter_shami_{index}_annotated.txt", encoding='utf8') as my_file:
            testsite_array += my_file.readlines()
    return [t.strip() for t in testsite_array]


def sync_annotations(repo_dir='/Users/chriscay/thesis/annotation',
                     annotator_name='Christian') -> None:
    """This method is called each time the annotator presses the `Sync` button.
    What it does:
        - Checks out the branch in the annotator's name
        - Commits the contents of the working directory
        - Pushes the commit to the remote branch in the annotator's name
        - Checks out local main
        - Locally merges all the remote branches (one for each annotator) into local main
        - Checks out the branch in the annotator's name again
    """
    annotations_name = f'{annotator_name}_annotations'
    repo = Repo(repo_dir)
    repo.git.checkout(annotations_name)
    annotator_file_path = os.path.join(repo_dir, f'annotations_{annotator_name}.json')
    repo.index.add([annotator_file_path])
    repo.index.commit(COMMIT_MESSAGE)
    repo.git.push('origin', annotations_name)

    repo.git.fetch()
    remote_branches = repo.git.branch('-r').splitlines()
    remote_branches = [branch.strip()
                       for branch in remote_branches if re.match(r'\w+/\w+$', branch.strip(), re.M) \
                           and 'main' not in branch and 'resource' not in branch]
    repo.git.checkout('main')
    for branch in remote_branches:
        repo.git.merge(branch.strip())
    repo.git.checkout(annotations_name)


def get_merged_json(repo_dir='/Users/chriscay/thesis/annotation') -> Dict[Annotator, List[Annotation]]:
    """This method should be called to get the JSON file with the annotator's respective
    annotations. This is the file which should be edited by the platform in the working 
    directory.
    """
    annotator_file_paths = [file_path for file_path in os.listdir(repo_dir) if '.json' in file_path]
    annotations_json: Dict[Annotator, List[Annotation]] = {}
    for annotator_file_path in annotator_file_paths:
        with open(os.path.join(repo_dir, annotator_file_path), encoding='utf8') as f:
            try:
                annotations_json[re.sub(
                    '.json', '', annotator_file_path).split('_')[1]] = json.load(f)
            except json.JSONDecodeError:
                annotations_json[re.sub(
                    '.json', '', annotator_file_path).split('_')[1]] = []
    return annotations_json


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def is_well_formed(annotations):
    for i, a in enumerate(annotations):
        fixed = a['fixed'].translate(
            str.maketrans('', '', string.punctuation + '،؟ ')).strip()
        raw = ''.join(a['raw']).translate(str.maketrans(
            '', '', string.punctuation + '،؟ ')).strip()
        if a['fixed'] and fixed != raw:
            return False
        elif a['fixed'] and fixed == raw or not a['fixed']:
            if len(a['raw']) != len(a['coda']):
                return False
            if len(a['raw']) != len(a['taxonomy']):
                return False
            elif len(a['segments']):
                segments = ''.join([s['text'] for t in a['segments'] for s in t]).translate(str.maketrans(
                    '', '', string.punctuation + '،؟ ')).strip()
                if len(a['segments']) != len(a['raw']) or segments != raw:
                    return False
    return True

def get_annotated_sentences(repo_dir, corpus_indexes):
    annotations_json = get_merged_json(repo_dir)
    for annotator, annotations in annotations_json.items():
        index = corpus_indexes[annotator.capitalize()][0]
        with open(os.path.join(repo_dir, 'corpus', f'inter_shami_{index}_annotated.txt'), 'w', encoding='utf8') as f_corpus, \
                open(os.path.join(repo_dir, f'annotations_{annotator}.json'), 'w', encoding='utf8') as f_annotations:
            for a in annotations:
                if a.get('taxonomy') is None:
                    a['taxonomy'] = []
                    for raw_token, coda_token in zip(a['raw'], a['coda']):
                        if raw_token.strip() != coda_token.strip():
                            a['taxonomy'].append(['NONE'])
                        else:
                            a['taxonomy'].append('equal')
                print(a['original'], file=f_corpus) 
            json.dump(annotations, f_annotations, ensure_ascii=False)
            

# repo_dir = os.path.join(os.getcwd(), 'annotations')
# repo = Repo(repo_dir)
# repo.git.checkout('wiam_resources')
# with open('/Users/chriscay/annotation-software/annotations/examples/gulf_tag_examples.json') as f_gulf, \
#         open('/Users/chriscay/annotation-software/annotations/examples/coda_examples.json') as f_coda, \
#         open('/Users/chriscay/annotation-software/annotations/examples/msa_tag_examples.json') as f_msa:
#     gulf_tag_examples = json.load(f_gulf)
#     coda_examples = json.load(f_coda)
#     msa_tag_examples = json.load(f_msa)

# repo.git.checkout('wiam_annotations')
# with open('/Users/chriscay/annotation-software/annotations/annotations_wiam.json') as f:
#     annotations_json = json.load(f)

# search_bar_previous_annotations('p1:1', annotations_json, ('Segments', 'POS', 'Exact', 'Wiam'))
# repo.git.checkout('wiam_resources')
# search_bar_examples('NOUN', gulf_tag_examples, msa_tag_examples, coda_examples, ('Enclitic', 'Approximate', 'MSA Tags'))


# clone_repo(repo_dir='/Users/chriscay/thesis/annotation_carine',
#            annotator_name='Carine')
# sync_annotations(repo_dir='/Users/chriscay/thesis/annotation_carine',
#                     annotator_name='Carine')
# get_merged_json(repo_dir='/Users/chriscay/thesis/annotation_wiaam',
#                 annotator_name='Wiaam')
