---
title: 'DeepSynth: Scaling Neural Program Synthesis with
Distribution-based Search'
tags:
  - Python
  - program synthesis
  - enumeration
  - scalable
authors:
  - name: Nathanaël Fijalkow
    orcid: 0000-0002-6576-4680  
    affiliation: "1, 2" # (Multiple affiliations must be quoted)
  - name: Guillaume Lagarde
    affiliation: 1
  - name: Théo Matricon
    affiliation: 1
    orcid:  0000-0002-5043-3221 
  - name: Kevin Ellis
    affiliation: 3
  - name: Pierre Ohlmann
    affiliation: 4
    orcid:  0000-0002-4685-5253
  - name: Akarsh Potta
    affiliation: 5
affiliations:
 - name: CNRS, LaBRI and Université de Bordeaux, France
   index: 1
 - name: The Alan Turing Institute of data science, United Kingdom
   index: 2
 - name: Cornell University, United States
   index: 3
 - name: University of Paris, France
   index: 4
 - name: Indidan Institute of Technology, Bombay, India 
   index: 5
date: 13 December 2021
bibliography: paper.bib
---

# Summary

Writing software is tedious, error-prone, and accessible only to a small share of the population – yet coding grows increasingly important as the digital world plays larger and larger roles in peoples’ lives.
One way to specify such programs is from pairs of input-output examples.
`DeepSynth` is such a framework. Contrary to other frameworks, `DeepSynth` leverages the speed of neural networks with the theoretical guarantees of symbolic methods to generate programs, combining the benefits of both worlds to make program synthesis scalable with guarantees.

# Statement of need

A common problem in program synthesis is to generate programs based on examples (PBE).  This automated synthesys shines when applied on domain specific languages (DSL). This DSL produced by the user can then be processed to generate programs however doing so is complex and the search for likely programs that fit the examples given can be hard.
`DeepSynth` proposes an automated pipeline for professionals and for students to generate programs based on pairs of input-output examples.
Figure \autoref{fig:description} illustrates the machine learning pipeline for program synthesis on a toy DSL describing integer list manipulating program. This software is the implementation associated to the paper of `@Fijalkow:2021` (TODO: fix this to AAAI 2022 submission).
Theis framework leverages `@pytorch` to produce a neural network to guide the search based on examples towards likely programs.
The enumeration of likely programs can thus be done optimally.
It can furthermore be parallisled without concerns providing a scalable neural program synthesys approach.

![Pipeline for neural predictions for syntax guided program synthesis.\label{fig:description}](main_figure.png)

# Features

The package allows to:
- create a simple DSL from syntaxic constraints and semantics functions
- Transform this DSL into a CFG
- Transform this CFG into a PCFG
- Sample programs from a PCFG
- Enumerate programs in a PCFG with many different algorithms including `HeapSearch`, a method that is practically faster than $A^*$ while remaining optimal like the latter
- A grammar splitter that enables to split the search into `n` independent search, enabling easy parallel search without any concerns and scaling linearly with the number of CPUs.
- A neural network architecture to predict probabilities of a CFG given pairs of input-output examples and its automatic training procedure from a DSL that supports `int`, `bool` and `list` inputs.

# References