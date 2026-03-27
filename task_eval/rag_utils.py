import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import os, json
import torch
from tqdm import tqdm
from global_methods import get_openai_embedding, set_openai_key, run_chatgpt_with_examples
from device_utils import get_torch_device


def _to_device(batch, device):
    if isinstance(batch, dict):
        return {k: v.to(device) for k, v in batch.items()}
    return batch.to(device)



def save_eval(data_file, accs, key='exact_match'):

    
    if os.path.exists(data_file.replace('.json', '_scores.json')):
        data = json.load(open(data_file.replace('.json', '_scores.json')))
    else:
        data = json.load(open(data_file))

    assert len(data['qa']) == len(accs), (len(data['qa']), len(accs), accs)
    for i in range(0, len(data['qa'])):
        data['qa'][i][key] = accs[i]
    
    with open(data_file.replace('.json', '_scores.json'), 'w') as f:
        json.dump(data, f, indent=2)


# Mean pooling
def mean_pooling(token_embeddings, mask):
    token_embeddings = token_embeddings.masked_fill(~mask[..., None].bool(), 0.)
    sentence_embeddings = token_embeddings.sum(dim=1) / mask.sum(dim=1)[..., None]
    return sentence_embeddings


def init_context_model(retriever):

    device = get_torch_device()

    if retriever == 'dpr':
        from transformers import DPRConfig, DPRContextEncoder, DPRQuestionEncoder, DPRQuestionEncoderTokenizer, DPRContextEncoderTokenizer
        context_tokenizer = DPRContextEncoderTokenizer.from_pretrained("facebook/dpr-ctx_encoder-single-nq-base")
        context_model = DPRContextEncoder.from_pretrained("facebook/dpr-ctx_encoder-single-nq-base").to(device)
        context_model.eval()
        return context_tokenizer, context_model

    elif retriever == 'contriever':

        from transformers import AutoTokenizer, AutoModel
        context_tokenizer = AutoTokenizer.from_pretrained('facebook/contriever')
        context_model = AutoModel.from_pretrained('facebook/contriever').to(device)
        context_model.eval()
        return context_tokenizer, context_model

    elif retriever == 'dragon':

        from transformers import AutoTokenizer, AutoModel
        context_tokenizer = AutoTokenizer.from_pretrained('facebook/dragon-plus-query-encoder')
        context_model = AutoModel.from_pretrained('facebook/dragon-plus-context-encoder').to(device)
        context_model.eval()
        return context_tokenizer, context_model

    elif retriever == 'openai':

        set_openai_key()
        return None, None
    
    else:
        raise ValueError
    
def init_query_model(retriever):

    device = get_torch_device()

    if retriever == 'dpr':
        from transformers import DPRConfig, DPRContextEncoder, DPRQuestionEncoder, DPRQuestionEncoderTokenizer, DPRContextEncoderTokenizer
        question_tokenizer = DPRQuestionEncoderTokenizer.from_pretrained("facebook/dpr-question_encoder-single-nq-base")
        question_model = DPRQuestionEncoder.from_pretrained("facebook/dpr-question_encoder-single-nq-base").to(device)
        question_model.eval()
        return question_tokenizer, question_model

    elif retriever == 'contriever':

        from transformers import AutoTokenizer, AutoModel
        question_tokenizer = AutoTokenizer.from_pretrained('facebook/contriever')
        question_model = AutoModel.from_pretrained('facebook/contriever').to(device)
        question_model.eval()
        return question_tokenizer, question_model

    elif retriever == 'dragon':

        from transformers import AutoTokenizer, AutoModel
        question_tokenizer = AutoTokenizer.from_pretrained('facebook/dragon-plus-query-encoder')
        question_model = AutoModel.from_pretrained('facebook/dragon-plus-query-encoder').to(device)
        question_model.eval()
        return question_tokenizer, question_model

    elif retriever == 'openai':

        set_openai_key()
        return None, None
    
    else:
        raise ValueError


def get_embeddings(retriever, inputs, mode='context'):

    if mode == 'context':
        tokenizer, encoder = init_context_model(retriever)
    else:
        tokenizer, encoder = init_query_model(retriever)
    
    all_embeddings = []
    batch_size = 24
    device = get_torch_device()
    with torch.no_grad():
        for i in tqdm(range(0, len(inputs), batch_size)):
            batch = inputs[i:(i+batch_size)]
            if retriever == 'dpr':
                input_ids = tokenizer(batch, return_tensors="pt", padding=True)["input_ids"].to(device)
                embeddings = encoder(input_ids).pooler_output.detach()
                all_embeddings.append(torch.nn.functional.normalize(embeddings, dim=-1))
            elif retriever == 'contriever':
                ctx_input = tokenizer(batch, padding=True, truncation=True, return_tensors='pt')
                ctx_input = _to_device(ctx_input, device)
                outputs = encoder(**ctx_input)
                embeddings = mean_pooling(outputs[0], ctx_input['attention_mask'])
                all_embeddings.append(torch.nn.functional.normalize(embeddings, dim=-1))
            elif retriever == 'dragon':
                ctx_input = tokenizer(batch, padding=True, truncation=True, return_tensors='pt')
                ctx_input = _to_device(ctx_input, device)
                embeddings = encoder(**ctx_input).last_hidden_state[:, 0, :]
                all_embeddings.append(embeddings)
            elif retriever == 'openai':
                all_embeddings.append(torch.tensor(get_openai_embedding(batch)))
            else:
                raise ValueError

    return torch.cat(all_embeddings, dim=0).cpu().numpy()


def get_context_embeddings(retriever, data, context_tokenizer, context_encoder, captions=None):

    context_embeddings = []
    context_ids = []
    device = get_torch_device()
    for i in tqdm(range(1,20), desc="Getting context encodings"):
        contexts = []
        if 'session_%s' % i in data:
            date_time_string = data['session_%s_date_time' % i]
            for dialog in data['session_%s' % i]:

                turn = ''
                # conv = conv + dialog['speaker'] + ' said, \"' + dialog['clean_text'] + '\"' + '\n'
                try:
                    turn = dialog['speaker'] + ' said, \"' + dialog['compressed_text'] + '\"' + '\n'
                    # conv = conv + dialog['speaker'] + ': ' + dialog['compressed_text'] + '\n'
                except KeyError:
                    turn = dialog['speaker'] + ' said, \"' + dialog['clean_text'] + '\"' + '\n'
                    # conv = conv + dialog['speaker'] + ': ' + dialog['clean_text'] + '\n'
                if "img_file" in dialog and len(dialog["img_file"]) > 0:
                    turn += '[shares %s]\n' % dialog["blip_caption"]
                contexts.append('(' + date_time_string + ') ' + turn)

                context_ids.append(dialog["dia_id"])
            with torch.no_grad():
                if retriever == 'dpr':
                    input_ids = context_tokenizer(contexts, return_tensors="pt", padding=True)["input_ids"].to(device)
                    embeddings = context_encoder(input_ids).pooler_output.detach()
                    context_embeddings.append(torch.nn.functional.normalize(embeddings, dim=-1))
                elif retriever == 'contriever':
                    inputs = context_tokenizer(contexts, padding=True, truncation=True, return_tensors='pt')
                    inputs = _to_device(inputs, device)
                    outputs = context_encoder(**inputs)
                    embeddings = mean_pooling(outputs[0], inputs['attention_mask'])
                    context_embeddings.append(torch.nn.functional.normalize(embeddings, dim=-1))
                elif retriever == 'dragon':
                    ctx_input = context_tokenizer(contexts, padding=True, truncation=True, return_tensors='pt')
                    ctx_input = _to_device(ctx_input, device)
                    embeddings = context_encoder(**ctx_input).last_hidden_state[:, 0, :]
                    context_embeddings.append(torch.nn.functional.normalize(embeddings, dim=-1))
                elif retriever == 'openai':
                    context_embeddings.append(torch.tensor(get_openai_embedding(contexts)))
                else:
                    raise ValueError

    # print(context_embeddings[0].shape[0])
    context_embeddings = torch.cat(context_embeddings, dim=0)
    # print(context_embeddings.shape[0])

    return context_ids, context_embeddings
