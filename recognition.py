import copy
import torch
import torch.nn as nn
import numpy as np
import torch.nn.functional as F
from torch.nn.utils.rnn import pack_padded_sequence

from pcfg import PCFG
from pcfg_logprob import LogProbPCFG

class RecognitionModel(nn.Module):
    def __init__(self, template_cfg, feature_extractor, intermediate_q=False):
        """
        template_cfg: a cfg giving the structure that will be output 
        by this recognition model

        feature_extractor: a neural network module 
        taking a list of tasks (such as a list of input-outputs) 
        and returning a tensor of shape 
        [len(list_of_tasks), feature_extractor.output_dimensionality]

        intermediate_q: whether the pcfg weights are produced 
        by first calculating an intermediate "Q" tensor as in dreamcoder 
        and then constructing the PCFG from that
        """
        super(RecognitionModel, self).__init__()

        self.feature_extractor = feature_extractor
        self.intermediate_q = intermediate_q

        self.template = template_cfg

        H = self.feature_extractor.output_dimensionality # hidden
        if not intermediate_q:
            projection_layer = {}
            for S in template_cfg.rules:
                n_productions = len(template_cfg.rules)
                module = nn.Sequential(
                    nn.Linear(H, n_productions),
                    nn.LogSoftmax(-1)
                    )
                projection_layer[format(S)] = module
            self.projection_layer = nn.ModuleDict(projection_layer)
        else:
            assert False

    def forward(self, tasks):
        """
        tasks: list of tasks
        returns: list of PCFGs
        """
        features = self.feature_extractor(tasks)
        template = self.template

        probabilities = {S: self.projection_layer[format(S)](features)
                         for S in template.rules}

        grammars = []
        for b in range(len(tasks)): # iterate over batches
            rules = {}
            for S in template.rules:
                rules[S] = {}
                for i, P in enumerate(template.rules[S]):
                    rules[S][P] = template.rules[S][P], probabilities[S][b, i]
            grammar = LogProbPCFG(template.start, 
                rules, 
                max_program_depth=template.max_program_depth)
            grammars.append(grammar)
        return grammars

class RecurrentFeatureExtractor(nn.Module):
    def __init__(self, _=None,
                 cuda=False,
                 # what are the symbols that can occur 
                 # in the inputs and outputs
                 lexicon=None,
                 # how many hidden units
                 H=32,
                 # should the recurrent units be bidirectional?
                 bidirectional=False):
        super(RecurrentFeatureExtractor, self).__init__()

        assert lexicon
        self.specialSymbols = [
            "STARTING",  # start of entire sequence
            "ENDING",  # ending of entire sequence
            "STARTOFOUTPUT",  # begins the start of the output
            "ENDOFINPUT"  # delimits the ending of an input - we might have multiple inputs
        ]
        lexicon += self.specialSymbols
        encoder = nn.Embedding(len(lexicon), H)
        self.encoder = encoder

        self.H = H
        self.bidirectional = bidirectional

        layers = 1

        model = nn.GRU(H, H, layers, bidirectional=bidirectional)
        self.model = model

        self.use_cuda = cuda
        self.lexicon = lexicon
        self.symbolToIndex = {
            symbol: index for index,
            symbol in enumerate(lexicon)
            }
        self.startingIndex = self.symbolToIndex["STARTING"]
        self.endingIndex = self.symbolToIndex["ENDING"]
        self.startOfOutputIndex = self.symbolToIndex["STARTOFOUTPUT"]
        self.endOfInputIndex = self.symbolToIndex["ENDOFINPUT"]

        # Maximum number of inputs/outputs we will run the recognition
        # model on per task
        # This is an optimization hack
        self.MAXINPUTS = 100

        if cuda: self.cuda()

    @property
    def output_dimensionality(self): return self.H

    # modify examples before forward (to turn them into iterables of lexicon)
    # you should override this if needed
    def tokenize(self, x): return x

    def packExamples(self, examples):
        """
        IMPORTANT! xs must be sorted in decreasing order of size 
        because pytorch is stupid
        """
        es = []
        sizes = []
        for xs, y in examples:
            e = [self.startingIndex]
            for x in xs:
                for s in x:
                    e.append(self.symbolToIndex[s])
                e.append(self.endOfInputIndex)
            e.append(self.startOfOutputIndex)
            for s in y:
                e.append(self.symbolToIndex[s])
            e.append(self.endingIndex)
            if es != []:
                assert len(e) <= len(es[-1]), \
                    "Examples must be sorted in decreasing order of their tokenized size. This should be transparently handled in recognition.py, so if this assertion fails it isn't your fault as a user of EC but instead is a bug inside of EC."
            es.append(e)
            sizes.append(len(e))

        m = max(sizes)
        # padding
        for j, e in enumerate(es):
            es[j] += [self.endingIndex] * (m - len(e))

        x = torch.tensor(es)
        if self.use_cuda: x = x.cuda()
        x = self.encoder(x)
        # x: (batch size, maximum length, E)
        x = x.permute(1, 0, 2)
        # x: TxBxE
        x = pack_padded_sequence(x, sizes)
        return x, sizes

    def examplesEncoding(self, examples):
        examples = sorted(examples, key=lambda xs_y: sum(
            len(z) + 1 for z in xs_y[0]) + len(xs_y[1]), reverse=True)
        x, sizes = self.packExamples(examples)
        outputs, hidden = self.model(x)
        # outputs, sizes = pad_packed_sequence(outputs)
        # I don't know whether to return the final output or the final hidden
        # activations...
        return hidden[0, :, :] + hidden[1, :, :]

    def forward_one_task(self, examples):
        tokenized = self.tokenize(examples)

        if hasattr(self, 'MAXINPUTS') and len(tokenized) > self.MAXINPUTS:
            tokenized = list(tokenized)
            random.shuffle(tokenized)
            tokenized = tokenized[:self.MAXINPUTS]
        e = self.examplesEncoding(tokenized)
        # max pool
        # e,_ = e.max(dim = 0)

        # take the average activations across all of the examples
        # I think this might be better because we might be testing on data
        # which has far more or far fewer examples then training
        e = e.mean(dim=0)
        return e

    def forward(self, tasks):
        #fix me! properly batch the recurrent network across all tasks at once
        return torch.stack([self.forward_one_task(task) for task in tasks])
    
