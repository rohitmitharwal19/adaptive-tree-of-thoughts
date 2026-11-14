import itertools
import numpy as np
from functools import partial
from tot.models import gpt
import tot.methods.bfs as bfs_mod

from tot.methods.bfs import get_proposals, get_samples, get_values, get_votes

def adaptive_solve(args, task, idx, to_print=True):
    global gpt
    gpt = partial(gpt, model=args.backend, temperature=args.temperature)
    bfs_mod.gpt = gpt

    x = task.get_input(idx)
    ys = ['']
    infos = []

    for step in range(task.steps):
        # 1. Thought Generation (same as original ToT)
        if args.method_generate == 'sample':
            new_ys = [get_samples(task, x, y, args.n_generate_sample, prompt_sample=args.prompt_sample, stop=task.stops[step]) for y in ys]
        elif args.method_generate == 'propose':
            new_ys = [get_proposals(task, x, y) for y in ys]
        new_ys = list(itertools.chain(*new_ys))
        ids = list(range(len(new_ys)))

        # 2. State Evaluation (same as original ToT)
        if args.method_evaluate == 'vote':
            values = get_votes(task, x, new_ys, args.n_evaluate_sample)
        elif args.method_evaluate == 'value':
            values = get_values(task, x, new_ys, args.n_evaluate_sample)

        # 3. NOVEL IMPROVEMENT 1: Adaptive Beam Width
        # Shrink beam to 1 if a 'sure' (high-confidence >= 20) branch is found;
        # prune all 'impossible' (<= 0.01) branches automatically.
        valid_ids = [i for i in ids if values[i] > 0.01]
        if not valid_ids:
            valid_ids = ids  # fallback if all scored low

        max_val = max(values[i] for i in valid_ids)
        if max_val >= 20:
            dynamic_b = 1  # High confidence: focus strictly on best path
        else:
            dynamic_b = min(args.n_select_sample, len(valid_ids))

        select_ids = sorted(valid_ids, key=lambda i: values[i], reverse=True)[:dynamic_b]
        select_new_ys = [new_ys[i] for i in select_ids]

        if to_print:
            print(f'-- adaptive step {step} (dynamic_b={dynamic_b}) --')
            print(f'kept values: {[values[i] for i in select_ids]}')

        infos.append({
            'step': step,
            'x': x,
            'ys': ys,
            'new_ys': new_ys,
            'values': values,
            'select_new_ys': select_new_ys,
            'dynamic_beam_width': dynamic_b
        })
        ys = select_new_ys

        # 4. NOVEL IMPROVEMENT 2: Early-Exit Verification
        # Stop exploring remaining tree depths if a valid solution is already reached
        for candidate in ys:
            check = task.test_output(idx, candidate)
            if check.get('r', 0) == 1:
                if to_print:
                    print(f'Early stopping triggered at step {step}! Valid solution found.')
                return [candidate], {'steps': infos, 'early_stopped_at': step}

    return ys, {'steps': infos}