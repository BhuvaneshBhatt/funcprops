# Certification model

## Why use certification?

Symbolic systems often return an expression without recording why it is valid or which hypotheses were proved. Funcprops distinguishes a computed candidate from a result whose mathematical obligations have been discharged. This matters most for branch-sensitive complex analysis, parameter-dependent identities, singularities, and global properties.

A certified result carries replayable evidence. `verify_certificate()` reconstructs the relevant obligations from the certificate data and checks that the stored conclusion still follows.

## Result states

The public APIs use three logically different outcomes:

- a certificate or certified value means the stated proposition was established for the supplied inputs;
- `False` is returned only when the API has established the negation of a Boolean proposition;
- `None` means the available proof procedures did not establish either side.

`None` is not evidence that a proposition is false.

`complete` describes whether an operation established that its returned mathematical object exhausts the requested result, such as all roots in a domain. `certified` describes whether the returned conclusion has proof-strength evidence. These fields are independent where an API can provide useful partial information.

## Replay

Certificate replay validates mathematical fields, not only a status flag. Changing a winding number, cut word, puncture set, solution set, or other proof-relevant field must cause verification to fail.

Certificates are evidence for the theorem implemented by their API. They are not general proof objects for arbitrary propositions outside that theorem's documented hypotheses.

## Failure boundaries

Proof procedures may stop when exact ordering, sign, root completeness, meromorphicity, branch data, or interval separation cannot be established. Funcprops keeps these boundaries visible.
