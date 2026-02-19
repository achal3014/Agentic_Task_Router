from pprint import pprint
from app.agents.summarizer_agent import summarize_text

text = '''
The rapid convergence of large-scale neural architectures, distributed data pipelines, and probabilistic inference mechanisms has fundamentally altered the epistemic boundaries of computational systems, such that modern machine-mediated decision processes no longer operate purely as deterministic function evaluators but instead as context-sensitive pattern synthesizers whose outputs are contingent upon latent representations learned from heterogeneous, often weakly supervised corpora. This shift introduces non-trivial challenges in interpretability, reproducibility, and governance, particularly when such systems are embedded within socio-technical infrastructures where feedback loops between human behavior and algorithmic adaptation can amplify biases, obscure causal accountability, and complicate post-hoc evaluation, thereby necessitating the development of robust oversight frameworks that reconcile statistical performance with ethical and regulatory constraints.
'''

result = summarize_text(text)

pprint(result)
