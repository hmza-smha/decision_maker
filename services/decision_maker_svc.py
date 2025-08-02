import copy
from dataclasses import dataclass
from pydantic import BaseModel
from ai_providers.factory import get_llm


@dataclass
class Step(BaseModel):
    order: int
    group: str
    content: str
    

class DecisionMakerSvc:
    
    def __init__(self, steps: list[dict]):

        if len(steps) == 0:
            raise Exception('Steps cannot be empty.')
        
        self.steps = steps
        self.step_order_content = []
        self.steps_groups = []
        self.__validate_steps()


    def get_steps_with_decisions(self):
        self._fill_steps_metadata()
        llm = get_llm()
        prompt = self._decision_steps_prompt()
        decision_steps = llm(input=prompt, is_json_response=True)

        decision_steps = [{
            **x,
            'type': 'decision'
        } for x in decision_steps]

        for rr in decision_steps:
            task = [x['content'] for x in self.step_order_content if x['order'] == rr['order']]
            rr['content'] = llm(input=self._decision_title_prompt().format(task=task))
            rr['group'] = llm(input=self._step_group_prompt().format(task=task, groups=self.steps_groups))

        self._merge_steps(decision_steps)
        steps = self._get_steps_ordered()
        return steps


    def __validate_steps(self):
        required_keys = ['order', 'content', 'group']
        for i, d in enumerate(self.steps):
            for key in required_keys:
                if key not in d:
                    raise KeyError(f"Step at index {i} is missing required key: '{key}'")


    def _merge_steps(self, decision_steps):
        list1 = decision_steps
        list2 = self.steps

        # Index decision steps by order
        decisions_map = {step['order']: step for step in list1}

        # Build output with interleaving
        self.steps = []
        for step in list2:
            self.steps.append(step)
            if step['order'] in decisions_map:
                self.steps.append(decisions_map[step['order']])


    def _get_steps_ordered(self):
        steps = self.steps
        original_to_index = {step['order']: [] for step in steps}
        for idx, step in enumerate(steps):
            original_to_index[step['order']].append(idx)

        sorted_steps = sorted(steps, key=lambda s: s['order'])
        new_steps = []
        order_mapping = {} 

        for new_order, step in enumerate(sorted_steps, start=1):
            new_step = copy.deepcopy(step)
            old_order = step['order']
            old_index = original_to_index[old_order].pop(0)
            order_mapping[old_index] = new_order
            new_step['order'] = new_order
            new_steps.append(new_step)


        for idx, step in enumerate(new_steps):
            if step['type'] == 'decision':
                for original_idx, mapped_order in order_mapping.items():
                    if mapped_order == step['order']:
                        original_decision = steps[original_idx]
                        yes_target = original_decision.get('yes_step')
                        no_target = original_decision.get('no_step')

                        for orig_idx, orig_step in enumerate(steps):
                            if orig_step['order'] == yes_target:
                                step['yes_step'] = order_mapping[orig_idx]
                            if orig_step['order'] == no_target:
                                step['no_step'] = order_mapping[orig_idx]

        return new_steps
    

    def _fill_steps_metadata(self):
        self.step_order_content = [{
            'order': x['order'],
            'content': x['content']
        } for x in self.steps]
        
        self.steps_groups = [{
            'group': x['group']
        } for x in self.steps]


    def _step_group_prompt(self) -> str:
        return """
Classify the following task into one of the given groups.
Respond with only the group name — no explanation or extra words.

Task:
{task}

Available Groups:
{groups}
"""

    def _decision_title_prompt(self) -> str:
        return """
Generate a decision title of 1-2 words of below task.
Return only your answer without any further word

Task:
{task}
"""

    def _rules_prompt(self) -> str:
        return """
yes_step and no_step must never point to the same step.
yes_step and no_step must never point to the same decision step.
At least one of yes_step or no_step must point to the next step.
"""

    def _output_format_prompt(self) -> str:
        return """Return only the decision steps in the following valid JSON format:
[
    {{
        "order": step order number that requires a decision or approval,
        "yes_step": <step order if the decision is true>,
        "no_step": <step order if the decision is false>
    }}
]
"""

    def _decision_steps_prompt(self) -> str:
        return """
You are provided with an ordered list of steps required to accomplish a project.

Your task:
Read, analyze, and fully understand the steps and how they relate to one another.
Identify any step that involves decision-making or requires approval to continue.

For each identified decision step, determine:
yes_step: the step order to follow if the decision is approved or true.
no_step: the step order to follow if the decision is rejected or false.

Output Format:
{output}

Important Rules:
{rules}

Your response must be a valid JSON array with no extra text.

Steps:
{steps}
""".format(output=self._output_format_prompt(), rules=self._rules_prompt(), steps=self.step_order_content)