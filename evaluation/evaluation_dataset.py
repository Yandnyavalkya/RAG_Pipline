
EVALUATION_DATASET = [
    {
        "id": 1,
        "question": "What is the Transformer architecture?",
        "expected_answer": (
            "The Transformer is an architecture based on attention "
            "mechanisms that uses self-attention instead of recurrence "
            "or convolution for sequence modelling."
        ),
        "relevant_chunk_keys": [
            "b50429afa5e4819892abdd64f2367e7519273e6ea17b1dc94503310f39bd785b",
        ],
        "answerable": True,
    },
    {
        "id": 2,
        "question": "What is the purpose of multi-head attention?",
        "expected_answer": (
            "Multi-head attention allows the model to jointly attend "
            "to information from different representation subspaces "
            "at different positions."
        ),
        "relevant_chunk_keys": [
            "0397b55f32ee41fd665890e637831f7b3de1c8af573f367172a0ebd3287fa7a4",
            "0c23cc3e784c2e6325885fad13ba0999f2cab635da89f144752591c23ad3d9e9",
            "c15e08c8278bcbacc654e450499c42540b3a4a2dcc51769bd07143df759808a8",
        ],
        "answerable": True,
    },
    {
        "id": 3,
        "question": "Why does the Transformer use positional encoding?",
        "expected_answer": (
            "Positional encoding provides information about token "
            "positions because the Transformer does not use recurrence "
            "or convolution to represent sequence order."
        ),
        "relevant_chunk_keys": [
            "9fa70977e466b930a27f59b10d592f3c37ed2581cdaada0b64426eb60c601ca6",
            "620ad196075b46f22bdb38b72af38199753c14c697c84425aeb53d3766c20f5b",
        ],
        "answerable": True,
    },
    {
        "id": 4,
        "question": "What is the difference between the encoder and decoder?",
        "expected_answer": (
            "The encoder processes the input sequence, while the decoder "
            "generates the output sequence using masked self-attention "
            "and attention over encoder outputs."
        ),
        "relevant_chunk_keys": [
            "733d373a77780f18e8377ed6f1638cb1d31d1a102f65729d8b39f0a757533bf0",
            "558ab3becf310aee695e2c57fb396c4787f2a3d7660be53dc60f2a989c99a470",
            "b50429afa5e4819892abdd64f2367e7519273e6ea17b1dc94503310f39bd785b",
        ],
        "answerable": True,
    },
    {
        "id": 5,
        "question": "What is the computational complexity of self-attention?",
        "expected_answer": (
            "The computational complexity of self-attention with respect "
            "to sequence length is quadratic."
        ),
        "relevant_chunk_keys": [
            "0397b55f32ee41fd665890e637831f7b3de1c8af573f367172a0ebd3287fa7a4",
            "4bce026c2eaeca9d30a509c49c6322485c91b452de3ad0aa07321a39455fcd56",
            "e94bd48f7b78d5370d93321de9dc32f6f0b754d3d923c78374fc18cff59c7a3d",
            "7b0ff7770536109d5fb0fe85f04c5320ec65739a85a8b9e9bf38048ef6bbb456",
        ],
        "answerable": True,
    },
    {
        "id": 6,
        "question": "Explain how photosynthesis works.",
        "expected_answer": (
            "This topic is not covered by the provided Transformer paper."
        ),
        "relevant_chunk_keys": [],
        "answerable": False,
    },
]
