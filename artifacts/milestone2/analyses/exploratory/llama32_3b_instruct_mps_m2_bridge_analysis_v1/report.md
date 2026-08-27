# Llama 3.2 3B Instruct M2 bridge analysis correction v1 results

This is a prospectively frozen but exploratory bridge on 24 previously used
prestage targets. It is not an independent confirmation or a scale curve.

| Layer | Ensemble mean | Ensemble 95% interval | Disjoint A-only mean | A-only 95% interval |
|---:|---:|:---:|---:|:---:|
| 5 | -0.02042789 | [-0.04346456, 0.00791963] | -0.01570587 | [-0.04172128, 0.01497396] |
| 11 | 0.02284696 | [0.00505693, 0.04422686] | 0.05532412 | [0.03292260, 0.07947684] |

Primary exploratory criterion: `exploratory_bridge_criterion_not_met`.
Both layer-5 lower bounds must exceed the prespecified delta 0.06; layer 11
cannot rescue layer 5.

The null ensemble has the unavoidable two-placement overlap documented by
the tokenizer-only design. Panel A is fully disjoint and is therefore reported
as a mandatory sensitivity. Random directions and zero hooks are secondary
integrity controls. No p-value or confirmatory status is assigned.

No model forward was performed by this analyzer, and P2/C1 were not accessed.
