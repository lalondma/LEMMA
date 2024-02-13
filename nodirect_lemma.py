import json
from lemma_component import LemmaComponent
from toolLearning import evidence_retreival
from config import data_root, out_root, definition_path
from utils import save_baseline, process_multilines_output

# mode ('direct' or 'cot' or 'cot+kg' or 'cot+fact' or 'lemma')
#### EXPLAINATION ####
# direct: directly use the text and image as input
# cot: use chain of thought method
# cot+kg: use chain of thought method and knowledge graph based reasoning
# cot+fact: use chain of thought method and fact check
# lemma: our method
mode = 'lemma_base'

# print the result
view = True

# automatic resume
resume = 1

# zero-shot conditional result
zs_flag = True

# intuition
intuition = True

# dataset (twitter or weibo or fakereddit or ticnn)
data_name = 'fakereddit'

# input data file name
if data_name == 'twitter':
    input_file = data_root + 'twitter/twitter_shuffled.json'
    use_online_image = True
elif data_name == 'weibo':
    input_file = data_root + 'weibo/weibo_50_2.json'
    use_online_image = False
elif data_name == 'fakereddit':
    input_file = data_root + 'fakereddit/FAKEDDIT_shuffled.json'
    use_online_image = True
elif data_name == 'ticnn':
    input_file = data_root + 'ticnn/ticnn_sample.json'
    use_online_image = True
elif data_name == 'fakehealth':
    input_file = data_root + 'fakehealth/fakehealth.json'
    use_online_image = True
elif data_name == 'weibo21':
    input_file = data_root + 'weibo21/weibo21_shuffle_1.json'
    use_online_image = False
elif data_name == 'pheme':
    input_file = data_root + 'PHEME/PHEME_reshuffled.json'
    use_online_image = True
elif data_name == 'test':
    input_file = data_root + 'exampleinput.json'
    use_online_image = True
else:
    raise ValueError('Invalid data name')

# output file names
output_score = out_root + data_name + '_' + mode + '_' + 'nodirect_result'
output_result = out_root + data_name + '_' + mode + '_' + 'nodirect_output.json'

with open(input_file, encoding='utf-8') as file:
    data = json.load(file)

if resume:
    with open(output_score, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        labels = []
        for char in lines[1]:
            if char.isdigit():
                labels.append(int(char))
        pred_labels = []
        for char in lines[3]:
            if char.isdigit():
                pred_labels.append(int(char))
    
        current_index = int(lines[4].split(':')[1].strip())
    with open(output_result, 'r', encoding='utf-8') as f:
        all_results = json.load(f)
    total_data_size = len(data)
    data = data[current_index + 1:]
    print('Resuming from index:', current_index, ', Next index:', current_index + 1)
else:
    pred_labels = []
    labels = []
    zero_shot_labels = []
    total_data_size = len(data)
    print('Starting from index 0')
    current_index = -1
    all_results = []

question_gen_module = LemmaComponent(prompt='question_gen.md', name='question_gen', model='gpt4v', using_cache=True,
                                     online_image=use_online_image, max_retry=3, max_tokens=1000, temperature=0.1,
                                     post_process=lambda x: json.loads(x))
modify_reasoning_module = LemmaComponent(prompt='reason_modify.md', name='modify_reasoning', model='gpt4v',
                                         using_cache=True,
                                         online_image=use_online_image, max_retry=3, max_tokens=1000, temperature=0.1,
                                         post_process=process_multilines_output)

for i, item in enumerate(data):
    current_index += 1
    print('Processing index {}/{}'.format(current_index, total_data_size))

    # Get input data
    url = item["image_url"]
    text = item["original_post"]
    label = item["label"]


    tool_learning_text = None
    zero_shot_external =1
    zero_shot_label = "None"
    zero_shot_explain = "None"

    if zero_shot_external == 1:
        question_gen = question_gen_module(TEXT=text, 
                                            PREDICTION=zero_shot_label, 
                                            REASONING=zero_shot_explain,
                                            image=url)
        if question_gen is None:
            continue
        title, questions = question_gen['title'], question_gen['questions']
        try:
            tool_learning_text = json.loads(evidence_retreival(text, title, questions))
            tool_learning_text = json.dumps([item for key in tool_learning_text for item in tool_learning_text[key]])
        except Exception as e:
            print(e)
            continue
        final_result = modify_reasoning_module(TEXT=text,
                                               ORIGINAL_REASONING=zero_shot_explain,
                                               TOOLLEARNING=tool_learning_text,
                                               DEFINITION=open(definition_path, 'r').read(),
                                               image=url)
        if final_result is None:
            continue
        modified_label = final_result["label"]
        modified_reasoning =  final_result["explanation"]

        for cat in ["True", "Satire/Parody", "Misleading Content", "Imposter Content", "False Connection",
                    "Manipulated Content", "Unverified"]:
            if cat.lower() in modified_label.lower():
                modified_label = cat
                break
        print('Modified label:', modified_label)
        if modified_label == 'True':
            pred_label = 0
        elif modified_label == 'Unverified':
            pred_label = 0
        else:
            pred_label = 1

    pred_labels.append(pred_label)
    labels.append(label)

    all_results.append({
        'text': text,
        'image_url': url,
        'tool_learning_text': tool_learning_text,
        'label': label,
        'prediction': pred_label,
        'explain': modified_reasoning,
    })




    print('Label:', label, ', Prediction:', pred_label, ', Zero-shot:', zero_shot_label)
    print('Modified explain:', modified_reasoning)

    save_baseline(labels, pred_labels, current_index, all_results, output_result, output_score)

if __name__ == '__main__':
    pass
